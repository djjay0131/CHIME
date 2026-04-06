#!/bin/bash
# setup-r650.sh — Unified Day 1 setup for r650 cluster at Clemson
#
# Runs the full pipeline: SSH keys → OFED → libs → hugepages → repos →
# CPU patch → build → config → workload symlinks → smoke test
#
# Usage:
#   ./setup-r650.sh <nodes_file> <master_ip_or_hostname>
#
# Example:
#   ./setup-r650.sh nodes.txt node-0.exp.chime-r650.cs620426sp-PG0.clemson.cloudlab.us
#
# Prerequisites:
#   - nodes.txt: one hostname per line (from CloudLab List View)
#   - SSH access to all nodes (password or key-based; setKey.py will distribute keys)
#   - Run from ~/CHIME on the master node, or from your laptop with SSH access
#
# Output:
#   - HEALTHY_NODES written to construction/scripts/healthy_nodes.txt
#   - common.json regenerated with healthy node IPs
#   - fig params patched to actual CN count
#   - Smoke test passed = cluster ready for experiments

set -euo pipefail
cd "$(dirname "$0")/../.."
CHIME_ROOT="$PWD"

# ---- Args ----
if [ $# -lt 2 ]; then
    echo "Usage: $0 <nodes_file> <master_ip_or_hostname> [min_cn]"
    echo "  nodes_file: one hostname per line"
    echo "  master: IP or hostname of the master/MN node (must appear in nodes_file)"
    echo "  min_cn: minimum compute nodes required (default: 2)"
    exit 1
fi

NODES_FILE="$(realpath "$1")"
MASTER="$2"
MIN_CN="${3:-2}"
ALL_NODES=($(cat "$NODES_FILE"))
NODE_COUNT=${#ALL_NODES[@]}
HEALTHY_NODES=()
FAILED_NODES=()
HEALTHY_FILE="$CHIME_ROOT/construction/scripts/healthy_nodes.txt"

log() { echo "[$(date '+%H:%M:%S')] $*"; }
log_ok() { echo "[$(date '+%H:%M:%S')]   OK $*"; }
log_fail() { echo "[$(date '+%H:%M:%S')]   FAIL $*"; }

SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=10"

log "=== setup-r650.sh: $NODE_COUNT nodes, master=$MASTER ==="
log ""

# ======================================================================
# Phase 1: SSH Keys (2 min)
# ======================================================================
log "Phase 1/7: Distributing SSH keys..."
NODES_FILE="$NODES_FILE" python3 "$CHIME_ROOT/script/setKey.py"
log "Phase 1 complete."
log ""

# ======================================================================
# Phase 2: Parallel Node Setup (15 min)
# ======================================================================
log "Phase 2/7: OFED + libs + hugepages on all nodes (parallel)..."
log "  This takes ~15 minutes. Each node runs independently."

SETUP_PIDS=()
for node in "${ALL_NODES[@]}"; do
    (
        ssh $SSH_OPTS "$node" "
            set -e
            cd ~/CHIME/script
            # OFED (skip if already installed)
            if ! ibv_devinfo &>/dev/null; then
                bash installMLNX.sh
            fi
            # Libraries
            bash installLibs.sh
            # Hugepages
            echo 36864 | sudo tee /proc/sys/vm/nr_hugepages > /dev/null
            sudo bash -c 'ulimit -l unlimited' 2>/dev/null || true
        " 2>&1 | while IFS= read -r line; do
            echo "  [$node] $line"
        done
    ) &
    SETUP_PIDS+=($!)
done

# Wait for all setup processes
SETUP_FAILED=0
for pid in "${SETUP_PIDS[@]}"; do
    if ! wait "$pid"; then
        SETUP_FAILED=$((SETUP_FAILED + 1))
    fi
done

if [ "$SETUP_FAILED" -gt 0 ]; then
    log "WARNING: $SETUP_FAILED node(s) had setup errors. Pre-flight will catch them."
fi
log "Phase 2 complete."
log ""

# ======================================================================
# Phase 3: Pre-flight Validation (5 min)
# ======================================================================
log "Phase 3/7: Validating RDMA on every node (2-stage check)..."

# Resolve master node — first node in file is assumed master
MASTER_NODE="${ALL_NODES[0]}"

for node in "${ALL_NODES[@]}"; do
    # Stage 1: ibv_devinfo — NIC present and active?
    if ! ssh $SSH_OPTS "$node" "ibv_devinfo 2>/dev/null | grep -q 'state.*PORT_ACTIVE'" 2>/dev/null; then
        log_fail "$node — ibv_devinfo: NIC not active (excluding)"
        FAILED_NODES+=("$node")
        continue
    fi

    # Stage 2: Pairwise RDMA connectivity (skip for master itself)
    if [ "$node" != "$MASTER_NODE" ]; then
        # Start ib_read_lat server on target, run client from master
        ssh $SSH_OPTS "$node" "timeout 10 ib_read_lat -d mlx5_0 &>/dev/null &" 2>/dev/null
        sleep 2
        if ssh $SSH_OPTS "$MASTER_NODE" "timeout 15 ib_read_lat -d mlx5_0 $node -n 10 &>/dev/null" 2>/dev/null; then
            HEALTHY_NODES+=("$node")
            log_ok "$node — RDMA active + connectivity verified"
        else
            log_fail "$node — RDMA connectivity test failed (excluding)"
            FAILED_NODES+=("$node")
        fi
        ssh $SSH_OPTS "$node" "killall ib_read_lat 2>/dev/null || true" 2>/dev/null
    else
        # Master node — just check NIC status (already passed stage 1)
        HEALTHY_NODES+=("$node")
        log_ok "$node — master node (RDMA NIC active)"
    fi
done

CN_COUNT=$(( ${#HEALTHY_NODES[@]} - 1 ))
log ""
log "Pre-flight results: ${#HEALTHY_NODES[@]} healthy, ${#FAILED_NODES[@]} failed"
log "  Healthy: ${HEALTHY_NODES[*]}"
if [ ${#FAILED_NODES[@]} -gt 0 ]; then
    log "  Failed:  ${FAILED_NODES[*]}"
fi
log "  Cluster: ${CN_COUNT} CN + 1 MN"

if [ "$CN_COUNT" -lt "$MIN_CN" ]; then
    log "FATAL: Need at least $MIN_CN CN. Only $CN_COUNT healthy. Aborting."
    exit 1
fi

# Save healthy nodes for later use by resilient_runner.py
printf '%s\n' "${HEALTHY_NODES[@]}" > "$HEALTHY_FILE"
log "Healthy nodes saved to $HEALTHY_FILE"
log "Phase 3 complete."
log ""

# ======================================================================
# Phase 4: Repos + RoCE Fixes + Builds (10 min)
# ======================================================================
log "Phase 4/7: Cloning repos + applying RoCE fixes + building..."

HEALTHY_CSV=$(printf '%s,' "${HEALTHY_NODES[@]}" | sed 's/,$//')

# Clone sibling repos if not present
bash "$CHIME_ROOT/script/run-on-nodes.sh" "$HEALTHY_CSV" \
    "cd ~ && [ -d SMART ] || bash ~/CHIME/script/clone-repos.sh"

# Patch CPU_PHYSICAL_CORE_NUM to 72 (r650 = 2x36 cores)
# r6525 had 64; paper default is 36 (single socket). r650 dual-socket = 72.
bash "$CHIME_ROOT/script/run-on-nodes.sh" "$HEALTHY_CSV" \
    "sed -i 's/define CPU_PHYSICAL_CORE_NUM.*/define CPU_PHYSICAL_CORE_NUM 72/' \
     ~/CHIME/include/Common.h ~/SMART/include/Common.h ~/ROLEX/include/Common.h 2>/dev/null || true"

# ---- RoCE fixes for r650 at Clemson ----
# The codebase defaults to InfiniBand; r650 uses RoCE over Ethernet.
# These 5 sed patches must be applied to all repos (CHIME, SMART, ROLEX).
log "  Applying RoCE fixes (Rdma.h + Resource.cpp) on all nodes..."
bash "$CHIME_ROOT/script/run-on-nodes.sh" "$HEALTHY_CSV" '
for repo in ~/CHIME ~/SMART ~/ROLEX; do
    [ -f "$repo/include/Rdma.h" ] || continue
    # 1. IB_DEV_NAME_IDX: 2 -> 0 (mlx5_0 is the active RoCE port)
    sed -i "s/IB_DEV_NAME_IDX .*/IB_DEV_NAME_IDX '\''0'\''/" "$repo/include/Rdma.h"
    # 2. IBV_MTU: 4096 -> 1024 (Ethernet MTU = 1500)
    sed -i "s/IBV_MTU IBV_MTU_4096/IBV_MTU IBV_MTU_1024/" "$repo/include/Rdma.h"
    # 3. hop_limit: 1 -> 64 (multi-hop RoCE)
    sed -i "s/hop_limit = 1/hop_limit = 64/g" "$repo/src/rdma/Resource.cpp"
done
'

# Default CHIME build — validates toolchain (libs, headers, CMake)
# Method-specific builds happen at experiment runtime via fig_*.py
log "  Building CHIME (default config) on all healthy nodes..."
bash "$CHIME_ROOT/script/run-on-nodes.sh" "$HEALTHY_CSV" \
    "cd ~/CHIME && mkdir -p build && cd build && cmake .. 2>&1 | tail -1 && make -j 2>&1 | tail -1"

log "Phase 4 complete."
log ""

# ======================================================================
# Phase 5: Configuration + Workloads (5 min)
# ======================================================================
log "Phase 5/7: Generating config and linking workloads..."

# Resolve hostnames to internal LAN IPs (10.x.x.x) for common.json.
# CRITICAL: RDMA traffic must go over the internal VLAN, not the public control net.
# The profile assigns 10.10.1.{1..N} but CloudLab may also assign a VLAN IP.
# We look for 10.x.x.x addresses; fall back to first IP if none found.
HEALTHY_IPS=""
for node in "${HEALTHY_NODES[@]}"; do
    ip=$(ssh $SSH_OPTS "$node" "hostname -I | tr ' ' '\n' | grep '^10\.' | head -1" 2>/dev/null)
    if [ -z "$ip" ]; then
        # Fallback: first IP (may be public — will warn)
        ip=$(ssh $SSH_OPTS "$node" "hostname -I | awk '{print \$1}'" 2>/dev/null)
        log "  WARNING: No 10.x.x.x IP found on $node, using $ip (may be public!)"
    fi
    if [ -n "$ip" ]; then
        HEALTHY_IPS="${HEALTHY_IPS:+$HEALTHY_IPS,}$ip"
    else
        HEALTHY_IPS="${HEALTHY_IPS:+$HEALTHY_IPS,}$node"
    fi
done

# Resolve master IP (internal LAN)
MASTER_IP=$(ssh $SSH_OPTS "$MASTER_NODE" "hostname -I | tr ' ' '\n' | grep '^10\.' | head -1" 2>/dev/null)
if [ -z "$MASTER_IP" ]; then
    MASTER_IP=$(ssh $SSH_OPTS "$MASTER_NODE" "hostname -I | awk '{print \$1}'" 2>/dev/null)
    log "  WARNING: No 10.x.x.x IP for master, using $MASTER_IP"
fi
if [ -z "$MASTER_IP" ]; then
    MASTER_IP="$MASTER"
fi

log "  Master IP: $MASTER_IP"
log "  Cluster IPs: $HEALTHY_IPS"

# Generate common.json
python3 "$CHIME_ROOT/construction/scripts/generate-common-json.py" \
    --home "/users/$(whoami)" \
    --master "$MASTER_IP" \
    --ips "$HEALTHY_IPS" \
    --out "$CHIME_ROOT/exp/params/common.json"

# Patch CN count in figure params
python3 "$CHIME_ROOT/construction/scripts/patch-cn-count.py" "$CN_COUNT"

# Symlink YCSB workloads from project NFS (if available)
NFS_WORKLOADS="/proj/cs620426sp-PG0/ycsb_workloads"
if ssh $SSH_OPTS "$MASTER_NODE" "[ -d '$NFS_WORKLOADS' ]" 2>/dev/null; then
    log "  NFS workloads found at $NFS_WORKLOADS — symlinking on all nodes"
    bash "$CHIME_ROOT/script/run-on-nodes.sh" "$HEALTHY_CSV" \
        "ln -sfn $NFS_WORKLOADS ~/CHIME/ycsb/workloads"
else
    log "  WARNING: NFS workloads not found at $NFS_WORKLOADS"
    log "  You'll need to generate workloads manually on each node."
    log "  Run: bash script/run-on-nodes.sh \"\$NODES\" \"cd ~/CHIME/ycsb && bash generate_full_workloads.sh\""
fi

# Check disk space on master
ROOT_FREE=$(ssh $SSH_OPTS "$MASTER_NODE" "df --output=avail / | tail -1" 2>/dev/null)
ROOT_FREE_GB=$((ROOT_FREE / 1024 / 1024))
if [ "$ROOT_FREE_GB" -lt 50 ]; then
    log "  WARNING: Root partition has only ${ROOT_FREE_GB}GB free."
    log "  Consider mounting NVMe for additional storage."
fi

log "Phase 5 complete."
log ""

# ======================================================================
# Phase 6: Smoke Test (5 min)
# ======================================================================
log "Phase 6/7: Running smoke test (CHIME, 1 CN + 1 MN, YCSB C)..."
cd "$CHIME_ROOT/exp"

if python3 smoke_test.py; then
    log "Smoke test PASSED."
else
    log "FATAL: Smoke test FAILED. Check RDMA connectivity and memcached."
    log "  Debug: ssh $MASTER_NODE 'cd ~/CHIME/exp && python3 smoke_test.py'"
    exit 1
fi

cd "$CHIME_ROOT"

log ""
log "============================================================"
log "  SETUP COMPLETE: ${CN_COUNT} CN + 1 MN on r650 at Clemson"
log "  Healthy nodes: $HEALTHY_FILE"
log "  common.json:   exp/params/common.json"
log "============================================================"
log ""
log "Next steps:"
log "  1. Start rsync backup (from laptop):"
log "     MASTER=\"$(whoami)@$MASTER_NODE\" bash scripts/rsync-results.sh"
log ""
log "  2. Start experiments (in tmux on master):"
log "     cd ~/CHIME/exp && python3 resilient_runner.py"
log ""
log "  3. Or run individual experiments:"
log "     cd ~/CHIME/exp && python3 fig_12.py"

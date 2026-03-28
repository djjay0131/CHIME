# Feature: RDMA r650 11-Node Production Run

**Status:** VERIFIED
**Date:** 2026-03-26
**Author:** Feature Architect (AI-assisted)

## Problem

The r6525 pre-deadline run (Mar 23-26) produced CHIME experiment results on non-paper-matched hardware (AMD EPYC 64 cores vs Intel Xeon 72 cores). These results cannot be directly compared to the paper's figures. Two approved r650 reservations at Clemson — 10 nodes (Mar 27-Apr 3) and 11 nodes (Apr 3-6) — provide the opportunity to reproduce all core figures on paper-matched Intel hardware. Additionally, mid/late April reservations are needed for CXL NUMA emulation runs (Part Two).

The r6525 run exposed multiple setup issues (broken RDMA nodes, disk space, memcached IP, YCSB compatibility) that were fixed manually. This run needs a unified, automated setup script that handles the full pipeline, pre-flight validation that catches bad nodes before experiments start, and a resilient experiment runner that never silently hangs or wastes hours on failures.

## Goals

- Unified `setup-r650.sh` script: SSH keys → OFED → libs → hugepages → repos → builds → workloads → smoke test in one command
- Pre-flight validation: RDMA health check on every node, automatic exclusion of bad nodes, minimum CN threshold
- Resilient experiment runner: per-experiment timeout, retry on failure, cleanup on hang, incremental result backup
- All 4 core figures (12, 14, 15a, 15b) reproduced on r650 hardware
- Extra experiments (cache sensitivity, value size, distribution) if time permits
- Results parsed, figures generated, LaTeX report updated with r650 data
- CloudLab reservations created for mid/late April CXL NUMA emulation runs
- Beamer presentation updated with r650 figures for Apr 7-9 delivery

## Non-Goals

- Modifying experiment scripts' core logic (only wrapping with resilience)
- CXL implementation (separate spec: `cxl-implementation.md`)
- Running experiments on r6525 again (already done)
- Marlin experiments (not needed for core figures)
- Changing CHIME's index algorithm or CMake flags beyond hardware-specific patches

## User Stories

- As a PhD student, I want a one-command setup so that I don't waste hours of reservation time on manual configuration.
- As a researcher, I want pre-flight validation so that broken nodes are caught before the 7.5-hour fig_12 run starts.
- As a student with limited CloudLab time, I want resilient experiment execution so that a single failure doesn't waste my reservation window.
- As a course presenter, I want r650 figures in my Beamer slides so that my results match the paper's hardware.

## Design Approach

### Architecture: Three-Layer Automation

```
┌─────────────────────────────────────────────────┐
│  Layer 3: Report & Presentation Pipeline        │
│  parse results → generate figures → update LaTeX│
├─────────────────────────────────────────────────┤
│  Layer 2: Resilient Experiment Runner           │
│  timeout → retry → checkpoint → rsync backup    │
├─────────────────────────────────────────────────┤
│  Layer 1: Unified Setup Script                  │
│  SSH → OFED → libs → hugepages → repos →        │
│  builds → workloads → common.json → smoke test  │
└─────────────────────────────────────────────────┘
```

### Layer 1: Unified Setup Script (`setup-r650.sh`)

**Input:** `nodes.txt` file (one hostname per line), master node hostname
**Output:** Fully configured cluster ready for experiments

**Phases (sequential, ~40 min total):**

1. **SSH Keys** (2 min): Distribute keys via `setKey.py`
2. **Parallel Node Setup** (15 min): On all nodes simultaneously:
   - Install MLNX OFED (`installMLNX.sh`)
   - Install libraries (`installLibs.sh`)
   - Configure hugepages (36864 pages)
   - Set `ulimit -l unlimited`
3. **Pre-flight Validation** (5 min): Two-stage RDMA health check
   - **Stage 1**: `ibv_devinfo` on each node — verify NIC is `PORT_ACTIVE`
   - **Stage 2**: Pairwise RDMA connectivity test (`ib_read_lat` between master and each node) — catches subtler failures like node10 on r6525 where NIC was "active" but RDMA was broken
   - Healthy nodes added to cluster; failed nodes excluded
   - **Hard fail if < 5 CN** (minimum viable cluster)
   - Log healthy/failed node list for operator awareness
4. **Repos + Builds** (10 min): On all healthy nodes:
   - Clone sibling repos (SMART, ROLEX) if not present
   - Patch `CPU_PHYSICAL_CORE_NUM` to 72 (r650) in all repos
   - Default CHIME build only (validates toolchain); method-specific builds with correct CMake flags from `common.json` are handled by experiment scripts at runtime
5. **Configuration** (5 min):
   - Generate `common.json` from healthy node IPs
   - Patch fig params CN count to match actual healthy CN count
   - Symlink YCSB workloads from project NFS (`/proj/cs620426sp-PG0/ycsb_workloads/`)
   - Update `memcached.conf` with master IP
6. **Smoke Test** (5 min): Run `smoke_test.py` (1 CN + 1 MN, YCSB C)
   - Must produce throughput > 0
   - **Hard fail if smoke test fails** — don't waste time on broken cluster

### Layer 2: Resilient Experiment Runner (`resilient_runner.py`)

**Design principles:**
- Never silently hang — every experiment has a timeout
- Never waste time on repeated failures — max 2 retries per experiment
- Never lose data — incremental rsync after each completed experiment
- Run the most important experiment first — fig_12 (primary result) before supplementary figures
- Checkpoint-based resume — fig_12 retries skip already-completed (method, workload, client_count) triples
- Intelligent failure classification — transient vs systemic, with different responses

**Execution order:**

| Priority | Experiment | Expected Runtime | Timeout | Purpose |
|----------|-----------|-----------------|---------|---------|
| 1 | fig_12 | 7.5 hours | 9 hours | **Primary result** (throughput-latency) — monitored by watchdog agent |
| 2 | fig_15b | 40 min | 50 min | ROLEX ablation |
| 3 | fig_15a | 44 min | 55 min | Sherman ablation |
| 4 | fig_14 | 35 min | 45 min | Cache consumption |
| 5 | extra_cache_sensitivity | ~30 min | 45 min | Stretch: cache size sweep |
| 6 | extra_value_size | ~30 min | 45 min | Stretch: value size scaling |
| 7 | extra_uniform_dist | ~30 min | 45 min | Stretch: distribution comparison |
| 8 | fig_03a | 23 min | 35 min | Stretch: trade-off curve |

**Watchdog agent (monitors fig_12):**
- Polls experiment progress every 5 minutes (checks `_partial.json` for new data points)
- Detects stalls: if no new data point after 2x expected interval, investigate
- Classifies failures:
  - **Transient** (single data point timeout, ycsb_test crash on one node): kill, retry that data point
  - **Systemic** (node unreachable, RDMA error on a node): exclude failed node, re-patch CN count, restart memcached, resume from checkpoint
- Sends notification on failure detection (log + optional alert)

**Checkpoint-based resume (fig_12):**
- On retry, load `exp/results/fig_12_*_partial.json`
- Parse existing data: each (method, workload) key with N entries means N client_count configurations are done
- Compare against expected configurations from `exp/params/fig_12.json`
- Skip completed triples, continue from first missing combination
- Same logic applies to other long-running experiments if needed

**Per-experiment flow:**
1. Log start time and experiment name
2. Launch `python3 fig_*.py` with `subprocess.run(timeout=...)`
3. For fig_12: watchdog agent monitors in parallel
4. On success: log completion, rsync results to local machine
5. On transient failure: cleanup, retry with checkpoint resume
6. On systemic failure: exclude bad node, reconfigure cluster, retry with checkpoint resume
7. On timeout: kill `ycsb_test` processes on all nodes, classify failure, retry or skip
8. After max retries: skip experiment, continue to next
9. Print summary table at end

**Incremental backup:**
- After each successful experiment, rsync `exp/results/` to local machine
- `rsync-results.sh` also runs in background every 5 minutes as safety net

### Layer 3: Report & Presentation Pipeline

**After experiments complete:**

1. **Parse results**: Verify all JSON result files exist in `exp/results/`
2. **Generate figures**: Run each `fig_*.py` plotting phase (or `pic_generator.py` directly)
3. **Compare with paper**: Side-by-side visual comparison, note discrepancies
4. **Update LaTeX report** (`report/main.tex`):
   - Replace r6525 figures with r650 figures
   - Update experimental setup section (r650 hardware specs)
   - Add comparison analysis (r6525 vs r650 if both datasets available)
5. **Update Beamer presentation** (`presentation/main.tex`):
   - Insert r650 figures
   - Update hardware description slides
6. **Build PDFs**: Verify LaTeX compilation, push to GitHub Pages

### CloudLab Reservations for CXL Runs

Create two small reservations for Part Two CXL NUMA emulation. CXL runs on a single dual-socket r650 node (NUMA node 0 = compute, NUMA node 1 = "CXL memory") — no multi-node cluster needed. RDMA baseline data comes from the Mar 27-Apr 6 runs.

| Reservation | Nodes | Hardware | Dates | Purpose |
|-------------|-------|----------|-------|---------|
| Mid-April | 1-2x r650 | Dual-socket Xeon | Apr 14-18 | CXL transport dev/debug (1 node for NUMA emulation, 1 spare) |
| Late-April | 1-2x r650 | Dual-socket Xeon | Apr 21-28 | Full CXL comparison run (all 5 methods on NUMA emulation) |

## Sample Implementation

```bash
#!/bin/bash
# setup-r650.sh — Unified Day 1 setup for r650 cluster
# Usage: ./setup-r650.sh <nodes_file> <master_node>
set -euo pipefail

NODES_FILE="$1"
MASTER="$2"
ALL_NODES=($(cat "$NODES_FILE"))
NODE_COUNT=${#ALL_NODES[@]}
HEALTHY_NODES=()

log() { echo "[$(date '+%H:%M:%S')] $*"; }

# ---- Phase 1: SSH Keys (2 min) ----
log "Phase 1/6: Distributing SSH keys..."
NODES_FILE="$NODES_FILE" python3 script/setKey.py

# ---- Phase 2: Parallel Setup (15 min) ----
log "Phase 2/6: OFED + libs + hugepages on all nodes..."
for node in "${ALL_NODES[@]}"; do
  ssh -o ConnectTimeout=10 "$node" "
    cd ~/CHIME/script &&
    bash installMLNX.sh &&
    bash installLibs.sh &&
    echo 36864 | sudo tee /proc/sys/vm/nr_hugepages &&
    sudo bash -c 'ulimit -l unlimited'
  " &
done
wait

# ---- Phase 3: Pre-flight Validation (5 min) ----
log "Phase 3/6: Validating RDMA on every node..."
MASTER_NODE="${ALL_NODES[0]}"

for node in "${ALL_NODES[@]}"; do
  # Stage 1: Check NIC status
  if ! ssh "$node" "ibv_devinfo 2>/dev/null | grep -q 'state.*PORT_ACTIVE'"; then
    log "  FAIL $node — ibv_devinfo: NIC not active (excluding)"
    continue
  fi

  # Stage 2: Pairwise RDMA connectivity (ib_read_lat from master)
  if [ "$node" != "$MASTER_NODE" ]; then
    # Start server on target node, run client from master
    ssh "$node" "timeout 10 ib_read_lat -d mlx5_0 &>/dev/null &"
    sleep 1
    if ssh "$MASTER_NODE" "timeout 10 ib_read_lat -d mlx5_0 $node -n 10 &>/dev/null"; then
      HEALTHY_NODES+=("$node")
      log "  OK $node — RDMA active + connectivity verified"
    else
      log "  FAIL $node — RDMA connectivity test failed (excluding)"
    fi
    ssh "$node" "killall ib_read_lat 2>/dev/null || true"
  else
    HEALTHY_NODES+=("$node")
    log "  OK $node — master node (RDMA NIC active)"
  fi
done

CN_COUNT=$(( ${#HEALTHY_NODES[@]} - 1 ))
log "Healthy: ${#HEALTHY_NODES[@]} nodes -> ${CN_COUNT} CN + 1 MN"
if [ "$CN_COUNT" -lt 5 ]; then
  log "FATAL: Need at least 5 CN. Only $CN_COUNT healthy. Aborting."
  exit 1
fi

# ---- Phase 4: Repos + Builds (10 min) ----
log "Phase 4/6: Cloning repos + patching + building..."
HEALTHY_CSV=$(printf '%s,' "${HEALTHY_NODES[@]}" | sed 's/,$//')
bash script/run-on-nodes.sh "$HEALTHY_CSV" \
  "cd ~ && [ -d SMART ] || bash ~/CHIME/script/clone-repos.sh"

# Patch CPU_PHYSICAL_CORE_NUM to 72 (r650 = 2x36 cores)
bash script/run-on-nodes.sh "$HEALTHY_CSV" \
  "sed -i 's/CPU_PHYSICAL_CORE_NUM [0-9]*/CPU_PHYSICAL_CORE_NUM 72/' \
   ~/CHIME/include/Common.h ~/SMART/include/Common.h ~/ROLEX/include/Common.h"

# Default CHIME build only — validates toolchain (libs, headers, CMake)
# Method-specific builds (with correct cmake_options from common.json) are
# handled by each fig_*.py experiment script at runtime
bash script/run-on-nodes.sh "$HEALTHY_CSV" \
  "cd ~/CHIME && mkdir -p build && cd build && cmake .. && make -j"

# ---- Phase 5: Config + Workloads (5 min) ----
log "Phase 5/6: Generating config and linking workloads..."
python3 construction/scripts/generate-common-json.py \
  --home "/users/$(whoami)" \
  --master "$MASTER" \
  --ips "$(printf '%s,' "${HEALTHY_NODES[@]}" | sed 's/,$//')" \
  --out exp/params/common.json

python3 construction/scripts/patch-cn-count.py "$CN_COUNT"

bash script/run-on-nodes.sh "$HEALTHY_CSV" \
  "ln -sfn /proj/cs620426sp-PG0/ycsb_workloads ~/CHIME/ycsb/workloads"

# ---- Phase 6: Smoke Test (5 min) ----
log "Phase 6/6: Smoke test..."
cd exp && python3 smoke_test.py
log "=== SETUP COMPLETE: ${CN_COUNT} CN + 1 MN on r650 ==="
```

```python
# resilient_runner.py — Experiment runner with timeout/retry/checkpoint

import subprocess, sys, time, os, signal

EXPERIMENTS = [
    ("fig_12",                9 * 3600),  # 9 hour timeout — PRIMARY, run first
    ("fig_15b",               50 * 60),   # 50 min timeout
    ("fig_15a",               55 * 60),   # 55 min timeout
    ("fig_14",                45 * 60),   # 45 min timeout
    ("extra_cache_sensitivity", 45 * 60),
    ("extra_value_size",      45 * 60),
    ("extra_uniform_dist",    45 * 60),
    ("fig_03a",               35 * 60),
]
MAX_RETRIES = 2
RSYNC_TARGET = os.environ.get("RSYNC_TARGET", "")  # user@laptop:path

def cleanup_cluster():
    """Kill any hanging ycsb_test processes on all nodes."""
    subprocess.run(["bash", "../script/run-on-nodes.sh",
                    os.environ.get("HEALTHY_NODES", ""),
                    "killall -9 ycsb_test 2>/dev/null || true"],
                   timeout=30, capture_output=True)

def rsync_results():
    """Incremental backup of results to local machine."""
    if RSYNC_TARGET:
        subprocess.run(["rsync", "-az", "results/", RSYNC_TARGET],
                       timeout=60, capture_output=True)

def run_experiment(name, timeout_sec):
    for attempt in range(1, MAX_RETRIES + 1):
        ts = time.strftime('%H:%M')
        print(f"[{ts}] {name} — attempt {attempt}/{MAX_RETRIES}")
        try:
            result = subprocess.run(
                ["python3", f"{name}.py"],
                timeout=timeout_sec,
                capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f"  OK {name} completed")
                rsync_results()
                return True
            else:
                print(f"  FAIL {name} (rc={result.returncode})")
                print(f"    {result.stderr[-300:]}")
        except subprocess.TimeoutExpired:
            print(f"  TIMEOUT {name} after {timeout_sec // 60}m")
            cleanup_cluster()
    print(f"  SKIP {name} after {MAX_RETRIES} attempts")
    return False

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    results = {}
    for name, timeout in EXPERIMENTS:
        results[name] = run_experiment(name, timeout)

    print("\n=== EXPERIMENT SUMMARY ===")
    for name, ok in results.items():
        status = "OK" if ok else "FAILED"
        print(f"  [{status}] {name}")

    failed = [n for n, ok in results.items() if not ok]
    if failed:
        print(f"\n{len(failed)} experiments failed: {', '.join(failed)}")
        sys.exit(1)
```

## Edge Cases & Error Handling

### EC-1: Multiple Nodes Fail RDMA Pre-flight
- **Scenario**: 3+ of 10 r650 nodes have broken RDMA, leaving < 7 CN
- **Behavior**: Setup script continues with healthy nodes if >= 5 CN; patches CN count accordingly; logs which nodes failed
- **Test**: Manually disable RDMA on 1 node before setup; verify it's excluded and experiments run on remaining nodes

### EC-2: fig_12.py Crashes Mid-Run (4 hours in) — Transient Failure
- **Scenario**: Single data point times out or ycsb_test crashes on one node during the 7.5-hour fig_12 run
- **Behavior**: Watchdog detects stall (no new data point in `_partial.json` after 2x expected interval). Kills ycsb_test, loads `_partial.json`, identifies completed (method, workload, client_count) triples, resumes from first missing combination. No data lost.
- **Test**: Kill ycsb_test on one node mid-run; verify watchdog detects, retries, and partial results are preserved

### EC-2b: Node Goes Down Mid-Run — Systemic Failure
- **Scenario**: A node becomes unreachable (hardware failure, RDMA error) during fig_12
- **Behavior**: Watchdog detects node unreachable via SSH probe. Excludes failed node from cluster. Re-patches CN count (`patch-cn-count.py` with N-1). Restarts memcached. Resumes fig_12 from checkpoint with reduced cluster. Logs the reconfiguration.
- **Test**: Manually disconnect one node mid-experiment; verify watchdog reconfigures and resumes

### EC-3: NFS Workload Path Unavailable
- **Scenario**: Project NFS `/proj/cs620426sp-PG0/ycsb_workloads/` not mounted or path changed on r650
- **Behavior**: Setup script checks NFS symlink target exists; if not, falls back to local workload generation (slow but works)
- **Test**: Setup on a node without NFS; verify fallback path triggers

### EC-4: Reservation Expires Mid-Experiment
- **Scenario**: Apr 3 reservation ends while fig_12 is still running
- **Behavior**: rsync backup running every 5 min ensures partial results are saved to local machine. Remaining experiments deferred to Apr 3-6 re-run.
- **Test**: Check rsync cron is active; verify results exist locally after sync

### EC-5: common.json IP Resolution Fails
- **Scenario**: CloudLab node hostnames don't resolve to expected IPs (different subnet on r650 vs r6525)
- **Behavior**: `generate-common-json.py` resolves hostnames to IPs at generation time; pre-flight validates memcached connectivity before experiments start
- **Test**: Smoke test verifies end-to-end connectivity

### EC-6: Disk Space on r650
- **Scenario**: r650 may have different partition layout than r6525 (which had 16GB root)
- **Behavior**: Setup script checks available disk space; if root < 50GB, mounts NVMe or warns operator
- **Test**: `df -h /` check in setup script

## Acceptance Criteria

### AC-1: Unified Setup Completes in Under 45 Minutes
- **Given** a fresh 10-11 node r650 CloudLab experiment with `nodes.txt`
- **When** running `./setup-r650.sh nodes.txt <master>`
- **Then** all phases complete, smoke test passes, and the cluster is experiment-ready

### AC-2: Pre-flight Catches Bad Nodes
- **Given** a cluster where 1+ nodes have broken RDMA
- **When** setup script runs pre-flight validation
- **Then** bad nodes are excluded, CN count is patched, and remaining nodes are fully functional

### AC-3: Core Figures Produced on r650
- **Given** a healthy r650 cluster after setup
- **When** `resilient_runner.py` completes
- **Then** JSON results and PDF figures exist in `exp/results/` for fig_12, fig_14, fig_15a, fig_15b

### AC-4: No Silent Hangs
- **Given** an experiment that hangs or times out
- **When** the timeout fires in resilient_runner
- **Then** ycsb_test processes are killed, the experiment is retried or skipped, and the runner proceeds to the next experiment

### AC-5: Incremental Backup
- **Given** experiments running on the cluster
- **When** any experiment completes successfully
- **Then** results are rsynced to the local machine within 5 minutes

### AC-6: LaTeX Report Updated with r650 Data
- **Given** r650 experiment results parsed and figures generated
- **When** the report pipeline completes
- **Then** `report/main.tex` contains r650 figures, updated hardware description, and r6525-vs-r650 comparison (if applicable)

### AC-7: Beamer Presentation Ready
- **Given** r650 figures available
- **When** presentation is updated
- **Then** `presentation/main.tex` contains r650 figures and is ready for Apr 7-9 delivery

### AC-8: CXL Reservations Created
- **Given** Part Two requires NUMA emulation runs on r650
- **When** reservations are submitted via portal-cli
- **Then** two reservations exist: mid-April (1-2x r650, dev/debug) and late-April (1-2x r650, full CXL run)

## Technical Notes

- **Affected components**: `construction/scripts/setup-r650.sh` (new), `exp/resilient_runner.py` (new), `exp/params/common.json` (regenerated per cluster), `exp/params/fig_*.json` (CN count patched), `report/main.tex`, `presentation/main.tex`
- **Patterns to follow**: Existing `day1-dry-run.sh` modular setup pattern; `run-on-nodes.sh` for parallel SSH; `patch-cn-count.py` for CN count adjustment; `generate-common-json.py` for config generation
- **Hardware-specific patches**: `CPU_PHYSICAL_CORE_NUM=72` for r650 (was 64 for r6525); memcached IP from hostname resolution (not hardcoded)
- **Workload reuse**: YCSB workloads on project NFS — no regeneration needed, just symlink
- **Build note**: r650 builds should use same CMake flags as r6525 run (only `CPU_PHYSICAL_CORE_NUM` differs)

## Timeline

### Mar 27 (Day 1): Setup + Quick Experiments

| Time | Activity | Duration |
|------|----------|----------|
| 17:00 UTC | Reservation starts; run `setup-r650.sh` | 45 min |
| 17:45 | Verify setup; start `resilient_runner.py` in tmux | 5 min |
| 17:50 | fig_12 starts (primary result, monitored by watchdog agent) | 7.5 hours |

### Mar 28 (Day 2): Verify + Extras

| Time | Activity | Duration |
|------|----------|----------|
| 01:20 UTC | fig_12 completes; fig_15b/15a/14 run automatically (~2h) | ~2 hours |
| 03:20 UTC | Core complete; extras begin automatically | ~1.5 hours |
| Morning | Verify all results; rsync to local | 30 min |
| Afternoon | Parse results, generate final figures | 2 hours |

### Mar 29-31: Report + Presentation

| Day | Activity |
|-----|----------|
| Mar 29 | Update LaTeX report with r650 figures; write comparison analysis |
| Mar 30 | Update Beamer presentation; rehearse |
| Mar 31 | Buffer for any re-runs or figure polish |

### Apr 3-6: Re-Run (11 nodes, 10 CN + 1 MN)

| Day | Activity |
|-----|----------|
| Apr 3 | Setup 11-node cluster; run setup-r650.sh; patch CN to 10 |
| Apr 4 | Run full experiment suite with 10 CN (paper-matched CN count) |
| Apr 5 | Parse results; generate definitive figures |
| Apr 6 | Final report/presentation updates |

### Apr 7-9: Presentation Delivered

### Mid-Late April: CXL Reservations

| Reservation | Dates | Nodes | Purpose |
|-------------|-------|-------|---------|
| CXL dev | Apr 14-18 | 1-2x r650 | NUMA emulation development and debugging |
| CXL full | Apr 21-28 | 1-2x r650 | Full CXL comparison run (all 5 methods, single-node NUMA emulation) |

## Dependencies

- CloudLab r650 reservation 1cf9c2b4 (10x r650, Mar 27-Apr 3) — APPROVED
- CloudLab r650 reservation 5488ef67 (11x r650, Apr 3-6) — APPROVED
- CXL reservations (mid/late April) — TO BE CREATED
- Project NFS `/proj/cs620426sp-PG0/ycsb_workloads/` accessible from Clemson r650 nodes
- r6525 results (completed Mar 23-26) as comparison baseline
- `portal-cli` configured with valid JWT for reservation creation

## Open Questions

- **r650 OFED version**: r650 may ship with a different MLNX OFED version than r6525. If `installMLNX.sh` fails, may need to adjust the script or use the pre-installed version.
- **r650 disk layout**: Need to verify whether r650 at Clemson has the same 16GB root partition issue as r6525, or if it has larger root storage. Affects whether NVMe mount is needed.
- **Thread count adjustment for r650**: r650 has 72 physical cores (vs 64 on r6525). Should `fig_12.json` thread counts be adjusted to go up to 72 threads/CN instead of 64? Paper uses up to 64 threads/CN on r650 — likely keep at 64 for consistency with paper.
- **Watchdog agent implementation**: Should the watchdog be a separate Python process, a background thread in `resilient_runner.py`, or a Claude Code agent monitoring via SSH? Needs to be lightweight enough to not interfere with experiments.
- **9 CN presentation strategy**: Mar 27-Apr 3 run has 9 CN (reservation mistake). Present with footnote explaining discrepancy. If Apr 3-6 re-run (10 CN) produces data before Apr 7, swap in those figures.
- **`ib_read_lat` availability**: Need to verify `ib_read_lat` is installed on r650 nodes (part of `perftest` package). If not, add to `installLibs.sh`.

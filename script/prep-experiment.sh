#!/usr/bin/env bash
# prep-experiment.sh — Make a fresh CloudLab experiment ready for CHIME runs.
#
# Steps (idempotent — safe to re-run):
#   1. Probe nodes via portal-cli manifests, build a nodes file
#   2. Distribute SSH key from master (node0) to all peers
#   3. Verify MLNX OFED + RDMA NIC active on every node
#   4. Set hugepages on each node
#         RDMA mode (default): 36864 on NUMA node1, 0 on node0
#         CXL mode (--cxl):    36864 on node0,        0 on node1   (deprecated; CHIME's CXL pool binds to node1 anyway)
#   5. Memcached: kill any running, start fresh on master, init counters
#   6. Confirm both interfaces (control + internal) and start the
#      control-net guard on every node, in the background, writing to /proj
#   7. Pre-stage the project repo on /proj NFS (idempotent git pull)
#   8. Print a summary and the path to the guard logs
#
# Usage:
#   bash script/prep-experiment.sh <experiment-name> [--cxl]
#
# Requires:
#   .venv/bin/portal-cli
#   files/cloudlab.jwt
set -u

cd "$(dirname "$0")/.."

EXP_NAME="${1:?usage: prep-experiment.sh <experiment-name> [--cxl]}"
shift || true
CXL_MODE=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        --cxl) CXL_MODE=1; shift ;;
        *) echo "unknown arg: $1" >&2; exit 1 ;;
    esac
done

JWT_FILE="${CLOUDLAB_JWT:-files/cloudlab.jwt}"
PORTAL_URL="${CLOUDLAB_PORTAL_URL:-https://boss.emulab.net:43794}"
PROJECT="${CLOUDLAB_PROJECT:-CS620426SP}"
PROJ_NFS="${PROJ_NFS:-/proj/cs620426sp-PG0}"
GUARD_DIR="$PROJ_NFS/guard-logs"
NODES_FILE="construction/scripts/nodes.txt"

run_portal() {
    .venv/bin/portal-cli --portal-url "$PORTAL_URL" --token "$(cat "$JWT_FILE")" "$@"
}

log() { echo "[$(date -u +%H:%M:%S)] $*"; }

# ---- 1. Find experiment id from name ----
log "step 1/8: lookup experiment '$EXP_NAME'"
exps_json=$(run_portal experiment list 2>/dev/null)
EXP_ID=$(echo "$exps_json" | python3 -c "
import sys, json
d = json.load(sys.stdin)
for e in d.get('experiments', []):
    if e.get('name') == '$EXP_NAME':
        print(e['id']); break
")
if [[ -z "$EXP_ID" ]]; then
    log "no experiment named '$EXP_NAME' found. Active experiments:"
    echo "$exps_json" | python3 -c "import sys,json;[print(e['name']) for e in json.load(sys.stdin).get('experiments',[])]"
    exit 1
fi
log "  id=$EXP_ID"

# ---- 2. Pull manifests, build nodes file ----
log "step 2/8: pull manifests, build nodes file"
manifest=$(run_portal experiment manifests get --experiment-id "$EXP_ID" 2>/dev/null)
mkdir -p "$(dirname "$NODES_FILE")"
echo "$manifest" | python3 -c "
import sys, json, re
d = json.load(sys.stdin)
xml = ''.join(d.values())
hosts = re.findall(r'<host name=\"([^\"]+)\"', xml)
print('\n'.join(hosts))
" > "$NODES_FILE"
NODE_COUNT=$(wc -l < "$NODES_FILE")
MASTER=$(head -1 "$NODES_FILE")
log "  $NODE_COUNT nodes; master=$MASTER"

# ---- 3. Distribute SSH key ----
log "step 3/8: distribute SSH key from master to peers"
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$MASTER" \
    "test -f ~/.ssh/id_rsa || ssh-keygen -t rsa -N '' -f ~/.ssh/id_rsa -q; cat ~/.ssh/id_rsa.pub" \
    > /tmp/master.pub.tmp
PUB=$(cat /tmp/master.pub.tmp)
while read -r node; do
    if [[ "$node" == "$MASTER" ]]; then continue; fi
    ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$node" \
        "grep -qF '$PUB' ~/.ssh/authorized_keys 2>/dev/null || echo '$PUB' >> ~/.ssh/authorized_keys; chmod 600 ~/.ssh/authorized_keys"
done < "$NODES_FILE"
log "  done"

# ---- 4. Verify OFED + NIC active ----
log "step 4/8: verify MLNX OFED + active NIC"
while read -r node; do
    state=$(ssh -o StrictHostKeyChecking=no "$node" \
        "ofed_info -s 2>/dev/null | head -1; ibv_devinfo 2>/dev/null | grep -E 'state|active_mtu' | head -2")
    log "  $node: ${state//$'\n'/ | }"
done < "$NODES_FILE"

# ---- 5. Hugepages ----
log "step 5/8: set hugepages (rdma mode: node1=36864 node0=0)"
NODE0_HP=0; NODE1_HP=36864
if (( CXL_MODE == 1 )); then
    log "  CXL mode requested but CHIME's CxlTransport binds to NUMA node1 anyway; using rdma layout"
fi
while read -r node; do
    ssh -o StrictHostKeyChecking=no "$node" "
        echo $NODE0_HP | sudo tee /sys/devices/system/node/node0/hugepages/hugepages-2048kB/nr_hugepages > /dev/null
        echo $NODE1_HP | sudo tee /sys/devices/system/node/node1/hugepages/hugepages-2048kB/nr_hugepages > /dev/null
    "
done < "$NODES_FILE"

# ---- 6. memcached ----
log "step 6/8: restart memcached on master and init counters"
INTERNAL_IP=$(ssh -o StrictHostKeyChecking=no "$MASTER" "ip addr show vlan296 2>/dev/null | awk '/inet /{print \$2}' | cut -d/ -f1")
log "  master internal IP: $INTERNAL_IP"
ssh -o StrictHostKeyChecking=no "$MASTER" "
    pkill memcached 2>/dev/null; sleep 1
    memcached -u root -l $INTERNAL_IP -p 11211 -c 10000 -d -P /tmp/memcached.pid
    sleep 1
    printf 'set serverNum 0 0 1\r\n0\r\nquit\r\n' | nc $INTERNAL_IP 11211 > /dev/null
    printf 'set clientNum 0 0 1\r\n0\r\nquit\r\n' | nc $INTERNAL_IP 11211 > /dev/null
"
ssh -o StrictHostKeyChecking=no "$MASTER" "echo -n '$INTERNAL_IP' > $PROJ_NFS/djjay-build/memcached.conf; echo; echo 11211 >> $PROJ_NFS/djjay-build/memcached.conf"
ssh -o StrictHostKeyChecking=no "$MASTER" "head $PROJ_NFS/djjay-build/memcached.conf"

# ---- 7. Start control-net guard on every node ----
log "step 7/8: launch control-net guard on every node"
mkdir_p_remote_done=0
ssh -o StrictHostKeyChecking=no "$MASTER" "mkdir -p $GUARD_DIR" && mkdir_p_remote_done=1
SCRIPT_REMOTE="$GUARD_DIR/control-net-guard.sh"
scp -o StrictHostKeyChecking=no script/control-net-guard.sh "$MASTER:$SCRIPT_REMOTE" > /dev/null
while read -r node; do
    short=$(echo "$node" | cut -d. -f1)
    LOG="$GUARD_DIR/${short}.log"
    TRIPPED="$GUARD_DIR/${short}.tripped"
    ssh -o StrictHostKeyChecking=no "$node" "
        chmod +x $SCRIPT_REMOTE
        pkill -f control-net-guard.sh 2>/dev/null
        nohup bash $SCRIPT_REMOTE --interval 30 --threshold 5242880 \
              --logfile $LOG --tripped-file $TRIPPED \
              --max-public-bytes-total 524288000 \
              > /dev/null 2>&1 < /dev/null & disown
    " &
done < "$NODES_FILE"
wait
log "  guard logs in $GUARD_DIR/"

# ---- 8. Pre-stage repo on master ----
log "step 8/8: ensure CHIME repo present on master"
ssh -o StrictHostKeyChecking=no "$MASTER" "
    if [ ! -d ~/CHIME ]; then
        git clone https://github.com/djjay0131/CHIME.git ~/CHIME 2>&1 | tail -3
    else
        cd ~/CHIME && git fetch -q origin && git reset -q --hard origin/main
    fi
    cd ~/CHIME && git log --oneline -3
"

log "DONE. Next steps:"
echo "  - run experiments via:  bash script/run-with-guard.sh -- <ycsb_test cmd>"
echo "  - watch guard logs:     tail -f $GUARD_DIR/*.log"
echo "  - status:               bash script/cloudlab-status-watch.sh"

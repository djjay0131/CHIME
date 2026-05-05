#!/usr/bin/env bash
# tonight-launch.sh — One-shot launch script for the May 6 01:00 UTC reservation.
#
# This script is invoked by a CronCreate one-shot at 01:02 UTC May 6.
# It performs steps 1–5 of the runbook:
#   1. Create experiment via portal-cli (or note that user must use web UI).
#   2. Poll until SSH on master responds (timeout 25 min).
#   3. Distribute SSH keys inline.
#   4. Write nodes.txt on master.
#   5. Dispatch bootstrap-node.sh on all 7 nodes in parallel.
#
# Output goes to /tmp/may6-launch.log on the laptop.
# When the script exits, the user-facing summary tells the user / Claude
# whether to proceed to the atomic-cap-fix step (12-min wakeup).
set -u

cd "$(dirname "$0")/.."

JWT_FILE="${CLOUDLAB_JWT:-files/cloudlab.jwt}"
PORTAL_URL="${CLOUDLAB_PORTAL_URL:-https://boss.emulab.net:43794}"
EXP_NAME="${EXP_NAME:-chime-r650-may6}"
N="${N:-7}"
LOG=/tmp/may6-launch.log
SSH_OPTS="-o ConnectTimeout=10 -o BatchMode=yes -o StrictHostKeyChecking=no"

log() { printf '[%s] %s\n' "$(date -u +%FT%TZ)" "$*" | tee -a $LOG; }

run_portal() {
    .venv/bin/portal-cli --portal-url "$PORTAL_URL" --token "$(cat "$JWT_FILE")" "$@"
}

log "=== May 6 launch begin ==="

# Step 1: create experiment
log "Step 1/5: create experiment '$EXP_NAME' with n=$N"
out=$(timeout 60 bash script/launch-experiment.sh "$EXP_NAME" "$N" 2>&1)
echo "$out" >> $LOG
EXP_ID=$(echo "$out" | grep -oE '"id":\s*"[a-f0-9-]{36}"' | head -1 | grep -oE '[a-f0-9-]{36}')
if [[ -z "$EXP_ID" ]]; then
    log "ERROR: experiment create failed via portal-cli. User must launch via web UI:"
    log "  https://www.cloudlab.us/p/CS620426SP/chime-r650-clemson-lan"
    log "  Set n=$N and name '$EXP_NAME', then notify Claude when status=ready."
    exit 1
fi
log "Experiment id: $EXP_ID"

# Step 2: poll for SSH on master
log "Step 2/5: poll for SSH on master (up to 25 min)"
MASTER="node0.${EXP_NAME}.cs620426sp-PG0.clemson.cloudlab.us"
for i in $(seq 1 25); do
    if ssh $SSH_OPTS "$MASTER" "true" 2>/dev/null; then
        log "  master SSH up after $i probes"
        break
    fi
    sleep 60
done
if ! ssh $SSH_OPTS "$MASTER" "true" 2>/dev/null; then
    log "ERROR: master SSH never came up. Aborting."
    exit 2
fi

# Step 3: distribute SSH keys inline
log "Step 3/5: distribute SSH keys to peers"
PUB=$(ssh $SSH_OPTS "$MASTER" "test -f ~/.ssh/id_rsa || ssh-keygen -t rsa -N '' -f ~/.ssh/id_rsa -q; cat ~/.ssh/id_rsa.pub")
log "  master pubkey len=${#PUB}"
for i in 1 2 3 4 5 6; do
    PEER="node${i}.${EXP_NAME}.cs620426sp-PG0.clemson.cloudlab.us"
    if ssh $SSH_OPTS "$PEER" "echo '$PUB' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo OK_$PEER" 2>&1 | tee -a $LOG | grep -q OK_; then
        log "  key installed on node$i"
    else
        log "  WARN: key install failed on node$i"
    fi
done

# Step 4: write nodes.txt on master
log "Step 4/5: write nodes.txt on master"
NODE_LIST=""
for i in 0 1 2 3 4 5 6; do
    NODE_LIST="${NODE_LIST}node${i}.${EXP_NAME}.cs620426sp-PG0.clemson.cloudlab.us\\n"
done
ssh $SSH_OPTS "$MASTER" "printf '$NODE_LIST' > /tmp/nodes.txt; wc -l /tmp/nodes.txt" 2>&1 | tee -a $LOG

# Step 5: dispatch bootstrap on all 7 in parallel
log "Step 5/5: scp + dispatch bootstrap-node.sh on all 7 nodes"
scp $SSH_OPTS script/bootstrap-node.sh "$MASTER:/tmp/bootstrap-node.sh" 2>&1 | tee -a $LOG | tail -3
ssh $SSH_OPTS "$MASTER" "
    for n in \$(cat /tmp/nodes.txt); do
        scp -o StrictHostKeyChecking=no /tmp/bootstrap-node.sh \$n:/tmp/bootstrap-node.sh > /dev/null 2>&1
        ssh -o StrictHostKeyChecking=no \$n 'nohup bash /tmp/bootstrap-node.sh > /tmp/boot-stdout.log 2>&1 < /dev/null & disown' &
    done
    # master itself needs the bootstrap too (master can't ssh to itself with cloudlab key)
    nohup bash /tmp/bootstrap-node.sh > /tmp/boot-stdout-master.log 2>&1 < /dev/null & disown
    wait
" 2>&1 | tee -a $LOG | tail -5

log "=== Launch complete. Bootstrap running on 7 nodes (~10 min) ==="
log "Next: 12-min wakeup at $(date -u -v+12M +%FT%TZ) for atomic-cap-fix decision."
log "Experiment id: $EXP_ID  master: $MASTER"

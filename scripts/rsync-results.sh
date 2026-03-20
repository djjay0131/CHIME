#!/bin/bash
#
# rsync-results.sh — Continuously pull results from master node to local machine
#
# Run this on YOUR LAPTOP during experiments to keep a live copy of results.
# Syncs every 5 minutes until you Ctrl+C.
#
# Prerequisites:
#   - SSH access to the master node (cloudlab_chime key)
#   - The master node must be reachable (reservation active)
#
# Usage:
#   MASTER="djjay@nodeX.exp.proj.clemson.cloudlab.us" bash scripts/rsync-results.sh
#
# The MASTER env var must be set to the SSH user@host of the master node.
# Get the hostname from the CloudLab experiment List View after provisioning.
#
# Results are synced to: exp/results/ (local copy)

set -euo pipefail

if [ -z "${MASTER:-}" ]; then
    echo "ERROR: Set MASTER env var to the master node SSH address."
    echo "  e.g., MASTER=\"djjay@nodeX.exp.proj.clemson.cloudlab.us\" bash scripts/rsync-results.sh"
    exit 1
fi

SSH_KEY="$HOME/.ssh/cloudlab_chime"
REMOTE_RESULTS="~/CHIME/exp/results/"
LOCAL_RESULTS="$(dirname "$0")/../exp/results/"
INTERVAL=300  # seconds between syncs

mkdir -p "$LOCAL_RESULTS"

echo "=== rsync-results: live results backup ==="
echo "Pulling from: $MASTER:$REMOTE_RESULTS"
echo "Saving to:    $LOCAL_RESULTS"
echo "Interval:     ${INTERVAL}s (Ctrl+C to stop)"
echo ""

sync_once() {
    local ts
    ts=$(date '+%H:%M:%S')
    if rsync -az --update \
        -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=no -o ConnectTimeout=10" \
        "$MASTER:$REMOTE_RESULTS" "$LOCAL_RESULTS" 2>/dev/null; then
        echo "[$ts] synced OK — $(ls "$LOCAL_RESULTS"*.json 2>/dev/null | wc -l) result files"
    else
        echo "[$ts] WARNING: rsync failed (node unreachable?)"
    fi
}

# Run immediately, then on interval
sync_once
while true; do
    sleep "$INTERVAL"
    sync_once
done

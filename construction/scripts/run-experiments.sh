#!/bin/bash
# run-experiments.sh — Run priority experiments on r650 cluster.
#
# Runs fig_12 (throughput-latency, ~7.5h) then fig_15b (ROLEX ablation, ~40m).
# Must be run from the master node after setup-r650.sh completes.
#
# Usage (in tmux on master):
#   cd ~/CHIME/construction/scripts && bash run-experiments.sh
#
# Or run individual figures:
#   cd ~/CHIME/exp && python3 fig_12.py
#   cd ~/CHIME/exp && python3 fig_15b.py

set -euo pipefail
cd "$(dirname "$0")/../.."
CHIME_ROOT="$PWD"

log() { echo "[$(date '+%H:%M:%S')] $*"; }

log "=== Starting experiment run ==="
log "Working directory: $CHIME_ROOT"
log ""

# Priority 1: fig_12 — main throughput-latency comparison (~7.5h)
log "--- fig_12: Throughput-Latency (all 5 methods, 6 YCSB workloads) ---"
cd "$CHIME_ROOT/exp"
if python3 fig_12.py; then
    log "fig_12 COMPLETE — results in exp/results/"
else
    log "fig_12 FAILED (exit code $?) — check logs above"
    log "Continuing to next experiment..."
fi
log ""

# Priority 2: fig_15b — ROLEX ablation (~40m)
log "--- fig_15b: ROLEX Factor Analysis ---"
if python3 fig_15b.py; then
    log "fig_15b COMPLETE — results in exp/results/"
else
    log "fig_15b FAILED (exit code $?) — check logs above"
fi
log ""

# Optional: fig_15a if not already collected (already have Mar 28 data)
# log "--- fig_15a: Sherman Factor Analysis ---"
# python3 fig_15a.py

log "=== All experiments finished ==="
log "Results:"
ls -la "$CHIME_ROOT/exp/results/"

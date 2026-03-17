#!/bin/bash
# Day 1 dry-run setup: run from master node inside ~/CHIME.
# Prereqs: NODES or NODES_FILE set, passwordless SSH to all nodes (run setKey.py first).
#
# Usage:
#   NODES="node-0,...,node-5" bash script/day1-dry-run.sh
#   NODES_FILE=./nodes.txt bash script/day1-dry-run.sh
#
# Optional: SKIP_INSTALL_LIBS=1 to skip installLibs (if already done)
# Optional: PIP_BREAK_SYSTEM=1 for Ubuntu 22+ when running installLibs

set -e
cd "$(dirname "$0")/.."
CHIME_ROOT="$PWD"

# Resolve NODES
if [ -n "$NODES_FILE" ] && [ -f "$NODES_FILE" ]; then
  NODES=$(paste -sd, - < "$NODES_FILE")
elif [ -z "$NODES" ]; then
  echo "Set NODES (comma-separated) or NODES_FILE (path to nodes.txt)"
  echo "Example: NODES=\"node-0.exp.proj.clemson.cloudlab.us,node-1.exp.proj.clemson.cloudlab.us\" bash script/day1-dry-run.sh"
  exit 1
fi

echo "=== Day 1 dry run setup (nodes: $NODES)"
echo ""

# 1. RDMA check
echo "--- Checking RDMA on all nodes ---"
bash script/run-on-nodes.sh "$NODES" "ibv_devinfo" || true
echo "If any node failed, install MLNX OFED there: bash script/run-on-nodes.sh \"\$NODES\" \"cd ~/CHIME/script && bash installMLNX.sh\""
echo ""

# 2. Dependencies
if [ -z "$SKIP_INSTALL_LIBS" ]; then
  echo "--- Installing dependencies on all nodes (this may take a while) ---"
  bash script/run-on-nodes.sh "$NODES" "cd ~/CHIME/script && bash installLibs.sh"
  echo ""
else
  echo "--- Skipping installLibs (SKIP_INSTALL_LIBS=1) ---"
  echo ""
fi

# 3. Hugepages
echo "--- Configuring hugepages on all nodes ---"
bash script/run-on-nodes.sh "$NODES" "sudo bash ~/CHIME/script/setup-hugepages.sh"
echo ""

# 4. Clone sibling repos
echo "--- Cloning SMART, ROLEX, Marlin on all nodes ---"
bash script/run-on-nodes.sh "$NODES" "bash ~/CHIME/script/clone-repos.sh"
echo ""

echo "=== Day 1 script done ==="
echo "Next (run from master with your cluster IPs):"
echo "  python3 construction/scripts/generate-common-json.py --home \$HOME --master <master_ip> --ips <ip1>,<ip2>,..."
echo "  python3 construction/scripts/patch-cn-count.py 5"
echo "See construction/scripts/day1-runbook.md for full steps."

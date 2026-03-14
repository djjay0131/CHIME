#!/bin/bash
# Run a command on multiple nodes in parallel.
# Usage:
#   ./run-on-nodes.sh "node1,node2,node3" "cmd"
#   ./run-on-nodes.sh "node1 node2 node3" "cmd"   # space-separated also works
#   USER=cloudlab ./run-on-nodes.sh "node1,node2" "sudo apt update"
#
# Requires: passwordless SSH from current host to all nodes.
# For CloudLab: run from your laptop or from the master node after setKey.py.

USER="${USER:-$(whoami)}"
NODES="$1"
CMD="$2"

if [ -z "$NODES" ] || [ -z "$CMD" ]; then
    echo "Usage: run-on-nodes.sh <nodes> <command>"
    echo "  nodes: comma- or space-separated (e.g. node-0.exp.proj.clemson.cloudlab.us,node-1,...)"
    exit 1
fi

# Normalize: commas or spaces -> newlines
NODELIST=$(echo "$NODES" | tr ', ' '\n' | grep -v '^$')
FAILED=0

for node in $NODELIST; do
    echo "[$node] $CMD"
    ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 "$USER@$node" "$CMD" &
done
wait

echo "Done."

#!/bin/bash
#
# recover.sh — Restore CloudLab node state after a reboot
#
# Run from the master node (MN). Re-mounts NVMe on all nodes, sets hugepages
# on CNs, and restarts memcached on MN. Safe to run multiple times.
#
# Usage: bash ~/CHIME/scripts/recover.sh

set -euo pipefail

CLUSTER_IPS=("130.127.134.40" "130.127.134.64" "130.127.134.47" "130.127.134.52" "130.127.134.38")
CN_IPS=(                       "130.127.134.64" "130.127.134.47" "130.127.134.52" "130.127.134.38")
NVME_DEV="/dev/nvme0n1"
NVME_MNT="/mnt/nvme"
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=10"

echo "=== CHIME CloudLab Recovery ==="
echo "Time: $(date)"
echo ""

# ── Step 1: Mount NVMe on all nodes ────────────────────────────────────────
echo "--- Step 1: Mount NVMe on all nodes ---"
for ip in "${CLUSTER_IPS[@]}"; do
    ssh $SSH_OPTS "$ip" "
        if mountpoint -q $NVME_MNT 2>/dev/null; then
            echo '[$ip] NVMe already mounted'
        else
            sudo mkdir -p $NVME_MNT
            sudo mount $NVME_DEV $NVME_MNT 2>/dev/null \
                && echo '[$ip] NVMe mounted OK' \
                || echo '[$ip] WARNING: mount failed (check blkid)'
        fi
    " &
done
wait
echo ""

# ── Step 2: Verify workload symlinks on CNs ─────────────────────────────────
echo "--- Step 2: Verify workload symlinks ---"
for ip in "${CN_IPS[@]}"; do
    ssh $SSH_OPTS "$ip" "
        if [ -d $NVME_MNT/ycsb_workloads ]; then
            count=\$(ls $NVME_MNT/ycsb_workloads 2>/dev/null | wc -l)
            echo '[$ip] workloads on NVMe: '\$count' dirs'
        else
            echo '[$ip] WARNING: $NVME_MNT/ycsb_workloads missing — workloads need regeneration'
        fi
        # Repair symlink if broken
        if [ ! -e ~/CHIME/ycsb/workloads ]; then
            ln -sfn $NVME_MNT/ycsb_workloads ~/CHIME/ycsb/workloads
            echo '[$ip] Repaired CHIME workload symlink'
        fi
        for repo in SMART ROLEX; do
            if [ -d ~/$repo/ycsb ] && [ ! -e ~/$repo/ycsb/workloads ]; then
                ln -sfn $NVME_MNT/ycsb_workloads ~/$repo/ycsb/workloads
                echo '[$ip] Repaired '$repo' workload symlink'
            fi
        done
    " &
done
wait
echo ""

# ── Step 3: Set hugepages on CNs ────────────────────────────────────────────
echo "--- Step 3: Set hugepages on CNs (36864) ---"
for ip in "${CN_IPS[@]}"; do
    ssh $SSH_OPTS "$ip" "
        echo 36864 | sudo tee /proc/sys/vm/nr_hugepages > /dev/null
        actual=\$(cat /proc/sys/vm/nr_hugepages)
        echo '[$ip] hugepages='\$actual
    " &
done
wait
echo ""

# ── Step 4: Restart memcached on MN ─────────────────────────────────────────
echo "--- Step 4: Restart memcached on MN ---"
pkill memcached 2>/dev/null && sleep 1 || true
memcached -d -p 11211 -l 0.0.0.0
sleep 1
if pgrep memcached > /dev/null; then
    echo "[MN] memcached running (PID: $(pgrep memcached))"
else
    echo "[MN] WARNING: memcached failed to start"
fi
echo ""

# ── Summary ─────────────────────────────────────────────────────────────────
echo "=== Recovery complete ==="
echo "Nodes accessible:"
for ip in "${CLUSTER_IPS[@]}"; do
    ssh $SSH_OPTS "$ip" "echo '  '$ip': OK — NVMe: '\$(mountpoint -q $NVME_MNT && echo mounted || echo NOT MOUNTED)" 2>/dev/null || echo "  $ip: UNREACHABLE"
done
echo ""
echo "Next: cd ~/CHIME/exp && python3 fig_14.py (or whichever figure to run)"

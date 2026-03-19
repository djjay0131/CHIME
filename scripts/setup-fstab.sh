#!/bin/bash
#
# setup-fstab.sh — Add NVMe to /etc/fstab so it auto-mounts after reboot
#
# Run once on EACH node during initial setup (or via pssh from MN).
# Safe to run multiple times — checks for duplicate entries.
#
# Usage from MN:
#   for ip in 130.127.134.40 130.127.134.64 130.127.134.47 130.127.134.52 130.127.134.38; do
#     ssh $ip "bash ~/CHIME/scripts/setup-fstab.sh"
#   done

set -euo pipefail

NVME_DEV="/dev/nvme0n1"
NVME_MNT="/mnt/nvme"

# Get UUID of the NVMe partition
UUID=$(sudo blkid "$NVME_DEV" -s UUID -o value 2>/dev/null)
if [ -z "$UUID" ]; then
    echo "ERROR: Could not get UUID for $NVME_DEV"
    echo "Is the device formatted? Run: sudo mkfs.ext4 $NVME_DEV"
    exit 1
fi

echo "[$HOSTNAME] NVMe UUID: $UUID"

# Check if already in fstab
if grep -q "$UUID" /etc/fstab; then
    echo "[$HOSTNAME] Already in /etc/fstab — skipping"
else
    sudo mkdir -p "$NVME_MNT"
    echo "UUID=$UUID $NVME_MNT ext4 defaults,nofail 0 2" | sudo tee -a /etc/fstab
    echo "[$HOSTNAME] Added to /etc/fstab"
fi

# Mount now if not already mounted
if ! mountpoint -q "$NVME_MNT"; then
    sudo mount "$NVME_MNT"
    echo "[$HOSTNAME] Mounted $NVME_MNT"
else
    echo "[$HOSTNAME] Already mounted"
fi

echo "[$HOSTNAME] Done. Contents: $(ls $NVME_MNT | head -5)"

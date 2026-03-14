#!/bin/bash
# Configure hugepages for CHIME experiments.
# Run on each node: sudo bash setup-hugepages.sh
# Paper/README use 36864 hugepages (2MB pages ≈ 72GB); smaller clusters can use fewer.

set -e
NR_HUGEPAGES="${1:-36864}"
echo "Configuring $NR_HUGEPAGES hugepages..."
echo "$NR_HUGEPAGES" | sudo tee /proc/sys/vm/nr_hugepages
echo "Verifying:"
grep -E "HugePages_Total|HugePages_Free" /proc/meminfo

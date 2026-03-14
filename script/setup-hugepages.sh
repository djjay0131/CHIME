#!/bin/bash
# Configure hugepages for CHIME experiments.
# Run on each node: sudo bash setup-hugepages.sh
# Paper uses 10240 hugepages (default 2MB pages = 20GB).

set -e
NR_HUGEPAGES="${1:-10240}"
echo "Configuring $NR_HUGEPAGES hugepages..."
echo "$NR_HUGEPAGES" | sudo tee /proc/sys/vm/nr_hugepages
echo "Verifying:"
grep -E "HugePages_Total|HugePages_Free" /proc/meminfo

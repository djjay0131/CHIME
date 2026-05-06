#!/usr/bin/env bash
# bootstrap-node.sh — Idempotent per-node setup. Runs on each cluster node.
#
# Order is deliberate:
#   1. Pre-write modprobe.d for mlx5_core (MAX_ATOMIC_ARG=8) BEFORE OFED loads.
#      This avoids the trap where `openibd restart` to apply the option
#      kills eno12399 (mlx5_core also manages the control NIC).
#   2. Install MLNX OFED from /proj NFS if not present (~5 min).
#   3. Install runtime libs (memcached, libtbb, libnuma, libboost, libgflags, cityhash).
#   4. Configure hugepages (RDMA layout: node1=36864, node0=0).
#   5. Confirm internal vlan is up (auto-detected; CloudLab uses different VLAN IDs per experiment).
#
# Usage (on each node):
#   bash /tmp/bootstrap-node.sh
#
# Output goes to /tmp/bootstrap-<short-host>.log
set -e
OFED=/proj/cs620426sp-PG0/djjay-tmp/ofed/MLNX_OFED_LINUX-4.9-5.1.0.0-ubuntu20.04-x86_64
NODE=$(hostname -s)
LOG=/tmp/bootstrap-${NODE}.log

{
echo "=== bootstrap on $NODE at $(date -u +%FT%TZ) ==="

# 1. Skip MAX_ATOMIC_ARG=8 modprobe option on r650 Clemson — May 6 incident
#    showed it crashes mlx5_core at load and bricks the control NIC. We accept
#    device_cap_flags=0 and run workloads that don't require RDMA atomics
#    (workload C and E are read-only; D requires atomics — skip on this run).
#    If a previous bootstrap installed the option, REMOVE it.
if [ -f /etc/modprobe.d/mlx5_core.conf ]; then
    echo "[$(date -u +%H:%M:%S)] removing /etc/modprobe.d/mlx5_core.conf (caps=0 fallback)"
    sudo rm -f /etc/modprobe.d/mlx5_core.conf
fi

# 2. Install OFED if absent
if ! ibv_devinfo &>/dev/null; then
    echo "[$(date -u +%H:%M:%S)] installing MLNX OFED from /proj..."
    cd $OFED
    sudo ./mlnxofedinstall --user-space-only --without-fw-update --force -q 2>&1 | tail -10
    echo "[$(date -u +%H:%M:%S)] OFED install done"
else
    echo "OFED already installed: $(ofed_info -s 2>/dev/null | head -1)"
fi

# 3. Runtime libs
echo "[$(date -u +%H:%M:%S)] installing libs..."
sudo apt-get -y update >/dev/null 2>&1 || true
sudo apt-get -y install memcached libmemcached-dev libtbb-dev libnuma-dev libboost-all-dev libgflags-dev cmake libgoogle-perftools-dev 2>&1 | tail -3

# cityhash from source if missing
if [ ! -f /usr/local/lib/libcityhash.so ]; then
    echo "[$(date -u +%H:%M:%S)] building cityhash..."
    cd /tmp
    rm -rf cityhash
    git clone https://github.com/google/cityhash.git 2>&1 | tail -3
    cd cityhash && ./configure --enable-sse4.2 && make -j4 && sudo make install 2>&1 | tail -3
fi
sudo ldconfig

# 4. Hugepages — RDMA layout (node1 = 36864, node0 = 0).
echo 0     | sudo tee /sys/devices/system/node/node0/hugepages/hugepages-2048kB/nr_hugepages > /dev/null
echo 36864 | sudo tee /sys/devices/system/node/node1/hugepages/hugepages-2048kB/nr_hugepages > /dev/null

# 5. Confirm internal vlan (auto-detect — CloudLab assigns different VLAN IDs per experiment)
INTERNAL_IFACE=$(ip -br addr show | awk '/10\.10\./{print $1; exit}' | sed 's/@.*//')
INTERNAL_IP=$(ip -br addr show | awk '/10\.10\./{print $3; exit}' | cut -d/ -f1)
echo "[$(date -u +%H:%M:%S)] internal iface=$INTERNAL_IFACE ip=$INTERNAL_IP"

# 6. Verify device caps look right (non-zero device_cap_flags)
CAPS=$(ibv_devinfo -v 2>/dev/null | awk '/device_cap_flags/{print $2; exit}')
echo "[$(date -u +%H:%M:%S)] device_cap_flags=$CAPS (should be non-zero like 0xe5721c36; if 0x00000000 the modprobe option did not take — node needs a fresh boot before mlx5_core ever loaded with default options)"

echo "[$(date -u +%H:%M:%S)] bootstrap complete on $NODE"
} > $LOG 2>&1
echo "DONE $NODE"

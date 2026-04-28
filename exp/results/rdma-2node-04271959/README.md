# Apr 27 2-node r650 RDMA Results

## Setup
- Hardware: 2× r650 Clemson, ConnectX-6 Dx
- Reservation UUID: `2afbcb47-b233-4d21-b350-d6af029d9074`
- Source: `/proj/cs620426sp-PG0/djjay-CHIME-orig/` (8b3e73e first commit + RoCE/Dx fixes)
- Build: `/proj/cs620426sp-PG0/djjay-build/build-rdma-orig/`

## RoCE/Dx Fixes Applied
- `MLX_GID = 3` (RoCE v2 + VLAN)
- `IBV_MTU_4096` (matches ens2f0 MTU 9000)
- `attr->grh.hop_limit = 64` (RoCE routing)
- `MAX_ATOMIC_ARG = 8` (was 32; ConnectX-6 Dx returns ENOTSUP at 32)
- `attr.cap.max_recv_sge = (mode==IBV_QPT_UD) ? 2 : 1` (UD needs GRH room on Dx)
- Full MLNX OFED 4.9 install with `--add-kernel-support` (rebuilds kernel modules)
- `openibd restart` on both nodes after install (capability-flag fix; pre-restart `device_cap_flags=0x00000000`, post-restart `0xe5721c36`)

## Workload Results
- **C (read-only, 8 threads)**: ✅ COMPLETE. Peak 1.11 Mops/s, 12M ops over 10 epochs.
- **A (50/50 read/update)**: ❌ assertion failure at `Tree.cpp:1596` (`leaf_node_update neighborSize`)
- **B (95% read, 5% update)**: ❌ same assertion as A
- **LOAD (100% insert)**: ⏳ partial — MN ran to "node 1 finish" but CN segfaulted

## Files
- `epoch_*.lat`: per-epoch latency CSVs from workload C
- `fig_12_c_sweep.jsonl`: peak throughput per thread count

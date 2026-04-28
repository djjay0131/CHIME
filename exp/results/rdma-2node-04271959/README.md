# Apr 27 r650 RDMA Reservation Results

## Setup
- Hardware: 2× r650 Clemson, ConnectX-6 Dx, 144 logical CPUs/node, 256GB DRAM
- Reservation UUID: `2afbcb47-b233-4d21-b350-d6af029d9074`
- Source: `/proj/cs620426sp-PG0/djjay-CHIME-orig/` (commit `8b3e73e` first commit + RoCE/Dx fixes)

## ConnectX-6 Dx Compatibility Patches
1. `MLX_GID = 3` (RoCE v2 + VLAN GID; was 1)
2. `IBV_MTU IBV_MTU_4096` (matches ens2f0 MTU 9000)
3. `attr->grh.hop_limit = 64` (RoCE routing; was 1)
4. `dAttr.hop_limit = 64`
5. `MAX_ATOMIC_ARG = 8` (was 32; ConnectX-6 Dx returns ENOTSUP at 32 even with full OFED)
6. `attr.cap.max_recv_sge = (mode==IBV_QPT_UD) ? 2 : 1` (UD needs GRH room on Dx)

## Critical Setup Steps
1. Full MLNX OFED 4.9 install with `--add-kernel-support`
2. **`sudo /etc/init.d/openibd restart`** on both nodes after install — this fixes `device_cap_flags=0x00000000` to `0xe5721c36`. Without it, ALL `ibv_create_qp` calls fail with errno 95 ENOTSUP.
3. Restore `ens2f0` MTU to 9000 after openibd restart (resets to 1500)
4. Initialize memcached counters: `set serverNum 0 0 1\n0\nset clientNum 0 0 1\n0`

## Results

### fig_12 throughput-thread sweep (1 CN + 1 MN, full CHIME)
| Threads | C (read-only) | D (95% R/5% I) | E (95% scan/5% I) |
|---------|---------------|----------------|-------------------|
|    4    |    0.58       |     ---        |       ---         |
|    8    |    1.12       |    1.07        |      0.21         |
|   16    |    5.34       |    2.11        |      0.61         |
|   32    |    4.23       |    3.86        |      0.82         |
|   64    |    5.36       |    4.82        |      1.32         |

### fig_15a per-technique ablation (YCSB C @ 16 threads)
| Variant                                | Mops/s |
|----------------------------------------|--------|
| Sherman-equivalent (all OFF)           | build failed at link |
| + HOPSCOTCH_LEAF_NODE                  |  2.14  |
| + VACANCY_AWARE_LOCK                   |  2.15  |
| + METADATA_REPLICATION                 |  2.40  |
| + SIBLING_BASED_VALIDATION             |  2.40  |
| + SPECULATIVE_READ (full CHIME)        |  2.22  |

### Aborted workloads
- **A (50/50 read/update)**: assertion `Tree.cpp:1596 leaf_node_update neighborSize` after LOAD phase
- **B (95% R, 5% U)**: same assertion as A
- **LOAD (100% insert)**: MN completed LOAD phase but CN segfaulted

## CXL build path (for completeness)
The CXL build (USE_CXL=ON) compiles cleanly on r650 (AC-7 strengthened beyond Docker), but `ycsb_test` segfaults in the worker thread after the LOAD phase begins. Three suspects (off-hardware bisectable):
1. Tree level convention (root_entry.level vs node.metadata.level)
2. Other GlobalAddress bit-packing call sites with same bug as commit 152b4e9 fix
3. read_sync transInternalSize from leaf-sized address when root is leaf

## Files
- `mn-c-8t-original.out` — first successful 8-thread YCSB C run (raw output)
- `lat-c-8t/epoch_*.lat` — per-epoch latency CSVs from that run
- `fig_12_c_sweep.jsonl` — fig_12 C-curve data
- `fig_12_de_sweep.jsonl` — fig_12 D and E curves
- `fig_12_chime_extra.jsonl` — additional CHIME-only C data points
- `fig_15a_sweep_v2.jsonl` — per-technique ablation
- `findings.txt` — chronological run log with hypothesis-narrowing notes
- `backtrace.txt` — gdb output from CXL crash
- `Common.h.snap`, `CMakeCache.txt.snap` — build state at first runtime probe

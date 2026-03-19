---
title: "Research Report"
subtitle: "Reproducing CHIME: A Cache-Efficient and High-Performance Hybrid Index on Disaggregated Memory"
---

CS 6204 Advanced Topics in Systems — Virginia Tech, Spring 2026. Due: March 26, 2026.

{{< pdf "/pdfs/report.pdf" >}}

---

## Report Structure

### 1. Introduction

CHIME is a hybrid B+ tree / hopscotch-hashing index designed for disaggregated memory. The paper addresses a fundamental cache-vs-amplification trade-off in DM range indexes:

- **B+ tree (Sherman)**: low cache consumption, but O(log N) RDMA reads per lookup
- **Learned index (ROLEX)**: low read amplification, but large per-node model caches
- **CHIME**: hopscotch leaf nodes embedded in a B+ tree — gets both properties simultaneously

We reproduced Figures 12, 14, 15a, and 15b from the paper on CloudLab r650 hardware.

### 2. Experimental Setup

**Hardware** (CloudLab r650, Clemson cluster):

| Component | Spec |
|-----------|------|
| CPU | 2× Intel Xeon (36 cores each) |
| Memory | 256 GB DDR4 |
| NIC | Mellanox ConnectX-6, 100 Gbps |
| Storage | 1.5 TB NVMe (for YCSB workloads) |
| Cluster | 9 CN + 1 MN (full run), 4 CN + 1 MN (dry run) |

**Software configuration** (matching paper Section 5.1):
- Compute nodes: 4 GB local RDMA cache, 64 clients per node
- Memory node: 64 GB DRAM, 1 CPU core
- YCSB: 60M entries, 8-byte keys, 8-byte values, Zipfian distribution
- MLNX OFED 4.9 (required for `ibv_exp_dct` Mellanox experimental RDMA verbs)

**Methods compared:**

| Method | Index Type | Source |
|--------|-----------|--------|
| CHIME | Hybrid (B+ tree + hopscotch) | dmemsys/CHIME |
| Sherman | B+ tree | CHIME repo (different CMake flags) |
| SMART | Radix tree (Sherman-style) | dmemsys/SMART |
| ROLEX | Learned index | River861/ROLEX |
| SMART-SC | SMART with sufficient cache | dmemsys/SMART |

### 3. Results

#### Figure 12: YCSB Throughput-Latency

Six YCSB workloads (LOAD, A, B, C, D, E) across all five methods. The paper claims CHIME achieves 1.5–3× higher throughput than Sherman while using 2–5× less cache than ROLEX.

*Results will be added after the full CloudLab run (Mar 27–Apr 3).*

#### Figure 14: Cache Consumption

Cache usage (GB) at varying dataset sizes (40M–120M entries). CHIME should show sub-linear cache growth compared to ROLEX's model-dominated footprint.

*Results will be added after the full run.*

#### Figure 15: Factor Analysis

Incremental contribution of each CHIME technique:
- **15a**: Sherman → +synchronization → +metadata → +speculative read → CHIME
- **15b**: ROLEX → same progression

*Results will be added after the full run.*

### 4. Analysis

Comparison of reproduced results against paper claims, including any discrepancies and their suspected root causes.

*To be completed after results are available.*

### 5. Challenges and Lessons Learned

Key obstacles encountered during the dry run (March 17–18):

1. **MLNX OFED**: Ubuntu's `libibverbs-dev` (v17) lacks Mellanox's experimental API (`ibv_exp_dct`). Had to manually copy OFED 4.9 `.deb` packages from apt cache and install with `dpkg -i` on all nodes.

2. **Root disk overflow**: YCSB workload files (~5–10 GB per workload type) fill the 16 GB root disk immediately. Fixed by formatting the 1.5 TB NVMe, mounting at `/mnt/nvme`, and symlinking `~/CHIME/ycsb/workloads/ → /mnt/nvme/ycsb_workloads/`.

3. **NVMe not auto-mounted on reboot**: Missing `/etc/fstab` entry means every reboot requires manual remount. Fix for full run: add UUID-based fstab entry during initial setup.

4. **Stale SSH connections**: Paramiko connections in `CMDManager` go stale after ~1.5 hours. `killall -9 ycsb_test` then hangs and triggers the infinite retry loop. Fix: restart the Python experiment script to reinitialize connections for long-running experiments.

5. **Reservation timing**: Experiment setup (OFED install, workload generation, compilation across 5 repos) consumed most of the dry-run reservation window, leaving insufficient time for results collection.

### 6. Conclusion

*To be completed after full results are available.*

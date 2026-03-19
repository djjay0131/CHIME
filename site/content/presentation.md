---
title: "Presentation"
subtitle: "15–20 min Beamer, April 7–9, 2026 (Week 12)"
---

Beamer presentation for CS 6204 Week 12. Built with the Metropolis theme (16:9).

{{< pdf "/pdfs/presentation.pdf" >}}

---

## Slide Outline

### Section 1: Paper Overview

**CHIME: Key Idea**
- Disaggregated memory separates compute and memory pools over a network fabric
- Range indexes on DM face a trade-off: cache consumption vs. read amplifications
- CHIME uses hopscotch-hashing leaf nodes inside a B+ tree skeleton — gets both benefits simultaneously: B+ tree internals keep cache low, hopscotch leaves keep reads low

**Three Key Techniques**
1. Three-level optimistic synchronization: cache line versions + reused bitmaps for concurrency without RDMA locks
2. Access-aggregated metadata management: piggyback vacancy bitmaps onto existing RDMA reads; replicate leaf metadata
3. Hotness-aware speculative read: hotspot buffer shortcuts neighborhood traversal for popular keys

### Section 2: Experimental Setup

**CloudLab Configuration**
- Hardware: 10× r650 nodes, ConnectX-6 (100 Gbps), 256 GB DRAM per node
- Software: CHIME + 4 baselines, YCSB 60M entries, 8-byte keys/values, Zipfian
- Roles: 9 compute nodes (4 GB cache each, 64 threads) + 1 memory node

**Methods Compared**

| Method | Type | Source |
|--------|------|--------|
| CHIME | Hybrid (B+ tree + hopscotch) | dmemsys/CHIME |
| Sherman | B+ tree | CHIME repo (diff flags) |
| SMART | Radix tree | dmemsys/SMART |
| ROLEX | Learned index | River861/ROLEX |
| SMART-SC | Radix tree (sufficient cache) | dmemsys/SMART |

### Section 3: Results

**Figure 12: YCSB Throughput-Latency**
- 6 workloads × 5 methods (LOAD, A, B, C, D, E)
- Expected: CHIME 1.5–3× throughput of Sherman, 2–5× less cache than ROLEX

*Slides will be updated with actual figures after full run (Mar 27–Apr 3).*

**Figure 14: Cache Consumption**
- Cache usage vs. dataset size (40M–120M entries)
- Expected: CHIME sub-linear growth vs. ROLEX

**Figure 15: Factor Analysis**
- Incremental technique contribution from two starting points (Sherman, ROLEX)

### Section 4: Analysis

**Comparison with Paper**
- How do our results align with the paper's claims?
- Any discrepancies and suspected root causes
- Key observations about reproducibility

**Lessons Learned**
- MLNX OFED installation (experimental verbs not in Ubuntu packages)
- Disk capacity planning for large YCSB workloads
- NVMe persistence across reboots (fstab)
- Paramiko connection management for long experiments

### Section 5: Next Steps

**Part Two: CXL Porting**
- Port CHIME's RDMA one-sided read/write layer to CXL memory-semantic operations
- Compare latency and throughput: RDMA vs. CXL
- Analyze implications for DM index design at CXL access granularity

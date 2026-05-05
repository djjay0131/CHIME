---
title: "Presentation"
subtitle: "Final Project Presentation, May 5, 2026"
---

## Final Presentation (May 5)

**Downloads:**

- <a href="/CHIME/pdfs/final-presentation.pdf">final-presentation.pdf</a> — audience view, **16 slides** for the 13-minute talk
- <a href="/CHIME/pdfs/final-presentation-notes.pdf">final-presentation-notes.pdf</a> — speaker view (slides + presenter notes side-by-side)
- <a href="/CHIME/pdfs/final-presentation-backup.pdf">final-presentation-backup.pdf</a> — full deck with Q&A backup slides (54 pages, includes the 16 spoken slides plus 38 backup slides for citation lookups during Q&A)

{{< pdf "/pdfs/final-presentation.pdf" >}}

The final-project presentation is reframed around agent-orchestrated reproduction on CloudLab as the contribution, with CHIME serving as the case study. The 16-slide arc: title, two-slide CHIME paper introduction, project setup (CloudLab configuration + methods compared), four-slide agent-orchestrated pipeline (three-layer overview, persona-driven workflow, CloudLab control surface, autonomous runner + ORNL XLOOP'25 differentiation), Sherman LOAD stress finding, two CXL results (workload-dependent CXL win, cross-day reproducibility), two-slide postmortem (misleading scheduler error, three concrete CloudLab API additions), and two closing slides (one-line allocator fix that the orchestration surfaced + key takeaways).

---

## Progress Presentation (April 9, history)

The earlier Week-12 progress presentation, preserved for history.

**Download:** <a href="/CHIME/pdfs/presentation.pdf">presentation.pdf</a>

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

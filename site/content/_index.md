---
title: "CHIME Reproduction"
---

Reproducing the key experiments from [*CHIME: A Cache-Efficient and High-Performance Hybrid Index on Disaggregated Memory*](https://dl.acm.org/doi/10.1145/3694715.3695976) (SOSP '24) as part of CS 6204 Advanced Topics in Systems at Virginia Tech.

## What is CHIME?

Disaggregated memory (DM) systems decouple compute and memory into separate network-connected pools. Range indexes built on DM face a fundamental tension: **B+ tree** designs have low cache consumption but high read amplification, while **learned indexes** have low read amplification but consume large amounts of cache at compute nodes.

CHIME resolves this by combining B+ tree internal nodes with **hopscotch-hashing leaf nodes**, achieving both properties simultaneously. Three key techniques make it work:

1. **Three-level optimistic synchronization** -- cache line versions + reused hopscotch bitmaps for fine-grained concurrency without locks
2. **Access-aggregated metadata management** -- vacancy bitmap piggybacking and leaf metadata replication to cut RDMA round trips
3. **Hotness-aware speculative read** -- a hotspot buffer that shortcuts neighborhood reads for popular keys

## Experiments Being Reproduced

We reproduce four figures from the paper on CloudLab r650 hardware with 100 Gbps RDMA:

| Figure | Description | Est. Runtime |
|--------|-------------|--------------|
| Fig. 12 | YCSB throughput-latency (6 workloads x 5 methods) | ~7.5 h |
| Fig. 14 | Cache consumption vs. dataset size | ~35 min |
| Fig. 15a | Factor analysis from Sherman (B+ tree baseline) | ~44 min |
| Fig. 15b | Factor analysis from ROLEX (learned index baseline) | ~40 min |

**Methods compared:** CHIME, Sherman, SMART, ROLEX, SMART-SC

## Project Status

| Dates | Phase | Status |
|-------|-------|--------|
| Mar 8 | CloudLab reservations submitted | <span class="badge badge-green">Done</span> |
| Mar 9--16 | Pre-work: scripts, build pipeline, profiles | <span class="badge badge-green">Done</span> |
| Mar 23--26 | Pre-deadline run: 11x r6525 Clemson (9 CN + 1 MN) | <span class="badge badge-green">Done</span> |
| Mar 27--Apr 3 | Full run: 10x r650 Clemson (9 CN + 1 MN) | <span class="badge badge-orange">Active</span> |
| Apr 3--6 | Re-run: 11x r650 Clemson (10 CN + 1 MN) | <span class="badge badge-maroon">Approved</span> |
| Apr 7--9 | Progress presentation (Week 12, 15--20 min) | <span class="badge badge-gray">Upcoming</span> |
| Late Apr | Part Two: CXL port | <span class="badge badge-gray">Upcoming</span> |
| May 5 | Final report due | <span class="badge badge-gray">Upcoming</span> |

## Deliverables

<div class="link-cards">
  <a href="/CHIME/experiment/" class="link-card">
    <h3>Experiment Details</h3>
    <p>Hardware, methods, workloads, timeline, and challenges</p>
  </a>
  <a href="/CHIME/paper/" class="link-card">
    <h3>Research Report</h3>
    <p>Section-by-section breakdown and reproduced results</p>
  </a>
  <a href="/CHIME/presentation/" class="link-card">
    <h3>Presentation</h3>
    <p>Beamer slides for the April 7--9 progress presentation</p>
  </a>
  <a href="https://github.com/djjay0131/CHIME" class="link-card">
    <h3>GitHub Repository</h3>
    <p>Experiment scripts, configs, and LaTeX sources</p>
  </a>
</div>

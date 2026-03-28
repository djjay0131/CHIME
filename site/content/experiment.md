---
title: "Experiment Details"
subtitle: "Reproducing CHIME on CloudLab with RDMA"
---

<div class="experiment-header">
  <h1>CHIME Reproduction Experiment</h1>
  <p>Full 5-method comparison on CloudLab r650 nodes with 100 Gbps RDMA</p>
</div>

## Presentation

<a href="/CHIME/pdfs/presentation.pdf" class="btn btn-orange" target="_blank">View Presentation PDF</a>
<a href="/CHIME/pdfs/presentation.pdf" class="btn btn-secondary" download>Download</a>

---

## Objective

Reproduce the key experimental results from [CHIME: A Cache-Efficient and High-Performance Hybrid Index on Disaggregated Memory](https://dl.acm.org/doi/10.1145/3694715.3695976) (SOSP '24) by Luo et al. on CloudLab hardware.

CHIME claims **2.0--5.6x throughput improvement** over existing disaggregated memory indexes while maintaining comparable cache consumption. We test this across 5 methods, 6 YCSB workloads, and 4 core experiments.

## Methods Compared

<div class="method-grid">
  <div class="method-card highlight">
    <h4>CHIME</h4>
    <p>Hybrid B+ tree + hopscotch hashing</p>
  </div>
  <div class="method-card">
    <h4>Sherman</h4>
    <p>B+ tree baseline</p>
  </div>
  <div class="method-card">
    <h4>SMART</h4>
    <p>Radix tree</p>
  </div>
  <div class="method-card">
    <h4>ROLEX</h4>
    <p>Learned index</p>
  </div>
  <div class="method-card">
    <h4>SMART-SC</h4>
    <p>Radix + sufficient cache</p>
  </div>
</div>

## Hardware Configuration

| Component | Specification |
|-----------|--------------|
| **Node type** | CloudLab r650 (Clemson) |
| **CPU** | 2x 36-core Intel Xeon (72 cores / 144 threads) |
| **Memory** | 256 GB DDR4 |
| **Network** | Mellanox ConnectX-6, 100 Gbps RDMA |
| **Cluster** | 10 compute nodes + 1 memory node |
| **OS** | Ubuntu 20.04 with Mellanox OFED 5.8 |

## Core Experiments

<div class="figure-grid">
  <div class="figure-card">
    <h4>Figure 12: Throughput-Latency</h4>
    <span class="runtime">~7.5 hours</span>
    <p>YCSB workloads A-E across all 5 methods. The primary result: does CHIME dominate on both throughput and latency?</p>
  </div>
  <div class="figure-card">
    <h4>Figure 14: Cache Consumption</h4>
    <span class="runtime">~35 minutes</span>
    <p>Cache usage vs. dataset size (40M-120M entries). Tests CHIME's claim of low cache overhead.</p>
  </div>
  <div class="figure-card">
    <h4>Figure 15a: Feature Breakdown (from Sherman)</h4>
    <span class="runtime">~44 minutes</span>
    <p>Cumulative contribution of each CHIME technique starting from a B+ tree baseline.</p>
  </div>
  <div class="figure-card">
    <h4>Figure 15b: Feature Breakdown (from ROLEX)</h4>
    <span class="runtime">~40 minutes</span>
    <p>Cumulative contribution of each CHIME technique starting from a learned index baseline.</p>
  </div>
</div>

## Additional Experiments

Beyond the paper's core figures, we run three sensitivity studies:

- **Cache sensitivity:** CHIME/Sherman/SMART at 10 MB, 100 MB, and 1000 MB cache (YCSB C)
- **Value size scaling:** 8B, 64B, 256B values across all methods (YCSB A)
- **Distribution comparison:** Zipfian vs. uniform distribution (YCSB C)

## Workload Configuration

| Parameter | Value |
|-----------|-------|
| Benchmark | YCSB (A, B, C, D, E, LOAD) |
| Entries | 60 million |
| Key size | 8 bytes |
| Value size | 8 bytes |
| Distribution | Zipfian (theta = 0.99) |
| Cache per CN | 4 GB (default) |
| Threads per CN | 64 |
| Coroutines per thread | 8 |

## Experiment Timeline

<div class="timeline">
  <div class="timeline-item done">
    <div class="timeline-date">March 8</div>
    <div class="timeline-title">CloudLab reservations submitted</div>
    <div class="timeline-desc">Profiles created, r650 nodes reserved at Clemson</div>
  </div>
  <div class="timeline-item done">
    <div class="timeline-date">March 9-16</div>
    <div class="timeline-title">Pre-work: automation scripts</div>
    <div class="timeline-desc">Setup scripts, build pipeline, experiment orchestration</div>
  </div>
  <div class="timeline-item done">
    <div class="timeline-date">March 23-26</div>
    <div class="timeline-title">Pre-deadline run on r6525</div>
    <div class="timeline-desc">11x r6525 (AMD EPYC), 9 CN + 1 MN (node 10 excluded - broken RDMA)</div>
  </div>
  <div class="timeline-item active">
    <div class="timeline-date">March 27 - April 3</div>
    <div class="timeline-title">Full run on r650</div>
    <div class="timeline-desc">10x r650 Clemson, 9 CN + 1 MN, hardware-matched to paper</div>
  </div>
  <div class="timeline-item upcoming">
    <div class="timeline-date">April 3-6</div>
    <div class="timeline-title">Re-run on r650 (10 CN)</div>
    <div class="timeline-desc">11x r650, 10 CN + 1 MN, full paper configuration</div>
  </div>
  <div class="timeline-item upcoming">
    <div class="timeline-date">April 7-9</div>
    <div class="timeline-title">Progress presentation</div>
    <div class="timeline-desc">15-20 min Beamer, Week 12</div>
  </div>
  <div class="timeline-item upcoming">
    <div class="timeline-date">May 5</div>
    <div class="timeline-title">Final report due</div>
    <div class="timeline-desc">Combined RDMA reproduction + CXL porting results</div>
  </div>
</div>

## Challenges Encountered

### Hardware mismatch
r650 nodes were fully booked pre-deadline. We pivoted to r6525 nodes (AMD EPYC, ConnectX-5) which required configuration changes: `CPU_PHYSICAL_CORE_NUM=64`, public IP memcached, NVMe storage for the 16 GB root partition.

### Broken RDMA on node 10
clnode304 had a non-functional RDMA interface. CloudLab reservations can't add nodes, so we ran with 9 CN instead of 10.

### YCSB API drift
YCSB 0.17.0 changed its Java package from `com.yahoo.ycsb` to `site.ycsb`, breaking the workload generator. Required patches to both Java bindings and Python parsing scripts.

### Persistent workloads
YCSB workload generation takes ~90 minutes. We store generated workloads on CloudLab project NFS (`/proj/cs620426sp-PG0/ycsb_workloads/`) and symlink from each experiment instance, enabling reuse across all three reservation windows.

## Results

*Results will be published here as experiment runs complete. Check back after April 3 for hardware-matched r650 data.*

## Part Two: CXL

The next phase ports CHIME from RDMA to CXL-based disaggregated memory using a compile-time transport abstraction layer and NUMA-based CXL emulation on the r650 dual-socket nodes. See the [presentation](/CHIME/presentation/) for details.

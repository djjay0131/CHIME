---
title: "Experiment Details"
subtitle: "Reproducing CHIME on CloudLab with RDMA"
---

<div class="experiment-header">
  <h1>CHIME Reproduction Experiment</h1>
  <p>Full 5-method comparison on CloudLab r650 nodes with 100 Gbps RDMA</p>
</div>

## Final Presentation (May 5)

<a href="/CHIME/pdfs/final-presentation.pdf" class="btn btn-orange" target="_blank">View Final Presentation</a>
<a href="/CHIME/pdfs/final-presentation-notes.pdf" class="btn btn-secondary" target="_blank">Speaker view (with notes)</a>
<a href="/CHIME/pdfs/final-presentation-backup.pdf" class="btn btn-secondary" target="_blank">Full deck (with Q&A backup)</a>

---

## Objective

Reproduce the key experimental results from [CHIME: A Cache-Efficient and High-Performance Hybrid Index on Disaggregated Memory](https://dl.acm.org/doi/10.1145/3694715.3695976) (SOSP '24) by Luo et al. on CloudLab hardware, and port the index from RDMA to CXL-attached memory for a transport-comparison study.

CHIME claims **2.0--5.6x throughput improvement** over existing disaggregated memory indexes while maintaining comparable cache consumption. We tested this across 5 methods on YCSB workloads C, D, E, plus the cumulative-ablation analyses (fig\_15a/b), then extended the matrix to a CXL transport on the same hardware.

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
| **Memory** | 256 GB DDR4 across two NUMA nodes |
| **Network** | Mellanox ConnectX-6 Dx, RoCE v2 over Ethernet (100 Gbps) |
| **Cluster (Run 7)** | 5 CN + 1 MN (paper's full 10 CN target was never available) |
| **Cluster (Run 8)** | 3 CN + 1 MN (extended Apr 6--7 window) |
| **Cluster (May 2 sprint)** | 3 CN + 1 MN (24-hour autonomous run) |
| **OS** | Ubuntu 20.04 with Mellanox OFED |
| **CXL emulation** | NUMA node 1, hugepages, `numa_set_preferred(1)` (single-CN only) |

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
    <div class="timeline-title">Automation scripts + build pipeline</div>
    <div class="timeline-desc">CloudLab REST API client, setup scripts, experiment orchestration, persistent workloads on NFS</div>
  </div>
  <div class="timeline-item done">
    <div class="timeline-date">March 23-26</div>
    <div class="timeline-title">Pre-deadline dry run on r6525</div>
    <div class="timeline-desc">11x r6525 (AMD EPYC), 9 CN + 1 MN — node 10 excluded for broken RDMA. Validated harness end-to-end on non-paper-matched hardware.</div>
  </div>
  <div class="timeline-item done">
    <div class="timeline-date">March 27 - April 3</div>
    <div class="timeline-title">r650 RDMA debug (Runs 1-4)</div>
    <div class="timeline-desc">Discovered six RoCE config requirements; confirmed internal LAN required for RDMA traffic (control-net = quarantine); identified the memcached.conf port-line bug that cost 10h on Run 7.</div>
  </div>
  <div class="timeline-item done">
    <div class="timeline-date">April 5-6</div>
    <div class="timeline-title">r650 Run 7 (5 CN + 1 MN)</div>
    <div class="timeline-desc">16-hour run. Collected fig_15a, fig_15b complete; fig_12 workloads C and D complete across all 5 methods.</div>
  </div>
  <div class="timeline-item done">
    <div class="timeline-date">April 6-7</div>
    <div class="timeline-title">r650 Run 8 (3 CN + 1 MN)</div>
    <div class="timeline-desc">20-hour extended window. fig_12 E complete; partial LOAD/A/B (Sherman LOAD crashes deterministically at Tree.cpp:382 — became a stress finding).</div>
  </div>
  <div class="timeline-item done">
    <div class="timeline-date">April 7-9</div>
    <div class="timeline-title">Progress presentation (Week 12)</div>
    <div class="timeline-desc">15-min Beamer covering r650 reproduction results.</div>
  </div>
  <div class="timeline-item done">
    <div class="timeline-date">April 21-26</div>
    <div class="timeline-title">CXL port engineering complete</div>
    <div class="timeline-desc"><code>CxlTransport</code> + <code>CxlDSM</code> + <code>USE_CXL=ON</code> compile flag; Docker preflight environment; debug-artifact harness; smoke gate; cache-consumption surrogate. All five build blockers cleared.</div>
  </div>
  <div class="timeline-item done">
    <div class="timeline-date">April 22-26</div>
    <div class="timeline-title">CloudLab scheduler outage</div>
    <div class="timeline-desc">Four reservations failed to bind: <code>0 available because of existing resource reservations to other projects or users</code> (the &ldquo;other project&rdquo; was ours). <code>reservationStatus</code> RPC returned a server-side Perl bug, blocking all diagnostic paths.</div>
  </div>
  <div class="timeline-item done">
    <div class="timeline-date">April 27</div>
    <div class="timeline-title">First successful r650 reservation; smoke gate FAILED</div>
    <div class="timeline-desc">2x r650 honored. Build clean, runtime SIGSEGV in <code>Tree::internal_node_search</code> after pool init. Trace captured into NFS for offline triage.</div>
  </div>
  <div class="timeline-item done">
    <div class="timeline-date">May 1</div>
    <div class="timeline-title">One-line allocator fix; CXL runs to completion</div>
    <div class="timeline-desc">Bug: <code>CxlTransport::alloc_offset_ = 0</code> overlapped <code>root_ptr_ptr</code> at 8 MB. Fix: <code>alloc_offset_(define::kChunkSize)</code> (commit <code>a3c9e87</code>). YCSB-C ran clean: 0.6 Mops/s, 10 epochs.</div>
  </div>
  <div class="timeline-item done">
    <div class="timeline-date">May 2</div>
    <div class="timeline-title">24-hour autonomous sprint (4x r650)</div>
    <div class="timeline-desc">Nine phases without human in chair. Comprehensive CXL fig_12 sweep, cross-day variance, fig_15a CXL ablation, single-CN four-method comparison (CHIME/SMART/Sherman/ROLEX), Sherman-on-CXL transport-isolation.</div>
  </div>
  <div class="timeline-item done">
    <div class="timeline-date">May 3-4</div>
    <div class="timeline-title">Report reframe + presentation delivery polish</div>
    <div class="timeline-desc">Project reframed around agent-orchestrated reproduction as primary contribution; CHIME case study secondary. 16-slide spoken arc + cuttable buffer slides.</div>
  </div>
  <div class="timeline-item active">
    <div class="timeline-date">May 5</div>
    <div class="timeline-title">Final presentation</div>
    <div class="timeline-desc">15-min slot, 12:30 spoken arc, three CloudLab API additions as the postmortem punch line.</div>
  </div>
  <div class="timeline-item upcoming">
    <div class="timeline-date">May 6</div>
    <div class="timeline-title">Final combined report due</div>
    <div class="timeline-desc">Reframe + reproduction + Sherman stress + CXL runtime + CloudLab postmortem.</div>
  </div>
</div>

## Challenges Encountered

### Hardware mismatch (March)
r650 nodes were fully booked before the Mar 26 deadline. We pivoted the dry run to r6525 nodes (AMD EPYC, ConnectX-5/6) which required code changes: <code>CPU_PHYSICAL_CORE_NUM=64</code>, public-IP memcached, NVMe storage for the 16 GB root partition.

### RoCE on r650 Clemson (April)
r650 nodes ship with ConnectX-6 Dx using RoCE v2 over Ethernet, not native InfiniBand. Six source fixes were required just to get any RDMA traffic flowing: <code>IB_DEV_NAME_IDX='2'</code>, <code>MLX_GID=3</code> (VLAN-tagged), <code>MAX_ATOMIC_ARG=8</code>, <code>max_recv_sge=2</code> for UD, OFED kernel-module restart, and a memcached.conf with both IP and port lines (the missing port line cost 10h on Run 7).

### Internal LAN versus control net
CloudLab quarantines experiments that send RDMA traffic on the control network. The fix is to provision a separate VLAN-tagged interface and bind RDMA to it; we wrote a guard script (<code>script/control-net-guard.sh</code>) that samples interface byte counters and aborts if RDMA appears on the control NIC.

### Sherman LOAD crash (independent stress finding)
At 3 CN x 64 threads, Sherman crashes deterministically at <code>Tree.cpp:382</code>: <code>Assertion `k &gt;= fence_keys.lowest' failed</code>. Static analysis identified a borrow/merge race where the parent pointer is updated after the child's lower fence widens; CHIME's <code>SIBLING_BASED_VALIDATION</code> + <code>VACANCY_AWARE_LOCK</code> close that exact window. Reported as a finding in the report.

### CloudLab scheduler outage (Apr 22-26)
Four approved r650 Clemson reservations failed to bind to experiments. The scheduler claimed capacity was held by &ldquo;other projects or users,&rdquo; but the holding project was in fact ours. The diagnostic CLI <code>reservationStatus</code> returned a server-side Perl bug, leaving no programmatic path to inspect reservation state. The PEM client cert authenticates the XML-RPC layer; JWT authenticates web cookies; neither can read reservation state without working <code>reservationStatus</code>. See the <a href="/CHIME/pdfs/final-report.pdf">final report</a> Section 7 for the full postmortem.

### CXL runtime: one-line allocator overlap
After three crashing reservations, an instrumented trace on May 1 showed <code>get_root_ptr</code> returning a level-33,025 garbage value (real value: 4) just before SIGSEGV. <code>CxlTransport::alloc</code> initialized <code>alloc_offset_ = 0</code> and grew linearly; the tree's root pointer is stored at <code>kRootPointerStoreOffest = 8 MB</code>. Once allocations crossed 8 MB, alloc handed back addresses on top of the root pointer. Fix: initialize <code>alloc_offset_(define::kChunkSize)</code>. One line, commit <code>a3c9e87</code>.

## Results

The reproduction half delivered paper-matching trends on r650 Clemson for fig_12 workloads C/D/E and fig_15a/b across all 5 methods (CHIME, Sherman, SMART, ROLEX, SMART-SC). The CXL port half delivered a complete code port with a single <code>USE_CXL=ON</code> compile flag, runtime-validated end-to-end after the May-1 allocator fix.

Headline runtime findings:

- **CXL beats RDMA on read-heavy workloads** (C, D) and **loses to RDMA on range scans** (E) at low thread counts: synchronous CXL <code>memcpy</code> cannot pipeline scan reads the way RDMA's coroutine-driven reads can.
- **CHIME-CXL is reproducible across days within ~5%**, while CHIME-RDMA varies up to ~2x on the same shared hardware. CXL is the more stable benchmark target on multi-tenant testbeds.
- **Speculative read can hurt on CXL**: at 16 threads on workload C, full CHIME-CXL is slower than +Sibling-CXL — the optimization stack that maximizes RDMA throughput is not transport-independent.
- **A Sherman-on-CXL build** (CHIME source with all 5 features off, <code>USE_CXL=ON</code>) shows the CXL win is mostly transport-driven and largely independent of CHIME's feature stack on workloads where CXL wins.
- **ROLEX-on-D crashes** at <code>Rolex.cpp:385</code> in single-CN configurations: workload D's 5% insert stream overflows the synonym-leaf chain.

Full numbers, plots, and analysis are in the [final report](/CHIME/paper/) and [presentation](/CHIME/presentation/).

## Part Two: CXL

The CXL port uses a compile-time transport abstraction layer (<code>CxlTransport</code> + <code>CxlDSM</code>) selected by <code>USE_CXL=ON</code>. NUMA emulation on r650 dual-socket nodes binds the &ldquo;remote&rdquo; pool to NUMA node 1 with <code>numa_set_preferred(1)</code>; the &ldquo;local&rdquo; CN runs on NUMA node 0. After the May-1 allocator fix, the port runs end-to-end on real r650 hardware. See the <a href="/CHIME/pdfs/final-report.pdf">final report</a> Section 7 (Late Data) and the <a href="/CHIME/presentation/">final presentation</a> for the runtime numbers.

# Part One: Reproduce CHIME Experiments on RDMA

**Created:** 2026-03-07
**Status:** Complete
**Related ADRs:** None
**Course:** CS 6204 - Advanced Topics in Systems (Spring 2026)
**Assigned Paper:** PP#4 - CHIME (SOSP '24)
**Grading:** Report 5%, Presentation 10%

---

## Overview

Part One of the course project requires reproducing the experiments from the assigned paper (CHIME, SOSP '24) using the open-source artifact code. We will run the full 5-method comparison (CHIME, Sherman, SMART, ROLEX, Marlin) on 10 CloudLab r650 nodes with RDMA. Deliverables include a LaTeX report hosted via GitHub Pages CI and a 15-20 minute Beamer presentation during Week 12 (April 7-9). As a PhD student, the expectation is thorough reproduction with analysis, not just screenshots.

---

## Problem Statement

The CHIME paper presents extensive evaluation comparing its hybrid B+tree/hopscotch index against three baselines (Sherman, SMART, ROLEX) on disaggregated memory with RDMA. We must reproduce the core experiments on CloudLab r650 hardware to verify the paper's claims and present the findings with professional-quality figures and analysis.

---

## Solution Approach

### Experiments to Reproduce

**Core (must complete):**

| Figure | Description | Runtime | Script |
|--------|-------------|---------|--------|
| Figure 12 | YCSB throughput-latency curves (5 methods x 6 workloads x multiple thread counts) | ~7h 37m | `fig_12.py` |
| Figure 14 | Cache consumption comparison | ~35m | `fig_14.py` |
| Figure 15a | Factor analysis: Sherman-based ablation | ~44m | `fig_15a.py` |
| Figure 15b | Factor analysis: ROLEX-based ablation | ~40m | `fig_15b.py` |

**Stretch (if time permits):**

| Figure | Description | Runtime | Script |
|--------|-------------|---------|--------|
| Figure 3a | Cache consumption vs amplification factor trade-off | ~23m | `fig_03a.py` |

**Total core experiment runtime:** ~9h 36m (plus ~1.5h YCSB generation per node)

### Methods Under Comparison

All five methods are confirmed compatible with the existing experiment infrastructure:

| Method | Source Repo | CMake Config Key | Notes |
|--------|-------------|-----------------|-------|
| CHIME | This repo (fork) | `"CHIME"` | Primary system |
| Sherman | This repo (included) | `"Sherman"` | B+tree baseline, built from same codebase |
| SMART | `dmemsys/SMART` (clone as sibling) | `"SMART"` | Radix tree baseline |
| ROLEX | `River861/ROLEX` (clone as sibling) | `"ROLEX"` | Learned index baseline |
| Marlin | `River861/Marlin` (clone as sibling) | `"Marlin"` | Variable-length B+tree (used in some figures) |

The experiment scripts (e.g., `fig_12.py`) drive all five methods automatically. Each method has its own CMake flags defined in `exp/params/common.json` under the `"cmake_options"` key. The scripts use `sed_generator.py` to rewrite compile-time constants in `include/Common.h` before each build variant.

### Experimental Setup (Paper Section 5.1)

- **Machines:** 10 CloudLab r650 nodes at **Clemson cluster** (Utah r650s unavailable)
- **Hardware per node:** 2x 36-core Intel Xeon CPUs, 256 GB DRAM, 100 Gbps Mellanox ConnectX-6 NIC
- **Network:** 100 Gbps Ethernet switch
- **CN config:** 4 GB DRAM cache, 64 CPU cores (each core = 1 client thread)
- **MN config:** 64 GB DRAM, 1 CPU core
- **Workloads:** YCSB with 8-byte keys and 8-byte values, 60M entries, Zipfian distribution
- **YCSB workloads:** LOAD (100% insert), A (50/50 search/update), B (95/5 search/update), C (100% search), D (95/5 search/insert), E (95/5 scan/insert)

**Reservation Strategy (updated 2026-03-08):**
- Dry run: 5x r650 at Clemson, Mar 17-19 (for setup validation and preliminary experiments)
- Full run: 10x r650 at Clemson, Mar 27-Apr 3 (for full-scale reproduction)
- Both reservations submitted via portal-cli (API endpoint: boss.emulab.net:43794); pending approval

**Repo state (as of pre–Day 1):** Experiment params (fig_12, fig_14, fig_15a, fig_15b) are patched for 10-node (9 CN + 1 MN); `common.json` has 10 IP placeholders. Day 1 automation: `construction/scripts/day1-runbook.md` and `script/day1-dry-run.sh`; after SSH and setKey, run the dry-run script then `generate-common-json.py` with real IPs.

### Build and Run Pipeline

The pipeline is fully automated via Python scripts run from the master node only:

1. **Configure** `exp/params/common.json` with cluster IPs, home directory, and workloads path
2. **Clone sibling repos** (SMART, ROLEX, Marlin) into the same parent directory as CHIME on all nodes
3. **Generate YCSB workloads** on all nodes (~1.5h per node; run in parallel)
4. **Run figure scripts** from the master node inside a tmux session:
   - Each script loads settings from `params/common.json` and `params/fig_*.json`
   - `sed_generator.py` rewrites `include/Common.h` compile-time constants for each variant
   - CMake rebuilds the target method with the appropriate flags
   - `memcached` is restarted between runs for clean state
   - Workloads are split across CNs and `ycsb_test` is launched remotely via Paramiko
   - `log_parser.py` extracts throughput and latency metrics
   - `pic_generator.py` produces PDF figures in `exp/results/`

### Deliverables

**LaTeX Report (5% of grade):**
- Professional LaTeX document with reproducibility results
- GitHub Pages CI pipeline for automatic PDF builds
- Sections: introduction, setup, methodology, results per figure, comparison with paper, analysis of discrepancies

**Beamer Presentation (10% of grade):**
- 15-20 minute presentation for Week 12 (April 7-9)
- Content: paper summary, experimental setup, methodology, results, comparison with paper figures, lessons learned
- Prepared for Q&A on CHIME internals and methodology

---

## Verification Criteria

1. All five methods (CHIME, Sherman, SMART, ROLEX, Marlin) build successfully on all 10 r650 nodes
2. `ycsb_test` completes without errors for all 6 YCSB workloads at full scale (640 threads)
3. Figure 12 throughput-latency curves show the same relative ordering as the paper (CHIME > Sherman, SMART, ROLEX)
4. Absolute throughput numbers are within ~2x of paper results (hardware generation differences expected)
5. Figure 14 cache consumption shows CHIME's advantage over baselines
6. Figures 15a/15b show monotonic improvement as techniques are added
7. LaTeX report builds via CI and is accessible on GitHub Pages
8. Presentation is rehearsed and within the 15-20 minute window

---

## Implementation Phases

### Phase A: Environment Setup (Mar 10-13)
- Reserve 10x r650 nodes on CloudLab (ASAP; reservation window: 7-10 days)
- Set up SSH keys for passwordless access between all nodes
- Install RDMA stack (MLNX OFED drivers, libibverbs, librdmacm)
- Install dependencies: memcached, CMake >= 3.12, g++ with C++17, Python3, Paramiko, matplotlib
- Configure hugepages on all nodes
- Clone CHIME, SMART, ROLEX, Marlin to all nodes

### Phase B: Build and Workload Preparation (Mar 13-15)
- Configure `exp/params/common.json` (home_dir, workloads_dir, master_ip, cluster_ips)
- Build CHIME with default flags on all nodes; verify `ycsb_test` binary produced
- Build all sibling repos (SMART, ROLEX, Marlin) on all nodes
- Generate YCSB workloads on all nodes in parallel (~1.5h)

### Phase C: Validation and Smoke Tests (Mar 15-17)
- Run `ycsb_test` with 1 CN + 1 MN (CHIME, YCSB C) as minimal smoke test
- Verify RDMA connection establishment and non-zero throughput
- Scale to 3 CNs + 1 MN
- Scale to full 10-node configuration
- Run YCSB C at full scale as baseline

### Phase D: Full Experiment Runs (Mar 17-21)
- Run `fig_12.py` inside tmux (~7.5h; can run overnight)
- Run `fig_14.py` (~35m)
- Run `fig_15a.py` (~44m)
- Run `fig_15b.py` (~40m)
- Stretch: run `fig_03a.py` (~23m)
- Save all raw logs and JSON results

### Phase E: Results and Report (Mar 21-26)
- Parse results and verify figures in `exp/results/`
- Set up LaTeX report repo with GitHub Pages CI
- Write report content: setup, methodology, results, comparison, analysis
- Compare our figures against paper figures; document discrepancies
- Submit Part One by March 26

### Phase F: Presentation (Mar 27 - Apr 6)
- Create Beamer slides (15-20 minutes of content)
- Include: paper summary, experimental setup, results, comparison, lessons learned
- Rehearse and prepare for Q&A
- Present during April 7-9

---

## Detailed Timeline

| Date | Day | Milestone | Deliverable |
|------|-----|-----------|-------------|
| **Mar 10 (Mon)** | 1 | CloudLab reservation submitted | Reservation confirmation |
| **Mar 11 (Tue)** | 2 | SSH keys + RDMA stack install | All nodes accessible, `ibv_devinfo` passes |
| **Mar 12 (Wed)** | 3 | Dependencies + hugepages + clone repos to all nodes | Build tools ready, repos cloned |
| **Mar 13 (Thu)** | 4 | Configure common.json, build all methods | All binaries compile |
| **Mar 14 (Fri)** | 5 | YCSB workload generation (all nodes, parallel) | Workload files in place |
| **Mar 15 (Sat)** | 6 | Single-node smoke test (1 CN + 1 MN) | YCSB C produces throughput > 0 |
| **Mar 16 (Sun)** | 7 | Scale to 3 nodes, then full 10 nodes | Full-scale YCSB C completes |
| **Mar 17 (Mon)** | 8 | Start fig_12.py (overnight run) | Running in tmux |
| **Mar 18 (Tue)** | 9 | fig_12 completes; run fig_14.py | fig_12 + fig_14 results |
| **Mar 19 (Wed)** | 10 | Run fig_15a.py + fig_15b.py | fig_15a + fig_15b results |
| **Mar 20 (Thu)** | 11 | Stretch: fig_03a.py; re-run any failed experiments | All experiment data collected |
| **Mar 21 (Fri)** | 12 | Parse results, generate final figures | Publication-quality PDFs |
| **Mar 22 (Sat)** | 13 | Set up LaTeX report + GitHub Pages CI | CI pipeline building PDF |
| **Mar 23 (Sun)** | 14 | Write report: setup + methodology sections | Draft sections complete |
| **Mar 24 (Mon)** | 15 | Write report: results + analysis sections | Near-complete draft |
| **Mar 25 (Tue)** | 16 | Report review and polish | Final draft |
| **Mar 26 (Wed)** | 17 | **Part One Due** | Report submitted |
| **Mar 27-31** | -- | Begin Beamer presentation | Slide outline + key figures |
| **Apr 1-4** | -- | Complete slides, rehearse | Full slide deck |
| **Apr 5-6** | -- | Final rehearsal, prepare Q&A notes | Presentation ready |
| **Apr 7-9** | -- | **Presentation (Week 12)** | Present in class |

### Critical Path

```
Reserve CloudLab (Day 1)
  -> RDMA + deps install (Day 2-3)
    -> Build all methods (Day 4)
      -> YCSB generation (Day 5)
        -> Smoke test + scale-up (Day 6-7)
          -> fig_12.py overnight (Day 8-9)
            -> fig_14, fig_15a, fig_15b (Day 9-10)
              -> Parse + figures (Day 12)
                -> LaTeX report (Day 13-17)
```

**Blocking risk:** CloudLab reservation. Must submit Day 1.

---

## Key Configuration Details

### common.json Fields to Update

```json
{
    "home_dir": "/users/<username>",
    "workloads_dir": "/users/<username>/CHIME/ycsb/workloads",
    "master_ip": "<actual master IP>",
    "cluster_ips": ["<ip1>", "<ip2>", ..., "<ip10>"]
}
```

### CMake Options per Method

Each method in `fig_12.py` uses different CMake flags from `common.json["cmake_options"]`:
- **CHIME:** Full feature set (cache, hopscotch, vacancy-aware lock, metadata replication, sibling validation, speculative read, fine-grained + greedy range query)
- **Sherman:** Cache only (all CHIME-specific features off) -- built from this same repo
- **SMART:** Separate repo, own feature flags (ART indexed cache, homogeneous internal node, lock-free internal, update-in-place leaf, rear-embedded lock)
- **ROLEX:** Separate repo, minimal flags (all CHIME features off)
- **Marlin:** Separate repo, variable-length KV with Marlin-specific tree flag

### sed_generator.py Behavior

Before each experiment variant, `sed_generator.py` rewrites constants in `include/Common.h`:
- `kClientNodeCount` -- number of compute nodes
- `kMemoryNodeCount` -- number of memory nodes
- `kMaxThread` -- threads per node (controls client count)
- `kHotspotBufSize` -- hotspot buffer size
- Various cache size parameters

The scripts handle this automatically; no manual sed commands needed.

---

## Risks and Mitigations

| Risk | Impact | Mitigation | Status |
|------|--------|------------|--------|
| CloudLab nodes unavailable for 7-10 days | Blocks all experiments | Two reservations submitted at Clemson (dry run + full run); portal-cli configured | Mitigated (pending approval) |
| RDMA stack / NIC firmware issues | Blocks experiments | Use CloudLab's known-good r650 profile; check OFED version | Open |
| Build failures on sibling repos | Missing baseline comparisons | Build each repo independently; fix CMake issues per-repo | Open |
| fig_12.py takes >7.5h or hangs | Delays timeline | Run overnight in tmux; monitor with periodic log checks | Open |
| Results differ significantly from paper | Weak presentation | Document differences honestly; analyze root causes (HW gen, network) | Open |
| Reservation expires mid-experiment | Lost progress | Save results frequently; extend reservation proactively | Open |
| GitHub Pages CI setup takes time | Delays report delivery | Use simple LaTeX->PDF workflow; CI is nice-to-have | Open |

---

## Open Questions (Resolved)

1. **How many nodes?** 10 r650 nodes -- full paper setup.
2. **Which experiments?** Figures 12, 14, 15a, 15b (core) + Figure 3a (stretch).
3. **Competitors?** Full 5-method comparison. SMART from dmemsys repo, ROLEX from River861 repo, Sherman built from this repo.
4. **What does done look like?** LaTeX report with reproduced figures + 15-20 min Beamer presentation. PhD-level analysis expected.
5. **How verified?** Same relative ordering in throughput-latency curves; absolute numbers within ~2x.

---

**Revision:** 2026-03-07 - Final specification after Q&A. Upgraded from CHIME-only to full 5-method comparison. Added Figures 15a/15b. Added report and presentation deliverable details. Resolved all open questions.

**Revision:** 2026-03-08 - Updated cluster from Utah to Clemson due to r650 unavailability. Added two-phase reservation strategy (dry run 5x Mar 17-19, full run 10x Mar 27-Apr 3). Noted timeline impact: report submitted with dry-run data, presentation uses full-scale results.

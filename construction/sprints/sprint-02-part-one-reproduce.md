# Sprint 02: Reproduce CHIME Experiments (Part One)

**Sprint Goal:** Reproduce CHIME's key experiments (Figures 12, 14, 15a, 15b) with full 5-method comparison on CloudLab r650 nodes; deliver LaTeX report and Beamer presentation
**Start Date:** 2026-03-10
**Target Date:** 2026-03-26 (Part One Due)
**Presentation:** 2026-04-07 to 2026-04-09 (Week 12)
**Status:** In Progress

**Prerequisites:** Sprint 01 (Documentation Bootstrap - Complete)

**Design Doc:** [construction/design/part-one-reproduce-experiments.md](../design/part-one-reproduce-experiments.md)

---

## Day-by-Day Timeline

### Pre-Week: Reservation Setup (Mar 8-16)

| Day | Date | Focus | Exit Criteria |
| --- | ---- | ----- | ------------- |
| -- | Mar 8 | portal-cli installed, profile created, 2 Clemson reservations submitted | DONE |
| -- | Mar 9-16 | Wait for reservation approvals; prepare scripts and configs locally | Reservations approved |

### Week 1: Dry Run -- 5x r650 at Clemson (Mar 17-19)

| Day | Date | Focus | Exit Criteria |
| --- | ---- | ----- | ------------- |
| 1 | Mon Mar 17 | SSH setup; install RDMA stack + deps on 5 nodes; configure hugepages; clone repos | All 5 nodes accessible; `ibv_devinfo` passes; repos cloned |
| 2 | Tue Mar 18 | Build all methods; generate YCSB workloads; smoke test (1 CN + 1 MN); scale to 5 nodes | Builds succeed; YCSB C produces throughput > 0 at 5-node scale |
| 3 | Wed Mar 19 | Run subset of experiments at 5-node scale (fig_14, fig_15a, fig_15b); collect preliminary data | Preliminary results for smaller experiments; identify any issues before full run |

### Week 2: Report Drafting (Mar 20-26)

| Day | Date | Focus | Exit Criteria |
| --- | ---- | ----- | ------------- |
| 4 | Thu Mar 20 | Parse dry-run results; set up LaTeX report repo + GitHub Pages CI | CI pipeline builds PDF; preliminary figures generated |
| 5 | Fri Mar 21 | Write report: introduction, experimental setup, methodology | Draft of first three sections |
| 6 | Sat Mar 22 | Write report: preliminary results sections (from dry run data) | Results sections drafted with available figures |
| 7 | Sun Mar 23 | Write report: analysis, comparison with paper (noting partial scale) | Analysis sections drafted |
| 8 | Mon Mar 24 | Write report: conclusion; review and polish | Near-final draft |
| 9 | Tue Mar 25 | Final review; prepare for submission | Draft ready for submission |
| 10 | Wed Mar 26 | **Part One report submitted** (with dry-run results; full results for presentation) | **Part One submitted** |

### Week 3-4: Full Run -- 10x r650 at Clemson (Mar 27 - Apr 3)

| Day | Date | Focus | Exit Criteria |
| --- | ---- | ----- | ------------- |
| 11 | Thu Mar 27 | SSH setup on 10 nodes; install RDMA + deps; clone repos; build all methods | All 10 nodes ready; builds succeed |
| 12 | Fri Mar 28 | Generate YCSB workloads (all nodes); smoke test; scale to 10 nodes | Full-scale YCSB C completes |
| 13 | Sat Mar 29 | Start `fig_12.py` in tmux (~7.5h overnight run) | Script running; partial logs confirm progress |
| 14 | Sun Mar 30 | Verify fig_12 results; run `fig_14.py` (~35m); run `fig_15a.py` (~44m) | fig_12 + fig_14 + fig_15a results |
| 15 | Mon Mar 31 | Run `fig_15b.py` (~40m); stretch: `fig_03a.py` (~23m); re-run any failures | All experiment data collected at full scale |
| 16 | Tue Apr 1 | Parse full-scale results; generate final figures; update report with full results | Publication-quality PDFs for all figures |
| -- | Apr 2-3 | Buffer days for re-runs or troubleshooting | All data finalized |

### Week 5: Presentation (Apr 4-9)

| Day | Date | Focus | Exit Criteria |
| --- | ---- | ----- | ------------- |
| -- | Apr 4-5 | Create Beamer slide deck with full-scale results | Slide outline complete; full-scale figures inserted |
| -- | Apr 6 | Rehearse presentation; prepare Q&A notes on CHIME internals | Comfortable with timing and material |
| -- | Apr 7-9 | **Present in class (Week 12)** | **Presentation delivered** |

---

## Tasks

### Task 1: CloudLab Reservation and SSH Setup

- [x] Install portal-cli and verify API connectivity (endpoint: boss.emulab.net:43794)
- [x] Create CloudLab profile for r650 experiment
- [x] Submit CloudLab reservations (using Clemson cluster -- r650 unavailable at Utah)
  - [x] Dry run reservation: 5x r650 at Clemson, Mar 17-19 (pending approval)
  - [x] Full run reservation: 10x r650 at Clemson, Mar 27-Apr 3 (pending approval)
- [ ] Reservations approved and confirmed
- [ ] Verify hardware: ConnectX-6 NICs, sufficient DRAM (256 GB per node)
- [ ] Generate SSH key pair and distribute to all nodes
- [ ] Verify passwordless SSH from master node to all other nodes
- [ ] Verify passwordless SSH between all node pairs (needed by Paramiko)

**Notes:**
- Using **Clemson cluster** instead of Utah due to r650 unavailability at Utah.
- Full run reservation (Mar 27-Apr 3) starts 1 day after Part One due date (Mar 26).
  This means the written report may need to be submitted before full-scale experiments complete.
  However, the presentation window (Apr 7-9) provides buffer for incorporating full results.
- Both reservations are pending approval as of Mar 8.

**Acceptance Criteria:**

- r650 nodes reserved and accessible at Clemson
- `ssh node-N hostname` works without password from master for all N

---

### Task 2: Environment Setup (RDMA, Libraries, Hugepages)

- [ ] Install MLNX OFED drivers on all nodes
- [ ] Install libibverbs, librdmacm, rdma-core on all nodes
- [ ] Verify RDMA with `ibv_devinfo` on each node
- [ ] Install memcached on master node; verify it starts
- [ ] Install CMake (>= 3.12), g++ (C++17 support) on all nodes
- [ ] Install Python3, Paramiko, matplotlib, numpy on master node
- [ ] Configure hugepages on all nodes (`echo 10240 > /proc/sys/vm/nr_hugepages`)
- [ ] Verify hugepage allocation with `cat /proc/meminfo | grep Huge`

**Acceptance Criteria:**

- `ibv_devinfo` shows active RDMA device on every node
- `memcached -h` runs on master
- `cmake --version` >= 3.12 on all nodes
- Hugepages allocated on all nodes

---

### Task 3: Clone Repositories to All Nodes

- [ ] Clone CHIME (this repo) to home directory on all nodes
- [ ] Clone `dmemsys/SMART` as sibling directory on all nodes
- [ ] Clone `River861/ROLEX` as sibling directory on all nodes
- [ ] Clone `River861/Marlin` as sibling directory on all nodes
- [ ] Verify directory structure: `~/CHIME`, `~/SMART`, `~/ROLEX`, `~/Marlin` on every node

**Acceptance Criteria:**

- All four repos present in home directory on all 10 nodes
- `ls ~/CHIME ~/SMART ~/ROLEX ~/Marlin` succeeds on every node

---

### Task 4: Configure common.json and Build All Methods

- [ ] Update `exp/params/common.json` fields: `home_dir`, `workloads_dir`, `master_ip`, `cluster_ips`
- [ ] Build CHIME: `mkdir build && cd build && cmake .. <CHIME flags> && make -j`
- [ ] Build Sherman (same repo, different CMake flags): verify binary works
- [ ] Build SMART in `~/SMART`: follow its build instructions
- [ ] Build ROLEX in `~/ROLEX`: follow its build instructions
- [ ] Build Marlin in `~/Marlin`: follow its build instructions
- [ ] Fix any compile errors (missing headers, library paths, CMake version issues)

**Acceptance Criteria:**

- `ycsb_test` binary produced for CHIME and Sherman
- SMART, ROLEX, Marlin each produce their benchmark binary
- Builds succeed on all 10 nodes

---

### Task 5: YCSB Workload Generation

- [ ] Run `cd ~/CHIME/ycsb && sh generate_full_workloads.sh` on all nodes (in parallel)
- [ ] Wait for completion (~1h 28m per node)
- [ ] Verify workload files exist at `workloads_dir` path on every node
- [ ] Verify file count and sizes match expectations (6 workload types, 60M entries each)

**Acceptance Criteria:**

- YCSB workload files for LOAD, A, B, C, D, E present on all 10 nodes
- File path matches `workloads_dir` in common.json

---

### Task 6: Single-Node Smoke Test

- [ ] Start memcached on master node
- [ ] Run `ycsb_test` with 1 CN + 1 MN using CHIME config
- [ ] Run YCSB LOAD (insert all entries) -- verify completion
- [ ] Run YCSB C (100% search) -- verify non-zero throughput
- [ ] Check for RDMA connection errors, crashes, or hangs
- [ ] Parse output manually to confirm metrics (throughput, latency) are printed

**Acceptance Criteria:**

- YCSB LOAD completes without errors
- YCSB C produces throughput > 0 Mops/s
- No RDMA connection failures or segfaults

---

### Task 7: Multi-Node Scale-Up

- [ ] Scale to 3 CNs + 1 MN; run YCSB C
- [ ] Scale to full 10-node configuration (9 CNs + 1 MN)
- [ ] Run YCSB C at full scale (640 threads)
- [ ] Verify throughput scales approximately with client count
- [ ] Debug any multi-node issues (memcached discovery, synchronization, timeouts)
- [ ] Test with YCSB A (write-heavy) to verify write path works at scale

**Acceptance Criteria:**

- Full 10-node YCSB C run completes
- Throughput at 10 nodes is significantly higher than at 1 node
- No node failures or timeouts

---

### Task 8: Run Core Experiments

- [ ] Create tmux session on master node
- [ ] Run `python3 fig_12.py` (~7h 37m; start evening of Day 8, check morning Day 9)
- [ ] Verify fig_12 output: JSON results + PDF in `exp/results/`
- [ ] Run `python3 fig_14.py` (~35m)
- [ ] Verify fig_14 output
- [ ] Run `python3 fig_15a.py` (~44m)
- [ ] Verify fig_15a output
- [ ] Run `python3 fig_15b.py` (~40m)
- [ ] Verify fig_15b output
- [ ] Save all raw logs from each run

**Acceptance Criteria:**

- JSON results files exist for fig_12, fig_14, fig_15a, fig_15b
- PDF figures generated in `exp/results/`
- No experiment scripts crashed or produced empty results

---

### Task 9: Stretch -- Run fig_03a.py

- [ ] Run `python3 fig_03a.py` (~23m)
- [ ] Verify output: cache consumption vs amplification factor plot
- [ ] Compare against paper Figure 3a

**Acceptance Criteria:**

- fig_03a PDF generated
- Results show expected trade-off curve

---

### Task 10: Parse Results and Generate Figures

- [ ] Review all generated PDFs in `exp/results/`
- [ ] Compare each figure against corresponding paper figure
- [ ] Document discrepancies with hypotheses (hardware generation, network conditions, etc.)
- [ ] Re-generate any figures that need cleanup or annotation
- [ ] Export final figures for inclusion in LaTeX report

**Acceptance Criteria:**

- Publication-quality figures for all core experiments
- Written notes comparing each figure to the paper version
- Figures ready for LaTeX inclusion

---

### Task 11: LaTeX Report Infrastructure + GitHub Pages CI

- [ ] Create LaTeX report directory structure (or separate branch/repo)
- [ ] Set up basic LaTeX template (article class, standard packages)
- [ ] Configure GitHub Actions workflow: LaTeX build -> PDF artifact
- [ ] Configure GitHub Pages deployment for the built PDF
- [ ] Verify CI pipeline: push triggers build; PDF accessible via Pages URL

**Acceptance Criteria:**

- `git push` triggers LaTeX build in CI
- PDF accessible at GitHub Pages URL
- Build completes without LaTeX errors

---

### Task 12: Write Report Content

- [ ] Introduction: paper summary, motivation for reproduction
- [ ] Experimental setup: hardware, software, configuration details
- [ ] Methodology: which figures, how scripts work, any modifications
- [ ] Results -- Figure 12: throughput-latency curves with analysis
- [ ] Results -- Figure 14: cache consumption with analysis
- [ ] Results -- Figure 15a: Sherman-based factor analysis
- [ ] Results -- Figure 15b: ROLEX-based factor analysis
- [ ] Results -- Figure 3a (if completed): trade-off analysis
- [ ] Comparison with paper: side-by-side discussion, discrepancy analysis
- [ ] Conclusion: key findings, lessons learned, what worked/didn't

**Acceptance Criteria:**

- All sections complete and proofread
- Figures embedded with captions
- Analysis goes beyond "we got similar numbers" -- PhD-level discussion
- Report submitted by March 26

---

### Task 13: Beamer Presentation

- [ ] Create Beamer slide deck outline (15-20 slides)
- [ ] Slide content: paper summary (2-3 slides), CHIME architecture (2 slides)
- [ ] Slide content: experimental setup and methodology (2-3 slides)
- [ ] Slide content: reproduced results with figures (4-6 slides)
- [ ] Slide content: comparison with paper results (2-3 slides)
- [ ] Slide content: lessons learned and challenges (1-2 slides)
- [ ] Rehearse to 15-20 minute target
- [ ] Prepare notes for anticipated Q&A (CHIME internals, hopscotch hashing, RDMA details)

**Acceptance Criteria:**

- Beamer PDF with 15-20 slides
- Presentation fits within 15-20 minute window
- Speaker comfortable with Q&A on CHIME design and methodology

---

## Architecture Decisions

- Full 5-method comparison (CHIME, Sherman, SMART, ROLEX, Marlin) -- not CHIME-only
- Use paper's default parameters (span=64, neighborhood=8, hotspot buffer=30MB)
- Run all experiment scripts unmodified from master node only
- LaTeX report with GitHub Pages CI for automatic PDF deployment
- **Clemson cluster** (not Utah) for r650 nodes due to availability constraints
- **Two-phase execution:** dry run (5 nodes, Mar 17-19) for validation + preliminary data; full run (10 nodes, Mar 27-Apr 3) for publication-quality results
- Report submitted Mar 26 with dry-run data; presentation (Apr 7-9) uses full-scale data

---

## Dependencies

- CloudLab r650 node availability at **Clemson cluster** (Utah r650s unavailable)
  - Dry run: 5x r650, Mar 17-19
  - Full run: 10x r650, Mar 27-Apr 3
- RDMA hardware and MLNX OFED driver compatibility
- Working memcached for metadata coordination
- YCSB workload generator (included in repo at `ycsb/generate_full_workloads.sh`)
- Sibling repos: SMART (dmemsys), ROLEX (River861), Marlin (River861)

---

## Risks

| Risk | Mitigation | Status |
| ---- | ---------- | ------ |
| Clemson reservation approval delayed or denied | Both reservations submitted early (Mar 8); follow up with CloudLab support; explore other clusters if needed | Open |
| r650 nodes at Clemson differ from Utah r650s (firmware, NIC config) | Test thoroughly during dry run (Mar 17-19); document any differences | Open |
| Full run starts after Part One due date (Mar 27 > Mar 26) | Submit report with dry-run (5-node) results; update with full-scale results for presentation (Apr 7-9) | **Active** |
| RDMA stack incompatibility on current CloudLab images | Use known-good r650 profile; check OFED version against CHIME requirements | Open |
| Sibling repos fail to build | Build each independently; check their READMEs for deps; fix CMake issues | Open |
| fig_12.py hangs or crashes mid-run (~7.5h) | Run in tmux; monitor logs periodically; re-run individual workloads if partial failure | Open |
| Results differ significantly from paper | Document honestly; analyze root causes (HW gen, NIC firmware, network topology) | Open |
| GitHub Pages CI setup takes too long | Fallback: manual PDF build and submission; CI is nice-to-have | Open |
| Dry run (5 nodes) insufficient to reproduce all figures accurately | Focus dry run on smaller experiments (fig_14, fig_15a/b); save fig_12 for full run | Open |

---

## Key Milestones

| Date | Milestone | Weight |
| ---- | --------- | ------ |
| Mar 8 | Reservations submitted at Clemson (portal-cli + profile) | DONE |
| Mar 16 | Reservations approved | Gate |
| Mar 17 | Dry run begins: 5x r650 at Clemson | Gate |
| Mar 19 | Dry-run experiments complete; preliminary data collected | Gate |
| Mar 26 | **Part One report submitted** (with dry-run results) | **Deadline** |
| Mar 27 | Full run begins: 10x r650 at Clemson | Gate |
| Mar 31 | All core experiment data collected at full scale (fig_12, 14, 15a, 15b) | Gate |
| Apr 1 | Full-scale figures generated | Checkpoint |
| Apr 7-9 | **Presentation delivered** (with full-scale results) | **Deadline** |

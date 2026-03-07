# Sprint 02: Reproduce CHIME Experiments (Part One)

**Sprint Goal:** Reproduce CHIME's key experiments (Figures 12, 14, 15a, 15b) with full 5-method comparison on CloudLab r650 nodes; deliver LaTeX report and Beamer presentation
**Start Date:** 2026-03-10
**Target Date:** 2026-03-26 (Part One Due)
**Presentation:** 2026-04-07 to 2026-04-09 (Week 12)
**Status:** Not Started

**Prerequisites:** Sprint 01 (Documentation Bootstrap - Complete)

**Design Doc:** [construction/design/part-one-reproduce-experiments.md](../design/part-one-reproduce-experiments.md)

---

## Day-by-Day Timeline

### Week 1: Setup and Build (Mar 10-16)

| Day | Date | Focus | Exit Criteria |
| --- | ---- | ----- | ------------- |
| 1 | Mon Mar 10 | Reserve 10x r650 nodes on CloudLab; set up SSH keys | Reservation confirmed; passwordless SSH between all nodes |
| 2 | Tue Mar 11 | Install MLNX OFED, libibverbs, librdmacm, rdma-core; verify RDMA | `ibv_devinfo` shows active device on every node |
| 3 | Wed Mar 12 | Install memcached, CMake, g++, Python3, Paramiko, matplotlib; configure hugepages | All build tools available; hugepages allocated |
| 4 | Thu Mar 13 | Clone CHIME + SMART + ROLEX + Marlin to all nodes; configure common.json | Repos present on all nodes; common.json has correct IPs and paths |
| 5 | Fri Mar 14 | Build all 5 methods on all nodes; fix any compile errors | `ycsb_test` binary produced for CHIME, Sherman; SMART/ROLEX/Marlin build clean |
| 6 | Sat Mar 15 | Generate YCSB workloads on all nodes in parallel (~1.5h) | Workload files present at configured path on every node |
| 7 | Sun Mar 16 | Single-node smoke test (1 CN + 1 MN, YCSB C); scale to 3 nodes; scale to 10 nodes | Full-scale YCSB C completes with non-zero throughput |

### Week 2: Experiments and Results (Mar 17-23)

| Day | Date | Focus | Exit Criteria |
| --- | ---- | ----- | ------------- |
| 8 | Mon Mar 17 | Start `fig_12.py` in tmux on master node (runs ~7.5h, finishes overnight) | Script running; partial logs confirm progress |
| 9 | Tue Mar 18 | Verify fig_12 results; run `fig_14.py` (~35m) | fig_12 JSON + PDF in results/; fig_14 complete |
| 10 | Wed Mar 19 | Run `fig_15a.py` (~44m) and `fig_15b.py` (~40m) | fig_15a + fig_15b results collected |
| 11 | Thu Mar 20 | Stretch: run `fig_03a.py` (~23m); re-run any failed experiments | All core data collected; stretch data if time allows |
| 12 | Fri Mar 21 | Parse all results; regenerate figures if needed; verify against paper | Publication-quality PDFs for all core figures |
| 13 | Sat Mar 22 | Set up LaTeX report repo; configure GitHub Pages CI for PDF builds | CI pipeline builds PDF on push |
| 14 | Sun Mar 23 | Write report: introduction, experimental setup, methodology | Draft of first three sections |

### Week 3: Report and Submission (Mar 24-26)

| Day | Date | Focus | Exit Criteria |
| --- | ---- | ----- | ------------- |
| 15 | Mon Mar 24 | Write report: results sections (one per figure), comparison with paper | Results sections drafted with embedded figures |
| 16 | Tue Mar 25 | Write report: analysis of discrepancies, conclusion; review and polish | Near-final draft; all sections complete |
| 17 | Wed Mar 26 | Final review; submit Part One report | **Part One submitted** |

### Week 4-5: Presentation (Mar 27 - Apr 9)

| Day | Date | Focus | Exit Criteria |
| --- | ---- | ----- | ------------- |
| -- | Mar 27-31 | Create Beamer slide deck: paper summary, setup, methodology, results | Slide outline complete; key figures inserted |
| -- | Apr 1-4 | Complete slides; add comparison plots; write speaker notes | Full 15-20 min deck ready |
| -- | Apr 5-6 | Rehearse presentation; prepare Q&A notes on CHIME internals | Comfortable with timing and material |
| -- | Apr 7-9 | **Present in class (Week 12)** | **Presentation delivered** |

---

## Tasks

### Task 1: CloudLab Reservation and SSH Setup

- [ ] Submit CloudLab reservation for 10x r650 nodes (7-10 day window starting Mar 10)
- [ ] Verify hardware: ConnectX-6 NICs, sufficient DRAM (256 GB per node)
- [ ] Generate SSH key pair and distribute to all nodes
- [ ] Verify passwordless SSH from master node to all other nodes
- [ ] Verify passwordless SSH between all node pairs (needed by Paramiko)

**Acceptance Criteria:**

- 10 r650 nodes reserved and accessible
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

---

## Dependencies

- CloudLab r650 node availability (10 nodes, 7-10 day reservation)
- RDMA hardware and MLNX OFED driver compatibility
- Working memcached for metadata coordination
- YCSB workload generator (included in repo at `ycsb/generate_full_workloads.sh`)
- Sibling repos: SMART (dmemsys), ROLEX (River861), Marlin (River861)

---

## Risks

| Risk | Mitigation | Status |
| ---- | ---------- | ------ |
| CloudLab reservation fails or expires mid-experiment | Reserve Day 1; request extension proactively; save results frequently | Open |
| RDMA stack incompatibility on current CloudLab images | Use known-good r650 profile; check OFED version against CHIME requirements | Open |
| Sibling repos fail to build | Build each independently; check their READMEs for deps; fix CMake issues | Open |
| fig_12.py hangs or crashes mid-run (~7.5h) | Run in tmux; monitor logs periodically; re-run individual workloads if partial failure | Open |
| Results differ significantly from paper | Document honestly; analyze root causes (HW gen, NIC firmware, network topology) | Open |
| GitHub Pages CI setup takes too long | Fallback: manual PDF build and submission; CI is nice-to-have | Open |
| Time pressure: 17 working days to submission | Prioritize core experiments (fig_12 first); report and slides can overlap | Open |

---

## Key Milestones

| Date | Milestone | Weight |
| ---- | --------- | ------ |
| Mar 10 | CloudLab reservation confirmed | Gate |
| Mar 14 | All methods build on all nodes | Gate |
| Mar 16 | Full-scale smoke test passes | Gate |
| Mar 19 | All core experiment data collected (fig_12, 14, 15a, 15b) | Gate |
| Mar 21 | Final figures generated | Checkpoint |
| Mar 26 | **Part One report submitted** | **Deadline** |
| Apr 7-9 | **Presentation delivered** | **Deadline** |

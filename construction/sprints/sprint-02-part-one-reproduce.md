# Sprint 02: Reproduce CHIME Experiments (Part One)

**Sprint Goal:** Reproduce CHIME's key experiments (Figures 12, 14, 15a, 15b) with full 5-method comparison on CloudLab; deliver LaTeX report and Beamer presentation
**Start Date:** 2026-03-10
**Target Date:** 2026-03-26 (Part One Due)
**Presentation:** 2026-04-07 to 2026-04-09 (Week 12)
**Status:** In Progress

**Prerequisites:** Sprint 01 (Documentation Bootstrap - Complete)

**Design Doc:** [construction/design/part-one-reproduce-experiments.md](../design/part-one-reproduce-experiments.md)  
**Setup Checklist:** [construction/scripts/setup-checklist.md](../scripts/setup-checklist.md)  
**Scripts README:** [construction/scripts/README.md](../scripts/README.md)

---

## Current State (Mar 23 -- r6525 Pre-Deadline Run Active)

### Hardware Change: r6525 instead of r650

- Original dry-run reservation (5x r650, Mar 17-19) expired without use
- New reservation **83cd62fd** (11x r6525 Clemson) approved and active since Mar 23 14:00 UTC
- Experiment created via CloudLab API: ID **4fc8525b**, profile `chime-r6525-clemson`
- Extended to **Mar 26 07:04 UTC**
- r6525 differences from r650: AMD EPYC (64 physical cores, not 72), ConnectX-6 Dx, 1.5TB NVMe

### Node Status

- 11 nodes provisioned, but **node10 (clnode304) has broken RDMA** -- excluded
- Running with **10 nodes (9 CN + 1 MN)** -- matches original CN count target
- `CPU_PHYSICAL_CORE_NUM` patched from 72 to 64 across all repos (r6525 has 64 physical cores)

### Setup Completed

- SSH keys distributed to all nodes
- MLNX OFED installed and verified on all working nodes
- `installLibs.sh` completed on all nodes
- Hugepages configured on all nodes
- Sibling repos (SMART, ROLEX) cloned on all nodes
- NVMe drives (1.5TB) mounted on all nodes (root partition only 16GB -- insufficient for workloads)
- memcached.conf fixed: wrong IP (10.10.1.2) replaced with public IP (130.127.134.72) on all repos/nodes
- All builds successful: CHIME, SMART, ROLEX (Sherman uses CHIME repo with different flags)

### YCSB Workloads

- All 11 workloads fully generated: la, a, b, c, d, e, 40M-120M
- Python 2/3 incompatibility in YCSB `bin/ycsb` and workload specs -- fixed
- Slow Python parsing of large files -- used awk for faster `gen_workload.py` processing
- Workloads copied to project NFS: `/proj/cs620426sp-PG0/ycsb_workloads/` for future reuse

### Experiment Progress (as of Mar 23 ~16:00 UTC)

- **fig_15b**: RUNNING (started ~15:56 UTC, ROLEX ablation, ~40 min)
- **Pipeline**: fig_15b -> fig_15a -> fig_12 -> fig_14 -> extra experiments
- 3 extra experiment scripts created: `extra_cache_sensitivity.py`, `extra_value_size.py`, `extra_uniform_dist.py`

### Issues Encountered and Resolved

1. Node10 (clnode304) broken RDMA -- excluded, patched CN count to 9
2. 16GB root partition filled during workload generation -- mounted NVMe drives on all nodes
3. YCSB Python 2/3 incompatibility -- fixed `bin/ycsb` script and workload spec files
4. memcached.conf had wrong IP (10.10.1.2 vs 130.127.134.72) -- fixed on all repos/nodes
5. `gen_workload.py` parsing too slow for large files -- used awk for faster parsing
6. SSH keys lost after `killall` -- re-distributed

---

## Day-by-Day Timeline

### Pre-Week: Reservation Setup (Mar 8-16)

| Day | Date | Focus | Exit Criteria |
| --- | ---- | ----- | ------------- |
| -- | Mar 8 | portal-cli installed, profile created, 2 Clemson reservations submitted | DONE |
| -- | Mar 9-16 | Wait for reservation approvals; prepare scripts and configs locally | Reservations approved |

### Week 1: Dry Run -- SKIPPED (reservation expired unused)

| Day | Date | Focus | Exit Criteria |
| --- | ---- | ----- | ------------- |
| 1-3 | Mar 17-19 | 5x r650 reservation expired without use (scheduling conflict) | SKIPPED |

### Week 2: r6525 Pre-Deadline Run (Mar 23-26) -- ACTIVE

| Day | Date | Focus | Exit Criteria |
| --- | ---- | ----- | ------------- |
| 1 | Sun Mar 23 | 11x r6525 provisioned; setup (SSH, OFED, libs, hugepages, repos, builds, workloads); fig_15b started | DONE -- all setup complete, fig_15b running |
| 2 | Mon Mar 24 | Complete experiment pipeline: fig_15a, fig_12 (~7.5h), fig_14; extra experiments | All core experiments complete |
| 3 | Tue Mar 25 | Parse results; generate figures; write/finalize report | Report near-final; figures ready |
| 4 | Wed Mar 26 | **Part One report submitted** (reservation ends 07:04 UTC) | **Part One submitted** |

### Week 3-4: Full Run -- 10x r650 at Clemson (Mar 27 - Apr 3)

| Day | Date | Focus | Exit Criteria |
| --- | ---- | ----- | ------------- |
| 5 | Thu Mar 27 | SSH setup on 10 nodes; install RDMA + deps; clone repos; build all methods; copy workloads from NFS | All 10 nodes ready; builds succeed |
| 6 | Fri Mar 28 | Smoke test; scale to 10 nodes; start `fig_12.py` (~7.5h overnight) | Full-scale YCSB C completes; fig_12 running |
| 7 | Sat Mar 29 | Verify fig_12 results; run `fig_14.py` (~35m); run `fig_15a.py` (~44m) | fig_12 + fig_14 + fig_15a results |
| 8 | Sun Mar 30 | Run `fig_15b.py` (~40m); stretch: `fig_03a.py` (~23m); extra experiments; re-run any failures | All experiment data collected at full scale |
| 9 | Tue Apr 1 | Parse full-scale results; generate final figures; update report with full results | Publication-quality PDFs for all figures |
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
  - [x] Dry run reservation: 5x r650 at Clemson, Mar 17-19 (EXPIRED unused)
  - [x] Full run reservation: 10x r650 at Clemson, Mar 27-Apr 3 (APPROVED, 1cf9c2b4)
  - [x] Re-run reservation: 11x r650 at Clemson, Apr 3-6 (APPROVED, 5488ef67)
  - [x] Pre-deadline reservation: 11x r6525 at Clemson, Mar 23-26 (APPROVED, 83cd62fd)
- [x] Reservations approved and confirmed
- [x] Create r6525 profile (`chime-r6525-clemson`) for pre-deadline run
- [x] Experiment instantiated via API (ID 4fc8525b), extended to Mar 26 07:04 UTC
- [x] Verify hardware: ConnectX-6 Dx NICs, 256 GB DRAM, 64 physical cores (AMD EPYC)
- [x] Generate SSH key pair and distribute to all nodes
- [x] Verify passwordless SSH from master node to all other nodes
- [x] Verify passwordless SSH between all node pairs (needed by Paramiko)

**Notes:**

- Using **Clemson cluster** instead of Utah due to r650 unavailability at Utah.
- Original dry run (b11e25ca, 5x r650 Mar 17-19) expired without use.
- Pre-deadline run uses **r6525** (not r650): AMD EPYC 64-core, ConnectX-6 Dx, 1.5TB NVMe.
- Node10 (clnode304) has broken RDMA -- excluded. Running 10 nodes (9 CN + 1 MN).
- Full run (1cf9c2b4, 10x r650 Mar 27-Apr 3) and re-run (5488ef67, 11x r650 Apr 3-6) still available for r650-based results.
- SSH keys had to be re-distributed after `killall` wiped ssh-agent.

**Acceptance Criteria:**

- r650 nodes reserved and accessible at Clemson
- `ssh node-N hostname` works without password from master for all N

---

### Task 2: Environment Setup (RDMA, Libraries, Hugepages)

- [x] Install MLNX OFED drivers on all nodes
- [x] Install libibverbs, librdmacm, rdma-core on all nodes
- [x] Verify RDMA with `ibv_devinfo` on each node (node10 broken -- excluded)
- [x] Install memcached on master node; verify it starts
- [x] Install CMake (>= 3.12), g++ (C++17 support) on all nodes
- [x] Install Python3, Paramiko, matplotlib, numpy on master node
- [x] Configure hugepages on all nodes (`sudo bash setup-hugepages.sh` or `echo 36864 > /proc/sys/vm/nr_hugepages`)
- [x] Verify hugepage allocation with `cat /proc/meminfo | grep Huge`
- [x] Mount NVMe drives (1.5TB) on all nodes (root partition only 16GB)
- [x] Patch `CPU_PHYSICAL_CORE_NUM` from 72 to 64 (r6525 has 64 physical cores)
- [x] Fix memcached.conf IP (10.10.1.2 -> 130.127.134.72) on all repos/nodes

**Acceptance Criteria:**

- `ibv_devinfo` shows active RDMA device on every node
- `memcached -h` runs on master
- `cmake --version` >= 3.12 on all nodes
- Hugepages allocated on all nodes

---

### Task 3: Clone Repositories to All Nodes

- [x] Clone CHIME (this repo) to home directory on all nodes
- [x] Clone `dmemsys/SMART` as sibling directory on all nodes
- [x] Clone `River861/ROLEX` as sibling directory on all nodes
- [ ] Clone `River861/Marlin` as sibling directory on all nodes (not needed for current experiments)
- [x] Verify directory structure: `~/CHIME`, `~/SMART`, `~/ROLEX` on every node

**Acceptance Criteria:**

- CHIME, SMART, ROLEX repos present in home directory on all working nodes
- `ls ~/CHIME ~/SMART ~/ROLEX` succeeds on every node

---

### Task 4: Configure common.json and Build All Methods

- [x] Update `exp/params/common.json` fields: `home_dir`, `workloads_dir`, `master_ip`, `cluster_ips` with real IPs
- [x] Build CHIME: `mkdir build && cd build && cmake .. <CHIME flags> && make -j`
- [x] Build Sherman (same repo, different CMake flags): verify binary works
- [x] Build SMART in `~/SMART`: follow its build instructions
- [x] Build ROLEX in `~/ROLEX`: follow its build instructions
- [ ] Build Marlin in `~/Marlin`: follow its build instructions (not needed for current experiments)
- [x] Fix any compile errors (missing headers, library paths, CMake version issues)
- [x] Patch `CPU_PHYSICAL_CORE_NUM` to 64 in all repos' `include/Common.h`

**Acceptance Criteria:**

- `ycsb_test` binary produced for CHIME and Sherman
- SMART, ROLEX each produce their benchmark binary
- Builds succeed on all working nodes (10 of 11)

---

### Task 5: YCSB Workload Generation

- [x] Generate all 11 workloads: la, a, b, c, d, e, 40M-120M
- [x] Fix YCSB Python 2/3 incompatibility in `bin/ycsb` and workload spec files
- [x] Fix slow `gen_workload.py` parsing -- used awk for large files
- [x] Verify workload files exist at `workloads_dir` path on every node
- [x] Verify file count and sizes match expectations
- [x] Copy workloads to project NFS `/proj/cs620426sp-PG0/ycsb_workloads/` for future reuse

**Acceptance Criteria:**

- YCSB workload files for LOAD, A, B, C, D, E (+ large variants) present on all working nodes
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

- [x] Create tmux session on master node
- [ ] Run `python3 fig_15b.py` (~40m) -- **RUNNING** (started ~15:56 UTC Mar 23)
- [ ] Verify fig_15b output
- [ ] Run `python3 fig_15a.py` (~44m)
- [ ] Verify fig_15a output
- [ ] Run `python3 fig_12.py` (~7h 37m)
- [ ] Verify fig_12 output: JSON results + PDF in `exp/results/`
- [ ] Run `python3 fig_14.py` (~35m)
- [ ] Verify fig_14 output
- [ ] Run extra experiments: `extra_cache_sensitivity.py`, `extra_value_size.py`, `extra_uniform_dist.py`
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
- **Three-phase execution:** pre-deadline run (11x r6525, Mar 23-26) for initial results; full run (10x r650, Mar 27-Apr 3); re-run (11x r650, Apr 3-6) for publication-quality results
- Report submitted Mar 26 with r6525 data; presentation (Apr 7-9) uses r650 full-scale data
- `CPU_PHYSICAL_CORE_NUM` must be patched per hardware (64 for r6525, 72 for r650)
- NVMe drives required for workload storage (root partition only 16GB on CloudLab nodes)
- YCSB workloads cached on project NFS for faster setup on future reservations

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
| Clemson reservation approval delayed or denied | Both reservations submitted early (Mar 8); follow up with CloudLab support; explore other clusters if needed | **Resolved** -- all reservations approved |
| r6525 hardware differences (AMD EPYC, ConnectX-6 Dx) | Patched CPU_PHYSICAL_CORE_NUM to 64; verified RDMA works; documented differences | **Resolved** |
| Node failures (broken RDMA on node10) | Excluded node10; patched CN count to 9; still matches paper's 9 CN target | **Resolved** |
| Full run starts after Part One due date (Mar 27 > Mar 26) | Pre-deadline r6525 run (Mar 23-26) provides data for report; r650 run for presentation | **Mitigated** |
| 16GB root partition insufficient for workloads | Mounted NVMe drives (1.5TB) on all nodes | **Resolved** |
| YCSB Python 2/3 incompatibility | Fixed bin/ycsb and workload specs for Python 3 | **Resolved** |
| memcached.conf wrong IP breaks experiment coordination | Fixed IP on all repos/nodes | **Resolved** |
| fig_12.py hangs or crashes mid-run (~7.5h) | Run in tmux; monitor logs periodically; re-run individual workloads if partial failure | Open |
| Results differ significantly from paper (r6525 vs r650) | Document hardware differences; r650 full run provides direct comparison | Open |
| GitHub Pages CI setup takes too long | Fallback: manual PDF build and submission; CI is nice-to-have | Open |
| Experiment pipeline does not complete before reservation expires (Mar 26 07:04 UTC) | Prioritize core experiments (fig_15b, fig_15a, fig_12, fig_14); extras are stretch | **Active** |

---

## Key Milestones

| Date | Milestone | Weight |
| ---- | --------- | ------ |
| Mar 8 | Reservations submitted at Clemson (portal-cli + profile) | DONE |
| Mar 16 | Reservations approved | DONE |
| Mar 17-19 | Dry run (5x r650) -- SKIPPED (reservation expired) | SKIPPED |
| Mar 23 | r6525 pre-deadline run begins: 11x r6525 provisioned, setup complete, experiments started | **DONE** |
| Mar 24 | Core experiments complete on r6525 (fig_15b, 15a, 12, 14) | Gate |
| Mar 25 | Results parsed; figures generated; report drafted | Gate |
| Mar 26 | **Part One report submitted** (with r6525 results; reservation ends 07:04 UTC) | **Deadline** |
| Mar 27 | Full run begins: 10x r650 at Clemson (1cf9c2b4) | Gate |
| Mar 31 | All core experiment data collected at full r650 scale | Gate |
| Apr 1 | Full-scale r650 figures generated | Checkpoint |
| Apr 3-6 | Re-run: 11x r650 at Clemson (5488ef67) for any missing data | Buffer |
| Apr 7-9 | **Presentation delivered** (with full-scale r650 results) | **Deadline** |

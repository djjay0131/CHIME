# Progress

## Completed

### Phase 1: Bootstrap
- `construction/` and `llm/memory_bank/` directories with documentation
- Codebase guide (`construction/design/codebase-guide.md`)
- `exp/fig_03a.py` walkthrough documentation

### Phase 2 Planning
- Design spec: `construction/design/part-one-reproduce-experiments.md`
- Sprint plan: `construction/sprints/sprint-02-part-one-reproduce.md`
- 5-method scope, 4 core figures + stretch, day-by-day timeline

### CloudLab Infrastructure (Mar 8–Apr 7)
- CloudLab REST API operational (`boss.emulab.net:43794`, `x-api-token` header)
- Profile `chime-r650-clemson-lan` with parameterized node count and hardware type
- Setup scripts: `setup-r650.sh` (7-phase automated setup), `run-experiments.sh`, `pull-results.sh`
- Automation: `generate-common-json.py`, `patch-cn-count.py`, `setup-checklist.md`, `day1-runbook.md`
- `smoke_test.py`, `resilient_runner.py` with checkpoint resume

### r6525 Pre-Deadline Run (Mar 23–26)
- 11x r6525 provisioned, 9 CN + 1 MN (node10 broken RDMA)
- Experiments completed: fig_15b, fig_15a, fig_12, fig_14, extras
- Results on non-paper-matched hardware (AMD EPYC vs Intel Xeon)

### r650 RDMA Pipeline Validation (Mar 27–Apr 3)
- Runs 1–4 on r650 Clemson: progressively debugged RDMA setup
- Discovered internal LAN requirement (control net RDMA = quarantine)
- Identified and validated RoCE config: `IB_DEV_NAME_IDX='2'`, `MLX_GID=3` (for VLAN)
- VLAN setup via `sudo /usr/local/etc/emulab/rc/rc.ifconfig`
- memcached.conf requires 2 lines (IP + port)

### r650 Data Collection — Run 7 (Apr 5–6)
- 6x r650 Clemson (5 CN + 1 MN), 16h experiment
- fig_15a: complete (6 methods × 5 workloads)
- fig_15b: complete (5 methods × 4 workloads) — 36 min runtime
- fig_12 YCSB C: complete (5 methods × 8 points)
- fig_12 YCSB D: complete (5 methods × 8 points)
- Lost ~10h to memcached.conf bug (missing port line)

### r650 Data Collection — Run 8 (Apr 6–7)
- 4x r650 Clemson (3 CN + 1 MN), 20h experiment (16h + 4h extension)
- fig_12 YCSB E: complete (5 methods × 6 points)
- fig_12 YCSB LOAD: partial (CHIME + SMART done; Sherman crashes with RDMA assertion)
- fig_12 YCSB A: completed on remote but NOT pulled before expiry
- fig_12 YCSB B: partial (CHIME 5/8 pts), not pulled
- Lost A results due to late pull scheduling (root of `feedback_pull_results_early.md`)

### CXL Transport Layer (Apr 1–3, build-fixed Apr 21)
- `include/CxlTransport.h` + `src/CxlTransport.cpp` — NUMA-emulated transport
- `include/CxlDSM.h` + `src/CxlDSM.cpp` — drop-in DSM replacement
- `DSM.h` gated with `#ifdef USE_CXL`
- Feature spec: `llm/features/cxl-implementation.md` (status: IMPLEMENTED Phase 1)
- **Build verified end-to-end in Docker** (`Dockerfile.cxl-preflight`, commit `e430d8d`) — 5 additional blockers fixed beyond `152b4e9`

### Part One Deliverables
- Part One progress report (`report/main.tex`)
- Hugo site with GitHub Pages CI
- Beamer presentation with VT branding and r650 results (`presentation/main.tex`, presented Apr 7–9)

### Final-Project Specification (Apr 21–22)
- `llm/features/final-project.md` — SPECIFIED with 14 ACs (CXL eval + Part One closure + deliverables)
- `report/main-partwo.tex` — Part Two report skeleton
- Three-phase timeline: P1 hardware day, P2 analysis+stretch, P3 deliverable polish

### Pre-Hardware Tooling (Apr 22–23)
- `Dockerfile.cxl-preflight` — Ubuntu 20.04 amd64 reference CXL build environment
- `Dockerfile.ycsb-gen` — YCSB workload generator with `2to3 -w` (deferred to cluster)
- `exp/run_harness.py` + tests — debug-artifact capture on failure (8/8 tests pass)
- `exp/fig_14_surrogate.py` + tests — single-point cache-consumption driver (5/5 tests pass)
- `exp/plot_fig_12_three_way.py` + tests — multi-series plot helper (5/5 tests pass)
- `construction/scripts/runbook-day1.md` — hardware-window playbook
- `construction/scripts/smoke-gate.sh` — automated CXL go/no-go gate
- `construction/design/sherman-load-crash-analysis.md` — Sherman baseline static analysis

## Hardware Window Failures (Apr 22–26)

- **Apr 22 reservation `43677ece`** (2×r650 Clemson, 8h): expired unused. Pre-hardware tooling overran the window.
- **Apr 23 reservation `5565ec96`** (2×r650 Clemson, 8h): every `startExperiment` failed with "Resource reservation violation: 0 r650 available because of existing resource reservations to other projects or users." Window expired with no successful experiments.
- **Apr 25 retry**: same failure mode against active multi-day reservations (UUIDs `8c36e934`, `cc0bf3c0`, spanning 4/20–4/25 and 4/21–4/26).
- **Apr 26 retry**: same failure mode persists.
- Indirect signal: `createReservation -n` dry-runs show r650 Clemson booked through Apr 27 — capacity exists, but the scheduler doesn't link it to CS620426SP.
- `reservationStatus` CLI is broken server-side (`Undefined subroutine &main::DoStatus`) — cannot inspect reservation state to diagnose.

## In Progress

- Awaiting reservation-detail fields (Project / Cluster / Type) from user's web UI to diagnose scheduler mismatch.
- Drafted CloudLab support email at `files/cloudlab-support-email-draft.md` (not yet sent).
- Part Two report skeleton `report/main-partwo.tex` waiting on data (or pivoting to "blocked by scheduler" narrative).

## Remaining (Hardware-Dependent)

- fig_12 YCSB A and B on r650 (need 2+ nodes, ~2h runtime)
- fig_12 YCSB LOAD for Sherman/ROLEX/SMART-SC (or annotate Sherman as known-limit)
- fig_14 cache-consumption (or use `fig_14_surrogate.py` single-point)
- CXL smoke gate on dual-socket r650 (NUMA emulation)
- CXL fig_12 sweep + single-node RDMA baseline + fig_15a/b ablation
- Three-way RDMA-multi vs RDMA-single vs CXL comparison plot
- Part Two report population
- Final presentation
- `v2.0-final` release tag before May 5

## Known Issues

- **CloudLab scheduler bug**: approved reservations not being matched to CS620426SP experiments. Three windows lost.
- **`reservationStatus` server-side bug**: `Undefined subroutine &main::DoStatus` blocks CLI diagnostics.
- **Sibling CXL ports deferred**: SMART/ROLEX/Marlin not ported. Post-hardware-day if at all.
- **Sherman LOAD crash**: `Assertion 'k >= fence_keys.lowest' failed` (Tree.cpp:382) — baseline limitation, framed as report finding via static analysis (no fix attempt on cluster).
- **YCSB 60M+ workload generation**: deferred to r650 (CloudLab Ubuntu has Python 2; Mac+Docker hit cascading Py2→Py3 issues).
- **RDMA build not Docker-verifiable**: `ibv_exp_dct` is MLNX OFED userspace only.

Last updated: 2026-04-26

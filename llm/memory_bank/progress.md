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

### CloudLab Infrastructure (Mar 8 – Apr 7)
- CloudLab REST API operational (`boss.emulab.net:43794`, `x-api-token` header, JWT)
- Profile `chime-r650-clemson-lan` with parameterized node count and hardware type
- Setup scripts: `setup-r650.sh` (7-phase automated setup), `run-experiments.sh`, `pull-results.sh`
- `smoke_test.py`, `resilient_runner.py` with checkpoint resume

### r6525 Pre-Deadline Run (Mar 23–26)
- 11× r6525 provisioned, 9 CN + 1 MN
- fig_15b, fig_15a, fig_12, fig_14 results on AMD EPYC (not paper-matched)

### r650 RDMA Pipeline Validation (Mar 27 – Apr 3)
- Runs 1–4 progressively debugged RDMA setup
- Identified RoCE config: `IB_DEV_NAME_IDX='2'`, `MLX_GID=3`
- Internal LAN over `vlan296` MTU 9000

### r650 Data Collection — Run 7 / Run 8 (Apr 5–7)
- 6× / 4× r650 Clemson, multi-CN setup
- fig_15a, fig_15b, fig_12 C/D/E across 5 methods (CHIME, Sherman, SMART, ROLEX, SMART-SC)
- Apr 27 1-CN-baseline RDMA sweep at high thread counts (`fig_12_*_sweep.jsonl`)

### CXL Transport Layer (Apr 1 – May 1)
- `include/CxlTransport.h` + `src/CxlTransport.cpp` — NUMA-emulated transport
- `include/CxlDSM.h` + `src/CxlDSM.cpp` — drop-in DSM replacement
- `DSM.h` gated with `#ifdef USE_CXL`
- Build verified end-to-end in Docker (`Dockerfile.cxl-preflight`)
- **Single-line allocator-overlap bug fixed (commit `a3c9e87`, May 1):** `CxlTransport::alloc_offset_(define::kChunkSize)` reserves the first 16 MB so the allocator never collides with `root_ptr_ptr` at `kRootPointerStoreOffest = kChunkSize/2 = 8 MB`. Bug haunted three reservations.

### CXL Runtime Data (May 1 – May 2)
- `fig_12_cxl_sweep.jsonl` + `fig_12_cxl_de.jsonl` — 17 data points across C/D/E single-CN
- `chime_cxl_may2_{c,d,e}.jsonl` — full reproducibility re-run on May 2 (within ~5 % of May 1)
- `cxl_ablation.jsonl` — 6-variant ablation at T=16 / 32 (Sherman → +hopscotch → +vacancy → +metadata → +sibling → CHIME)

### Competitor Single-CN Comparison (May 2)
- `smart_{c,d,e}_sweep.jsonl` — full SMART sweep on r650 1 CN + 1 MN
- `sherman_{c,d,e}_sweep.jsonl` — full Sherman (CHIME source with features off)
- `rolex_c_sweep.jsonl` — full ROLEX C; D/E crash documented
- `sherman_cxl_{c,d,e}.jsonl` — Sherman-on-CXL via CHIME's transport
- `chime_rdma_may2_{c,d,e}.jsonl` — same-day CHIME-RDMA reference for cross-day comparison

### Findings Documented in Report (May 2)
- **CXL allocator bug + fix** (§ "Resolution: May 1 reservation").
- **Three-workload CXL evaluation**: workload-dependent (CXL wins C/D, loses E) — `fig12-rdma-vs-cxl.pdf`, `fig12-cxl-rdma-ratio.pdf`.
- **Late-data: competitor methods on single-CN hardware** — `fig12-competitors.pdf`.
- **ROLEX-D synonym-leaf assertion** — `Rolex.cpp:385`, single-CN scaling limit.
- **Sherman-on-CXL**: separates transport-driven from feature-driven CXL benefit — `fig12-transport-method.pdf`.
- **Cross-day RDMA variance + CXL reproducibility** — `fig12-cxl-reproducibility.pdf`.
- **CXL fig_15a ablation: speculative read can hurt on CXL** — `fig15a-cxl-ablation.pdf`.

### Pre-Hardware Tooling (Apr 22–23)
- `Dockerfile.cxl-preflight` — Ubuntu 20.04 amd64 reference CXL build environment
- `exp/run_harness.py` + tests (8/8 pass) — debug-artifact capture on failure
- `exp/fig_14_surrogate.py` + tests (5/5) — single-point cache-consumption driver
- `exp/plot_fig_12_three_way.py` + tests (5/5) — multi-series plot helper
- `construction/scripts/runbook-day1.md` — hardware-window playbook
- `construction/scripts/smoke-gate.sh` — automated CXL go/no-go gate

### Control-Net Mitigation (May 2)
After CloudLab admin email re: unusual control-network traffic on the May 1 reservation:

- `script/control-net-guard.sh` — on-node sampler of `/sys/class/net/<iface>/statistics/{rx,tx}_bytes`. Aborts experiment at 500 MB cumulative public traffic.
- `script/run-with-guard.sh` — wraps any `ycsb_test` invocation with the guard.
- `script/cloudlab-status-watch.sh` — portal API status (no ssh polling).
- `script/prep-experiment.sh` — 8-step idempotent post-provision setup; auto-launches the guard on every node.
- `script/launch-experiment.sh` — creates an experiment from `chime-r650-clemson-lan`.
- `script/autonomous-runner.sh` — cluster-side 24-hour 8-phase autonomous experiment driver.
- `files/cloudlab-control-net-reply.md` — admin reply draft + Gmail draft to `portal-ops@cloudlab.us`.

### Final-Project Deliverables State (May 2)
- `report/main-partwo.tex`: 34 pages, all major findings present, builds clean, bibliography resolves.
- `presentation/main.tex`: 48 pages, includes CXL Runtime Results section (3 slides), Competitor Methods (2 slides), CXL fig_15a finding, Cross-day variance.
- All sweep JSONL data committed under `exp/results/may2-competitors/` and `exp/results/rdma-2node-04271959/`.
- 18 commits pushed to `origin/main` since Apr 28.

## In Progress (May 2 17:00 UTC — May 3 17:00 UTC sprint)

- Phase 0: experiment `chime-r650-may2` provisioning (status: `provisioning` at 17:02 UTC).
- Heartbeat cron `*/29 * * * *` will be armed by the launch-retry cron once status=ready.
- Cluster-side autonomous-runner.sh will drive phases 1–8 over the 24-hour window.

## Remaining

### Sprint phases pending (this 24h window)
- Multi-CN (3 CN + 1 MN) data for CHIME / SMART / Sherman / ROLEX × C/D/E
- Variance reps for CHIME-CXL T=16/32 × C/D/E × 5
- **CXL port engineering for SMART and ROLEX** (Phase 4, Claude human-in-loop)
- SMART-CXL + ROLEX-CXL sweeps (Phase 5)
- T=96 / T=128 high-thread sweeps (Phase 6)
- Workload A/B retry at 3 CN + 1 MN (Phase 7)
- 30-rep variance run for cross-day claim (Phase 8)

### Post-sprint (May 3 17:00 → May 5)
- Integrate sprint findings into report and slides
- Final polish on prose (parallel paper-writer Claude session)
- `v2.0-final` release tag before May 5 presentation

### Next reservation (May 6 → May 11, 7× r650)
- Repeat similar matrix at higher CN counts if useful
- Long-running stability tests
- Extra CXL ablations not yet covered

## Known Issues

- **Cross-day RDMA variance (~2×)** at the same hardware class — root cause likely warm-vs-cold cache + NIC queue state. Documented as a finding rather than a bug.
- **Sherman LOAD crash**: `Tree.cpp:382` fence-key invariant under split/borrow at single-CN. CHIME closes this race via SIBLING_BASED_VALIDATION + VACANCY_AWARE_LOCK. Static analysis in report.
- **Sherman A/B at single-CN**: assertion at `Tree.cpp:1596`. Phase 7 of sprint will retry at 3 CN + 1 MN.
- **ROLEX D/E at single-CN**: synonym-chain overflow at `Rolex.cpp:385`. Phase 2 of sprint will retry at 3 CN + 1 MN.
- **CloudLab cross-experiment-boundary scheduler bug**: documented with five reproducible UUIDs; support ticket pending response.
- **CloudLab control-net traffic alert** (May 1, resolved): mitigations now in repo.

Last updated: 2026-05-02

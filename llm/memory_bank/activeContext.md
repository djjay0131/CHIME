# Active Context

## Current Focus

**Final-deliverable polish window (May 3–6).** Experiments are complete; data is committed; report and presentation now reframed around agent-orchestrated CloudLab reproduction as the spine, with CHIME and CXL findings as the case study (per `llm/features/final-project-reframe.md`, IMPLEMENTED 2026-05-03). Next experiments not until 2026-05-05 21:00; the May-2 24-hour sprint completed before this reframe was authored. No parallel session is running.

## Spec

- `llm/features/final-presentation-delivery.md` (IMPLEMENTED 2026-05-04, AC-D4 user-rehearsal pending) — May 5 talk delivery: 15 spoken slides (1 title + 14 frames), 12:30 total, every slide ≤30 body words, both `main.pdf` and `main-notes.pdf` build, cut-here marker on slide 11. Backup contains 36 frames, headline-suppressed via `\setbeamertemplate{headline}{}` after `\appendix`. Verification: `bash scripts/verify-presentation-delivery.sh` PASS.
- `llm/features/final-project-reframe.md` (VERIFIED 2026-05-04) — preceding reframe spec. Spine reframe at title, abstract, contributions block, conclusion opener; new `\section{Approach: Agent-Orchestrated Experimentation Pipeline}` (§3) with four subsections; ORNL XLOOP'25 differentiation paragraph; verification scripts at `scripts/verify-reframe.sh`. All four quality gates PASS, all 12 ACs satisfied (with two coherence-justified deviations: reading-guide update in §1 and ORNL bibitem on references slide). Surface-area tripwire reports 20% (at the floor).
- `llm/features/final-project-no-hardware.md` (IMPLEMENTED) — superseded by the reframe at the spine level; body sections (§4–§9) intact.
- `llm/features/final-project.md` (Apr 21) — preserved as historical context.

## Hardware Status (May 2, 2026)

- **Reservation `312ca700`**: 4× r650 Clemson, 17:00 UTC May 2 → 17:00 UTC May 3. Active. Experiment `chime-r650-may2` (id `a417376d-1db8-4f65-b2b2-1f513519aa39`) created and provisioning.
- **Reservation `8971e238`**: 7× r650 Clemson, 01:00 UTC May 6 → 01:00 UTC May 11. Approved, awaiting use.
- **Scheduler bug closure**: documented across-experiment-boundary recurrence with five UUID reproductions; CloudLab support email drafted at `files/cloudlab-control-net-reply.md`.
- **CloudLab admin email about unusual control-net traffic** (May 1): cause was sustained ssh-tail polling from the laptop. Mitigations now in `script/control-net-guard.sh`, `script/run-with-guard.sh`, `script/cloudlab-status-watch.sh` (portal API instead of ssh).

## Key Findings Collected (Apr 27 — May 2)

1. **CHIME-CXL works** after a single-line allocator-overlap fix (`CxlTransport::alloc_offset_(define::kChunkSize)`, commit `a3c9e87`). Workloads C, D, E now run end-to-end on a single-process NUMA-emulated CXL transport.
2. **Cross-day reproducibility**: CHIME-CXL re-runs across days within ~5%; CHIME-RDMA varies up to ~2× on the same hardware class. The reproducibility finding is the cleanest "research" result of the project.
3. **Speculative read can hurt on CXL** (`fig15a-cxl-ablation.pdf`): full CHIME-CXL is slower than +Sibling-CXL at 16 threads on workload C. Mechanism: speculative read hides RDMA round-trip; on synchronous CXL it just serializes.
4. **Sherman-on-CXL** (commit `6171be0`): Sherman built from CHIME source with all 5 features off, USE_CXL=on. Shows the CXL benefit is mostly transport-driven (1.4× at T=4 on C) and roughly matches CHIME's same-day CXL/RDMA ratio. The CXL feature stack is mostly orthogonal to CHIME's optimizations on the workloads where CXL wins.
5. **ROLEX-D synonym-leaf assertion**: ROLEX crashes at `Rolex.cpp:385` on workload D at single-CN due to synonym-chain overflow. Predicted to clear at 3 CN + 1 MN (Phase 2 of the 24h sprint will test).
6. **Single-CN four-method comparison**: SMART, Sherman, CHIME, ROLEX C peak within a 1.4× band on a single CN — the paper's wider gaps appear at multi-CN scale.

## Sprint Phase Plan (24 h)

| Phase | Window (UTC)        | Goal                                                          |
| ----- | ------------------- | ------------------------------------------------------------- |
| 0     | 17:00 – 17:20       | prep-experiment, smoke RDMA + CXL                             |
| 1     | 17:20 – 19:20       | 3 CN + 1 MN: CHIME / SMART / Sherman C/D/E (RDMA)             |
| 2     | 19:20 – 20:20       | 3 CN + 1 MN: ROLEX C/D/E (test synonym-leaf at multi-CN)      |
| 3     | 20:20 – 22:20       | CHIME-CXL variance: T=16/32 × C/D/E × 5 reps                  |
| 4     | 22:20 – 02:20       | **CXL ports for SMART/ROLEX** (Claude human-in-loop)          |
| 5     | 02:20 – 06:20       | SMART-CXL + ROLEX-CXL sweeps                                  |
| 6     | 06:20 – 09:20       | T=96 / T=128 high-thread on CXL + 3 CN RDMA                   |
| 7     | 09:20 – 13:20       | Workloads A/B retry at 3 CN + 1 MN                            |
| 8     | 13:20 – 16:20       | Long variance: T=16, 30 reps each transport                   |
| 9     | 16:20 – 17:00       | Final pulldown, plots, report append, push                    |

## Storage / Sweep Pattern

- Cluster writes to `/proj/cs620426sp-PG0/djjay-results/may2-24h/` (NFS, persistent).
- Master node updates a heartbeat file every 60 s.
- Laptop pulls a single `scp -r` of the results directory per wakeup (every ~29 min) — replaces the per-poll `ssh tail` pattern that triggered CloudLab's unusual-traffic alert.
- Plots regenerate locally from the pulled JSONL.

## Deliverables State

- **Report** (`report/main-partwo.tex`): 34 pages. Abstract + Contributions reflect runtime CXL findings. New paragraphs for ROLEX-D crash, Sherman-on-CXL, cross-day variance, CXL reproducibility, CXL fig_15a. Builds clean. Bibliography resolves.
- **Presentation** (`presentation/main.tex`): 48 pages. New section "CXL Runtime Results" (3 slides), new section "Competitor Methods, Same Hardware" (2 slides), 2 slides on cross-day variance + CXL fig_15a finding.
- **Both PDFs**: committed and pushed to `origin/main`.
- **Site CI**: `.github/workflows/build-and-deploy.yml` builds both report variants; pushes to `origin/main` trigger Hugo rebuild.

## Key Entry Points (current)

- `construction/sprints/sprint-may2-24h.md` — active sprint plan
- `script/autonomous-runner.sh` — cluster-side 8-phase runner
- `script/cloudlab-status-watch.sh` — portal API status (no ssh)
- `script/prep-experiment.sh` — idempotent post-provision setup
- `script/control-net-guard.sh` — on-node byte-counter guard
- `script/run-with-guard.sh` — wraps ycsb_test invocations with guard
- `exp/plot_competitor_comparison.py`, `exp/plot_transport_method.py`, `exp/plot_cxl_reproducibility.py`, `exp/plot_cxl_ablation.py` — finding-specific renderers

## Coordination With Parallel Claude Session

- This session: experiment driving + finding additions. Owns `script/`, `exp/results/`, `exp/plot_*.py`, `report/figures/*.pdf`, `construction/sprints/`.
- Other session (paper writer): editorial polish on `report/main-partwo.tex`, `references.bib`, `presentation/main.tex`.
- Conflict avoidance: this session does `git pull --rebase` before every commit; only **appends** to `.tex` files (new `\paragraph`s and figure refs); never rewrites their prose.

Last updated: 2026-05-02

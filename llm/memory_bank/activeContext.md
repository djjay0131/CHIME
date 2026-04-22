# Active Context

## Current Focus

**Pre-hardware-day execution for final-project delivery.** Reservation opens 15:00 UTC today (Apr 22, 2-node r650 Clemson, 8h, UUID `43677ece`). All off-hardware work scheduled for completion before the window opens.

## Spec

`llm/features/final-project.md` — SPECIFIED with 14 ACs covering CXL evaluation, Part One closure, report/presentation/release artifacts. Most ACs are hardware-dependent and unlock during/after tomorrow's window.

## Completed Today (pre-hardware)

- **CXL build works end-to-end in Docker** (`Dockerfile.cxl-preflight`) — catches 5 additional blockers beyond the earlier CXL commit set (`include/Common.h`, `src/Common.cpp`, `src/Tree.cpp`, `src/CxlDSM.cpp`). Committed as `e430d8d`.
- **`exp/run_harness.py`** with debug-artifact capture on failure: core dump, stderr, git SHA, CMakeCache, Common.h, hostname/hugepage state. 8/8 local tests pass (`exp/tests/test_run_harness.py`). Covers AC-14.
- **`exp/fig_14_surrogate.py`** — single-point cache-consumption driver for 60M keys, schema in JSON. 5/5 parser tests pass. Foundation for AC-13.
- **`exp/plot_fig_12_three_way.py`** — multi-series throughput-latency plot helper for multi-node RDMA + single-node RDMA + CXL. 5/5 loader tests pass. Foundation for AC-4.
- **Sibling repos cloned** at `/Users/djjay0131/code/SMART`, `ROLEX-1`, `Marlin`. Layout-inventory confirms CHIME-compatible harness.
- **Sherman Tree.cpp:382 static analysis** — `construction/design/sherman-load-crash-analysis.md`. Hypothesis: the `k >= fence_keys.lowest` assertion has no escape hatch for borrow/merge-induced fence widening under concurrent reads. `SIBLING_BASED_VALIDATION` + `VACANCY_AWARE_LOCK` close the window in CHIME. Framed as a finding about Sherman's baseline, not a bug to fix.
- **YCSB workload generator Dockerfile** (`Dockerfile.ycsb-gen`) — in progress. YCSB 0.17.0 ships Py2 syntax; using `2to3 -w` at image build time.

## In Progress

- YCSB 60M-key workload generation deferred to the r650 (CloudLab Ubuntu image has Python 2 available; local Mac + Docker hit cascading Py2→Py3 issues that would cost an hour to chase). Plan: generate on r650 at cluster bring-up — ~20 min of reservation time. Needed only for AC-13 (fig_14 surrogate), stretch.

## Known Limitations

- **RDMA build cannot be verified in stock Docker** — CHIME uses `ibv_exp_dct` (Mellanox experimental extension only in MLNX OFED userspace). Updated AC-7 to scope Docker preflight to CXL-only; RDMA regression check happens on cluster via AC-12 (per-thread throughput vs Part One baseline).
- **Sibling CXL ports deferred**: SMART, ROLEX, Marlin need their own CxlTransport/CxlDSM ported. Not 5-fix patches. Post-hardware-day work if CHIME-on-CXL succeeds tomorrow.
- **Sherman LOAD crash is baseline limitation**, not fixable without adopting CHIME's validation techniques. Report handling: annotate partial data point; do not debug on cluster.

## Hardware Window

- **Opens:** Apr 22, ≥15:00 UTC (reservation `43677ece`, 2×r650 Clemson, 8h)
- **Critical gate:** CXL smoke test at 0:40 — must pass both YCSB LOAD (5s, exercises CAS/alloc) and YCSB C (30s, exercises reads). Failure → pivot to Part One closure.
- **Fallback sequence** documented in spec `§Fallbacks for Reservation Denial`.

## Files Created Today

- `Dockerfile.cxl-preflight` (extended with `libibverbs-dev`, `libmemcached-dev` — harmless even though RDMA build hits `ibv_exp_*`)
- `Dockerfile.ycsb-gen`
- `exp/run_harness.py` + `exp/tests/test_run_harness.py`
- `exp/fig_14_surrogate.py` + `exp/tests/test_fig_14_surrogate.py`
- `exp/plot_fig_12_three_way.py` + `exp/tests/test_plot_fig_12_three_way.py`
- `construction/design/sherman-load-crash-analysis.md`
- `llm/features/final-project.md` (SPECIFIED)
- `report/main-partwo.tex` (skeleton, from previous session)

## Files Modified Today

- `llm/features/final-project.md` — AC-7 scoped to CXL-only per Docker findings
- `include/Common.h`, `src/Common.cpp`, `src/Tree.cpp`, `src/CxlDSM.cpp` — CXL build blockers (committed in `e430d8d`)

## Key Entry Points (updated)

- `exp/run_harness.py` — wrap ycsb_test invocations tomorrow for auto-artifact capture
- `exp/fig_14_surrogate.py` — single-point cache measurement at 60M keys
- `exp/plot_fig_12_three_way.py` — render comparison PDF from three JSON sources
- `Dockerfile.cxl-preflight` — reference build environment (CXL-only)
- `construction/design/sherman-load-crash-analysis.md` — feeds Part Two report narrative

Last updated: 2026-04-22

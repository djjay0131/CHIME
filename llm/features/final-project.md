# Feature: Final Project Delivery (CS 6204 Course Wrap-Up)

**Status:** SPECIFIED
**Date:** 2026-04-21
**Author:** Feature Architect (AI-assisted)

## Problem

The CS 6204 course project has three outstanding deliverables against a hard May 5 deadline and a late-April final presentation: (1) the CXL-ported CHIME evaluation, (2) a polished Part One (loose ends: fig_12 YCSB A/B, Sherman LOAD crash, fig_14), and (3) a reproducible artifact (tagged release, CI-green code, published GitHub Pages site). The CXL code now compiles end-to-end as of commit `e430d8d`, but has never executed a real workload on hardware. Reservation availability on CloudLab r650 is unreliable — tomorrow's 2-node, 8-hour window (UUID `43677ece`, Apr 22 ≥15:00 UTC) is the only confirmed slot, and it must deliver the bulk of the CXL data before further access can be scheduled. Without a hard-scheduled plan that (a) treats the CXL smoke test as the critical gate, (b) parallelizes off-hardware work, and (c) degrades gracefully when reservations are denied, the project will miss either the deadline or the PhD-rigor bar — both have been confirmed as non-negotiable.

## Goals

- **Results bar:** All figures for CHIME on CXL (fig_12 A-E, fig_15a, fig_15b) collected on r650 hardware, with a matched single-node RDMA baseline from the same reservation for apples-to-apples transport comparison.
- **Analysis bar:** Written analysis in `report/main-partwo.tex` explaining *why* CXL and RDMA differ per-technique (hopscotch leaves, vacancy-aware locks, metadata replication, sibling-based validation, speculative read), grounded in numbers from (1).
- **Engineering bar:** Code reproduces end-to-end from a fresh clone via `docker build -f Dockerfile.cxl-preflight && make`; CI green on `main`; `v2.0-final` tag on both the CHIME repo and competitor forks; GitHub Pages site serves the Part One + Part Two reports; all `TODO` markers removed from `main-partwo.tex`.
- **Breadth stretch:** Other 4 methods (Sherman, SMART, ROLEX, Marlin) ported to CXL for at least one workload (YCSB C) if Day-1 CHIME-only work completes ahead of schedule.
- **Part One closure:** Either collect the missing fig_12 A/B data on a secured later reservation, or document the gap explicitly with the partial data plotted and captioned.
- **Deliverables:** Final Beamer presentation (late April), populated `main-partwo.tex` (May 5), tagged release.

## Non-Goals

- Modifying CHIME's core index algorithm (B+tree/hopscotch logic is untouched — only the transport layer).
- Real CXL hardware (NUMA emulation on r650 dual-socket is the stated scope).
- Re-running Part One multi-node RDMA data from scratch — the existing fig_12 C/D/E + fig_15a/b on 3-5 CN Clemson r650 is reused directly with captioned provenance.
- Debugging Sherman's LOAD crash *inside* a reservation window — investigation happens off-hardware against the source.
- Generating YCSB 60M-120M workloads on the reserved hardware — workload generation is CPU-bound and happens on the local Mac or any spare box.
- Supporting fig_3a, fig_14 at larger scale (120M+), or any figure not already planned in `cxl-implementation.md`.

## User Stories

- As a PhD student, I want a time-boxed plan that turns tomorrow's 8-hour reservation into measurable progress, so that I do not waste the only confirmed hardware slot on indecision or on work that could run elsewhere.
- As a PhD student, I want a graceful-degradation order of operations, so that partial reservation access still yields a submittable artifact.
- As the course instructor, I want to see a reproducible artifact with three-way comparison plots and rigorous per-technique analysis, so that I can assess the work at the PhD bar.
- As a future reader, I want a tagged release with a working Docker build and a published report, so that I can re-run the experiments without cluster access.

## Design Approach

### Timeline (three-phase arc)

| Phase | Dates | Mode | Primary output |
|-------|-------|------|----------------|
| **P1: Hardware day** | Apr 22, 15:00-23:00 UTC | 2×r650 Clemson | CXL data for CHIME across all workloads + single-node RDMA baseline |
| **P2: Analysis + stretch** | Apr 23-29 | Off-hardware + opportunistic reservations | Sherman crash investigation, workload gen for fig_14, other-method CXL ports, additional reservations if needed |
| **P3: Deliverable polish** | Apr 30 - May 5 | Off-hardware | Populate `main-partwo.tex`, build final presentation, cut release, publish site |

### The CXL Smoke Test Is the Critical Gate

Tomorrow's window has one irreversible decision point at ≈0:40 elapsed: does the CXL port produce correct numbers? If yes, all downstream work proceeds. If no, the slot pivots to Part One closure (collect fig_12 YCSB A/B, regenerate 60M-120M workloads on the cluster, attempt fig_14). This branch point is the single biggest risk in the plan.

The gate must exercise **both** read and write paths, because a 100% read workload does not exercise CAS, faa, or write batching — which have the most non-trivial CXL-specific code. The gate comprises two micro-runs:

1. **Write-heavy micro-check (≈5s of YCSB LOAD):** loads 10K keys; exercises `cas_sync`, `alloc`, and on-chip-memory routing. Must complete without assertion failure or segfault.
2. **Read-heavy micro-check (≈30s of YCSB C):** reads from the loaded key space; exercises read batching and speculative reads. Must report throughput > 0.

Both must pass before committing to the 3-hour fig_12 CHIME-CXL run.

### Parallelization Principle

Anything that can run off the reserved hardware must run off the reserved hardware. That includes: workload generation (60M-120M YCSB datasets), Sherman crash static analysis, LaTeX writing, presentation layout, CI setup, release scripting. The 8-hour window is reserved only for things that demand the r650 hardware specifically: CXL builds, RDMA baseline runs, cluster-level orchestration.

### Scope Ordering Inside the Window

When time pressure hits during tomorrow's run, cut from the bottom of this list first:

1. Cluster bring-up + CXL smoke test (non-negotiable gate)
2. CHIME CXL fig_12 (A-E + LOAD): the central evaluation artifact
3. Single-node RDMA baseline for same-scale transport comparison
4. CHIME CXL fig_15a/15b (ablation): analysis-bar material
5. Other-method CXL ports (Sherman/SMART/ROLEX/Marlin) — stretch

### Three-Way Comparison Data Sources

| Series | Data provenance | Collected |
|--------|-----------------|-----------|
| Multi-node RDMA | Part One existing data (fig_12 C/D/E, fig_15a/b on 3-5 CN r650 Clemson) | Already in `exp/results/` (runs 7-8, Apr 5-7) |
| Single-node RDMA | Tomorrow's 1 CN + 1 MN run (2-node reservation) | Apr 22 |
| Single-node CXL | Tomorrow's 1-node NUMA emulation | Apr 22 |

The multi-node RDMA series is reused from Part One with explicit captioning of CN count and date. No re-collection. This is the only decision that trades rigor for time — justified because re-running would consume a reservation we don't yet have.

### Pre-Tomorrow Tasks (today, before 15:00 UTC Apr 22)

These are off-hardware tasks that must complete **before** the reservation window opens, because they de-risk what happens tomorrow:

- **Extend the Docker preflight to cover the RDMA build path** — install `libibverbs-dev`, `libmemcached-dev`, `libboost-coroutine-dev`, `libboost-context-dev`; verify `cmake .. && make -j` (no `USE_CXL`) compiles cleanly. Catches any silent RDMA regression from the CXL refactor commits (`152b4e9`, `e430d8d`).
- **Apply the 5 CHIME CXL fixes to each sibling repo** (SMART, ROLEX, Sherman, Marlin) via the same Docker preflight. Each should pass `cmake -DUSE_CXL=ON .. && make -j`. If any sibling has a unique blocker (e.g., different DSM call site, different coroutine macro pattern), document the fix and commit. This prevents burning tomorrow's time on sibling discovery.
- **Start YCSB 60M-80M-100M-120M workload generation** on local Mac (multi-hour CPU job). Needed for fig_14 full and for the fig_14 surrogate (60M alone is enough for the surrogate).
- **Static analysis of Sherman LOAD crash**: read `src/Tree.cpp:382` and the fence_keys invariant chain. Identify root cause candidate. This enables the crash to be framed as a finding in the report rather than a blocker.

### Fallbacks for Reservation Denial

- **No additional reservation secured by Apr 26:** Ship report with CXL data + Part One multi-node RDMA + single-node RDMA baseline. Fig_14 is omitted with a one-paragraph explanation of the workload-generation blocker. Other-method CXL ports stay at YCSB C only or absent.
- **Tomorrow's smoke test fails:** Pivot remaining time to Part One closure (fig_12 A/B with RDMA) and document the CXL port as "compiles, runtime blocker identified (cite log line)." Report focuses on Part One polish + CXL design retrospective.
- **Tomorrow's reservation denied at start:** Deliver the entire report from existing Part One data + CXL design chapter (no CXL experimental data). Explicitly scope-mark in the abstract.

## Sample Implementation

```python
# final-project delivery scheduler — see Phase 5 pseudocode for full version.
# This version shows the critical branching logic in ≈60 lines.

GATE_TIMEOUT_SEC = 60  # the CXL smoke test must complete in under 60 seconds

def main():
    cluster = reserve_or_abort(uuid="43677ece")
    bringup(cluster, timeout_min=20)
    verify_ibv(cluster, device="mlx5_2")

    # Gate: CXL smoke test. Everything downstream depends on this.
    smoke = run_timed(
        cluster.node(0),
        "cd CHIME/build-cxl && cmake -DUSE_CXL=ON .. && make -j && "
        "./test/ycsb_test 1 8 1 randint c",
        timeout=GATE_TIMEOUT_SEC,
    )
    if smoke.exit_code != 0 or smoke.throughput == 0:
        # Pivot to Part One closure — don't burn the slot.
        run(fig_12_rdma.py, workloads=["a", "b"], cluster=cluster)
        commit_failure_note("smoke_failed", smoke.stderr)
        return

    # Happy path: collect CHIME-on-CXL across all workloads.
    for w in "abcde":           # LOAD is appended after — SMART-sibling crash risk
        run_and_pull(fig_12_cxl.py, workload=w, method="CHIME")
    try_or_log(run_and_pull, fig_12_cxl.py, workload="LOAD", method="CHIME")

    # Matched single-node RDMA baseline (1 CN + 1 MN since we only got 2 nodes)
    run_and_pull(fig_12_rdma_2cn.py, cluster=cluster, cn_count=1)

    # Ablation (same node, rebuild per variant)
    for variant in ABLATION_SERIES:
        run_and_pull(fig_15a_cxl.py, build_flags=variant)
    for variant in ABLATION_SERIES_ROLEX:
        run_and_pull(fig_15b_cxl.py, build_flags=variant)

    # Stretch: other methods, YCSB C only, in priority order
    if time_remaining(cluster) > timedelta(hours=1):
        for method in ["SMART", "ROLEX", "Sherman"]:   # Marlin deferred
            port_status = port_method_to_cxl(method)
            if port_status.ok:
                try_or_log(run_and_pull, fig_12_cxl.py, method=method, workload="c")

    pull_all_to_local()                # never leave the node without pulling


# Off-hardware, launched BEFORE tomorrow's window starts:
def parallel_background():
    generate_ycsb_workloads(sizes=[60e6, 80e6, 100e6, 120e6])  # local CPU, ~3h
    debug_sherman_load_statically()     # read Tree.cpp:382, trace invariant
    draft_partwo_sections(              # populate TODOs with data-free analysis
        ["intro", "background", "design", "related_work"]
    )


# The done check (runs in CI and locally)
def verify_done():
    assert exists("report/main-partwo.pdf")
    assert pages("presentation/main.pdf") >= 20
    assert docker_build_and_make_succeeds()
    assert ci_status("main") == "green"
    assert git_tag_exists("v2.0-final")
    assert count_todos("report/main-partwo.tex") == 0
    assert figures_present([
        "fig_12_cxl_chime", "fig_15a_cxl", "fig_15b_cxl",
        "fig_12_rdma_single_node", "fig_12_rdma_multi_node",
    ])
    # Direction-only numeric check (no magnitude claim, avoid overfitting)
    assert numeric("cxl_ycsb_c_throughput") >= numeric("single_node_rdma_ycsb_c_throughput")
```

## Edge Cases & Error Handling

### CXL smoke test fails
- **Scenario**: `USE_CXL=ON` builds but `ycsb_test` segfaults, hangs, or returns zero throughput.
- **Behavior**: Capture stderr to the git log with a `cxl-runtime-failure-apr22.log` artifact. Pivot slot to Part One fig_12 A/B collection. File a retrospective bug report section in `main-partwo.tex` explaining the blocker and proposed fix.
- **Test**: `verify: smoke.throughput > 0 within 60s` gate at 0:40 elapsed.

### Sherman LOAD crashes on RDMA (known, Tree.cpp:382)
- **Scenario**: `Assertion 'k >= fence_keys.lowest' failed` after ~5M keys loaded.
- **Behavior**: Do not attempt to debug on the cluster. Static analysis of `src/Tree.cpp:382` fence-key invariant. Report Sherman LOAD as "partial — crashes at N keys under Y concurrency; root cause: [finding]" in the report. If the finding is compelling, include it as an independent contribution.
- **Test**: Report narrative references the specific fence_keys invariant and shows partial-data plot.

### 60M-120M workload regeneration takes longer than expected
- **Scenario**: Off-hardware generation on local Mac exceeds 4h, blocking fig_14.
- **Behavior**: Fig_14 is stretch; drop from scope if generation not done by Apr 26. Caption in report: "Cache-consumption figure (Fig 14) omitted — dataset generation blocked; see Appendix X."
- **Test**: `ls ycsb/workloads/workload*_60M` etc. before Apr 26 midnight.

### Other-method CXL port reveals a new blocker
- **Scenario**: Sherman/SMART/ROLEX needs fixes beyond what CHIME needed (e.g., a DSM call site Tree.cpp doesn't have).
- **Behavior**: Log the blocker, skip that method, continue to the next. Do not iterate past 30 min per method during the reservation window.
- **Test**: Each method's port attempt has a `port_status` record; failures are captured.

### `main-partwo.tex` has leftover TODOs at the deadline
- **Scenario**: Writing slips; TODO markers remain when the May 5 deadline arrives.
- **Behavior**: Do a final sweep at Apr 30. Any remaining TODO either gets populated or the enclosing paragraph gets cut. Never submit with a TODO in the PDF.
- **Test**: `grep -c TODO report/main-partwo.tex == 0` in the done check.

### Reservation denied mid-session (quarantine, network violation, etc.)
- **Scenario**: CloudLab terminates the experiment (as happened in Part One history — RDMA on control net).
- **Behavior**: The profile `chime-r650-clemson-lan` already uses internal LAN. But if termination happens, pull any partial results via SSH before the session closes, and document in a `termination-report.md`.
- **Test**: Post-session, `exp/results/` has at least one non-empty file per started workload.

### Mid-session runtime failure (intermittent segfault, hang, assertion)
- **Scenario**: A workload crashes mid-run, 20+ minutes in. Need to decide (skip / restart / investigate) in <5 minutes without losing debug info.
- **Behavior**: Run harness wraps each `ycsb_test` invocation to auto-capture on failure:
  - `ulimit -c unlimited` before invocation; core dump → `debug/<timestamp>-<workload>/core`
  - Full stderr → `debug/<timestamp>-<workload>/stderr.log`
  - `git rev-parse HEAD` → `debug/<timestamp>-<workload>/commit.txt`
  - `CMakeCache.txt` + `Common.h` snapshot → `debug/<timestamp>-<workload>/`
  - Hugepage state (`cat /proc/sys/vm/nr_hugepages`) + memcached status → `debug/<timestamp>-<workload>/host.txt`
- Artifacts stay local on the node; pull alongside results. No debug session consumes live reservation time — triage happens off-hardware.
- **Test**: Induce a crash locally (e.g., kill a worker mid-run); confirm `debug/` artifact directory is populated.

### CXL legitimately slower than single-node RDMA
- **Scenario**: NUMA-emulated CXL on r650 has QPI latency (~80ns) vs RDMA loopback, but RDMA's software buffering may produce higher throughput under certain workloads.
- **Behavior**: This is a finding, not a bug. Report frames it as such: "CXL throughput on [workload] is X% lower than single-node RDMA; we attribute this to [specific technical cause]." The three-way plot keeps all three series visible regardless of order.
- **Test**: Report text names the specific sub-system (e.g., write combining, coroutine overlap) that accounts for the gap.

### CI fails at the last minute
- **Scenario**: `v2.0-final` tag pushes red CI because a sibling repo build breaks.
- **Behavior**: The CHIME repo CI is the only one that must pass. Sibling repos are documented as "linked externally" in the release notes. Do not block the final tag on sibling CI.
- **Test**: `gh pr checks --state success` on main CHIME repo only.

## Acceptance Criteria

### AC-1: CXL smoke test produces correct numbers on both read and write paths
- **Given** a 1-node r650 experiment with `USE_CXL=ON` built
- **When** (a) a 5-second YCSB LOAD insert of 10K keys runs, then (b) `./ycsb_test 1 8 1 randint c` runs for 30 seconds
- **Then** LOAD completes with no assertion failure or segfault (exercises CAS + alloc), YCSB C throughput > 0 ops/sec, no segfault, no assert failure, stdout contains the standard latency histogram

### AC-2: CHIME CXL fig_12 A-E exists
- **Given** tomorrow's reservation proceeds past the smoke test
- **When** fig_12_cxl.py completes for workloads A, B, C, D, E (and LOAD best-effort)
- **Then** `exp/results/cxl/fig_12_<workload>.json` exists for each of A, B, C, D, E, containing non-empty throughput and latency arrays

### AC-3: Single-node RDMA baseline exists
- **Given** the 2-node reservation
- **When** fig_12_rdma_2cn.py runs with 1 CN + 1 MN
- **Then** `exp/results/rdma_single/fig_12_<workload>.json` exists for each of A, B, C, D, E, with consistent thread-count sweep

### AC-4: Three-way comparison plots exist
- **Given** Parts One data, single-node RDMA (AC-3), and CXL (AC-2) all present
- **When** `exp/plot_fig_12_three_way.py` runs
- **Then** PDF figures at `report/figures/fig_12_{workload}_three_way.pdf` for each workload, each showing all three series with a legend and caption noting CN counts and dates

### AC-5: CXL fig_15a/b ablation exists
- **Given** tomorrow's reservation
- **When** the ablation variants (5 for 15a, 4 for 15b) each build and run
- **Then** `exp/results/cxl/fig_15a_cxl.json` and `exp/results/cxl/fig_15b_cxl.json` contain throughput per variant per workload

### AC-6: Per-technique analysis written
- **Given** AC-5 results
- **When** Section "Which CHIME Techniques Still Matter?" in `main-partwo.tex` is populated
- **Then** the section names each of hopscotch leaves, vacancy-aware locks, metadata replication, sibling-based validation, speculative read, and states whether its contribution on CXL is larger, smaller, or similar to RDMA, with the numeric delta cited

### AC-7: Artifact reproduces from clone (CXL build in Docker; RDMA on cluster)
- **Given** a fresh machine with Docker installed
- **When** `git clone <repo> && docker build --platform linux/amd64 -f Dockerfile.cxl-preflight -t chime . && docker run --rm --platform linux/amd64 -v $PWD:/src chime bash -c "mkdir -p b-cxl && cd b-cxl && cmake -DUSE_CXL=ON .. && make -j"` runs
- **Then** exit code is 0 and `b-cxl/ycsb_test` binary exists.
- **Note:** RDMA build cannot be verified in stock Docker because CHIME depends on `ibv_exp_dct` — a Mellanox-experimental extension only present with MLNX OFED userspace. RDMA regression check is AC-12 (run on cluster against Part One per-thread throughput baseline).

### AC-8: Final report PDF committed
- **Given** completed analysis text
- **When** `cd report && make` runs
- **Then** `report/main-partwo.pdf` builds with no LaTeX errors, `grep -c TODO main-partwo.tex` returns 0, PDF is committed to `main`

### AC-9: Final presentation builds
- **Given** report content ready
- **When** `cd presentation && make` runs (using the existing Makefile)
- **Then** a PDF with ≥20 slides including CXL results exists and is committed

### AC-10: GitHub Pages site serves both reports
- **Given** committed PDFs
- **When** CI runs on `main`
- **Then** the Hugo site at `site/` renders both Part One and Part Two reports as downloadable PDFs, CI is green

### AC-11: Tagged release exists
- **Given** all above complete
- **When** `git tag v2.0-final && git push --tags` runs
- **Then** GitHub shows a release with attached PDFs and a one-page release note summarizing deliverables

### AC-12: RDMA regression check against Part One baseline
- **Given** tomorrow's single-node RDMA YCSB C run and Part One's `exp/results/fig_12_c.json`
- **When** per-thread throughput (total throughput ÷ thread count) is computed for both
- **Then** tomorrow's per-thread number is within a 2× window of Part One's per-thread number. Deviation beyond 2× flags a silent RDMA regression from the CXL refactor commits and triggers investigation before trusting the three-way comparison

### AC-13: Fig_14 surrogate — cache consumption at 60M keys
- **Given** CHIME loaded with the existing 60M key workload under both CXL and single-node RDMA
- **When** the internal-node cache size is measured (via the existing `statistics()` hook in `src/Tree.cpp`)
- **Then** `exp/results/fig_14_surrogate.json` contains cache sizes for CHIME, Sherman, SMART, ROLEX on both transports at 60M keys. Report text explicitly acknowledges this is a surrogate for the full 40-120M sweep, with the full sweep deferred; plot shows the cache-efficiency *trend* — the claim CHIME makes in its headline

### AC-14: Debug artifacts captured on failure
- **Given** a workload crashes during tomorrow's run
- **When** the harness detects non-zero exit
- **Then** `debug/<timestamp>-<workload>/` directory exists with `core`, `stderr.log`, `commit.txt`, `CMakeCache.txt`, `Common.h`, `host.txt` populated; triage can proceed off-hardware after the reservation closes

## Technical Notes

- **Affected components:** `report/main-partwo.tex` (populate), `presentation/main.tex` (extend with CXL slides), `exp/fig_12_cxl.py`, `exp/fig_15a_cxl.py`, `exp/fig_15b_cxl.py`, `exp/fig_12_rdma_2cn.py`, `exp/fig_14_surrogate.py` (new), `exp/plot_fig_12_three_way.py` (new), `exp/run_harness.py` (new — wraps ycsb_test invocations with debug-artifact capture), `Dockerfile.cxl-preflight` (extend with RDMA deps), sibling CHIME/SMART/ROLEX/Marlin repos (for other-method CXL ports).
- **Patterns to follow:**
  - Compile-time reconfiguration via `sed_common.py` — same as Part One.
  - Multi-method comparison via sibling repo layout — already established.
  - CXL transport substitution via `USE_CXL` flag — already in place (commit `152b4e9` + `e430d8d`).
  - Incremental pulling of results after each workload completes — feedback memory `feedback_pull_results_early.md` applies.
- **Data model changes:** None to the CHIME index. New JSON result schemas under `exp/results/cxl/` and `exp/results/rdma_single/` follow the existing `fig_12_<workload>.json` schema.
- **Build system:** `Dockerfile.cxl-preflight` is the reference build environment for AC-7. Local Mac builds are best-effort (known IDE false alarms for `numa.h`, `boost/coroutine2`).

## Dependencies

- **Hardware:** CloudLab r650 Clemson reservation `43677ece` (Apr 22 ≥15:00 UTC, 8h, 2 nodes) — confirmed, auto-approved.
- **Hardware (stretch):** One additional r650 reservation of 3+ nodes by Apr 26 — not secured, needs manual admin approval per Q1 findings from today's reservation probing.
- **Code:** Commit `e430d8d` and prerequisites (cxl-implementation.md: IMPLEMENTED Phase 1) landed.
- **Tooling:** Docker Desktop on local Mac (running); Docker image `chime-cxl-preflight` built and cached.
- **Memory bank entries:** `project_apr22_reservation.md`, `project_roce_fixes.md`, `feedback_pull_results_early.md` — all current.
- **Existing data:** `exp/results/` from Part One (fig_12 C/D/E, fig_15a/b on 3-5 CN r650 Clemson) — reused for multi-node RDMA series.

## Open Questions

- **Exact final-presentation date** in "late April" — drives whether the presentation must be ready Apr 25, Apr 29, or something in between. Assumed Apr 29 for planning; will adjust.
- **Will the 2-node reservation actually materialize at 15:00 UTC Apr 22?** Reservation is auto-approved but CloudLab's scheduler has been unreliable in prior sessions. Monitor from ~14:30 UTC.
- **Is fig_14 truly required at the PhD bar** or is a "deferred with rigorous explanation" acceptable? Depends on professor's emphasis — the project brief and syllabus say all four core figures, but Part One already shipped without fig_14.
- **Other-method CXL port depth**: if a method's port requires >30 min of structural changes beyond the CHIME pattern, should we time-box strictly or finish the one we started? Tentatively: strict time-box, move on. Revisit if close.
- **Sibling repo CI**: do we block the `v2.0-final` tag on SMART/ROLEX builds, or ship CHIME-only CI? Tentatively: CHIME-only. Revisit if sibling breakage is trivial.

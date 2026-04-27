# Active Context

## Current Focus

**Pivoted to no-hardware deliverable.** After four reservation windows failed against the same CloudLab scheduler bug (Apr 22, 23, 25, 26), the May 5 presentation and May 6 report are being produced from the engineering work already complete plus a structured infrastructure postmortem. Spec at `llm/features/final-project-no-hardware.md` (SPECIFIED) — covers a combined Part One + Part Two report against the instructor's six rubric guidelines. New ACs: 15 (combined report), 16 (engineering effort narrative), 17 (cited postmortem), 18 (repro/stress separation), 19 (paper side-by-side), 20 (Sherman analysis), 21 (fig_14 design discussion), 22 (late-data slot). Deferred from parent: AC-1, AC-2, AC-3, AC-5, AC-12, AC-13.

## Spec

`llm/features/final-project.md` — SPECIFIED with 14 ACs covering CXL evaluation, Part One closure, report/presentation/release artifacts. Most ACs remain hardware-blocked.

## Hardware Status

- **Scheduler bug**: `reservationStatus <uuid>` returns `Undefined subroutine &main::DoStatus` server-side — cannot inspect reservation details from the CLI. Web UI requires interactive login (PEM client cert doesn't authenticate it; JWT is cookie-based).
- **Active reservations** (per user, unverified by tooling): UUIDs `8c36e934-666d-41dd-b899-920861083b09` and `cc0bf3c0-160f-4e53-bdd4-0f3e108b4757`, both r650, spanning 4/20–4/25 and 4/21–4/26.
- **Indirect signal**: `createReservation -n` dry-runs return `nbd: "2026-04-27T15:00:00Z"` — capacity IS held through Apr 27, but the scheduler thinks the holder is "other projects or users", not CS620426SP. Most likely cause: reservations filed under a different project/cluster/hardware-type-URN than the experiment's profile asks for.
- **Path forward**: need to inspect at least one reservation's `Project` / `Cluster` / `Type` fields via the user's browser, OR escalate to `support@cloudlab.us` (draft at `files/cloudlab-support-email-draft.md`).

## Apr 27 Progress

- **Spec amended** at `llm/features/final-project-no-hardware.md` — explicit 8-section report design, 8 new ACs, 7 deferred ACs, late-data placeholder.
- **Report restructured** at `report/main-partwo.tex` — full 8-section scaffold with TOC; combined Part One + Part Two title.
- **§3 Engineering Effort** populated: RoCE 6 fixes, internal-LAN quarantine risk, memcached.conf 10h bug, YCSB Py2/Py3 friction, CXL 5-blocker fix sequence, hardware reservation reliability with forward ref to §7.
- **§7 Postmortem** populated: reservation timeline table, verbatim scheduler error, failed-experiment UUID table, `reservationStatus` Perl bug, PEM/JWT auth asymmetry, indirect evidence via `nbd` dry-run, four mismatch hypotheses, three concrete CloudLab API improvement recommendations.
- **PDF builds clean**, 9 pages so far (still has TODO placeholders for §1/2/4/5/6/8).
- **End of day Apr 27**: all 8 sections + abstract + appendices populated. `report/main-partwo.pdf` builds clean (18 pages, 422 KB), zero TODO markers. Bibliography resolves (CHIME, Sherman, SMART, ROLEX, YCSB cites all working). AC-8 (zero TODOs) and AC-15 (combined report structure) satisfied. AC-19 (paper side-by-side figures) deferred to polish window — text references the paper figures with the matching axis convention but does not yet embed cropped paper panels.
- **Presentation extended**: `presentation/main.tex` updated for May 5 final delivery. New title ("Reproducing CHIME and Attempting a CXL Port"). Added Sherman LOAD stress finding, CXL Engineering Completed, three-frame postmortem section (Reservation Outage, Misleading Error, What Would Have Unblocked Us), Future Work, and refreshed Key Takeaways. Builds clean at 36 pages — AC-9 met (≥18 slides).
- **Apr 27 4pm reservation set**: UUID `2afbcb47-b233-4d21-b350-d6af029d9074`, 1-day, opens 16:00 ET. Cron job `adb76486` set to fire startExperiment at that time (session-only, requires Claude alive). Calendar event "CHIME r650 reservation OPENS" set as reliable human-side reminder.
- **CI workflow updated** (`.github/workflows/build-and-deploy.yml`): now builds both `report/main.tex` (Part One) AND `report/main-partwo.tex` (combined final). Builds both `presentation/main-v2.tex` (Apr 9 progress) AND `presentation/main.tex` (final May 5). Copies all four PDFs into `site/static/pdfs/` with both descriptive and short filenames. Will trigger on next push to `main`.
- **Hugo site updated**: `site/content/_index.md` Project Status table reflects current state (4 reservations blocked by CloudLab). `site/content/paper.md` surfaces Final Report at the top with Part One preserved as history. `site/content/presentation.md` surfaces final presentation; progress deck preserved as history.
- **Release notes drafted**: `RELEASE_NOTES_v2.0-final.md` — what reproduced, what didn't and why, Sherman stress finding, CloudLab postmortem summary, reproduction recipe. Tag stays unpushed until May 5 per spec.

## Pre-Hardware Tooling Complete (Apr 21–23)

- **CXL build works end-to-end in Docker** (`Dockerfile.cxl-preflight`, commit `e430d8d`): catches 5 blockers beyond the earlier CXL commit set.
- **`exp/run_harness.py`** with debug-artifact capture (core, stderr, git SHA, CMakeCache, Common.h, hostname, hugepage state). 8/8 tests pass.
- **`exp/fig_14_surrogate.py`** — single-point cache-consumption driver for 60M keys. 5/5 tests pass.
- **`exp/plot_fig_12_three_way.py`** — multi-series plot helper for multi-node RDMA + single-node RDMA + CXL. 5/5 tests pass.
- **`construction/scripts/runbook-day1.md`** — exact T+0:00..T+7:30 commands.
- **`construction/scripts/smoke-gate.sh`** — automated PASS/FAIL CXL gate (5s LOAD + 30s YCSB C).
- **Sherman LOAD crash static analysis** (`construction/design/sherman-load-crash-analysis.md`): framed as Sherman baseline limitation, not a bug to fix.
- **Sibling repos cloned**: `/Users/djjay0131/code/SMART`, `ROLEX-1`, `Marlin`. Layout-inventory confirms CHIME-compatible harness.

## Data Status

**No new experiment data since Apr 7.** Existing results:
- `fig_15a.json` / `fig_15a.pdf` — complete (Mar 28, run 7)
- `fig_15b.json` / `fig_15b.pdf` — complete (Apr 6, run 7)
- `fig_12_c.json`, `fig_12_d.json`, `fig_12_e.json` — complete (5 methods × 6–8 points)
- `fig_12_a_partial.json`, `fig_12_la_partial.json` — partial only
- **Missing**: fig_12 LOAD, fig_12 A, fig_12 B (full), fig_14, all CXL data

## Known Limitations

- **RDMA build cannot be verified in stock Docker** — uses `ibv_exp_dct` (MLNX OFED only). AC-7 scoped to CXL-only Docker preflight.
- **Sibling CXL ports deferred**: SMART/ROLEX/Marlin need their own CxlTransport/CxlDSM ports. Post-hardware-day work if CHIME-on-CXL succeeds.
- **`reservationStatus` server bug**: blocks all CLI-side diagnostic visibility into reservation state.

## Deadline Pressure

- **Final report due May 5** — 9 days remaining as of this update.
- **Final presentation late April** — effectively this week.
- If hardware stays blocked, Part Two becomes a "compiles clean in Docker, runtime eval blocked by scheduler" report section backed by static analysis and the smoke gate definition.

## Key Entry Points

- `exp/run_harness.py` — wrap ycsb_test invocations on cluster for debug capture
- `exp/fig_14_surrogate.py` — single-point cache measurement at 60M keys
- `exp/plot_fig_12_three_way.py` — render three-way comparison PDF
- `Dockerfile.cxl-preflight` — reference CXL build environment
- `construction/scripts/runbook-day1.md` — hardware-window playbook
- `construction/scripts/smoke-gate.sh` — automated CXL go/no-go check
- `construction/design/sherman-load-crash-analysis.md` — feeds Part Two narrative
- `files/cloudlab-support-email-draft.md` — escalation draft

Last updated: 2026-04-26

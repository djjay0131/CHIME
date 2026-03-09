# Progress

## Completed

- Added top-level `construction/` workflow folder.
- Added top-level `memory-bank/` continuity folder.
- Wrote a CHIME-specific codebase guide.
- Linked the new documentation from the main README files.
- Added a clearer explanation of what `exp/fig_03a.py` does.
- Completed Sprint 02 planning: full design spec and day-by-day sprint for Part One experiment reproduction.
  - Finalized design doc with all Q&A decisions: 5-method comparison, 4 core figures + 1 stretch, LaTeX report + Beamer presentation deliverables.
  - Created sprint with 13 tasks, day-by-day timeline from Mar 10 to Apr 9, gate milestones, and risk mitigations.
  - Updated activeContext.md with all decisions and immediate next steps.
- CloudLab infrastructure setup (2026-03-08):
  - Installed and configured portal-cli for CloudLab API access.
  - Resolved CloudLab API endpoint: `boss.emulab.net:43794`.
  - Created CloudLab profile `chime-r650-utah` (ID: 1d025108), updated script for Clemson CM.
  - Tested r650 availability across Utah, Clemson, and Wisconsin clusters.
  - Confirmed Clemson r650 works (1-node test provisioned successfully); Utah r650 unavailable (stale prediction data since Mar 3).
  - Submitted two reservations at Clemson: dry run 5x r650 Mar 17-19 (b11e25ca), full run 10x r650 Mar 27-Apr 3 (1cf9c2b4). Both pending approval.
  - Cleaned up 5 test profiles from CloudLab.

## Remaining

- More detailed architecture notes for DSM, directory, and RDMA helpers.
- Coverage for additional figure scripts besides `fig_03a.py`.
- A glossary for CHIME terms and major compile-time flags.
- Execute Sprint 02 (starts Mar 10).

## Risks

- The current docs are intentionally high-level and do not yet explain every low-level correctness mechanism.
- Some understanding of sibling repositories is still implicit in experiment scripts.
- CloudLab reservation is the first gate for Sprint 02; if it fails or is delayed, the entire timeline shifts.

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
  - Submitted two reservations at Clemson: dry run 5x r650 Mar 17-19 (b11e25ca) — **APPROVED**, full run 10x r650 Mar 27-Apr 3 (1cf9c2b4) — pending.
  - Cleaned up 5 test profiles from CloudLab.
- Pre-work for Sprint 02 dry run (2026-03-08):
  - Created `script/setup-hugepages.sh` for hugepage configuration.
  - Created `script/clone-repos.sh` to clone SMART, ROLEX, Marlin.
  - Created `construction/scripts/generate-common-json.py` to generate common.json from cluster IPs.
  - Created `construction/scripts/setup-checklist.md` with day-by-day setup steps.
- Additional Sprint 02 scripts (2026-03-08):
  - `script/run-on-nodes.sh` — run a command in parallel across nodes
  - `script/setKey.py` — parameterized via SETKEY_USER, NODES, NODES_FILE
  - `exp/smoke_test.py` — minimal 1 CN + 1 MN smoke test (YCSB C)
  - `generate-common-json.py` now also updates `memcached.conf` with master IP

## Remaining

- More detailed architecture notes for DSM, directory, and RDMA helpers.
- Coverage for additional figure scripts besides `fig_03a.py`.
- A glossary for CHIME terms and major compile-time flags.
- Execute Sprint 02 (starts Mar 10).

## Risks

- The current docs are intentionally high-level and do not yet explain every low-level correctness mechanism.
- Some understanding of sibling repositories is still implicit in experiment scripts.
- CloudLab reservation is the first gate for Sprint 02; if it fails or is delayed, the entire timeline shifts.

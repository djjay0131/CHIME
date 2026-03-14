# Active Context

## Current Focus

**Part One: Reproduce CHIME experiments on RDMA (CloudLab r650 nodes)**

Course: CS 6204 Advanced Topics in Systems (Spring 2026)
Assigned Paper: PP#4 - CHIME (SOSP '24)
Deadline: March 26, 2026 (Part One Due)
Presentation: April 7-9, 2026 (Week 12)

## Most Useful Starting Points

- `construction/design/part-one-reproduce-experiments.md` - Full design spec (Complete)
- `construction/sprints/sprint-02-part-one-reproduce.md` - Day-by-day task breakdown
- `construction/design/codebase-guide.md` - Code orientation
- `exp/README.md` - Experiment pipeline and runtime estimates

## Immediate Next Steps

1. ~~Wait for Clemson reservation approvals~~ — Dry run approved; full run pending
2. ~~Prepare Clemson-specific setup scripts~~ — Added: setup-hugepages.sh, clone-repos.sh, generate-common-json.py, setup-checklist.md
3. When dry run starts (Mar 17): SSH setup, install RDMA+deps, configure common.json with node IPs
4. Install RDMA stack and dependencies on all nodes once dry-run reservation starts
5. Clone all four repos (CHIME, SMART, ROLEX, Marlin) to all nodes
6. Build all 5 methods and generate YCSB workloads
7. Smoke test at single-node during dry run, then scale to full 10 nodes in full run

## Recent Decisions

- 2026-03-08: CloudLab API endpoint resolved: `boss.emulab.net:43794`
- 2026-03-08: Targeting Clemson cluster (not Utah) -- r650 unavailable at Utah (stale prediction data since Mar 3)
- 2026-03-08: Clemson r650 confirmed working via 1-node test provisioning
- 2026-03-08: CloudLab profile `chime-r650-utah` created (ID: 1d025108) -- targets Clemson despite name
- 2026-03-08: CloudLab profile script updated for Clemson CM
- 2026-03-08: Two reservations submitted at Clemson:
  - Dry run: 5+1=6x r650, Mar 17-19 (IDs: b11e25ca + 6b8d83dc) -- **APPROVED**
  - Full run: 10x r650, Mar 27-Apr 3 (ID: 1cf9c2b4) -- **APPROVED** (9 CN + 1 MN)
  - Re-run: 11x r650, Apr 3-6 (ID: 5488ef67) -- pending (proper 10 CN + 1 MN)
- 2026-03-12: Paper requires 11 nodes (10 CN + 1 MN). fig_12.json hardcodes CN_num=10.
- 2026-03-12: Approved reservations can't have node count changed (only reason modifiable).
- 2026-03-12: Strategy: run with 10 nodes first (Mar 27), then re-run with 11 (Apr 3-6).
- 2026-03-08: Cleaned up 5 test profiles from CloudLab
- 2026-03-07: Full 5-method comparison confirmed (CHIME, Sherman, SMART, ROLEX, Marlin) -- not CHIME-only
- 2026-03-07: Core experiments: Figures 12, 14, 15a, 15b; stretch: Figure 3a
- 2026-03-07: All sibling repos confirmed compatible (SMART from dmemsys, ROLEX/Marlin from River861, Sherman built from CHIME repo)
- 2026-03-07: LaTeX report with GitHub Pages CI (5% of grade)
- 2026-03-07: Beamer presentation, 15-20 minutes (10% of grade)
- 2026-03-07: PhD student expectations -- thorough analysis, not just screenshots
- 2026-03-07: CloudLab reservation ASAP starting Mar 10, 7-10 day window
- 2026-03-07: Experiment runtimes confirmed: fig_12 ~7.5h, fig_14 ~35m, fig_15a ~44m, fig_15b ~40m, YCSB gen ~1.5h
- 2026-03-07: All scripts run from master node only, inside tmux sessions
- 2026-03-07: sed_generator rewrites Common.h automatically; cmake_options per method in common.json
- 2026-03-07: Design spec finalized; Sprint 02 created with day-by-day timeline (Mar 10 - Apr 9)

## Current Blockers

- 11-node re-run reservation (5488ef67) pending approval (Apr 3-6).
- `installMLNX.sh` hardcoded for Ubuntu 18.04 — needs update for Clemson OS image.
- `installLibs.sh` uses deprecated `--force-yes`, old Boost URL, may need `--break-system-packages` on Ubuntu 22.04+.

Last Updated: 2026-03-12

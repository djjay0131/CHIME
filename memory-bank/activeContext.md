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

1. Submit CloudLab reservation for 10x r650 nodes on March 10 (Day 1 -- critical gate)
2. Install RDMA stack and dependencies on all nodes (Days 2-3)
3. Clone all four repos (CHIME, SMART, ROLEX, Marlin) to all nodes (Day 4)
4. Build all 5 methods and generate YCSB workloads (Days 4-5)
5. Smoke test at single-node, then scale to full 10 nodes (Days 6-7)
6. Run fig_12.py overnight on Day 8; remaining experiments Days 9-10

## Recent Decisions

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

- None yet. First gate: CloudLab reservation on Mar 10.

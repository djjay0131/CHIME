# Active Context

## Current Focus

**r650 production run tooling implemented.** Unified setup script + resilient experiment runner ready for Mar 27 reservation. CXL feature spec also complete.

## Implemented Tooling

- `construction/scripts/setup-r650.sh` — One-command cluster setup (SSH, OFED, libs, hugepages, repos, build, config, smoke test)
- `exp/resilient_runner.py` — Experiment runner with timeout, retry, checkpoint resume, watchdog, failure classification, rsync backup
- `exp/test_checkpoint.py` — 16 unit tests for checkpoint detection logic (all passing)
- `script/installLibs.sh` — Updated with `perftest` package for `ib_read_lat` RDMA validation

## Active Experiment Run

- **r6525 pre-deadline run:** Completed (Mar 23-26), data on non-paper-matched hardware
- **r650 reservation 1cf9c2b4:** 10x r650 Clemson, Mar 27 17:00 UTC – Apr 3 17:00 UTC (9 CN + 1 MN)
- **r650 reservation 5488ef67:** 11x r650 Clemson, Apr 3 18:00 UTC – Apr 6 18:00 UTC (10 CN + 1 MN)

## Upcoming

- Run `setup-r650.sh` on r650 cluster when reservation starts
- Run `resilient_runner.py` for all experiments (fig_12 first with watchdog)
- Parse results, update report and presentation with r650 data
- Create CXL reservations for mid/late April (1-2x r650 each)
- Beamer presentation Apr 7-9

## Recent Decisions

- Clean transport abstraction for CXL port (not a fork) — templates for zero-overhead
- NUMA-based CXL emulation on r650 dual-socket (not QEMU, not real hardware)
- All 5 methods ported to CXL with comparative analysis
- Coroutines stripped in CXL backend for realistic performance
- fig_12 runs first (primary result) with watchdog monitoring
- Pairwise RDMA connectivity test in pre-flight (not just ibv_devinfo)
- Default CHIME build in setup; method-specific builds at experiment runtime
- CXL reservations: 1-2 nodes only (NUMA emulation is single-node)

## Feature Specs

- `llm/features/presentation-progress-report.md` — Status: VERIFIED
- `llm/features/cxl-implementation.md` — Status: SPECIFIED
- `llm/features/rdma-r650-11-nodes-run-1.md` — Status: IMPLEMENTED

## Key Entry Points

- `construction/scripts/setup-r650.sh` — r650 setup (run first)
- `exp/resilient_runner.py` — experiment execution (run after setup)
- `construction/design/part-one-reproduce-experiments.md` — full design spec
- `construction/sprints/sprint-02-part-one-reproduce.md` — sprint tasks
- `exp/README.md` — experiment pipeline

Last updated: 2026-03-27

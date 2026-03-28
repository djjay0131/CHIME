# Progress

## Completed

### Phase 1: Bootstrap
- `construction/` and `memory-bank/` directories with documentation
- Codebase guide (`construction/design/codebase-guide.md`)
- `exp/fig_03a.py` walkthrough documentation

### Phase 2 Planning
- Design spec: `construction/design/part-one-reproduce-experiments.md`
- Sprint plan: `construction/sprints/sprint-02-part-one-reproduce.md`
- 5-method scope, 4 core figures + stretch, day-by-day timeline

### CloudLab Infrastructure (Mar 8-17)
- `portal-cli` configured, API endpoint resolved
- Profile `chime-r650-utah` created (ID: 1d025108)
- Reservations submitted: dry run, full run, re-run at Clemson
- Setup scripts: `setup-hugepages.sh`, `clone-repos.sh`, `run-on-nodes.sh`, `setKey.py`
- Automation: `generate-common-json.py`, `setup-checklist.md`, `day1-runbook.md`
- `day1-dry-run.sh` one-shot setup, `smoke_test.py`, `patch-cn-count.py`
- installLibs fix for Ubuntu 22+ (PIP_BREAK_SYSTEM)

### r6525 Pre-Deadline Setup (Mar 23)
- 11x r6525 provisioned (experiment 4fc8525b, profile chime-r6525-clemson)
- node10 excluded (broken RDMA), running 9 CN + 1 MN
- Hardware configured: CPU_PHYSICAL_CORE_NUM=64, public IPs in memcached.conf
- YCSB 0.17.0 fixed (`site.ycsb`, Python 3), workloads on project NFS
- Experiments started in sequence: fig_15b, fig_15a, fig_12, fig_14, extras

## In Progress

- r6525 experiment execution — wrapping up (deadline today Mar 26)
- Part One report drafting (`report/main.tex`)

## Remaining

- r650 full run (Mar 27-Apr 3): 9 CN + 1 MN on target hardware
- r650 re-run (Apr 3-6): 10 CN + 1 MN for proper fig_12
- Finalize report with combined results
- Beamer presentation (Apr 7-9)
- Part Two: CXL port (due May 5)

## Known Issues

- r6525 results may not match r650 (AMD EPYC vs Intel Xeon, different NICs)
- node10 broken RDMA limits CN count to 9
- r6525 root partition 16GB — requires NVMe/NFS for storage

Last updated: 2026-03-26

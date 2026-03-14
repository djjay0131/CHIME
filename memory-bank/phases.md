# Project Phases

## Phase 1: Bootstrap

Status: complete

Goals:

- create `construction/` and `memory-bank/`
- establish a first-pass codebase guide
- add discoverable links from README files

## Phase 2: Part One - Reproduce CHIME Experiments on RDMA

Status: in progress (infrastructure setup complete, awaiting reservation approval)

Design: `construction/design/part-one-reproduce-experiments.md`
Sprint: `construction/sprints/sprint-02-part-one-reproduce.md`
Deadline: 2026-03-26 (Part One Due)
Presentation: 2026-04-07 to 2026-04-09
Cluster: Clemson (r650 nodes) -- Utah r650 unavailable
Profile: `chime-r650-utah` (ID: 1d025108, targets Clemson CM)
Reservations:
- Dry run: 5x r650, Mar 17-19 (ID: b11e25ca) — approved
- Full run: 10x r650, Mar 27-Apr 3 (ID: 1cf9c2b4) — pending

Goals:

- set up CloudLab r650 environment with RDMA at Clemson cluster
- build and run CHIME's YCSB benchmarks
- reproduce Figure 12 (throughput-latency) and Figure 14 (cache consumption)
- present results in class

## Phase 3: Part Two - Port CHIME to CXL

Status: not started

Goals:

- modify CHIME's RDMA communication layer to use CXL
- adapt experiments for CXL-based platform
- run comparative experiments (RDMA vs CXL)
- final presentation and report

## Phase 4: Core Runtime Deepening (Documentation)

Status: pending

Goals:

- document DSM-related classes
- explain node lifecycle and thread registration
- map common metrics back to their source prints

## Phase 5: Figure Coverage (Documentation)

Status: pending

Goals:

- extend documentation beyond `fig_03a.py`
- classify figures by benchmark pattern
- document which metrics come from which parser paths

# Project Phases

## Phase 1: Bootstrap

Status: complete

Goals:

- create `construction/` and `memory-bank/`
- establish a first-pass codebase guide
- add discoverable links from README files

## Phase 2: Part One - Reproduce CHIME Experiments on RDMA

Status: in progress

Design: `construction/design/part-one-reproduce-experiments.md`
Sprint: `construction/sprints/sprint-02-part-one-reproduce.md`
Deadline: 2026-03-26 (Part One Due)
Presentation: 2026-04-07 to 2026-04-09

Goals:

- set up CloudLab r650 environment with RDMA
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

# Project Brief

## Mission

Reproduce and extend the CHIME artifact as a course project for CS 6204 (Spring 2026). The project has two parts:

- **Part One (due Mar 26):** Reproduce CHIME's RDMA-based experiments on CloudLab
- **Part Two (due May 5):** Port CHIME to CXL-based hardware and compare performance

## Course Context

- Course: CS 6204 Advanced Topics in Systems - Disaggregated Memory/Storage Systems
- Instructor: Sam H. Noh
- Assigned Paper: PP#4 - CHIME (SOSP '24)
- Grading: Part One presentation (10%), Final presentation (15%), Final report (20%)

## Repository Scope

CHIME contains:

- the C++ implementation of the CHIME distributed-memory index
- test and benchmark executables
- Python orchestration for reproducing paper figures
- environment and workload setup scripts

## Current Focus

Part One: reproduce (a part of) the experiments from the CHIME paper using the open-source artifact on CloudLab r650 nodes with RDMA.

Target experiments:
- Figure 12: YCSB throughput-latency comparison (primary)
- Figure 14: Cache consumption comparison
- Figure 3a: Trade-off analysis (stretch goal)

## Success Criteria

- CHIME builds and runs on CloudLab r650 with RDMA
- At least the YCSB throughput-latency results are reproduced
- Results are presented in class (Week 12, Apr 7-9)
- Documentation enables Part Two CXL porting work

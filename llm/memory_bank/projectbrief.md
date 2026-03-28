# Project Brief

## Overview

CHIME (Cache-efficient and High-performance Hybrid Index on disaggregated Memory) — a SOSP '24 paper artifact that combines B+ tree with hopscotch hashing for distributed-memory range indexes. This repo is a fork of `juyoungbang/CHIME` being used as a course project for CS 6204 (Spring 2026, Prof. Sam H. Noh) at Virginia Tech.

## Problem

Existing disaggregated-memory range indexes face a trade-off between cache consumption and read amplifications. CHIME breaks this trade-off by using hopscotch hashing at leaf nodes while keeping B+ tree structure for internal nodes and range queries.

## Target Users

- Course instructor evaluating reproduction fidelity and CXL porting
- The student (Jason Cusati, PhD) reproducing and extending the artifact

## Scope

### In Scope — Part One (due Mar 26)
- Reproduce RDMA experiments on CloudLab (Clemson cluster)
- Full 5-method comparison: CHIME, Sherman, SMART, ROLEX, Marlin
- Core figures: 12, 14, 15a, 15b; stretch: 3a
- Extra experiments: cache sensitivity, value size scaling, distribution comparison
- LaTeX report with GitHub Pages CI
- 15-20 min Beamer presentation (Apr 7-9)

### In Scope — Part Two (due May 5)
- Port CHIME from RDMA to CXL-based hardware
- Comparative experiments (RDMA vs CXL)
- Final presentation and report

### Out of Scope
- Modifying CHIME's core algorithm
- Supporting hardware beyond CloudLab r650/r6525

## Key Constraints

- CloudLab r650 is the target hardware (paper-matched); r6525 used for pre-deadline runs
- Paper requires 10 CN + 1 MN (11 nodes total)
- Experiments are long-running (fig_12 ~7.5h) and require RDMA
- Sibling repos (SMART, ROLEX) must coexist at same directory level
- PhD student expectations per syllabus (higher bar than MS)

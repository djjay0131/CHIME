# v2.0-final Release Notes

**Tag date:** May 5, 2026
**Course:** CS 6204 Advanced Topics in Systems, Spring 2026, Virginia Tech
**Paper:** CHIME (SOSP '24) — A Cache-Efficient and High-Performance Hybrid Index on Disaggregated Memory

This release marks the final-project deliverable for the course. It is the combined Part One + Part Two artifact: a partial reproduction of CHIME's published RDMA results on CloudLab r650 hardware, plus a complete CXL port of CHIME (gated by `USE_CXL=ON`) that compiles cleanly in a reproducible Docker preflight environment.

## Highlights

- **Combined report**: `report/main-partwo.pdf` — 18 pages, follows the instructor's six rubric guidelines, with explicit sections for Setup (paper-vs-actual), Engineering Effort, Reproduction Results, Stress-Testing, CXL Engineering Completed, and a structured CloudLab postmortem.
- **Final presentation**: `presentation/main.pdf` — final-project Beamer deck (May 5).
- **CXL port**: `CxlTransport`/`CxlDSM` swap the entire transport layer via a single compile flag. Build verified end-to-end in `Dockerfile.cxl-preflight`.
- **Off-hardware tooling**: 18 unit tests passing across `exp/run_harness.py`, `exp/fig_14_surrogate.py`, `exp/plot_fig_12_three_way.py`. Automated CXL smoke gate at `construction/scripts/smoke-gate.sh`. Hardware-window playbook at `construction/scripts/runbook-day1.md`.

## Deliverables

| Artifact | Path | Status |
|---|---|---|
| Combined final report (PDF) | `report/main-partwo.pdf` | Built clean, 0 TODOs, 18 pages |
| Final presentation (PDF) | `presentation/main.pdf` | 36 pages |
| Part One progress report (PDF) | `report/main.pdf` | History; preserved |
| Progress presentation (PDF) | `presentation/main-v2.pdf` | History; preserved (Apr 9) |
| CXL build (Docker) | `Dockerfile.cxl-preflight` | Reproducible from clone |
| Sherman static analysis | `construction/design/sherman-load-crash-analysis.md` | Source for stress-testing finding |
| Memory bank | `llm/memory_bank/` | Reflects final state, dated 2026-04-26+ |
| Final-project spec (no-hardware pivot) | `llm/features/final-project-no-hardware.md` | Status: IN-PROGRESS at tag time |

## What Reproduced

- fig\_12 throughput-latency for YCSB workloads C, D, E across CHIME, Sherman, SMART, ROLEX, SMART-SC. Trends consistent with the paper.
- fig\_15a (cumulative ablation from Sherman to CHIME, 5 workloads, 6 build variants).
- fig\_15b (cumulative ablation from ROLEX, 4 workloads, 5 build variants).

## What Did Not Reproduce, and Why

- **fig\_12 workload A**: completed on the cluster but not pulled before reservation expiry.
- **fig\_12 workload B**: partial (CHIME 5/8 thread-count points); reservation expired mid-sweep.
- **fig\_12 LOAD for Sherman / ROLEX / SMART-SC**: Sherman crashes (see Stress Finding below); other methods preempted.
- **fig\_14 (cache consumption sweep)**: 60M+ YCSB workloads not regenerated in time. Single-point surrogate at 60M is described as design-time discussion in §6.7 of the report; runtime measurement requires a successful CXL run.
- **Part Two CXL evaluation**: hardware-blocked. Four CloudLab reservations between April 22 and 26 returned the same scheduler error; zero nodes ever provisioned. Documented in §7 of the report with cited reservation UUIDs (`43677ece`, `5565ec96`, `8c36e934`, `cc0bf3c0`) and verbatim error strings.

## Stress-Testing Finding

Sherman's YCSB LOAD phase crashes deterministically at ~5M keys on r650 with `Assertion 'k >= fence_keys.lowest' failed` (`src/Tree.cpp:382`). The assertion has no escape hatch for the borrow/merge race that produces it. CHIME's `SIBLING_BASED_VALIDATION` and `VACANCY_AWARE_LOCK` close the window — empirically reinforcing the paper's claim that the techniques are jointly necessary for correctness, not just throughput.

## CloudLab Postmortem (selected)

- 4 r650 Clemson reservations, 80+ approved hours, 0 nodes ever provisioned.
- Scheduler error verbatim: `*** Resource reservation violation: 2 nodes of type r650 requested, but only 0 available because of existing resource reservations to other projects or users.`
- `reservationStatus` CLI broken server-side: `Undefined subroutine &main::DoStatus called at /usr/testbed/bin/manage_resgroup line 208.`
- Three concrete unblock recommendations submitted to CloudLab support (see §7.9 of the report).

## Reproduction (CXL build, any dual-socket x86_64 with Docker)

```bash
git clone https://github.com/djjay0131/CHIME && cd CHIME
docker build --platform linux/amd64 -f Dockerfile.cxl-preflight -t chime .
docker run --rm --platform linux/amd64 -v $PWD:/src chime bash -c \
  "mkdir -p b-cxl && cd b-cxl && cmake -DUSE_CXL=ON .. && make -j"
ls b-cxl/ycsb_test  # exists on success
```

## Acknowledgments

- Prof. Sam H. Noh for course design and rubric guidelines.
- The CHIME authors for the open artifact and reference implementation.
- CloudLab for compute capacity (when honored).

---

*Author: Jason Cusati (`djjay@vt.edu`). PhD student, Virginia Tech.*

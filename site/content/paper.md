---
title: "Research Report"
subtitle: "Reproducing CHIME and Attempting a CXL Port"
---

CS 6204 Advanced Topics in Systems — Virginia Tech, Spring 2026.

## Final Report (May 6 deliverable)

**Downloads:**
- <a href="/CHIME/pdfs/Jason_Cusati_Project_Final_Report_Short.pdf">Jason_Cusati_Project_Final_Report_Short.pdf</a> &mdash; short version, 27 pages (recommended for a first read)
- <a href="/CHIME/pdfs/Jason_Cusati_Project_Final_Report.pdf">Jason_Cusati_Project_Final_Report.pdf</a> &mdash; full version, 42 pages (every figure, every UUID, every detail)

{{< pdf "/pdfs/Jason_Cusati_Project_Final_Report_Short.pdf" >}}

The final report is reframed around **agent-orchestrated reproduction on CloudLab** as the primary contribution, with CHIME serving as the case study. It covers:

- **The reproduction half**: paper-matching trends on r650 Clemson for fig\_12 workloads C/D/E and fig\_15a/b across all 5 methods (CHIME, Sherman, SMART, ROLEX, SMART-SC) on Runs 7 (5 CN + 1 MN) and 8 (3 CN + 1 MN).
- **A Sherman LOAD-crash stress finding**: deterministic assertion at `Tree.cpp:382`; static analysis identifies the borrow/merge race that CHIME's `SIBLING_BASED_VALIDATION` + `VACANCY_AWARE_LOCK` close.
- **The CXL port half**: complete port via `USE_CXL=ON` flag, runtime-validated on r650 after the May-1 one-line allocator fix (commit `a3c9e87`). End-to-end CHIME-CXL data on workloads C/D/E, plus a four-method single-CN comparison and a Sherman-on-CXL transport-isolation build.
- **A negative-result postmortem of agent-driven testbed work**: a six-day CloudLab scheduler-binding outage with a deterministic cross-experiment-boundary reproduction recipe, a PEM/JWT auth-asymmetry that no agent can bridge, and three concrete CloudLab API additions (each independently sufficient to surface root cause inside the first failed window).

The report follows the instructor's six rubric guidelines across nine sections:

1. Introduction and Project Scope (with reframed contributions)
2. Experimental Setup: Paper vs. Actual
3. Approach: Agent-Orchestrated Experimentation Pipeline (with ORNL XLOOP'25 differentiation)
4. Engineering Effort and Obstacles
5. Part One: Reproduction Results
6. Part One: Stress-Testing Findings
7. Part Two: CXL Port — Engineering Completed
8. Part Two: CXL Port — Postmortem and Late Data (one-line allocator fix; CXL runtime; cross-day reproducibility; speculative-read-hurts-on-CXL ablation)
9. Conclusion and Future Work

---

## Part One Progress Report (March 26 milestone)

**Download:** <a href="/CHIME/pdfs/Jason_Cusati_Project_Part_One.pdf">Jason_Cusati_Project_Part_One.pdf</a>

The earlier progress report documenting the planned experiments, CloudLab reservation challenges, the r6525 dry-run experience, and the r650 run plan. Preserved for history; superseded by the combined final report above.

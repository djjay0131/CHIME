# Feature: Final Project Delivery — No-Hardware Pivot

**Status:** IMPLEMENTED (AC-12 unblocked by Apr 27 reservation) (all ACs except AC-11 satisfied; tag stays unpushed until May 5)
**Date:** 2026-04-27
**Author:** Feature Architect (AI-assisted)
**Parent spec:** `llm/features/final-project.md` (this is an amendment — read the parent for unchanged design rationale)

## Problem

The original `final-project.md` (Apr 21) assumed at least one usable r650 Clemson reservation between Apr 22 and May 5 to collect CXL runtime data. Four reservation windows (Apr 22, 23, 25, 26) failed with the same misleading scheduler error — `Resource reservation violation: 0 r650 available because of existing resource reservations to other projects or users` — even when approved multi-day reservations were active. The `reservationStatus` CLI is broken server-side (`Undefined subroutine &main::DoStatus`), so reservation state cannot be inspected from the CLI for diagnosis. With 8 days remaining (presentation May 5, report May 6) and no path to runtime data, the deliverable must be reframed: completed engineering + a structured infrastructure postmortem, not an evaluation of CHIME-on-CXL performance. The course rubric (provided by the instructor) explicitly asks for the build-difficulty narrative and a "what you couldn't reproduce, explain why" treatment — this pivot fits the rubric, but the report and presentation must execute it carefully so it reads as analysis, not excuses.

## Goals

- **Combined deliverable**: One unified report (`report/main-partwo.tex` absorbing the Part One narrative) and one Beamer deck (`presentation/main.tex` extended) covering both Part One reproduction and Part Two attempted port + postmortem.
- **Rubric coverage**: Each of the six instructor-provided guidelines is satisfied by a named section of the report:
  1. Experimental setup (paper-vs-actual, with delta analysis)
  2. Engineering effort + obstacles encountered
  3. Reproduction (Part One) separated from stress-testing (Sherman LOAD analysis)
  4. Reproduction results: trends, consistencies, differences-with-explanation, what-couldn't-reproduce-with-explanation
  5. Stress-testing: Sherman LOAD crash static analysis
  6. Figures rendered with paper-matching axes/units, side-by-side with paper figures
- **Postmortem rigor**: Every claim about the CloudLab failure is backed by a cited artifact — UUIDs, timestamps, error strings, server bug names, log lines.
- **Reproducible CXL artifact**: `Dockerfile.cxl-preflight` builds CHIME-on-CXL from clone with one command. Pre-existing AC-7 satisfied.
- **Tagged release**: `v2.0-final` cut after report PDF and presentation PDF are committed.
- **Late-hardware contingency**: If hardware opens up between Apr 28 and May 4, the report has *one designated section* (Appendix or "Late Data") into which any data lands without rewriting the main narrative.

## Non-Goals

- Any AC requiring runtime CXL data, single-node RDMA baseline, or new fig_12/fig_15 measurements (parent ACs 1, 2, 3, 5, 12, 13 — explicitly DEFERRED, see Acceptance Criteria below).
- Apologetic framing of the postmortem. Every limitation is paired with what was attempted and what was learned.
- Modifying CHIME's index code further. Code is frozen at the last green CXL build (`e430d8d`).
- Other-method CXL ports (SMART, ROLEX, Marlin) — would require hardware to verify.
- Editorializing on CloudLab as a project. The postmortem is technical, not editorial.

## User Stories

- As a PhD student, I want a deliverable that survives the hardware gap by reframing scope, so that the project earns the PhD-rigor bar even without runtime data.
- As the course instructor, I want each rubric guideline addressed with a clearly identifiable section, so that I can grade systematically.
- As a future reader of this artifact, I want a verifiable account of what worked, what didn't, and why, so that I can learn from both the engineering and the infrastructure failures.
- As a maintainer of CloudLab/Emulab, I want a structured bug report (UUIDs + timestamps + reproduction recipe), so that the scheduler issue can be triaged.

## Design Approach

### Report Structure

Single document at `report/main-partwo.tex`. Eight sections in order:

| § | Title | Source material | Rubric guideline |
|---|-------|------|---|
| 1 | Introduction & Project Scope | Paper abstract + course goals | — |
| 2 | Experimental Setup: Paper vs. Actual | techContext.md, RoCE fix list, reservation history | #1 |
| 3 | Engineering Effort & Obstacles | git log Mar 8 – Apr 27, RoCE fix discovery, CXL build journey | #2 |
| 4 | Part One: Reproduction Results | `exp/results/fig_15a/b`, `fig_12_c/d/e`, partial A/LOAD/LA, side-by-side with paper Fig 12/15 | #3, #4, #6 |
| 5 | Part One: Stress-Testing Findings | Sherman LOAD crash static analysis (`construction/design/sherman-load-crash-analysis.md`), the fence_keys invariant | #3, #5 |
| 6 | Part Two: CXL Port — Engineering Completed | CxlTransport/CxlDSM design, 5-blocker fix sequence, Docker preflight, smoke-gate definition, debug-capture harness, fig_14 surrogate | #2 |
| 7 | Part Two: CXL Port — Evaluation Blocked, with Postmortem | 4-window reservation timeline, scheduler error analysis, server-side bug enumeration, auth-layer asymmetry, what would unblock | #4 ("couldn't reproduce, explain why") |
| 8 | Conclusion & Future Work | What we'd run if hardware opened, what the smoke gate would tell us, lessons for course infrastructure | — |

`report/main.tex` (Part One progress report) stays committed for history but is no longer the primary deliverable; the combined `main-partwo.tex` cites it.

### Presentation Structure

`presentation/main.tex` extended from the Apr 7-9 deck. Target ~20 slides, ~15-20 min:

| Bucket | Slides | Content |
|---|---|---|
| Setup & motivation | 3-4 | Paper claim, course goals, what we set out to do |
| Part One results | 5-6 | fig_15a/b complete, fig_12 C/D/E complete, partial A/B/LOAD findings, paper side-by-side comparisons |
| Stress-test finding | 2 | Sherman LOAD crash + fence_keys invariant analysis |
| Part Two engineering | 3-4 | CXL port design, 5-blocker journey, Docker preflight, smoke-gate, harness |
| Postmortem | 3-4 | 4-window reservation timeline, scheduler error, server-side bugs, what we'd verify if hardware opened |
| Closing | 1-2 | What we delivered, what we learned, future work |

VT branding from the existing deck is preserved (Apr 9 commit `6be62b2`).

### Postmortem Section Contract

Every claim in §7 must cite an artifact:

- **Reservation UUIDs**: `43677ece-3dcb-11f1-a92d-c4cbe1eff744` (Apr 22), `5565ec96-3ebe-11f1-a92d-c4cbe1eff744` (Apr 23), `8c36e934-666d-41dd-b899-920861083b09` and `cc0bf3c0-160f-4e53-bdd4-0f3e108b4757` (Apr 25-26 multi-day).
- **Failed experiment UUIDs** (sample): `30166300-97e9-414c-a95b-f128ad976ca3`, `4f385918-e363-42a1-b301-e0bf0c053f63`, `39d89110-9227-4409-926c-ae530f73fb3a`, `46a9cf1b-5b20-4f6a-931a-59be0a1cc224`, `89dd98da-6713-446b-9262-a649f6be40b2`, `8ee49dbb-4bf7-4195-8334-ab38cfb58f6d`, `1ddc9b8e-d3f2-4f61-a57c-a015ffbc5ba3`.
- **Server-side bugs**: `Undefined subroutine &main::DoStatus called at /usr/testbed/bin/manage_resgroup line 208` (verbatim).
- **Scheduler error**: `*** Resource reservation violation: 2 nodes of type r650 requested, but only 0 available because of existing resource reservations to other projects or users.` (verbatim).
- **Auth asymmetry**: PEM client cert authenticates the XML-RPC CLI (works) but not `www.cloudlab.us/portal/...` (returns HTML login page). JWT works in the web cookie path but not against the boss XML-RPC endpoint.

The postmortem ends with **"What would have unblocked us"**: a fixed `reservationStatus`, a more precise scheduler error message, and a programmatic reservation→experiment binding API.

### Late-Hardware Insertion Point

If hardware opens between Apr 28 and May 4: the existing `construction/scripts/runbook-day1.md` runs unchanged. Whatever data lands gets one figure + one paragraph in §7 ("Late Data: Smoke Gate Result"), without restructuring §1-6. The narrative survives intact whether late data appears or not.

## Sample Implementation

```python
# This isn't code — the deliverable is a written artifact. The "implementation"
# is a section-by-section build plan with content sources.

# report/main-partwo.tex section-by-section build plan

SECTIONS = [
    ("intro",          source="paper abstract + projectbrief.md",                  todo_count=0),
    ("setup",          source="techContext.md + cloudlab-r650-LAN profile",        todo_count=0),
    ("effort",         source="git log + roce-fixes memory + cxl 5-blocker series", todo_count=0),
    ("repro_results",  source="exp/results/*.json + paper figs 12, 15a, 15b",      todo_count=0),
    ("stress_results", source="construction/design/sherman-load-crash-analysis.md", todo_count=0),
    ("part2_engineering", source="cxl-implementation.md + Dockerfile.cxl-preflight + smoke-gate.sh + run_harness.py", todo_count=0),
    ("postmortem",     source="reservation UUIDs above + verbatim error strings + auth-layer notes", todo_count=0),
    ("conclusion",     source="ALL ABOVE",                                         todo_count=0),
]

# Build order (parallelizable: blocks 1 and 2 can run today simultaneously)
DAY_PLAN = {
    "Apr 27": ["draft postmortem (§7)", "draft engineering-effort (§3)"],
    "Apr 28": ["draft setup (§2)", "draft part2 engineering (§6)"],
    "Apr 29": ["draft repro results (§4) — paper side-by-side figures"],
    "Apr 30": ["draft stress-testing (§5)", "draft intro/conclusion (§1, §8)"],
    "May 1":  ["full pass: smooth voice, fix transitions, add abstract"],
    "May 2":  ["build presentation slides from completed sections"],
    "May 3":  ["dry-run presentation, fix gaps"],
    "May 4":  ["final review, CI green, prep release tag"],
    "May 5":  ["present, push v2.0-final tag"],
    "May 6":  ["submit final report PDF"],
}

# Done check (what AC verification scripts will assert)
def verify_done():
    assert exists("report/main-partwo.pdf")
    assert no_todos_in("report/main-partwo.tex")
    assert pages("presentation/main.pdf") >= 18  # was 20 in parent, dropped to 18 — no CXL data slides
    assert docker_build_and_make_succeeds()      # AC-7 (carried over)
    assert ci_status("main") == "green"          # AC-10 (carried over)
    assert git_tag_exists("v2.0-final")          # AC-11 (carried over)
    assert sections_present(["setup_paper_vs_actual", "engineering_effort",
                              "repro_results_with_paper_sidebyside",
                              "stress_test_sherman_load",
                              "cxl_port_engineering_complete",
                              "cxl_evaluation_blocked_postmortem"])
    # Postmortem rigor check: every reservation UUID we have must appear
    assert all_uuids_cited_in("report/main-partwo.tex",
        ["43677ece", "5565ec96", "8c36e934", "cc0bf3c0"])
```

## Edge Cases & Error Handling

### Hardware opens up between now and May 4
- **Scenario**: A reservation works and produces real data.
- **Behavior**: Data lands in §7 "Late Data" subsection. Existing §1-6 narrative is preserved. Postmortem still ships — the failure was real and is graded under guideline #2.
- **Test**: Confirm §1-6 word-count is unchanged from pre-data version; new content is contained in a labeled subsection.

### Postmortem reads as whining
- **Scenario**: Reviewer feels the §7 narrative is excuse-making rather than analysis.
- **Behavior**: Audit pass on Apr 30: every claim must be paired with (a) a cited artifact and (b) a "what would unblock this" statement. Tone test: read aloud. If any sentence sounds emotional, rewrite as factual.
- **Test**: Apr 30 self-review checklist + a peer-tone-check from a generative reviewer (e.g., spawn a code-reviewer agent on the section).

### Writing slips and TODOs remain at deadline
- **Scenario**: Same as parent AC-8: TODOs in `main-partwo.tex` at submit.
- **Behavior**: Apr 30 sweep. Any unfinishable TODO → cut the surrounding paragraph rather than ship with TODO visible.
- **Test**: `grep -c TODO report/main-partwo.tex == 0`.

### Side-by-side paper figures cause copyright concern
- **Scenario**: Embedding the paper's original figure pages alongside ours.
- **Behavior**: Use academic fair-use precedent — figures included with citation. If concerned, use cropped panels with paper citation in caption rather than full-page reproductions.
- **Test**: Each side-by-side figure has caption like "Left: original Fig 12 from Bang et al. SOSP '24. Right: our reproduction on r650 Clemson 5 CN, Apr 6 2026."

### CI breaks on `main-partwo.pdf` builder
- **Scenario**: LaTeX environment in CI doesn't have a package the local Mac TeX install has.
- **Behavior**: Pin the CI image to the same TeX Live version the local build uses. Test the CI build before May 1 — never first-run in the deadline week.
- **Test**: A CI run on a PR validates `main-partwo.pdf` builds before Apr 30.

### Presentation runs over time
- **Scenario**: 20-slide deck takes 25 minutes; class limit is 15-20.
- **Behavior**: Each slide bucket is independently cuttable. Default cut order if over: drop one engineering-detail slide, then one paper-side-by-side comparison, then one postmortem detail. Never cut the conclusion.
- **Test**: Dry-run on May 3 with a stopwatch.

### Late hardware delivers data that contradicts the postmortem narrative
- **Scenario**: Hardware opens, smoke gate passes, but full sweep contradicts something in §7.
- **Behavior**: §7 gets one paragraph noting the contradiction. The postmortem isn't retroactively edited — it stands as the historical account. The new data is what it is.
- **Test**: Time-stamped section labels distinguish "as of Apr 27" claims from "May 4 update" claims.

## Acceptance Criteria

### Carried over from parent (still required)

- **AC-7 (Carried, DONE)**: CXL build reproduces from clone via Docker. Verified at commit `e430d8d`.
- **AC-8 (Carried, MODIFIED)**: `report/main-partwo.pdf` builds clean, zero TODOs, **content covers Part One + Part Two combined** (was Part Two only).
- **AC-9 (Carried, MODIFIED)**: `presentation/main.pdf` builds with **≥18 slides** including all six section buckets (was ≥20 with CXL slides).
- **AC-10 (Carried)**: GitHub Pages CI green; site renders both Part One and combined report PDFs.
- **AC-11 (Carried)**: `v2.0-final` git tag exists with release notes.
- **AC-14 (Carried, DONE)**: Debug-artifact capture harness exists with passing tests.

### Deferred from parent (hardware-blocked, explicitly named in the report)

- **AC-1, AC-2, AC-3, AC-4, AC-5, AC-12, AC-13**: Marked DEFERRED. Each is named in §7 of the report with a one-line explanation of what would be required to satisfy it. AC-13 has a structural alternative below (AC-21).

### New ACs (no-hardware deliverable)

#### AC-15: Combined Part One + Part Two report
- **Given** `report/main-partwo.tex` and committed Part One results in `exp/results/`
- **When** `cd report && make`
- **Then** the resulting PDF has section headings matching the §1-§8 structure in Design Approach, Part One reproduction (§4) cites the existing JSON results, and the bibliography cites the original CHIME paper, the Sherman paper, and the rubric source

#### AC-16: Engineering-effort narrative satisfies rubric guideline #2
- **Given** §3 "Engineering Effort & Obstacles" of the report
- **When** the section is read in isolation
- **Then** it documents (a) the 6 RoCE fixes required for r650 Clemson with concrete file:line references, (b) the YCSB workload generation Py2/Py3 issues encountered, (c) the 5-blocker CXL build journey from `152b4e9` through `e430d8d` with each blocker described, (d) the memcached.conf bug that cost 10h on Run 7

#### AC-17: CloudLab postmortem cites verifiable artifacts
- **Given** §7 of the report
- **When** the section is read
- **Then** it includes: (a) all 4 reservation UUIDs, (b) at least 5 failed experiment UUIDs with timestamps, (c) the verbatim `Undefined subroutine &main::DoStatus` error string, (d) the verbatim `Resource reservation violation` scheduler error, (e) a description of the PEM/JWT auth-layer asymmetry, (f) a "what would have unblocked us" subsection naming three concrete CloudLab API improvements

#### AC-18: Reproduction (§4) is structurally separate from stress-testing (§5)
- **Given** the report
- **When** the table of contents is read
- **Then** there are two distinct top-level sections labeled "Reproduction Results" and "Stress-Testing Findings", each with their own subsections, neither cross-cuts the other (no stress-test claim appears in §4, no reproduction claim appears in §5)

#### AC-19: Side-by-side paper figures with matching axes
- **Given** §4 of the report
- **When** any reproduction figure is inspected
- **Then** axes labels and units match the paper's corresponding figure exactly; the figure either pairs with a paper-figure cropped panel or has a "compare to Fig X in Bang et al." caption with figure-page citation

#### AC-20: Sherman static analysis is the stress-test contribution
- **Given** §5 of the report
- **When** the section is read
- **Then** it presents the `Tree.cpp:382` `Assertion 'k >= fence_keys.lowest' failed` finding with: (a) the exact code path that produces the assertion, (b) the fence_keys invariant explanation, (c) why CHIME's `SIBLING_BASED_VALIDATION` + `VACANCY_AWARE_LOCK` close the window that crashes Sherman, (d) the framing as a Sherman baseline limitation, not a fixable bug

#### AC-21: Fig_14 surrogate framed as design discussion (replaces parent AC-13)
- **Given** §6 of the report and `exp/fig_14_surrogate.py`
- **When** §6 discusses cache consumption
- **Then** the surrogate methodology is described (a single 60M-key load measured via the existing `statistics()` hook in `src/Tree.cpp`), the fact that no run was executed is stated explicitly, and the design-time analysis of expected cache trends is given based on the paper's hopscotch leaf cardinality vs Sherman's B+ leaf

#### AC-22: Late-data insertion test
- **Given** the report committed by Apr 30
- **When** §7 is inspected
- **Then** there is a labeled subsection "Late Data (if applicable)" with a placeholder paragraph; if no late data lands, the placeholder reads "No additional data became available before May 5 — see preceding postmortem for analysis"

## Technical Notes

- **Affected files**: `report/main-partwo.tex` (rewrite), `report/main.tex` (no change — preserved), `presentation/main.tex` (extend), `presentation/Makefile` (no change), `site/` (Hugo content for combined report — minor add). New `report/figures/` subdir with paper-figure scans (cropped panels for fair use).
- **Patterns to follow**: Existing report build (Makefile pattern from Part One). Beamer slide style from the Apr 9 commit. Hugo site adjusts.
- **Data model changes**: None.
- **Provenance discipline**: Every reproduction figure caption states "r650 Clemson, N CN, [date]" — same standard as Part One captions.
- **Source of truth for postmortem facts**: `files/cloudlab-support-email-draft.md` already has the failed experiment UUIDs and verbatim errors. `llm/memory_bank/activeContext.md` has the reservation UUIDs and timeline. These two files are the canonical citation sources.

## Dependencies

- **Code**: Frozen at `e430d8d` (CXL Docker preflight green) plus any tooling already merged.
- **Tooling**: Local TeX Live, Beamer, Docker (already in place). Hugo for site CI.
- **Existing artifacts** (must remain in tree): `report/main.tex`, `presentation/main.tex`, `Dockerfile.cxl-preflight`, `exp/results/fig_*.json`, `exp/run_harness.py`, `exp/fig_14_surrogate.py`, `exp/plot_fig_12_three_way.py`, `construction/design/sherman-load-crash-analysis.md`, `construction/scripts/runbook-day1.md`, `construction/scripts/smoke-gate.sh`.
- **Memory bank**: All three core files updated 2026-04-26 reflect the no-hardware reality.
- **Course rubric**: Six guidelines provided by the instructor (transcribed in this spec's §Design Approach table).

## Open Questions

- **Final-presentation slot length**: assumed 15-20 min. Confirm before May 3 dry-run.
- **Should the CHIME repo `v2.0-final` tag include the sibling repos as submodules** or just link them externally in the release notes? Tentatively: external links (parent spec's position).
- **Hugo site CI**: same TeX Live image as local? — verify before Apr 30.
- **Side-by-side paper figures**: cropped panels or full-page scans? Tentatively: cropped panels with caption citation. Revisit if professor's reference reports use a different convention.

## Status of Parent Spec

`llm/features/final-project.md` is preserved unchanged. This spec amends it. When this spec's ACs conflict with the parent's, this spec wins. The parent's "Fallbacks for Reservation Denial" section (§Design Approach) effectively predicted this pivot.

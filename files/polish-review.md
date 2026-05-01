# Polish Review: Final Report and Presentation

Reviewer pass over `report/main-partwo.tex` and `presentation/main.tex` against the Apr 27 data files in `exp/results/rdma-2node-04271959/` and the rubric in `llm/features/final-project-no-hardware.md`.

## Summary

- Report: 28 pages, builds clean (`pdflatex` + `bibtex` clean, only overfull-hbox warnings remaining; no undefined refs).
- Presentation: 27 frames, builds clean (only navigation-bar overfull-hbox warnings, which are cosmetic and intrinsic to the Madrid + miniframes theme).
- Rubric: all six instructor guidelines have a clearly identified section.

## Rubric Coverage Verification

| Guideline | Section | Status |
|---|---|---|
| #1 setup paper-vs-actual | §2 (`sec:setup`) | Present |
| #2 engineering effort + obstacles | §3 (`sec:effort`), §6 (`sec:cxl-engineering`) | Present |
| #3 reproduction vs stress separated | §4 (`sec:repro`) and §5 (`sec:stress`) are distinct top-level sections | Present |
| #4 reproduction with what-couldn't-reproduce | §4.5 ("What We Could Not Reproduce, and Why"), §7 (`sec:postmortem`) | Present |
| #5 stress-testing | §5 (Sherman LOAD crash analysis) | Present |
| #6 paper-matching axes | §4 figures pair with `figures/fig12-paper.png` | Present |

## High-Priority Issues (factual/contradictory, must fix)

### H-1: "RDMA fallback also blocked at runtime" paragraph contradicts the data table immediately above it
- **File:** `report/main-partwo.tex` line 661
- **What's wrong:** The paragraph says the RDMA path was attempted "and also blocked at runtime" with the "CN-side binary segfaulted immediately on startup." But this paragraph follows Table~\ref{tab:rdma-c-curve} and Figure~\ref{fig:fig12-apr27}, which present a complete C/D/E throughput curve from a successful RDMA run. The chronology is: initial RDMA attempt failed, then full OFED reinstall + Dx patches succeeded → the data in the table. The current paragraph order makes the success and failure look contradictory.
- **Fix:** Reframe the paragraph to make clear it describes the *initial* failed attempt that motivated the OFED reinstall, and explicitly link to the bullet list below ("After installing full MLNX OFED 4.9...") which explains the recovery.

### H-2: "Two of three runs report ~2.22, one reports ~5.34" miscounts the variance data
- **File:** `report/main-partwo.tex` line 600
- **What's wrong:** Across the three relevant JSONL files (`fig_12_c_sweep` 1 point at 5.34; `fig_12_chime_extra` 1 point at 2.22; `fig_12_variance` 3 points: one at 5.34 + two at 2.22; `fig_12_variance_v2` 5 points all at 2.22), the 16-thread distribution is ~8 reps at 2.22 and 2 reps at 5.34 — i.e. roughly 1-in-5, not "2 of 3 vs 1." The variance figure caption (line 612) correctly says "one-in-eight" but the prose says "two of three."
- **Fix:** Reword to align with the variance-figure caption: e.g. "the warm-cache mode at ~5.34 Mops/s appears in roughly one in five runs at 16 threads; the rest sit at the cold-cache steady state near 2.22 Mops/s."

### H-3: "Three-rep variance" footer/footnote claims "fourth rep at 16 threads" but variance_v2 has 5 reps
- **File:** `report/main-partwo.tex` line 584
- **What's wrong:** Table caption says "Three-rep variance shown for the workload-C points where it was measured (a fourth rep at 16 threads showed the same bimodality)." Actually `fig_12_variance_v2.jsonl` has five additional reps at 16 threads (all at ~2.23), and the variance figure cites eight total reps. The "fourth rep" wording understates the data and conflicts with the figure caption.
- **Fix:** Update wording to "Additional replications (n=5 per thread count) committed in `fig_12_variance_v2.jsonl` are shown in Figure~\ref{fig:fig12-variance}."

### H-4: Reservation timeline says "Apr 20--25" and "Apr 21--26" but project memory and parent spec name them "Apr 25-26 multi-day"
- **File:** `report/main-partwo.tex` line 419-420
- **What's wrong:** The two admin-approved reservation rows show windows that span April 20-25 and 21-26, but a reservation labelled "Apr 20-25" cannot have failed an Apr 23 startExperiment. Cross-checking with the failed-experiment table (Apr 23, 25, 26 attempts), the windows must include those dates. The Apr 20-25 and Apr 21-26 ranges are likely correct as stated; this is ambiguous in the narrative. Lower-priority "this is fine" — verified that admin-approved reservations span across the failed-experiment dates.
- **Status:** No fix required; verified consistent.

### H-5: Abstract overstates Part One coverage
- **File:** `report/main-partwo.tex` line 47
- **What's wrong:** Abstract says "the full fig_15a/b ablation across five competing methods." fig_15a and fig_15b are themselves ablation analyses (cumulative technique deltas), not method comparisons, though they reference Sherman/ROLEX as starting baselines. The phrasing "across five competing methods" is more accurate for fig_12. Reads as a slight conflation.
- **Fix:** Reword: "...collected fig_12 workloads C/D/E across five competing methods and the full fig_15a/b cumulative technique ablation."

### H-6: Apr 27 finding paragraph contradicts itself on Tree.cpp:1596 attribution
- **File:** `report/main-partwo.tex` line 659
- **What's wrong:** Says workloads A, B, LOAD aborted at `Tree.cpp:1596 leaf_node_update`. The CXL crash trace earlier (line 533, segfault stack) involves `Tree::insert` → `hopscotch_split_and_unlock`, not `leaf_node_update`. These are two different crash signatures. The text is ambiguous about whether the A/B failure is on the CXL build or the RDMA build. From context (it follows the RDMA C/D/E table and AC-12 RDMA regression check), it's the RDMA build. Should be made explicit.
- **Fix:** Add "On the same RDMA 1\,CN+1\,MN configuration..." prefix.

## Medium-Priority Issues (prose quality, transitions, defensiveness)

### M-1: Conclusion §8.4 "Could We Have Used Different Hardware?" reads defensively in places
- **File:** `report/main-partwo.tex` lines 725-746
- **What's wrong:** The whole subsection answers "why didn't you use X?" — five paragraphs explaining why every alternative is worse. Several phrasings ("cost dollars we do not have", "academic-testbed levels", "we did not have access to a Virginia Tech departmental cluster") read as defensive. The technical content is correct and useful, but the framing should be analytical (what each alternative trades off) rather than apologetic.
- **Fix:** Tighten phrasings; convert "defensive" verbs to "analytical" ones. Specific edits below.

### M-2: §7 "Late Data" paragraph "Worker-thread instrumentation trace" lands at the very end after the summary bullets
- **File:** `report/main-partwo.tex` lines 663-690
- **What's wrong:** The "What this reservation produced, in summary" paragraph (line 663) functions as a section conclusion, but it's followed by a "Worker-thread instrumentation trace" with a stack trace. A summary should be the last thing in the section.
- **Fix:** Reorder so the instrumentation trace precedes the summary paragraph.

### M-3: §4 What We Could Not Reproduce — reasons read as excuses for some items
- **File:** `report/main-partwo.tex` lines 232-239
- **What's wrong:** "result-pull step was scheduled too late and the experiment expired before the JSON files were transferred to the local machine. The lesson, captured in our project memory as a feedback note..." For an A workload that the cluster completed, this is an operational failure, not a hardware failure. Technically correct but reads slightly self-referential; mention of "project memory" and "feedback note" is internal vocabulary.
- **Fix:** Drop the "captured in our project memory as a feedback note" parenthetical; tighten to a one-sentence operational lesson.

### M-4: §5 "What This Tells Us" final paragraph weakens the framing
- **File:** `report/main-partwo.tex` line 305
- **What's wrong:** "Two minimal patches would close the window in the Sherman code itself: replacing the assertion with a retry loop... or adopting validation as a baseline. Neither belongs in the comparison: keeping Sherman's baseline behavior visible is the point of the fig\_15a ablation." This is good but ends with a slightly hedging "Neither belongs" — could be tightened.
- **Fix:** Tighten last two sentences.

### M-5: §6 "Why a CXL Port?" intro paragraph is a long single block
- **File:** `report/main-partwo.tex` line 320
- **What's wrong:** One paragraph spans ~10 lines with three distinct ideas (latency comparison, optimization implications, deletion vs translation). Hard to scan.
- **Fix:** Split into two paragraphs at the boundary "That makes CHIME on CXL an interesting target..."

### M-6: §7 reservation timeline table caption is unwieldy
- **File:** `report/main-partwo.tex` line 411
- **What's wrong:** Caption is two long sentences with parentheticals. Specifically the "Failed' means every startExperiment attempt..." should move into a footnote or table-note.
- **Fix:** Shorten caption; move the "Failed" definition to surrounding prose or footnote.

### M-7: Late Data paragraph "The scheduler bug recurred when the experiment ended" is dense and slightly editorial
- **File:** `report/main-partwo.tex` line 577
- **What's wrong:** Sentence "This is exactly the failure pattern that motivated the postmortem in §\ref{sec:postmortem-error}" reads as defensive vindication rather than analysis. Same finding can be stated as: "The bug is reproducible on demand, which converts a one-week observation window into an unambiguous reproduction recipe for CloudLab support."
- **Fix:** Reword to lead with the reproducibility-as-evidence framing.

### M-8: Presentation slide "Late Data" footnote dagger on 16t bimodality
- **File:** `presentation/main.tex` line 946
- **What's wrong:** "Bimodal: 2/3 runs ~2.22, 1/3 ~5.34" — same miscount as report H-2.
- **Fix:** Update to "Bimodal: ~1/5 runs warm-cache (~5.34); rest cold-cache (~2.22)."

### M-9: Presentation Table~`tab:rdma-c-curve`-equivalent (slide ~24) shows "n=3" but text says "n=3 (a fourth rep)"
- **File:** `presentation/main.tex` lines 932-944
- **What's wrong:** Same data-source disagreement as H-3.
- **Fix:** Update the slide footnote/dagger to acknowledge variance_v2 reps.

### M-10: Presentation slide "Methods Compared" shows SMART-SC sourced from `dmemsys/SMART`
- **File:** `presentation/main.tex` line 279
- **What's wrong:** SMART-SC ("SMART with sufficient cache") is a CHIME-paper ablation variant, not a separate repository — it's the SMART codebase configured with `ENABLE_CACHE_OPT=ON`. The current row is OK ("dmemsys/SMART"), just slightly imprecise ("SMART-SC = SMART build with cache feature"). Low priority.
- **Status:** Acceptable as-is.

### M-11: Presentation "Experiment Status" slide (~Slide 15) lists "r650 Fig 12 YCSB A, B, LOAD (in progress)" but those didn't complete
- **File:** `presentation/main.tex` line 525
- **What's wrong:** Status reads "in progress" but as of May 5 they're not in progress — they're aborted with documented reasons. The slide carries Apr 7 framing into the May 5 deck.
- **Fix:** Update to "blocked: documented in §7 of report" or "deferred (Sherman crash + reservation outage)."

### M-12: Presentation "Solutions" slide (~Slide 14) shows "Public IP memcached config" as a fix
- **File:** `presentation/main.tex` line 487
- **What's wrong:** The actual fix was the missing port line in `restartMemc.sh` — "public IP" is not what changed (per §3.3 of the report, the bug was the absent port directive). Slight mis-summary on the slide.
- **Fix:** Change to "memcached port directive" or "memcached.conf port + IP".

## Low-Priority Issues (formatting nits, list only — do not fix)

- **L-1:** Many overfull-hbox warnings in the report (`pdflatex` log lines 518-855). All are cosmetic margin overruns from long URLs and inline `\texttt{}` commands. None push content off the page. Could be addressed with `\sloppy` or per-paragraph `\fussy`/break hints.
- **L-2:** Presentation overfull-hboxes are intrinsic to the Madrid + miniframes navigation bar with this many sections (8 sections, 27 frames). Visible as a thin margin overrun in the section-bar at the top. Cosmetic.
- **L-3:** Bibtex bbl file in `report/main-partwo.bbl` is dated Apr 27; CI might re-run it. Not an issue if `bibtex` runs are part of the release flow.
- **L-4:** `references.bib` has `rolex2023` defined but report uses no key for ROLEX (only `chime2024` and `ycsb` are cited). Could add `\cite{rolex2023}` next to first ROLEX mention but not load-bearing.
- **L-5:** Footnote dagger on table line 592 of report is `($\dagger$)` inline rather than a true footnote with `\footnote`. Stylistic only.
- **L-6:** Some `\paragraph{...}` blocks span 6+ printed lines and could become `\subsection*{...}`. Aesthetic.
- **L-7:** Presentation slide ordering: Late Data section appears after "What we built" but before Future Work. Probably fine but could test whether "Late Data" should come earlier (right after Postmortem) for narrative flow.
- **L-8:** No abstract page numbering: the report has `\maketitle` then `\tableofcontents` then `\newpage` then §1 — page numbering starts at 1 on the title page. Some venues prefer roman-numeraled front matter.

## Final Notes

The report and presentation read well overall and meet all stated acceptance criteria. The Apr 27 late-data section is the densest area (most prose, most citations, most edits in the polish pass) — recommend a final pre-submission read of just §7.6 ("Late Data") aloud to catch any remaining defensive phrasing.

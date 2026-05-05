# Feature: Final Presentation Delivery (May 5, 12–13 min talk)

**Status:** IMPLEMENTED (AC-D4 stopwatch rehearsal pending user)
**Date:** 2026-05-04 (specified) / 2026-05-04 (implemented)
**Author:** Feature Architect (AI-assisted)
**Parent specs:** `llm/features/final-project-reframe.md` (VERIFIED 2026-05-04) — the spine reframe this delivery preserves.

## Problem

The current `presentation/main.tex` has 50 frames whose existing `\textbf{Time:}` notes sum to ~43 minutes — the deck was originally drafted for the April 9 progress talk and has accumulated CXL-runtime, competitor-method, postmortem, and reframe content since. The May 5 slot is **15 minutes total = 12–13 minutes talk + 2–3 minutes Q&A**. Without an explicit triage of the deck into a *spoken arc* and an *appendix*, plus a Zen-style content compression of the slides that anchor the new agent-orchestration spine, the talk will either run over time, dilute the spine, or read aloud as a stale progress report. One frame ("What the Single-CN Competitor Curves Tell Us") also lacks a `\note{}` block, which the spec preserves only for backup-slide use.

## Goals

- **Spoken arc of 15 slides** (within the 13–18 target band): 1 title + 2 setup + 4 Approach + 4 results + 2 postmortem + 2 closing.
- **Total spoken time ≤ 13:00** with **≥ 0:30 slack** measured from the sum of `Time:` values in retained `\note{}` blocks.
- **Stopwatch rehearsal ≤ 13:00** read aloud at conversational pace before the May 5 slot.
- **Zen compression** on every spoken slide:
  - body word count ≤ 30 (excluding frame title, figure captions, axis labels)
  - at least one visual element (figure, chart, table, diagram, or TikZ block) carrying the message
  - ≤ 4 bullets per slide if bullets are used at all
- **Complete `\note{}` block** on every spoken slide using the existing 4-line convention: `Key point: / Say: / Transition: / Time: <N>s`.
- **Spine reframe preserved**: orchestration claim spoken first; ORNL XLOOP'25 differentiation spoken; three CloudLab API additions spoken as the postmortem punch line.
- **Appendix preserves all dropped slides verbatim** (no information loss; available for Q&A).
- **One slide tagged "if running short, cut here"** so a real-time stretch is doable on stage without panic.
- **Two final presentation PDFs**, both committed before May 5 morning:
  - `presentation/main.pdf` — audience-facing, slides only, **no notes ever visible** (this is the projected version; "the main slides have to work" is the contract)
  - `presentation/main-notes.pdf` — speaker view, slides + notes side-by-side on each page (built by setting `\SHOWNOTES` to trigger Beamer's `show notes on second screen=right`); used on a second laptop if the classroom projector doesn't support dual-screen presenter view

## Non-Goals

- **Not redesigning data figures.** `figures/fig12-rdma-vs-cxl.pdf`, `fig12-cxl-reproducibility.pdf`, `fig15a-cxl-ablation.pdf`, etc. stay as-is. Plots already follow Zen.
- **Not rewriting prose in `report/main-partwo.tex`.** The report is VERIFIED at the reframe; presentation work is independent.
- **Not creating new content.** No new findings, no new figures, no new claims. The deck has all the material; this spec triages and compresses.
- **Not generating a workshop-paper version of the deck.** A future spec may extract paper-shaped content; this one is the May 5 deliverable only.
- **Not modifying `presentation/main-v2.tex`** (the April 9 progress deck). Historical, frozen, untouched.
- **Not changing the Beamer theme, VT branding, or fonts.** Madrid + miniframes + VT colors remain.

## User Stories

- As a PhD student presenter, I want a spoken arc that fits 12–13 minutes with rehearsed timing, so that I do not run over my class slot or rush through the spine.
- As the course instructor (audience), I want each rubric guideline addressed by at least one spoken slide, so that I can grade the talk against the same six guidelines as the report.
- As an attendee unfamiliar with the project, I want every spoken slide to convey one clear point through a visual, with the prose explanation in the speaker's mouth, so that I am not reading a wall of text while the presenter talks.
- As the presenter on a deadline-week morning, I want a backup slide pile reachable from the deck's appendix so that Q&A can be answered with a relevant slide, not stammered prose.
- As the presenter discovering the talk is running long mid-flight, I want one labeled "cut here" slide that I can skip without breaking continuity, so that I can recover 50–60 seconds without panic.

## Design Approach

### Spoken arc — 15 slides, ~13 minutes

| # | Section | Slide | Approx time |
|---|---|---|---|
| 1 | Title | Title slide | 0:30 |
| 2 | Setup | CloudLab Configuration | 0:45 |
| 3 | Setup | Methods Compared | 0:45 |
| 4 | Approach | Three Layers of the Pipeline | 0:50 |
| 5 | Approach | Layer 1: Persona-Driven Workflow | 0:55 |
| 6 | Approach | Layer 2: CloudLab Control Surface | 0:60 |
| 7 | Approach | Layer 3: Autonomous Runner + ORNL diff | 0:75 |
| 8 | Stress | Sherman LOAD Crash on RDMA | 0:50 |
| 9 | Results | CXL/RDMA Workload-Dependent Win | 0:60 |
| 10 | Results | Cross-Day Reproducibility | 0:55 |
| 11 | Results | CXL fig\_15a: Speculative Read Hurts on CXL | 0:55 |
| 12 | Postmortem | The Misleading Scheduler Error | 0:50 |
| 13 | Postmortem | Three CloudLab API Additions | 0:55 |
| 14 | Closing | Late Data: From Crash to Throughput in One Patch | 0:60 |
| 15 | Closing | Key Takeaways | 0:60 |
| | | **Subtotal** | **12:55** |

Slack against 13:00 = 5 seconds. **Slide 11 (CXL fig\_15a) is tagged `% CUT-HERE-IF-SHORT`** — droppable cleanly because slides 9 and 10 already carry the headline CXL findings.

If the rehearsal pass times beyond 13:00, the cut-here slide drops first; if still over, the second cut is slide 8 (Sherman LOAD crash, since the report contains the full analysis).

### Appendix — everything else, untouched

Every dropped slide moves after `\appendix` in the source file and is grouped under backup `\section{...}` headers. Beamer's `\appendix` removes those sections from the miniframes navigation bar so the spoken arc has clean section dots at the top of every spoken slide.

```latex
% spoken arc ends with Key Takeaways slide
\appendix
\section{Backup: Reproduction Experience}
% Challenge: Hardware Mismatch / Broken Node / RoCE / Tooling / Solutions
% Persistent Workloads, Experiment Status, Lessons Learned
\section{Backup: Methodology and Expected Results}
% Methodology, Expected Outcomes, Sherman/ROLEX-CHIME ablation slides
\section{Backup: CXL Engineering Detail}
% RDMA vs CXL, Transport Abstraction Layer, NUMA Emulation, CXL Hypotheses,
% CXL Engineering: What We Built, From Crash to Throughput in One Patch
\section{Backup: Competitor Methods}
% Single-CN Competitors, What the Single-CN Competitor Curves Tell Us,
% Sherman-on-CXL, additional context slides
\section{Backup: Postmortem Detail}
% The Reservation Outage (timeline) — moved here per Phase 4 Q3 decision
\section{Backup: Late Data Supplements}
% What We Got on the r650 Reservation, fig_15a Ablation: Sherman → CHIME on YCSB C/D
\section{Backup: Future Work and References}
% Future Work, References, final thanks/Q&A slides
```

The "What the Single-CN Competitor Curves Tell Us" frame (currently missing its `\note{}`) lives in this appendix and gets a stub note: `Backup slide; not part of spoken arc.`

### Diagram authoring — TikZ or generated image

For each redesigned slide, the implementer chooses the cheapest path to a working visual:

- **TikZ vector** when the diagram is structurally simple (boxes + arrows, layered stacks, comparison tables) — fits the existing deck's style; no asset to manage; lossless at any zoom.
- **Generated raster image** when the diagram is conceptually rich enough that hand-coding TikZ would dominate the time budget — e.g., a stylized schematic of the agent fleet, a labeled rendering of the CloudLab control surfaces with their PEM/JWT bridge, or a one-line allocator-overlap "before/after" memory diagram. Generate via Claude image generation, save to `presentation/figures/<name>.pdf` or `.png`, include via `\includegraphics`.
- **Hybrid** when a generated image needs precise overlays (axis labels, callout arrows, annotations) — generate the base image, overlay TikZ annotation nodes on top of it.

The Zen word cap (AC-D5) does not count anything inside TikZ blocks, figure environments, or image captions. AC-D6 (visual required) accepts either form.

### Zen redesign — slides flagged for likely redesign, others auditable

Audit table from Phase 4 Q5:

| Spoken slide | Action | Reason |
|---|---|---|
| 1. Title | None | Beamer title page is minimal |
| 2. CloudLab Configuration | Audit only | Likely already TikZ |
| 3. Methods Compared | Audit only | Likely already a comparison table |
| 4. Three Layers | None | Already a 3-card TikZ stack |
| 5. Layer 1 Persona Workflow | **Redesign** | 4 dense bullets, no visual; replace with a substrate-stack TikZ diagram + ≤25 words |
| 6. Layer 2 CloudLab | **Redesign** | ~85 words across 2 bullet groups + numbered list; replace with two-surface TikZ + broken-bridge arrow per Phase 5 sample |
| 7. Layer 3 Runner + ORNL | **Redesign** | Two bullet groups, dense; replace with 2-column visual: 9-phase timeline (left) + 3-row differentiation table (right) |
| 8. Sherman LOAD crash | Audit + light trim | Code listing + short prose; verify under 30-word cap |
| 9. CXL/RDMA workload-dependent | None | PDF chart-led |
| 10. Cross-day reproducibility | None | PDF chart-led |
| 11. CXL fig\_15a ablation | None | PDF chart-led |
| 12. Misleading scheduler error | **Redesign** | Currently has 4-item hypothesis list + verbatim error; trim to verbatim error + single one-line "what this means" caption; full hypothesis list moves to appendix |
| 13. Three API additions | Audit | Already a 3-item enumerated list with bold leads; verify ≤30 words |
| 14. Late Data: From Crash to Throughput in One Patch | **Redesign** | Currently text-heavy with embedded GDB trace; replace with before/after `GlobalAddress` allocator diagram + the one-line diff + ≤25 words. **Spine-validation framing is required:** the `\note{}` Say: block explicitly names the orchestration capability that surfaced the fix (cluster-side runner wrote the crash trace into NFS; laptop-side agent analyzed offline; one-line fix landed on next reservation). This is the slide that closes the loop on the agent-orchestration contribution. |
| 15. Key Takeaways | None | Already a 3-item TikZ block, rewritten in the reframe pass |

So **5 slides need content redesign** (Layer 1, Layer 2, Layer 3, Misleading scheduler error, Late Data), **3 slides need an audit pass** (CloudLab Configuration, Methods Compared, Sherman LOAD, Three API additions), **7 slides need no content change**. Combined with the targeted `\note{}` rewrites (4 Approach slides + any with stale "expected" framing), the editing surface is bounded.

### Notes editorial bar — targeted pass (Phase 4 Q5 = b)

- **Rewrite from scratch:** the 4 Approach slides' notes (just-written in the reframe pass; should be sharp; align with the Zen redesigns).
- **Rewrite if stale framing:** any spoken slide whose `Say:` references "expected results" or "what we'd verify if hardware opened" — this language predates the May 1 fix. Likely candidates: any retained slide from §Expected Results (probably none survive into the spoken arc, but check).
- **Leave as-is:** every other spoken slide's existing notes, after a tone read for "would this read fluently aloud at conversational pace?".
- **One stub:** "What the Single-CN Competitor Curves Tell Us" gets `Backup slide; not part of spoken arc.` since it's now in appendix.

### Verification

Two scripts at `scripts/`:

1. `scripts/verify-presentation-delivery.sh` — counts spoken frames (≤ first `\appendix`), confirms each has a `\note{}`, sums `Time:` values, asserts ≤ 13:00 and ≥ 11:00 (warn-only on the lower bound), invokes the Zen word-cap helper.
2. `scripts/check_zen_word_cap.py` — for each spoken `\begin{frame}...\end{frame}` block, strip out frame title, figures, captions, TikZ pictures, and `\note{}`; count the remaining body words; assert ≤ 30.

Plus a manual stopwatch rehearsal whose result is recorded in the implementation report (no script can simulate conversational pace).

## Sample Implementation

```latex
%% --- 1. Mark all retained-but-not-spoken slides as appendix --------------
% Place \appendix AFTER the spoken Key Takeaways slide. Beamer hides
% appendix sections from the miniframes outertheme navigation bar.
\section{Closing}
% [Late Data: One-Line Allocator Fix slide]
% [Key Takeaways slide]
\appendix
\section{Backup: Reproduction Experience}
% (etc.)

%% --- 2. Zen redesign sample: Layer 2 CloudLab Control Surface ------------
% AFTER (Zen — ~22 body words; TikZ carries the message):
\begin{frame}{Layer 2: CloudLab Control Surface}
\centering
\begin{tikzpicture}[
  surface/.style={draw, rounded corners=4pt, minimum width=4cm,
                  minimum height=2cm, align=center, font=\small},
  xmark/.style={text=mRed, font=\Large\bfseries},
]
  \node[surface, fill=mGreen!12, draw=mGreen] (xmlrpc) at (-3,1) {
    \textbf{XML-RPC}\\PEM cert\\\textit{agent-driveable}};
  \node[surface, fill=mRed!12, draw=mRed] (web) at (3,1) {
    \textbf{Web portal}\\JWT cookie\\\textit{browser-only}};
  \node[xmark] at (0,1) {$\nleftrightarrow$};
  \node[surface, fill=myOrange!18, draw=myOrange] (rpc) at (0,-1.4) {
    \textbf{\texttt{reservationStatus}} \emph{returns}\\
    \texttt{Undefined subroutine \&main::DoStatus}};
  \draw[->, thick, mGray] (xmlrpc) -- (rpc);
\end{tikzpicture}
\note{
  \textbf{Key point:} Two control planes; the bridge is broken.\\
  \textbf{Say:} CloudLab has two control surfaces. The XML-RPC side
  accepts PEM certs --- an agent can drive that. The web portal accepts
  JWT cookies --- an agent without a browser cannot. They don't
  interoperate. For us this was fine until reservationStatus broke with
  a server-side Perl bug. Without it, reservation state was only
  inspectable through the JWT-only web UI. That cost us six days.\\
  \textbf{Transition:} Three concrete API fixes would unblock that.\\
  \textbf{Time:} 60s
}
\end{frame}

%% --- 3. Cut-here tag on the optional slide -------------------------------
% Slide 11 (CXL fig_15a) carries this comment marker; the verification
% script grep-confirms exactly one such marker is present in the spoken arc.
%   % CUT-HERE-IF-SHORT  (slide 11 only — drop cleanly if rehearsal > 13:00)

%% --- 4. Verification script (scripts/verify-presentation-delivery.sh) ----
function verify_delivery() {
    local tex=presentation/main.tex

    # 1. Spoken-slide count = frames before \appendix; bound to [13, 18].
    SPOKEN=$(awk '/\\appendix/{exit} /\\begin{frame}/{c++} END{print c+0}' "$tex")
    [ "$SPOKEN" -ge 13 ] && [ "$SPOKEN" -le 18 ] \
        || { echo "FAIL: spoken count ${SPOKEN} not in [13,18]"; return 1; }

    # 2. Every spoken frame has a \note{} block.
    awk '/\\appendix/{exit}
         /\\begin{frame}/{f=1; n=0; t=$0}
         /\\note\{/{n=1}
         /\\end{frame}/{if(f && !n){print "FAIL missing note: " t; exit 1}; f=0}
        ' "$tex" || return 1

    # 3. Sum of Time: values in spoken frames.
    TOTAL_S=$(awk '/\\appendix/{exit} /Time:/{
        match($0, /[0-9]+s/); if (RSTART) s+=substr($0,RSTART,RLENGTH-1)
    } END{print s+0}' "$tex")
    [ "$TOTAL_S" -le 780 ] || { echo "FAIL over 13:00: ${TOTAL_S}s"; return 1; }
    [ "$TOTAL_S" -ge 660 ] || echo "WARN: under 11:00 (${TOTAL_S}s)"

    # 4. Per-spoken-slide body-word cap (Zen).
    python3 scripts/check_zen_word_cap.py "$tex" 30 || return 1

    # 5. Exactly one CUT-HERE-IF-SHORT marker in the spoken arc.
    CUTS=$(awk '/\\appendix/{exit} /CUT-HERE-IF-SHORT/{c++} END{print c+0}' "$tex")
    [ "$CUTS" -eq 1 ] || { echo "FAIL cut markers: ${CUTS}"; return 1; }

    echo "PASS: ${SPOKEN} spoken slides, ${TOTAL_S}s total."
}
```

## Edge Cases & Error Handling

### Rehearsal stopwatch comes in over 13:00 even though `Time:` sum says ≤13:00
- **Scenario:** Conversational pace is slower than note-density math; rehearsal hits 14:30.
- **Behavior:** First cut: drop slide 11 (CXL fig\_15a, the cut-here-tagged slide). If still over: drop slide 8 (Sherman LOAD). If still over: trim the longest `\note{}` blocks one by one. Re-rehearse after each cut.
- **Test:** Rehearsal pass logged with stopwatch; if first pass over 13:00, second pass after first cut must be ≤ 13:00.

### A spoken slide has more than 30 body words after redesign
- **Scenario:** Layer 1 redesign keeps a TikZ diagram but still has 35 words of explanatory text.
- **Behavior:** Move 5 words to the `\note{}` `Say:` block. Re-run the word-cap check. Iterate until ≤ 30.
- **Test:** `scripts/check_zen_word_cap.py presentation/main.tex 30` returns 0.

### `\appendix` placement breaks Beamer compilation
- **Scenario:** Some Beamer themes complain about `\appendix` outside expected positions.
- **Behavior:** If pdflatex errors after adding `\appendix`, fall back to commenting out the dropped frames instead of using `\appendix` — same effect (frames not in spoken arc), at the cost of losing the appendix structure for Q&A reachability. Document the fallback and revisit post-talk.
- **Test:** `pdflatex` exits 0 after the `\appendix` add; PDF table-of-contents/section-bar shows only the spoken-arc sections.

### A redesigned slide loses information critical to the spoken note
- **Scenario:** The Zen redesign of Layer 2 removes the verbatim `\&main::DoStatus` error string from the slide; the note still references "the Perl bug" but the audience now has nothing to look at while it's spoken.
- **Behavior:** Keep the verbatim error string on the slide as a subtitle or in-figure annotation. Word-cap-check counts it, but it's < 10 words and earns its place. The redesign is "minimum words to support the speech," not "no words."
- **Test:** Word-cap check passes AND every `\note{}` `Say:` reference has a corresponding visible element on the slide.

### One Approach slide's Zen redesign cuts the 4-claim coherence
- **Scenario:** Trimming Layer 3 to ≤30 words drops the ORNL differentiation summary; the spine reframe weakens.
- **Behavior:** Layer 3's Zen budget (30 words) must include "ORNL XLOOP'25" + at least 2 of the 3 differentiation points. If they don't fit, the differentiation table goes on the slide as a TikZ table (visual element, not "body text"), and the body text shrinks to a 1-sentence headline.
- **Test:** Slide 7 contains the strings `ORNL` (or `XLOOP`) and at least 2 of `testbed`/`scale`/`framing` (or synonyms thereof).

### A backup slide accidentally lands in the spoken arc due to file-order bugs
- **Scenario:** A frame from §Reproduction Experience ends up before `\appendix` because a `\section` move went wrong.
- **Behavior:** The verification script counts spoken frames; if > 18, it fails. Visual review of the section bar in the rendered PDF as a final check.
- **Test:** AC-D1 (spoken count in [13,18]) catches this.

### The course slot moves or the time budget changes day-of
- **Scenario:** Instructor shortens the slot to 10 min, or extends to 18 min.
- **Behavior:** The `Time:` sum is the lever. To shorten: cut slide 11 (-55s), then 8 (-50s), then 10 (-55s), in order. To extend: enable Layer 3's full ORNL differentiation table (currently abbreviated), un-cut slide 11, optionally promote one backup slide to spoken.
- **Test:** Each operation has a documented diff; rehearsal confirms new total.

### CI builds the report after this delivery work and the deck reframe got rebased
- **Scenario:** The reframe spec's branch protocol said branch was optional; this delivery work is on `main` and the report verification ran against an unrelated change.
- **Behavior:** The report's verification (`scripts/verify-reframe.sh`) is independent of the presentation file and continues to pass. AC-D-final ensures `presentation/main.pdf` builds clean and is committed.
- **Test:** Both `scripts/verify-reframe.sh` (report) and `scripts/verify-presentation-delivery.sh` (presentation) exit 0 from a clean repo.

## Acceptance Criteria

### AC-D1: Spoken-slide count in 13–18
- **Given** `presentation/main.tex` after delivery edits
- **When** the verification script counts `\begin{frame}` occurrences before the first `\appendix`
- **Then** the count is between 13 and 18 inclusive

### AC-D2: Every spoken slide has a complete `\note{}` block
- **Given** the spoken arc
- **When** each spoken `\begin{frame}...\end{frame}` is inspected
- **Then** each contains a `\note{...}` block, and that block contains all 4 lines: `Key point:`, `Say:`, `Transition:`, `Time:` `<N>s`

### AC-D3: Spoken `Time:` sum ≤ 13:00 with ≥ 0:30 slack
- **Given** the spoken arc
- **When** all `Time:` values in spoken-slide notes are summed
- **Then** the total is ≤ 780 seconds (13:00) AND ≤ 750 seconds (12:30) is preferred to leave slack for conversational pace; under 660 seconds emits a WARN but does not fail

### AC-D4: Stopwatch rehearsal ≤ 13:00 (single pass at IMPLEMENTED time)
- **Given** the rendered `presentation/main.pdf` opened in presenter view
- **When** the implementer rehearses by reading each `Say:` line aloud at conversational pace, advancing slides on `Transition:`, with a stopwatch
- **Then** total elapsed time is ≤ 13:00; if > 13:00, the cut-here slide is dropped, the file is rebuilt, and rehearsal is repeated; the final passing time is recorded in the IMPLEMENTED-status implementation report (e.g., "Rehearsal: 12:47, no cuts applied" or "Rehearsal: 13:18 → cut slide 11 → 12:33"). The cut-here mechanism (AC-D9) remains as a day-of safety valve for any conversational-pace drift on May 5 itself; this AC is the IMPLEMENTED-time gate, not a day-of one.

### AC-D5: Zen body-word cap (≤ 30 per spoken slide)
- **Given** the spoken arc
- **When** for each spoken frame, frame title, `\includegraphics`/figure environments, `tikzpicture` contents, table contents, `\caption{...}`, and `\note{...}` are stripped, then remaining word count is computed
- **Then** every spoken frame's remaining word count is ≤ 30

### AC-D6: Visual element required per spoken slide
- **Given** the spoken arc
- **When** each spoken frame is inspected
- **Then** each contains at least one of: `\includegraphics` (data figure, generated diagram image, or schematic), `\begin{tikzpicture}` (vector diagram), `\begin{tabular}` (comparison table), `\begin{lstlisting}` (code/error excerpt), or a labeled figure environment. **Diagrams may be TikZ vector OR raster images** — for slides where TikZ would be cumbersome, a generated diagram image (e.g., via Claude image generation, exported PNG/PDF, or screenshot) used via `\includegraphics{figures/diagram-name.pdf}` is equally acceptable

### AC-D7: Rubric guideline coverage in the spoken arc
- **Given** the six instructor rubric guidelines (setup, effort, repro vs stress, repro results + gaps, stress, paper-matching figures)
- **When** the spoken arc is mapped against them
- **Then** each guideline is hit by at least one spoken slide: setup → slides 2–3, effort → slides 4–7 + 14, repro vs stress → slides 8–11, repro results + gaps → slides 9–11, stress → slide 8, paper-matching figures → slides 9–11. No guideline is unmapped.

### AC-D8: Spine reframe preserved in spoken arc
- **Given** the spoken arc
- **When** the title slide (slide 1), the four Approach slides (4–7), and the Key Takeaways slide (15) are read in isolation
- **Then** all four lead with agent-orchestrated reproduction language; the three CloudLab API additions appear on slide 13; the ORNL XLOOP'25 differentiation appears on slide 7

### AC-D9: Cut-here marker exists on exactly one spoken slide
- **Given** the spoken arc
- **When** `% CUT-HERE-IF-SHORT` comments are counted in the spoken-arc range
- **Then** exactly 1 such comment exists; it is on slide 11 (the CXL fig\_15a ablation)

### AC-D10: Appendix preserves all dropped slides verbatim
- **Given** the original deck (50 frames) and the post-edit deck
- **When** a frame-by-frame diff is computed for non-redesigned dropped frames
- **Then** the only differences are LaTeX comment changes (e.g., relocated `% Slide N — title` markers); slide content is identical

### AC-D11: Every spoken slide passes the Zen audit
- **Given** the spoken arc
- **When** each spoken slide is inspected against the Zen criterion (≤ 30 body words, visual element present, ≤ 4 bullets if bullets are used)
- **Then** every spoken slide passes; slides that don't pass are redesigned until they do
- **Note:** the audit table in §Design Approach lists slides 5, 6, 7, 12, 14 as *expected* redesign candidates and slides 2, 3, 8, 13 as *expected* audit-only — these are estimates, not contractual. The contract is the per-slide word-cap pass (AC-D5), not the count of redesigns.

### AC-D12: Verification script returns 0
- **Given** the post-edit repository
- **When** `bash scripts/verify-presentation-delivery.sh` runs from repo root
- **Then** the script returns 0 and prints `PASS: <count> spoken slides, <total>s total.`

### AC-D13: Both final PDFs build clean and are committed
- **Given** all delivery edits applied
- **When** the build commands run:
  - `cd presentation && pdflatex main.tex` (twice, for cross-references) — produces `main.pdf` (audience-facing)
  - `cd presentation && pdflatex -jobname=main-notes '\def\SHOWNOTES{}\input{main}'` (twice) — produces `main-notes.pdf` (speaker view)
- **Then** both PDFs exist with no LaTeX errors; `main.pdf` shows ONLY slides (no notes anywhere — the contract is "the main slides have to work"); `main-notes.pdf` shows slide on left, notes on right of each page; the section navigation bar in both shows only spoken-arc sections; both files are committed to `main`. The `presentation/Makefile` gains a `notes` target mirroring the existing `v2-notes` pattern so `make notes` reproduces the speaker-view PDF.

## Technical Notes

- **Affected files:**
  - `presentation/main.tex` — primary work surface: redesign 5 slides, audit 3, complete notes, insert `\appendix`, group backup `\section{...}` headers, add cut-here marker.
  - `scripts/verify-presentation-delivery.sh` — new verification.
  - `scripts/check_zen_word_cap.py` — new helper.
  - `llm/features/final-presentation-delivery.md` — this spec.
  - `llm/memory_bank/activeContext.md` — flip status to IMPLEMENTED on completion.
- **Files explicitly NOT touched:**
  - `presentation/main-v2.tex` (Apr 9 progress deck — historical).
  - `report/main-partwo.tex` and the report's verification.
  - `references.bib`, `figures/*` (data figures).
  - `.claude/`, `script/` (cluster automation), `exp/`, `include/`, `src/`.
- **Patterns to follow:**
  - Existing `\note{}` 4-line convention (`Key point: / Say: / Transition: / Time:`).
  - Beamer `\section{...}` pattern (miniframes outertheme auto-renders the navigation bar).
  - VT colors `myRed`/`myOrange` and the `mTeal`/`mGreen`/`mRed`/`mGray` accent palette already in the preamble.
  - TikZ patterns from existing slides (rounded-corner cards, arrow connectors, color-fills at ~12–18% saturation).
  - Phase-table convention from existing setup slides for the Layer 3 timeline visual.
- **Beamer `\appendix` mechanics:**
  - Appears once, after the last spoken slide.
  - Hides subsequent `\section{...}` from miniframes navigation bar.
  - Frames after `\appendix` are still in the PDF (and in the speaker-notes side-screen if `\SHOWNOTES` is defined).
  - Frame numbers continue across `\appendix` (e.g., spoken arc 1–15, appendix 16–50).
- **Word-cap helper conventions:**
  - Stripped (NOT counted): `\frametitle{...}` and the `{Title}` in `\begin{frame}{Title}`; all `\includegraphics{...}`; **all `\begin{tikzpicture}...\end{tikzpicture}` blocks in their entirety, including TikZ-internal text** (annotation labels inside a diagram are part of the diagram, not body prose); all `\begin{tabular}...\end{tabular}`; all `\caption{...}`; all `\note{...}`; all LaTeX comment lines.
  - Counted: bullet-list items, paragraph text, footnotes, free `\textbf{...}` / `\emph{...}` / `\texttt{...}` content that lives outside the stripped environments. Macro names (`\textbf`, `\emph`, etc.) are not words; their contents are.
  - Rationale: the user's Zen concern is "too many bullets or sentences on the slide" — wall-of-text body prose. Diagram annotations (TikZ node labels, table cells, figure captions) are visual elements doing visual work; they're stripped because they're not what the audience reads as prose.
  - Practical implication: a slide that is one large TikZ diagram with eight node labels totaling 80 words has a body word count of 0 (or close) — passes the Zen cap. A slide with a 4-bullet list of 35 total words fails. This matches the user's stated intent.

## Dependencies

- **Parent spec:** `llm/features/final-project-reframe.md` (VERIFIED 2026-05-04). The four Approach slides created during the reframe are the spine slides; this delivery preserves them.
- **In-tree artifacts the spoken arc references:**
  - Data figures: `presentation/figures/*` and `report/figures/*` (used as `\includegraphics` in spoken slides 9–11 and possibly 14).
  - VT logo macro: `\vtlogo` (defined in preamble).
  - Existing TikZ palette: `myRed`/`myOrange`/`mTeal`/`mGreen`/`mRed`/`mGray`.
- **Tooling:** local TeX Live, `pdfinfo`, `python3` ≥ 3.10 for the word-cap helper.
- **Memory bank entries:**
  - `activeContext.md` — needs flip after IMPLEMENTED.
- **Course constraint:** May 5 talk is the deadline; this spec must IMPLEMENT and VERIFY before that morning.

## Open Questions

- **Exact slot length on May 5:** assumed 12–13 min talk. If instructor announces different (e.g., 10 min), apply the cut sequence in the edge-case section.
- **Whether the instructor uses a hard timer vs polite drift:** affects whether AC-D4 needs ≤ 13:00 strict or ≤ 13:30 soft. Default strict.
- **Layer 1 substrate-stack diagram details:** the exact TikZ shape for the persona/memory/spec layers is open — implementer's choice between (a) a 3-layer stack, (b) a 4-quadrant Venn, or (c) a timeline. All satisfy AC-D6; (a) is closest to the existing "Three Layers of the Pipeline" pattern on slide 4.
- **Whether to add a "thank you / questions" slide explicitly:** Beamer's `{ \setbeamercolor{...} \begin{frame}[plain] ... }` pattern at the end of the existing deck already serves this; spec leaves it untouched.
- **Whether rehearsal happens with or without the `\note{}` side-screen visible:** affects how detailed the `Say:` block needs to be. Default: rehearse with notes visible (presenter view), so `Say:` can be sentence-level rather than word-for-word.

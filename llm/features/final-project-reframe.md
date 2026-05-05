# Feature: Final Project Reframe — Agent-Orchestrated Reproduction as the Spine

**Status:** VERIFIED
**Date:** 2026-05-03 (specified) / 2026-05-03 (implemented) / 2026-05-04 (verified)
**Author:** Feature Architect (AI-assisted)
**Parent specs:** `llm/features/final-project.md` (Apr 21, hardware-optimistic) and `llm/features/final-project-no-hardware.md` (Apr 27, postmortem-pivot, IMPLEMENTED). This spec amends both — it does not replace prior ACs, it re-weights the contribution narrative.

## Problem

The current `report/main-partwo.tex` and `presentation/main.tex` treat the agent fleet, the CloudLab control surface, and the autonomous cluster-side runner as *enabling background* for the CHIME-on-CXL findings. In reality those tools are themselves a substantive contribution — and one that, on a novelty fact-check against the 2025–2026 literature (Agent Laboratory, AI-Researcher, ORNL "AI Agents for Autonomous Experiments at HPC User Facilities" SC '25 Workshops, OPTIMAS, the LLM-driven optical-network field-trial paper), occupies a distinct slot: **CloudLab/Emulab as agent target, with a negative-result framing and three concrete API additions**. The current artifacts under-claim this work, leaving roughly a quarter of the actual project effort buried as scaffolding. The reframe makes agent-orchestrated reproduction the spine and CHIME the case study, without losing the CHIME and CXL findings the parallel session is still landing.

## Goals

- **Rubric gate (primary verification):** every one of the instructor's six rubric guidelines maps to a clearly labeled section of `report/main-partwo.tex`, AND the `\subsection{Contributions}` block names ≥2 distinctly agent-orchestration contributions alongside the CHIME-on-CXL findings.
- **Spine reframe at first/last impression points:** title, abstract opening, `\subsection{Contributions}`, and conclusion opening paragraph all lead with agent-orchestrated reproduction; CHIME findings follow.
- **One new substantive section** — `\section{Approach: Agent-Orchestrated Experimentation Pipeline}` between current §2 (Setup) and current §3 (Engineering Effort), structured around four named claims (fleet, control surface, autonomous runner, what-it-got-us-and-what-it-didn't).
- **Presentation arc realigned:** title slide and agenda slide rewritten; new 4–5-slide "Approach" block inserted before engineering challenges; closing "Key Takeaways" slide leads with orchestration claim before CHIME findings.
- **Coordination protocol preserved:** all reframe edits land on a branch (`reframe-agent-spine`), so the parallel session's May-3 sprint can keep appending CXL findings to `main` without rebasing through a moving spine.
- **Surface-area floor (secondary, tripwire only):** ≥20% of report page count and ≥20% of presentation slide count is in agent-orchestration sections — measured by section markers, not by padding.

## Non-Goals

- **Not writing a workshop/conference submission.** Novelty fact-check identified plausible fit for SC Workshops / HotInfra / USENIX experience track, but a paper submission is a separate spec written *after* this deliverable lands.
- **Not demoting or removing CHIME-on-CXL findings.** Those remain a peer contribution. The reframe is additive at the spine level (title/abstract/contributions/conclusion + new §3) and untouched in the body sections (§4 Engineering Effort, §5 Reproduction Results, §6 Stress-Testing, §7 CXL Engineering, §8 Postmortem, §9 Late Data).
- **Not rewriting prose the parallel session is editing.** §4–§9 stay where they are; the parallel session continues to append CXL findings to those sections on `main`. This spec's branch only touches the spine.
- **Not introducing new agent-orchestration tooling.** The contribution is what already exists in `.claude/agents/`, `script/`, `exp/`, `llm/memory_bank/`, `llm/features/`, and `construction/sprints/`. No new code.
- **Not fabricating quantitative claims about agent productivity.** No "agents made me 3× faster" — we have no controlled measurement and the literature shows reviewers reject those claims without one.

## User Stories

- **As a PhD student**, I want the title and contributions block of my final report to lead with the contribution that matches the project's actual novelty in the 2026 literature, so that grader and any future reader form the right first impression.
- **As the course instructor**, I want each of my six rubric guidelines to map to a clearly labeled section, AND I want to see the orchestration work surfaced as a distinct contribution rather than buried as scaffolding, so that I can grade systematically at the PhD bar.
- **As a future reader (or workshop reviewer in a follow-up paper)**, I want a self-contained section that names the agent fleet, the CloudLab control surface, the autonomous runner, and what each got us versus did not, with citations to in-tree artifacts, so that the contribution is verifiable.
- **As the parallel agent session running the May-2 24h sprint**, I want my appends to `report/main-partwo.tex` and `presentation/main.tex` on `main` to succeed without rebasing through a moving spine, so that I can finish the data-collection sprint without merge-conflict stalls.

## Design Approach

### Scope: hybrid spine reframe (γ)

The reframe touches four points where readers form first/last impressions, plus inserts one new mid-section. Body sections owned by the parallel session stay untouched on `main`.

| Edit point | Scope | File | Owner |
|---|---|---|---|
| Title | Rewrite (1 line) | `report/main-partwo.tex` | this session, `reframe-agent-spine` branch |
| Abstract opening (first ~3 sentences) | Rewrite | `report/main-partwo.tex` | this session, branch |
| `\subsection{Contributions}` | Rewrite (add ≥2 new bullets at top, keep CHIME bullets) | `report/main-partwo.tex` | this session, branch |
| `\section{Approach: Agent-Orchestrated Experimentation Pipeline}` | Insert as new §3 | `report/main-partwo.tex` | this session, branch |
| §4 Engineering Effort, §5 Reproduction, §6 Stress-Test, §7 CXL Engineering, §8 Postmortem, §9 Late Data | NO CHANGE | `report/main-partwo.tex` | parallel session, `main` |
| Conclusion opening paragraph | Rewrite | `report/main-partwo.tex` | this session, branch |
| Title slide, agenda slide | Rewrite | `presentation/main.tex` | this session, branch |
| New 4–5 slide "Approach" block | Insert before engineering-challenges section | `presentation/main.tex` | this session, branch |
| Closing "Key Takeaways" slide | Rewrite to lead with orchestration | `presentation/main.tex` | this session, branch |
| Existing CXL/competitor/postmortem slides | NO CHANGE | `presentation/main.tex` | parallel session, `main` |

### Branch protocol (simplified — experiments complete)

Experiment data collection completed before this spec was authored; all results are committed to `main` and reflected in §4–§9 of `report/main-partwo.tex`. No parallel session is running. The branch protocol therefore exists for *PR review hygiene*, not for collision avoidance:

1. Create `reframe-agent-spine` from `main`.
2. All reframe edits commit to this branch.
3. PR `reframe-agent-spine` → `main` for clean diff review (the diff is the reframe, separable from the experimental content already on `main`).
4. Self-merge after CI green. Tag `v2.0-final` when full deliverable polish is complete.

If timeboxing pressure makes the branch costly, edits can land directly on `main` — there is no race condition. The branch is preferred but not required.

### The new §3: four-claim scaffold

Each subsection lifts evidence already in the tree; no new code is written for this spec.

#### §3.1 Persona-Driven User Workflow
- **Framing:** this is a *methodology* contribution, not a systems contribution. The personas are not a self-orchestrating fleet — the human invokes them per task, with persistent memory banks and feature specs as the substrate. The contribution is that this workflow stays coherent across a 6-week project with three reality pivots and multiple Claude sessions, where a single-agent context-bloat workflow would not.
- **Claim:** persistent memory banks (`llm/memory_bank/*.md`) plus feature specs (`llm/features/*.md`) plus role-scoped personas (`.claude/agents/*.md`) form a substrate that survives Claude session boundaries and project pivots; the human-invoked persona pattern is what made the substrate useful.
- **Cite:** `.claude/agents/*.md` (6 personas: feature-architect, construction-lead, knowledge-steward, memory-agent, construction-agent, proposal-agent), `llm/memory_bank/*.md` (6 files), `llm/features/*.md` (5 specs evolving across the project: cxl-implementation → final-project → final-project-no-hardware → final-project-reframe).
- **Show:** persona-role table; memory-bank file inventory; spec-evolution timeline (Apr 21 → Apr 27 → May 3, three specs across one project tracking the reality pivots) — the timeline itself is the most concrete evidence that the workflow held up.
- **Explicitly NOT claimed:** that the personas auto-orchestrate without a human in the chair. Almost every commit is human-invoked from a Claude Code session; an autonomous self-handoff loop is future work.

#### §3.2 Programmatic CloudLab Control Surface
- **Claim:** the XML-RPC + REST control surface is sufficient for reservation + experiment lifecycle automation, BUT inspecting reservation state requires the broken `reservationStatus` RPC — which is the exact gap that produced the six-day outage in §8. The PEM/JWT authentication-layer asymmetry is structurally non-bridgeable by an agent without interactive web-UI access.
- **Cite:** `script/cloudlab-setup.py`, `script/cloudlab-status-watch.sh`, `script/prep-experiment.sh`. Auth-asymmetry table lives in §8 (referenced from here as supporting evidence, not duplicated).
- **Show:** API surface diagram (PEM/XML-RPC client cert vs JWT/cookie web layer split); short table of which RPCs work, which return server-side bugs, which require the auth surface that agents don't have. (Full auth-asymmetry table stays in §8.)
- **Inline at close (the punch line, duplicated from §8 by design — these are the contribution):** three concrete CloudLab API additions, each individually sufficient to surface root cause inside the first failed window of the six-day outage:
    1. **Fix `reservationStatus`** — server-side `Undefined subroutine &main::DoStatus called at /usr/testbed/bin/manage_resgroup line 208` is a one-line Perl bug; restoring the RPC restores the only programmatic path to inspect reservation state.
    2. **Make the scheduler error precise** — current "0 available because of existing resource reservations to other projects or users" is misleading when capacity is held by the same project but in an unmatched binding. Naming the conflicting reservation UUID, or distinguishing "no matching reservation" from "capacity exhausted by other projects," would point at the project/cluster/hardware-type mismatch hypothesis on first failure.
    3. **Add `startExperiment --reservation <uuid>`** — current reservation-to-experiment binding is implicit (matching project, cluster, hardware type, time window). An explicit binding flag would let the scheduler return "your reservation has hardware type X but the profile asks for Y" on the spot.
- **Maintenance discipline:** these three bullets must stay textually identical to the corresponding subsection of §8 ("What Would Have Unblocked Us"). §8 is the source of truth (already in `main` from prior committed work); §3.2 imports its prose at draft time. AC-R12 below is a one-shot draft-time check, not an ongoing drift surface — experiments are complete and §8 prose is frozen.

#### §3.3 Autonomous Cluster-Side Runner
- **Claim:** a 9-phase plan executes for 24 hours without human-in-loop; checkpoint resume + on-node guards survive control-net quarantine and OOM-style failures; the laptop-side agent only wakes on a 29-minute cadence to pull results and commit.
- **Cite:** `script/autonomous-runner.sh` (275 lines, 9-phase), `exp/resilient_runner.py` (394 lines), `script/control-net-guard.sh`, `script/run-with-guard.sh`, `construction/sprints/sprint-may2-24h.md`.
- **Show:** phase table from `sprint-may2-24h.md`; guard-rail invariants (control-net byte-counter, OOM watchdog, NFS heartbeat); the cron + scp pattern that replaced the ssh-tail polling that triggered the CloudLab admin email.

#### §3.4 What This Approach Got Us, and What It Did Not
- **Got us:** multi-method runtime data on a hard deadline; a 24h autonomous sprint with the laptop-side agent awake only on 29-minute cadences; a structured postmortem with cited UUIDs and verbatim error strings; spec-driven evolution across three reality pivots (hardware-optimistic → no-hardware → reframe).
- **Did not:** bridge PEM/JWT auth asymmetry; diagnose scheduler-binding without a working `reservationStatus`; replace the human in irreversible decisions (reservation fees, force-pushes, control-net quarantine triage); produce controlled productivity measurements (we have no human-only baseline).
- **Forward pointer:** §8's three CloudLab API additions are the gap; each is named in the contributions block as a primary contribution.
- **Differentiation from ORNL's SC '25 Workshops paper** ("AI Agents for Enabling Autonomous Experiments at ORNL's HPC and Manufacturing User Facilities"). One paragraph naming three points of contrast: (1) **target testbed** — ORNL targets internal HPC + manufacturing user facilities with controlled provenance infrastructure; this work targets CloudLab/Emulab, the academic community's primary *shared* systems testbed, where the control surface is what users get rather than what facility operators design. (2) **scale of operator** — ORNL describes institutional infrastructure with facility staff in the loop; this work is a single PhD student on a course timeline with no operator privileges. (3) **framing of contribution** — ORNL is a success-story paper demonstrating capability; this work is a negative-result experience report whose contribution is the three concrete API additions inferred from where the agent approach broke. The differentiation is what makes this work a useful complement to the ORNL line of inquiry, not a duplicate.
- **Cite (`references.bib` addition):** ORNL paper full citation. Optionally also cite Agent Laboratory (Schmidgall 2025), OPTIMAS, and the LLM-driven optical-network field trial as adjacent prior art if §3.4 has space.

### The new contributions block

Order matters — agent-orchestration contributions named first, CHIME findings after, surfaces the spine. Existing CHIME bullets stay verbatim except for the demoted position.

```latex
\subsection{Contributions}
\begin{itemize}[nosep]
    %% Agent-orchestration contributions (new, leading) ---
    \item An agent-orchestrated CloudLab experimentation pipeline for a single
          PhD student: a Constellize-style persona-driven workflow
          (feature-architect, construction-lead, knowledge-steward,
          memory-agent) with persistent memory banks and feature specs as the
          substrate, a programmatic CloudLab control surface, and an autonomous
          cluster-side runner with checkpoint resume. The personas are
          human-invoked per task; coherence across a 6-week project comes from
          the memory-bank + spec substrate, not from agent-to-agent
          self-handoff.
    \item A negative-result postmortem of agent-driven testbed work: a six-day
          CloudLab scheduler-binding outage with a deterministic cross-experiment-
          boundary reproduction recipe, an authentication-layer asymmetry
          (PEM/JWT) that no agent can bridge without interactive web-UI access,
          and three concrete CloudLab API additions (\texttt{reservationStatus}
          fix, precise scheduler error message, \texttt{startExperiment
          --reservation}) each individually sufficient to surface root cause
          inside the first failed window.
    %% CHIME case-study findings (kept, second-tier billing) ---
    \item Partial reproduction of CHIME on r650 Clemson (YCSB C/D/E, fig\_15a/b)
          across five competing methods, with paper-matching trends.
    \item A complete CXL port of CHIME (\texttt{CxlTransport}, \texttt{CxlDSM})
          gated by a single \texttt{USE\_CXL} compile flag ... [keep existing prose]
    \item Single-CN runtime comparison ... [keep existing prose]
    \item A reproducibility finding: CHIME-CXL re-runs across days within
          $\sim 5\%$ ... [keep existing prose]
    \item A ROLEX scaling finding: ... [keep existing prose]
    \item A static-analysis finding on Sherman's load-time crash: ... [keep
          existing prose]
\end{itemize}
```

### Rubric guideline mapping (verification target)

| Rubric guideline | Section |
|---|---|
| #1 Experimental setup (paper vs actual) | §2 (existing, unchanged) |
| #2 Engineering effort + obstacles | §3 (NEW agent approach) + §4 (existing engineering effort) |
| #3 Reproduction separated from stress-testing | §5 (existing reproduction) and §6 (existing stress-test) |
| #4 Reproduction results + what couldn't reproduce | §5 + §8 postmortem (existing) |
| #5 Stress-testing | §6 (existing) |
| #6 Paper-matching axes/units | §5 figures (existing) |

The rubric mapping is unchanged from the parent spec — the reframe adds spine, it does not move guideline coverage.

## Sample Implementation

```latex
%% --- NEW TITLE -------------------------------------------------------------
\title{Agent-Orchestrated Reproduction on CloudLab:\\
A Case Study Reproducing CHIME and Porting It to CXL\\[0.5em]
\large CS 6204 Final Project Report}

%% --- NEW ABSTRACT OPENING (rewrite first sentences; keep findings prose) ---
\begin{abstract}
We report on an agent-orchestrated reproduction study on CloudLab, in which
a single PhD student used a multi-persona AI agent fleet (planning,
construction, memory-stewardship, postmortem) to drive end-to-end experiments
against a shared academic testbed. The case study is CHIME (SOSP'24): a
reproduction of its RDMA-based throughput-latency and ablation results, plus
a CXL transport port that compiles and runs from a single \texttt{USE\_CXL=ON}
flag. We separate two contributions: (i) systems-research findings on CHIME
and CXL (workload-dependent CXL wins, cross-day RDMA bimodality, speculative
read can hurt on CXL); (ii) orchestration findings --- what the agent fleet
enabled, what it did not (a six-day CloudLab scheduler-binding outage that no
agent could diagnose without a working \texttt{reservationStatus}), and three
concrete CloudLab API additions that would each independently let an agent
detect the failure mode in the first window. ...
% [keep the existing CHIME findings prose after this lead-in]
\end{abstract}

%% --- NEW §3 ---------------------------------------------------------------
\section{Approach: Agent-Orchestrated Experimentation Pipeline}
\label{sec:approach}

\subsection{Multi-Persona Agent Fleet}
% Cite .claude/agents/*.md (6 personas), llm/memory_bank/*.md, llm/features/*.md
\subsection{Programmatic CloudLab Control Surface}
% Cite script/cloudlab-setup.py, cloudlab-status-watch.sh, prep-experiment.sh,
% auth-asymmetry table cross-ref to §8.
\subsection{Autonomous Cluster-Side Runner}
% Cite script/autonomous-runner.sh, exp/resilient_runner.py,
% control-net-guard.sh, run-with-guard.sh, construction/sprints/sprint-may2-24h.md
\subsection{What This Approach Got Us, and What It Did Not}
% Got: multi-method data, 24h autonomous sprint, structured postmortem,
% spec evolution across 3 reality pivots.
% Did not: bridge auth-layer asymmetry, diagnose without reservationStatus,
% replace human in irreversible decisions, produce productivity measurements.

%% --- NEW CONCLUSION OPENER -------------------------------------------------
\section{Conclusion and Future Work}
\label{sec:conclusion}
This project demonstrates that an agent-orchestrated experimentation pipeline
--- a multi-persona fleet, a programmatic testbed control surface, and an
autonomous cluster-side runner --- can deliver a multi-method, multi-transport
reproduction study under hard deadlines and adverse testbed conditions, at the
unit of analysis of a single PhD student. It also demonstrates that this
approach has a sharp ceiling: when a testbed's control plane has gaps that
require interactive web-UI access, no agent can bridge them, and an entire
reservation window can be lost. ...
% [keep existing CHIME-findings closing paragraphs]
```

```bash
# Verification script (lives in scripts/verify-reframe.sh, runs locally + CI).
# Anchors to LaTeX labels and bullet *position*, not specific prose, so a
# May-4 copyedit pass cannot silently drift the verification.
function verify_reframe() {
    local tex=report/main-partwo.tex

    # 1. Structural anchors present (not prose-dependent):
    grep -q '\\label{sec:approach}'    "$tex" || return 1
    grep -q '\\label{sec:postmortem}'  "$tex" || return 1
    grep -q '\\label{sec:conclusion}'  "$tex" || return 1

    # 2. New §3 has the four required subsection labels (any prose):
    grep -q '\\label{sec:approach:fleet}'    "$tex" || return 1
    grep -q '\\label{sec:approach:cloudlab}' "$tex" || return 1
    grep -q '\\label{sec:approach:runner}'   "$tex" || return 1
    grep -q '\\label{sec:approach:limits}'   "$tex" || return 1

    # 3. Top-2 \items inside \subsection{Contributions} are the orchestration
    #    bullets. Verified by *position*, not by string match — the spec
    #    contract is "orchestration first, CHIME findings after." Any prose
    #    is fine as long as those top-2 bullets contain a \label{contrib:orch:1}
    #    and \label{contrib:orch:2} marker.
    awk '/subsection\{Contributions\}/,/end\{itemize\}/' "$tex" \
      | awk '/\\item/{i++} i==1 && /\\label\{contrib:orch:1\}/{f1=1}
                       i==2 && /\\label\{contrib:orch:2\}/{f2=1}
             END { exit (f1 && f2) ? 0 : 1 }'

    # 4. §3 is positioned between Setup (§2) and Engineering Effort.
    #    (Section ordering check via line numbers of the three labels.)
    local setup_line approach_line effort_line
    setup_line=$(grep -n  '\\label{sec:setup}'    "$tex" | head -1 | cut -d: -f1)
    approach_line=$(grep -n '\\label{sec:approach}' "$tex" | head -1 | cut -d: -f1)
    effort_line=$(grep -n '\\label{sec:effort}'   "$tex" | head -1 | cut -d: -f1)
    [ -n "$setup_line" ] && [ -n "$approach_line" ] && [ -n "$effort_line" ] \
        && [ "$setup_line" -lt "$approach_line" ] \
        && [ "$approach_line" -lt "$effort_line" ] || return 1

    # 5. Surface-area tripwire: agent-orch sections >= 20% of report pages.
    #    Computed via pdftotext page-break sentinel between sec:approach and
    #    sec:postmortem ranges in the rendered PDF. Tripwire only — informs
    #    whether to expand §3.4, not a hard fail.
    local pct
    pct=$(python3 scripts/measure_spine_pct.py report/main-partwo.pdf "$tex")
    [ "$pct" -ge 20 ] || echo "WARN: spine sections at ${pct}%, below 20% tripwire"

    # 6. Drift check between §3.2 inline list and §8 source-of-truth list.
    #    Both lists are wrapped in \begin{enumerate}[label=...] blocks tagged
    #    with \label{api-additions:approach} and \label{api-additions:postmortem}
    #    so the script can extract each list cleanly.
    python3 scripts/check_api_additions_match.py "$tex" || return 1

    # 7. Branch protocol (drafting time only, NOT in main CI):
    # test "$(git branch --show-current)" = "reframe-agent-spine"

    return 0
}
```

The verification depends on the report carrying these LaTeX labels (added by the implementing session, not requested today):

- `\label{sec:setup}` on existing §2
- `\label{sec:approach}` on the new §3
- `\label{sec:approach:fleet}`, `\label{sec:approach:cloudlab}`, `\label{sec:approach:runner}`, `\label{sec:approach:limits}` on the four §3 subsections
- `\label{sec:effort}` on existing §4 (Engineering Effort)
- `\label{sec:postmortem}` on existing §8
- `\label{sec:conclusion}` on existing §10
- `\label{contrib:orch:1}` and `\label{contrib:orch:2}` inside the top-two bullets of `\subsection{Contributions}`

Several of these labels likely already exist in the file; the implementing session adds the missing ones. Labels are stable across copyedits in a way prose is not.

## Edge Cases & Error Handling

### Parallel session adds a new contribution bullet during the 24h sprint
- **Scenario:** the parallel session (per `activeContext.md`) appends a new bullet to `\subsection{Contributions}` on `main` while this branch is rewriting the same block.
- **Behavior:** the merge at step 4 of the branch protocol resolves by union — both the parallel session's appended bullet (placed in the CHIME-findings group) and this branch's two new orchestration bullets (placed at the top) are preserved. Order: orchestration bullets first, CHIME bullets in chronological-append order.
- **Test:** post-merge, `awk '/subsection\{Contributions\}/,/end\{itemize\}/' report/main-partwo.tex | grep -c '\\item'` returns the expected sum (existing 7 + 2 new orchestration bullets + any new bullets the parallel session added).

### Parallel session edits the abstract opening on main
- **Scenario:** parallel session appends a finding sentence to the abstract on `main`, the same prose this branch is rewriting.
- **Behavior:** rebase will produce a conflict in the abstract block. Manual resolution preserves the new agent-orchestration opening sentences from this branch and the parallel session's appended finding sentence after the existing CHIME-findings prose.
- **Test:** post-merge abstract begins with "We report on an agent-orchestrated reproduction study" and contains all parallel-session-added finding sentences.

### Sprint deadline (May 3 17:00 UTC per Phase 9) slips
- **Scenario:** parallel session's Phase 9 finishes late or partially.
- **Behavior:** rebase whatever has landed; do NOT block the reframe merge on a complete sprint. The rubric gate is the verification target, not "all data collected."
- **Test:** verify the rubric gate (every guideline maps to a section, ≥2 orchestration contributions named) regardless of sprint completeness.

### Surface-area tripwire fires below 20%
- **Scenario:** §3 ends up shorter than 7 of 35 pages.
- **Behavior:** add concrete content to §3.4 ("What it got us, and what it didn't") — this is the subsection most amenable to expansion without padding. Pull additional in-tree artifact citations rather than inflate prose.
- **Test:** `pdftk` page count check on the rendered §3 region after build.

### Reframe reads as overclaiming agent autonomy
- **Scenario:** §3 implies the agents did the work autonomously, when in reality a human steered most decisions.
- **Behavior:** §3.4 names the limits explicitly ("did not replace the human in irreversible decisions"). Audit pass on May 4: every claim in §3 either cites an in-tree artifact or names a limit. Tone test: read aloud — if any sentence sounds like marketing, rewrite as factual with the citation.
- **Test:** a code-reviewer agent given §3 + the empty `.claude/` directory must be able to verify each artifact citation resolves. If a claim has no artifact, cut or qualify it.

### Conflict between branch protocol and parallel session's `git pull --rebase` policy
- **Scenario:** parallel session does `git pull --rebase` and pulls in the spine reframe before it's merged (e.g., it pulls from a feature branch by mistake).
- **Behavior:** the parallel session's policy is `git pull --rebase` against `origin/main`, not against feature branches. The branch is local-only (or pushed to `origin/reframe-agent-spine` but not into `origin/main`). The protocol does not require the parallel session to know the branch exists.
- **Test:** confirm the parallel session's pull command targets `origin/main` (per `activeContext.md`).

### Final PDF page count exceeds course-stated limits
- **Scenario:** if the course or instructor has a page cap, the new §3 pushes us over.
- **Behavior:** trim §3.4 first (most compressible), then §3.1 (table can become prose), then §3.3 (phase table can be summarized). Keep §3.2 — it's the most novel content (PEM/JWT asymmetry).
- **Test:** check page count against any stated cap before final merge.

## Acceptance Criteria

### AC-R1: Spine reframe at first/last impression points
- **Given** `report/main-partwo.tex` on the `reframe-agent-spine` branch (or post-merge on `main`)
- **When** the title, abstract first paragraph, `\subsection{Contributions}`, and `\section{Conclusion}` first paragraph are read in isolation
- **Then** all four lead with agent-orchestrated reproduction language; CHIME findings appear after the lead in each

### AC-R2: New §3 exists with four-claim scaffold
- **Given** the report
- **When** the table of contents is read
- **Then** `\section{Approach: Agent-Orchestrated Experimentation Pipeline}` appears between Setup and Engineering Effort, with four subsections: Multi-Persona Agent Fleet, Programmatic CloudLab Control Surface, Autonomous Cluster-Side Runner, What This Approach Got Us and What It Did Not. Each subsection cites at least one in-tree artifact path.

### AC-R3: Contributions block names ≥2 distinct agent-orchestration items
- **Given** `\subsection{Contributions}` of the report
- **When** the bullets are listed
- **Then** at least two bullets are agent-orchestration contributions (named first), and at least four are CHIME case-study findings (kept). Exact phrasing verified by the spine-marker `grep` in the verification script.

### AC-R4: Rubric guideline mapping intact
- **Given** the report's section structure
- **When** mapped against the six instructor rubric guidelines
- **Then** each guideline maps to at least one section (§2 → #1, §3 + §4 → #2, §5 + §6 → #3, §5 + §8 → #4, §6 → #5, §5 figures → #6). No guideline is unmapped.

### AC-R5: Presentation arc realigned
- **Given** `presentation/main.tex` on the branch (or post-merge on `main`)
- **When** the title slide, agenda slide, the inserted "Approach" block (4–5 slides), and the closing "Key Takeaways" slide are inspected
- **Then** title slide names agent orchestration; agenda slide lists "Approach: Agent-Orchestrated Pipeline" before "Engineering Challenges"; "Approach" block has slides matching the four-claim scaffold of report §3; "Key Takeaways" leads with the orchestration claim before CHIME findings

### AC-R6: Branch protocol respected — no edits to body sections on this branch
- **Given** the diff `main..reframe-agent-spine` on `report/main-partwo.tex`
- **When** the diff hunks are inspected
- **Then** every hunk is contained in: title block, abstract, `\subsection{Contributions}`, the new `\section{Approach}`, or the conclusion's first paragraph. No hunks touch §4–§9 body prose.

### AC-R7: Surface-area tripwire — ≥20% in agent-orchestration content
- **Given** the rendered `report/main-partwo.pdf`
- **When** page counts are computed for the spine sections (abstract + §3 + §8 postmortem)
- **Then** their combined page count is ≥20% of total page count. (Tripwire only — informs whether to expand §3.4, not a hard fail.)

### AC-R8: Verification script passes (label-anchored, prose-independent)
- **Given** the repository on `reframe-agent-spine` after all edits
- **When** `bash scripts/verify-reframe.sh` runs
- **Then** the script returns 0; all required `\label{...}` anchors are present (`sec:setup`, `sec:approach`, `sec:approach:{fleet,cloudlab,runner,limits}`, `sec:effort`, `sec:postmortem`, `sec:conclusion`, `contrib:orch:1`, `contrib:orch:2`); §3 is positioned between §2 (setup) and §4 (effort) by line-number check; the top-two `\item`s inside `\subsection{Contributions}` carry the `contrib:orch:{1,2}` labels regardless of prose. Surface-area tripwire is informational only.

### AC-R9: Clean PR diff for review
- **Given** the `reframe-agent-spine` branch (or direct edits if branch was skipped)
- **When** `git diff main..reframe-agent-spine -- report/main-partwo.tex presentation/main.tex` is read
- **Then** the diff is contained to the spine (title, abstract, contributions, new §3, conclusion opener, slide title/agenda/approach-block/takeaways) — every hunk is a reframe hunk, none touch §4–§9 body prose. The reviewer (or self-review) can read the diff in one sitting.

### AC-R10: No new tooling code introduced
- **Given** the diff `main..reframe-agent-spine`
- **When** non-`.tex`/`.md` files are listed
- **Then** the only non-prose addition is `scripts/verify-reframe.sh` (the verification script). No new files in `script/`, `exp/`, `include/`, `src/`, `.claude/agents/`, `llm/memory_bank/`, or `llm/features/` (this spec being the only `llm/features/` addition).

### AC-R12: Three CloudLab API additions duplicated faithfully between §3.2 and §8
- **Given** the inline list at the close of §3.2 ("Inline at close: three concrete CloudLab API additions") and the corresponding subsection in §8 ("What Would Have Unblocked Us")
- **When** the two lists are extracted (item-by-item, after macro expansion)
- **Then** they match textually, item-for-item, in the same order. The verification script extracts each list to a temp file and `diff`s them; non-zero diff is a verification failure. Drift is the failure mode that AC-R12 catches; the fix is to re-sync §3.2 from §8 (§8 is the source of truth for prose, §3.2 imports it).

### AC-R11: Existing parent ACs remain satisfied
- **Given** all parent ACs from `final-project-no-hardware.md` (AC-7 through AC-22) at IMPLEMENTED status
- **When** the reframe merges to `main`
- **Then** none are regressed — same PDF builds clean, same Hugo CI green, same tag eligibility. The reframe is purely additive at the spine.

## Technical Notes

- **Affected files (this spec only):**
  - `report/main-partwo.tex` — title, abstract, `\subsection{Contributions}`, new `\section{Approach}`, conclusion first paragraph.
  - `presentation/main.tex` — title slide, agenda slide, inserted approach block (4–5 slides), closing takeaways slide.
  - `scripts/verify-reframe.sh` — new verification script for the rubric gate.
  - `llm/features/final-project-reframe.md` — this spec.
- **Files explicitly NOT touched by this spec:**
  - `report/main-partwo.tex` body sections §4 Engineering Effort, §5 Reproduction Results, §6 Stress-Testing, §7 CXL Engineering, §8 Postmortem, §9 Late Data.
  - `presentation/main.tex` existing CXL/competitor/postmortem slide blocks.
  - `script/`, `exp/`, `include/`, `src/`, `.claude/agents/`, `llm/memory_bank/`, `construction/`.
- **Patterns to follow:**
  - LaTeX section structure from existing `main-partwo.tex` (Apr 27 + May 1–2 prose).
  - Beamer slide style from current `presentation/main.tex` (VT branding, `myRed`/`myOrange`).
  - Citation style: in-tree artifact paths as `\texttt{...}` inline, same as §7's UUID/error-string conventions.
- **Branch protocol:** `reframe-agent-spine` from `main`; commits land there; rebase + merge after May-3 sprint Phase 9. Self-merge after CI green.
- **Coordination:** parallel session's `activeContext.md` policy is preserved — it pulls/rebases against `origin/main`, not feature branches.
- **Tone discipline:** every claim in §3 cites an in-tree artifact OR names a limit. No "agents made me 3× faster" claims (no controlled measurement). No editorializing on CloudLab — the postmortem in §8 is technical.

### LaTeX labels — explicit checklist for the implementing session

The verification script (`scripts/verify-reframe.sh`) anchors on LaTeX labels rather than prose. The implementing session must ensure every label below is present at merge time. Verified by `grep -nE '\\label\{(sec:|contrib:|api-additions:)' report/main-partwo.tex` against the current state of the file (snapshot 2026-05-03).

**Labels that already exist on `main` (no action needed, just don't break):**
- `\label{sec:intro}`, `\label{sec:setup}`, `\label{sec:effort}`, `\label{sec:effort-roce}`, `\label{sec:effort-cxl}`, `\label{sec:effort-reservations}`
- `\label{sec:repro}`, `\label{sec:stress}` (and three sub-labels), `\label{sec:cxl-engineering}` (and three sub-labels)
- `\label{sec:postmortem}`, `\label{sec:postmortem-error}`, `\label{sec:postmortem-resstatus}`, `\label{sec:late-data}`
- `\label{sec:conclusion}`, `\label{sec:alt-hardware}`

**New labels the implementing session MUST add:**
- `\label{sec:approach}` — on the new `\section{Approach: Agent-Orchestrated Experimentation Pipeline}` heading.
- `\label{sec:approach:fleet}` — on `\subsection{Persona-Driven User Workflow}`.
- `\label{sec:approach:cloudlab}` — on `\subsection{Programmatic CloudLab Control Surface}`.
- `\label{sec:approach:runner}` — on `\subsection{Autonomous Cluster-Side Runner}`.
- `\label{sec:approach:limits}` — on `\subsection{What This Approach Got Us, and What It Did Not}`.
- `\label{contrib:orch:1}` — inside the FIRST `\item` of `\subsection{Contributions}` (the agent-orchestrated pipeline bullet).
- `\label{contrib:orch:2}` — inside the SECOND `\item` of `\subsection{Contributions}` (the negative-result postmortem bullet).
- `\label{api-additions:approach}` — on the inline numbered list inside `\subsection{Programmatic CloudLab Control Surface}`.
- `\label{api-additions:postmortem}` — on the corresponding numbered list inside `\subsection{What Would Have Unblocked Us}` of §8 (the source-of-truth list). May already implicitly exist as content; the label needs to be added so `scripts/check_api_additions_match.py` can extract both lists.

**Existing labels the implementing session must NOT remove or rename:**
- All `sec:*` labels listed above as "already exist." A rename breaks the verification script and any cross-references.

## Dependencies

- **Parent specs:** `llm/features/final-project.md` (Apr 21), `llm/features/final-project-no-hardware.md` (Apr 27, IMPLEMENTED). All ACs from the latter remain in force; this spec adds AC-R1 through AC-R11.
- **In-tree artifacts cited by §3 (must remain in tree at merge time):**
  - `.claude/agents/*.md` (6 personas + README)
  - `llm/memory_bank/*.md` (6 files)
  - `llm/features/*.md` (5 specs evolving across the project)
  - `script/cloudlab-setup.py`, `cloudlab-status-watch.sh`, `prep-experiment.sh`, `control-net-guard.sh`, `run-with-guard.sh`, `autonomous-runner.sh`
  - `exp/resilient_runner.py`
  - `construction/sprints/sprint-may2-24h.md`
  - `files/cloudlab-support-email-draft.md` (cited from §8 cross-ref in §3.2)
- **Coordination dependency:** parallel session running per `construction/sprints/sprint-may2-24h.md` (Phase 9 ETA ~17:00 UTC May 3). This spec's branch must NOT block that sprint.
- **Memory bank entries used:**
  - `project_apr22_reservation.md` (and successors)
  - `project_cloudlab_control_net.md`
  - `feedback_pull_results_early.md`
  - `MEMORY.md` index

## Open Questions

- **Does the existing `presentation/main.tex` agenda slide structure** (`\section{...}` blocks driving the miniframes outertheme) absorb a new `\section{Approach}` cleanly without breaking VT-themed page numbering? Verify before final merge by building locally.
- **Word/page budget:** if the course has a page cap on the final report, does §3 push us over? Need to confirm the cap before measuring; trim order is in the edge-case section above.
- **Parallel session's exact bullet additions to `\subsection{Contributions}`** during the sprint — unknown until merge time. Resolution by union is the pre-committed strategy.
- **Whether to update the `presentation/main-v2.tex` deck** (the Apr 9 progress deck): NO. The Apr 9 deck is historical and committed; only `presentation/main.tex` (the May 5 final deck) gets the reframe.
- **Whether to extract a workshop submission later:** explicit non-goal of this spec; deferred to a separate spec written after May 6.

# Feature: Progress Presentation (Part One)

**Status:** VERIFIED
**Date:** 2026-03-26
**Author:** Feature Architect (AI-assisted)

## Problem

The Part One progress presentation (Apr 7-9, 15-20 min) needs to tell the story of reproducing CHIME's experiments on CloudLab. The existing Beamer skeleton (`presentation/main.tex`) has TODO placeholders and a bullet-heavy structure that violates the zen aesthetic requirement. The presentation must assume no completed experiment data is available and convey the paper's contributions, the reproduction experience (what went wrong, what was learned), and CXL plans.

Two PDF outputs are required: one clean version for presentation/publishing and one with speaker notes for delivery. A durable PDF snapshot must be published to GitHub Pages via new CI, with a git tag marking the source.

## Goals

- ~25 slides covering paper summary -> reproduction experience -> expected results -> CXL plans
- Zen aesthetic: minimal text, image/diagram-driven, one idea per slide
- Script-style speaker notes on every slide (presenter has no rehearsal time)
- Assumes no completed experiment data — results section is methodology + expectations
- Two PDF outputs: `main.pdf` (no notes) and `main-notes.pdf` (with notes)
- New CI pipeline to publish presentation PDF to GitHub Pages
- Compiles cleanly with `make` in `presentation/`
- ~20 minute delivery (avg ~48s per slide)
- Git tag `progress-v1` at submission

## Non-Goals

- Final presentation content (Part Two results, CXL analysis) — separate spec
- Final report or progress report — separate deliverables
- Creating actual experiment figures (those come from `exp/*.py` scripts)
- Video recording or rehearsal tooling
- Interactive or animated slides

## User Stories

- As the presenter, I want script-style speaker notes with timing so I can deliver without rehearsal.
- As the audience (professor + classmates), I want to understand CHIME's key idea, what was attempted, and what went wrong without reading walls of text.
- As the student, I want the presentation to work with no experiment results, so I'm not blocked on data collection.

## Design Approach

### Snapshot Strategy

- Single source file: `presentation/main.tex` (overwrite existing skeleton)
- Git tag `progress-v1` at submission time
- New GitHub Actions workflow publishes `presentation/main.pdf` to GitHub Pages
- If GitHub Pages doesn't support large PDFs, use `git lfs track "*.pdf"` as fallback

### Build Outputs

Two targets in `presentation/Makefile`:
- `make` or `make presentation` -> `main.pdf` (no speaker notes, for publishing)
- `make notes` -> `main-notes.pdf` (speaker notes visible on right side, for delivery)

Implementation: a `\ifdefined\SHOWNOTES` toggle in the preamble. The `notes` target passes `\def\SHOWNOTES{}` via `pdflatex "\def\SHOWNOTES{}\input{main}"`.

### CI Pipeline

New workflow: `.github/workflows/presentation.yml`
- Trigger: push to `main` when `presentation/**` changes
- Build: `make` in `presentation/`
- Publish: upload `main.pdf` to GitHub Pages alongside existing `report/main.pdf`

### Image Strategy

Two directories for two types of images:

- `presentation/figures/` — experiment data figures from `exp/results/`. May or may not exist. Use `\IfFileExists` fallback pattern.
- `presentation/diagrams/` — presentation diagrams. Two creation methods:
  - **Simple diagrams**: TikZ (placeholder boxes, timelines, simple tables)
  - **Complex diagrams**: Claude-generated images via prompts. Each complex diagram slide includes a generation prompt in this spec. Generated images committed to repo as PDF or PNG.

Complex diagrams requiring Claude generation:
- Slide 2: Cache vs read-amp trade-off visualization
- Slide 3: CHIME hybrid structure (B+ tree + hopscotch leaves)
- Slide 6: CloudLab cluster topology (10 CN + 1 MN + switch)
- Slide 11: Cluster with broken node
- Slide 14: NFS reuse workflow
- Slide 19: RDMA vs CXL memory model comparison
- Slide 20: Transport abstraction layer architecture
- Slide 21: NUMA emulation dual-socket diagram

### Beamer Configuration

- Theme: `metropolis` (already in use)
- Aspect ratio: 16:9 (`aspectratio=169`)
- Font: default metropolis (Fira Sans)
- Speaker notes: `\usepackage{pgfpages}` with conditional `\setbeameroption{show notes on second screen=right}`
- Citations: `\thebibliography{}` (avoids biber dependency)

### Slide-by-Slide Specification

#### Section 1: What is CHIME? (5 slides, ~3 min)

**Slide 1 — Title**
- Content: Title, author, course, date
- Visual: Clean metropolis title page
- Notes: "Good morning/afternoon, I'm Jason Cusati, presenting my progress on reproducing CHIME for CS 6204."
- Time: 15s

**Slide 2 — The Problem**
- Content: "Disaggregated Memory Indexes" as frame title
- Visual: [CLAUDE DIAGRAM] Trade-off visualization — left side shows B+ tree icon with labels "Low cache" and "High read amplification", right side shows hash index icon with "High cache" and "Low read amplification", tension/trade-off arrow between them. Clean, minimal, professional style with teal and brown tones.
- Prompt: "Create a clean presentation diagram (16:9, white background) showing a trade-off between two approaches. Left side: a small B+ tree icon labeled 'B+ Tree' with annotations 'Low cache consumption' (green) and 'High read amplification' (red). Right side: a hash table icon labeled 'Hash Index' with annotations 'High cache consumption' (red) and 'Low read amplification' (green). Between them: a double-headed arrow labeled 'Trade-off'. Style: minimal, professional, sans-serif, using teal (#2b7a78) and warm brown (#c9956b) accents."
- Notes: "Disaggregated memory separates compute and memory over a network. Range indexes on DM face a fundamental trade-off: B+ trees cache well but need multiple round trips per lookup, while hash indexes are fast but consume huge cache. CHIME breaks this trade-off."
- Time: 45s

**Slide 3 — The Insight**
- Content: Frame title only, diagram carries the slide
- Visual: [CLAUDE DIAGRAM] CHIME hybrid structure — B+ tree internal nodes (teal) at top levels, hopscotch hashing leaf nodes (brown) at bottom. Clear visual separation between tree structure above and hash structure below. Labeled: "B+ tree internals for range queries" and "Hopscotch leaves for point lookups".
- Prompt: "Create a clean presentation diagram (16:9, white background) of a hybrid data structure. Top 2 levels: B+ tree internal nodes as rounded rectangles in teal (#2b7a78, 20% opacity fill, teal border). 1 root node connecting to 2 internal nodes, connecting to 4 leaf nodes. Bottom level: 4 leaf nodes as rounded rectangles in warm brown (#c9956b, 20% opacity fill, brown border) labeled 'Hopscotch'. Right side annotations: 'Low cache' next to internal nodes (teal text), 'Low read amp' next to leaves (brown text). A dashed horizontal line separating internal from leaf level. Style: minimal, sans-serif, professional."
- Notes: "CHIME's key insight: keep B+ tree internals for structure and range queries, but replace sorted leaf nodes with hopscotch hashing. This gives you low cache consumption from the tree structure and low read amplification from hash-based leaves."
- Time: 45s

**Slide 4 — Three Techniques**
- Content: Three labeled items, minimal text
- Visual: Three columns, each with a simple icon and ~5 word label. (1) "Three-level optimistic sync" (2) "Access-aggregated metadata" (3) "Hotness-aware speculative read". Simple TikZ icons or Unicode symbols.
- Notes: "Three techniques make this work. First, three-level optimistic synchronization reuses hopscotch bitmaps for fine-grained concurrency — no global locks. Second, vacancy bitmap piggybacking and metadata replication reduce round trips for metadata. Third, a hotspot buffer shortcuts reads for frequently accessed neighborhoods."
- Time: 50s

**Slide 5 — The Claim**
- Content: Single large number
- Visual: Large typography: "2.0--5.6x throughput" centered. Nothing else.
- Notes: "The paper claims CHIME achieves 2.0 to 5.6 times higher throughput than state-of-the-art DM indexes while using comparable or less cache. Our job: reproduce this on real hardware."
- Time: 30s

#### Section 2: Our Experiment (4 slides, ~3 min)

**Slide 6 — CloudLab Setup**
- Content: Minimal labels only
- Visual: [CLAUDE DIAGRAM] Cluster topology — 10 compute nodes (labeled CN0-CN9) on the left connected via a central 100Gbps switch to 1 memory node (MN) on the right. Hardware label: "r650: 2x36-core Xeon, 256GB, ConnectX-6". Clean network diagram style.
- Prompt: "Create a clean network topology diagram (16:9, white background) for a compute cluster. Left side: 10 server icons arranged in 2 columns of 5, labeled CN0 through CN9 in teal (#2b7a78). Center: a network switch icon labeled '100 Gbps Ethernet'. Right side: 1 larger server icon labeled 'MN' (Memory Node) in warm brown (#c9956b). Lines connecting all servers to the switch. Below the diagram: 'r650: 2x36-core Xeon, 256GB, ConnectX-6' in small gray text. Style: minimal, professional, sans-serif."
- Notes: "We used CloudLab's r650 nodes at Clemson. 10 compute nodes and 1 memory node, each with dual 36-core Xeons and a 100Gbps Mellanox NIC. This matches the paper's setup exactly."
- Time: 40s

**Slide 7 — Methods Compared**
- Content: Clean 5-row table
- Visual: Beamer table with columns Method, Type, Source. Rows: CHIME (Hybrid B+ tree + hopscotch, dmemsys/CHIME), Sherman (B+ tree, CHIME repo), SMART (Radix tree, dmemsys/SMART), ROLEX (Learned index, River861/ROLEX), SMART-SC (Radix tree + sufficient cache, dmemsys/SMART). CHIME row highlighted.
- Notes: "We compared all five methods from the paper. Sherman is a pure B+ tree — actually built from the same CHIME codebase with different compile flags. SMART is a radix tree, ROLEX is a learned index. SMART-SC is SMART with sufficient cache — the upper bound for cache-heavy approaches."
- Time: 45s

**Slide 8 — What We Measured**
- Content: 4 cards
- Visual: 2x2 grid of cards: "Throughput-Latency (Fig 12) — Which method is fastest?" / "Cache Consumption (Fig 14) — At what cost?" / "Feature Breakdown (Fig 15a) — What contributes?" / "Feature Breakdown (Fig 15b) — By how much?". Simple TikZ boxes.
- Notes: "Four core experiments. Figure 12 is the main comparison — throughput vs latency across YCSB workloads. Figure 14 shows how much cache each method consumes. Figures 15a and 15b break down which CHIME techniques contribute how much performance."
- Time: 45s

**Slide 9 — Timeline**
- Content: Visual timeline
- Visual: Horizontal TikZ timeline: "Mar 23-26: r6525 (pre-deadline)" -> "Mar 27-Apr 3: r650 (full run)" -> "Apr 3-6: r650 (10CN)" -> "Apr 7-9: This talk". Color-code: past=gray, active=teal, future=light.
- Notes: "Our timeline. We couldn't get r650 nodes until March 27, so we ran a pre-deadline set on r6525 — different hardware, AMD instead of Intel. We have two more r650 windows for hardware-matched data."
- Time: 30s

#### Section 3: What Happened (7 slides, ~6 min)

**Slide 10 — Challenge: Hardware Mismatch**
- Content: Side-by-side comparison
- Visual: Two-column TikZ: "Paper: r650" with "Intel Xeon, ConnectX-6" vs "Us: r6525" with "AMD EPYC, ConnectX-5". Large "!=" symbol between them.
- Notes: "Our first challenge: r650 nodes were fully booked until after the deadline. We pivoted to r6525 nodes — AMD instead of Intel, different NIC. We had to validate that RDMA features like DCT actually worked on this hardware. They did, but we can't directly compare our numbers to the paper's."
- Time: 50s

**Slide 11 — Challenge: Broken Node**
- Content: Cluster diagram with one node X'd out
- Visual: [CLAUDE DIAGRAM] Same cluster topology as slide 6, but CN9 (node 10) has a red X overlay and label "RDMA failure — clnode304". Remaining 9 CNs + 1 MN are normal.
- Prompt: "Create a network topology diagram (16:9, white background) identical in layout to a 10-CN + 1-MN cluster with a central switch. 9 of the compute nodes are in teal (#2b7a78). The 10th compute node (bottom-right of the CN group) has a red X overlaid and is grayed out, with a red label 'RDMA failure'. The memory node on the right is in warm brown (#c9956b). Style: minimal, professional, sans-serif."
- Notes: "Node 10 had a broken RDMA interface. We couldn't replace it — CloudLab reservations are fixed. So we ran with 9 compute nodes instead of 10. This matches our upcoming r650 run but means figure 12's CN scaling won't match the paper exactly."
- Time: 45s

**Slide 12 — Challenge: Tooling Issues**
- Content: 3 short items
- Visual: Three TikZ icons with one-line labels: "YCSB 0.17 API change" / "16GB root partition" / "No internal network"
- Notes: "Three more issues. YCSB changed its Java package name between versions — broke the workload generator. The r6525 root partition is only 16 gigs — builds and logs fill it fast, so we moved everything to NVMe. And there's no internal network on r6525, so memcached had to use public IPs."
- Time: 50s

**Slide 13 — What We Tried**
- Content: Solutions matching the challenges
- Visual: Three solution cards: "Patched YCSB for site.ycsb + Python 3" / "NVMe mount + project NFS" / "Public IP memcached config". Arrows or check marks linking to previous challenges.
- Notes: "For each issue, we found pragmatic fixes. Patched the YCSB generator for the new API. Mounted NVMe drives and stored workloads on CloudLab's project NFS — which persists across experiments, so we only generate workloads once. And rewrote the memcached config for public IPs."
- Time: 45s

**Slide 14 — Key Win: Persistent Workloads**
- Content: Diagram of NFS reuse pattern
- Visual: [CLAUDE DIAGRAM] Workflow diagram showing: "YCSB Generation (90 min)" arrow to "Project NFS (/proj/...)" which then has arrows to three experiment boxes: "r6525 run", "r650 run", "r650 re-run". Each experiment box shows a symlink icon. Label: "Generate once, reuse everywhere".
- Prompt: "Create a workflow diagram (16:9, white background). Left: a box labeled 'YCSB Generation' with '90 min' subtitle, with an arrow pointing right to a central cylinder/database icon labeled 'Project NFS' in teal (#2b7a78). From the NFS icon, three arrows fan out to the right pointing to three boxes stacked vertically: 'r6525 run (Mar 23)', 'r650 run (Mar 27)', 'r650 re-run (Apr 3)' in warm brown (#c9956b). Each box has a small link icon. Below the diagram: 'Generate once, reuse everywhere' in italic gray. Style: minimal, professional, sans-serif."
- Notes: "The biggest win was persisting YCSB workloads on project NFS. Workload generation takes 90 minutes and produces gigabytes of data. By storing them on shared NFS, every experiment instance — r6525, r650, re-runs — just symlinks to the same data. Saved hours across our three reservation windows."
- Time: 40s

**Slide 15 — Experiment Status**
- Content: Checklist
- Visual: TikZ checklist: "~ r6525 experiments (in progress)" / "○ r650 full run (Mar 27)" / "○ r650 re-run 10 CN (Apr 3)" / "○ Hardware-matched comparison"
- Notes: "Status check. The r6525 pre-deadline experiments are still running. We have two more r650 windows to get hardware-matched data. The final presentation will include those results and a direct comparison to the paper."
- Time: 30s

**Slide 16 — Lessons So Far**
- Content: 2-3 key lessons
- Visual: Two or three short statements in large text: "Reserve hardware early" / "Automate everything you'll repeat" / "Expect API drift in open-source tools"
- Notes: "Three lessons from reproduction. First, reserve CloudLab hardware weeks in advance — popular nodes book up fast. Second, automate setup scripts aggressively because you'll re-run them across multiple reservations. Third, don't assume open-source tooling is frozen — YCSB changed its API between releases and it broke our pipeline."
- Time: 45s

#### Section 4: Expected Results (3 slides, ~2.5 min)

**Slide 17 — What We're Measuring**
- Content: Methodology summary
- Visual: Two-column layout. Left: "Workloads" with list "YCSB A-E, 60M entries, 8B key/value, Zipfian". Right: "Metrics" with list "Throughput (Mops/s), P50/P99 latency (us), Cache size (MB)". Clean table or cards.
- Notes: "Here's what we're running. YCSB workloads A through E — 60 million entries, 8 byte keys and values, Zipfian distribution. We measure throughput in millions of operations per second, median and tail latency in microseconds, and cache consumption in megabytes."
- Time: 40s

**Slide 18 — What We Expect**
- Content: Predictions based on paper
- Visual: Three prediction cards: "CHIME: highest throughput, lowest latency" / "Sherman: low cache, but slow (many round trips)" / "SMART-SC: fast, but massive cache". No actual numbers.
- Notes: "Based on the paper, we expect CHIME to dominate on throughput and latency while using moderate cache. Sherman, being a pure B+ tree, should have low cache consumption but suffer from read amplification. SMART with sufficient cache should be fast but use disproportionate memory. Our final presentation will validate or challenge these expectations."
- Time: 45s

**Slide 19 — [PLACEHOLDER] Early Results**
- Content: Placeholder — to be filled if any experiment data arrives before presentation
- Visual: `\IfFileExists` pattern for any available figure, otherwise: "Results pending — data collection in progress on r650 cluster"
- Notes: [PLACEHOLDER — fill with actual data description if available, otherwise: "Our experiments are still running on the r650 cluster. We'll have hardware-matched results for the final presentation. For now, I've walked you through our methodology and what we expect to see based on the paper's claims."]
- Time: 40s

#### Section 5: CXL Plan (5 slides, ~3.5 min)

**Slide 20 — Why CXL?**
- Content: RDMA vs CXL comparison
- Visual: [CLAUDE DIAGRAM] Two-column comparison. Left: "RDMA" with icons showing NIC-mediated path, labels "Verb-based API", "Async (coroutines)", "NIC processes requests". Right: "CXL" with icons showing direct CPU-memory path, labels "Load/store", "Synchronous", "Cache-coherent". Arrow at bottom: "Industry trend" pointing from RDMA to CXL.
- Prompt: "Create a comparison diagram (16:9, white background) with two columns. Left column header 'RDMA' in teal (#2b7a78): show a simplified path CPU -> NIC -> Network -> Remote Memory, with labels 'Verb-based API', 'Async (coroutines)', 'NIC-mediated'. Right column header 'CXL' in warm brown (#c9956b): show a simplified path CPU -> CXL Bus -> Memory Pool, with labels 'Load/store', 'Synchronous', 'Cache-coherent'. At the bottom, a horizontal arrow from left to right labeled 'Industry trend'. Style: minimal, professional, sans-serif, clean icons."
- Notes: "Part Two ports CHIME to CXL. CXL is the industry's answer to disaggregated memory — instead of going through a NIC with RDMA verbs, you do direct load/store to remote memory with hardware cache coherence. It's lower latency but changes the programming model fundamentally."
- Time: 45s

**Slide 21 — Transport Abstraction**
- Content: Architecture diagram
- Visual: [CLAUDE DIAGRAM] Three-layer architecture. Top: "Index Layer" spanning full width with "CHIME / Sherman / SMART / ROLEX / Marlin". Middle: "Transport Interface" with API labels "read / write / CAS". Bottom split into two: left "RDMA Backend (wraps DSM, + coroutines)" in teal, right "CXL Backend (NUMA mmap, synchronous)" in brown.
- Prompt: "Create a layered architecture diagram (16:9, white background). Top layer: wide rounded rectangle labeled 'Index Layer' with subtitle 'CHIME / Sherman / SMART / ROLEX / Marlin' in gray (#555). Middle layer: wide rounded rectangle labeled 'Transport Interface' with small text 'read_sync / write_sync / cas_sync' in dark gray. Bottom layer split in half: left rounded rectangle in teal (#2b7a78, 20% fill) labeled 'RDMA Backend' with small text 'wraps DSM + coroutines', right rounded rectangle in warm brown (#c9956b, 20% fill) labeled 'CXL Backend' with small text 'NUMA mmap + atomics'. Arrows pointing down between layers. Style: minimal, professional, sans-serif."
- Notes: "Our approach: a compile-time transport abstraction. The index code calls generic read/write/CAS operations. At build time, we select either the RDMA backend — which wraps the existing DSM — or the CXL backend, which uses NUMA-mapped memory with direct CPU operations. Zero vtable overhead thanks to C++ templates."
- Time: 45s

**Slide 22 — NUMA Emulation**
- Content: r650 dual-socket diagram
- Visual: [CLAUDE DIAGRAM] r650 dual-socket diagram. Left socket: "Socket 0 / NUMA 0" labeled "Compute (application threads)" in teal. Right socket: "Socket 1 / NUMA 1" labeled "CXL Memory Pool" in brown. UPI interconnect between them labeled "~100ns". Below: "No real CXL hardware — NUMA cross-socket access emulates CXL latency".
- Prompt: "Create a hardware diagram (16:9, white background) showing a dual-socket server. Left: a CPU/chip icon labeled 'Socket 0 / NUMA 0' with subtitle 'Compute' in teal (#2b7a78). Right: a CPU/chip icon labeled 'Socket 1 / NUMA 1' with subtitle 'CXL Memory Pool' in warm brown (#c9956b). Between them: a bidirectional arrow labeled 'UPI ~100ns'. Below the diagram in italic gray: 'NUMA cross-socket latency emulates CXL'. Style: minimal, professional, sans-serif, clean chip/processor icons."
- Notes: "We don't have real CXL hardware, so we emulate it using the r650's second NUMA domain. Application threads run on socket 0, memory pool is bound to socket 1. Cross-socket latency approximates CXL's expected 100-200 nanoseconds of additional latency."
- Time: 40s

**Slide 23 — What We Expect from CXL**
- Content: Hypotheses
- Visual: Three prediction cards: "Lower per-op latency (no NIC overhead)" / "No coroutines needed (sync load/store)" / "Masked CAS emulation risk (tail latency)"
- Notes: "Three hypotheses. One: CXL should have lower per-operation latency — no NIC overhead. Two: RDMA uses coroutines to hide network latency; CXL doesn't need them because operations complete synchronously. Three: RDMA NICs support masked CAS natively, but CPUs don't — we'll need to emulate it, which could hurt tail latency under contention."
- Time: 45s

**Slide 24 — Part Two Timeline**
- Content: Timeline
- Visual: Horizontal TikZ timeline: "Apr 7-9: This talk" -> "Apr: Transport layer" -> "Late Apr: CXL experiments" -> "May 5: Final report"
- Notes: "The plan: implement the transport abstraction in April, run CXL experiments on the r650 nodes we already have reserved, and submit the final report May 5th."
- Time: 20s

#### Section 6: Close (3 slides, ~2 min)

**Slide 25 — Key Takeaways**
- Content: 3 items max
- Visual: Three large, short statements: "Hybrid indexes break the trade-off" / "Reproduction is harder than it looks" / "CXL will change the game"
- Notes: "Three things to remember. CHIME's hybrid B+ tree plus hopscotch design genuinely breaks the cache vs read-amp trade-off. Reproducing systems research is harder than reading the paper — hardware availability, tooling drift, and configuration issues dominate the work. And CXL is going to change how we think about disaggregated memory indexes."
- Time: 40s

**Slide 26 — References**
- Content: Key citations (numbered, compact)
- Visual: 5-6 references: CHIME (SOSP '24), Sherman (SIGMETICS '22), SMART (ATC '23), ROLEX (OSDI '24), CXL spec. Use `\thebibliography`.
- Notes: No spoken content — reference slide for Q&A.
- Time: 5s

**Slide 27 — Questions?**
- Content: Standout frame
- Visual: metropolis `[standout]` frame with "Questions?"
- Notes: "Thank you. Happy to take questions about the reproduction, our CXL plans, or anything about CHIME's design."
- Time: remainder

### Design Guidelines

**Typography rules:**
- Maximum 15 words of visible text per slide (excluding speaker notes, tables, citations)
- No bullet points with more than 5 words per item
- Prefer diagrams, figures, and single stats over text
- Use metropolis's built-in `\alert{}` for emphasis, not bold+italic

**Figure handling:**
- Experiment figures: `\IfFileExists{figures/fig_XX.pdf}{\includegraphics{...}}{placeholder}` pattern
- Experiment figures stored in `presentation/figures/` (copied from `exp/results/` when available)
- Diagrams stored in `presentation/diagrams/` (committed to repo)
- All images scaled to fill the frame (`width=\textwidth` or `height=0.8\textheight`)

**Speaker notes format:**
```latex
\note{
  \textbf{Key point:} [One sentence]\\
  \textbf{Say:} [2-3 sentence delivery script]\\
  \textbf{Transition:} [Bridge to next slide]\\
  \textbf{Time:} [Target seconds]
}
```

**Placeholder pattern for results slides:**
```latex
\note{
  \textbf{Key point:} [PLACEHOLDER --- update with actual findings]\\
  \textbf{Say:} [PLACEHOLDER --- describe what the data shows]\\
  \textbf{Transition:} [Bridge to next slide]\\
  \textbf{Time:} [Target seconds]
}
```

## Sample Implementation

```latex
% Preamble with notes toggle
\documentclass[aspectratio=169]{beamer}
\usetheme{metropolis}

\ifdefined\SHOWNOTES
  \usepackage{pgfpages}
  \setbeameroption{show notes on second screen=right}
\fi

% ... packages ...

\begin{document}

% Representative results slide with placeholder pattern
\begin{frame}{Early Results}
\centering
\IfFileExists{figures/fig_12_a.pdf}{%
  \includegraphics[width=0.9\textwidth]{figures/fig_12_a.pdf}%
}{%
  \begin{tikzpicture}
    \draw[gray, dashed] (0,0) rectangle (10,6);
    \node[gray, align=center] at (5,3)
      {\large Results pending\\[0.5em]
       \normalsize Data collection in progress on r650};
  \end{tikzpicture}%
}
\note{
  \textbf{Key point:} [PLACEHOLDER --- update with actual findings]\\
  \textbf{Say:} [PLACEHOLDER --- describe what the data shows.
  If no data: ``Our experiments are still running on the r650
  cluster. We'll have hardware-matched results for the final
  presentation.'']\\
  \textbf{Transition:} Let's look at what's next --- our CXL plan.\\
  \textbf{Time:} 40s
}
\end{frame}

% Representative diagram slide using committed image
\begin{frame}{CHIME: Hybrid Structure}
\centering
\includegraphics[height=0.8\textheight]{diagrams/chime-hybrid-structure.pdf}
\note{
  \textbf{Key point:} Hybrid = tree structure + hash leaves.\\
  \textbf{Say:} CHIME keeps B+ tree internal nodes for structure
  and range query support, but replaces sorted leaves with
  hopscotch hashing. Internal nodes cache well because there
  are few of them. Leaves use hashing to find keys in one
  round trip instead of binary search.\\
  \textbf{Transition:} Three specific techniques make this
  hybrid work in practice.\\
  \textbf{Time:} 45s
}
\end{frame}

% Makefile targets
% make:       pdflatex main (no notes)
% make notes: pdflatex "\def\SHOWNOTES{}\input{main}" -jobname=main-notes

\end{document}
```

## Edge Cases & Error Handling

### EC-1: No Experiment Figures Available
- **Scenario**: All experiment data is still pending at presentation time
- **Behavior**: Results section (slides 17-19) focuses on methodology and expectations. Slide 19 shows placeholder. Speaker notes have fallback scripts.
- **Test**: Build with empty `presentation/figures/`, verify placeholders render and notes are coherent

### EC-2: Too Many/Few Slides for Time
- **Scenario**: 27 slides runs over or under 20 minutes
- **Behavior**: Speaker notes include per-slide timing totaling ~20 min. If over: cut slide 16 (Lessons) first, then compress challenges (10-13) into 2 slides. If under: expand speaker notes on CXL section.
- **Test**: Sum timing annotations; verify total is 18-22 min

### EC-3: Audience Asks About Missing Results
- **Scenario**: Professor asks why there are no experiment results
- **Behavior**: Slide 15 (Experiment Status) and slide 19 (Placeholder) explicitly address timeline. Speaker notes include: "We'll have hardware-matched data for the final presentation."
- **Test**: Review notes for slides 15 and 19

### EC-4: Claude-Generated Diagrams Don't Match Theme
- **Scenario**: Generated images clash with metropolis color palette
- **Behavior**: Prompts specify exact hex colors (#2b7a78 teal, #c9956b brown). Regenerate with refined prompt if needed. Fallback: simple TikZ version.
- **Test**: Visual review of each diagram against metropolis theme

### EC-5: CI Pipeline Fails on LaTeX Build
- **Scenario**: GitHub Actions can't build the presentation
- **Behavior**: Use `xu-cheng/latex-action` or similar Docker-based LaTeX builder. Fallback: manually upload PDF.
- **Test**: Push a change to `presentation/` and verify CI produces artifact

## Acceptance Criteria

### AC-1: Compiles Cleanly — Two Outputs
- **Given** the updated `presentation/main.tex`
- **When** running `make` and `make notes` in `presentation/`
- **Then** produces `main.pdf` (no notes) and `main-notes.pdf` (with notes) with no LaTeX errors

### AC-2: Slide Count and Timing
- **Given** the complete deck
- **When** counting slides
- **Then** 25-29 slides total, timing annotations sum to 18-22 minutes

### AC-3: Zen Aesthetic
- **Given** any content slide (excluding title, references, questions, tables)
- **When** counting visible text words
- **Then** no slide exceeds 20 words

### AC-4: Speaker Notes Coverage
- **Given** every slide
- **When** checking for `\note{}`
- **Then** every slide has notes with Key point, Say, Transition, and Time fields. Results slides clearly marked [PLACEHOLDER] where data-dependent.

### AC-5: Figure Fallback
- **Given** the deck built with zero figures in `presentation/figures/`
- **When** viewing the PDF
- **Then** all experiment figure slides show labeled placeholders, no broken references

### AC-6: Diagrams Committed
- **Given** the `presentation/diagrams/` directory
- **When** listing files
- **Then** all Claude-generated diagrams exist as PDF or PNG, referenced correctly from main.tex

### AC-7: One Idea Per Slide
- **Given** any slide
- **When** reading its content
- **Then** it conveys exactly one concept

### AC-8: PDF Published via CI
- **Given** a push to `main` modifying `presentation/`
- **When** CI completes
- **Then** `main.pdf` is accessible on GitHub Pages

### AC-9: Citations Present
- **Given** the references slide
- **When** reviewing citations
- **Then** CHIME, Sherman, SMART, ROLEX cited with correct venue and year

## Technical Notes

- **Affected files**: `presentation/main.tex` (rewrite), `presentation/Makefile` (add `notes` target), new `presentation/diagrams/` directory, new `.github/workflows/presentation.yml`
- **New files**: `presentation/diagrams/*.pdf` (Claude-generated), CI workflow
- **Patterns to follow**: Existing metropolis theme; `\IfFileExists` for figure degradation; `\ifdefined` for notes toggle
- **No biblatex**: Use `\thebibliography` to avoid biber dependency in CI
- **Diagram count**: 8 Claude-generated diagrams (slides 2, 3, 6, 11, 14, 20, 21, 22)

## Dependencies

- Metropolis Beamer theme (standard in TeX Live)
- TikZ package (standard in TeX Live)
- Claude agent for diagram generation (8 diagrams)
- GitHub Actions with LaTeX support for CI
- Experiment figures optional (graceful degradation)

## Open Questions

- **Diagram format**: Should Claude-generated diagrams be PNG or PDF? PDF is vector and scales better in Beamer, but PNG may be simpler to generate.
- **GitHub Pages structure**: Where exactly should the presentation PDF land relative to the existing report PDF? Same directory or separate path?
- **Speaker notes PDF size**: The notes version with `pgfpages` doubles the page count. Acceptable for a ~27 slide deck, but verify CI doesn't choke.

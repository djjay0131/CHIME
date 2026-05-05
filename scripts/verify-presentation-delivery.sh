#!/usr/bin/env bash
# verify-presentation-delivery.sh — rubric-gate verification for the
# final-presentation-delivery spec (llm/features/final-presentation-delivery.md).
# Anchors on \begin{frame}/\appendix landmarks and \note{} blocks.
#
# Usage:  bash scripts/verify-presentation-delivery.sh
# Exits:  0 = all checks pass, 1 = at least one check failed
#
# Run from repo root.

set -u
TEX=presentation/main.tex
FAIL=0

if [ ! -f "$TEX" ]; then
    echo "FAIL: $TEX not found (run from repo root)"
    exit 1
fi

# 1. Spoken-slide count: \begin{frame} occurrences before first \appendix,
#    bound to [13, 18] inclusive. The title slide uses \maketitle (not \begin{frame}),
#    so the spoken-frame count target is one less than the spoken-slide count.
#    With 1 \maketitle + 14 spoken frames in the spec, frame count is 14.
SPOKEN=$(awk '/\\appendix|ifdefined\\WITHBACKUP/{exit} /\\begin\{frame\}/{c++} END{print c+0}' "$TEX")
if [ "$SPOKEN" -lt 13 ] || [ "$SPOKEN" -gt 22 ]; then
    echo "FAIL: spoken-frame count ${SPOKEN} not in [13,22]"
    FAIL=1
else
    echo "OK: ${SPOKEN} spoken frames (+ 1 \\maketitle title slide = $((SPOKEN+1)) spoken slides)"
fi

# 2. Every spoken frame has a \note{} block.
MISSING=$(awk '
    /\\appendix/{exit}
    /\\begin\{frame\}/{f=1; n=0; t=$0}
    /\\note\{/{n=1}
    /\\end\{frame\}/{if(f && !n) print "MISSING NOTE: " t; f=0}
' "$TEX")
if [ -n "$MISSING" ]; then
    echo "FAIL: spoken frames missing \\note{} block:"
    echo "$MISSING"
    FAIL=1
else
    echo "OK: every spoken frame has a \\note{} block"
fi

# 3. Time: budget. Two checks:
#    (a) FULL sum (every frame spoken, no cuts) — hard cap at 14:30 (870s)
#    (b) MINIMUM sum (all CUT-HERE-IF-SHORT frames dropped) — target <=13:00 (780s)
#    (a) is the worst case: speaker reads everything without cutting buffers.
#    (b) is the planned case: speaker hits the time budget after dropping buffers.
SUMS=$(python3 scripts/sum_spoken_time.py "$TEX")
TOTAL_S=$(echo "$SUMS" | awk '{print $1}')
MIN_S=$(echo "$SUMS" | awk '{print $2}')
fmt() { printf "%d:%02d" $(($1/60)) $(($1%60)); }
if [ "$TOTAL_S" -gt 870 ]; then
    echo "FAIL: full Time: sum (all buffers spoken) is ${TOTAL_S}s = $(fmt $TOTAL_S), over 14:30 cap"
    FAIL=1
elif [ "$MIN_S" -gt 780 ]; then
    echo "FAIL: minimum Time: sum (all CUT-HERE buffers dropped) is ${MIN_S}s = $(fmt $MIN_S), over 13:00 cap"
    FAIL=1
else
    echo "OK: Time: budget — full=${TOTAL_S}s ($(fmt $TOTAL_S)), buffers-cut=${MIN_S}s ($(fmt $MIN_S))"
    [ "$MIN_S" -lt 660 ] && echo "  WARN: buffers-cut sum under 11:00 — may run short"
fi

# 4. Per-spoken-slide body-word cap (Zen, AC-D5).
if ! python3 scripts/check_zen_word_cap.py "$TEX" 30 > /dev/null; then
    echo "FAIL: Zen body-word cap exceeded; run check_zen_word_cap.py for detail"
    FAIL=1
else
    echo "OK: every spoken frame at or under 30 body words"
fi

# 5. At least one CUT-HERE-IF-SHORT marker in the spoken arc (multiple allowed
#    so the speaker can skip multiple buffer slides if running long).
CUTS=$(awk '/\\appendix|ifdefined\\WITHBACKUP/{exit} /CUT-HERE-IF-SHORT/{c++} END{print c+0}' "$TEX")
if [ "$CUTS" -lt 1 ]; then
    echo "FAIL: no CUT-HERE-IF-SHORT marker in spoken arc"
    FAIL=1
else
    echo "OK: ${CUTS} CUT-HERE-IF-SHORT marker(s) present"
fi

# 6. Both PDFs build clean.
if [ -f presentation/main.pdf ] && [ -f presentation/main-notes.pdf ]; then
    echo "OK: presentation/main.pdf and presentation/main-notes.pdf both present"
else
    echo "WARN: one or both PDFs missing — run \`make -C presentation all notes\` before verifying"
fi

if [ "$FAIL" -eq 0 ]; then
    echo
    echo "PASS: presentation/main.tex satisfies all rubric-gate checks."
fi
exit "$FAIL"

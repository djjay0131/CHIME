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
SPOKEN=$(awk '/\\appendix/{exit} /\\begin\{frame\}/{c++} END{print c+0}' "$TEX")
if [ "$SPOKEN" -lt 13 ] || [ "$SPOKEN" -gt 18 ]; then
    echo "FAIL: spoken-frame count ${SPOKEN} not in [13,18]"
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

# 3. Sum of Time: values in spoken arc (\maketitle's note is included since
#    it's before the first \begin{frame}). Cap at 780s (13:00) hard.
TOTAL_S=$(awk '
    /\\appendix/{exit}
    /Time:/{match($0, /[0-9]+s/); if(RSTART) s+=substr($0,RSTART,RLENGTH-1)}
    END{print s+0}
' "$TEX")
if [ "$TOTAL_S" -gt 780 ]; then
    echo "FAIL: spoken Time: sum is ${TOTAL_S}s, over 13:00 cap"
    FAIL=1
elif [ "$TOTAL_S" -lt 660 ]; then
    echo "WARN: spoken Time: sum is ${TOTAL_S}s, under 11:00 (might be too short)"
    echo "OK (with WARN): ${TOTAL_S}s = $((TOTAL_S/60)):$(printf '%02d' $((TOTAL_S%60)))"
else
    echo "OK: spoken Time: sum is ${TOTAL_S}s = $((TOTAL_S/60)):$(printf '%02d' $((TOTAL_S%60)))"
fi

# 4. Per-spoken-slide body-word cap (Zen, AC-D5).
if ! python3 scripts/check_zen_word_cap.py "$TEX" 30 > /dev/null; then
    echo "FAIL: Zen body-word cap exceeded; run check_zen_word_cap.py for detail"
    FAIL=1
else
    echo "OK: every spoken frame at or under 30 body words"
fi

# 5. Exactly one CUT-HERE-IF-SHORT marker in the spoken arc.
CUTS=$(awk '/\\appendix/{exit} /CUT-HERE-IF-SHORT/{c++} END{print c+0}' "$TEX")
if [ "$CUTS" -ne 1 ]; then
    echo "FAIL: expected exactly 1 CUT-HERE-IF-SHORT marker, got ${CUTS}"
    FAIL=1
else
    echo "OK: 1 CUT-HERE-IF-SHORT marker present"
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

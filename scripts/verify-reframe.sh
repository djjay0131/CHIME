#!/usr/bin/env bash
# verify-reframe.sh — rubric-gate verification for the final-project-reframe
# spec (llm/features/final-project-reframe.md, AC-R8). Anchors on LaTeX
# labels and bullet position rather than prose, so a copyedit pass cannot
# silently drift the verification.
#
# Usage:  bash scripts/verify-reframe.sh
# Exits:  0 = all checks pass, 1 = one or more checks failed
#
# Run from repo root.

set -u
TEX="report/main-partwo.tex"
PDF="report/main-partwo.pdf"
FAIL=0

if [ ! -f "$TEX" ]; then
    echo "FAIL: $TEX not found (run from repo root)"
    exit 1
fi

# 1. Structural anchors present (not prose-dependent):
for label in sec:approach sec:postmortem sec:conclusion \
             sec:approach:fleet sec:approach:cloudlab \
             sec:approach:runner sec:approach:limits; do
    if ! grep -q "\\\\label{${label}}" "$TEX"; then
        echo "FAIL: missing \\label{${label}}"
        FAIL=1
    fi
done

# 2. Top-2 \items inside \subsection{Contributions} carry orchestration
#    labels. Verified by *position*: the first \item line in the
#    Contributions block must contain \label{contrib:orch:1}, and the
#    second \item line must contain \label{contrib:orch:2}.
PYRESULT=$(python3 - <<'PYEOF'
import re, sys
with open("report/main-partwo.tex") as f:
    text = f.read()
m = re.search(r"\\subsection\{Contributions\}.*?\\end\{itemize\}",
              text, re.DOTALL)
if not m:
    print("FAIL: could not locate \\subsection{Contributions} ... \\end{itemize}")
    sys.exit(1)
block = m.group(0)
items = re.findall(r"\\item\b[^\n]*", block)
if len(items) < 2:
    print(f"FAIL: only {len(items)} \\item entries in Contributions block")
    sys.exit(1)
ok1 = "\\label{contrib:orch:1}" in items[0]
ok2 = "\\label{contrib:orch:2}" in items[1]
if not ok1:
    print(f"FAIL: first \\item missing \\label{{contrib:orch:1}}: {items[0][:80]}")
if not ok2:
    print(f"FAIL: second \\item missing \\label{{contrib:orch:2}}: {items[1][:80]}")
sys.exit(0 if ok1 and ok2 else 1)
PYEOF
)
if [ -n "$PYRESULT" ]; then
    echo "$PYRESULT"
    FAIL=1
fi

# 3. §3 Approach is positioned between §2 Setup and §4 Effort.
SETUP_LINE=$(grep -n '\\label{sec:setup}' "$TEX" | head -1 | cut -d: -f1)
APPROACH_LINE=$(grep -n '\\label{sec:approach}' "$TEX" | head -1 | cut -d: -f1)
EFFORT_LINE=$(grep -n '\\label{sec:effort}' "$TEX" | head -1 | cut -d: -f1)
if [ -z "$SETUP_LINE" ] || [ -z "$APPROACH_LINE" ] || [ -z "$EFFORT_LINE" ]; then
    echo "FAIL: one of sec:setup, sec:approach, sec:effort labels missing"
    FAIL=1
elif [ "$SETUP_LINE" -ge "$APPROACH_LINE" ] || \
     [ "$APPROACH_LINE" -ge "$EFFORT_LINE" ]; then
    echo "FAIL: section ordering wrong: setup=L$SETUP_LINE, approach=L$APPROACH_LINE, effort=L$EFFORT_LINE"
    FAIL=1
fi

# 4. API-additions lists in §3.2 and §8 match (AC-R12).
python3 scripts/check_api_additions_match.py "$TEX" || FAIL=1

# 5. Surface-area tripwire (informational, never fails).
if [ -f "$PDF" ]; then
    PCT=$(python3 scripts/measure_spine_pct.py "$PDF" "$TEX" 2>/dev/null || echo 0)
    if [ "$PCT" -lt 20 ] 2>/dev/null; then
        echo "WARN: spine sections at ${PCT}% of report pages, below 20% tripwire"
    else
        echo "OK: spine sections at ${PCT}% of report pages"
    fi
fi

# 6. Rubric mapping printout (always runs, never fails).
echo
echo "Rubric guideline mapping:"
echo "  #1 Experimental setup       -> sec:setup"
echo "  #2 Engineering effort       -> sec:approach + sec:effort"
echo "  #3 Repro vs stress separation -> sec:repro + sec:stress"
echo "  #4 Repro results + gaps     -> sec:repro + sec:postmortem"
echo "  #5 Stress-testing           -> sec:stress"
echo "  #6 Paper-matching figures   -> sec:repro"

if [ "$FAIL" -eq 0 ]; then
    echo
    echo "PASS: all rubric-gate checks satisfied."
fi
exit "$FAIL"

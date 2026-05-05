#!/usr/bin/env python3
"""Sum spoken-arc Time: values, separating CUT-HERE-cuttable frames.

Output: "<full> <minimum>" — full = every spoken frame counted,
minimum = with all CUT-HERE-IF-SHORT-tagged frames dropped.
"""
import re
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: sum_spoken_time.py <tex>", file=sys.stderr)
        return 1
    try:
        text = open(sys.argv[1]).read()
    except (FileNotFoundError, OSError) as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1

    # Truncate at appendix/conditional include
    m = re.search(r"\\appendix|\\ifdefined\\WITHBACKUP", text)
    spoken = text[: m.start()] if m else text

    total = 0
    minimum = 0

    # Walk by lines so we can detect CUT-HERE-IF-SHORT comment immediately
    # preceding a \begin{frame} — within the previous 3 non-blank lines.
    lines = spoken.splitlines()
    n = len(lines)
    i = 0
    while i < n:
        line = lines[i]
        if line.lstrip().startswith(r"\begin{frame}"):
            # Detect CUT-HERE marker in the 3 previous non-blank lines
            is_cut = False
            j = i - 1
            checked = 0
            while j >= 0 and checked < 3:
                prev = lines[j].strip()
                if prev:
                    if "CUT-HERE-IF-SHORT" in prev:
                        is_cut = True
                        break
                    checked += 1
                j -= 1
            # Find matching \end{frame} and extract Time:
            seconds = 0
            k = i + 1
            while k < n and not lines[k].lstrip().startswith(r"\end{frame}"):
                tm = re.search(r"Time:[^0-9]*?(\d+)s", lines[k])
                if tm:
                    seconds = int(tm.group(1))
                k += 1
            total += seconds
            if not is_cut:
                minimum += seconds
            i = k + 1 if k < n else n
        else:
            i += 1

    # Also count the \maketitle title-slide note's Time: (which is NOT inside
    # a \begin{frame} block — it's a free-standing \note{} after \maketitle).
    mtl = re.search(r"\\maketitle\b(.*?)(?=\\begin\{frame\}|\\section\b|\\appendix|$)",
                    spoken, re.DOTALL)
    if mtl:
        tm = re.search(r"Time:[^0-9]*?(\d+)s", mtl.group(1))
        if tm:
            seconds = int(tm.group(1))
            total += seconds
            minimum += seconds

    print(f"{total} {minimum}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

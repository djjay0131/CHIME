#!/usr/bin/env python3
"""
check_api_additions_match.py — AC-R12 verification.

Extracts the three CloudLab-API-additions list from the inline §3.2
\\label{api-additions:approach} block and the source-of-truth §8
\\label{api-additions:postmortem} block, then verifies the *core* claim of
each numbered item (the \\textbf{...} title) is the same across both lists.

Prose around the title is allowed to differ — the spec's contract is that
the three additions match in identity and order, not byte-for-byte.

Usage:  python3 scripts/check_api_additions_match.py <tex-file>
Exits:  0 = match, 1 = drift detected
"""
import re
import sys


def extract_titles(text: str, label: str) -> list[str]:
    """Find the list immediately following \\label{label} and return the
    \\textbf{...} title of each \\item, in order."""
    pat = rf"\\label\{{{re.escape(label)}\}}.*?\\begin\{{(itemize|enumerate)\}}(.*?)\\end\{{\1\}}"
    m = re.search(pat, text, re.DOTALL)
    if not m:
        return []
    block = m.group(2)
    titles = re.findall(r"\\item\b[^\n]*?\\textbf\{([^}]+)\}", block)
    return [t.strip().rstrip(".") for t in titles]


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_api_additions_match.py <tex-file>", file=sys.stderr)
        return 1
    tex_path = sys.argv[1]
    try:
        with open(tex_path) as f:
            text = f.read()
    except FileNotFoundError:
        print(f"FAIL: tex file not found: {tex_path}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"FAIL: could not read {tex_path}: {e}", file=sys.stderr)
        return 1

    approach = extract_titles(text, "api-additions:approach")
    postmortem = extract_titles(text, "api-additions:postmortem")

    if not approach:
        print("FAIL: api-additions:approach list not found or empty")
        return 1
    if not postmortem:
        print("FAIL: api-additions:postmortem list not found or empty")
        return 1
    if len(approach) != len(postmortem):
        print(f"FAIL: list length mismatch: §3.2={len(approach)}, §8={len(postmortem)}")
        print(f"  §3.2 titles:    {approach}")
        print(f"  §8   titles:    {postmortem}")
        return 1
    drift = []
    for i, (a, p) in enumerate(zip(approach, postmortem), 1):
        if a != p:
            drift.append((i, a, p))
    if drift:
        print("FAIL: api-additions title drift between §3.2 and §8:")
        for i, a, p in drift:
            print(f"  item {i}: §3.2='{a}' vs §8='{p}'")
        return 1
    print(f"OK: {len(approach)} api-additions titles match between §3.2 and §8.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
measure_spine_pct.py — surface-area tripwire (AC-R7).

Reports what percentage of the report's rendered pages are dedicated to
the agent-orchestration spine (abstract + §3 Approach + §8 Postmortem).
Tripwire only — informs whether to expand §3.4, never a hard fail.

Usage:  python3 scripts/measure_spine_pct.py <pdf> <tex>
Output: integer percent (0-100) on stdout
"""
import re
import subprocess
import sys


def total_pages(pdf_path: str) -> int:
    try:
        out = subprocess.check_output(["pdfinfo", pdf_path]).decode()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return 0
    m = re.search(r"^Pages:\s+(\d+)", out, re.MULTILINE)
    return int(m.group(1)) if m else 0


def section_line_ranges(tex_path: str) -> dict[str, int]:
    """Return {label: line-number} for every \\label{...} in the .tex file.
    Returns empty dict if the file cannot be opened."""
    out: dict[str, int] = {}
    try:
        with open(tex_path) as f:
            for i, line in enumerate(f, start=1):
                for m in re.finditer(r"\\label\{([^}]+)\}", line):
                    out.setdefault(m.group(1), i)
    except (FileNotFoundError, OSError):
        pass
    return out


def estimate_pct(pdf_path: str, tex_path: str) -> int:
    """Estimate spine percentage as (sum of spine section line spans) /
    (total file line span). Crude but good enough as a tripwire — actual
    page-level mapping requires \\pageref macros we have not added."""
    labels = section_line_ranges(tex_path)
    needed = ["sec:approach", "sec:effort", "sec:postmortem", "sec:late-data"]
    if not all(k in labels for k in needed):
        return 0
    try:
        with open(tex_path) as f:
            total_lines = sum(1 for _ in f)
    except (FileNotFoundError, OSError):
        return 0
    approach_span = labels["sec:effort"] - labels["sec:approach"]
    postmortem_span = labels["sec:late-data"] - labels["sec:postmortem"]
    spine_lines = approach_span + postmortem_span
    return int(round(100 * spine_lines / max(total_lines, 1)))


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: measure_spine_pct.py <pdf> <tex>", file=sys.stderr)
        return 1
    print(estimate_pct(sys.argv[1], sys.argv[2]))
    return 0


if __name__ == "__main__":
    sys.exit(main())

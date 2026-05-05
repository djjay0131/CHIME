#!/usr/bin/env python3
"""
check_zen_word_cap.py — Zen body-word cap check for the spoken arc.

Per llm/features/final-presentation-delivery.md AC-D5:
  body word count <= 30 per spoken slide,
  excluding frame title, figure captions, axis labels, TikZ blocks,
  table contents, lstlisting blocks, and \\note{} blocks.

Walk the file from \\begin{document} to the first \\appendix; for each
\\begin{frame}...\\end{frame} block, strip the excluded environments and
count remaining words.

Usage:  python3 scripts/check_zen_word_cap.py <tex-file> <cap>
Exits:  0 = all spoken slides under cap, 1 = at least one over
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


STRIP_ENVS = ("tikzpicture", "lstlisting", "tabular", "figure", "table")
STRIP_MACROS = (
    r"\\frametitle\{[^}]*\}",
    r"\\caption\{[^}]*\}",
    r"\\includegraphics(?:\[[^\]]*\])?\{[^}]*\}",
)


def strip_blocks(text: str) -> str:
    """Remove environments and macro-arg content that don't count as body words."""
    # Remove \begin{ENV}...\end{ENV} blocks
    for env in STRIP_ENVS:
        pat = re.compile(
            rf"\\begin\{{{env}\}}(?:\[[^\]]*\])?.*?\\end\{{{env}\}}",
            re.DOTALL,
        )
        text = pat.sub(" ", text)
    # Remove \note{...} (brace-balanced)
    text = strip_balanced_macro(text, r"\\note")
    # Remove specific macros and their argument
    for pat in STRIP_MACROS:
        text = re.sub(pat, " ", text)
    # Remove the title in \begin{frame}{Title}
    text = re.sub(r"\\begin\{frame\}(?:\[[^\]]*\])?\{[^}]*\}", " ", text)
    # Remove latex comments
    text = re.sub(r"(?<!\\)%[^\n]*", " ", text)
    return text


def strip_balanced_macro(text: str, macro_pattern: str) -> str:
    """Strip a macro and its brace-balanced argument."""
    out_parts: list[str] = []
    i = 0
    macro_re = re.compile(macro_pattern + r"\s*\{")
    while i < len(text):
        m = macro_re.search(text, i)
        if not m:
            out_parts.append(text[i:])
            break
        out_parts.append(text[i:m.start()])
        # Find matching close brace
        j = m.end()
        depth = 1
        while j < len(text) and depth > 0:
            c = text[j]
            if c == "\\" and j + 1 < len(text):
                j += 2
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            j += 1
        i = j  # past the closing brace
    return "".join(out_parts)


WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9'-]+")


def count_words(text: str) -> int:
    """Count alphabetic-leading words in remaining text. LaTeX macros
    (e.g., \\textbf, \\emph) and pure-numeric tokens don't count as words;
    the contents inside their {} groups DO."""
    # Remove backslash macro names but keep their argument contents
    text = re.sub(r"\\[A-Za-z@]+\*?(?:\[[^\]]*\])?", " ", text)
    # Remaining { and } are noise
    text = text.replace("{", " ").replace("}", " ")
    return len(WORD_RE.findall(text))


def split_spoken_frames(tex: str) -> list[tuple[str, str]]:
    """Return [(frame_title, frame_body), ...] for frames before \\appendix."""
    # Truncate at \appendix
    appendix_match = re.search(r"\\appendix", tex)
    body = tex[:appendix_match.start()] if appendix_match else tex
    # Find document body start
    bd = body.find(r"\begin{document}")
    if bd >= 0:
        body = body[bd + len(r"\begin{document}"):]
    # Find each \begin{frame} ... \end{frame}
    frames = []
    pos = 0
    frame_re = re.compile(r"\\begin\{frame\}(?:\[[^\]]*\])?(?:\{([^}]*)\})?")
    end_re = re.compile(r"\\end\{frame\}")
    while True:
        m = frame_re.search(body, pos)
        if not m:
            break
        title = m.group(1) or "[plain]"
        e = end_re.search(body, m.end())
        if not e:
            break
        frames.append((title.strip(), body[m.start():e.end()]))
        pos = e.end()
    return frames


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: check_zen_word_cap.py <tex-file> <cap>", file=sys.stderr)
        return 2
    tex_path = Path(sys.argv[1])
    try:
        cap = int(sys.argv[2])
    except ValueError:
        print(f"FAIL: cap must be an integer, got {sys.argv[2]!r}", file=sys.stderr)
        return 2
    try:
        tex = tex_path.read_text()
    except FileNotFoundError:
        print(f"FAIL: tex file not found: {tex_path}", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"FAIL: could not read {tex_path}: {e}", file=sys.stderr)
        return 1

    frames = split_spoken_frames(tex)
    over = []
    for title, body in frames:
        stripped = strip_blocks(body)
        w = count_words(stripped)
        marker = "OK" if w <= cap else "OVER"
        print(f"  {marker:5} ({w:3} words) {title}")
        if w > cap:
            over.append((title, w))

    if over:
        print(f"\nFAIL: {len(over)} spoken slide(s) over {cap}-word cap:", file=sys.stderr)
        for title, w in over:
            print(f"  - {title}: {w} words", file=sys.stderr)
        return 1
    print(f"\nPASS: all {len(frames)} spoken slides at or under {cap} words.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

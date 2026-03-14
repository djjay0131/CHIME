#!/usr/bin/env python3
"""
Patch experiment parameter files to use a different CN count.
Paper default is 10 CNs (requires 11 nodes). For 10-node clusters, use 9 CNs.

Usage:
  python3 patch-cn-count.py 9    # Patch all fig params to 9 CNs
  python3 patch-cn-count.py 10   # Restore to paper default (10 CNs)

Uses regex replacement to preserve original file formatting.
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PARAMS_DIR = REPO_ROOT / "exp" / "params"

TARGET_FILES = ["fig_12.json", "fig_14.json", "fig_15a.json", "fig_15b.json"]

# Match [<number>, <number>] patterns in "client_num" context
# This catches both compact [10, 32] and expanded [[10, 4], [10, 8], ...] formats
PAIR_PATTERN = re.compile(r'\[(\d+),\s*(\d+)\s*\]')


def patch_file(path: Path, old_cn: int, new_cn: int):
    text = path.read_text()

    # Only replace inside the "client_num" section
    # Find the client_num key and its value
    cn_match = re.search(r'"client_num"\s*:', text)
    if not cn_match:
        print(f"  {path.name}: no client_num found, skipping")
        return

    start = cn_match.start()
    changed = 0

    def replacer(m):
        nonlocal changed
        cn, threads = int(m.group(1)), int(m.group(2))
        if cn == old_cn:
            changed += 1
            # Preserve original spacing by replacing only the CN number
            original = m.group(0)
            return original.replace(str(old_cn), str(new_cn), 1)
        return m.group(0)

    # Replace only after "client_num":
    before = text[:start]
    after = PAIR_PATTERN.sub(replacer, text[start:])
    path.write_text(before + after)
    print(f"  {path.name}: {changed} pairs patched ({old_cn} -> {new_cn})")


def detect_current_cn(path: Path):
    """Detect the current CN count from the first [X, Y] pair in client_num."""
    text = path.read_text()
    cn_match = re.search(r'"client_num"\s*:', text)
    if not cn_match:
        return None
    after = text[cn_match.end():]
    pair = PAIR_PATTERN.search(after)
    return int(pair.group(1)) if pair else None


def main():
    if len(sys.argv) != 2:
        print("Usage: patch-cn-count.py <CN_count>")
        print("  e.g., patch-cn-count.py 9   (for 10-node cluster: 9 CN + 1 MN)")
        print("  e.g., patch-cn-count.py 10  (paper default: 10 CN + 1 MN = 11 nodes)")
        sys.exit(1)

    new_cn = int(sys.argv[1])
    print(f"Patching experiment params to CN_num={new_cn} (total nodes = {new_cn + 1})")

    for fname in TARGET_FILES:
        path = PARAMS_DIR / fname
        if not path.exists():
            print(f"  {fname}: not found, skipping")
            continue
        old_cn = detect_current_cn(path)
        if old_cn is None:
            print(f"  {fname}: could not detect current CN count")
            continue
        if old_cn == new_cn:
            print(f"  {fname}: already at CN_num={new_cn}")
            continue
        patch_file(path, old_cn, new_cn)

    print(f"\nDone. Experiments will now use {new_cn} CNs + 1 MN = {new_cn + 1} nodes.")
    print(f"Make sure cluster_ips in common.json has >= {new_cn + 1} entries.")


if __name__ == "__main__":
    main()

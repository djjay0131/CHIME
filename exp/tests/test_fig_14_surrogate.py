"""Tests for exp/fig_14_surrogate.py stats parsing (AC-13 data shape)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fig_14_surrogate import parse_stats


def test_parse_stats_extracts_numeric_keys() -> None:
    stderr = """Starting benchmark...
[stats] internal_cache_bytes = 12582912
[stats] leaf_cache_bytes = 4194304
[stats] total_cache_bytes = 16777216
Done.
"""
    result = parse_stats(stderr)
    assert result["internal_cache_bytes"] == 12582912
    assert result["leaf_cache_bytes"] == 4194304
    assert result["total_cache_bytes"] == 16777216
    print("PASS: test_parse_stats_extracts_numeric_keys")


def test_parse_stats_ignores_non_stats_lines() -> None:
    stderr = "[stats] foo = 42\nnoise line\nanother = 99\n[stats] bar = 100"
    result = parse_stats(stderr)
    assert result == {"foo": 42, "bar": 100}
    print("PASS: test_parse_stats_ignores_non_stats_lines")


def test_parse_stats_handles_extra_whitespace() -> None:
    stderr = "[stats]   spaced = 5   \n[stats] tight=7\n"
    result = parse_stats(stderr)
    assert result == {"spaced": 5, "tight": 7}
    print("PASS: test_parse_stats_handles_extra_whitespace")


def test_parse_stats_empty_input_returns_empty_dict() -> None:
    assert parse_stats("") == {}
    assert parse_stats("no stats here") == {}
    print("PASS: test_parse_stats_empty_input_returns_empty_dict")


def test_parse_stats_non_numeric_value_skipped() -> None:
    # The regex requires \d+, so non-numeric values don't match
    stderr = "[stats] notnumeric = oops\n[stats] valid = 123\n"
    result = parse_stats(stderr)
    assert result == {"valid": 123}
    print("PASS: test_parse_stats_non_numeric_value_skipped")


def main() -> int:
    tests = [
        test_parse_stats_extracts_numeric_keys,
        test_parse_stats_ignores_non_stats_lines,
        test_parse_stats_handles_extra_whitespace,
        test_parse_stats_empty_input_returns_empty_dict,
        test_parse_stats_non_numeric_value_skipped,
    ]
    failures = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            print(f"FAIL: {t.__name__}: {e}")
            failures += 1
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

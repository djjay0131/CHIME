"""Tests for exp/plot_fig_12_three_way.py load_series logic.

Intentionally does NOT test the matplotlib rendering — that requires the
`matplotlib` package and produces PDFs that are hard to assert on.
The rendering is a thin wrapper around load_series and ax.plot.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from plot_fig_12_three_way import load_series


def _write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data))


def test_load_series_tpt_lat_schema() -> None:
    """The primary schema: {method: {"tpt": [...], "lat": [...]}}."""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "r.json"
        _write(p, {"CHIME": {"tpt": [1.0, 2.0], "lat": [5, 6]}})
        series = load_series(p)
        assert series == {"CHIME": [(1.0, 5), (2.0, 6)]}
    print("PASS: test_load_series_tpt_lat_schema")


def test_load_series_list_of_pairs_schema() -> None:
    """Alternate schema: {method: [[tpt, lat], [tpt, lat]]}."""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "r.json"
        _write(p, {"CHIME": [[1.0, 5], [2.0, 6]]})
        series = load_series(p)
        assert series == {"CHIME": [(1.0, 5), (2.0, 6)]}
    print("PASS: test_load_series_list_of_pairs_schema")


def test_load_series_missing_file_returns_empty() -> None:
    """Graceful handling of missing file — means 'no data for this series'."""
    result = load_series(Path("/nonexistent/path/foo.json"))
    assert result == {}
    print("PASS: test_load_series_missing_file_returns_empty")


def test_load_series_multiple_methods() -> None:
    """Multiple methods in a single JSON — preserves all."""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "r.json"
        _write(p, {
            "CHIME": {"tpt": [1.0], "lat": [5]},
            "Sherman": {"tpt": [0.5], "lat": [10]},
            "SMART": {"tpt": [0.8], "lat": [7]},
        })
        series = load_series(p)
        assert set(series.keys()) == {"CHIME", "Sherman", "SMART"}
        assert series["Sherman"] == [(0.5, 10)]
    print("PASS: test_load_series_multiple_methods")


def test_load_series_mismatched_tpt_lat_lengths() -> None:
    """If tpt and lat have different lengths, zip truncates silently — acceptable."""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "r.json"
        _write(p, {"CHIME": {"tpt": [1.0, 2.0, 3.0], "lat": [5]}})
        series = load_series(p)
        # Only the one pair that both have survives
        assert series == {"CHIME": [(1.0, 5)]}
    print("PASS: test_load_series_mismatched_tpt_lat_lengths")


def main() -> int:
    tests = [
        test_load_series_tpt_lat_schema,
        test_load_series_list_of_pairs_schema,
        test_load_series_missing_file_returns_empty,
        test_load_series_multiple_methods,
        test_load_series_mismatched_tpt_lat_lengths,
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

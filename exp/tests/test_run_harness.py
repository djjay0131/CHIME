"""Self-contained tests for exp/run_harness.py (no pytest dependency).

Run with: python3 -m exp.tests.test_run_harness
Or: (cd /path/to/CHIME && python3 exp/tests/test_run_harness.py)

Covers AC-14: run_harness must capture debug artifacts on failure.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


HARNESS = Path(__file__).resolve().parent.parent / "run_harness.py"
REPO_ROOT = HARNESS.parent.parent


def _invoke(args: list[str], debug_root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HARNESS), "--debug-root", str(debug_root),
         "--source-dir", str(REPO_ROOT), *args],
        capture_output=True, text=True,
    )


def _newest(debug_root: Path) -> Path:
    dirs = [p for p in debug_root.iterdir() if p.is_dir()]
    assert dirs, "no artifact dir created"
    return max(dirs, key=lambda p: p.stat().st_mtime)


def test_success_leaves_ok_marker() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        result = _invoke(["--workload", "smoke", "--", "/usr/bin/true"], root)
        assert result.returncode == 0, f"expected 0, got {result.returncode}"
        d = _newest(root)
        assert (d / "OK").exists(), f"OK marker missing in {d}"
        assert not (d / "FAILED").exists(), "FAILED marker should not be present"
        assert not (d / "commit.txt").exists(), (
            "On success we don't snapshot build artifacts (keeps clean)"
        )
    print("PASS: test_success_leaves_ok_marker")


def test_nonzero_exit_captures_artifacts() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        result = _invoke(["--workload", "boom", "--", "/usr/bin/false"], root)
        assert result.returncode != 0, "expected non-zero exit"
        d = _newest(root)
        assert (d / "FAILED").exists(), f"FAILED marker missing in {d}"
        assert (d / "commit.txt").exists(), "commit.txt missing"
        assert (d / "host.txt").exists(), "host.txt missing"
        assert (d / "stderr.log").exists(), "stderr.log missing"
        # commit.txt should contain a SHA (40 hex chars)
        sha = (d / "commit.txt").read_text().strip()
        assert len(sha) == 40, f"bad SHA: {sha!r}"
    print("PASS: test_nonzero_exit_captures_artifacts")


def test_segfault_in_stderr_triggers_capture() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        # Use a shell command that writes the segfault sentinel without actually
        # coring. The harness should still trigger capture based on stderr text.
        cmd = [
            "/bin/bash", "-c",
            "echo 'Segmentation fault (core dumped)' 1>&2; exit 0",
        ]
        result = _invoke(["--workload", "segv", "--", *cmd], root)
        # The wrapper exits with whatever the child returns (0 here), but it
        # should still capture because the stderr sentinel matched.
        d = _newest(root)
        assert (d / "FAILED").exists(), (
            "Segfault sentinel in stderr must trigger FAILED capture even on exit 0"
        )
    print("PASS: test_segfault_in_stderr_triggers_capture")


def test_assertion_in_stderr_triggers_capture() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cmd = [
            "/bin/bash", "-c",
            "echo 'Assertion k >= fence_keys.lowest failed' 1>&2; exit 134",
        ]
        result = _invoke(["--workload", "assert", "--", *cmd], root)
        assert result.returncode == 134
        d = _newest(root)
        assert (d / "FAILED").exists()
    print("PASS: test_assertion_in_stderr_triggers_capture")


def test_timeout_kills_and_captures() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        cmd = ["/bin/sleep", "30"]
        result = _invoke(
            ["--workload", "stuck", "--timeout", "2", "--", *cmd], root
        )
        assert result.returncode != 0, "timeout should produce non-zero exit"
        d = _newest(root)
        assert (d / "FAILED").exists()
        stderr = (d / "stderr.log").read_text()
        assert "TIMEOUT after" in stderr, f"timeout note missing from stderr: {stderr!r}"
    print("PASS: test_timeout_kills_and_captures")


def test_no_command_errors() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        result = _invoke(["--workload", "nothing"], root)
        assert result.returncode != 0, "expected argparse error on missing cmd"
        assert "Provide the command" in result.stderr, result.stderr
    print("PASS: test_no_command_errors")


def test_find_core_dump_returns_newest() -> None:
    """find_core_dump picks the most recently modified core file."""
    import time
    sys.path.insert(0, str(HARNESS.parent))
    from run_harness import find_core_dump

    with tempfile.TemporaryDirectory() as td:
        cwd = Path(td)
        started = time.time()
        time.sleep(0.05)
        old = cwd / "core.old"
        old.write_text("old")
        # Force old core to be BEFORE started
        old_time = started - 10
        import os
        os.utime(old, (old_time, old_time))

        # A new core created after started
        time.sleep(0.05)
        new = cwd / "core.new"
        new.write_text("new")

        result = find_core_dump(cwd, started)
        assert result == new, f"Expected {new}, got {result}"

        # When no core exists after started, returns None
        assert find_core_dump(Path("/tmp/definitely/not/a/dir/xyzzy"), started) is None
    print("PASS: test_find_core_dump_returns_newest")


def test_debug_root_auto_created_when_missing() -> None:
    """Nested missing debug_root is created by the harness."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "does" / "not" / "exist" / "yet"
        assert not root.exists()
        result = _invoke(
            ["--workload", "nest", "--", "/usr/bin/true"], root
        )
        assert result.returncode == 0
        assert root.exists(), f"debug root should have been created at {root}"
        d = _newest(root)
        assert (d / "OK").exists()
    print("PASS: test_debug_root_auto_created_when_missing")


def main() -> int:
    tests = [
        test_success_leaves_ok_marker,
        test_nonzero_exit_captures_artifacts,
        test_segfault_in_stderr_triggers_capture,
        test_assertion_in_stderr_triggers_capture,
        test_timeout_kills_and_captures,
        test_no_command_errors,
        test_find_core_dump_returns_newest,
        test_debug_root_auto_created_when_missing,
    ]
    failures = 0
    for t in tests:
        try:
            t()
        except AssertionError as e:
            print(f"FAIL: {t.__name__}: {e}")
            failures += 1
        except Exception as e:  # pragma: no cover — debugging aid
            print(f"ERROR: {t.__name__}: {type(e).__name__}: {e}")
            failures += 1
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

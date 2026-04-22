"""Run-harness wrapper for ycsb_test with debug-artifact capture (AC-14).

Wraps any ycsb_test invocation. On non-zero exit, segfault, or assertion
failure, captures: core dump, stderr, git rev-parse, CMakeCache, Common.h,
hugepage/memcached state. Artifacts land in debug/<timestamp>-<workload>/.

Usage (local or on master node over SSH):
    python3 run_harness.py --workload c --threads 8 --build-dir build-cxl \\
        -- ./ycsb_test 1 8 1 randint c

Design notes:
  - Runs the wrapped command under `ulimit -c unlimited` so the kernel
    writes cores next to the binary (or to `core_pattern` if set).
  - Streams stdout/stderr to files AND to the console so operators can
    watch progress in a tmux pane.
  - On failure, snapshots are taken BEFORE returning — operator can
    decide next steps with full context.
"""

import argparse
import datetime
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path


def capture_snapshot(debug_dir: Path, build_dir: Path, source_dir: Path) -> None:
    """Copy the artifacts that explain 'what was this build?' into debug_dir."""
    debug_dir.mkdir(parents=True, exist_ok=True)

    git_rev = subprocess.run(
        ["git", "-C", str(source_dir), "rev-parse", "HEAD"],
        capture_output=True, text=True,
    ).stdout.strip()
    (debug_dir / "commit.txt").write_text(git_rev + "\n")

    cmake_cache = build_dir / "CMakeCache.txt"
    if cmake_cache.exists():
        shutil.copy(cmake_cache, debug_dir / "CMakeCache.txt")

    common_h = source_dir / "include" / "Common.h"
    if common_h.exists():
        shutil.copy(common_h, debug_dir / "Common.h")

    host_lines = []
    try:
        hp = Path("/proc/sys/vm/nr_hugepages").read_text().strip()
        host_lines.append(f"nr_hugepages={hp}")
    except (FileNotFoundError, PermissionError):
        host_lines.append("nr_hugepages=unavailable")
    try:
        out = subprocess.run(
            ["pgrep", "-a", "memcached"], capture_output=True, text=True, timeout=5,
        )
        host_lines.append(f"memcached={out.stdout.strip() or 'not running'}")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        host_lines.append("memcached=check-failed")
    host_lines.append(f"hostname={os.uname().nodename}")
    host_lines.append(f"uname={' '.join(os.uname())}")
    (debug_dir / "host.txt").write_text("\n".join(host_lines) + "\n")


def find_core_dump(cwd: Path, started_at: float) -> Path | None:
    """Return the newest core file created after `started_at`, if any."""
    candidates = list(cwd.glob("core*")) + list(Path("/tmp").glob("core.*"))
    candidates = [p for p in candidates if p.stat().st_mtime >= started_at - 1]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def run_with_capture(
    cmd: list[str],
    workload: str,
    build_dir: Path,
    source_dir: Path,
    debug_root: Path,
    timeout: float | None = None,
) -> int:
    """Run cmd, streaming output. On failure, snapshot artifacts. Returns exit code."""
    timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    debug_dir = debug_root / f"{timestamp}-{workload}"
    debug_dir.mkdir(parents=True, exist_ok=True)

    stderr_path = debug_dir / "stderr.log"
    stdout_path = debug_dir / "stdout.log"

    started_at = time.time()
    # preexec_fn raises core-dump limit for the child process
    try:
        import resource
        def _preexec():
            resource.setrlimit(resource.RLIMIT_CORE, (resource.RLIM_INFINITY,
                                                     resource.RLIM_INFINITY))
    except ImportError:
        _preexec = None  # pragma: no cover

    with stderr_path.open("w") as ef, stdout_path.open("w") as of:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=_preexec,
            cwd=build_dir if build_dir.exists() else None,
        )
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.send_signal(signal.SIGTERM)
            try:
                stdout, stderr = proc.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout, stderr = proc.communicate()
            stderr = (stderr or "") + f"\n[harness] TIMEOUT after {timeout}s\n"
        of.write(stdout or "")
        ef.write(stderr or "")
        sys.stdout.write(stdout or "")
        sys.stderr.write(stderr or "")

    exit_code = proc.returncode

    failure = (
        exit_code != 0
        or "Segmentation fault" in (stderr or "")
        or "Assertion" in (stderr or "")
        or "Aborted" in (stderr or "")
    )

    if failure:
        capture_snapshot(debug_dir, build_dir, source_dir)
        core = find_core_dump(build_dir, started_at)
        if core is not None:
            shutil.copy(core, debug_dir / "core")
        (debug_dir / "FAILED").write_text(
            f"exit_code={exit_code}\ncmd={' '.join(cmd)}\n"
        )
        print(
            f"[harness] FAILURE captured → {debug_dir}", file=sys.stderr,
        )
    else:
        # Keep stdout/stderr even on success so operators can diff runs
        (debug_dir / "OK").write_text(f"exit_code={exit_code}\n")

    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workload", required=True, help="e.g. a, b, c, LOAD")
    parser.add_argument(
        "--build-dir", type=Path, default=Path("build"),
        help="Where the ycsb_test binary lives (for CMakeCache capture)",
    )
    parser.add_argument(
        "--source-dir", type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repo root (for git rev-parse and Common.h)",
    )
    parser.add_argument(
        "--debug-root", type=Path, default=Path("debug"),
        help="Where to drop <timestamp>-<workload>/ artifacts",
    )
    parser.add_argument(
        "--timeout", type=float, default=None,
        help="Hard kill after N seconds (unset = no timeout)",
    )
    parser.add_argument(
        "cmd", nargs=argparse.REMAINDER,
        help="Command after --; e.g. -- ./ycsb_test 1 8 1 randint c",
    )
    args = parser.parse_args()

    cmd = args.cmd
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        parser.error("Provide the command to run after '--'")

    return run_with_capture(
        cmd=cmd,
        workload=args.workload,
        build_dir=args.build_dir,
        source_dir=args.source_dir,
        debug_root=args.debug_root,
        timeout=args.timeout,
    )


if __name__ == "__main__":
    sys.exit(main())

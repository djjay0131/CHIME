"""Fig 14 surrogate: single-point cache-consumption measurement at 60M keys (AC-13).

The full fig_14 sweeps dataset sizes 40M–120M in 20M increments, which
needs workload files we haven't generated yet and 3+ cluster nodes. The
surrogate takes a single measurement at 60M keys on whatever nodes we
have, for both CXL and single-node RDMA transports, to tell the cache-
efficiency story (CHIME's headline claim) without the full sweep.

Output schema: exp/results/fig_14_surrogate.json
  {
    "method": {
      "transport": {
        "dataset_keys": 60000000,
        "internal_cache_bytes": 12345678,
        "leaf_cache_bytes": 0,
        "total_cache_bytes": 12345678,
        "measured_at": "ISO-8601",
        "commit": "SHA"
      }, ...
    }
  }

The surrogate driver runs ycsb_test in a special "warm-up-and-report"
mode where the YCSB workload is loaded, the tree is populated, and
Tree::statistics() is called to dump cache sizes via STATS_PROMPT lines
on stderr. We parse those here.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path


STATS_PATTERN = re.compile(
    r"\[stats\]\s+(?P<key>\w+)\s*=\s*(?P<value>\d+)"
)


def parse_stats(stderr: str) -> dict[str, int]:
    """Extract '[stats] key = N' lines from ycsb_test stderr."""
    out: dict[str, int] = {}
    for line in stderr.splitlines():
        m = STATS_PATTERN.search(line)
        if m:
            out[m.group("key")] = int(m.group("value"))
    return out


def git_commit(source_dir: Path) -> str:
    """Return current git SHA for the source tree."""
    try:
        return subprocess.run(
            ["git", "-C", str(source_dir), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=False,
        ).stdout.strip() or "unknown"
    except FileNotFoundError:
        return "unknown"  # pragma: no cover


def run_one(
    method: str,
    transport: str,
    ycsb_test: Path,
    workload_path: Path,
    dataset_keys: int,
    threads: int = 8,
    timeout: float = 1800.0,
) -> dict:
    """Run one (method, transport) measurement. Returns a result dict."""
    if not ycsb_test.exists():
        raise FileNotFoundError(f"ycsb_test not found at {ycsb_test}")
    if not workload_path.exists():
        raise FileNotFoundError(f"workload file not found at {workload_path}")

    cmd = [str(ycsb_test), "1", str(threads), "1", "randint", "c",
           "--stats-only", "--load", str(workload_path)]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    stats = parse_stats(proc.stderr)
    return {
        "dataset_keys": dataset_keys,
        "internal_cache_bytes": stats.get("internal_cache_bytes", 0),
        "leaf_cache_bytes": stats.get("leaf_cache_bytes", 0),
        "total_cache_bytes": stats.get("total_cache_bytes",
                                       stats.get("internal_cache_bytes", 0)
                                       + stats.get("leaf_cache_bytes", 0)),
        "measured_at": datetime.datetime.utcnow().isoformat() + "Z",
        "commit": git_commit(ycsb_test.resolve().parent.parent),
        "method": method,
        "transport": transport,
        "exit_code": proc.returncode,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method", required=True,
                        choices=["CHIME", "Sherman", "SMART", "ROLEX"])
    parser.add_argument("--transport", required=True,
                        choices=["cxl", "rdma_single"])
    parser.add_argument("--ycsb-test", type=Path, required=True)
    parser.add_argument("--workload", type=Path, required=True,
                        help="Path to 60M-key YCSB workload file")
    parser.add_argument("--dataset-keys", type=int, default=60_000_000)
    parser.add_argument("--output", type=Path,
                        default=Path("exp/results/fig_14_surrogate.json"))
    parser.add_argument("--threads", type=int, default=8)
    args = parser.parse_args()

    result = run_one(
        method=args.method, transport=args.transport,
        ycsb_test=args.ycsb_test, workload_path=args.workload,
        dataset_keys=args.dataset_keys, threads=args.threads,
    )

    # Merge into existing JSON if present
    data: dict = {}
    if args.output.exists():
        data = json.loads(args.output.read_text())
    data.setdefault(args.method, {})[args.transport] = result
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2) + "\n")
    print(f"[fig_14_surrogate] wrote {args.output} for "
          f"{args.method}/{args.transport}: total_cache_bytes="
          f"{result['total_cache_bytes']}")
    return 0 if result["exit_code"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

"""Render fig_12 throughput-thread curve from the Apr 27 r650 reservation."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main() -> None:
    base = Path(__file__).parent / "results" / "rdma-2node-04271959"
    points = []
    for fn in ("fig_12_c_sweep.jsonl", "fig_12_de_sweep.jsonl"):
        path = base / fn
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                points.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    # Add the manual 8-thread C point
    points.append({"workload": "c", "threads": 8, "peak_mops": 1.12})

    series = {}
    for p in points:
        series.setdefault(p["workload"], []).append((p["threads"], p["peak_mops"]))
    for w in series:
        series[w].sort()

    fig, ax = plt.subplots(figsize=(6, 4))
    styles = {
        "c": dict(marker="o", color="#1f77b4", label="YCSB C (read-only)"),
        "d": dict(marker="s", color="#ff7f0e", label="YCSB D (read-mostly)"),
        "e": dict(marker="^", color="#2ca02c", label="YCSB E (range scan)"),
    }
    for w, pts in sorted(series.items()):
        xs = [t for t, _ in pts]
        ys = [m for _, m in pts]
        style = styles.get(w, dict(marker="x", label=w))
        ax.plot(xs, ys, linewidth=1.5, markersize=6, **style)

    ax.set_xlabel("Threads per CN")
    ax.set_ylabel("Peak Throughput (Mops/s)")
    ax.set_xscale("log", base=2)
    ax.set_xticks([4, 8, 16, 32, 64])
    ax.set_xticklabels(["4", "8", "16", "32", "64"])
    ax.grid(alpha=0.3)
    ax.set_title("CHIME on r650 Clemson, 1 CN + 1 MN, Apr 27 2026")
    ax.legend()
    fig.tight_layout()

    out = Path(__file__).parent / ".." / "report" / "figures" / "fig12-apr27-cde.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, bbox_inches="tight")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

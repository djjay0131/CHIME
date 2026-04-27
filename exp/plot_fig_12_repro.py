"""Render reproduction-of-fig_12 panels matching the CHIME paper's axis layout.

Reads our Part One results (X_data/Y_data/BACKUP_data schema from exp/fig_12.py)
and emits a multi-panel PDF with throughput on x-axis and P99 latency on y-axis,
in Mops/s and microseconds (paper-matching units), so the result can sit next to
the cropped Figure 12 from the paper for AC-19.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


WORKLOAD_LABELS = {
    "c": "YCSB C", "d": "YCSB D", "e": "YCSB E",
    "a": "YCSB A", "b": "YCSB B", "load": "YCSB LOAD",
}

METHOD_STYLES = {
    "CHIME":    dict(marker="o", color="#1f77b4"),
    "SMART":    dict(marker="s", color="#ff7f0e"),
    "Sherman":  dict(marker="^", color="#2ca02c"),
    "ROLEX":    dict(marker="v", color="#d62728"),
    "SMART-SC": dict(marker="d", color="#9467bd"),
    "SMART-Opt": dict(marker="d", color="#9467bd"),
}


def load_series(path: Path) -> dict[str, tuple[list[float], list[float]]]:
    data = json.loads(path.read_text())
    out = {}
    for m in data.get("methods", []):
        x = data.get("X_data", {}).get(m, [])
        y = data.get("Y_data", {}).get(m, [])
        out[m] = (x, y)
    return out


def render(workloads: list[str], inputs: list[Path], output: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")  # pragma: no cover
    import matplotlib.pyplot as plt

    n = len(workloads)
    fig, axes = plt.subplots(1, n, figsize=(4.0 * n, 3.4))
    if n == 1:
        axes = [axes]

    for ax, wk, inp in zip(axes, workloads, inputs):
        series = load_series(inp)
        for method, (xs, ys) in series.items():
            style = METHOD_STYLES.get(method, dict(marker="x", color="gray"))
            ax.plot(xs, ys, linewidth=1.2, markersize=4, label=method, **style)
        ax.set_xlabel("Throughput (Mops/s)")
        ax.set_ylabel("P99 Latency ($\\mu$s)")
        ax.set_title(f"({chr(ord('a') + workloads.index(wk))}) {WORKLOAD_LABELS[wk]}")
        ax.grid(alpha=0.3)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=len(labels),
               bbox_to_anchor=(0.5, -0.02), frameon=False)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight")
    print(f"wrote {output}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--workload", action="append", required=True,
                   help="Workload letter (c/d/e/a/b/load), repeat for multi-panel.")
    p.add_argument("--input", action="append", required=True,
                   help="Input JSON file, paired with --workload.")
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    if len(args.workload) != len(args.input):
        raise SystemExit("--workload and --input must be paired")
    render(args.workload, [Path(p) for p in args.input], args.output)


if __name__ == "__main__":
    main()

"""Plot helper: three-way throughput-latency comparison for fig_12 (AC-4).

Consumes three JSON sources and emits one PDF per workload:
  - Multi-node RDMA: reuses Part One results in exp/results/
  - Single-node RDMA: tomorrow's 1 CN + 1 MN run, exp/results/rdma_single/
  - Single-node CXL: tomorrow's NUMA-emulation run, exp/results/cxl/

Usage:
  python3 plot_fig_12_three_way.py \\
      --workload c \\
      --multi-node exp/results/fig_12_c.json \\
      --single-node-rdma exp/results/rdma_single/fig_12_c.json \\
      --cxl exp/results/cxl/fig_12_c.json \\
      --output report/figures/fig_12_c_three_way.pdf \\
      --caption-cn-count 5 --caption-date 2026-04-07

Each JSON is expected to map method name -> list of (throughput, latency) points.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_series(path: Path) -> dict[str, list[tuple[float, float]]]:
    """Return {method_name: [(throughput_kops, p50_latency_us), ...]}."""
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    series: dict[str, list[tuple[float, float]]] = {}
    for method, payload in data.items():
        if isinstance(payload, dict) and "tpt" in payload and "lat" in payload:
            tpts = payload["tpt"]
            lats = payload["lat"]
            series[method] = list(zip(tpts, lats))
        elif isinstance(payload, list):
            # Already a list of [tpt, lat] pairs
            series[method] = [tuple(p) for p in payload]
    return series


def render(
    workload: str,
    multi_node: dict[str, list[tuple[float, float]]],
    single_node_rdma: dict[str, list[tuple[float, float]]],
    cxl: dict[str, list[tuple[float, float]]],
    output: Path,
    caption_cn_count: int | None,
    caption_date: str | None,
) -> None:
    """Emit a PDF with three series overlaid. No magnitude claims in caption —
    we only annotate provenance."""
    import matplotlib
    matplotlib.use("Agg")  # pragma: no cover — headless only
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6, 4))
    styles = {
        "multi_node": {"linestyle": "-", "marker": "o", "alpha": 0.9,
                       "label_suffix": f" (multi-node RDMA)"},
        "single_node_rdma": {"linestyle": "--", "marker": "s", "alpha": 0.85,
                             "label_suffix": " (1-node RDMA)"},
        "cxl": {"linestyle": "-.", "marker": "^", "alpha": 0.95,
                "label_suffix": " (CXL)"},
    }
    for series, style_key in [
        (multi_node, "multi_node"),
        (single_node_rdma, "single_node_rdma"),
        (cxl, "cxl"),
    ]:
        s = styles[style_key]
        for method, points in series.items():
            if not points:
                continue
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            ax.plot(xs, ys, label=f"{method}{s['label_suffix']}",
                    linestyle=s["linestyle"], marker=s["marker"],
                    alpha=s["alpha"])

    ax.set_xlabel("Throughput (Mops)")
    ax.set_ylabel("Latency (µs)")
    ax.set_title(f"YCSB {workload.upper()} — transport comparison")
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend(fontsize=7, loc="best")

    caption_parts = [f"YCSB {workload.upper()}"]
    if caption_cn_count is not None:
        caption_parts.append(f"multi-node: {caption_cn_count} CN")
    if caption_date is not None:
        caption_parts.append(f"Part One runs: {caption_date}")
    caption = " | ".join(caption_parts)
    fig.text(0.5, -0.02, caption, ha="center", fontsize=7, style="italic")

    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)
    print(f"[plot_fig_12_three_way] wrote {output}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workload", required=True)
    parser.add_argument("--multi-node", type=Path, required=True)
    parser.add_argument("--single-node-rdma", type=Path, required=True)
    parser.add_argument("--cxl", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--caption-cn-count", type=int, default=None)
    parser.add_argument("--caption-date", default=None)
    args = parser.parse_args()

    multi = load_series(args.multi_node)
    single = load_series(args.single_node_rdma)
    cxl = load_series(args.cxl)

    if not (multi or single or cxl):
        print("[plot_fig_12_three_way] ERROR: no input data at any of the "
              "three JSON paths", file=sys.stderr)
        return 1

    render(
        workload=args.workload,
        multi_node=multi, single_node_rdma=single, cxl=cxl,
        output=args.output,
        caption_cn_count=args.caption_cn_count,
        caption_date=args.caption_date,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

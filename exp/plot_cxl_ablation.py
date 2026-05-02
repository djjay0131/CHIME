"""Render CXL ablation: cumulative add of CHIME features starting from Sherman-CXL."""
from __future__ import annotations

import json
from pathlib import Path
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def main() -> None:
    base = Path(__file__).parent / "results" / "may2-competitors"
    out_dir = Path(__file__).parent / ".." / "report" / "figures"

    points = load_jsonl(base / "cxl_ablation.jsonl")

    variants = ["sherman", "hopscotch", "vacancy", "metadata", "sibling", "chime"]
    labels = ["Sherman", "+Hopscotch", "+Vacancy", "+Metadata", "+Sibling", "+Speculative\n(full CHIME)"]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    workloads = ["c", "d"]
    titles = ["YCSB C @ 16 threads", "YCSB C @ 32 threads"]
    threads_for_panel = [16, 32]

    for ax, w, T, title in zip(axes, ["c", "c"], threads_for_panel, titles):
        ys = []
        for v in variants:
            matches = [p for p in points
                       if p.get("variant") == v
                       and p.get("workload") == w
                       and p.get("threads") == T
                       and p.get("peak_mops", 0) > 0]
            ys.append(matches[0]["peak_mops"] if matches else 0)
        x = list(range(len(variants)))
        ax.bar(x, ys, color=["#7f7f7f", "#1f77b4", "#ff7f0e", "#2ca02c", "#9467bd", "#d62728"])
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=9, rotation=15, ha="right")
        ax.set_ylabel("Peak Throughput (Mops/s)", fontsize=11)
        ax.set_title(title, fontsize=11)
        ax.grid(axis="y", alpha=0.3)
        for xi, y in zip(x, ys):
            if y > 0:
                ax.annotate(f"{y:.2f}", (xi, y),
                            ha="center", va="bottom", fontsize=8)

    fig.suptitle("CXL Ablation: Cumulative Sherman-CXL → CHIME-CXL on r650 Clemson 1 CN + 1 MN",
                 fontsize=11)
    fig.tight_layout()
    out = out_dir / "fig15a-cxl-ablation.pdf"
    fig.savefig(out, bbox_inches="tight")
    print(f"wrote {out}")
    plt.close(fig)


if __name__ == "__main__":
    main()

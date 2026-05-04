"""Render the CXL fig_15a ablation across full thread sweeps for C, D, E.

Headline: speculative read is net-negative on CXL across all thread counts and
workloads — most dramatic on range-scan E (29-42% slower than sibling), still
present on read-heavy C/D where chime can be slower than even the no-features
sherman baseline at low thread counts.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load_jsonl(p: Path) -> list[dict]:
    out = []
    if not p.exists():
        return out
    for line in p.read_text().splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def main() -> None:
    base = Path(__file__).parent / "results" / "may2-24h"
    out_dir = Path(__file__).parent / ".." / "report" / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "c": base / "p42_comprehensive_C.jsonl",
        "d": base / "p43_comprehensive_D.jsonl",
        "e": base / "p44_comprehensive_E.jsonl",
    }

    variants = ["sherman", "hopscotch", "vacancy", "metadata", "sibling", "chime"]
    labels = ["Sherman", "+Hopscotch", "+Vacancy", "+Metadata", "+Sibling", "+Speculative\n(full CHIME)"]
    colors = ["#7f7f7f", "#1f77b4", "#ff7f0e", "#2ca02c", "#9467bd", "#d62728"]
    markers = ["x", "o", "s", "^", "D", "*"]

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.6))
    titles = {"c": "YCSB C (read-only)", "d": "YCSB D (95% R / 5% I)", "e": "YCSB E (range scan)"}

    from statistics import mean, stdev
    for ax, w in zip(axes, ["c", "d", "e"]):
        points = load_jsonl(files[w])
        for i, v in enumerate(variants):
            grouped: dict[int, list[float]] = {}
            for p in points:
                if p.get("variant") == v and p.get("peak_mops", 0) > 0:
                    grouped.setdefault(p["threads"], []).append(p["peak_mops"])
            if not grouped:
                continue
            xs = sorted(grouped)
            ys = [mean(grouped[t]) for t in xs]
            yerr = [stdev(grouped[t]) if len(grouped[t]) > 1 else 0 for t in xs]
            ax.errorbar(xs, ys, yerr=yerr, label=labels[i], color=colors[i],
                        marker=markers[i], linewidth=1.5, markersize=7,
                        linestyle="-" if v != "chime" else "--",
                        capsize=3, capthick=1.0)
        ax.set_xlabel("Threads", fontsize=11)
        ax.set_ylabel("Peak Throughput (Mops/s)", fontsize=11)
        ax.set_xscale("log", base=2)
        ax.set_title(titles[w], fontsize=11)
        ax.grid(alpha=0.3)
        if w == "c":
            ax.legend(loc="upper left", fontsize=8)

    fig.suptitle("CXL fig_15a Ablation: Cumulative Sherman-CXL → CHIME-CXL across thread counts (r650 Clemson, May 3, 2026)",
                 fontsize=11)
    fig.tight_layout()
    out = out_dir / "fig15a-cxl-ablation-full.pdf"
    fig.savefig(out, bbox_inches="tight")
    print(f"wrote {out}")
    plt.close(fig)


if __name__ == "__main__":
    main()

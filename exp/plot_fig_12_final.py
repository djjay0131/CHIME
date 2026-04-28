"""Render the final fig_12 throughput-thread comparison from Apr 27 r650 data.

Reads all the JSONL result files committed under exp/results/rdma-2node-04271959/
and produces:
- fig_12_final.pdf: 3-panel C/D/E throughput-thread curves
- fig_15a_final.pdf: 2-panel ablation comparison (C vs D)
- variance.pdf: error bars from variance runs
"""
from __future__ import annotations

import json
from pathlib import Path
from collections import defaultdict
from statistics import mean, stdev

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def render_throughput_curves(base: Path, out: Path) -> None:
    points = (
        load_jsonl(base / "fig_12_c_sweep.jsonl")
        + load_jsonl(base / "fig_12_de_sweep.jsonl")
        + load_jsonl(base / "fig_12_chime_extra.jsonl")
    )
    # Add the manual 8-thread C point that wasn't in any sweep file
    points.append({"workload": "c", "threads": 8, "peak_mops": 1.12})

    series: dict[str, list[tuple[int, float]]] = defaultdict(list)
    for p in points:
        if p.get("peak_mops", 0) > 0 and "workload" in p:
            series[p["workload"]].append((p["threads"], p["peak_mops"]))
    for w in series:
        # If multiple points at the same thread count, take the mean
        agg: dict[int, list[float]] = defaultdict(list)
        for t, m in series[w]:
            agg[t].append(m)
        series[w] = sorted([(t, mean(v)) for t, v in agg.items()])

    fig, ax = plt.subplots(figsize=(7, 4.5))
    styles = {
        "c": dict(marker="o", color="#1f77b4", label="YCSB C (read-only)"),
        "d": dict(marker="s", color="#ff7f0e", label="YCSB D (95% read, 5% insert)"),
        "e": dict(marker="^", color="#2ca02c", label="YCSB E (range scan)"),
    }
    for w, pts in sorted(series.items()):
        xs = [t for t, _ in pts]
        ys = [m for _, m in pts]
        ax.plot(xs, ys, linewidth=1.5, markersize=7, **styles[w])

    ax.set_xlabel("Threads per CN", fontsize=11)
    ax.set_ylabel("Peak Throughput (Mops/s)", fontsize=11)
    ax.set_xscale("log", base=2)
    ax.set_xticks([4, 8, 16, 32, 48, 64])
    ax.set_xticklabels(["4", "8", "16", "32", "48", "64"])
    ax.grid(alpha=0.3)
    ax.set_title("CHIME on r650 Clemson, 1 CN + 1 MN, ConnectX-6 Dx (April 27, 2026)",
                 fontsize=11)
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    print(f"  wrote {out}")
    plt.close(fig)


def render_variance(base: Path, out: Path) -> None:
    """Plot variance error bars from variance_v2.jsonl."""
    points_v1 = load_jsonl(base / "fig_12_variance.jsonl")
    points_v2 = load_jsonl(base / "fig_12_variance_v2.jsonl")
    all_pts = points_v1 + points_v2

    by_t: dict[int, list[float]] = defaultdict(list)
    for p in all_pts:
        if p.get("peak_mops", 0) > 0:
            by_t[p["threads"]].append(p["peak_mops"])
    if not by_t:
        return

    threads = sorted(by_t.keys())
    means = [mean(by_t[t]) for t in threads]
    mins = [min(by_t[t]) for t in threads]
    maxs = [max(by_t[t]) for t in threads]
    counts = [len(by_t[t]) for t in threads]
    err_lo = [m - lo for m, lo in zip(means, mins)]
    err_hi = [hi - m for m, hi in zip(means, maxs)]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.errorbar(threads, means, yerr=[err_lo, err_hi],
                fmt="o", capsize=5, capthick=1.5, linewidth=1.5,
                color="#1f77b4", markersize=8, label="Mean ± range")
    for t, m, n in zip(threads, means, counts):
        ax.annotate(f"n={n}", (t, m), textcoords="offset points", xytext=(7, -10),
                    fontsize=9, color="#555")

    ax.set_xlabel("Threads per CN", fontsize=11)
    ax.set_ylabel("Peak Throughput (Mops/s)", fontsize=11)
    ax.set_xscale("log", base=2)
    ax.set_xticks([16, 32, 48, 64])
    ax.set_xticklabels(["16", "32", "48", "64"])
    ax.grid(alpha=0.3)
    ax.set_title("YCSB C variance: range across replications", fontsize=11)
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    print(f"  wrote {out}")
    plt.close(fig)


def render_ablation(base: Path, out: Path) -> None:
    c_pts = load_jsonl(base / "fig_15a_sweep_v2.jsonl")
    d_pts = load_jsonl(base / "fig_15a_d_sweep.jsonl")

    variant_order = ["hopscotch", "+vacancy", "+metadata", "+sibling", "chime"]
    label_map = {
        "hopscotch": "+ Hopscotch leaves",
        "+vacancy":  "+ Vacancy lock",
        "+metadata": "+ Metadata repl.",
        "+sibling":  "+ Sibling validation",
        "chime":     "+ Speculative read\n(full CHIME)",
        "build-15a-hopscotch": "+ Hopscotch leaves",
        "build-15a-+vacancy":  "+ Vacancy lock",
        "build-15a-+metadata": "+ Metadata repl.",
        "build-15a-+sibling":  "+ Sibling validation",
        "build-15a-chime":     "+ Speculative read\n(full CHIME)",
    }
    norm = {v: v for v in variant_order}
    norm.update({f"build-15a-{v}": v for v in variant_order})

    def get(pts):
        m = {}
        for p in pts:
            v = norm.get(p["variant"])
            if v and p.get("peak_mops", 0) > 0:
                m[v] = p["peak_mops"]
        return m

    c_data = get(c_pts)
    d_data = get(d_pts)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = list(range(len(variant_order)))
    c_y = [c_data.get(v, 0) for v in variant_order]
    d_y = [d_data.get(v, 0) for v in variant_order]

    width = 0.35
    ax.bar([i - width / 2 for i in x], c_y, width, label="YCSB C @ 16 threads",
           color="#1f77b4")
    ax.bar([i + width / 2 for i in x], d_y, width, label="YCSB D @ 32 threads",
           color="#ff7f0e")

    ax.set_xticks(x)
    ax.set_xticklabels([label_map[v] for v in variant_order], fontsize=9)
    ax.set_ylabel("Peak Throughput (Mops/s)", fontsize=11)
    ax.set_title("fig_15a Cumulative Ablation: Sherman → CHIME, r650 1 CN + 1 MN",
                 fontsize=11)
    ax.grid(axis="y", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    print(f"  wrote {out}")
    plt.close(fig)


def main() -> None:
    base = Path(__file__).parent / "results" / "rdma-2node-04271959"
    out_dir = Path(__file__).parent / ".." / "report" / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Rendering throughput curves...")
    render_throughput_curves(base, out_dir / "fig12-final-cde.pdf")
    print("Rendering variance plot...")
    render_variance(base, out_dir / "fig12-variance.pdf")
    print("Rendering ablation plot...")
    render_ablation(base, out_dir / "fig15a-ablation.pdf")


if __name__ == "__main__":
    main()

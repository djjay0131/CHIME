"""Render multi-method comparison: CHIME vs SMART vs ROLEX vs Sherman across thread counts."""
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


def series_for_method(points: list[dict], workload: str) -> list[tuple[int, float]]:
    by_t: dict[int, list[float]] = defaultdict(list)
    for p in points:
        if p.get("workload") != workload:
            continue
        m = p.get("peak_mops", 0)
        if m and m > 0:
            by_t[p["threads"]].append(m)
    return sorted([(t, max(vals)) for t, vals in by_t.items()])


def main() -> None:
    base = Path(__file__).parent / "results" / "rdma-2node-04271959"
    competitor_base = Path(__file__).parent / "results" / "may2-competitors"
    out_dir = Path(__file__).parent / ".." / "report" / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)

    # CHIME points (re-use Apr 27 data — same hardware, same harness)
    chime_files = ["fig_12_c_sweep.jsonl", "fig_12_chime_extra.jsonl",
                   "fig_12_de_sweep.jsonl"]
    chime_points = []
    for f in chime_files:
        for d in load_jsonl(base / f):
            d.setdefault("method", "CHIME")
            chime_points.append(d)
    # Add manual 8-thread C
    chime_points.append({"method": "CHIME", "workload": "c", "threads": 8, "peak_mops": 1.12})

    method_data = {"CHIME": chime_points}
    for method in ("SMART", "ROLEX", "Sherman"):
        accum = []
        for w in "cde":
            f = competitor_base / f"{method.lower()}_{w}_sweep.jsonl"
            for d in load_jsonl(f):
                d.setdefault("method", method)
                accum.append(d)
        method_data[method] = accum

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    workloads = ["c", "d", "e"]
    titles = ["YCSB C (read-only)", "YCSB D (95% read, 5% insert)",
              "YCSB E (range scan)"]
    styles = {
        "CHIME":   {"color": "#d62728", "marker": "o", "linestyle": "-",  "lw": 2.0, "ms": 7},
        "SMART":   {"color": "#1f77b4", "marker": "s", "linestyle": "--", "lw": 1.5, "ms": 6},
        "ROLEX":   {"color": "#2ca02c", "marker": "^", "linestyle": "-.", "lw": 1.5, "ms": 6},
        "Sherman": {"color": "#7f7f7f", "marker": "x", "linestyle": ":",  "lw": 1.5, "ms": 7},
    }

    for ax, w, title in zip(axes, workloads, titles):
        for method, pts in method_data.items():
            s = series_for_method(pts, w)
            if not s:
                continue
            ax.plot([p[0] for p in s], [p[1] for p in s],
                    label=method, **styles[method])
        ax.set_xlabel("Threads per CN", fontsize=11)
        ax.set_ylabel("Peak Throughput (Mops/s)", fontsize=11)
        ax.set_xscale("log", base=2)
        all_t = sorted({p["threads"] for pts in method_data.values()
                        for p in pts if p.get("workload") == w})
        if all_t:
            ax.set_xticks(all_t)
            ax.set_xticklabels([str(t) for t in all_t])
        ax.set_title(title, fontsize=11)
        ax.grid(alpha=0.3)
        ax.legend(loc="best", fontsize=9)

    fig.suptitle("CHIME vs Competitors on r650 Clemson, 1 CN + 1 MN",
                 fontsize=12)
    fig.tight_layout()
    out = out_dir / "fig12-competitors.pdf"
    fig.savefig(out, bbox_inches="tight")
    print(f"wrote {out}")
    plt.close(fig)


if __name__ == "__main__":
    main()

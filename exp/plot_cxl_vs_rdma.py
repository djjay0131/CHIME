"""Render CXL vs RDMA comparison figures from May 1 data."""
from __future__ import annotations

import json
from pathlib import Path
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load(path: Path) -> list[dict]:
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
    base = Path(__file__).parent / "results" / "rdma-2node-04271959"
    out_dir = Path(__file__).parent / ".." / "report" / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)

    rdma_files = ["fig_12_c_sweep.jsonl", "fig_12_chime_extra.jsonl",
                  "fig_12_de_sweep.jsonl", "fig_12_variance.jsonl",
                  "fig_12_variance_v2.jsonl"]
    cxl_files = ["fig_12_cxl_sweep.jsonl", "fig_12_cxl_de.jsonl"]

    rdma = defaultdict(list)
    for f in rdma_files:
        for d in load(base / f):
            m = d.get("peak_mops", 0)
            if m > 0:
                w = d.get("workload", "c")
                rdma[(w, d.get("threads"))].append(m)

    cxl = defaultdict(list)
    for f in cxl_files:
        for d in load(base / f):
            m = d.get("peak_mops", 0)
            if m > 0:
                cxl[(d["workload"], d["threads"])].append(m)

    # Build series per (transport, workload)
    def series(data, w):
        pts = []
        for (ww, t), vals in data.items():
            if ww == w:
                pts.append((t, max(vals)))
        return sorted(pts)

    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2))
    workloads = ["c", "d", "e"]
    titles = ["YCSB C (read-only)", "YCSB D (95% read, 5% insert)",
              "YCSB E (range scan)"]

    for ax, w, title in zip(axes, workloads, titles):
        r = series(rdma, w)
        c = series(cxl, w)
        if r:
            ax.plot([p[0] for p in r], [p[1] for p in r],
                    "o-", color="#1f77b4", linewidth=1.5, markersize=7,
                    label="RDMA")
        if c:
            ax.plot([p[0] for p in c], [p[1] for p in c],
                    "s--", color="#d62728", linewidth=1.5, markersize=7,
                    label="CXL")
        ax.set_xlabel("Threads", fontsize=11)
        ax.set_ylabel("Peak Throughput (Mops/s)", fontsize=11)
        ax.set_xscale("log", base=2)
        all_threads = sorted(set([p[0] for p in r] + [p[0] for p in c]))
        ax.set_xticks(all_threads)
        ax.set_xticklabels([str(t) for t in all_threads])
        ax.set_title(title, fontsize=11)
        ax.grid(alpha=0.3)
        ax.legend(loc="best")

    fig.suptitle("CHIME on r650 Clemson, 1 CN + 1 MN, May 1, 2026", fontsize=12)
    fig.tight_layout()
    fig.savefig(out_dir / "fig12-rdma-vs-cxl.pdf", bbox_inches="tight")
    print(f"wrote {out_dir/'fig12-rdma-vs-cxl.pdf'}")
    plt.close(fig)

    # Speedup ratio bar chart
    fig, ax = plt.subplots(figsize=(8, 4))
    ratios_c, ratios_d, ratios_e = {}, {}, {}
    for (w, t), vals in cxl.items():
        rmax = max(rdma.get((w, t), [0])) if rdma.get((w, t)) else None
        if rmax and rmax > 0:
            cmax = max(vals)
            target = {"c": ratios_c, "d": ratios_d, "e": ratios_e}.get(w)
            if target is not None:
                target[t] = cmax / rmax

    threads = sorted(set(list(ratios_c) + list(ratios_d) + list(ratios_e)))
    width = 0.27
    x = list(range(len(threads)))
    ax.bar([i - width for i in x], [ratios_c.get(t, 0) for t in threads], width,
           label="C", color="#1f77b4")
    ax.bar(x, [ratios_d.get(t, 0) for t in threads], width,
           label="D", color="#ff7f0e")
    ax.bar([i + width for i in x], [ratios_e.get(t, 0) for t in threads], width,
           label="E", color="#2ca02c")
    ax.axhline(y=1.0, color="gray", linestyle="--", linewidth=1, alpha=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels([str(t) for t in threads])
    ax.set_xlabel("Threads", fontsize=11)
    ax.set_ylabel("CXL / RDMA Throughput Ratio", fontsize=11)
    ax.set_title("CXL Throughput Speedup vs RDMA per Workload",
                 fontsize=11)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_dir / "fig12-cxl-rdma-ratio.pdf", bbox_inches="tight")
    print(f"wrote {out_dir/'fig12-cxl-rdma-ratio.pdf'}")


if __name__ == "__main__":
    main()

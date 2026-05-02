"""Compare CHIME-CXL across May 1 and May 2 to demonstrate reproducibility."""
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


def series(points: list[dict], workload: str) -> list[tuple[int, float]]:
    by_t: dict[int, list[float]] = defaultdict(list)
    for p in points:
        if p.get("workload") != workload:
            continue
        m = p.get("peak_mops", 0)
        if m and m > 0:
            by_t[p["threads"]].append(m)
    return sorted([(t, max(vals)) for t, vals in by_t.items()])


def main() -> None:
    apr27 = Path(__file__).parent / "results" / "rdma-2node-04271959"
    may2 = Path(__file__).parent / "results" / "may2-competitors"
    out_dir = Path(__file__).parent / ".." / "report" / "figures"

    cxl_may1 = (load_jsonl(apr27 / "fig_12_cxl_sweep.jsonl")
                + load_jsonl(apr27 / "fig_12_cxl_de.jsonl"))
    cxl_may2 = []
    rdma_apr27 = []
    rdma_may2 = []
    for w in "cde":
        cxl_may2.extend(load_jsonl(may2 / f"chime_cxl_may2_{w}.jsonl"))
        rdma_may2.extend(load_jsonl(may2 / f"chime_rdma_may2_{w}.jsonl"))
    for f in ["fig_12_c_sweep.jsonl", "fig_12_chime_extra.jsonl",
              "fig_12_de_sweep.jsonl"]:
        rdma_apr27.extend(load_jsonl(apr27 / f))
    rdma_apr27.append({"workload": "c", "threads": 8, "peak_mops": 1.12})

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    workloads = ["c", "d", "e"]
    titles = ["YCSB C (read-only)", "YCSB D (95% read, 5% insert)",
              "YCSB E (range scan)"]

    for ax, w, title in zip(axes, workloads, titles):
        for label, pts, color, marker, linestyle in [
            ("RDMA Apr 27", rdma_apr27, "#1f77b4", "o", "--"),
            ("RDMA May 2",  rdma_may2,  "#1f77b4", "o", "-"),
            ("CXL  May 1",  cxl_may1,   "#d62728", "s", "--"),
            ("CXL  May 2",  cxl_may2,   "#d62728", "s", "-"),
        ]:
            s = series(pts, w)
            if not s:
                continue
            ax.plot([p[0] for p in s], [p[1] for p in s],
                    label=label, color=color, marker=marker, linestyle=linestyle,
                    lw=1.5, ms=6)
        ax.set_xlabel("Threads", fontsize=11)
        ax.set_ylabel("Peak Throughput (Mops/s)", fontsize=11)
        ax.set_xscale("log", base=2)
        ax.set_title(title, fontsize=11)
        ax.grid(alpha=0.3)
        ax.legend(loc="best", fontsize=9)

    fig.suptitle("CHIME RDMA vs CXL: Cross-Day Reproducibility on r650 Clemson 1 CN + 1 MN",
                 fontsize=11)
    fig.tight_layout()
    out = out_dir / "fig12-cxl-reproducibility.pdf"
    fig.savefig(out, bbox_inches="tight")
    print(f"wrote {out}")
    plt.close(fig)


if __name__ == "__main__":
    main()

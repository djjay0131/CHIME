"""Plot 2x2 transport vs method: CHIME/Sherman x RDMA/CXL on the same hardware."""
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

    chime_rdma = []
    for w in "cde":
        chime_rdma.extend(load_jsonl(may2 / f"chime_rdma_may2_{w}.jsonl"))

    chime_cxl = (load_jsonl(apr27 / "fig_12_cxl_sweep.jsonl")
                 + load_jsonl(apr27 / "fig_12_cxl_de.jsonl"))

    sherman_rdma = []
    for w in "cde":
        sherman_rdma.extend(load_jsonl(may2 / f"sherman_{w}_sweep.jsonl"))

    sherman_cxl = []
    for w in "cde":
        sherman_cxl.extend(load_jsonl(may2 / f"sherman_cxl_{w}.jsonl"))

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    workloads = ["c", "d", "e"]
    titles = ["YCSB C", "YCSB D", "YCSB E"]
    styles = {
        "CHIME-RDMA":   {"color": "#d62728", "marker": "o", "linestyle": "-"},
        "CHIME-CXL":    {"color": "#d62728", "marker": "o", "linestyle": "--"},
        "Sherman-RDMA": {"color": "#1f77b4", "marker": "s", "linestyle": "-"},
        "Sherman-CXL":  {"color": "#1f77b4", "marker": "s", "linestyle": "--"},
    }

    for ax, w, title in zip(axes, workloads, titles):
        for label, pts in [("CHIME-RDMA", chime_rdma),
                           ("CHIME-CXL", chime_cxl),
                           ("Sherman-RDMA", sherman_rdma),
                           ("Sherman-CXL", sherman_cxl)]:
            s = series(pts, w)
            if not s:
                continue
            ax.plot([p[0] for p in s], [p[1] for p in s],
                    label=label, lw=1.5, ms=6, **styles[label])
        ax.set_xlabel("Threads", fontsize=11)
        ax.set_ylabel("Peak Throughput (Mops/s)", fontsize=11)
        ax.set_xscale("log", base=2)
        ax.set_title(title, fontsize=11)
        ax.grid(alpha=0.3)
        ax.legend(loc="best", fontsize=9)

    fig.suptitle("Transport vs Method: CHIME/Sherman x RDMA/CXL, r650 Clemson 1 CN + 1 MN (RDMA May 2 + CXL May 1, same hardware)",
                 fontsize=11)
    fig.tight_layout()
    out = out_dir / "fig12-transport-method.pdf"
    fig.savefig(out, bbox_inches="tight")
    print(f"wrote {out}")
    plt.close(fig)


if __name__ == "__main__":
    main()

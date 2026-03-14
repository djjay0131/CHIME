#!/usr/bin/env python3
"""
Generate exp/params/common.json from cluster configuration.

Usage:
  python3 generate-common-json.py --home /users/you --master 10.10.1.2 \\
    --ips 10.10.1.2,10.10.1.1,... --out exp/params/common.json

Examples:
  Dry run (6 nodes: 5 CN + 1 MN):  --ips with 6 IPs, first = master
  Full run (10 nodes: 9 CN + 1 MN): --ips with 10 IPs
  11-node paper config (10 CN + 1 MN): --ips with 11 IPs
"""

import argparse
import json
import sys
from pathlib import Path

# Load base common.json to preserve cmake_options etc.
REPO_ROOT = Path(__file__).resolve().parents[2]
COMMON_JSON = REPO_ROOT / "exp" / "params" / "common.json"


def main():
    ap = argparse.ArgumentParser(description="Generate common.json from cluster config")
    ap.add_argument("--home", required=True, help="Home directory on nodes (e.g. /users/you)")
    ap.add_argument("--master", required=True, help="Master node IP")
    ap.add_argument("--ips", required=True, help="Comma-separated cluster IPs (master first)")
    ap.add_argument("--out", default=None, help="Output path (default: overwrite exp/params/common.json)")
    args = ap.parse_args()

    home = args.home.rstrip("/")
    workloads_dir = f"{home}/CHIME/ycsb/workloads"
    cluster_ips = [ip.strip() for ip in args.ips.split(",") if ip.strip()]

    if args.master not in cluster_ips:
        print("Warning: master IP not in cluster_ips; adding as first element", file=sys.stderr)
        cluster_ips.insert(0, args.master)

    with open(COMMON_JSON) as f:
        cfg = json.load(f)

    cfg["home_dir"] = home
    cfg["workloads_dir"] = workloads_dir
    cfg["master_ip"] = args.master
    cfg["cluster_ips"] = cluster_ips

    out_path = Path(args.out) if args.out else COMMON_JSON
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(cfg, f, indent=4)

    # Also update memcached.conf if it exists (master IP + port)
    memcached_conf = REPO_ROOT / "memcached.conf"
    if memcached_conf.exists():
        with open(memcached_conf, "w") as f:
            f.write(f"{args.master}\n11211\n")
        print(f"Updated {memcached_conf} with master_ip")

    print(f"Wrote {out_path}")
    print(f"  home_dir: {home}")
    print(f"  master_ip: {args.master}")
    print(f"  cluster_ips: {len(cluster_ips)} nodes")


if __name__ == "__main__":
    main()

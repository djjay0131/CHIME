# Sprint 02 Setup Scripts

Helper scripts for the Part One experiment reproduction (CloudLab r650 at Clemson).

**Current repo state:** Experiment params (`fig_12`, `fig_14`, `fig_15a`, `fig_15b`) are patched for **10-node (9 CN + 1 MN)**. Day 1 automation is in place: use `day1-runbook.md` and `script/day1-dry-run.sh` after SSH and `setKey.py`.

| Script | Purpose |
|--------|---------|
| `generate-common-json.py` | Generate `exp/params/common.json` and `memcached.conf` from cluster IPs (use real IPs after reservation) |
| `patch-cn-count.py` | Patch fig params for cluster size (dry run: 5; full run: 9 — already run for 9 CN in repo) |
| `nodes.txt.example` | Template for node hostnames; copy to `nodes.txt` for setKey.py |
| `day1-runbook.md` | Day 1 copy-paste runbook (dry run / full run) |
| `setup-checklist.md` | Day-by-day setup checklist for dry run and full run (10-node flow) |

See also `script/` in repo root: `run-on-nodes.sh`, `setKey.py`, `clone-repos.sh`, `setup-hugepages.sh`, **`day1-dry-run.sh`** (one-shot Day 1 after setKey).

Run `generate-common-json.py` from the repo root after you have node IPs:

```bash
python3 construction/scripts/generate-common-json.py \
  --home /users/$(whoami) \
  --master <master_ip> \
  --ips <ip1>,<ip2>,<ip3>,...
```

See `setup-checklist.md` for the full setup flow.

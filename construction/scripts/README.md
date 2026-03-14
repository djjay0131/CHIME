# Sprint 02 Setup Scripts

Helper scripts for the Part One experiment reproduction (CloudLab r650 at Clemson).

| Script | Purpose |
|--------|---------|
| `generate-common-json.py` | Generate `exp/params/common.json` and `memcached.conf` from cluster IPs |
| `patch-cn-count.py` | Patch fig params for cluster size (dry run: 5, full run: 9) |
| `nodes.txt.example` | Template for node hostnames; copy to `nodes.txt` for setKey.py |
| `setup-checklist.md` | Day-by-day setup checklist for dry run and full run |

See also `script/` in repo root: `run-on-nodes.sh`, `setKey.py`, `clone-repos.sh`, `setup-hugepages.sh`.

Run `generate-common-json.py` from the repo root after you have node IPs:

```bash
python3 construction/scripts/generate-common-json.py \
  --home /users/$(whoami) \
  --master <master_ip> \
  --ips <ip1>,<ip2>,<ip3>,...
```

See `setup-checklist.md` for the full setup flow.

# Sprint 02 Setup Checklist

Use this checklist during the dry run (Mar 17–19) and full run (Mar 27–Apr 3). **Repo is pre-patched for 10-node (9 CN + 1 MN):** `exp/params` fig_12, fig_14, fig_15a, fig_15b and `common.json` (10 IP placeholders). For dry run with fewer nodes, run `patch-cn-count.py 5` (or 4) before experiments; after full-run setup, params already match 9 CN.

## Day 1: SSH + RDMA + Repos

**Quick path (after SSH to master):** Pull repo → create `nodes.txt` from CloudLab List View → run `setKey.py` → run `day1-dry-run.sh` → then generate `common.json` with real IPs (step 7).

### 1. Get node IPs and hostnames

After CloudLab reservation starts, get the node list from the CloudLab dashboard (List View → node hostnames). Create `nodes.txt` (one hostname per line) for `setKey.py` and `run-on-nodes.sh`:

```
node-0.your-experiment.your-project.clemson.cloudlab.us
node-1.your-experiment.your-project.clemson.cloudlab.us
node-2.your-experiment.your-project.clemson.cloudlab.us
...
```

Template: `construction/scripts/nodes.txt.example`. Copy to `nodes.txt` and fill in your experiment hostnames. **Day 1 runbook:** `construction/scripts/day1-runbook.md`. **One-shot script (after setKey):** `NODES_FILE=./nodes.txt bash script/day1-dry-run.sh`.
Or use comma-separated: `node-0.exp.proj.clemson.cloudlab.us,node-1.exp.proj.clemson.cloudlab.us,...`

### 2. SSH setup

- Generate SSH key on your laptop if needed: `ssh-keygen -t ed25519 -N ''`
- Add your public key to CloudLab project/account so you can `ssh <user>@<node>`
- From the **master node** (first node), run `script/setKey.py`:

```bash
cd ~/CHIME
# Option A: edit USER and SERVER_LIST in script/setKey.py
# Option B: use env vars
SETKEY_USER=youruser NODES="node-0.exp.proj.clemson.cloudlab.us,node-1.exp.proj.clemson.cloudlab.us" python3 script/setKey.py
# Option C: nodes from file (one hostname per line)
SETKEY_USER=youruser NODES_FILE=./nodes.txt python3 script/setKey.py
```

Or manually:
- On master: `ssh-keygen -t rsa -N '' -f ~/.ssh/id_rsa`
- Copy `~/.ssh/id_rsa.pub` to `authorized_keys` on all nodes
- Ensure passwordless SSH: `ssh node-1 hostname` works from master

### 3. Install RDMA stack (each node)

**Option A:** CloudLab r650 profile may include RDMA. Verify first:

```bash
ibv_devinfo
```

If that fails, install MLNX OFED:

```bash
cd ~/CHIME/script
bash installMLNX.sh   # Ubuntu 18.04; adjust URL in script for Ubuntu 20/22
```

### 4. Install dependencies (each node)

```bash
cd ~/CHIME
# Run in parallel on all nodes:
bash script/run-on-nodes.sh "node-0,node-1,..." "cd ~/CHIME/script && bash installLibs.sh"
# Or run manually on each node
```

**Ubuntu 22+:** If `installLibs.sh` fails with pip "externally managed environment" error:

```bash
export PIP_BREAK_SYSTEM=1
bash script/installLibs.sh
```

### 5. Configure hugepages (each node)

```bash
sudo bash ~/CHIME/script/setup-hugepages.sh
```

### 6. Clone repos (each node)

CHIME is typically cloned via CloudLab profile or manually. Siblings:

```bash
bash ~/CHIME/script/clone-repos.sh
```

### 7. Generate common.json

From master node, after you have the cluster IPs:

```bash
cd ~/CHIME
python3 construction/scripts/generate-common-json.py \
  --home "$HOME" \
  --master "<master_ip>" \
  --ips "<ip1>,<ip2>,<ip3>,..." \
  --out exp/params/common.json
```

Example for 6-node dry run (5 CN + 1 MN):

```bash
python3 construction/scripts/generate-common-json.py \
  --home /users/$(whoami) \
  --master 10.10.1.2 \
  --ips 10.10.1.2,10.10.1.1,10.10.1.3,10.10.1.4,10.10.1.5,10.10.1.6
```

Example for 10-node full run:

```bash
python3 construction/scripts/generate-common-json.py \
  --home /users/$(whoami) \
  --master 10.10.1.2 \
  --ips 10.10.1.2,10.10.1.1,10.10.1.3,10.10.1.4,10.10.1.5,10.10.1.6,10.10.1.7,10.10.1.8,10.10.1.9,10.10.1.10
```

### 7b. Patch experiment params for node count

Figure params (fig_12, fig_14, fig_15a, fig_15b) hardcode CN count. **Run this before experiments** (repo is currently patched for **10-node / 9 CN**; re-run only if you use a different size):

| Cluster size | Total nodes | CN count | Command |
|--------------|-------------|----------|---------|
| Dry run      | 5 or 6      | 4 or 5   | `python3 construction/scripts/patch-cn-count.py 5` |
| Full run     | 10          | 9        | `python3 construction/scripts/patch-cn-count.py 9` (already applied in repo) |
| 11-node      | 11          | 10       | `python3 construction/scripts/patch-cn-count.py 10` (paper default) |

```bash
cd ~/CHIME
# Dry run: 5 CN + 1 MN (if you have 6 nodes) or 4 CN + 1 MN (5 nodes)
python3 construction/scripts/patch-cn-count.py 5

# Full run (10 nodes): 9 CN + 1 MN
python3 construction/scripts/patch-cn-count.py 9
```

---

## Day 2: Build + YCSB + Smoke test

### 8. Build CHIME and Sherman

```bash
cd ~/CHIME
rm -rf build && mkdir build && cd build
cmake .. -DENABLE_CACHE=on -DHOPSCOTCH_LEAF_NODE=on [other flags from common.json]
make -j
# Verify: ls test/ycsb_test
```

Repeat for Sherman (different CMake flags). The figure scripts handle rebuilds automatically.

### 9. Build SMART, ROLEX, Marlin

Follow each repo’s README. Typical:

- SMART: `mkdir build && cd build && cmake .. && make -j`
- ROLEX: same pattern
- Marlin: same pattern

### 10. Generate YCSB workloads (all nodes, in parallel)

```bash
# On each node - use run-on-nodes.sh for parallel execution:
cd ~/CHIME
NODES="node-0,node-1,..."  # or use node hostnames
bash script/run-on-nodes.sh "$NODES" "cd ~/CHIME/ycsb && rm -rf workloads && sudo sh generate_full_workloads.sh"
# Or run manually on each node; ~1h 28m per node
```

### 11. Smoke test (1 CN + 1 MN)

```bash
cd ~/CHIME/exp
python3 smoke_test.py
```

This builds CHIME, splits workloads for 1 CN, and runs YCSB C. Requires `cluster_ips` with ≥2 nodes and `memcached.conf` with master IP (set by `generate-common-json.py`).

---

## Verification

- [ ] `ibv_devinfo` passes on all nodes
- [ ] `memcached -h` works on master
- [ ] `cmake --version` >= 3.12
- [ ] `grep HugePages /proc/meminfo` shows allocated hugepages (default: 36864 per paper)
- [ ] `ls ~/CHIME ~/SMART ~/ROLEX ~/Marlin` on every node
- [ ] `ssh node-N hostname` without password from master
- [ ] YCSB C produces throughput > 0 at 1-node scale

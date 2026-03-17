# Day 1 Runbook — Dry Run (Mar 17)

Run from the **master node** (first node in your CloudLab experiment) with CHIME repo in `~/CHIME`. Replace placeholders with your experiment’s node hostnames and IPs.

---

## 0. Prerequisites

- CloudLab reservation is active; you can `ssh <user>@<node-i>` to each node (password or project key).
- CHIME is on the master (e.g. `git clone` or profile). If your profile does not deploy CHIME to all nodes, clone it on each node first.

---

## 1. Node list

Create `~/CHIME/nodes.txt` (one hostname per line) from CloudLab List View, e.g.:

```
node-0.exp12345.myproject.clemson.cloudlab.us
node-1.exp12345.myproject.clemson.cloudlab.us
...
```

Or set a comma-separated list:

```bash
export NODES="node-0.exp....,node-1.exp....,node-2.exp....,node-3.exp....,node-4.exp....,node-5.exp...."
```

---

## 2. SSH (passwordless between nodes)

From the master (or laptop with SSH to all nodes):

```bash
cd ~/CHIME
SETKEY_USER=$(whoami) NODES_FILE=./nodes.txt python3 script/setKey.py
# Or: SETKEY_USER=$(whoami) NODES="node-0,...,node-5" python3 script/setKey.py
```

Verify:

```bash
# From master; use your actual node hostname for node-1
ssh node-1 hostname
```

---

## 3. RDMA

On the master:

```bash
ibv_devinfo
```

If that works, run on all nodes:

```bash
cd ~/CHIME
NODES=$(paste -sd, - < nodes.txt)   # if you use nodes.txt
bash script/run-on-nodes.sh "$NODES" "ibv_devinfo"
```

If `ibv_devinfo` fails on any node, install MLNX OFED there:

```bash
bash script/run-on-nodes.sh "$NODES" "cd ~/CHIME/script && bash installMLNX.sh"
```

---

## 4. Dependencies (all nodes, parallel)

```bash
cd ~/CHIME
NODES=$(paste -sd, - < nodes.txt)
bash script/run-on-nodes.sh "$NODES" "cd ~/CHIME/script && bash installLibs.sh"
```

(Takes several minutes. On Ubuntu 22+ if pip fails, run with `PIP_BREAK_SYSTEM=1` on each node or use the Day 1 script with that env set.)

---

## 5. Hugepages (all nodes)

```bash
bash script/run-on-nodes.sh "$NODES" "sudo bash ~/CHIME/script/setup-hugepages.sh"
```

---

## 6. Clone sibling repos (all nodes)

Assumes CHIME already exists on each node:

```bash
bash script/run-on-nodes.sh "$NODES" "bash ~/CHIME/script/clone-repos.sh"
```

---

## 7. common.json (master only)

Get your cluster **IPs** from CloudLab (List View or `ifconfig` on each node). First IP = master.

```bash
cd ~/CHIME
python3 construction/scripts/generate-common-json.py \
  --home "$HOME" \
  --master "<master_ip>" \
  --ips "<ip1>,<ip2>,<ip3>,<ip4>,<ip5>,<ip6>"
```

Example (replace with your IPs):

```bash
python3 construction/scripts/generate-common-json.py \
  --home /users/$(whoami) \
  --master 10.10.1.2 \
  --ips 10.10.1.2,10.10.1.1,10.10.1.3,10.10.1.4,10.10.1.5,10.10.1.6
```

---

## 8. Patch for 5 CN (dry run)

```bash
cd ~/CHIME
python3 construction/scripts/patch-cn-count.py 5
```

---

## 9. Quick checks

```bash
# Hugepages
bash script/run-on-nodes.sh "$NODES" "grep HugePages_Total /proc/meminfo"

# Repos
bash script/run-on-nodes.sh "$NODES" "ls ~/CHIME ~/SMART ~/ROLEX ~/Marlin"
```

---

**Next (Day 2):** Build all methods, generate YCSB workloads, run `exp/smoke_test.py`. See `setup-checklist.md` from step 8 onward.

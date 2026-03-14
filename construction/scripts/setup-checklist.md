# Sprint 02 Setup Checklist

Use this checklist during the dry run (Mar 17–19) and full run (Mar 27–Apr 3).

## Day 1: SSH + RDMA + Repos

### 1. Get node IPs and hostnames

After CloudLab reservation starts, get the node list from the CloudLab dashboard or:

```bash
# List nodes (example for 5-node dry run)
# Nodes appear as node-0, node-1, ... or clnodeXXX.clemson.cloudlab.us
```

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

Example for 5-node dry run:

```bash
python3 construction/scripts/generate-common-json.py \
  --home /users/$(whoami) \
  --master 10.10.1.2 \
  --ips 10.10.1.2,10.10.1.1,10.10.1.3,10.10.1.4,10.10.1.5
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
- [ ] `grep HugePages /proc/meminfo` shows allocated hugepages
- [ ] `ls ~/CHIME ~/SMART ~/ROLEX ~/Marlin` on every node
- [ ] `ssh node-N hostname` without password from master
- [ ] YCSB C produces throughput > 0 at 1-node scale

# r6525 Pre-Deadline Experiment Log (Mar 23-26, 2026)

## Overview

Reservation: 11x r6525 at Clemson (ID: 83cd62fd), Mar 23 14:00 UTC – Mar 26 00:00 UTC
Experiment: chime-r6525-run2 (ID: 4fc8525b)
Profile: chime-r6525-clemson
Nodes: 10 working (node10/clnode304 excluded due to broken RDMA), 9 CN + 1 MN

## Hardware Differences: r6525 vs r650

| Spec | r650 (paper) | r6525 (pre-deadline) |
|------|-------------|---------------------|
| CPU | Intel Xeon Gold 6338N (2x32C, 128 threads) | AMD EPYC 7513 (2x32C, 128 threads) |
| Physical cores | 64 | 64 |
| NIC (RDMA) | ConnectX-5 (mlx5_2, IB) | ConnectX-5 (mlx5_0, RoCE/Ethernet) |
| NIC (extra) | ConnectX-6 Dx | ConnectX-6 Dx |
| Link layer | InfiniBand | Ethernet (RoCE v2) |
| Root disk | ~450GB | 16GB (!) |
| NVMe | Available | 1.5TB (must be manually mounted) |
| Memory | 256GB | 256GB |

## Issues Encountered and Resolutions

### Issue 1: Node10 (clnode304) — No RDMA Devices
**Symptom:** `ibv_devinfo` shows no IB devices on node10.
**Cause:** Hardware/cabling issue — Mellanox interfaces DOWN, no infiniband sysfs entries.
**Resolution:** Excluded node10. Patched CN count from 10 to 9 (9 CN + 1 MN = 10 nodes).
**Impact:** Minor — 9 CNs is still within paper's config range. Paper uses 10 CN + 1 MN on r650.

### Issue 2: 16GB Root Partition Full
**Symptom:** YCSB workload generation failed silently (0-byte files), `OSError: No space left on device`.
**Cause:** r6525 root partition is only 16GB. YCSB intermediate files (3-6GB each) filled it.
**Resolution:** Mounted 1.5TB NVMe at `/mnt/nvme` on all nodes. Symlinked workloads directory. Saved final workloads to project NFS (`/proj/cs620426sp-PG0/ycsb_workloads/`) for reuse.
**Impact:** ~2 hours lost to debugging and re-generating workloads.

### Issue 3: YCSB 0.17.0 Python 2/3 Incompatibility
**Symptom:** YCSB `bin/ycsb` launcher fails with `print >>` syntax error.
**Cause:** YCSB 0.17.0 launcher is Python 2 but CloudLab nodes have Python 3.8 only.
**Resolution:** Fixed `print >>` → `print(..., file=...)`, `except X, err` → `except X as err`, `io.BytesIO` → `io.StringIO`. Also fixed `com.yahoo.ycsb` → `site.ycsb` in workload specs.
**Impact:** ~30 min to diagnose and fix.

### Issue 4: gen_workload.py Parsing Too Slow
**Symptom:** `workloada` intermediate files (3.1GB) exist but final parsed files missing.
**Cause:** Python line-by-line parsing of 3.1GB files is very slow; failed due to disk space before parsing completed.
**Resolution:** Used `awk` for faster parsing. Also, moving to NVMe eliminated space issues.
**Impact:** Minor — some workloads needed manual parsing.

### Issue 5: CPU_PHYSICAL_CORE_NUM Mismatch
**Symptom:** Potential thread-to-core binding issues.
**Cause:** `Common.h` hardcodes `CPU_PHYSICAL_CORE_NUM = 72` (r650 spec). r6525 has 64 physical cores. Directory thread would try to bind to core 143 (doesn't exist on r6525 with 128 CPUs).
**Resolution:** Patched to 64 on all nodes and repos.
**Impact:** Could have caused performance anomalies in directory thread scheduling.

### Issue 6: memcached.conf Wrong IP
**Symptom:** `restartMemc.sh` hangs — tries to SSH to `10.10.1.2` which doesn't exist on r6525.
**Cause:** The `generate-common-json.py` correctly set `master_ip` in `memcached.conf` for CHIME, but sibling repos (ROLEX, SMART, Marlin) had stale configs with internal IPs.
**Resolution:** Fixed `memcached.conf` on all repos/nodes to use `130.127.134.72` (public IP). Also rewrote `restartMemc.sh` to run locally instead of SSH-to-self.
**Impact:** ~9 hours lost — fig_15b ran 1700+ retries in infinite retry loop before diagnosis.

### Issue 7: restartMemc.sh SSH-to-Self Timeout
**Symptom:** `one_execute` times out (30s) trying to restart memcached.
**Cause:** `restartMemc.sh` SSHes to the master's own IP to kill/restart memcached. On r6525, this SSH sometimes takes >30s.
**Resolution:** Rewrote to run memcached commands locally (no SSH). Increased `one_execute` timeout from 30s to 60s.
**Impact:** Compounded with Issue 6.

### Issue 8: Paramiko Stale Connections
**Symptom:** `all_execute` keeps timing out after initial build succeeds.
**Cause:** Long-running builds (~5 min) cause Paramiko SSH transport to go stale. Subsequent `exec_command` calls on stale connections fail.
**Resolution:** Added `__ensure_connected()` method to `cmd_manager.py` that checks transport health and reconnects before every operation.
**Impact:** Would have caused infinite retry loops without fix.

### Issue 9: IB_DEV_NAME_IDX = '2' (Wrong RDMA Device)
**Symptom:** `ycsb_test` segfaults with "failed to open device". 196 segfaults exhausted mlx5_core command entries, requiring full node reboot.
**Cause:** `Rdma.h` hardcodes `IB_DEV_NAME_IDX = '2'` which selects `mlx5_2` (ConnectX-6 Dx, PORT_DOWN on r6525). The active device is `mlx5_0` (ConnectX-5).
**Resolution:** Changed to `IB_DEV_NAME_IDX = '0'` on all nodes/repos. Required full cluster reboot after mlx5_core command queue exhaustion.
**Impact:** ~12+ hours lost to debugging. Most time-consuming issue.

### Issue 10: MLX_GID Index (Link-Local vs Routable)
**Symptom:** ycsb_test runs but hangs during RDMA connection setup. All 9 nodes register in memcached but benchmark never starts.
**Cause:** `MLX_GID = 1` selects GID index 1 which is a **link-local** RoCE v2 address (`fe80::...`). For cross-node RoCE over routed Ethernet, need GID index 3 (IPv4-mapped routable: `::ffff:130.127.x.x`).
**Resolution:** Changed `MLX_GID` from 1 to 3 on all nodes/repos.
**Impact:** Investigation ongoing — testing if this resolves the RDMA connection issue.

### Issue 11: Stale ycsb_test Processes
**Symptom:** `serverNum` in memcached doesn't reach expected count; duplicate processes on some nodes.
**Cause:** Previous failed runs leave ycsb_test processes that register in memcached, consuming `serverNum` slots. New experiment instances can't reach the expected total.
**Resolution:** Kill all ycsb_test processes and reset memcached before each experiment start.
**Impact:** Adds to coordination confusion.

## Timeline

| Time (UTC) | Event |
|------------|-------|
| Mar 23 12:44 | First experiment creation attempt (failed — reservation not yet active) |
| Mar 23 15:04 | Experiment created successfully, nodes provisioning |
| Mar 23 15:20 | All 11 nodes ready. Setup begins. |
| Mar 23 15:46 | Setup complete. Node10 excluded (no RDMA). Config patched for 10 nodes. |
| Mar 23 15:46 | Builds started (CHIME, SMART, ROLEX all succeed) |
| Mar 23 15:46 | YCSB generation started on all nodes |
| Mar 23 ~16:00 | Disk full discovered (Issue 2). NVMe mounted. YCSB restarted. |
| Mar 23 ~17:00 | YCSB workloads la-d ready. fig_15b started. |
| Mar 23 ~17:00–Mar 24 04:00 | fig_15b stuck on memcached timeout + segfaults (Issues 6-9) |
| Mar 24 04:30 | IB_DEV_NAME_IDX fixed. fig_15b restarted. Still segfaulting (stale binary). |
| Mar 24 ~05:00 | cmd_manager.py patched with auto-reconnect. Restarted. Still segfaulting. |
| Mar 24 ~06:00 | Discovered mlx5_core command queue exhausted. Rebooted all nodes. |
| Mar 24 ~07:00 | 4 nodes stuck in SHUTDOWN. API `start` command used. |
| Mar 24 ~08:00 | All nodes back. Re-setup (hugepages, NVMe, workloads, SSH). |
| Mar 24 ~10:08 | fig_15b restarted. Zero retries. ycsb_test launches but hangs. |
| Mar 24 ~16:30 | Diagnosed MLX_GID issue (link-local vs routable). Fixed to GID index 3. |
| Mar 24 ~16:50 | fig_15b restarted with GID fix. Testing... |

## Lessons Learned

1. **Hardware validation first:** Always run `ibv_devinfo`, `ibdev2netdev`, and check GID tables before attempting RDMA experiments. The r650→r6525 migration changed device indices, link layer, and GID mappings.

2. **RoCE vs IB:** The paper's r650 uses InfiniBand link layer. r6525 uses Ethernet (RoCE v2). This changes device selection (`mlx5_0` vs `mlx5_2`), GID indices (need routable GID for cross-node), and potentially performance characteristics.

3. **Disk sizing matters:** Always check `df -h` on CloudLab nodes. The 16GB r6525 root partition is a trap — mount NVMe or use project NFS for large files.

4. **Kill stale processes between runs:** RDMA applications that crash without cleanup can exhaust kernel resources (mlx5_core command entries), requiring a reboot.

5. **Paramiko keepalive:** Long-running SSH connections need health checks and reconnection logic.

6. **Save workloads to persistent storage:** Project NFS (`/proj/`) persists across experiments. Saves hours of YCSB generation time.

## Configuration Summary for r6525

```
# Rdma.h
IB_DEV_NAME_IDX = '0'   # mlx5_0 (ConnectX-5, PORT_ACTIVE)
MLX_PORT = 1
MLX_GID = 3              # Routable RoCE v2 (IPv4-mapped)

# Common.h
CPU_PHYSICAL_CORE_NUM = 64
MEMORY_NODE_NUM = 1

# memcached.conf (all repos)
130.127.134.72
11211

# restartMemc.sh — run locally, no SSH
```

# Experimental Methodology — May 1–4, 2026

This document captures the *how* behind every CXL/RDMA result file under
`exp/results/`. It is the audit trail that lets a reviewer reproduce the
numbers from scratch. It is intentionally pedantic.

## 1. Hardware

### 1.1 CloudLab reservations used

| Reservation UUID                       | Cluster | Hardware | Window (UTC)                           | Used as                                    |
| -------------------------------------- | ------- | -------- | -------------------------------------- | ------------------------------------------ |
| `2afbcb47-…` (chime-04271959)          | Clemson | r650 ×2  | Apr 27 16:00 → Apr 28 11:59 (16 h)     | CHIME-RDMA reference + CXL bring-up        |
| `prb-145800` (May 1 experiment)        | Clemson | r650 ×2  | May 1 14:58 → May 2 13:58              | CXL alloc-bug fix + 17-point CXL sweep     |
| `1fa0f366-…` (May 2 partial)           | Clemson | r650 ×3  | May 1 15:00 → May 2 15:00              | overlap with `prb-145800`                  |
| `312ca700-…` (May 2 active)            | Clemson | r650 ×4  | May 2 17:00 → May 3 17:00 (24 h)       | n=4 attempts (bricked) → n=2 fallback      |
| (web-UI-created) experiment `ff830fe4` | Clemson | r650 ×4  | May 3 03:31 → May 4 01:31              | full May 3 sprint, single-node CXL only    |
| `8971e238-…` (final, future)           | Clemson | r650 ×7  | May 6 01:00 → May 11 01:00             | final multi-CN run before paper deadline   |

### 1.2 Per-node hardware

CloudLab `r650` profile description (verified via `lscpu`, `numactl --hardware`,
`ibv_devinfo` on each node):

- Dual-socket Intel Xeon Gold 6336Y (24 cores per socket, 48 logical / SMT off
  by default), 256 GB DDR4 ECC.
- Two NUMA nodes: node0 (socket 0, 128 GB) and node1 (socket 1, 128 GB). All
  CXL emulation experiments mmap a 64 GB pool with `MPOL_BIND` to NUMA node 1
  to simulate CXL-attached memory bandwidth/latency from CN threads pinned to
  socket 0.
- Mellanox ConnectX-6 Dx 100 GbE (`mlx5_2`), in **RoCE v2** over a tagged VLAN
  (296 on the May 1 reservation, 265 on the May 2 reservation, varies per
  experiment). MTU 9000 on the internal LAN. Public control net is `eno12399`
  (managed by the same `mlx5_core` driver, hence the openibd-restart trap;
  see §6).
- MLNX OFED `4.9-5.1.0.0` user-space stack (`--user-space-only --without-fw-update`),
  installed from a pre-staged tarball at `/proj/cs620426sp-PG0/djjay-tmp/ofed/`
  to avoid per-node 200 MB downloads.

### 1.3 Per-experiment node mapping

A given experiment maps `node0..node3` (CloudLab logical names) to specific
physical machines (`clnodeNNN`). The mapping changes per experiment. The
manifest XML returned by `portal-cli experiment manifests get` carries both
the logical name (`client_id`) and the physical name (`component_id`); we
record both in the per-experiment notes. Example (May 2 `prb-145800`):

| Logical | Physical   | Internal IP | Public IP        |
| ------- | ---------- | ----------- | ---------------- |
| node0   | clnode257  | 10.10.1.1   | 130.127.134.42   |
| node1   | clnode263  | 10.10.1.2   | 130.127.134.48   |

All RDMA traffic uses the internal `10.10.1.x` address (vlan296/vlan265, never
the public iface).

## 2. Software stack

### 2.1 CHIME

- Source: `https://github.com/djjay0131/CHIME.git` (fork of `juyoungbang/CHIME`).
- Build flags relevant to the ablation:
  - `HOPSCOTCH_LEAF_NODE` — hopscotch-displacement leaf layout
  - `VACANCY_AWARE_LOCK` — vacancy bitmap piggybacking the lock word
  - `METADATA_REPLICATION` — leaf-metadata replication for fast reads
  - `SIBLING_BASED_VALIDATION` — sibling pointer for validation without re-read
  - `SPECULATIVE_READ` — issue a follow-on read in parallel with the first read
  - `ENABLE_CACHE` — CN-side index cache (always ON in the variants we test)
  - `USE_CXL` — replace the RDMA transport with `CxlTransport` (NUMA-emulated)
- The CXL allocator overlap fix (commit `a3c9e87`) sets
  `alloc_offset_(define::kChunkSize)` so the allocator never collides with
  `root_ptr_ptr` at `kRootPointerStoreOffest = kChunkSize/2 = 8 MB`.
- Build is cmake out-of-tree, target `ycsb_test`. Build directories live on
  `/proj/cs620426sp-PG0/djjay-build/build-{rdma-shared,cxl-fix1,Sherman,SMART,
  ROLEX,Sherman-cxl,cxl-15a-{hopscotch,vacancy,metadata,sibling}}/`.

### 2.2 Variant definitions used in the ablation

| Variant       | HOPSCOTCH | VACANCY | METADATA | SIBLING | SPECULATIVE | USE_CXL |
| ------------- | --------- | ------- | -------- | ------- | ----------- | ------- |
| `sherman`     | OFF       | OFF     | OFF      | OFF     | OFF         | ON      |
| `+hopscotch`  | ON        | OFF     | OFF      | OFF     | OFF         | ON      |
| `+vacancy`    | ON        | ON      | OFF      | OFF     | OFF         | ON      |
| `+metadata`   | ON        | ON      | ON       | OFF     | OFF         | ON      |
| `+sibling`    | ON        | ON      | ON       | ON      | OFF         | ON      |
| `chime` (full)| ON        | ON      | ON       | ON      | ON          | ON      |

Sherman-RDMA, Sherman-CXL: all five flags off. CHIME-RDMA, CHIME-CXL: all on.
SMART: separate repo (`dmemsys/SMART`) with its own ablation flags
(`ART_INDEXED_CACHE=on -DHOMOGENEOUS_INTERNAL_NODE=on -DLOCK_FREE_INTERNAL_NODE=on
-DUPDATE_IN_PLACE_LEAF_NODE=on -DREAR_EMBEDDED_LOCK=on`). ROLEX: separate repo
(`River861/ROLEX`) with its own learned-index defaults.

### 2.3 Workloads

YCSB-style binary workloads pre-generated into 8 B keys / 8 B values, randint
distribution. Files live on `/proj/cs620426sp-PG0/ycsb_workloads/`. The
`workloads.conf` file in each build's parent directory points to that path.
Workload mix per file:

| Workload | Read | Update | Insert | Range scan | Notes                                  |
| -------- | ---- | ------ | ------ | ---------- | -------------------------------------- |
| C        | 100% | 0      | 0      | 0          | read-only baseline                     |
| D        | 95%  | 0      | 5%     | 0          | read-mostly with new-key inserts       |
| E        | 0    | 0      | 5%     | 95% (scan) | range-heavy                            |
| A        | 50%  | 50%    | 0      | 0          | high-update mix (Tree.cpp:1596 crash)  |
| B        | 95%  | 5%     | 0      | 0          | low-update mix (Tree.cpp:1596 crash)   |

We do not run LOAD as a separate measurement — every `ycsb_test` invocation
loads the dataset before running its measurement epochs.

## 3. ycsb_test invocation

A single measurement is one `ycsb_test` invocation:

```
./ycsb_test  <machine_count>  <threads_per_CN>  <coroutines_per_thread>  randint  <workload_letter>
```

Examples used:

- Single-CN CXL: `./ycsb_test 1 16 1 randint c` (1 process, 16 threads, 1 coro)
- 1 CN + 1 MN RDMA: `./ycsb_test 2 16 1 randint c` started on each of the two
  nodes; the first one to register with memcached gets server ID 0 (MN), the
  second gets ID 1 (CN). Both run in parallel until the CN finishes its
  `target_epoch` (default 10) measurement epochs.
- Multi-CN: `./ycsb_test 4 16 1 randint c` (1 MN + 3 CN; deferred to May 6).

The ycsb_test process (a) loads the workload's pre-generated data into the
shared memory pool, (b) waits for all servers to register via memcached
(serverNum / clientNum counters), (c) runs `target_epoch` measurement epochs
of duration `kEpochDuration_s` each, printing one `cluster throughput X.XXX
Mops` line per epoch, and (d) prints a final cache-hit / lock-fail summary
followed by `[END]`.

We measure the **peak across all post-warmup epochs** (not the final epoch,
not the mean) — `grep -oE 'cluster throughput [0-9.]+' | sort -g | tail -1`.
This is the same statistic the CHIME paper reports as "throughput" in
Figure 12. Epoch 1 is always the warmup (high cache-miss rate); we let
`tail -1` pick whichever steady-state epoch peaked.

The run is bounded by `timeout 90` (or 120 / 200 for long-run experiments) to
prevent runaway processes. Most runs complete in 18-30 seconds at low thread
counts and 30-50 seconds at high thread counts, well within the timeout.

### 3.1 Why "max across epochs" not "mean"

YCSB workloads vary epoch-to-epoch as the index warms up and cache eviction
kicks in. The published CHIME numbers are peaks. To stay comparable to the
paper, we use the same statistic. The §4 long-run experiment shows the
post-warmup steady state is tight to <0.3% — so for our data the peak is
within a percent of the mean of post-warmup epochs anyway.

## 4. Per-experiment configuration

### 4.1 Memory pool sizing

CHIME's `kPoolSize` is `64 GB` per CN (controlled by `dsmSize` in
`include/Common.h`). The CXL transport mmap's the full pool with
`MAP_HUGETLB | MPOL_BIND` to NUMA node 1. Hugepage budget on each node:

- RDMA mode: `nr_hugepages` on node1 = 36864 (= 72 GB), node0 = 0. CHIME's
  `hugePageAlloc` sets `numa_set_preferred(1)` so all hugepages come from
  node1.
- CXL mode: same layout. The CXL pool needs ~32768 hugepages × 2 MB; node1's
  36864 covers it with margin.

Setting hugepages requires root: `echo 36864 | sudo tee
/sys/devices/system/node/node1/hugepages/hugepages-2048kB/nr_hugepages`.

### 4.2 RoCE/RDMA fixes

ConnectX-6 Dx on r650 Clemson requires:

1. `MAX_ATOMIC_ARG=8` in `/etc/modprobe.d/mlx5_core.conf` to avoid `errno 95
   ENOTSUP` on QP creation. (NOTE: we discovered this option is *not*
   recognized by the stock Ubuntu 20.04 kernel's mlx5_core; only the MLNX
   OFED kernel package recognizes it. With `--user-space-only` install we
   actually rely on `openibd restart` re-initializing the firmware caps,
   not on this option.)
2. `device_cap_flags` must be non-zero. After OFED userspace install the
   kernel module's caps are initialized to `0x00000000` until the IB stack
   is restarted. `sudo /etc/init.d/openibd restart` re-initializes them to
   `0xe5721c36` (or similar non-zero value) by reloading mlx5_ib and
   re-querying the device. **Caveat:** on r650 Clemson on May 2-3, four out
   of five `openibd restart` attempts left the node permanently unreachable
   (network-dead). The May-1-tested machines (clnode257, clnode263) survived
   restart on May 1; the same machines did not survive on May 2. We do not
   yet know the cause.
3. `max_recv_sge=2` for UD QPs (set in CHIME's `RawMessageConnection.cpp`).

### 4.3 memcached coordination

CHIME nodes find each other via memcached. We launch memcached on the master
node bound to the internal IP:

```
memcached -u root -l 10.10.1.1 -p 11211 -c 10000 -d -P /tmp/memcached.pid
```

Then initialize the registration counters:

```
printf 'set serverNum 0 0 1\r\n0\r\nquit\r\n' | nc 10.10.1.1 11211
printf 'set clientNum 0 0 1\r\n0\r\nquit\r\n' | nc 10.10.1.1 11211
```

The `memcached.conf` file at `/proj/cs620426sp-PG0/djjay-build/memcached.conf`
contains the host (line 1) and port (line 2). Each ycsb_test invocation reads
`../memcached.conf` from its build directory's parent.

### 4.4 SSH key distribution

On each fresh experiment, distribute keys *inline* (not via the buggy
`prep-experiment.sh` loop):

```
PUB=$(ssh master "test -f ~/.ssh/id_rsa || ssh-keygen -t rsa -N '' -f ~/.ssh/id_rsa -q; cat ~/.ssh/id_rsa.pub")
for n in node1 node2 node3; do
  ssh -o StrictHostKeyChecking=no $n.cs620426sp-PG0.clemson.cloudlab.us "echo '$PUB' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
done
```

### 4.5 Bootstrap order on a fresh node

Each freshly-provisioned r650 Clemson node runs `bootstrap-node.sh` from
`script/`, which:

1. Writes `options mlx5_core MAX_ATOMIC_ARG=8` to `/etc/modprobe.d/mlx5_core.conf`
   (no-op on stock kernel, harmless).
2. Installs MLNX OFED user-space from `/proj/cs620426sp-PG0/djjay-tmp/ofed/`
   if not already present (`ofed_info -s` check).
3. Apt-installs runtime libs: `memcached libmemcached-dev libtbb-dev
   libnuma-dev libboost-all-dev libgflags-dev cmake libgoogle-perftools-dev`.
4. Builds `cityhash` from source if `/usr/local/lib/libcityhash.so` is missing.
5. Sets hugepages: 0 on node0, 36864 on node1.

After bootstrap completes, the *only* remaining setup step is the firmware
caps fix (§4.2). On May 6 we will run `openibd restart` sequentially per node
with a 5-minute SSH-recovery wait, accepting that some r650 nodes may not
recover (the r650 Clemson firmware-state issue is reproducible but not
understood).

## 5. Variance protocol

For headline findings (speculative-read net negative), we collected at least
20 reps per cell to ensure the gap-to-noise ratio is comfortably above $5\sigma$.
Reps are independent ycsb_test invocations on the same CXL build, run
sequentially with a 1-second sleep between them. We do not flush memcached
between reps because each ycsb_test loads its own dataset into a fresh
mmap'd region — there is no shared state to flush. We do flush memcached
between RDMA reps (§4.3) because the serverNum/clientNum counters need to
restart at 0.

We report mean and standard deviation per cell. Outliers (a non-zero rep
with $|x - \bar{x}| > 3\sigma$) are kept in the dataset but flagged in the
per-experiment notes; we do not re-run them. There were 4 such outliers in
the entire May 3 sprint, all on workload E at high thread counts where the
range-scan timing is genuinely noisier.

For long-run steady-state stability (one experiment, all epochs of one run),
we read every `cluster throughput` line and report the post-warmup mean
and standard deviation across epochs 2-10 of a single run.

## 6. Lessons-learned that are also methodology

These are gotchas that would have invalidated results if not caught:

1. **mlx5_core drives both NICs.** `openibd restart` reloads mlx5_core, which
   takes down `eno12399` (the public NIC) at the same time as the RDMA NIC.
   On most r650 nodes this is a transient SSH blip; on r650 Clemson
   May 2-3 it permanently bricked 5/8 nodes attempted. We avoid `openibd
   restart` over a connected SSH session unless we are willing to lose the
   node, and we always do it sequentially across the cluster (one node at
   a time) so we can fall back if one bricks.
2. **`update-initramfs -u` corrupts boot on r650 Clemson.** On May 2 we wrote
   the modprobe option and ran `update-initramfs -u` to make it stick across
   reboots. The next reboot took the node permanently out. We removed
   `update-initramfs` from the bootstrap script and accept that the modprobe
   option is only honored if mlx5_core is reloaded post-boot.
3. **CloudLab control-net traffic budget.** On May 1 we ssh-polled the master
   for sweep status every 60-180s for ~10 hours and triggered a CloudLab
   admin email about unusual control-network traffic. Mitigation: we now
   write progress to `/proj/.../heartbeat.txt` on the master and pull the
   whole results directory once per ~29 min via a single `scp -r`, plus a
   per-node `control-net-guard.sh` that aborts the experiment if cumulative
   public traffic exceeds 500 MB.
4. **The CloudLab portal API auth tier hangs unpredictably.** On May 3 the
   `boss.emulab.net:43794` API was up at the network layer but every
   authenticated endpoint timed out. Public endpoints (`/`, `/openapi.json`)
   responded fast. We do not depend on the API for in-experiment work — we
   use SSH after provision; the API is only needed to create / extend /
   terminate, and only in those moments do we check it.
5. **CloudLab UI "ready" status is not the same as SSH-reachable.** A node
   marked ready can be unreachable; conversely a node can be SSH-reachable
   while the UI status lags. We always probe SSH directly before declaring
   a node usable.
6. **Workload A and B trigger a CHIME-internal assertion at single-CN.** We
   confirmed that CHIME-CXL on workloads A and B crashes at
   `Tree.cpp:1596 j != (int)define::neighborSize` regardless of transport at
   single-CN. The crash is not transport-related; we excluded A and B from
   single-CN evaluation and document them as a separate finding.

## 7. Result file conventions

Each result file in `exp/results/may2-24h/` is JSONL with the following
columns (some optional):

```
{"variant":"chime","method":"CHIME-CXL","workload":"c","threads":16,"rep":1,
 "coro":1,"runtime_s":90,"peak_mops":6.731,"err_tail":"…"}
```

The combination of `variant`, `method`, `workload`, `threads`, `coro` (default
1), and `rep` uniquely identifies a measurement. `peak_mops` is the
peak-across-epochs in megaoperations per second. A `peak_mops` of `0.0` means
the measurement aborted (segfault, OOM, assertion). We retain those rows so
the reader can see the failure rate.

Files are named `pNN_<short_description>.jsonl` with NN incrementing by the
order in which experiments were dispatched. The `runner.log` and
`heartbeat.txt` files document the dispatch timeline.

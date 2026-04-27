# Tech Context

## Languages and Versions

- **C++17** — index and benchmark code (`src/`, `include/`, `test/`)
- **CMake 3.10.2+** — build system with extensive compile-time feature flags
- **Python 3** — experiment orchestration (`exp/`), workload generation (`ycsb/`)
- **Paramiko** — SSH-based remote command execution from experiment scripts
- **memcached** — coordination service for node discovery
- **RDMA (libibverbs)** — data plane; requires Mellanox OFED and ConnectX NICs

## Key Dependencies (linked at build time)

`-lnuma -lcityhash -lboost_coroutine -lboost_context -lpthread -libverbs -lmemcached -ltbb`

CXL mode (`USE_CXL`): drops `-libverbs -lmemcached -lboost_coroutine -lboost_context`, adds `-latomic`

## Build and Run

```bash
# Standard RDMA build (all nodes):
mkdir build && cd build && cmake .. && make -j

# CXL build (single node):
mkdir build && cd build && cmake -DUSE_CXL=ON .. && make -j

# On memory node only:
/bin/bash ../script/restartMemc.sh

# On all nodes (split workloads):
python3 ../ycsb/split_workload.py <workload> randint <CN_num> <clients_per_CN>

# On all nodes (run benchmark):
./ycsb_test <CN_num> <clients_per_CN> <coro_per_client> randint <workload>
```

Hugepages must be set before each run: `echo 36864 > /proc/sys/vm/nr_hugepages && ulimit -l unlimited`

## CMake Feature Flags

Core CHIME features (all ON = full CHIME, selectively OFF = baselines for fig_15):
- `HOPSCOTCH_LEAF_NODE`, `VACANCY_AWARE_LOCK`, `METADATA_REPLICATION`
- `SIBLING_BASED_VALIDATION`, `SPECULATIVE_READ`

Environment flags: `ENABLE_CACHE`, `ENABLE_CACHE_EVICTION`, `ENABLE_CORO`
Optimization flags: `READ_DELEGATION`, `WRITE_COMBINING`, `CACHE_MORE_INTERNAL_NODE`
Test epoch flags: `SHORT_TEST_EPOCH`, `MIDDLE_TEST_EPOCH`, `LONG_TEST_EPOCH`
Transport flag: `USE_CXL` — switches DSM to CxlDSM (NUMA-emulated CXL)

## CloudLab Hardware

### r650 (target, paper-matched)
- Intel Xeon (2x 36-core, 72 physical cores), 256 GB DRAM, ConnectX-6 100 Gbps
- Setup: `script/installMLNX.sh`, `script/installLibs.sh`
- **Internal LAN required** — RDMA on control net triggers CloudLab quarantine
- Profile `chime-r650-clemson-lan` (parameterized: n=node count, hw=r650/r6525) creates nodes with VLAN on ens2f0

### r650 RoCE Configuration (6 required fixes)
1. `IB_DEV_NAME_IDX '2'` — mlx5_2 on ens2f0 (the VLAN parent NIC, not mlx5_0 on eno12399)
2. `IBV_MTU IBV_MTU_1024` — RoCE requires smaller MTU than InfiniBand
3. `MLX_GID 3` — RoCE v2 GID index for VLAN interface (not 1, which is ens2f0 link-local)
4. `attr->grh.hop_limit = 64` — required for RoCE routing
5. `CPU_PHYSICAL_CORE_NUM 72` — match r650 hardware
6. VLAN setup: `sudo /usr/local/etc/emulab/rc/rc.ifconfig` on each node after boot
7. memcached.conf: 2 lines — IP on line 1, port (11211) on line 2

### r6525 (pre-deadline alternative)
- AMD EPYC (2x 32-core, 128 CPUs), ConnectX-5 + ConnectX-6 Dx
- `CPU_PHYSICAL_CORE_NUM=64` (vs 72 on r650)
- Root partition 16GB only — use NVMe (`/mnt/nvme`, 1.5TB) or project NFS
- `ibv_exp_dct` confirmed working

### Workload Storage
- YCSB workloads on project NFS: `/proj/cs620426sp-PG0/ycsb_workloads/`
- Symlink `~/CHIME/ycsb/workloads` → NFS path for cross-experiment reuse
- YCSB 0.17.0 uses `site.ycsb` package (not `com.yahoo.ycsb`)
- Standard workloads (a, b, c, d, e, la) available; 60M-120M scaled workloads missing

## Infrastructure

- **`portal-tools` XML-RPC CLI** (PEM client cert auth) — primary path used today: `createReservation`, `startExperiment`, `experimentStatus`, `experimentManifests`, `terminateExperiment`. Decrypted PEM at `~/.ssl/emulab.pem` (auto-loaded). Encrypted copy at `files/cloudlab.pem`. Wrapper source: `~/Library/Python/3.9/lib/python/site-packages/emulab_sslxmlrpc/client/api.py`.
- **CloudLab JWT** (`files/cloudlab.jwt`, exp 2027-12) — for the REST/web layer (`boss.emulab.net:43794`, `x-api-token` header). Cookie-based on the web UI; cannot be used as Bearer token against `www.cloudlab.us/portal/...` paths.
- **Known server-side bugs**:
  - `reservationStatus <uuid>` returns `Undefined subroutine &main::DoStatus called at /usr/testbed/bin/manage_resgroup line 208`. No client-side workaround.
  - Scheduler may report "0 available because of existing resource reservations to other projects or users" even when the user has approved reservations — root cause not yet diagnosed (project/cluster/hw-type mismatch suspected).
- **Profile**: `chime-r650-clemson-lan` (project `CS620426SP`), parameterized: `n` (node count), `hw` (`r650` / `r6525`). Cluster is pinned in the profile, not via bindings.
- **Local tools constraint** (per user feedback): use Docker-based environments for build/preflight, not Homebrew. See `Dockerfile.cxl-preflight`.
- GitHub Pages: Hugo site + LaTeX report CI
- Sibling repos needed at same level: SMART (`dmemsys/SMART`), ROLEX (`River861/ROLEX`), Marlin (`River861/Marlin`)

## Experiment Param Files

- `exp/params/common.json` — cluster IPs, home dir, CMake flags (regenerated per run)
- `exp/params/fig_12.json` — full fig_12 config (6 workloads, 5 methods, 8 thread counts)
- `exp/params/fig_12_remaining.json` — only A, B, E, LOAD (skips completed C, D)
- `exp/params/fig_12_remaining_3cn.json` — same scope, scaled for 3 CN
- `exp/params/fig_*_cxl.json` — CXL experiment configs (1 node, no CN count)
- `exp/params/fig_12_rdma_2cn.json` — single-node RDMA baseline for CXL comparison

## Pre-Hardware Tooling (Apr 22–23)

- **`Dockerfile.cxl-preflight`** — Ubuntu 20.04 amd64; deps: `cmake`, `libnuma-dev`, `libtbb-dev`, `libboost-coroutine-dev`, `libibverbs-dev`, `libmemcached-dev`. cityhash built from source with `--build=$(gcc -dumpmachine)`. **CXL-only**; RDMA build needs MLNX OFED `ibv_exp_dct` and cannot run in stock Docker.
- **`exp/run_harness.py`** — wraps `ycsb_test` invocations. On crash/timeout, captures: core dump, full stderr, git SHA, CMakeCache, `include/Common.h`, hostname, `/proc/sys/vm/nr_hugepages`. Tests in `exp/tests/test_run_harness.py` (8/8 pass).
- **`exp/fig_14_surrogate.py`** — single-point cache-consumption driver for 60M keys. Parses `[stats] key = N` lines from ycsb_test stderr. Tests in `exp/tests/test_fig_14_surrogate.py` (5/5 pass).
- **`exp/plot_fig_12_three_way.py`** — multi-series throughput-latency plot for multi-node RDMA + single-node RDMA + CXL. Tests in `exp/tests/test_plot_fig_12_three_way.py` (5/5 pass).
- **`construction/scripts/runbook-day1.md`** — exact T+0:00..T+7:30 commands for a hardware window.
- **`construction/scripts/smoke-gate.sh`** — automated PASS/FAIL CXL gate: 5s YCSB LOAD (CAS/alloc) + 30s YCSB C (reads).

Last updated: 2026-04-26

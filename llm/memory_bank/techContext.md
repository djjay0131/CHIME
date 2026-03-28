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

## Build and Run

```bash
# On all nodes:
mkdir build && cd build && cmake .. && make -j

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

## CloudLab Hardware

### r650 (target, paper-matched)
- Intel Xeon (2x 36-core), 256 GB DRAM, ConnectX-6 100 Gbps
- Setup: `script/installMLNX.sh`, `script/resizePartition.sh`, `script/installLibs.sh`

### r6525 (pre-deadline alternative)
- AMD EPYC (2x 32-core, 128 CPUs), ConnectX-5 + ConnectX-6 Dx
- `CPU_PHYSICAL_CORE_NUM=64` (vs 36 on r650)
- Root partition 16GB only — use NVMe (`/mnt/nvme`, 1.5TB) or project NFS
- No internal 10.x network — `memcached.conf` must use public IPs
- `ibv_exp_dct` confirmed working

### Workload Storage
- YCSB workloads on project NFS: `/proj/cs620426sp-PG0/ycsb_workloads/`
- Symlink `~/CHIME/ycsb/workloads` → NFS path for cross-experiment reuse
- YCSB 0.17.0 uses `site.ycsb` package (not `com.yahoo.ycsb`)

## Infrastructure

- CloudLab API: `boss.emulab.net:43794`, JWT token at `files/cloudlab.jwt`
- CLI: `portal-cli` from `portal-api` (gitlab)
- GitHub Pages: LaTeX report CI
- Sibling repos needed at same level: SMART (`dmemsys/SMART`), ROLEX (`River861/ROLEX`)

Last updated: 2026-03-26

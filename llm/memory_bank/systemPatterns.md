# System Patterns

## Architecture: Six Layers

1. **Compile-time configuration** — `CMakeLists.txt` flags + `include/Common.h` constants
2. **DSM and communication (RDMA)** — `include/DSM.h`, `src/DSM.cpp`, `src/rdma/`, `include/Directory.h`
3. **DSM and communication (CXL)** — `include/CxlDSM.h`, `src/CxlDSM.cpp`, `include/CxlTransport.h`, `src/CxlTransport.cpp`
4. **Index implementation** — `include/Tree.h`, `src/Tree.cpp`, `include/InternalNode.h`, `include/LeafNode.h`
5. **Benchmark executables** — `test/ycsb_test.cpp` (main), plus hash/zipf test files
6. **Experiment orchestration** — `exp/*.py` scripts, `exp/params/`, `exp/utils/`

## Directory Structure

```
include/          # Headers: Tree, DSM, CxlDSM, CxlTransport, nodes, cache, config, RDMA types
src/              # Implementation: Tree.cpp, DSM.cpp, CxlDSM.cpp, CxlTransport.cpp, rdma/
test/             # Benchmark entry points (ycsb_test.cpp is primary)
exp/              # Python experiment scripts (one per figure)
  params/         # JSON configs (common.json, fig_*.json, fig_*_cxl.json)
  utils/          # cmd_manager.py, log_parser.py, sed_common.py
  styles/         # Matplotlib styles
script/           # Shell setup scripts (install, hugepages, memcached)
ycsb/             # Workload generation and splitting
construction/     # Project management (design docs, sprints, scripts)
  design/         # Design specifications
  sprints/        # Sprint plans
  scripts/        # Automation helpers (setup-r650.sh, generate-common-json.py, etc.)
llm/              # LLM memory bank and feature specs
  memory_bank/    # 5 core knowledge files + architectural decisions
  features/       # Feature specifications (cxl-implementation.md, etc.)
report/           # LaTeX report source
presentation/     # Beamer presentation source
site/             # Hugo site for GitHub Pages
cloudlab/         # CloudLab profile scripts
.claude/          # Claude Code agents, skills, project config
```

## Pattern: Compile-Time Experiment Reconfiguration

Experiment scripts don't just pass runtime args — they `sed`-rewrite constants in `include/Common.h` (via `exp/utils/sed_common.py`) and rebuild binaries. Each figure sweep is effectively a sweep over differently-compiled systems. Key constants: `kLeafCardinality`, `kInternalCardinality`, `kMaxCacheSize`, `kMaxHandOverNum`.

## Pattern: Benchmarks as Operational Entry Points

`test/ycsb_test.cpp` is not a unit test — it's the main benchmark binary invoked by all experiment scripts. It reads memcached for node discovery, loads/runs YCSB workloads, and emits throughput/latency metrics.

## Pattern: Python Controls, C++ Executes

Python layer (`exp/`): edits configs, SSHs into cluster nodes via Paramiko, fans out build/run commands, collects logs, parses metrics with `log_parser.py`, renders matplotlib figures.

C++ layer: stores/accesses the distributed index, performs RDMA operations, emits raw metrics to stdout/files that Python parses.

## Pattern: Multi-Method Comparison via Sibling Repos

Competitor methods (Sherman, SMART, ROLEX) live in sibling directories at the same level as CHIME. They share the same harness layout (`include/Common.h`, `test/ycsb_test.cpp`, `script/restartMemc.sh`). Experiment scripts `cd` into each repo, rebuild with method-specific CMake flags, and run the same benchmark binary.

## Pattern: Feature Flag Families

CMake flags group into families matching paper concepts:
- **Core CHIME features**: HOPSCOTCH_LEAF_NODE → VACANCY_AWARE_LOCK → METADATA_REPLICATION → SIBLING_BASED_VALIDATION → SPECULATIVE_READ (cumulative, fig_15)
- **Cache/eviction**: ENABLE_CACHE, ENABLE_CACHE_EVICTION
- **Optimizations**: READ_DELEGATION, WRITE_COMBINING, CACHE_MORE_INTERNAL_NODE
- **Range queries**: FINE_GRAINED_RANGE_QUERY, GREEDY_RANGE_QUERY

## Pattern: CXL Transport Substitution

When `USE_CXL` is defined at compile time, `DSM.h` conditionally includes `CxlDSM.h` which `#define DSM CxlDSM`. This makes `CxlDSM` a transparent drop-in for `DSM` — no changes to Tree.cpp or ycsb_test.cpp. CxlDSM delegates to CxlTransport which uses NUMA node 1 mmap'd memory to emulate remote CXL-attached memory. All operations are synchronous (no coroutines, no RDMA CQ polling).

## Pattern: VLAN Interface Activation

CloudLab assigns VLAN IDs per experiment (vlan285, vlan293, etc.) but doesn't always bring the interface up automatically. Each node must run `sudo /usr/local/etc/emulab/rc/rc.ifconfig` after boot to create the VLAN interface on ens2f0. The internal LAN IPs (10.10.1.x) are defined in the profile and appear in `/etc/hosts`, but the actual network interface needs this manual activation step.

## Pattern: RoCE Fix Application

Six fixes must be applied to every repo (CHIME, SMART, ROLEX) on every node before building. These are sed-applied to `include/Rdma.h`, `src/rdma/Resource.cpp`, and `include/Common.h`. The fixes are idempotent and order-independent. The `setup-r650.sh` script applies these automatically in Phase 4.

## Pattern: CloudLab API Automation

Experiment lifecycle is fully automated via the REST API at `boss.emulab.net:43794`:
1. `POST /experiments/` to create (with profile bindings for node count)
2. Poll `GET /experiments/{id}/node/nodeN` until all show `status: ready`
3. `GET /experiments/{id}/manifests` to extract hostnames and internal IPs from XML
4. `PUT /experiments/{id}` with `extend_by` to add hours (subject to availability)
5. `POST /resgroups/search?duration=N` to find next available time slot

## Pattern: Incremental Experiment Resumption

When fig_12 can't complete in a single experiment window, use `fig_12_remaining.json` to skip already-collected workloads. The experiment scripts save per-workload `_partial.json` files incrementally, and complete workloads get a final `.json`. Pull results after each workload completes, not on a timer.

## Pattern: Off-Hardware Docker Preflight

CXL builds are validated end-to-end inside `Dockerfile.cxl-preflight` (Ubuntu 20.04 amd64) before consuming reservation time. The container catches build-system blockers (missing headers, conditional-compile path issues, transitively-broken includes) that don't surface until link time. Each fix is committed separately so a failed cluster build can be diff-bisected against the last known-good Docker preflight. RDMA builds skip this gate (need MLNX OFED `ibv_exp_*`).

## Pattern: Debug-Artifact Capture Wrapper

`exp/run_harness.py` wraps `ycsb_test` invocations with timeout enforcement and post-mortem capture. On non-zero exit or timeout, it copies stderr/stdout, any core dump, the current git SHA, CMakeCache, `include/Common.h`, hostname, and hugepage state into a per-invocation debug directory. This makes a failed cluster run reproducible offline without requiring live debugging on the reservation clock.

## Pattern: CloudLab Reservation Failure Modes

The `startExperiment` failure message `0 available because of existing resource reservations to other projects or users` is misleading. It fires when:
1. The user has an approved reservation but the project/cluster/hardware-type tuple doesn't match the experiment's profile (most common).
2. The reservation hasn't started yet (start time in the future).
3. The reservation actually was filed for "other projects or users" (i.e., user has no relevant hold).

`reservationStatus <uuid>` is currently broken server-side (`Undefined subroutine &main::DoStatus`), so the standard CLI diagnostic path is unavailable. Indirect signal: `createReservation -n` dry-run returns `nbd: <date>` for the next available start — if that date is far in the future, capacity IS held by someone, but doesn't tell you whom.

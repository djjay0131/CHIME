# System Patterns

## Architecture: Five Layers

1. **Compile-time configuration** — `CMakeLists.txt` flags + `include/Common.h` constants
2. **DSM and communication** — `include/DSM.h`, `src/DSM.cpp`, `src/rdma/`, `include/Directory.h`
3. **Index implementation** — `include/Tree.h`, `src/Tree.cpp`, `include/InternalNode.h`, `include/LeafNode.h`
4. **Benchmark executables** — `test/ycsb_test.cpp` (main), plus hash/zipf test files
5. **Experiment orchestration** — `exp/*.py` scripts, `exp/params/`, `exp/utils/`

## Directory Structure

```
include/          # Headers: Tree, DSM, nodes, cache, config, RDMA types
src/              # Implementation: Tree.cpp, DSM.cpp, rdma/
test/             # Benchmark entry points (ycsb_test.cpp is primary)
exp/              # Python experiment scripts (one per figure)
  params/         # JSON configs (common.json, fig_*.json)
  utils/          # cmd_manager.py, log_parser.py, sed_common.py
  styles/         # Matplotlib styles
script/           # Shell setup scripts (install, hugepages, memcached)
ycsb/             # Workload generation and splitting
construction/     # Project management (design docs, sprints, scripts)
  design/         # Design specifications
  sprints/        # Sprint plans
  scripts/        # Automation helpers
memory-bank/      # Legacy (migrated to llm/memory_bank/)
llm/              # LLM memory bank and feature specs
report/           # LaTeX report source
presentation/     # Beamer presentation source
```

## Pattern: Compile-Time Experiment Reconfiguration

Experiment scripts don't just pass runtime args — they `sed`-rewrite constants in `include/Common.h` (via `exp/utils/sed_common.py`) and rebuild binaries. Each figure sweep is effectively a sweep over differently-compiled systems. Key constants: `kLeafCardinality`, `kInternalCardinality`, `kMaxCacheSize`, `kMaxHandOverNum`.

## Pattern: Benchmarks as Operational Entry Points

`test/ycsb_test.cpp` is not a unit test — it's the main benchmark binary invoked by all experiment scripts. It reads memcached for node discovery, loads/runs YCSB workloads, and emits throughput/latency metrics.

## Pattern: Python Controls, C++ Executes

Python layer (`exp/`): edits configs, SSHs into cluster nodes via Paramiko, fans out build/run commands, collects logs, parses metrics with `log_parser.py`, renders matplotlib figures.

C++ layer: stores/accesses the distributed index, performs RDMA operations, emits raw metrics to stdout/files that Python parses.

## Pattern: Multi-Method Comparison via Sibling Repos

Competitor methods (Sherman, SMART, ROLEX, Marlin) live in sibling directories at the same level as CHIME. They share the same harness layout (`include/Common.h`, `test/ycsb_test.cpp`, `script/restartMemc.sh`). Experiment scripts `cd` into each repo, rebuild with method-specific CMake flags, and run the same benchmark binary.

## Pattern: Feature Flag Families

CMake flags group into families matching paper concepts:
- **Core CHIME features**: HOPSCOTCH_LEAF_NODE → VACANCY_AWARE_LOCK → METADATA_REPLICATION → SIBLING_BASED_VALIDATION → SPECULATIVE_READ (cumulative, fig_15)
- **Cache/eviction**: ENABLE_CACHE, ENABLE_CACHE_EVICTION
- **Optimizations**: READ_DELEGATION, WRITE_COMBINING, CACHE_MORE_INTERNAL_NODE
- **Range queries**: FINE_GRAINED_RANGE_QUERY, GREEDY_RANGE_QUERY

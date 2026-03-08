# CHIME Codebase Guide

## What This Repository Contains

CHIME is an RDMA-backed distributed-memory index. The repository is split between:

- C++ runtime and data-structure code in `include/` and `src/`
- benchmark entrypoints in `test/`
- experiment orchestration and plotting in `exp/`
- workload generation utilities in `ycsb/`
- machine setup scripts in `script/`

The core idea reflected in the code is a B+ tree style index whose leaf behavior is extended with hopscotch hashing and several cache/validation optimizations.

## Fast Orientation

If you are trying to understand behavior end to end, read files in this order:

1. `CMakeLists.txt`
2. `include/Common.h`
3. `include/Tree.h`
4. `src/Tree.cpp`
5. `test/ycsb_test.cpp`
6. `exp/fig_03a.py`
7. `exp/utils/`

That path takes you from build flags, to compile-time constants, to the main index API, to the benchmark harness, and finally to the paper reproduction scripts.

## Build and Feature Model

`CMakeLists.txt` compiles all `src/*.cpp` files into a static `CHIME` library and then links every file in `test/` as a standalone executable.

Two layers of configuration matter:

- CMake options: enable or disable whole features such as cache usage, coroutines, speculative read, hopscotch leaves, and range-query modes.
- `include/Common.h`: sets fixed constants such as key size, value size, cache size, memory-node count, and leaf span.

This is important because the experiment scripts mutate `include/Common.h` with `sed` and rebuild variants repeatedly. In other words, some "runtime" experiment parameters are actually compile-time parameters.

## Core Runtime Components

### `include/Common.h`

Defines global constants and layout decisions:

- machine and coroutine limits
- key and value sizes
- cache sizes
- leaf/internal node sizing
- hopscotch neighborhood sizing
- RDMA transfer and allocation sizes

If a result changes when the paper varies cache size, amplification factor, or neighbor size, this file is usually involved.

### `include/Tree.h` and `src/Tree.cpp`

This is the main index implementation.

Key responsibilities:

- public operations: `insert`, `update`, `search`, `range_query`
- coroutine-driven execution via `run_coroutine`
- root lookup and traversal
- local locking and remote lock state updates
- cache accounting and internal-node caching
- leaf search/insert/update logic
- split handling
- hopscotch-specific leaf operations
- speculative-read and sibling-validation paths

The constructor also initializes the root leaf on node 0 and installs the root pointer in distributed memory.

### `DSM`, `Directory`, and connection classes

The files `include/DSM.h`, `include/Directory*.h`, `include/*Connection.h`, and matching files under `src/` implement the distributed shared memory substrate and communication layer. They provide remote allocation, RDMA reads/writes/CAS, and node/thread registration.

You do not need to read all of these to follow the experiments, but you do need to know that `Tree` is built on top of this DSM abstraction rather than local memory alone.

### `test/ycsb_test.cpp`

This is the main benchmark executable used by the experiment scripts.

It:

- loads YCSB load and transaction files
- creates per-thread request arrays
- performs warmup and synchronization across nodes
- runs the selected operations against `Tree`
- prints throughput and internal metrics parsed later by Python

When experiment scripts call `./ycsb_test ...`, this file is the entrypoint doing the real work.

## Experiment Pipeline

The `exp/` directory is a controller layer around the C++ binaries.

Important pieces:

- `exp/params/common.json`: cluster IPs, home directory, workload path, and per-system CMake option sets
- `exp/params/fig_*.json`: figure-specific experiment settings
- `exp/utils/cmd_manager.py`: SSH fan-out to all cluster nodes with retries and long-running log capture
- `exp/utils/sed_generator.py`: generates `sed` commands that rewrite compile-time constants in `include/Common.h`
- `exp/utils/log_parser.py`: extracts throughput, cache, lock, and validation statistics from benchmark output
- `exp/utils/pic_generator.py`: renders the final figure after JSON data is produced

## Walkthrough: `exp/fig_03a.py`

`fig_03a.py` is a good example of the house style for these experiments.

The control flow is:

1. Load shared cluster settings from `exp/params/common.json`.
2. Load figure-specific settings from `exp/params/fig_03a.json`.
3. For each method variant and amplification setting:
4. Rewrite `workloads.conf` and `include/Common.h`.
5. Reconfigure and rebuild the target project on all nodes.
6. Restart memcached on the master node.
7. Split YCSB workloads across compute nodes.
8. Run `ycsb_test` remotely and collect logs.
9. Parse consumed cache size from the logs.
10. Save JSON results and generate the figure.

Two details are easy to miss:

- The script compares multiple repositories, not just this one. For `Sherman` it points back to `CHIME`; other methods expect sibling repositories such as `SMART` and `ROLEX` in the same parent directory.
- "Amplification factor" is translated into different compile-time constants per method before each rebuild.

## How To Read One Experiment Safely

When documenting or modifying one figure script, confirm these four things:

1. Which JSON file defines the figure parameters.
2. Which compile-time constants are rewritten by `sed_generator.py`.
3. Which binary is eventually executed on the nodes.
4. Which parser method extracts the metric shown in the figure.

If any of those are unclear, it is easy to misread a figure as a runtime-only change when it is actually a rebuild of a different binary configuration.

## Practical Mental Model

Use this model when reasoning about CHIME:

- `Common.h` chooses the physical shape of data and buffers.
- CMake options choose which algorithmic features exist in the binary.
- `Tree` implements the index operations over DSM.
- `ycsb_test` drives the workload and prints metrics.
- `exp/*.py` automates rebuilds, distributed execution, parsing, and plotting.

That is the shortest accurate path from paper figure to implementation.

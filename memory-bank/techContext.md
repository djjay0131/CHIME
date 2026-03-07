# Tech Context

## Languages and Tooling

- C++17 for the index and benchmark code
- CMake for builds
- Python for experiment automation and plotting
- Paramiko for remote command execution
- memcached and RDMA stack for the artifact environment

## Important Files

- `CMakeLists.txt`: feature flags and executable generation
- `include/Common.h`: compile-time constants and memory/layout parameters
- `include/Tree.h`, `src/Tree.cpp`: main index logic
- `test/ycsb_test.cpp`: benchmark harness
- `exp/params/common.json`: shared experiment settings
- `exp/utils/`: orchestration helpers

## Constraints

- The artifact is tuned for CloudLab r650 nodes.
- Several experiments assume sibling repositories such as `SMART` and `ROLEX` exist beside `CHIME`.
- Some scripts edit source headers in place before rebuilding.
- Long-running experiments require remote coordination across multiple machines.

## Documentation Caveat

When explaining behavior, distinguish clearly between:

- settings changed by command-line arguments
- settings changed by JSON inputs
- settings changed by source rewrites plus rebuilds

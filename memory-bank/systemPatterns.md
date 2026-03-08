# System Patterns

## Layered Structure

CHIME is easiest to understand as five layers:

1. Compile-time configuration
2. DSM and communication substrate
3. Tree/index implementation
4. Benchmark executables
5. Experiment orchestration and plotting

## Pattern: Compile-Time Experiment Reconfiguration

The experiment scripts do not only pass runtime arguments. They also rewrite constants in `include/Common.h` and rebuild binaries. That means many figure sweeps are effectively sweeps over different compiled systems.

## Pattern: Benchmarks As Real Entry Points

The code under `test/` is not only unit-style testing. Files such as `test/ycsb_test.cpp` are operational entrypoints used by the experiment scripts.

## Pattern: Python Controls, C++ Executes

The Python layer:

- edits config files
- fans commands out across cluster nodes
- collects logs
- parses metrics
- renders figures

The C++ layer:

- stores and accesses the distributed index
- performs benchmark operations
- emits the raw metrics the Python layer consumes

## Pattern: Feature Families

Important feature toggles appear in groups:

- cache and cache-eviction flags
- hopscotch leaf and vacancy-aware lock flags
- metadata replication and sibling validation flags
- speculative read flags
- range-query mode flags

These toggles are the main bridge between paper concepts and build artifacts.

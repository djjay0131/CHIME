# Product Context

## Why This Repository Exists

This repository is the artifact for the SOSP'24 CHIME paper. Its practical uses are:

- reproducing published experiments
- serving as the implementation reference for the paper
- enabling further systems research on distributed-memory indexing

## Users

- researchers reproducing results
- maintainers making small targeted changes
- readers trying to connect paper claims to implementation details

## Documentation Need

The repository already explains setup and reproduction, but the internal code flow is harder to learn quickly. The documentation added here closes that gap by mapping:

- build flags to features
- C++ runtime code to benchmark entrypoints
- experiment scripts to the binaries and metrics they control

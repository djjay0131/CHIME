# Competitor Repo Compatibility Notes

**Created:** 2026-03-07
**Purpose:** Document whether SMART and ROLEX repos are compatible with CHIME's experiment harness

---

## Summary

| Repo | Compatible? | Notes |
|------|-------------|-------|
| **Sherman** | YES - same repo | Uses CHIME repo with different CMake flags. `fig_12.py` line 66: `project_dir = "CHIME" if method == "Sherman"` |
| **SMART** | YES - same harness layout | Has identical directory structure: `include/Common.h`, `test/ycsb_test.cpp`, `script/restartMemc.sh`, `CMakeLists.txt` |
| **ROLEX** (River861/ROLEX) | YES - CHIME-compatible reimplementation | Same harness layout. CHIME authors re-implemented ROLEX with their infrastructure. See `exp/README.md`. |
| **ROLEX** (iotlpf/ROLEX) | NO - original, incompatible | Different layout entirely. Do NOT use this repo. |

---

## SMART (dmemsys/SMART) - COMPATIBLE

Structure matches CHIME's harness exactly:

```
SMART/
  CMakeLists.txt          # same cmake structure
  include/Common.h        # same constants (MAX_MACHINE, MEMORY_NODE_NUM, etc.)
  test/ycsb_test.cpp      # same benchmark entry point
  script/
    cloudlab.profile      # same CloudLab profile
    installMLNX.sh        # same install scripts
    installLibs.sh
    resizePartition.sh
    restartMemc.sh        # required by fig_12.py line 82
  ycsb/                   # same workload tooling
  exp/                    # has its own experiment scripts
  us_lat/                 # latency output dir (referenced by fig_12.py line 94)
  workloads.conf          # rewritten by sed_generator
```

`Common.h` constants are in the same format (same #define names, same sed-rewritable patterns).

cmake_options from `common.json`:
```
"SMART": "-DENABLE_CACHE=on -DART_INDEXED_CACHE=on -DHOMOGENEOUS_INTERNAL_NODE=on -DLOCK_FREE_INTERNAL_NODE=on -DUPDATE_IN_PLACE_LEAF_NODE=on -DREAR_EMBEDDED_LOCK=on"
```

These flags are SMART-specific but the build system accepts them. **SMART should work out of the box with CHIME's experiment scripts.**

---

## ROLEX - RESOLVED

### Key Discovery

From `exp/README.md`:
> ROLEX (FAST'23) is the latest learned index on DM. We [re-implement it](https://github.com/River861/ROLEX) with [its open-source models](https://github.com/iotlpf/ROLEX).

The CHIME authors **re-implemented ROLEX** in their own harness at `https://github.com/River861/ROLEX`. The original `iotlpf/ROLEX` repo is incompatible.

### River861/ROLEX - COMPATIBLE

```
ROLEX/ (River861 reimplementation)
  CMakeLists.txt          # same cmake structure as CHIME/SMART
  include/Common.h        # same constants, same sed-rewritable format
  test/ycsb_test.cpp      # same benchmark entry point
  script/
    cloudlab.profile
    installMLNX.sh
    installLibs.sh
    resizePartition.sh
    restartMemc.sh
  us_lat/                 # latency output dir
  workloads.conf
```

### iotlpf/ROLEX - INCOMPATIBLE (original paper authors' code)

Completely different layout: `benchs/Rolex/rolex.cc`, no `include/Common.h`, no `test/`, different cmake, uses gflags/boost_coroutine. **Do NOT use this repo.**

### Fork Status

- We initially forked `iotlpf/ROLEX` to `djjay0131/ROLEX` - this is WRONG
- We need to fork `River861/ROLEX` instead
- The djjay0131/ROLEX fork should be deleted or renamed

---

## Impact on Timeline

- **SMART** (dmemsys/SMART): No extra work. Clone, configure IPs, run.
- **Sherman**: No extra work. Same repo as CHIME, different flags.
- **ROLEX** (River861/ROLEX): No extra work. Same harness layout as CHIME/SMART.
- **SMART-SC**: Just SMART with `cache_size=1000` (sufficient cache). No extra setup.

ALL four competitor methods are fully compatible with CHIME's experiment scripts. No adaptation work needed.

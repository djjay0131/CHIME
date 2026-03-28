# Feature: CXL Transport Backend for CHIME and Competitor Indexes

**Status:** SPECIFIED
**Date:** 2026-03-26
**Author:** Feature Architect (AI-assisted)

## Problem

CHIME and its four competitor indexes (Sherman, SMART, ROLEX, Marlin) are built entirely on RDMA one-sided operations for disaggregated memory. Part Two of the CS 6204 course project requires porting all five methods to CXL-based memory and producing comparative RDMA-vs-CXL performance analysis. The codebase has no transport abstraction — RDMA is hardwired throughout the DSM layer, and the coroutine-based async model is tightly coupled to RDMA completion semantics.

The port must use a clean abstraction layer (not a fork), emulate CXL via NUMA on CloudLab r650 dual-socket nodes, strip coroutines for realistic CXL performance, and produce figures with analysis explaining *why* performance differs.

## Goals

- Transport abstraction layer that supports both RDMA and CXL backends from a single codebase
- All 5 methods (CHIME, Sherman, SMART, ROLEX, Marlin) working on both RDMA and CXL
- RDMA-vs-CXL comparative throughput-latency figures using identical workloads
- Analytical explanation of performance differences (latency, cache coherence, coroutine overhead)
- CXL emulated via remote NUMA node on r650 (2x Xeon, 2 NUMA domains)
- Coroutines stripped in CXL backend for realistic synchronous load/store performance

## Non-Goals

- Real CXL hardware support (emulation only; can revisit if hardware becomes available)
- CXL 3.0 multi-host sharing or cross-host coherence (single-node NUMA emulation)
- Modifying CHIME's core index algorithm (B+tree/hopscotch logic stays the same)
- Supporting CXL Type 1 or Type 2 devices
- Production-grade CXL memory pool management

## User Stories

- As a PhD student, I want to compare CHIME's performance on RDMA vs CXL so that I can analyze the impact of transport choice on disaggregated-memory indexes.
- As a course instructor, I want to see a clean abstraction layer so that the student demonstrates deep understanding of both transport models.
- As a researcher, I want comparative figures with analysis so that the results contribute meaningful insight beyond simple reproduction.

## Design Approach

### Architecture: Transport Abstraction Layer

```
┌─────────────────────────────────────────────┐
│          Index Layer (Tree.cpp)              │
│   CHIME / Sherman / SMART / ROLEX / Marlin  │
├─────────────────────────────────────────────┤
│          Transport Interface                 │
│   read_sync / write_sync / cas_sync / ...   │
├──────────────────┬──────────────────────────┤
│  RdmaTransport   │     CxlTransport         │
│  (wraps DSM)     │  (NUMA mmap + atomics)   │
│  + coroutines    │  - no coroutines          │
│  + lkey/rkey     │  - no registration        │
│  + CQ polling    │  - synchronous            │
└──────────────────┴──────────────────────────┘
```

### Key Components

1. **`Transport` concept / template parameter** (`include/Transport.h`): Defines the interface — `read_sync`, `write_sync`, `read_batch_sync`, `write_batch_sync`, `cas_sync`, `cas_mask_sync`, `faa_sync`, `alloc`, `free`, `barrier`. No coroutine parameters. **Compile-time polymorphism** via C++ templates (`template <typename TransportT>`) to eliminate vtable overhead on hot paths (millions of operations/sec). Selected at build time via `USE_CXL` CMake flag.

2. **`RdmaTransport`** (`src/RdmaTransport.cpp`): Wraps existing `DSM` class. Bridges the coroutine-based async model to the synchronous `Transport` interface. Preserves all current RDMA behavior. Replicates `Directory` + `LocalAllocator` allocation logic.

3. **`CxlTransport`** (`src/CxlTransport.cpp`): Maps remote NUMA node memory via `mmap` with `MPOL_BIND` to the remote NUMA node. Translates `GlobalAddress` to pointer arithmetic. Uses `memcpy` for reads/writes, GCC `__sync_*` builtins for atomics. Replicates `Directory` + `LocalAllocator` allocation logic adapted for shared NUMA memory (concurrent allocators must coordinate via atomics rather than RPC).

4. **`OpRegion`** (`include/Transport.h`): Transport-agnostic replacement for `RdmaOpRegion`. Contains `source`, `dest` (GlobalAddress), `size` — no lkey/rkey.

5. **Masked CAS emulation**: CXL backend must handle masked CAS (a Mellanox NIC extension with no CPU equivalent). Multiple strategies to explore during implementation:
   - **Option A — Read-modify-CAS loop**: Read current value, apply mask comparison, attempt full CAS. Risk: spurious retries when non-masked bits change concurrently, potential livelock under high contention.
   - **Option B — Separate cache-line per lock**: Dedicate a full cache line (64B) to each lock word, eliminating false sharing on non-masked bits. Trades memory for contention reduction.
   - **Option C — Per-lock byte with `__atomic_*`**: Replace bit-mask locking with byte-level atomics (`__atomic_exchange_n` on a dedicated lock byte). Simplest but changes locking semantics.
   - Trade-offs and tail-latency impact under contention to be documented in the report as part of the CXL analysis.

6. **On-chip memory emulation**: RDMA's on-chip lock memory (`is_on_chip` flag, separate `lockBase`) mapped to a dedicated region within the CXL memory pool. Same `GlobalAddress` routing, different base pointer.

7. **CMake flag**: `USE_CXL` compile-time flag selects the transport backend. Experiment scripts set this via the existing `sed_common.py` pattern.

8. **Experiment orchestration**: New `exp/fig_cxl_*.py` scripts that run each method on both transports and produce comparative plots.

### Data Flow: CXL Read

```
Tree.cpp: transport->read_sync(buffer, gaddr, size)
  → CxlTransport::read_sync()
    → resolve(gaddr) = base_addr_ + gaddr.offset
    → memcpy(buffer, resolved_ptr, size)
    → returns immediately (synchronous)
```

### Data Flow: CXL CAS (Lock Acquisition)

```
Tree.cpp: transport->cas_sync(gaddr, 0, ~0, &result)
  → CxlTransport::cas_sync()
    → target = base_addr_ + gaddr.offset
    → result = __sync_val_compare_and_swap(target, 0, ~0)
    → return (result == 0)
```

### Refactoring Strategy for Index Code

The index code (`Tree.cpp` and equivalents in sibling repos) currently calls `dsm->read_sync(...)`. The refactoring:

1. Templatize Tree class: `template <typename TransportT> class Tree` — selected at compile time via `USE_CXL`
2. Remove `CoroPull *sink` parameters from all call sites in CXL path (guarded by `#ifdef USE_CXL` or `if constexpr`)
3. Replace `RdmaOpRegion` with `OpRegion` at call sites
4. Composite operations (`write_cas`, `cas_read`, etc.) decomposed into sequential calls in CXL backend

### Sibling Repo Strategy

All 5 repos share identical layout. The transport abstraction applies uniformly:
- Add `include/Transport.h`, `include/CxlTransport.h`, `src/CxlTransport.cpp` to each repo
- Wrap each repo's existing DSM in `RdmaTransport`
- CMake flag `USE_CXL` toggles backend
- `sed_common.py` extended to set `USE_CXL`

### NUMA Emulation Setup

On r650 (2x Xeon):
- NUMA node 0: compute (application threads)
- NUMA node 1: "CXL memory" (mmap'd with `mbind(MPOL_BIND)` to node 1)
- `numactl --membind=1` for the memory pool allocation
- Optional: inject artificial latency via kernel `hmat` tables or `e820` reservation to model CXL's ~100-200ns additional latency over local DRAM

## Sample Implementation

```cpp
// include/Transport.h — Transport abstraction (compile-time polymorphism)

#pragma once
#include "GlobalAddress.h"
#include <cstdint>
#include <cstddef>
#include <string>
#include <cstring>

// Transport-agnostic operation region (replaces RdmaOpRegion)
struct OpRegion {
  uint64_t source;      // local buffer address
  GlobalAddress dest;   // remote address
  uint64_t size;
};

// No base class — backends are selected via template parameter at compile time.
// Tree<CxlTransport> or Tree<RdmaTransport> — zero vtable overhead.

// ---- CXL Backend (NUMA-emulated) ----

class CxlTransport {
  void *base_addr_;   // mmap'd remote NUMA region
  void *lock_addr_;   // emulated on-chip lock region
  size_t pool_size_;

  void *resolve(GlobalAddress gaddr, bool is_lock = false) {
    void *base = is_lock ? lock_addr_ : base_addr_;
    return static_cast<char *>(base) + gaddr.offset;
  }

public:
  CxlTransport(int numa_node, size_t pool_size, size_t lock_size);

  void read_sync(char *buffer, GlobalAddress gaddr, size_t size) {
    memcpy(buffer, resolve(gaddr), size);  // CPU load
  }

  void write_sync(const char *buffer, GlobalAddress gaddr, size_t size) {
    memcpy(resolve(gaddr), buffer, size);  // CPU store
  }

  void read_batch_sync(OpRegion *rs, int count) {
    for (int i = 0; i < count; i++)
      memcpy(reinterpret_cast<char *>(rs[i].source),
             resolve(rs[i].dest), rs[i].size);
  }

  bool cas_sync(GlobalAddress gaddr, uint64_t expected,
                uint64_t desired, uint64_t *result) {
    auto *target = static_cast<uint64_t *>(resolve(gaddr));
    *result = __sync_val_compare_and_swap(target, expected, desired);
    return (*result == expected);
  }

  bool cas_mask_sync(GlobalAddress gaddr, uint64_t expected,
                     uint64_t desired, uint64_t *result,
                     uint64_t compare_mask, uint64_t swap_mask) {
    // Emulate masked CAS: read-modify-CAS loop
    // TODO: evaluate alternative strategies (separate cache-line per lock,
    //       per-lock byte atomics) for tail latency under contention
    auto *target = static_cast<uint64_t *>(resolve(gaddr));
    while (true) {
      uint64_t current = __atomic_load_n(target, __ATOMIC_SEQ_CST);
      if ((current & compare_mask) != (expected & compare_mask)) {
        *result = current;
        return false;
      }
      uint64_t new_val = (current & ~swap_mask) | (desired & swap_mask);
      if (__sync_bool_compare_and_swap(target, current, new_val)) {
        *result = current;
        return true;
      }
    }
  }

  uint64_t faa_sync(GlobalAddress gaddr, uint64_t add_val) {
    auto *target = static_cast<uint64_t *>(resolve(gaddr));
    return __sync_fetch_and_add(target, add_val);
  }

  // alloc, free: replicate Directory + LocalAllocator with atomic coordination
  // barrier: shared-memory barrier (e.g., pthread_barrier or atomic counter)
};

// ---- Usage in index code ----
// template <typename TransportT>
// class Tree {
//   TransportT *transport_;
//   void search(Key k) {
//     transport_->read_sync(buf, node_addr, size);  // inlined, no vtable
//   }
// };
// Instantiated as Tree<CxlTransport> or Tree<RdmaTransport> via USE_CXL flag.
```

## Edge Cases & Error Handling

### EC-1: Masked CAS Livelock
- **Scenario**: High contention on a lock word causes the read-modify-CAS loop in `cas_mask_sync` to spin indefinitely
- **Behavior**: Bounded retry with exponential backoff; fall back to mutex if retry count exceeded
- **Test**: Stress test with maximum thread count on a single lock word; verify progress

### EC-2: NUMA Memory Exhaustion
- **Scenario**: Remote NUMA node runs out of memory for the CXL pool
- **Behavior**: `CxlTransport` constructor fails with clear error message indicating required pool size and available NUMA memory
- **Test**: Attempt allocation larger than remote node capacity; verify graceful failure

### EC-3: GlobalAddress NodeID in Single-Node CXL
- **Scenario**: CHIME's GlobalAddress encodes a 16-bit nodeID, but CXL emulation runs on a single machine with shared memory
- **Behavior**: CXL backend ignores nodeID field (all memory is in one pool); `resolve()` uses only the offset
- **Test**: Operations with different nodeIDs in GlobalAddress all resolve to the same pool

### EC-4: Composite Operation Atomicity
- **Scenario**: RDMA's `write_cas` posts both operations as a single WQE batch (atomic from the network perspective). CXL decomposes into sequential `write` + `cas`
- **Behavior**: Acceptable because CXL coherence + the CAS verification ensures correctness — if the CAS fails, the write is rolled back by the index logic (same as RDMA CAS failure path)
- **Test**: Concurrent split operations; verify no corruption via YCSB correctness checks

### EC-5: Coroutine Removal Side Effects
- **Scenario**: Removing coroutine yield points changes thread scheduling behavior, potentially exposing latent concurrency bugs
- **Behavior**: CXL backend uses simple threading (1 thread per client, no coroutine multiplexing). Thread count matched to RDMA's effective concurrency for fair comparison
- **Test**: Run YCSB with increasing thread counts; compare correctness and throughput stability

## Acceptance Criteria

### AC-1: Transport Abstraction Compiles for Both Backends
- **Given** the CHIME codebase with `Transport.h` added
- **When** built with `cmake -DUSE_CXL=OFF` (RDMA) and `cmake -DUSE_CXL=ON` (CXL)
- **Then** both produce working `ycsb_test` binaries with no compilation errors

### AC-2: CXL Backend Passes YCSB Correctness
- **Given** CxlTransport initialized on remote NUMA node
- **When** running YCSB workloads A-F with all 5 methods
- **Then** all operations (insert, read, update, scan) return correct results; no assertion failures or segfaults

### AC-3: RDMA Backend Preserves Existing Performance
- **Given** RdmaTransport wrapping existing DSM
- **When** running the same YCSB workloads as Part One
- **Then** throughput and latency within 5% of pre-refactoring measurements (no regression)

### AC-4: CXL Latency Lower Than RDMA
- **Given** both backends running the same workload on r650
- **When** comparing median read latency
- **Then** CXL median latency < RDMA median latency (expected ~3-5x improvement based on NUMA vs InfiniBand)

### AC-5: Comparative Figures Generated
- **Given** completed runs on both transports for all 5 methods
- **When** experiment scripts produce output
- **Then** at minimum: throughput-latency curves (like Fig 12) for RDMA vs CXL, cache comparison (like Fig 14), and a latency breakdown figure

### AC-6: All 5 Methods Work on CXL Under Stress
- **Given** the transport abstraction applied to CHIME, Sherman, SMART, ROLEX, and Marlin repos
- **When** each is built with `USE_CXL=ON` and run with YCSB workload A at maximum thread count for 60 seconds
- **Then** all 5 produce correct benchmark output with no assertion failures, segfaults, or hangs

### AC-7: Report Includes Performance Analysis
- **Given** comparative figures
- **When** the LaTeX report is complete
- **Then** it includes analysis of why CXL outperforms RDMA (synchronous vs async, no verb overhead, cache coherence effects, coroutine elimination)

## Technical Notes

- **Affected components**: `include/DSM.h`, `src/DSM.cpp`, `include/Tree.h`, `src/Tree.cpp`, `test/ycsb_test.cpp`, `CMakeLists.txt`, `exp/utils/sed_common.py`, all sibling repos (SMART, ROLEX, Marlin — Sherman uses CHIME repo)
- **Patterns to follow**: Compile-time flag pattern (existing CMake flags like `HOPSCOTCH_LEAF_NODE`); `sed_common.py` rewrite pattern for experiment automation
- **Data model changes**: `OpRegion` replaces `RdmaOpRegion` at index-layer call sites; `GlobalAddress` unchanged
- **Build changes**: New CMake flag `USE_CXL`; conditional compilation of `CxlTransport.cpp` vs `RdmaTransport.cpp`
- **Key papers to reference**: Rcmp (TACO 2024), PCC guidelines (arXiv 2511.06460), Demystifying CXL (MICRO '23)

## Dependencies

- CloudLab r650 reservation with dual-socket access (approved: Mar 27-Apr 3 and Apr 3-6)
- Part One RDMA results as baseline for comparison (due today, Mar 26)
- `numactl` and `libnuma` on r650 nodes (standard on Ubuntu)
- Sibling repos (SMART, ROLEX, Marlin) forked and accessible

## Open Questions

- **Artificial latency injection**: Should we add ~100-200ns artificial latency to NUMA accesses to better model real CXL? (e.g., via `hmat` kernel tables or busy-wait padding in `resolve()`). This affects result realism but adds complexity.
- **Thread count normalization**: RDMA uses coroutines (e.g., 8 coros per thread x 24 threads = 192 effective workers). CXL uses plain threads. Should CXL use 192 threads for fair comparison, or match the 24 physical threads?
- **Memory node role**: In RDMA, the memory node runs a server process. In CXL, there's no server — just shared memory. How to handle the 11th node? (Likely: don't use it, run 10 CN with local NUMA-emulated CXL)
- **Scan operations**: CHIME's range scan uses `FINE_GRAINED_RANGE_QUERY` with multiple RDMA reads. On CXL, this becomes sequential pointer chasing with hardware prefetch. Worth investigating prefetch hints (`__builtin_prefetch`) for CXL scan performance?
- **Transport interface universality**: Do all 5 methods' DSM usage patterns decompose cleanly into the common `Transport` template interface? Sherman's `write_faa` composite, CHIME's `cas_read`, and SMART's read delegation may need method-specific extensions or escape hatches. Must audit each repo's DSM call sites during implementation.
- **Masked CAS strategy selection**: Three options identified (read-modify-CAS loop, separate cache-line per lock, per-lock byte atomics). Need to prototype and benchmark under contention to select. Tail latency impact to be documented in report.

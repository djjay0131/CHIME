# Sherman LOAD Crash: Static Analysis of `Tree.cpp:382`

**Date:** 2026-04-22
**Author:** Static analysis (pre-tomorrow task from `llm/features/final-project.md`)
**Status:** Hypothesis, unverified against crash logs from run8

## Observed behavior

During Run 8 (Apr 6-7, r650 Clemson, 3 CN + 1 MN, Sherman LOAD workload), `ycsb_test` crashed with:

```
Assertion `k >= fence_keys.lowest' failed
```

at `src/Tree.cpp:382`, after ~5M keys loaded, preceded by `RDMA Work Request Flushed` errors on multiple CN threads.

## The assertion

```cpp
// src/Tree.cpp, internal_node_search(), lines 372-385
const auto& fence_keys = node->metadata.fence_keys;
if (from_cache && (!node->metadata.valid ||
                   k < fence_keys.lowest || k >= fence_keys.highest)) {
  return false;    // escape hatch: retry via cache refresh
}
if (k >= fence_keys.highest) {          // escape hatch: walk right sibling
  node_addr = node->metadata.sibling_ptr;
  path_stack[sink ? sink->get() : 0][level - 1] = node_addr;
  internal_node_search(node_addr, sibling_addr, k, level, false, sink);
  return true;
}
assert(k >= fence_keys.lowest);          // crash site (382)
```

**Claim: the assertion is reachable under legitimate concurrent behavior.** The function has an escape hatch for:
- Cached+invalid OR key out of range (line 373 — but only when `from_cache`)
- `k >= highest` (line 376 — walk the sibling pointer)

There is **no escape hatch for `k < lowest` on a freshly-read (not-from-cache) node**. The assertion assumes this is impossible. It isn't, under the following sequence:

## Proposed race (Sherman-specific)

Thread A splits internal node N:
1. A acquires N's lock, reads N.
2. A creates sibling node S; S.fence_keys = {split_key, old_N_highest}.
3. A updates N.fence_keys.highest = split_key (N's upper bound shrinks).
4. A updates N.metadata.sibling_ptr = S.
5. A releases N's lock.
6. A walks up the tree to update the parent P to point at S.
7. **Window:** between steps 5 and 6, N and S exist with consistent fence keys, but P still has a single entry pointing at N covering the original {lowest, old_N_highest} range.

Thread B descends concurrently:
1. B reads P (unlocked, read path).
2. B sees P's entry pointing at N for a key `k` in `(split_key, old_N_highest)` — the range that *has already moved to S*.
3. B reads N (fresh, `from_cache=false`).
4. B sees N.fence_keys = {old_N_lowest, split_key}.
5. Evaluates line 376: `k >= fence_keys.highest` (=`split_key`) → walks sibling pointer to S.

Step 5 works. **So this exact race does not trigger the assertion.**

But consider the dual: thread A *grows N's lower bound* via a left-sibling merge-in or a borrow operation.

Under Sherman's simpler B+tree-with-byte-writes protocol (no hopscotch, no vacancy-aware locks), merge/borrow operations update `fence_keys.lowest` in place. The window between "A updates N.lowest" and "A updates parent P to reflect the new range" produces a state where B can descend into N carrying a `k < new_lowest`. Since line 373's escape only fires `from_cache`, and line 376 only handles `k >= highest`, the fall-through is the assertion at 382.

## Why CHIME doesn't hit this but Sherman does

CHIME's extra techniques incidentally close this window:

- **`SIBLING_BASED_VALIDATION`**: each read of a non-root internal node cross-validates against the sibling's fence keys, catching the inconsistency before the assertion.
- **`VACANCY_AWARE_LOCK`**: piggybacks a vacancy bitmap on the lock word, which forces readers to see a consistent snapshot of lock + fence state.
- **`METADATA_REPLICATION`**: leaf metadata is replicated per segment, so a stale read on any single segment is caught by mismatched version numbers.

Sherman, built with these OFF (the fig_15a baseline configuration), lacks all three.

## Evidence to verify

To confirm the hypothesis, the following would be needed from a reproduction run (not attempted today — off-hardware static analysis only):

1. **Reproduce deterministically**: run Sherman LOAD with `--tsan` or gdb-watchpoints on the crash thread's `fence_keys.lowest`.
2. **Capture the tree state at crash**: core dump from AC-14's debug harness, `gdb` post-mortem showing the parent pointer chain.
3. **Count threads stuck in the `re_read` loop**: if many threads are spinning and one finally hits the assertion, concurrent split-in-flight is the signal.

## What the report should say

Frame this as a **finding about the Sherman baseline**, not a CHIME bug:

> We observed Sherman's LOAD phase crashing repeatedly at ~5M keys under
> 3 CN × 64 threads on r650. The crash is an assertion at
> `src/Tree.cpp:382` asserting `k >= fence_keys.lowest`. The assertion's
> code path has escape hatches for `k >= highest` (right-walk to sibling)
> and for cache-staleness, but no escape for `k < lowest` on a freshly-
> read non-cached node. Under concurrent split/borrow operations, a
> reader can descend through a stale parent pointer into a node whose
> `fence_keys.lowest` has just been widened, triggering the assertion.
> CHIME's `SIBLING_BASED_VALIDATION` and `VACANCY_AWARE_LOCK` close this
> window, which explains why CHIME completes LOAD without the crash.
> This is consistent with the paper's claim that the techniques are
> jointly necessary, not just a throughput optimization.

## Proposed fix (not to implement — out of scope)

Either:
- **Minimal fix**: retry-on-inconsistency at line 382 instead of asserting — add a `goto re_read` after incrementing a retry counter; abort only on repeated failure. Matches the style of the `decode_node_versions` retry at line 369-371.
- **Structural fix**: adopt `SIBLING_BASED_VALIDATION` as a baseline rather than an optimization — this is effectively what CHIME does.

Neither is appropriate to land in the Sherman baseline for our comparison; the whole point of fig_15a is to show what Sherman *without* these techniques looks like. The crash stays as a **documented limitation of the baseline** in the report.

## Takeaway for tomorrow's run

- Do not attempt to debug this on the cluster — it's a known baseline limitation.
- When collecting fig_12 LOAD for Sherman, expect the crash; collect whatever partial data we can before it fires, and include the crash as an annotated data point in the plot.
- The crash itself reinforces fig_15a's thesis — add a callout in the report.

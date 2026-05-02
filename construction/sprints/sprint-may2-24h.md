# Sprint: May 2 17:00 UTC — May 3 17:00 UTC, 4 r650 Clemson nodes

**Reservation:** `312ca700-36c8-4e29-a911-dbad8ab5d8e1` (4 r650 Clemson)
**Window:** 2026-05-02 17:00 UTC -> 2026-05-03 17:00 UTC (24 h)
**Hardware available:** 4 nodes — supports up to **3 CN + 1 MN**
**Mode:** autonomous; control-net guard active on all nodes; results -> `/proj/cs620426sp-PG0/djjay-results/`

## Themes (priority-ordered)

1. **Multi-CN data on r650 Clemson.** First time we have a 3 CN + 1 MN config that matches the paper's geometry. CHIME / SMART / ROLEX / Sherman x C/D/E.
2. **CXL ports for SMART, ROLEX, Sherman.** Sherman-CXL exists already (CHIME source with features off). SMART and ROLEX have their own transports — port each behind a `USE_CXL=on` flag so we can do same-method RDMA-vs-CXL on each.
3. **Cross-method on CXL.** Direct CXL comparison of the four indexes on the same hardware.
4. **Variance reps.** Tighten the cross-day variance claim by adding 5–10 reps per cell at T=16, T=32 for the most-cited points.
5. **Higher thread counts.** T=96, T=128 on CXL (single-process) and on RDMA at 3 CN to find scaling ceilings.
6. **Workloads A/B retry.** Sherman crashes on A/B at single-CN; check if 3 CN + 1 MN closes the race the way the paper implies.

## Phase plan (24 h)

| Phase | Time-window (UTC)    | Goal                                                           |
| ----- | -------------------- | -------------------------------------------------------------- |
| 0     | 17:00 – 17:20 (20m)  | Auto-create experiment; prep-experiment.sh; smoke RDMA + CXL   |
| 1     | 17:20 – 19:20 (2h)   | 3 CN + 1 MN sweep: CHIME / SMART / Sherman C/D/E (RDMA)        |
| 2     | 19:20 – 20:20 (1h)   | 3 CN + 1 MN ROLEX C/D/E retry (predicted to clear synonym leaf) |
| 3     | 20:20 – 22:20 (2h)   | Variance reps: CHIME-CXL T=16/32 x C/D/E x 5 reps              |
| 4     | 22:20 – 02:20 (4h)   | **CXL port for Sherman/SMART/ROLEX (engineering)** + smoke    |
| 5     | 02:20 – 06:20 (4h)   | SMART-CXL + ROLEX-CXL sweeps (single-process, NUMA emulation)  |
| 6     | 06:20 – 09:20 (3h)   | High thread count sweep: T=96, T=128 on CXL + 3 CN RDMA        |
| 7     | 09:20 – 13:20 (4h)   | Workload A/B retry at 3 CN + 1 MN                              |
| 8     | 13:20 – 16:20 (3h)   | Long variance run: CHIME-RDMA bimodality at T=16, 30 reps      |
| 9     | 16:20 – 17:00 (40m)  | Final pulldown, plots, report update, push                     |

## Phase 4: CXL port plan (highest engineering risk)

### SMART
- Source: `/proj/cs620426sp-PG0/djjay-repos/SMART`
- Approach: replicate CHIME's `CxlTransport` + `CxlDSM` pattern, gated by a new `USE_CXL` cmake option.
- Likely files to add: `include/CxlTransport.h`, `src/CxlTransport.cpp`, `include/CxlDSM.h`, `src/CxlDSM.cpp`.
- SMART's `DSM` calls `read_sync` / `write_sync` / `cas_sync` against the RDMA transport — we hook them to the CXL pool.
- Risk: SMART has lock-free internal nodes that assume RDMA atomicity guarantees. CXL emulation uses regular x86 atomics, which should map cleanly.

### ROLEX
- Source: `/proj/cs620426sp-PG0/djjay-repos/ROLEX`
- Same approach. Risk: ROLEX has a learned-index pre-train phase that loads 60M keys; this should be transport-agnostic (it's all CN-side memory).

### Sherman
- Already done — `build-Sherman-cxl` is the same source as CHIME with all 5 feature flags off.

## Storage / sweep pattern (avoid ssh-polling)

- All experiment binaries write JSONL to `/proj/cs620426sp-PG0/djjay-results/`.
- Master node maintains `/proj/cs620426sp-PG0/djjay-results/heartbeat.txt` (one line per minute).
- Laptop wakes every 30 min; one `scp -r` of `/proj/cs620426sp-PG0/djjay-results/` to `exp/results/may2-24h/`.
- Plots regenerate locally; results commit + push to GitHub.
- Control-net guard is active on every node; aborts on >500 MB cumulative public traffic.

## Success criteria

- Multi-CN data for at least CHIME and one competitor on at least workload C.
- ROLEX-D crash either reproduced at multi-CN (negative) or absent (predicted positive).
- CXL ports for SMART or ROLEX runtime-validated end-to-end.
- Variance error bars on the cross-day claim (CHIME-CXL stable, RDMA bimodal).
- Report updated with new findings, presentation updated.

## Failure modes / fallbacks

- If experiment provisioning fails: poll portal-cli, retry every 5 min for up to 30 min, then alert.
- If CXL port doesn't compile: skip and run a deeper RDMA sweep instead.
- If a node dies mid-run: continue on remaining nodes; nodes-file is regenerated each prep.
- If control-net guard trips: ABORT all background sweeps, kill ycsb_test on every node, scp the guard log down, diagnose.

## Sprint Retrospective Addendum (May 2 21:11 UTC)

The n=4 attempt failed twice during launch:
1. **First experiment** (`a417376d`, 17:02 UTC): bootstrapped successfully, but `openibd restart` to apply `MAX_ATOMIC_ARG=8` killed the public control net (mlx5_core also drives `eno12399`). Experiment terminated at 19:35 UTC.
2. **Second experiment** (`af875a06`, 19:42 UTC): bootstrap-node.sh updated to write the modprobe.d entry BEFORE OFED loads, with `update-initramfs -u`. Bootstrap completed but `device_cap_flags` was still `0x00000000` because the option only takes effect on next boot. Issued soft reboot at 20:21 UTC; nodes never came back. Powercycle at 20:44 UTC also didn't help. Terminated at 21:04 UTC.

**Falling back to n=2** (1 CN + 1 MN). This config worked reliably May 1-2, so we know the pipeline. The 24h plan deferred phases 1, 2, 4, 7 (multi-CN-only) to the **May 6 7-node reservation** (`8971e238`). On the n=2 reservation we'll run phases 3, 5, 6, 8 — variance reps, SMART-CXL/ROLEX-CXL ports + sweeps, high-thread CXL, and the long-rep variance run.

**Lesson learned**: the modprobe-then-reboot path doesn't survive a double-reboot today. Better approach for May 6: include the modprobe option BEFORE the first OFED install (we now do), but also run the full bootstrap before any reboot, then test `device_cap_flags` — if zero, just accept it for read-only workloads (workload C/D/E don't actually need atomics; only A/B do). The atomic fix is only needed for workloads that use CAS heavily.

## Final status (May 2 22:30 UTC) — sprint aborted

Both n=4 (`af875a06`) and n=2 (`77421a96`) experiments became unreachable after the reboot needed to apply `MAX_ATOMIC_ARG=8`. Pattern: SSH up before reboot → soft reboot via portal-cli → SSH dies → does not come back within 25+ min. Powercycle didn't help either.

Root cause confirmed via standalone CN run: `ycsb_test` on workload C dies with `Failed to create QP` because `device_cap_flags=0x00000000` (no atomic capability advertised). This is the exact same `errno 95 ENOTSUP` issue documented in our memory bank from prior reservations.

The May 1 `prb-145800` experiment did NOT hit this dead-after-reboot pattern because we applied the fix via `openibd restart` over the still-connected SSH session, and that came back. Today we tried to AVOID `openibd restart` (because last time it killed `eno12399`) by writing the modprobe option pre-install and rebooting — but the reboot itself made the nodes unreachable. The bootstrap script's `update-initramfs -u` step is the most likely suspect; on `r650` Clemson stock images it appears to corrupt something about the boot path.

**Strategy for May 6 (7-node reservation `8971e238`):**
1. After OFED install, run `openibd restart` ONE TIME over the still-connected SSH session (the path that proved survivable May 1). Accept the brief eno12399 blip.
2. Skip `update-initramfs -u` entirely.
3. Verify `device_cap_flags` non-zero before any sweep launch.
4. The May 1-2 single-CN data we already have (`exp/results/may2-competitors/`) is sufficient for every CXL claim in the report; the May 6 reservation is for multi-CN scaling, ROLEX-D-at-3-CN test, and any further variance reps.

The autonomous-runner.sh, bootstrap-node.sh, control-net-guard.sh, run-with-guard.sh, and prep-experiment.sh are committed and ready. The launch sequence works through portal-cli `experiment create` → SSH probe → key distribution → bootstrap dispatch — only the post-OFED-install step needs revision (use `openibd restart`, not `reboot`).

Heartbeat cron not started (would have nothing to pull).

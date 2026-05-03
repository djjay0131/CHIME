# Sprint: May 6 — Final 7-Node Reservation Before Paper Deadline

**Reservation:** `8971e238-b183-462c-ba65-8d688912f98f`
**Window:** 2026-05-06 01:00 UTC → 2026-05-11 01:00 UTC (5 days approved)
**Realistic working window:** 2026-05-06 01:00 UTC → 2026-05-07 04:00 UTC (~27 h until midnight EDT paper deadline May 6)
**Hardware:** 7× r650 Clemson — supports up to **6 CN + 1 MN**
**Mode:** primary goal is multi-CN data; secondary goal is filling May 2 sprint gaps

## What we already have (no need to re-collect)

After the May 2 sprint (`exp/results/may2-24h/`):
- 30+ reps CHIME-CXL T=16/32 × C/D/E variance — error bars are paper-grade.
- Full CXL ablation T=4..48 × C/D/E across 6 variants (sherman → +hopscotch → +vacancy → +metadata → +sibling → +speculative).
- Speculative-read transition zone T=20..44 with 10 reps each at confirmation.
- Low-thread T=4..16 confirmation × {sherman, sibling, chime} with 10 reps each.
- Sherman-CXL full grid T=4..64 × C/D/E.
- 180 s long-run steady-state (epochs <0.3% drift).
- Coroutine sweep 1..32 (no effect on CXL).
- Single-CN data for SMART, ROLEX, Sherman-RDMA, Sherman-CXL.
- Cross-day reproducibility (CHIME-CXL May 1 ↔ May 2 within ~5%).

## What's missing (what May 6 must close)

1. **Multi-CN reproduction of the speculative-read net-negative finding.** Single-CN: confirmed. Does it scale? Hypothesis: yes, because the mechanism (synchronous CXL serializing speculative reads) is per-thread, but at higher CN counts the lock-coordination overhead rises and might hide the speculative-read penalty. Need 3 CN + 1 MN and 5 CN + 1 MN data.
2. **Multi-CN CHIME-CXL throughput vs CHIME-RDMA** at scale. Single-CN says CXL wins on C/D and loses on E. Multi-CN may flip if cross-CN coordination dominates.
3. **ROLEX-D synonym-leaf assertion test at multi-CN** — single-CN says the chain overflows; predicted to clear at 3 CN where the 5% insert stream is distributed.
4. **fig_12 paper-style three-way plot** with multi-CN CHIME, SMART, ROLEX, Sherman, SMART-SC. We have all five at multi-CN from Run 7-8 (Apr 6-7) — good. Adding May 6 multi-CN refresh would let us nail the bimodality story.

## Phase plan (~24 h, lessons-learned-applied)

| Phase | Window (UTC) | Goal | Lessons |
| ----- | ------------ | ---- | ------- |
| 0 | 01:00–01:30 | Provision via web UI (n=7), then take over via SSH from laptop | API was dead May 2-3; assume API is unreliable |
| 1 | 01:30–02:00 | Distribute SSH keys inline (skip prep-experiment.sh's buggy loop), write nodes.txt, install OFED via bootstrap-node.sh on all 7 in parallel | bootstrap-node.sh works |
| 2 | 02:00–02:30 | **CRITICAL:** Apply MAX_ATOMIC_ARG=8 fix WITHOUT triggering openibd restart. Three options:<br>(a) `sudo /etc/init.d/openibd restart` SEQUENTIAL on each node — proved to brick clnode257/263 May 2; do NOT use this path<br>(b) skip the atomic fix, accept device_cap_flags=0 — workload C can still segfault with "Failed to create QP"<br>(c) reboot via portal-cli AFTER bootstrap-node.sh writes the modprobe.d entry — proved to NOT come back on r650 Clemson May 2 (`update-initramfs -u`)<br>**Plan A:** try (c) first since the May 2 Clemson nodes may have been a fluke; if 5+ of 7 don't return in 25 min, fall back to using only the responsive subset. | All three paths failed May 2; need to research what actually fixes this |
| 3 | 02:30–03:00 | Smoke test 1 CN + 1 MN, confirm caps and throughput | |
| 4 | 03:00–06:00 | 3 CN + 1 MN multi-CN sweep on RDMA: CHIME, SMART, Sherman, ROLEX × C/D/E. Same harness as May 2 single-CN. | |
| 5 | 06:00–09:00 | 5 CN + 1 MN multi-CN sweep on RDMA: same matrix. Compare to Run 7-8 reference. | |
| 6 | 09:00–11:00 | ROLEX-D at 3 CN + 1 MN: predicted to clear synonym-leaf assertion. Single hypothesis test, 5 reps × 5 thread counts on workload D only. | |
| 7 | 11:00–14:00 | If nodes recover from openibd restart somewhere along the way, multi-CN CHIME-CXL... but CXL is single-process by design (NUMA emulation). Use the spare nodes for *parallel* CXL ablation runs (independent), 5+ different builds running simultaneously gives us 5x throughput on the variance reps. | |
| 8 | 14:00–24:00 | Polish window: pull data, regenerate every plot, append findings to report, push v2.0-final tag. | |
| 9 | 24:00–27:00 | Final report polish on laptop only. Cluster idle. | |

## What to NOT do (May 2 lessons)

- Do NOT run `sudo /etc/init.d/openibd restart` over a connected SSH session — confirmed it bricks r650 Clemson nodes today (3 of 4 didn't return).
- Do NOT run `update-initramfs -u` before a planned reboot — boot path on r650 Clemson seems to corrupt and the node never comes back.
- Do NOT trust the API. Use SSH-only operation as the default; portal-cli only for one-shot experiment list / get / terminate.
- Do NOT ssh-poll log files. Write progress to `/proj/.../heartbeat.txt` on the master and `scp -r` once per heartbeat. (May 2 lesson — CloudLab admin emailed about unusual control-net traffic.)
- Do NOT depend on prep-experiment.sh's SSH key distribution — it only handled 1 of 3 peers May 2. Distribute keys inline in the launch sequence.

## Pre-launch checklist (run from laptop, May 5 at 20:00 UTC, well before reservation start)

- [ ] `cd /Users/djjay0131/code/CHIME && git pull origin main` to get any other-Claude-session updates.
- [ ] Verify all 6 build artifacts under `/proj/cs620426sp-PG0/djjay-build/` survive across reservations (NFS persistent — they should).
- [ ] Verify YCSB workloads under `/proj/cs620426sp-PG0/ycsb_workloads/` are present.
- [ ] `bash script/cloudlab-status-watch.sh` — confirm reservation 8971e238 is approved and visible.
- [ ] Test portal-cli works (or note that it's down again).
- [ ] Have the web UI URL ready: `https://www.cloudlab.us/p/CS620426SP/chime-r650-clemson-lan`.

## Launch sequence (run when reservation opens at 01:00 UTC May 6)

1. Open https://www.cloudlab.us/p/CS620426SP/chime-r650-clemson-lan, click Instantiate, set n=7, name `chime-r650-may6`. Submit.
2. Schedule a Claude wakeup 12 min later via CronCreate (one-shot) to begin the bootstrap sequence.
3. The wakeup runs the May-2-proven inline sequence (no prep-experiment.sh):
   - `PUB=$(ssh node0 "test -f ~/.ssh/id_rsa || ssh-keygen -t rsa -N '' -f ~/.ssh/id_rsa -q; cat ~/.ssh/id_rsa.pub")`
   - `for n in node1..node6; do ssh -o StrictHostKeyChecking=no $n.chime-r650-may6.cs620426sp-PG0.clemson.cloudlab.us "echo '$PUB' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"; done`
   - Write nodes.txt with all 7 hostnames on master.
   - scp `script/bootstrap-node.sh` to master, distribute to peers, dispatch on all 7.
4. After bootstrap completes (~10 min on cached OFED tarball), schedule a 12-min wakeup to verify caps and decide next step.
5. The decision tree at "verify caps" wakeup:
   - If all 7 caps already non-zero (firmware re-init happened to be picked up): proceed straight to memcached + smoke + multi-CN sweeps.
   - If all 7 caps zero: do a **portal-cli reboot of one specific clnode** (whichever cluster member is least critical). If it returns within 8 min, that's our test of whether reboot path is now working. If yes, reboot the rest. If no, abandon the reboot path and proceed with caps=0 — workloads C/D/E may still work for the methods that don't use atomics heavily (SMART, ROLEX).
6. If the smoke test fails because of "Failed to create QP": the node-by-node `openibd restart` is the only remaining path. Run on ONE node first, wait 5 min for SSH recovery; if it returns, sequential on the rest. If it doesn't return, accept that node as lost and continue with remaining responsive nodes.
7. Once at least 4 nodes have working RDMA + caps, kick off `autonomous-runner.sh` for phases 1, 2, 6, 7 (multi-CN-relevant phases).
8. Heartbeat cron `*/29 * * * *` for results pulls / plots / commits.

## Goal metrics (paper-grade)

After May 6 sprint, the report should have:
- A multi-CN throughput-thread plot for at least 3 methods (CHIME, Sherman, SMART) × C/D/E.
- A direct ROLEX-D-at-3-CN test result confirming or refuting the synonym-leaf hypothesis.
- 3+ reps per cell on the headline multi-CN points, allowing statistical bars on cross-method gaps.
- An updated abstract reflecting whether the speculative-read CXL net-negative finding scales out (or not).

## Stop conditions

- If the openibd-restart trap from May 2 still bricks all nodes: stop after one bricked attempt, accept caps=0, run whatever methods do not crash, and document the constraint.
- If we get to 14:00 UTC May 6 with no working multi-CN run: cut bait, write up the single-CN-only findings as the final paper, and submit on time.
- Paper deadline is HARD: midnight EDT May 6 = 04:00 UTC May 7. The 9 h before deadline is for prose/figure polish only — no new experiments after 18:00 UTC May 6.

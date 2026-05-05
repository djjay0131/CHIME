# May 5 21:00 EDT (May 6 01:00 UTC) Launch Runbook

**Reservation:** `8971e238` — 7 r650 Clemson, May 6 01:00 UTC → May 11 01:00 UTC
**Working window before paper deadline (midnight EDT May 6 = 04:00 UTC May 7):** ~27 h
**Source:** `construction/sprints/sprint-may6-final.md` is the strategic plan; this file is the step-by-step.

---

## T-9h to T-1h (May 5, 16:00–20:00 UTC) — Pre-launch checks (DO NOW)

### 1. Confirm infrastructure

- [ ] `bash script/cloudlab-status-watch.sh` → reservation 8971e238 visible, ~9h to start.
- [ ] `git pull origin main` to sync with the paper-writer session.
- [ ] `git status` shows no conflicts.
- [ ] `ls script/` confirms all scripts present and executable.

### 2. Write tonight's launch cron in advance

Pre-load the cron NOW, while the laptop has clean state. The cron fires at
01:02 UTC May 6 (2 min after reservation opens) and starts the launch chain.

### 3. Test portal-cli with current JWT

- [ ] `source .venv/bin/activate && portal-cli --portal-url "https://boss.emulab.net:43794" --token "$(cat files/cloudlab.jwt)" experiment list`
  should return `{"experiments": []}` (no active experiments) within 30 s.
  If timeout, the API auth tier is unhealthy; fall back to web-UI launch
  (https://www.cloudlab.us/p/CS620426SP/chime-r650-clemson-lan).

### 4. Open backup tabs

- [ ] Browser tab open to https://www.cloudlab.us/p/CS620426SP/chime-r650-clemson-lan
  (web-UI fallback).
- [ ] Browser tab open to https://www.cloudlab.us/status.php (status page).

### 5. Write the launch script that the cron will run

See `tonight-launch.sh` below. It:
1. Creates the experiment via `portal-cli` (or fall back to manual web UI).
2. Polls until SSH on the master responds (timeout 25 min).
3. Distributes SSH keys inline to all 6 peers.
4. Writes `/tmp/nodes.txt` on master with all 7 hostnames.
5. Dispatches `bootstrap-node.sh` on all 7 nodes in parallel (idempotent —
   reads OFED tarball from /proj NFS, no per-node download).
6. Schedules a 12-min wakeup for the atomic-cap-fix decision.

---

## T+0h to T+0:30h (01:00–01:30 UTC) — Provision

The cron fires at 01:02 UTC and runs `tonight-launch.sh`. Steps 1–5 above
happen automatically. Output is logged to `/tmp/may6-launch.log`. If the
launch script aborts (e.g., API hangs), the user is paged.

---

## T+0:30h to T+1h (01:30–02:00 UTC) — Atomic-cap fix decision

This is the highest-risk step. May 2-3 evidence: 5 of 8 r650 Clemson nodes
permanently bricked from `openibd restart`. We cannot lose 5 of 7 nodes.

### Decision tree (12-min wakeup at 01:14 UTC)

1. Check `device_cap_flags` on all 7 nodes after bootstrap. If non-zero on any
   subset, those nodes are already RDMA-ready — skip the atomic-cap fix on
   them.
2. For nodes with `device_cap_flags=0x00000000`, try the **least-invasive**
   path first:
   ```
   sudo modprobe -r mlx5_ib && sudo modprobe mlx5_ib
   ```
   This reloads only the IB module, NOT mlx5_core. If `device_cap_flags`
   becomes non-zero, success — no risk to networking.
3. If step 2 doesn't fix caps, on ONE node (not all) try `sudo
   /etc/init.d/openibd restart`. Wait 5 minutes. If SSH returns and caps
   are non-zero, do the rest of the nodes one at a time (NOT in parallel).
   If SSH does not return, consider that node bricked and continue with
   the rest.
4. If `openibd restart` bricks 2+ nodes, **STOP** the atomic-cap fix and
   accept whatever caps state we have. Run smoke tests anyway — workloads
   that don't use atomics heavily (read-only C, scan E) may still work
   even with caps=0.
5. The fallback if RDMA is impossible: drop to single-process CXL on
   whatever nodes survive — but this gives us nothing new beyond May 2-3
   data, so this is the "abort multi-CN" path.

### Build artifacts already on /proj NFS (no rebuild needed)

- `build-rdma-shared/` — full CHIME RDMA
- `build-cxl-fix1/` — full CHIME CXL (with the alloc fix)
- `build-Sherman/` — Sherman RDMA
- `build-Sherman-cxl/` — Sherman CXL
- `build-SMART/` — SMART RDMA
- `build-ROLEX/` — ROLEX RDMA
- `build-cxl-15a-{hopscotch,vacancy,metadata,sibling}/` — ablation builds CXL

If anything changed in the source tree since May 2, those are stale. We
will not rebuild during the launch window unless the smoke test fails for
a build-version reason.

---

## T+1h to T+12h (02:00–13:00 UTC) — Multi-CN sweeps (the actual deliverable)

The single missing piece in the report is multi-CN data on this hardware.
Priority order:

1. **3 CN + 1 MN sweep (4 nodes)** — CHIME, SMART, Sherman × workloads C/D/E
   × thread counts 4/8/16/32/48/64. ~3 h. Runs via `script/autonomous-runner.sh
   /tmp/nodes.txt 1 1` (phase 1 of the autonomous runner).
2. **ROLEX at 3 CN + 1 MN on workloads C/D/E** — tests whether the May 2
   single-CN synonym-leaf assertion at `Rolex.cpp:385` clears with
   distributed inserts. ~1 h. (Phase 2 of the runner.)
3. **5 CN + 1 MN sweep (6 nodes)** — same matrix. ~3 h. (Add a 5-CN phase
   to the runner if needed.)
4. **6 CN + 1 MN sweep (7 nodes, paper-matching geometry)** — same matrix.
   ~3 h. This is the closest we can get to the paper's 10 CN + 1 MN.
5. **3 reps per cell on the headline points** to give multi-CN error bars.
   ~1 h.

### Storage / monitoring

Same as May 2-3 sprint: results land in `/proj/cs620426sp-PG0/djjay-results/may6-final/`,
heartbeat written every 60 s by the runner. Laptop pulls one `scp -r` of
the results dir per ~29 min via durable cron `*/29 * * * *`. **Do not
ssh-poll** the master (CloudLab admin email warning from May 1).

---

## T+12h to T+18h (13:00–19:00 UTC) — Polish window

- [ ] Pull all multi-CN data and regenerate plots.
- [ ] Write up multi-CN findings as a new paragraph in §6 of the report.
- [ ] Update the abstract if multi-CN reveals anything that changes the
      headline (e.g., if speculative-read net-negative goes away at multi-CN,
      that softens the §3 finding).
- [ ] Update `fig12-competitors.pdf` with multi-CN curves alongside
      single-CN.
- [ ] Build report and presentation, verify both PDFs are clean.
- [ ] Tag `v2.0-final` and push.

---

## T+18h to T+27h (19:00 UTC May 6 → 04:00 UTC May 7) — Submission window

- [ ] No new experiments after T+18h.
- [ ] If anything goes catastrophically wrong, the May 2-3 single-CN data
      is the floor — the paper has enough findings to submit even with no
      multi-CN data.

---

## Stop conditions

- If 5+ nodes are bricked by atomic-cap fix attempts: stop, switch to
  CXL-only on whatever nodes remain.
- If 13:00 UTC May 6 with no successful multi-CN run: **stop trying for
  multi-CN**, write up the single-CN-only findings as the final paper, and
  use the polish window for prose.
- Paper deadline is HARD: 04:00 UTC May 7. **No new experiments after
  19:00 UTC May 6.**

---

## Files referenced

- `script/launch-experiment.sh` — wraps `portal-cli experiment create`
- `script/bootstrap-node.sh` — installs OFED + libs + hugepages, idempotent
- `script/autonomous-runner.sh` — cluster-side phase runner
- `script/cloudlab-status-watch.sh` — portal API status (no ssh)
- `script/control-net-guard.sh` — on-node byte-counter guard
- `construction/sprints/sprint-may6-final.md` — strategic plan (this is the tactical file)

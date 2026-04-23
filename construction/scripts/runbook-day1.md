# Day-1 Hardware Runbook — Apr 23 Reservation Window

**Reservation UUID:** `5565ec96-3ebe-11f1-a92d-c4cbe1eff744`
**Window:** Apr 23 15:00 UTC (11:00 AM ET) for 8 hours
**Profile:** `CS620426SP,chime-r650-clemson-lan` · `{"n":"2","hw":"r650"}`

This runbook has **exact commands, in order**. Do not deviate during the critical first 40 minutes. Each block is one tmux paste.

## T+0:00 — Open the experiment (run on Mac)

```bash
export PATH="$HOME/Library/Python/3.9/bin:$PATH"
NAME="chime-$(date -u +%m%d%H%M)"
echo "Name: $NAME"
startExperiment --name "$NAME" \
  --bindings='{"n":"2","hw":"r650"}' \
  --project CS620426SP \
  "CS620426SP,chime-r650-clemson-lan"
```

Save `$NAME` — every later command uses it. Expected: silent success, experiment in `provisioning`.

## T+0:01 — Poll until ready (run on Mac, background)

```bash
for i in $(seq 1 40); do
  json=$(experimentStatus -j "CS620426SP,$NAME" 2>&1)
  st=$(echo "$json" | grep -oE '"status":"[^"]*"' | head -1 | cut -d'"' -f4)
  echo "$(date -u +%H:%M:%S): $st"
  [ "$st" = "ready" ] && { echo "READY!"; break; }
  [ "$st" = "failed" ] && { echo "$json"; exit 1; }
  sleep 30
done
```

Expected: provisioning → provisioned → ready in 5-15 min. If `failed` with "Resource reservation violation", check UUID matches.

## T+0:15 — Extract hostnames (run on Mac)

```bash
experimentManifests "CS620426SP,$NAME" 2>&1 \
  | grep -oE 'hostname="[^"]*"' | cut -d'"' -f2 | sort -u > /tmp/nodes.txt
cat /tmp/nodes.txt
# Expected: two hostnames like node-0.<exp>.cs620426sp-PG0.clemson.cloudlab.us
```

Pick `node-0` as master. Export:
```bash
MASTER=$(head -1 /tmp/nodes.txt)
echo "MASTER=$MASTER"
```

## T+0:17 — Cluster setup (SSH + OFED + VLAN + RoCE + build)

```bash
cd /Users/djjay0131/code/CHIME
./construction/scripts/setup-r650.sh /tmp/nodes.txt "$MASTER"
# This does 7 phases. Watch for errors. Takes ~20 min.
```

If it fails partway, the phases are idempotent — rerun the same command.

## T+0:37 — Go to master, build CXL (on master)

```bash
ssh "djjay@$MASTER"
cd ~/CHIME
rm -rf build-cxl && mkdir build-cxl && cd build-cxl
cmake -DUSE_CXL=ON .. 2>&1 | tail -3
make -j$(nproc) 2>&1 | tail -3
ls -la ycsb_test
# Expected: ycsb_test binary, non-zero size
```

## T+0:42 — THE SMOKE GATE (on master, critical)

Paste both checks. Both must pass.

```bash
cd ~/CHIME/build-cxl
echo 36864 | sudo tee /proc/sys/vm/nr_hugepages
ulimit -l unlimited

# (a) Write-heavy micro-check: 5 seconds of LOAD exercises CAS + alloc
python3 ../exp/run_harness.py --workload smoke-load \
  --build-dir . --source-dir .. \
  --timeout 30 \
  -- ./ycsb_test 1 8 1 randint LOAD &
SMOKE_PID=$!
sleep 5
kill $SMOKE_PID 2>/dev/null
wait $SMOKE_PID 2>/dev/null
# Check: debug/<timestamp>-smoke-load/ should contain stderr.log WITHOUT
# "Assertion" or "Segmentation fault"
grep -l -E "Assertion|Segmentation" debug/*smoke-load*/stderr.log 2>/dev/null && {
  echo "SMOKE GATE FAILED: write path broken"; exit 1;
}

# (b) Read-heavy micro-check: 30s of YCSB C exercises reads
python3 ../exp/run_harness.py --workload smoke-c \
  --build-dir . --source-dir .. \
  --timeout 60 \
  -- ./ycsb_test 1 8 1 randint c &
sleep 30
kill %1 2>/dev/null
wait 2>/dev/null
grep -l -E "Assertion|Segmentation" debug/*smoke-c*/stderr.log 2>/dev/null && {
  echo "SMOKE GATE FAILED: read path broken"; exit 1;
}
# Look for non-zero throughput in stdout.log
grep -E "throughput|tpt" debug/*smoke-c*/stdout.log | head -5
echo "=== SMOKE GATE PASSED ==="
```

**If gate fails:** pull the debug/ dir, commit a failure note, pivot to Part One fig_12 RDMA run (see §Fallback below).

## T+1:00 — Kick off the fig_12 CHIME-CXL sweep (on master, tmux)

```bash
cd ~/CHIME/exp
# Sanity: make sure common.json and fig_12_cxl.json exist
ls params/fig_12_cxl.json params/common.json

# Run — inside tmux so it survives disconnect:
tmux new-session -d -s fig12cxl "python3 fig_12.py > /tmp/fig_12_cxl.log 2>&1"
tmux ls
# Watch progress:
tail -f /tmp/fig_12_cxl.log
```

Pull results **after each workload completes**, not at the end.

## T+3:00 — Single-node RDMA baseline (on master, after CXL sweep)

```bash
cd ~/CHIME
rm -rf build-rdma && mkdir build-rdma && cd build-rdma
cmake .. 2>&1 | tail -3
make -j$(nproc) 2>&1 | tail -3
# Run fig_12 in RDMA mode with 1 CN + 1 MN (we only have 2 nodes)
cd ~/CHIME/exp
tmux new-session -d -s fig12rdma "python3 fig_12.py > /tmp/fig_12_rdma.log 2>&1"
```

## T+6:00 — Pull results and plot (run on Mac)

```bash
cd /Users/djjay0131/code/CHIME
./construction/scripts/pull-results.sh "djjay@$MASTER"
# Verify:
ls exp/results/cxl/fig_12_*.json
ls exp/results/rdma_single/fig_12_*.json
ls exp/results/debug/  # if any crashes captured
```

## T+7:30 — Final pull + sanity (before window closes!)

Repeat the pull. Verify every result file exists. Commit.

```bash
cd /Users/djjay0131/code/CHIME
git add exp/results/
git commit -m "r650 run: CXL + single-node RDMA fig_12 results (Apr 23)"
```

---

## Fallback: Smoke Gate Fails

If the CXL smoke gate fails at T+0:45:

1. Copy `debug/` off the master to Mac immediately.
2. Do NOT debug live — the reservation clock is running.
3. Rebuild RDMA:  `rm -rf build-cxl; mkdir build-rdma && cd build-rdma && cmake .. && make -j`
4. Run fig_12 YCSB A and B (the missing Part One workloads) on 1 CN + 1 MN.
5. Pull results, close the window cleanly.

The CXL failure becomes a report section in Part Two: "compiles clean, runtime blocker at [location], proposed fix: [hypothesis]."

## Rules for the Window

- **Do NOT start any non-cluster work during the reservation.** If you have 10 minutes waiting for a build, rest, don't task-switch.
- **Pull results after EACH workload completes.** `feedback_pull_results_early.md` — we lost data last Part One run because of timer-based pulls.
- **Do NOT let the window close without a final pull.** Calendar alert at 6:30 PM ET is for this.
- **If something gets stuck for >10 min, use run_harness.py to capture state and move on.** No heroic debugging mid-window.

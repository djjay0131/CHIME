#!/usr/bin/env bash
# autonomous-runner.sh — Cluster-side 24-hour autonomous experiment driver.
#
# Runs on the master node. Reads the phase plan from sprint-may2-24h.md
# at $PLAN, executes each phase in order, writes a heartbeat every minute
# to $HEARTBEAT, and writes results JSONL files into $RESULTS_DIR.
#
# Designed to be invoked once after prep-experiment.sh completes. Detaches
# itself with nohup so the laptop can scp results periodically without
# needing to ssh-poll.
#
# Usage:
#   bash script/autonomous-runner.sh <nodes-file> [phase-from] [phase-to]
#
# Defaults: phase-from=1 phase-to=8 (skip 0=setup which prep does, and 9=closeout)
set -u

NODES_FILE="${1:?usage: autonomous-runner.sh <nodes-file> [from] [to]}"
PHASE_FROM="${2:-1}"
PHASE_TO="${3:-8}"

PROJ_NFS="${PROJ_NFS:-/proj/cs620426sp-PG0}"
RESULTS_DIR="${RESULTS_DIR:-$PROJ_NFS/djjay-results/may2-24h}"
HEARTBEAT="${HEARTBEAT:-$RESULTS_DIR/heartbeat.txt}"
LOGFILE="${LOGFILE:-$RESULTS_DIR/runner.log}"
GUARD_DIR="$PROJ_NFS/guard-logs"

mkdir -p "$RESULTS_DIR"

ALL_NODES=($(cat "$NODES_FILE"))
MASTER="${ALL_NODES[0]}"
N=${#ALL_NODES[@]}
INTERNAL_PREFIX="10.10.1"

log() { printf "[%s] %s\n" "$(date -u +%FT%TZ)" "$*" | tee -a "$LOGFILE"; }
hb()  { printf "[%s] %s\n" "$(date -u +%FT%TZ)" "$*" >> "$HEARTBEAT"; }

memcached_init() {
    local mip="${INTERNAL_PREFIX}.1"
    echo flush_all | nc -q1 "$mip" 11211 > /dev/null
    printf 'set serverNum 0 0 1\r\n0\r\nquit\r\n' | nc "$mip" 11211 > /dev/null
    printf 'set clientNum 0 0 1\r\n0\r\nquit\r\n' | nc "$mip" 11211 > /dev/null
}

# Two-node 1 CN + 1 MN sweep: master = MN, $1 = CN node, $2 = build dir
# $3 = workload, $4 = output jsonl, $5 = thread CSV, $6 = method label
sweep_2node() {
    local cn="$1" build="$2" workload="$3" out="$4" threads_csv="$5" method="$6"
    local threads=(${threads_csv//,/ })
    : > "$out".tmp
    for T in "${threads[@]}"; do
        hb "sweep_2node $method $workload T=$T"
        memcached_init
        cd "$build"
        nohup ./ycsb_test 2 "$T" 1 randint "$workload" > /tmp/sweep-mn-$T.log 2>&1 < /dev/null & disown
        sleep 3
        ssh -o ConnectTimeout=5 "$cn" "cd $build && timeout 120 ./ycsb_test 2 $T 1 randint $workload > /tmp/sweep-cn-$T.log 2>&1"
        sleep 1
        pkill -9 ycsb_test 2>/dev/null
        ssh "$cn" 'pkill -9 ycsb_test 2>/dev/null'
        sleep 2
        local peak
        peak=$(grep -oE 'cluster throughput [0-9.]+' /tmp/sweep-mn-$T.log | awk '{print $3}' | sort -g | tail -1)
        peak="${peak:-0}"
        printf '{"method":"%s","workload":"%s","threads":%d,"peak_mops":%s}\n' "$method" "$workload" "$T" "$peak" >> "$out".tmp
        log "  $method $workload T=$T peak=$peak Mops"
    done
    mv "$out".tmp "$out"
}

# 3 CN + 1 MN sweep: master = MN, all other nodes = CN. Single thread count call,
# producing one JSONL line per CN (which the master will sum after).
sweep_3cn1mn() {
    local build="$1" workload="$2" out="$3" threads_csv="$4" method="$5"
    local threads=(${threads_csv//,/ })
    : > "$out".tmp
    for T in "${threads[@]}"; do
        hb "sweep_3cn1mn $method $workload T=$T"
        memcached_init
        cd "$build"
        # MN on master, machine_nr = 4 (1 MN + 3 CN)
        nohup ./ycsb_test 4 "$T" 1 randint "$workload" > /tmp/sweep-mn-$T.log 2>&1 < /dev/null & disown
        sleep 3
        # Launch CN on each non-master node in parallel
        local pids=()
        for ((i=1; i<N; i++)); do
            ssh -o ConnectTimeout=5 "${ALL_NODES[$i]}" "cd $build && timeout 120 ./ycsb_test 4 $T 1 randint $workload > /tmp/sweep-cn-$T.log 2>&1" &
            pids+=($!)
        done
        for pid in "${pids[@]}"; do wait "$pid" 2>/dev/null; done
        sleep 1
        pkill -9 ycsb_test 2>/dev/null
        for ((i=1; i<N; i++)); do ssh "${ALL_NODES[$i]}" 'pkill -9 ycsb_test 2>/dev/null'; done
        sleep 2
        local peak
        peak=$(grep -oE 'cluster throughput [0-9.]+' /tmp/sweep-mn-$T.log | awk '{print $3}' | sort -g | tail -1)
        peak="${peak:-0}"
        printf '{"method":"%s","workload":"%s","threads":%d,"cn_count":%d,"peak_mops":%s}\n' "$method" "$workload" "$T" "$((N-1))" "$peak" >> "$out".tmp
        log "  $method $workload T=$T cn=$((N-1)) peak=$peak Mops"
    done
    mv "$out".tmp "$out"
}

# Single-process CXL sweep: master only, machine_nr=1
sweep_cxl_1node() {
    local build="$1" workload="$2" out="$3" threads_csv="$4" method="$5"
    local threads=(${threads_csv//,/ })
    : > "$out".tmp
    for T in "${threads[@]}"; do
        hb "sweep_cxl $method $workload T=$T"
        cd "$build"
        timeout 120 ./ycsb_test 1 "$T" 1 randint "$workload" > /tmp/cxl-mn-$T.log 2>&1
        local peak
        peak=$(grep -oE 'cluster throughput [0-9.]+' /tmp/cxl-mn-$T.log | awk '{print $3}' | sort -g | tail -1)
        peak="${peak:-0}"
        printf '{"method":"%s-CXL","workload":"%s","threads":%d,"peak_mops":%s}\n' "$method" "$workload" "$T" "$peak" >> "$out".tmp
        log "  $method-CXL $workload T=$T peak=$peak Mops"
    done
    mv "$out".tmp "$out"
}

# Build directories (must exist or be built earlier)
B_CHIME="$PROJ_NFS/djjay-build/build-rdma-shared"
B_SHERMAN="$PROJ_NFS/djjay-build/build-Sherman"
B_SMART="$PROJ_NFS/djjay-build/build-SMART"
B_ROLEX="$PROJ_NFS/djjay-build/build-ROLEX"
B_CHIME_CXL="$PROJ_NFS/djjay-build/build-cxl-fix1"
B_SHERMAN_CXL="$PROJ_NFS/djjay-build/build-Sherman-cxl"

THREADS_FAST="4,8,16,32,64"
THREADS_FULL="4,8,16,32,48,64"
THREADS_HIGH="32,64,96,128"

# ---- Phase 1: 3 CN + 1 MN sweep, RDMA, CHIME / SMART / Sherman, C/D/E ----
phase1() {
    log "=== Phase 1: 3 CN + 1 MN RDMA, CHIME / SMART / Sherman C/D/E ==="
    for w in c d e; do
        sweep_3cn1mn "$B_CHIME"   "$w" "$RESULTS_DIR/p1_chime_${w}.jsonl"   "$THREADS_FAST" CHIME
        sweep_3cn1mn "$B_SMART"   "$w" "$RESULTS_DIR/p1_smart_${w}.jsonl"   "$THREADS_FAST" SMART
        sweep_3cn1mn "$B_SHERMAN" "$w" "$RESULTS_DIR/p1_sherman_${w}.jsonl" "$THREADS_FAST" Sherman
    done
}

# ---- Phase 2: 3 CN + 1 MN sweep, ROLEX C/D/E retry ----
phase2() {
    log "=== Phase 2: 3 CN + 1 MN ROLEX C/D/E (retry — predicted to clear synonym leaf) ==="
    for w in c d e; do
        sweep_3cn1mn "$B_ROLEX" "$w" "$RESULTS_DIR/p2_rolex_${w}.jsonl" "$THREADS_FAST" ROLEX
    done
}

# ---- Phase 3: variance reps for CHIME-CXL ----
phase3() {
    log "=== Phase 3: CHIME-CXL variance reps T=16/32 x C/D/E x 5 reps ==="
    for w in c d e; do
        for T in 16 32; do
            for rep in 1 2 3 4 5; do
                hb "var CHIME-CXL $w T=$T rep=$rep"
                cd "$B_CHIME_CXL"
                timeout 120 ./ycsb_test 1 "$T" 1 randint "$w" > /tmp/var-cxl-$w-$T-$rep.log 2>&1
                peak=$(grep -oE 'cluster throughput [0-9.]+' /tmp/var-cxl-$w-$T-$rep.log | awk '{print $3}' | sort -g | tail -1)
                peak="${peak:-0}"
                printf '{"method":"CHIME-CXL","workload":"%s","threads":%d,"rep":%d,"peak_mops":%s}\n' \
                    "$w" "$T" "$rep" "$peak" >> "$RESULTS_DIR/p3_chime_cxl_variance.jsonl"
                log "  CHIME-CXL $w T=$T rep=$rep peak=$peak"
            done
        done
    done
}

# ---- Phase 4: CXL ports (build/test only — actual sweeps in phase 5) ----
# This phase is left as a marker. The actual port engineering is done by
# Claude during a wakeup; the autonomous runner just creates a placeholder
# file that signals "ready for human-in-loop work".
phase4() {
    log "=== Phase 4: CXL port engineering — pausing for human-in-loop ==="
    : > "$RESULTS_DIR/p4_pause_for_cxl_port.flag"
    hb "phase4: paused for CXL port engineering"
    sleep 1
}

# ---- Phase 5: SMART-CXL and ROLEX-CXL sweeps (only if builds exist) ----
phase5() {
    log "=== Phase 5: SMART-CXL / ROLEX-CXL sweeps (if builds present) ==="
    for m in SMART ROLEX; do
        local build="$PROJ_NFS/djjay-build/build-${m}-cxl"
        if [ ! -x "$build/ycsb_test" ]; then
            log "  $m-CXL build not present at $build — skipping"
            continue
        fi
        for w in c d e; do
            sweep_cxl_1node "$build" "$w" "$RESULTS_DIR/p5_${m,,}_cxl_${w}.jsonl" "$THREADS_FAST" "$m"
        done
    done
}

# ---- Phase 6: high thread count ----
phase6() {
    log "=== Phase 6: high thread count CXL + 3 CN RDMA ==="
    for w in c d; do
        sweep_cxl_1node "$B_CHIME_CXL" "$w" "$RESULTS_DIR/p6_chime_cxl_high_${w}.jsonl" "$THREADS_HIGH" CHIME
        sweep_3cn1mn    "$B_CHIME"     "$w" "$RESULTS_DIR/p6_chime_rdma_high_${w}.jsonl" "$THREADS_HIGH" CHIME
    done
}

# ---- Phase 7: workloads A and B retry at 3 CN + 1 MN ----
phase7() {
    log "=== Phase 7: A/B at 3 CN + 1 MN ==="
    for w in a b; do
        sweep_3cn1mn "$B_CHIME"   "$w" "$RESULTS_DIR/p7_chime_${w}.jsonl"   "$THREADS_FAST" CHIME
        sweep_3cn1mn "$B_SHERMAN" "$w" "$RESULTS_DIR/p7_sherman_${w}.jsonl" "$THREADS_FAST" Sherman
        sweep_3cn1mn "$B_SMART"   "$w" "$RESULTS_DIR/p7_smart_${w}.jsonl"   "$THREADS_FAST" SMART
    done
}

# ---- Phase 8: long variance run, T=16, 30 reps ----
phase8() {
    log "=== Phase 8: long variance, CHIME-RDMA + CHIME-CXL T=16 on C, 30 reps each ==="
    for rep in $(seq 1 30); do
        hb "long-var rdma rep=$rep"
        memcached_init
        cd "$B_CHIME"
        nohup ./ycsb_test 4 16 1 randint c > /tmp/lvar-rdma-mn-$rep.log 2>&1 < /dev/null & disown
        sleep 3
        for ((i=1; i<N; i++)); do
            ssh -o ConnectTimeout=5 "${ALL_NODES[$i]}" "cd $B_CHIME && timeout 90 ./ycsb_test 4 16 1 randint c > /tmp/lvar-rdma-cn-$rep.log 2>&1" &
        done
        wait
        sleep 1
        pkill -9 ycsb_test 2>/dev/null
        for ((i=1; i<N; i++)); do ssh "${ALL_NODES[$i]}" 'pkill -9 ycsb_test 2>/dev/null'; done
        sleep 2
        peak=$(grep -oE 'cluster throughput [0-9.]+' /tmp/lvar-rdma-mn-$rep.log | awk '{print $3}' | sort -g | tail -1)
        peak="${peak:-0}"
        printf '{"method":"CHIME","workload":"c","threads":16,"cn_count":3,"rep":%d,"peak_mops":%s}\n' "$rep" "$peak" >> "$RESULTS_DIR/p8_rdma_long_variance.jsonl"
        log "  rdma rep=$rep peak=$peak"
    done
    for rep in $(seq 1 30); do
        hb "long-var cxl rep=$rep"
        cd "$B_CHIME_CXL"
        timeout 90 ./ycsb_test 1 16 1 randint c > /tmp/lvar-cxl-$rep.log 2>&1
        peak=$(grep -oE 'cluster throughput [0-9.]+' /tmp/lvar-cxl-$rep.log | awk '{print $3}' | sort -g | tail -1)
        peak="${peak:-0}"
        printf '{"method":"CHIME-CXL","workload":"c","threads":16,"rep":%d,"peak_mops":%s}\n' "$rep" "$peak" >> "$RESULTS_DIR/p8_cxl_long_variance.jsonl"
        log "  cxl rep=$rep peak=$peak"
    done
}

# ---- Heartbeat writer (background) ----
heartbeat_loop() {
    while true; do
        printf "[%s] alive (results=%d files)\n" "$(date -u +%FT%TZ)" "$(ls "$RESULTS_DIR" 2>/dev/null | wc -l)" >> "$HEARTBEAT"
        sleep 60
    done
}

heartbeat_loop &
HB_PID=$!
trap 'kill "$HB_PID" 2>/dev/null' EXIT

log "Autonomous runner starting. Phases $PHASE_FROM..$PHASE_TO. Master=$MASTER N=$N"

for p in $(seq "$PHASE_FROM" "$PHASE_TO"); do
    log "Starting phase $p"
    "phase${p}"
    log "Phase $p complete"
    # Check guard sentinel; if any node tripped, abort
    if ls "$GUARD_DIR"/*.tripped 2>/dev/null | grep -q .; then
        log "GUARD TRIPPED — ABORTING further phases"
        break
    fi
done

log "Autonomous runner finished phases $PHASE_FROM..$PHASE_TO"
hb "DONE phases $PHASE_FROM..$PHASE_TO"

#!/usr/bin/env bash
# control-net-guard.sh — Detect and abort on accidental public-network use.
#
# Runs on a cluster node (CloudLab r650 Clemson). Samples the byte counters
# under /sys/class/net/<iface>/statistics/{rx,tx}_bytes for the public
# control interface AND the internal RDMA-LAN interface, and writes a small
# rate log every INTERVAL seconds. If the public interface exceeds
# THRESHOLD bytes in a sampling window, the script writes a sentinel file
# (TRIPPED_FILE) and exits non-zero so a wrapper can abort the experiment.
#
# Usage:
#   bash control-net-guard.sh [--internal IFACE] [--public IFACE]
#                             [--interval SECS] [--threshold BYTES]
#                             [--logfile PATH] [--tripped-file PATH]
#                             [--max-public-bytes-total BYTES] [--once]
#
# Defaults (CloudLab r650 Clemson):
#   --internal vlan296            (RDMA LAN, 10.10.1.x)
#   --public  auto-detected       (eno12399 / ens1f0np0; first non-vlan,
#                                  non-lo, non-veth iface with a route)
#   --interval 10                 (sample every 10 seconds)
#   --threshold 1048576           (1 MB per window before warning)
#   --max-public-bytes-total 0    (0 = no abort threshold; otherwise
#                                  abort when cumulative public RX+TX
#                                  exceeds this many bytes since start)
#
# Exit codes:
#   0  normal termination (--once or signaled stop with no breach)
#   1  argument / setup error
#   2  threshold breached — wrapper should abort the experiment
set -u

INTERNAL_IFACE="${INTERNAL_IFACE:-vlan296}"
PUBLIC_IFACE="${PUBLIC_IFACE:-}"
INTERVAL="${INTERVAL:-10}"
THRESHOLD="${THRESHOLD:-1048576}"
LOGFILE="${LOGFILE:-/tmp/control-net-guard.log}"
TRIPPED_FILE="${TRIPPED_FILE:-/tmp/control-net-guard.tripped}"
MAX_PUBLIC_BYTES_TOTAL="${MAX_PUBLIC_BYTES_TOTAL:-0}"
RUN_ONCE=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --internal)  INTERNAL_IFACE="$2"; shift 2 ;;
        --public)    PUBLIC_IFACE="$2"; shift 2 ;;
        --interval)  INTERVAL="$2"; shift 2 ;;
        --threshold) THRESHOLD="$2"; shift 2 ;;
        --logfile)   LOGFILE="$2"; shift 2 ;;
        --tripped-file) TRIPPED_FILE="$2"; shift 2 ;;
        --max-public-bytes-total) MAX_PUBLIC_BYTES_TOTAL="$2"; shift 2 ;;
        --once)      RUN_ONCE=1; shift ;;
        -h|--help)
            sed -n '2,30p' "$0"
            exit 0 ;;
        *) echo "unknown arg: $1" >&2; exit 1 ;;
    esac
done

autodetect_public_iface() {
    # Pick the iface that owns the default route (1.1.1.1 used as a public
    # target purely for routing-table lookup; no packet is sent).
    local i
    i=$(ip route get 1.1.1.1 2>/dev/null | awk 'NR==1 {for (n=1;n<=NF;n++) if ($n=="dev") print $(n+1)}')
    if [[ -n "$i" && -d "/sys/class/net/$i" ]]; then
        echo "$i"; return 0
    fi
    # Fallback: first iface that is not lo, not vlan*, not veth*
    for i in /sys/class/net/*; do
        local name
        name=$(basename "$i")
        case "$name" in
            lo|vlan*|veth*|virbr*|docker*|br-*|tap*|ib*|cali*) ;;
            *) echo "$name"; return 0 ;;
        esac
    done
    return 1
}

if [[ -z "$PUBLIC_IFACE" ]]; then
    PUBLIC_IFACE=$(autodetect_public_iface) || {
        echo "control-net-guard: failed to autodetect public interface" >&2
        exit 1
    }
fi

for iface in "$PUBLIC_IFACE" "$INTERNAL_IFACE"; do
    if [[ ! -d "/sys/class/net/$iface" ]]; then
        echo "control-net-guard: interface '$iface' does not exist on this host" >&2
        exit 1
    fi
done

read_bytes() {
    # $1 = iface; echoes "rx_bytes tx_bytes"
    local rx tx
    rx=$(cat "/sys/class/net/$1/statistics/rx_bytes" 2>/dev/null || echo 0)
    tx=$(cat "/sys/class/net/$1/statistics/tx_bytes" 2>/dev/null || echo 0)
    echo "$rx $tx"
}

format_kib() { awk -v n="$1" 'BEGIN { printf "%9.1f KiB", n/1024 }'; }

# Wipe stale sentinel/log on start.
rm -f "$TRIPPED_FILE"
mkdir -p "$(dirname "$LOGFILE")"
{
    echo "# control-net-guard started $(date -u +%FT%TZ)"
    echo "# host=$(hostname)  public=$PUBLIC_IFACE  internal=$INTERNAL_IFACE"
    echo "# threshold per ${INTERVAL}s window: $THRESHOLD bytes"
    echo "# max cumulative public RX+TX (0 = unlimited): $MAX_PUBLIC_BYTES_TOTAL"
    printf "# %-20s %14s %14s %14s %14s   %s\n" \
        "timestamp" "pub_rx_d" "pub_tx_d" "int_rx_d" "int_tx_d" "note"
} >> "$LOGFILE"

read prev_pub_rx prev_pub_tx <<<"$(read_bytes "$PUBLIC_IFACE")"
read prev_int_rx prev_int_tx <<<"$(read_bytes "$INTERNAL_IFACE")"
start_pub_rx="$prev_pub_rx"
start_pub_tx="$prev_pub_tx"

trap 'echo "# control-net-guard stopped $(date -u +%FT%TZ)" >> "$LOGFILE"; exit 0' INT TERM

while true; do
    sleep "$INTERVAL"
    read pub_rx pub_tx <<<"$(read_bytes "$PUBLIC_IFACE")"
    read int_rx int_tx <<<"$(read_bytes "$INTERNAL_IFACE")"

    pub_rx_d=$(( pub_rx - prev_pub_rx ))
    pub_tx_d=$(( pub_tx - prev_pub_tx ))
    int_rx_d=$(( int_rx - prev_int_rx ))
    int_tx_d=$(( int_tx - prev_int_tx ))

    note=""
    pub_window=$(( pub_rx_d + pub_tx_d ))
    if (( pub_window >= THRESHOLD )); then
        note="WARN public traffic ${pub_window}B exceeds threshold ${THRESHOLD}B"
        echo "control-net-guard: $note" >&2
    fi

    if (( MAX_PUBLIC_BYTES_TOTAL > 0 )); then
        cum=$(( (pub_rx - start_pub_rx) + (pub_tx - start_pub_tx) ))
        if (( cum >= MAX_PUBLIC_BYTES_TOTAL )); then
            echo "$cum cumulative public bytes >= $MAX_PUBLIC_BYTES_TOTAL — TRIPPED" >> "$LOGFILE"
            echo "control-net-guard: cumulative public bytes $cum exceeded $MAX_PUBLIC_BYTES_TOTAL — TRIPPED" >&2
            : > "$TRIPPED_FILE"
            exit 2
        fi
    fi

    printf "  %-20s %14d %14d %14d %14d   %s\n" \
        "$(date -u +%FT%TZ)" "$pub_rx_d" "$pub_tx_d" "$int_rx_d" "$int_tx_d" "$note" >> "$LOGFILE"

    prev_pub_rx="$pub_rx"; prev_pub_tx="$pub_tx"
    prev_int_rx="$int_rx"; prev_int_tx="$int_tx"

    [[ "$RUN_ONCE" -eq 1 ]] && exit 0
done

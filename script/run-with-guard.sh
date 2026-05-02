#!/usr/bin/env bash
# run-with-guard.sh — Run an experiment binary with control-net-guard active.
#
# Wraps any ycsb_test invocation (or any other command) so that
# control-net-guard.sh runs in the background, and the wrapper aborts
# the experiment if the guard sentinel file appears.
#
# Usage:
#   bash run-with-guard.sh -- <command> [args...]
#
# Example:
#   bash run-with-guard.sh -- ./ycsb_test 2 16 1 randint c
#
# Environment overrides (passed through to the guard):
#   CONTROL_NET_GUARD_PATH (default: same dir as this script)
#   GUARD_INTERVAL          (default: 10)
#   GUARD_THRESHOLD         (default: 1048576)
#   GUARD_MAX_TOTAL         (default: 0; set non-zero to enable hard cap)
#   GUARD_LOGFILE           (default: /tmp/control-net-guard.log)
#   GUARD_TRIPPED_FILE      (default: /tmp/control-net-guard.tripped)
#   GUARD_PUBLIC            (default: auto)
#   GUARD_INTERNAL          (default: vlan296)
set -u

SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
GUARD="${CONTROL_NET_GUARD_PATH:-$SCRIPT_DIR/control-net-guard.sh}"
GUARD_INTERVAL="${GUARD_INTERVAL:-10}"
GUARD_THRESHOLD="${GUARD_THRESHOLD:-1048576}"
GUARD_MAX_TOTAL="${GUARD_MAX_TOTAL:-0}"
GUARD_LOGFILE="${GUARD_LOGFILE:-/tmp/control-net-guard.log}"
GUARD_TRIPPED_FILE="${GUARD_TRIPPED_FILE:-/tmp/control-net-guard.tripped}"

if [[ "$#" -lt 1 || "$1" != "--" ]]; then
    echo "usage: $0 -- <command> [args...]" >&2
    exit 1
fi
shift

if [[ ! -x "$GUARD" ]]; then
    echo "guard script not found or not executable: $GUARD" >&2
    exit 1
fi

# Build guard args
GUARD_ARGS=(
    --interval "$GUARD_INTERVAL"
    --threshold "$GUARD_THRESHOLD"
    --logfile "$GUARD_LOGFILE"
    --tripped-file "$GUARD_TRIPPED_FILE"
)
[[ -n "${GUARD_PUBLIC:-}" ]]   && GUARD_ARGS+=( --public "$GUARD_PUBLIC" )
[[ -n "${GUARD_INTERNAL:-}" ]] && GUARD_ARGS+=( --internal "$GUARD_INTERNAL" )
(( GUARD_MAX_TOTAL > 0 ))      && GUARD_ARGS+=( --max-public-bytes-total "$GUARD_MAX_TOTAL" )

rm -f "$GUARD_TRIPPED_FILE"
bash "$GUARD" "${GUARD_ARGS[@]}" &
GUARD_PID=$!
trap 'kill "$GUARD_PID" 2>/dev/null' EXIT

# Run the command
"$@" &
CMD_PID=$!

# Wait for the command, watching the tripped sentinel.
while kill -0 "$CMD_PID" 2>/dev/null; do
    if [[ -e "$GUARD_TRIPPED_FILE" ]]; then
        echo "run-with-guard: control-net guard tripped — killing experiment $CMD_PID" >&2
        kill -TERM "$CMD_PID" 2>/dev/null
        sleep 2
        kill -KILL "$CMD_PID" 2>/dev/null
        exit 2
    fi
    sleep 1
done

wait "$CMD_PID"
EXIT=$?
echo "run-with-guard: command exited $EXIT (guard log: $GUARD_LOGFILE)"
exit "$EXIT"

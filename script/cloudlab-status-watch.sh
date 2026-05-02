#!/usr/bin/env bash
# cloudlab-status-watch.sh — One-shot status check for our CloudLab reservations and experiments.
#
# Lists each upcoming/active reservation and experiment, with time-to-start
# and time-to-expire. Designed to be run from the laptop on a cron / loop or
# on demand. Replaces the ssh-polling pattern that triggered CloudLab's
# unusual-traffic warning: this hits the CloudLab portal API directly
# (https://boss.emulab.net:43794) rather than ssh-ing into a node.
#
# Usage:
#   bash cloudlab-status-watch.sh           # one-shot
#   bash cloudlab-status-watch.sh --watch   # loop every 5 min until interrupted
#   bash cloudlab-status-watch.sh --json    # raw JSON (machine-readable)
#
# Requires:
#   .venv/bin/portal-cli (from portal-api package, see day1-runbook.md)
#   files/cloudlab.jwt
set -u

cd "$(dirname "$0")/.."
JWT_FILE="${CLOUDLAB_JWT:-files/cloudlab.jwt}"
PORTAL_URL="${CLOUDLAB_PORTAL_URL:-https://boss.emulab.net:43794}"
WATCH=0
RAW=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --watch) WATCH=1; shift ;;
        --json)  RAW=1; shift ;;
        -h|--help) sed -n '2,18p' "$0"; exit 0 ;;
        *) echo "unknown arg: $1" >&2; exit 1 ;;
    esac
done

if [[ ! -f "$JWT_FILE" ]]; then
    echo "missing JWT file: $JWT_FILE" >&2
    exit 1
fi

if [[ ! -x .venv/bin/portal-cli ]]; then
    echo "portal-cli not found at .venv/bin/portal-cli — run: pip install portal-api" >&2
    exit 1
fi

run_portal() {
    .venv/bin/portal-cli --portal-url "$PORTAL_URL" --token "$(cat "$JWT_FILE")" "$@"
}

format_dt() {
    # ISO 8601 -> "YYYY-MM-DD HH:MM UTC (Δ)"
    python3 -c "
import sys, datetime
s = sys.argv[1]
if not s or s == 'None': print('-'); sys.exit(0)
dt = datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
now = datetime.datetime.now(datetime.timezone.utc)
delta = dt - now
h = int(delta.total_seconds() // 3600)
m = int((delta.total_seconds() % 3600) // 60)
sign = 'in' if delta.total_seconds() > 0 else 'ago'
print(dt.strftime('%Y-%m-%d %H:%M UTC') + f' ({sign} {abs(h)}h {abs(m)}m)')
" "$1"
}

print_status() {
    local rg_json="$1"
    local exp_json="$2"

    if (( RAW )); then
        printf '%s\n%s\n' "$rg_json" "$exp_json"
        return
    fi

    echo "=== Reservations ==="
    echo "$rg_json" | python3 -c "
import sys, json, datetime
d = json.load(sys.stdin)
for r in d.get('resgroups', []):
    nodes = r.get('nodetypes', {}).get('nodetypes', [])
    cnt = sum(n.get('count', 0) for n in nodes)
    types = ','.join(sorted({n.get('nodetype','?') for n in nodes}))
    print(f\"id={r['id'][:8]}  start={r.get('start_at')}  expires={r.get('expires_at')}  {cnt}x{types}  reason={r.get('reason','')[:40]}\")
"

    echo
    echo "=== Active experiments ==="
    echo "$exp_json" | python3 -c "
import sys, json
d = json.load(sys.stdin)
exps = d.get('experiments', [])
if not exps:
    print('  (none)')
else:
    for e in exps:
        print(f\"  name={e['name']}  status={e['status']}  expires={e.get('expires_at')}  bindings={e.get('bindings')}\")
"

    echo
    echo "=== Pretty timeline ==="
    echo "$rg_json" | python3 -c "
import sys, json, datetime
d = json.load(sys.stdin)
now = datetime.datetime.now(datetime.timezone.utc)
events = []
for r in d.get('resgroups', []):
    nodes = r.get('nodetypes', {}).get('nodetypes', [])
    cnt = sum(n.get('count', 0) for n in nodes)
    types = ','.join(sorted({n.get('nodetype','?') for n in nodes}))
    rid = r['id'][:8]
    events.append((r['start_at'],   f'reservation {rid} ({cnt}x{types}) STARTS'))
    events.append((r['expires_at'], f'reservation {rid} EXPIRES'))
events.sort()
for ts, label in events:
    if not ts:
        continue
    dt = datetime.datetime.fromisoformat(ts.replace('Z','+00:00'))
    delta = dt - now
    if delta.total_seconds() < -3600*48:
        continue  # skip stuff more than 48h in the past
    h = int(delta.total_seconds() // 3600)
    m = int((delta.total_seconds() % 3600) // 60)
    sign = 'in ' if delta.total_seconds() > 0 else '  '
    print(f'  {dt.strftime(\"%Y-%m-%d %H:%M UTC\")}   {sign}{h:+4d}h {abs(m):2d}m   {label}')
"
}

while true; do
    rg=$(run_portal resgroup list --creator djjay 2>/dev/null)
    exps=$(run_portal experiment list 2>/dev/null)
    print_status "$rg" "$exps"
    [[ "$WATCH" -eq 0 ]] && break
    echo
    echo "(refresh in 5 min — Ctrl-C to stop)"
    sleep 300
done

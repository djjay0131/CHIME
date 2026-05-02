#!/usr/bin/env bash
# launch-experiment.sh — Create a CloudLab experiment on the chime-r650-clemson-lan profile.
#
# Usage:
#   bash script/launch-experiment.sh [name] [n]
#
# Defaults: name = chime-r650-may2 ; n = 4 (matches the 312ca700 reservation).
# After provisioning, run:  bash script/prep-experiment.sh <name>
set -u
cd "$(dirname "$0")/.."

NAME="${1:-chime-r650-may2}"
N="${2:-4}"
JWT_FILE="${CLOUDLAB_JWT:-files/cloudlab.jwt}"
PORTAL_URL="${CLOUDLAB_PORTAL_URL:-https://boss.emulab.net:43794}"
PROJECT="${CLOUDLAB_PROJECT:-CS620426SP}"
PROFILE_NAME="${CLOUDLAB_PROFILE:-chime-r650-clemson-lan}"

run_portal() {
    .venv/bin/portal-cli --portal-url "$PORTAL_URL" --token "$(cat "$JWT_FILE")" "$@"
}

echo "Creating experiment '$NAME' from profile '$PROFILE_NAME' (project=$PROJECT) with n=$N..."
run_portal experiment create \
    --name "$NAME" \
    --project "$PROJECT" \
    --profile-name "$PROFILE_NAME" \
    --profile-project "$PROJECT" \
    --bindings '{"n":"'$N'"}' 2>&1 | tail -20

echo
echo "Watch with:  bash script/cloudlab-status-watch.sh --watch"
echo "Once status=ready, run: bash script/prep-experiment.sh $NAME"

#!/bin/bash
# Clone CHIME and sibling repos (SMART, ROLEX, Marlin) to home directory.
# Run on each node from a directory containing CHIME (or after cloning CHIME).
# Usage: cd ~ && bash clone-repos.sh
# Or: cd ~/CHIME && bash script/clone-repos.sh

set -e
cd "$HOME"

clone_if_missing() {
    local url="$1"
    local dir="$2"
    if [ -d "$dir" ]; then
        echo "[SKIP] $dir already exists"
    else
        echo "[CLONE] $url -> $dir"
        git clone "$url" "$dir"
    fi
}

# CHIME should already be present (clone manually or via CloudLab profile)
if [ ! -d "CHIME" ]; then
    echo "CHIME not found in $HOME. Clone it first or run from CHIME repo."
    exit 1
fi

clone_if_missing "https://github.com/dmemsys/SMART" "SMART"
clone_if_missing "https://github.com/River861/ROLEX" "ROLEX"
clone_if_missing "https://github.com/River861/Marlin" "Marlin"

echo "Done. Verify: ls ~/CHIME ~/SMART ~/ROLEX ~/Marlin"

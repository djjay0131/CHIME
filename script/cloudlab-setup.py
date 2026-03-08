#!/usr/bin/env python3
"""
CloudLab experiment automation for CHIME reproduction.

Prerequisites:
  pip install cloudlabclient[cli]

  Export your CloudLab Portal API token:
    export PORTAL_TOKEN="your_token_here"

  Get your token from CloudLab web UI: click your name -> "Portal API Token"

Usage:
  # Search for available 10x r650 slot (7 days)
  python3 script/cloudlab-setup.py search

  # Create reservation for 10x r650 nodes
  python3 script/cloudlab-setup.py reserve

  # Create experiment using the CHIME cloudlab profile
  python3 script/cloudlab-setup.py create

  # Check experiment status and get SSH info
  python3 script/cloudlab-setup.py status

  # Extend experiment by N hours
  python3 script/cloudlab-setup.py extend 48

  # Setup all nodes (install deps, clone repos, generate YCSB)
  python3 script/cloudlab-setup.py setup

  # Terminate experiment
  python3 script/cloudlab-setup.py terminate
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────

CLOUDLAB_PORTAL = "https://www.cloudlab.us:43794"
PROJECT = os.environ.get("CLOUDLAB_PROJECT", "CS620426SP")
PROFILE_NAME = "chime-r650"  # we'll create this profile
PROFILE_PROJECT = ""  # set to your project or PortalProfiles

# r650 node specs
NODE_TYPE = "r650"
NODE_COUNT = 10
DURATION_HOURS = 168  # 7 days
CLUSTER_URN = "urn:publicid:IDN+cloudlab.us+authority+cm"  # Utah cluster for r650

# Repos to clone on each node
REPOS = [
    "https://github.com/djjay0131/CHIME.git",
    "https://github.com/dmemsys/SMART.git",
    "https://github.com/River861/ROLEX.git",
    "https://github.com/River861/Marlin.git",
]

STATE_FILE = Path(__file__).parent.parent / ".cloudlab-state.json"


def get_token():
    token = os.environ.get("PORTAL_TOKEN")
    if not token:
        print("ERROR: Set PORTAL_TOKEN environment variable.")
        print("Get your token from CloudLab: click your name -> 'Portal API Token'")
        sys.exit(1)
    return token


def run_cli(*args, capture=True):
    """Run portal-cli command and return output."""
    cmd = [
        "portal-cli",
        "--token", get_token(),
        "--portal-url", CLOUDLAB_PORTAL,
    ] + list(args)
    if capture:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"ERROR: {result.stderr}")
            sys.exit(1)
        return result.stdout.strip()
    else:
        subprocess.run(cmd)


def save_state(data):
    """Save experiment state to file."""
    existing = load_state()
    existing.update(data)
    STATE_FILE.write_text(json.dumps(existing, indent=2))


def load_state():
    """Load experiment state from file."""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


# ──────────────────────────────────────────────
# Commands
# ──────────────────────────────────────────────

def cmd_search(args):
    """Search for available r650 node slots."""
    print(f"Searching for {NODE_COUNT}x {NODE_TYPE} nodes for {DURATION_HOURS}h...")

    res_data = {
        "nodetypes": [{
            "count": NODE_COUNT,
            "nodetype": NODE_TYPE,
            "urn": CLUSTER_URN,
        }]
    }
    tmpfile = Path("/tmp/cloudlab-search.json")
    tmpfile.write_text(json.dumps(res_data))

    output = run_cli(
        "resgroup", "search",
        "--project", PROJECT,
        "--duration", str(DURATION_HOURS),
        "--nodetypes", f"@{tmpfile}",
    )
    print(output)


def cmd_reserve(args):
    """Create a reservation for r650 nodes."""
    print(f"Creating reservation: {NODE_COUNT}x {NODE_TYPE} for {DURATION_HOURS}h...")

    res_data = {
        "nodetypes": [{
            "count": NODE_COUNT,
            "nodetype": NODE_TYPE,
            "urn": CLUSTER_URN,
        }]
    }
    tmpfile = Path("/tmp/cloudlab-reserve.json")
    tmpfile.write_text(json.dumps(res_data))

    output = run_cli(
        "resgroup", "create",
        "--project", PROJECT,
        "--reason", "CS 6204 course project: reproducing CHIME (SOSP'24) experiments",
        "--start-at", "now",
        "--duration", str(DURATION_HOURS),
        "--nodetypes", f"@{tmpfile}",
    )
    print(output)

    try:
        res_id = json.loads(output).get("id")
        if res_id:
            save_state({"reservation_id": res_id})
            print(f"\nReservation ID: {res_id} (saved to {STATE_FILE})")
    except (json.JSONDecodeError, AttributeError):
        print(output)


def cmd_create(args):
    """Create an experiment using the CHIME profile."""
    print(f"Creating experiment with {NODE_COUNT}x {NODE_TYPE} nodes...")

    bindings = {
        "nodeCount": str(NODE_COUNT),
        "phystype": NODE_TYPE,
        "osImage": "default",
    }
    tmpfile = Path("/tmp/cloudlab-bindings.json")
    tmpfile.write_text(json.dumps(bindings))

    exp_args = [
        "experiment", "create",
        "--name", "chime-reproduce",
        "--project", PROJECT,
        "--duration", str(DURATION_HOURS),
        "--bindings", f"@{tmpfile}",
    ]

    # Use the CHIME cloudlab profile if available
    if PROFILE_NAME and PROFILE_PROJECT:
        exp_args.extend(["--profile-name", PROFILE_NAME, "--profile-project", PROFILE_PROJECT])
    elif args.profile:
        exp_args.extend(["--profile-name", args.profile])

    output = run_cli(*exp_args)
    print(output)

    try:
        exp_id = json.loads(output).get("id")
        if exp_id:
            save_state({"experiment_id": exp_id})
            print(f"\nExperiment ID: {exp_id} (saved to {STATE_FILE})")
    except (json.JSONDecodeError, AttributeError):
        print(output)


def cmd_status(args):
    """Get experiment status and node info."""
    state = load_state()
    exp_id = state.get("experiment_id") or args.experiment_id
    if not exp_id:
        print("No experiment ID found. Run 'create' first or pass --experiment-id.")
        sys.exit(1)

    output = run_cli("--elaborate", "experiment", "get", "--experiment-id", exp_id)
    print(output)

    # Also get manifests for SSH info
    print("\n--- Manifests (SSH info) ---")
    manifests = run_cli("experiment", "manifests", "get", "--experiment-id", exp_id)
    print(manifests)


def cmd_extend(args):
    """Extend experiment duration."""
    state = load_state()
    exp_id = state.get("experiment_id") or args.experiment_id
    if not exp_id:
        print("No experiment ID found.")
        sys.exit(1)

    hours = args.hours
    print(f"Extending experiment {exp_id} by {hours} hours...")
    output = run_cli(
        "experiment", "extend",
        "--experiment-id", exp_id,
        "--extend-by", str(hours),
    )
    print(output)


def cmd_terminate(args):
    """Terminate the experiment."""
    state = load_state()
    exp_id = state.get("experiment_id") or args.experiment_id
    if not exp_id:
        print("No experiment ID found.")
        sys.exit(1)

    print(f"Terminating experiment {exp_id}...")
    output = run_cli("experiment", "terminate", "--experiment-id", exp_id)
    print(output)


def cmd_setup(args):
    """SSH into all nodes and run setup commands."""
    # Load common.json to get IPs
    common_json = Path(__file__).parent.parent / "exp" / "params" / "common.json"
    with open(common_json) as f:
        params = json.load(f)

    cluster_ips = params["cluster_ips"]
    home_dir = params["home_dir"]
    user = args.user or "root"

    print(f"Setting up {len(cluster_ips)} nodes as {user}...")
    print(f"Home dir: {home_dir}")

    # Phase 1: Install MLNX OFED and libraries on all nodes in parallel
    setup_cmds = [
        # Resize partition
        f"cd {home_dir}/CHIME && bash script/resizePartition.sh",
        # Install Mellanox OFED
        f"cd {home_dir}/CHIME && bash script/installMLNX.sh",
        # Install libraries
        f"cd {home_dir}/CHIME && bash script/installLibs.sh",
        # Install Python deps
        "pip3 install paramiko func_timeout matplotlib numpy",
        # Setup hugepages
        "echo 36864 > /proc/sys/vm/nr_hugepages",
    ]

    # Phase 2: Clone repos on all nodes
    clone_cmds = []
    for repo in REPOS:
        repo_name = repo.split("/")[-1].replace(".git", "")
        clone_cmds.append(f"cd {home_dir} && [ -d {repo_name} ] || git clone {repo}")

    # Phase 3: Generate YCSB workloads on all nodes
    ycsb_cmd = f"cd {home_dir}/CHIME/ycsb && [ -d workloads ] || bash generate_full_workloads.sh"

    print("\n=== Phase 1: Install dependencies (all nodes in parallel) ===")
    processes = []
    for ip in cluster_ips:
        for cmd in setup_cmds:
            full_cmd = f"ssh -o StrictHostKeyChecking=no {user}@{ip} '{cmd}'"
            print(f"  [{ip}] {cmd[:80]}...")
            p = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            processes.append((ip, cmd, p))

    for ip, cmd, p in processes:
        p.wait()
        if p.returncode != 0:
            print(f"  WARNING [{ip}] Failed: {cmd[:60]}")
            print(f"    stderr: {p.stderr.read().decode()[:200]}")

    print("\n=== Phase 2: Clone repos (all nodes in parallel) ===")
    processes = []
    for ip in cluster_ips:
        for cmd in clone_cmds:
            full_cmd = f"ssh -o StrictHostKeyChecking=no {user}@{ip} '{cmd}'"
            print(f"  [{ip}] {cmd[:80]}...")
            p = subprocess.Popen(full_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            processes.append((ip, cmd, p))

    for ip, cmd, p in processes:
        p.wait()
        if p.returncode != 0:
            print(f"  WARNING [{ip}] Failed: {cmd[:60]}")

    print("\n=== Phase 3: Generate YCSB workloads (all nodes, ~1.5h) ===")
    print("Running in background on each node via nohup...")
    for ip in cluster_ips:
        full_cmd = f"ssh -o StrictHostKeyChecking=no {user}@{ip} 'nohup bash -c \"{ycsb_cmd}\" > /tmp/ycsb_gen.log 2>&1 &'"
        print(f"  [{ip}] Starting YCSB generation...")
        subprocess.run(full_cmd, shell=True)

    print("\nYCSB generation started on all nodes. Check progress with:")
    print(f"  ssh {user}@<node_ip> 'tail -f /tmp/ycsb_gen.log'")
    print(f"\nSetup complete! Next: update {common_json} with correct IPs and paths.")


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="CloudLab automation for CHIME experiments")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # search
    subparsers.add_parser("search", help="Search for available r650 node slots")

    # reserve
    subparsers.add_parser("reserve", help="Create a reservation for r650 nodes")

    # create
    p_create = subparsers.add_parser("create", help="Create an experiment")
    p_create.add_argument("--profile", help="Profile name to use")

    # status
    p_status = subparsers.add_parser("status", help="Get experiment status")
    p_status.add_argument("--experiment-id", help="Experiment ID")

    # extend
    p_extend = subparsers.add_parser("extend", help="Extend experiment duration")
    p_extend.add_argument("hours", type=int, help="Hours to extend by")
    p_extend.add_argument("--experiment-id", help="Experiment ID")

    # setup
    p_setup = subparsers.add_parser("setup", help="Setup all nodes (install deps, clone, YCSB)")
    p_setup.add_argument("--user", default="root", help="SSH user (default: root)")

    # terminate
    p_term = subparsers.add_parser("terminate", help="Terminate experiment")
    p_term.add_argument("--experiment-id", help="Experiment ID")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "search": cmd_search,
        "reserve": cmd_reserve,
        "create": cmd_create,
        "status": cmd_status,
        "extend": cmd_extend,
        "setup": cmd_setup,
        "terminate": cmd_terminate,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()

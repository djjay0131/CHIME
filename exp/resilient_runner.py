#!/usr/bin/env python3
"""
resilient_runner.py — Resilient experiment runner for CHIME r650 cluster.

Wraps existing fig_*.py scripts with:
  - Per-experiment timeout and retry (max 2 attempts)
  - Watchdog thread for long-running experiments (fig_12)
  - Checkpoint-based resume: detects completed data points in _partial.json
  - Failure classification: transient (retry) vs systemic (reconfigure cluster)
  - Incremental rsync backup after each completed experiment
  - Summary report at end

Usage (on master node, in tmux):
  cd ~/CHIME/exp && python3 resilient_runner.py

Environment variables:
  RSYNC_TARGET  — user@laptop:path for incremental backup (optional)
  HEALTHY_FILE  — path to healthy_nodes.txt (default: ../construction/scripts/healthy_nodes.txt)

Execution order: fig_12 first (primary result), then shorter experiments.
"""

import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path


# ---- Configuration ----

EXPERIMENTS = [
    # (script_name, timeout_seconds, is_long_running)
    ("fig_12",                 9 * 3600, True),    # 7.5h expected, 9h timeout
    ("fig_15b",                50 * 60,  False),
    ("fig_15a",                55 * 60,  False),
    ("fig_14",                 45 * 60,  False),
    ("extra_cache_sensitivity", 45 * 60, False),
    ("extra_value_size",       45 * 60,  False),
    ("extra_uniform_dist",     45 * 60,  False),
    ("fig_03a",                35 * 60,  False),
]

MAX_RETRIES = 2
WATCHDOG_INTERVAL = 300  # 5 minutes
WATCHDOG_STALL_FACTOR = 3  # stall if no progress after N intervals

RESULTS_DIR = Path("results")
PARAMS_DIR = Path("params")
RSYNC_TARGET = os.environ.get("RSYNC_TARGET", "")
HEALTHY_FILE = Path(os.environ.get(
    "HEALTHY_FILE",
    str(Path(__file__).parent.parent / "construction" / "scripts" / "healthy_nodes.txt")
))
CHIME_ROOT = Path(__file__).parent.parent


def log(msg):
    ts = time.strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


# ---- Checkpoint Detection ----

def count_partial_points(exp_name):
    """Count completed data points in _partial.json files for an experiment.

    Returns dict: {workload_name: {method: count}} or empty dict if no partials.
    """
    completed = {}
    for partial_file in RESULTS_DIR.glob(f"fig_{exp_name.replace('fig_', '')}_*_partial.json"):
        try:
            with open(partial_file) as f:
                data = json.load(f)
            # Extract workload name from filename: fig_12_c_partial.json -> c
            parts = partial_file.stem.split("_")
            # Remove 'fig', exp_num, and 'partial' to get workload name
            wl_name = "_".join(parts[2:-1])  # e.g., 'c', 'la', 'a'
            method_counts = {}
            for method in data.get("methods", []):
                x_data = data.get("X_data", {}).get(method, [])
                method_counts[method] = len(x_data)
            completed[wl_name] = method_counts
        except (json.JSONDecodeError, KeyError, IndexError):
            continue
    return completed


def total_completed_points(exp_name):
    """Total number of data points completed across all partials."""
    completed = count_partial_points(exp_name)
    return sum(
        count
        for methods in completed.values()
        for count in methods.values()
    )


# ---- Cluster Management ----

def get_healthy_nodes():
    """Read healthy nodes from file."""
    if HEALTHY_FILE.exists():
        return [line.strip() for line in HEALTHY_FILE.read_text().splitlines() if line.strip()]
    return []


def get_healthy_csv():
    """Get healthy nodes as comma-separated string."""
    return ",".join(get_healthy_nodes())


def cleanup_cluster():
    """Kill any hanging ycsb_test processes on all healthy nodes."""
    nodes = get_healthy_csv()
    if not nodes:
        return
    try:
        subprocess.run(
            ["bash", str(CHIME_ROOT / "script" / "run-on-nodes.sh"),
             nodes, "killall -9 ycsb_test 2>/dev/null || true"],
            timeout=30, capture_output=True
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass


def check_node_health(node):
    """Check if a node is reachable via SSH."""
    try:
        result = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=no",
             node, "echo ok"],
            timeout=10, capture_output=True, text=True
        )
        return result.returncode == 0 and "ok" in result.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def reconfigure_cluster(failed_node):
    """Exclude a failed node and reconfigure the cluster.

    Returns True if reconfiguration succeeded, False if cluster is too small.
    """
    nodes = get_healthy_nodes()
    if failed_node in nodes:
        nodes.remove(failed_node)
        log(f"  Excluded {failed_node}. {len(nodes)} nodes remaining.")

    cn_count = len(nodes) - 1  # reserve 1 for MN
    if cn_count < 5:
        log(f"  FATAL: Only {cn_count} CN remaining. Cannot continue.")
        return False

    # Update healthy_nodes.txt
    HEALTHY_FILE.write_text("\n".join(nodes) + "\n")

    # Re-patch CN count
    try:
        subprocess.run(
            ["python3", str(CHIME_ROOT / "construction" / "scripts" / "patch-cn-count.py"),
             str(cn_count)],
            timeout=30, capture_output=True, check=True
        )
        log(f"  Patched CN count to {cn_count}")
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
        log(f"  WARNING: Failed to patch CN count: {e}")

    # Restart memcached
    master = nodes[0]
    try:
        subprocess.run(
            ["ssh", "-o", "ConnectTimeout=10", master,
             "cd ~/CHIME/build && /bin/bash ../script/restartMemc.sh"],
            timeout=30, capture_output=True
        )
        log(f"  Restarted memcached on {master}")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        log(f"  WARNING: Failed to restart memcached")

    return True


# ---- Rsync Backup ----

def rsync_results():
    """Incremental backup of results to local machine."""
    if not RSYNC_TARGET:
        return
    try:
        subprocess.run(
            ["rsync", "-az", str(RESULTS_DIR) + "/", RSYNC_TARGET],
            timeout=120, capture_output=True
        )
        log(f"  Results synced to {RSYNC_TARGET}")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        log(f"  WARNING: rsync failed")


# ---- Watchdog ----

class ExperimentWatchdog:
    """Monitors a long-running experiment by polling _partial.json for progress.

    Detects stalls and node failures. Runs in a background thread.
    """

    def __init__(self, exp_name, process):
        self.exp_name = exp_name
        self.process = process
        self.last_point_count = total_completed_points(exp_name)
        self.stall_count = 0
        self.failed_node = None
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=10)

    @property
    def detected_stall(self):
        return self.stall_count >= WATCHDOG_STALL_FACTOR

    @property
    def detected_systemic_failure(self):
        return self.failed_node is not None

    def _run(self):
        while not self._stop.wait(WATCHDOG_INTERVAL):
            if self.process.poll() is not None:
                break  # Process finished

            current = total_completed_points(self.exp_name)
            if current > self.last_point_count:
                # Progress — reset stall counter
                delta = current - self.last_point_count
                self.last_point_count = current
                self.stall_count = 0
                log(f"  [watchdog] {self.exp_name}: +{delta} points (total: {current})")
            else:
                self.stall_count += 1
                log(f"  [watchdog] {self.exp_name}: no progress ({self.stall_count}/{WATCHDOG_STALL_FACTOR})")

                if self.detected_stall:
                    # Check node health
                    for node in get_healthy_nodes():
                        if not check_node_health(node):
                            self.failed_node = node
                            log(f"  [watchdog] Node {node} unreachable — systemic failure")
                            # Kill the experiment process
                            self.process.kill()
                            return

                    # All nodes reachable but still stalled — transient
                    log(f"  [watchdog] All nodes reachable but stalled — transient failure")
                    self.process.kill()
                    return


# ---- Experiment Runner ----

def run_experiment(name, timeout_sec, is_long_running):
    """Run a single experiment with timeout, retry, watchdog, and checkpoint resume."""

    for attempt in range(1, MAX_RETRIES + 1):
        # Check how many points we already have (for resume logging)
        existing_points = total_completed_points(name)
        if existing_points > 0 and attempt > 1:
            log(f"  Resuming with {existing_points} existing data points")

        log(f"{name} — attempt {attempt}/{MAX_RETRIES}")

        watchdog = None
        try:
            # Start the experiment as a subprocess
            proc = subprocess.Popen(
                ["python3", f"{name}.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            # Start watchdog for long-running experiments
            if is_long_running:
                watchdog = ExperimentWatchdog(name, proc)
                watchdog.start()

            # Wait for completion with timeout
            try:
                stdout, _ = proc.communicate(timeout=timeout_sec)

                # Log last few lines of output
                if stdout:
                    last_lines = stdout.strip().split("\n")[-5:]
                    for line in last_lines:
                        log(f"  [{name}] {line}")

                if proc.returncode == 0:
                    new_points = total_completed_points(name)
                    log(f"  OK {name} completed ({new_points} total data points)")
                    rsync_results()
                    return True
                else:
                    log(f"  FAIL {name} (rc={proc.returncode})")

            except subprocess.TimeoutExpired:
                log(f"  TIMEOUT {name} after {timeout_sec // 60}m")
                proc.kill()
                proc.wait()

        finally:
            if watchdog:
                watchdog.stop()

                # Handle watchdog-detected failures
                if watchdog.detected_systemic_failure:
                    log(f"  Systemic failure: node {watchdog.failed_node} down")
                    if not reconfigure_cluster(watchdog.failed_node):
                        log(f"  Cannot continue — cluster too small")
                        return False

        # Cleanup between retries
        cleanup_cluster()
        time.sleep(5)

    log(f"  SKIP {name} after {MAX_RETRIES} attempts")
    return False


# ---- Main ----

def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    RESULTS_DIR.mkdir(exist_ok=True)

    log("=== CHIME Resilient Experiment Runner ===")
    log(f"Experiments: {len(EXPERIMENTS)}")
    log(f"Healthy nodes: {len(get_healthy_nodes())}")
    log(f"CN count: {len(get_healthy_nodes()) - 1}")
    log(f"Rsync target: {RSYNC_TARGET or '(none)'}")
    log("")

    results = {}
    start_time = time.time()

    for name, timeout, is_long in EXPERIMENTS:
        # Check if script exists
        if not Path(f"{name}.py").exists():
            log(f"SKIP {name} — script not found")
            results[name] = None
            continue

        results[name] = run_experiment(name, timeout, is_long)
        log("")

    elapsed = time.time() - start_time
    elapsed_h = int(elapsed // 3600)
    elapsed_m = int((elapsed % 3600) // 60)

    # Final rsync
    rsync_results()

    # Summary
    log("=== EXPERIMENT SUMMARY ===")
    log(f"Total time: {elapsed_h}h {elapsed_m}m")
    log("")
    for name, ok in results.items():
        if ok is None:
            status = "SKIP (not found)"
        elif ok:
            status = "OK"
            points = total_completed_points(name)
            if points > 0:
                status += f" ({points} points)"
        else:
            status = "FAILED"
        log(f"  [{status}] {name}")

    failed = [n for n, ok in results.items() if ok is False]
    if failed:
        log(f"\n{len(failed)} experiment(s) failed: {', '.join(failed)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

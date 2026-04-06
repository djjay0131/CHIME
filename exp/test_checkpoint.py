#!/usr/bin/env python3
"""
Tests for resilient_runner.py checkpoint detection logic.

These test the locally-testable parts: partial JSON parsing, point counting,
and failure classification helpers. Cluster-dependent parts (SSH, rsync,
process management) are tested on the live cluster.

Run: cd ~/CHIME/exp && python3 test_checkpoint.py
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure we can import from the exp directory
sys.path.insert(0, str(Path(__file__).parent))

import resilient_runner as rr


class TestCountPartialPoints(unittest.TestCase):
    """Test checkpoint detection from _partial.json files."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.orig_results = rr.RESULTS_DIR
        rr.RESULTS_DIR = Path(self.tmpdir)

    def tearDown(self):
        rr.RESULTS_DIR = self.orig_results
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_partial(self, filename, data):
        path = Path(self.tmpdir) / filename
        with open(path, "w") as f:
            json.dump(data, f)

    def test_no_partials_returns_empty(self):
        result = rr.count_partial_points("fig_12")
        self.assertEqual(result, {})

    def test_single_workload_single_method(self):
        self._write_partial("fig_12_c_partial.json", {
            "methods": ["CHIME"],
            "X_data": {"CHIME": [1.5, 2.3, 3.1]},
            "Y_data": {"CHIME": [10, 20, 30]},
        })
        result = rr.count_partial_points("fig_12")
        self.assertEqual(result, {"c": {"CHIME": 3}})

    def test_multiple_methods(self):
        self._write_partial("fig_12_a_partial.json", {
            "methods": ["CHIME", "SMART", "Sherman"],
            "X_data": {"CHIME": [1, 2], "SMART": [3], "Sherman": [4, 5, 6]},
            "Y_data": {"CHIME": [10, 20], "SMART": [30], "Sherman": [40, 50, 60]},
        })
        result = rr.count_partial_points("fig_12")
        self.assertEqual(result, {"a": {"CHIME": 2, "SMART": 1, "Sherman": 3}})

    def test_multiple_workloads(self):
        self._write_partial("fig_12_c_partial.json", {
            "methods": ["CHIME"],
            "X_data": {"CHIME": [1, 2]},
            "Y_data": {"CHIME": [10, 20]},
        })
        self._write_partial("fig_12_la_partial.json", {
            "methods": ["CHIME", "SMART"],
            "X_data": {"CHIME": [3], "SMART": [4, 5]},
            "Y_data": {"CHIME": [30], "SMART": [40, 50]},
        })
        result = rr.count_partial_points("fig_12")
        self.assertIn("c", result)
        self.assertIn("la", result)
        self.assertEqual(result["c"]["CHIME"], 2)
        self.assertEqual(result["la"]["SMART"], 2)

    def test_empty_methods_returns_zero_counts(self):
        self._write_partial("fig_12_c_partial.json", {
            "methods": ["CHIME"],
            "X_data": {"CHIME": []},
            "Y_data": {"CHIME": []},
        })
        result = rr.count_partial_points("fig_12")
        self.assertEqual(result["c"]["CHIME"], 0)

    def test_malformed_json_skipped(self):
        path = Path(self.tmpdir) / "fig_12_c_partial.json"
        path.write_text("not valid json{{{")
        result = rr.count_partial_points("fig_12")
        self.assertEqual(result, {})

    def test_missing_x_data_key(self):
        self._write_partial("fig_12_c_partial.json", {
            "methods": ["CHIME"],
            "Y_data": {"CHIME": [10]},
        })
        result = rr.count_partial_points("fig_12")
        self.assertEqual(result["c"]["CHIME"], 0)

    def test_non_matching_experiment_ignored(self):
        """fig_15b partials should not appear when querying fig_12."""
        self._write_partial("fig_15b_a_partial.json", {
            "methods": ["CHIME"],
            "X_data": {"CHIME": [1, 2, 3]},
            "Y_data": {"CHIME": [10, 20, 30]},
        })
        result = rr.count_partial_points("fig_12")
        self.assertEqual(result, {})


class TestTotalCompletedPoints(unittest.TestCase):
    """Test total point counting across all partials."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.orig_results = rr.RESULTS_DIR
        rr.RESULTS_DIR = Path(self.tmpdir)

    def tearDown(self):
        rr.RESULTS_DIR = self.orig_results
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _write_partial(self, filename, data):
        path = Path(self.tmpdir) / filename
        with open(path, "w") as f:
            json.dump(data, f)

    def test_no_partials_returns_zero(self):
        self.assertEqual(rr.total_completed_points("fig_12"), 0)

    def test_sums_across_workloads_and_methods(self):
        self._write_partial("fig_12_c_partial.json", {
            "methods": ["CHIME", "SMART"],
            "X_data": {"CHIME": [1, 2], "SMART": [3]},
            "Y_data": {"CHIME": [10, 20], "SMART": [30]},
        })
        self._write_partial("fig_12_a_partial.json", {
            "methods": ["CHIME"],
            "X_data": {"CHIME": [4, 5, 6]},
            "Y_data": {"CHIME": [40, 50, 60]},
        })
        # 2 (CHIME/c) + 1 (SMART/c) + 3 (CHIME/a) = 6
        self.assertEqual(rr.total_completed_points("fig_12"), 6)


class TestGetHealthyNodes(unittest.TestCase):
    """Test reading healthy nodes from file."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.orig_healthy = rr.HEALTHY_FILE
        rr.HEALTHY_FILE = Path(self.tmpdir) / "healthy_nodes.txt"

    def tearDown(self):
        rr.HEALTHY_FILE = self.orig_healthy
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_missing_file_returns_empty(self):
        self.assertEqual(rr.get_healthy_nodes(), [])

    def test_reads_nodes_from_file(self):
        rr.HEALTHY_FILE.write_text("node-0.example.com\nnode-1.example.com\nnode-2.example.com\n")
        nodes = rr.get_healthy_nodes()
        self.assertEqual(len(nodes), 3)
        self.assertEqual(nodes[0], "node-0.example.com")

    def test_ignores_blank_lines(self):
        rr.HEALTHY_FILE.write_text("node-0.example.com\n\nnode-1.example.com\n\n")
        nodes = rr.get_healthy_nodes()
        self.assertEqual(len(nodes), 2)


class TestExperimentWatchdog(unittest.TestCase):
    """Test watchdog stall detection logic."""

    def test_stall_detected_after_threshold(self):
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None  # process still running
        mock_proc.kill = MagicMock()

        watchdog = rr.ExperimentWatchdog("fig_12", mock_proc)
        self.assertFalse(watchdog.detected_stall)

        # Simulate stalls
        watchdog.stall_count = rr.WATCHDOG_STALL_FACTOR
        self.assertTrue(watchdog.detected_stall)

    def test_no_systemic_failure_by_default(self):
        mock_proc = MagicMock()
        watchdog = rr.ExperimentWatchdog("fig_12", mock_proc)
        self.assertFalse(watchdog.detected_systemic_failure)

    def test_systemic_failure_when_node_set(self):
        mock_proc = MagicMock()
        watchdog = rr.ExperimentWatchdog("fig_12", mock_proc)
        watchdog.failed_node = "node-5.example.com"
        self.assertTrue(watchdog.detected_systemic_failure)


class TestGetHealthyCsv(unittest.TestCase):
    """Test CSV generation from healthy nodes."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.orig_healthy = rr.HEALTHY_FILE
        rr.HEALTHY_FILE = Path(self.tmpdir) / "healthy_nodes.txt"

    def tearDown(self):
        rr.HEALTHY_FILE = self.orig_healthy
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_empty_file_returns_empty_string(self):
        self.assertEqual(rr.get_healthy_csv(), "")

    def test_returns_comma_separated(self):
        rr.HEALTHY_FILE.write_text("node-0\nnode-1\nnode-2\n")
        self.assertEqual(rr.get_healthy_csv(), "node-0,node-1,node-2")


class TestCleanupCluster(unittest.TestCase):
    """Test cluster cleanup with mocked subprocess."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.orig_healthy = rr.HEALTHY_FILE
        rr.HEALTHY_FILE = Path(self.tmpdir) / "healthy_nodes.txt"

    def tearDown(self):
        rr.HEALTHY_FILE = self.orig_healthy
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    @patch("resilient_runner.subprocess.run")
    def test_cleanup_calls_run_on_nodes(self, mock_run):
        rr.HEALTHY_FILE.write_text("node-0\nnode-1\n")
        rr.cleanup_cluster()
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        self.assertIn("killall", args[-1])

    def test_cleanup_no_nodes_does_not_crash(self):
        # No healthy_nodes.txt exists
        rr.cleanup_cluster()  # should not raise


class TestRsyncResults(unittest.TestCase):
    """Test rsync backup with mocked subprocess."""

    @patch("resilient_runner.subprocess.run")
    def test_rsync_called_when_target_set(self, mock_run):
        orig = rr.RSYNC_TARGET
        rr.RSYNC_TARGET = "user@laptop:~/results/"
        try:
            rr.rsync_results()
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            self.assertEqual(args[0], "rsync")
        finally:
            rr.RSYNC_TARGET = orig

    @patch("resilient_runner.subprocess.run")
    def test_rsync_not_called_when_no_target(self, mock_run):
        orig = rr.RSYNC_TARGET
        rr.RSYNC_TARGET = ""
        try:
            rr.rsync_results()
            mock_run.assert_not_called()
        finally:
            rr.RSYNC_TARGET = orig

    @patch("resilient_runner.subprocess.run", side_effect=subprocess.TimeoutExpired("rsync", 60))
    def test_rsync_timeout_does_not_crash(self, mock_run):
        orig = rr.RSYNC_TARGET
        rr.RSYNC_TARGET = "user@laptop:~/results/"
        try:
            rr.rsync_results()  # should not raise
        finally:
            rr.RSYNC_TARGET = orig


class TestCheckNodeHealth(unittest.TestCase):
    """Test node health check with mocked SSH."""

    @patch("resilient_runner.subprocess.run")
    def test_healthy_node(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="ok\n")
        self.assertTrue(rr.check_node_health("node-0"))

    @patch("resilient_runner.subprocess.run")
    def test_unhealthy_node_nonzero_rc(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        self.assertFalse(rr.check_node_health("node-0"))

    @patch("resilient_runner.subprocess.run", side_effect=subprocess.TimeoutExpired("ssh", 10))
    def test_timeout_returns_false(self, mock_run):
        self.assertFalse(rr.check_node_health("node-0"))


class TestReconfigureCluster(unittest.TestCase):
    """Test cluster reconfiguration with mocked subprocess."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.orig_healthy = rr.HEALTHY_FILE
        rr.HEALTHY_FILE = Path(self.tmpdir) / "healthy_nodes.txt"
        # 8 nodes: 1 master + 7 CN
        rr.HEALTHY_FILE.write_text(
            "node-0\nnode-1\nnode-2\nnode-3\nnode-4\nnode-5\nnode-6\nnode-7\n"
        )

    def tearDown(self):
        rr.HEALTHY_FILE = self.orig_healthy
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    @patch("resilient_runner.subprocess.run")
    def test_excludes_failed_node(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        result = rr.reconfigure_cluster("node-3")
        self.assertTrue(result)
        # Verify node-3 is removed from file
        remaining = rr.get_healthy_nodes()
        self.assertNotIn("node-3", remaining)
        self.assertEqual(len(remaining), 7)

    @patch("resilient_runner.subprocess.run")
    def test_fails_when_too_few_nodes(self, mock_run):
        # Only 6 nodes: removing one leaves 5 total = 4 CN, below threshold
        rr.HEALTHY_FILE.write_text("node-0\nnode-1\nnode-2\nnode-3\nnode-4\nnode-5\n")
        result = rr.reconfigure_cluster("node-5")
        # 5 remaining, 4 CN — below minimum of 5
        self.assertFalse(result)

    @patch("resilient_runner.subprocess.run")
    def test_excludes_unknown_node_gracefully(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0)
        # Node not in list — should still succeed (no-op exclusion)
        result = rr.reconfigure_cluster("node-99")
        self.assertTrue(result)
        remaining = rr.get_healthy_nodes()
        self.assertEqual(len(remaining), 8)  # unchanged


class TestLogFunction(unittest.TestCase):
    """Test the log utility."""

    @patch("builtins.print")
    def test_log_outputs_timestamped_message(self, mock_print):
        rr.log("test message")
        mock_print.assert_called_once()
        output = mock_print.call_args[0][0]
        self.assertIn("test message", output)
        self.assertRegex(output, r"\[\d{2}:\d{2}:\d{2}\]")


if __name__ == "__main__":
    unittest.main(verbosity=2)

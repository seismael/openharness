#!/usr/bin/env python3
"""Regression tests for failure classification (RFC-0014)."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "openharness_failures.py"


def entry(iteration, failure=None, **overrides):
    base = {
        "ts": "2026-10-24T00:00:00Z",
        "iteration": iteration,
        "front": "debug",
        "hypothesis": "The cache invalidates on write",
        "decision": "rejected",
    }
    if failure is not None:
        base["failure"] = failure
    base.update(overrides)
    return base


class FailureTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="ohp_failures_"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def journal(self, *entries):
        path = self.root / "journal.jsonl"
        path.write_text(
            "\n".join(json.dumps(item) for item in entries) + "\n", encoding="utf-8"
        )
        return path

    def run_failures(self, path, *extra):
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "--journal", str(path), *extra],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_counts_and_rate(self):
        path = self.journal(
            entry(1, {"class": "tool-misuse", "detail": "wrong flag"}),
            entry(2, {"class": "context-loss", "detail": "dropped file"}),
            entry(3),
        )
        result = self.run_failures(path)
        self.assertEqual(result.returncode, 0, result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["failures"], 2)
        self.assertEqual(payload["iterations"], 3)
        self.assertAlmostEqual(payload["rate"], 0.6667)
        self.assertEqual(payload["classes"]["tool-misuse"], 1)

    def test_unknown_class_is_an_error_but_counted(self):
        path = self.journal(entry(1, {"class": "cosmic-rays"}))
        result = self.run_failures(path)
        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["classes"]["unclassified"], 1)
        self.assertIn("failure.unclassified", [f["code"] for f in payload["findings"]])

    def test_recurrence_is_a_harness_gap(self):
        path = self.journal(
            entry(1, {"class": "wrong-premise", "detail": "stale assumption"}),
            entry(2, {"class": "wrong-premise", "detail": "stale assumption again"}),
        )
        payload = json.loads(self.run_failures(path).stdout)
        self.assertEqual(payload["repeated"], [{"class": "wrong-premise", "count": 2}])
        self.assertIn("failure.recurring", [f["code"] for f in payload["findings"]])

    def test_recurrence_threshold_is_configurable(self):
        path = self.journal(
            entry(1, {"class": "dead-end"}),
            entry(2, {"class": "dead-end"}),
        )
        payload = json.loads(self.run_failures(path, "--recurrence", "3").stdout)
        self.assertEqual(payload["repeated"], [])

    def test_recurrence_below_two_is_refused(self):
        result = self.run_failures(self.journal(entry(1)), "--recurrence", "1")
        self.assertEqual(result.returncode, 2)

    def test_undiagnosed_unclassified_warns(self):
        path = self.journal(entry(1, {"class": "unclassified"}))
        result = self.run_failures(path)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn(
            "failure.undiagnosed",
            [f["code"] for f in json.loads(result.stdout)["findings"]],
        )

    def test_non_object_failure_is_an_error(self):
        path = self.journal(entry(1, "tool-misuse"))
        result = self.run_failures(path)
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "failure.invalid",
            [f["code"] for f in json.loads(result.stdout)["findings"]],
        )

    def test_unclassified_is_never_reported_as_recurring(self):
        path = self.journal(
            entry(1, {"class": "unclassified"}),
            entry(2, {"class": "unclassified"}),
        )
        self.assertEqual(json.loads(self.run_failures(path).stdout)["repeated"], [])

    def test_unreadable_journal_exits_two(self):
        result = self.run_failures(self.root / "missing.jsonl")
        self.assertEqual(result.returncode, 2)

    def test_output_is_bounded_and_deterministic(self):
        path = self.journal(
            *[
                entry(index, {"class": "tool-misuse", "detail": "detail " * 20})
                for index in range(1, 200)
            ]
        )
        first = self.run_failures(path)
        second = self.run_failures(path)
        self.assertEqual(first.returncode, 0, first.stdout)
        self.assertLessEqual(len(first.stdout.encode("utf-8")), 2500)
        self.assertEqual(first.stdout, second.stdout)


if __name__ == "__main__":
    unittest.main()

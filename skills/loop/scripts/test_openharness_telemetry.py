#!/usr/bin/env python3
"""Regression tests for journal telemetry (RFC-0011)."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "openharness_telemetry.py"


def entry(**overrides):
    base = {
        "ts": "2026-10-24T00:00:00Z",
        "iteration": 1,
        "front": "improve",
        "hypothesis": "Trim duplicated always-on instructions",
        "decision": "adopted",
        "scope": "invariant",
        "deficiency": "context-management",
        "cases": ["one", "two"],
        "metric_before": 10.0,
        "metric_after": 12.0,
        "contrast": "mitigated",
        "evidence_ref": "receipts/it-1.json",
    }
    base.update(overrides)
    return base


class TelemetryTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="ohp_telemetry_"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def journal(self, *entries):
        path = self.root / "journal.jsonl"
        path.write_text(
            "\n".join(json.dumps(item) for item in entries) + "\n", encoding="utf-8"
        )
        return path

    def run_telemetry(self, path, *extra):
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "--journal", str(path), *extra],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_counts_and_decision_mix(self):
        path = self.journal(
            entry(iteration=1),
            entry(iteration=2, decision="rejected", contrast="unchanged"),
            entry(
                iteration=3, decision="preserved", cases=["one"], contrast="unproven"
            ),
        )
        result = self.run_telemetry(path)
        self.assertEqual(result.returncode, 0, result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["iterations"], 3)
        self.assertEqual(payload["decisions"]["adopted"], 1)
        self.assertEqual(payload["decisions"]["preserved"], 1)
        self.assertEqual(payload["contrasts"]["mitigated"], 1)

    def test_cost_sums_only_recorded_fields(self):
        path = self.journal(
            entry(iteration=1, cost={"tokens_in": 100, "tokens_out": 20, "usd": 0.5}),
            entry(iteration=2, cost={"usd": 0.25, "tool_calls": 4}),
        )
        result = self.run_telemetry(path)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["tokens_total"], 120)
        self.assertEqual(payload["cost"]["usd"], 0.75)
        self.assertEqual(payload["cost"]["tool_calls"], 4)
        self.assertEqual(payload["costed_iterations"], 2)

    def test_cost_per_gain_uses_measured_gain(self):
        path = self.journal(
            entry(iteration=1, cost={"tokens_in": 200, "usd": 1.0}),
        )
        payload = json.loads(self.run_telemetry(path).stdout)
        self.assertEqual(payload["gain_total"], 2.0)
        self.assertEqual(payload["cost_per_gain"]["usd"], 0.5)
        self.assertEqual(payload["cost_per_gain"]["tokens"], 100.0)

    def test_no_gain_means_no_cost_per_gain(self):
        path = self.journal(entry(iteration=1, metric_before=5.0, metric_after=5.0))
        payload = json.loads(self.run_telemetry(path).stdout)
        self.assertEqual(payload["gain_total"], 0.0)
        self.assertIsNone(payload["cost_per_gain"])

    def test_minimize_direction_flips_gain_sign(self):
        path = self.journal(entry(iteration=1, metric_before=10.0, metric_after=8.0))
        payload = json.loads(self.run_telemetry(path, "--direction", "minimize").stdout)
        self.assertEqual(payload["gain_total"], 2.0)
        self.assertEqual(payload["regression_total"], 0.0)

    def test_regressions_are_kept_separate(self):
        path = self.journal(
            entry(iteration=1, metric_before=10.0, metric_after=12.0),
            entry(iteration=2, metric_before=10.0, metric_after=9.0),
        )
        payload = json.loads(self.run_telemetry(path).stdout)
        self.assertEqual(payload["gain_total"], 2.0)
        self.assertEqual(payload["regression_total"], -1.0)

    def test_deficiency_breakdown(self):
        path = self.journal(
            entry(iteration=1, deficiency="context-management"),
            entry(
                iteration=2,
                deficiency="tool-use",
                decision="rejected",
                contrast="regressed",
            ),
        )
        payload = json.loads(self.run_telemetry(path).stdout)
        self.assertEqual(payload["deficiencies"]["context-management"]["mitigated"], 1)
        self.assertEqual(payload["deficiencies"]["tool-use"]["adopted"], 0)

    def test_evidence_coverage(self):
        path = self.journal(
            entry(iteration=1),
            entry(
                iteration=2, evidence_ref="", decision="preserved", contrast="unproven"
            ),
        )
        payload = json.loads(self.run_telemetry(path).stdout)
        self.assertEqual(payload["evidence_coverage"], 0.5)

    def test_invalid_entries_are_counted_not_crashing(self):
        path = self.journal({"decision": "adopted"}, entry(iteration=2))
        payload = json.loads(self.run_telemetry(path).stdout)
        self.assertEqual(payload["invalid"], 1)
        self.assertEqual(payload["iterations"], 1)

    def test_unknown_decision_is_unclassified(self):
        path = self.journal(entry(iteration=1, decision="maybe"))
        payload = json.loads(self.run_telemetry(path).stdout)
        self.assertEqual(payload["decisions"]["unclassified"], 1)

    def test_unreadable_journal_exits_two(self):
        result = self.run_telemetry(self.root / "missing.jsonl")
        self.assertEqual(result.returncode, 2)
        self.assertIn("error", json.loads(result.stdout))

    def test_output_is_bounded_and_deterministic(self):
        path = self.journal(
            *[
                entry(
                    iteration=index,
                    deficiency=f"class-{index % 9}",
                    cost={"tokens_in": index, "usd": 0.01},
                )
                for index in range(1, 200)
            ]
        )
        first = self.run_telemetry(path)
        second = self.run_telemetry(path)
        self.assertEqual(first.returncode, 0, first.stdout)
        self.assertLessEqual(len(first.stdout.encode("utf-8")), 2500)
        self.assertEqual(first.stdout, second.stdout)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Regression tests for the iteration-contract validator (RFC-0010)."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "openharness_verify.py"
FP = "a" * 64


def entry(**overrides):
    base = {
        "ts": "2026-10-24T00:00:00Z",
        "iteration": 1,
        "front": "improve",
        "hypothesis": "Trim always-on duplication to free output budget",
        "decision": "adopted",
        "scope": "invariant",
        "deficiency": "context-management",
        "cases": ["unit", "integration"],
        "metric_before": 0.5,
        "metric_after": 0.7,
        "contrast": "mitigated",
        "harness_fingerprint": FP,
        "evidence_ref": "receipts/it-1.json",
        "rationale": "both cases improved with invariants clean",
    }
    base.update(overrides)
    return base


class IterationContractTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="ohp_verify_"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def journal(self, *entries):
        path = self.root / "journal.jsonl"
        path.write_text(
            "\n".join(json.dumps(item) for item in entries) + "\n", encoding="utf-8"
        )
        return path

    def run_verify(self, path, *extra):
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "--journal", str(path), *extra],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_clean_iteration_passes(self):
        result = self.run_verify(self.journal(entry()), "--fingerprint", FP)
        self.assertEqual(result.returncode, 0, result.stdout)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["counts"]["error"], 0)

    def test_adoption_without_scope_is_error(self):
        result = self.run_verify(self.journal(entry(scope=None)))
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "scope.missing", [f["code"] for f in json.loads(result.stdout)["findings"]]
        )

    def test_invariant_needs_two_cases(self):
        result = self.run_verify(self.journal(entry(cases=["unit"])))
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "invariant.single_case",
            [f["code"] for f in json.loads(result.stdout)["findings"]],
        )

    def test_local_evidence_cannot_be_global(self):
        result = self.run_verify(
            self.journal(entry(scope="local", promote_global=True))
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "scope.promotion",
            [f["code"] for f in json.loads(result.stdout)["findings"]],
        )

    def test_duplicate_iteration_is_error(self):
        result = self.run_verify(self.journal(entry(), entry()))
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "iteration.duplicate",
            [f["code"] for f in json.loads(result.stdout)["findings"]],
        )

    def test_contrast_mismatch_is_warning(self):
        result = self.run_verify(
            self.journal(
                entry(metric_before=0.7, metric_after=0.5, contrast="mitigated")
            )
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        payload = json.loads(result.stdout)
        self.assertIn("contrast.inconsistent", [f["code"] for f in payload["findings"]])
        self.assertEqual(payload["counts"]["error"], 0)

    def test_minimize_direction_flips_the_verdict(self):
        result = self.run_verify(
            self.journal(
                entry(metric_before=0.5, metric_after=0.3, contrast="mitigated")
            ),
            "--direction",
            "minimize",
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(json.loads(result.stdout)["counts"]["warn"], 0)

    def test_stale_fingerprint_is_error(self):
        result = self.run_verify(self.journal(entry()), "--fingerprint", "b" * 64)
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "fingerprint.stale",
            [f["code"] for f in json.loads(result.stdout)["findings"]],
        )

    def test_preserved_requires_observation(self):
        result = self.run_verify(
            self.journal(entry(decision="preserved", rationale=""))
        )
        self.assertEqual(result.returncode, 1)
        codes = [f["code"] for f in json.loads(result.stdout)["findings"]]
        self.assertIn("preserve.justification", codes)

    def test_unreadable_journal_exits_two(self):
        result = self.run_verify(self.root / "missing.jsonl")
        self.assertEqual(result.returncode, 2)
        self.assertIn("error", json.loads(result.stdout))

    def test_output_is_bounded_and_deterministic(self):
        path = self.journal(
            *[
                entry(iteration=i, scope="invariant", cases=["one"])
                for i in range(1, 60)
            ]
        )
        first = self.run_verify(path)
        second = self.run_verify(path)
        self.assertEqual(first.returncode, 1)
        self.assertLessEqual(len(first.stdout.encode("utf-8")), 2500)
        self.assertEqual(first.stdout, second.stdout)


if __name__ == "__main__":
    unittest.main()

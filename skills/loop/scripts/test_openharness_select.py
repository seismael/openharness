#!/usr/bin/env python3
"""Regression tests for anonymized candidate selection (RFC-0010)."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "openharness_select.py"


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="ohp_select_"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.candidates = self.root / "candidates"
        self.candidates.mkdir()
        (self.candidates / "alpha.md").write_text("alpha deliverable\n", encoding="utf-8")
        (self.candidates / "beta.md").write_text("beta deliverable\n", encoding="utf-8")

    def run_select(self, *extra):
        return subprocess.run(
            [
                sys.executable,
                "-B",
                str(SCRIPT),
                "--candidates",
                str(self.candidates),
                *extra,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def add_receipts(self):
        for name in ("alpha.md", "beta.md"):
            (self.candidates / f"{name}.receipt.json").write_text(
                json.dumps({"metric": 1, "fingerprint": "a" * 64}), encoding="utf-8"
            )

    def test_init_creates_separate_seal(self):
        result = self.run_select()
        self.assertEqual(result.returncode, 0, result.stdout)
        selection = (self.candidates / "selection.json").read_text(encoding="utf-8")
        self.assertTrue((self.candidates / "mapping.json").is_file())
        self.assertNotIn("alpha.md", selection)
        self.assertNotIn("beta.md", selection)
        self.assertEqual(json.loads(selection)["count"], 2)

    def test_anonymization_is_deterministic(self):
        self.run_select()
        first = (self.candidates / "mapping.json").read_text(encoding="utf-8")
        (self.candidates / "selection.json").unlink()
        self.run_select()
        self.assertEqual(first, (self.candidates / "mapping.json").read_text(encoding="utf-8"))

    def test_choice_requires_reason(self):
        self.run_select()
        label = json.loads((self.candidates / "selection.json").read_text(encoding="utf-8"))[
            "candidates"
        ][0]["id"]
        self.add_receipts()
        result = self.run_select("--choose", label)
        self.assertEqual(result.returncode, 2)

    def test_choice_requires_probe_receipt(self):
        self.run_select()
        label = json.loads((self.candidates / "selection.json").read_text(encoding="utf-8"))[
            "candidates"
        ][0]["id"]
        result = self.run_select("--choose", label, "--reason", "clearer deliverable")
        self.assertEqual(result.returncode, 1)
        self.assertIn("probe receipt", json.loads(result.stdout)["error"])

    def test_unprobed_choice_is_recorded_as_unproven(self):
        self.run_select()
        label = json.loads((self.candidates / "selection.json").read_text(encoding="utf-8"))[
            "candidates"
        ][0]["id"]
        result = self.run_select(
            "--choose", label, "--reason", "clearer deliverable", "--allow-unprobed"
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["unproven"])
        self.assertEqual(payload["chosen"], label)

    def test_choice_with_receipts_is_clean(self):
        self.run_select()
        label = json.loads((self.candidates / "selection.json").read_text(encoding="utf-8"))[
            "candidates"
        ][0]["id"]
        self.add_receipts()
        result = self.run_select("--choose", label, "--reason", "clearer deliverable")
        self.assertEqual(result.returncode, 0, result.stdout)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["unproven"])
        self.assertEqual(payload["mode"], "existing-output")

    def test_unknown_choice_is_refused(self):
        self.run_select()
        self.add_receipts()
        result = self.run_select("--choose", "cand-zz", "--reason", "nope")
        self.assertEqual(result.returncode, 2)

    def test_unseal_prints_mapping(self):
        self.run_select()
        result = self.run_select("--unseal")
        self.assertEqual(result.returncode, 0)
        self.assertIn("alpha.md", result.stdout)


if __name__ == "__main__":
    unittest.main()

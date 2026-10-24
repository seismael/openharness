#!/usr/bin/env python3
"""Regression tests for the deterministic harness audit (OHP RFC-0009)."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "openharness_audit.py"
LONG_LINE = (
    "Always re-run the declared pipeline before claiming that a metric has improved."
)


class HarnessAuditTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="ohp_harness_"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def manifest(self, components, budget=None, schema="harness.manifest.v1"):
        data = {
            "schema": schema,
            "name": "fixture",
            "root": ".",
            "components": components,
        }
        if budget is not None:
            data["budget"] = budget
        return self.write("harness.json", json.dumps(data))

    def run_audit(self, path):
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "--manifest", str(path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def surface(self, instruction="When building, load the `build` skill.\n"):
        self.write("AGENTS.md", instruction)
        self.write(
            "skills/build/SKILL.md",
            "---\nname: build\ndescription: Build things\n---\nBody\n",
        )
        components = [
            {
                "id": "prompt",
                "kind": "system_prompt",
                "paths": ["AGENTS.md"],
                "always_on": True,
            },
            {"id": "build", "kind": "skills", "paths": ["skills/*/SKILL.md"]},
        ]
        return components

    def test_clean_surface_passes(self):
        result = self.run_audit(
            self.manifest(self.surface(), {"always_on_tokens": 1000})
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt["schema"], "openharness.receipt.v1")
        self.assertTrue(receipt["ok"])
        self.assertEqual(receipt["counts"]["error"], 0)
        self.assertLessEqual(len(result.stdout.encode("utf-8")), 2500)

    def test_always_on_budget_violation_is_error(self):
        result = self.run_audit(self.manifest(self.surface(), {"always_on_tokens": 1}))
        self.assertEqual(result.returncode, 1)
        codes = [item["code"] for item in json.loads(result.stdout)["findings"]]
        self.assertIn("budget.always_on_exceeded", codes)

    def test_orphan_component_is_error(self):
        result = self.run_audit(
            self.manifest(
                self.surface(instruction="When deploying, read the runbook.\n")
            )
        )
        self.assertEqual(result.returncode, 1)
        codes = [item["code"] for item in json.loads(result.stdout)["findings"]]
        self.assertIn("reachability.orphan", codes)

    def test_mentioned_component_is_reachable(self):
        result = self.run_audit(self.manifest(self.surface()))
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_duplicate_instruction_is_warned(self):
        self.write(
            "AGENTS.md", LONG_LINE + "\nWhen building, load the `build` skill.\n"
        )
        self.write("guardrails.md", LONG_LINE + "\n")
        self.write(
            "skills/build/SKILL.md",
            "---\nname: build\ndescription: Build things\n---\nBody\n",
        )
        components = [
            {
                "id": "prompt",
                "kind": "system_prompt",
                "paths": ["AGENTS.md"],
                "always_on": True,
            },
            {
                "id": "guards",
                "kind": "guardrails",
                "paths": ["guardrails.md"],
                "always_on": True,
            },
            {"id": "build", "kind": "skills", "paths": ["skills/*/SKILL.md"]},
        ]
        result = self.run_audit(self.manifest(components))
        receipt = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertIn(
            "duplication.line", [item["code"] for item in receipt["findings"]]
        )
        self.assertEqual(receipt["counts"]["warn"], 1)

    def test_missing_markdown_link_is_warned(self):
        self.write("AGENTS.md", "See [the guide](references/missing.md).\n")
        components = [
            {
                "id": "prompt",
                "kind": "system_prompt",
                "paths": ["AGENTS.md"],
                "always_on": True,
            }
        ]
        result = self.run_audit(self.manifest(components))
        receipt = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertIn("link.missing", [item["code"] for item in receipt["findings"]])

    def test_missing_component_is_error(self):
        components = [
            {
                "id": "ghost",
                "kind": "memory",
                "paths": ["absent/*.md"],
                "always_on": True,
            }
        ]
        result = self.run_audit(self.manifest(components))
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "component.missing",
            [item["code"] for item in json.loads(result.stdout)["findings"]],
        )

    def test_disabled_component_is_skipped(self):
        components = [
            {
                "id": "ghost",
                "kind": "memory",
                "paths": ["absent/*.md"],
                "enabled": False,
            }
        ]
        result = self.run_audit(self.manifest(components))
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_manifest_with_bom_is_accepted(self):
        """Windows shells write UTF-8 BOM by default; that must not read as a broken manifest."""
        payload = {
            "schema": "harness.manifest.v1",
            "name": "bom",
            "components": self.surface(),
        }
        path = self.root / "bom.json"
        path.write_text(json.dumps(payload), encoding="utf-8-sig")
        result = self.run_audit(path)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_invalid_manifest_exits_two(self):
        path = self.manifest(self.surface(), schema="wrong.v0")
        result = self.run_audit(path)
        self.assertEqual(result.returncode, 2)
        self.assertIn("error", json.loads(result.stdout))

    def test_receipt_is_deterministic(self):
        path = self.manifest(
            self.surface(instruction="When deploying, read the runbook.\n")
        )
        first = self.run_audit(path).stdout
        second = self.run_audit(path).stdout
        self.assertEqual(first, second)

    def test_receipt_stays_bounded_under_many_findings(self):
        components = [
            {"id": f"ghost{i}", "kind": "memory", "paths": [f"absent{i}/*.md"]}
            for i in range(120)
        ]
        result = self.run_audit(self.manifest(components))
        self.assertEqual(result.returncode, 1)
        self.assertLessEqual(len(result.stdout.encode("utf-8")), 2500)
        receipt = json.loads(result.stdout)
        self.assertTrue(receipt["truncated"])
        self.assertGreater(receipt["dropped_findings"], 0)

    def test_receipt_carries_state_fingerprint(self):
        receipt = json.loads(self.run_audit(self.manifest(self.surface())).stdout)
        self.assertRegex(receipt["fingerprint"], r"^[a-f0-9]{64}$")

    def test_fingerprint_only_prints_identity(self):
        path = self.manifest(self.surface())
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                str(SCRIPT),
                "--manifest",
                str(path),
                "--fingerprint-only",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(set(payload), {"fingerprint"})
        self.assertEqual(len(payload["fingerprint"]), 64)

    def test_fingerprint_tracks_content_not_component_layout(self):
        path = self.manifest(self.surface())
        original = json.loads(self.run_audit(path).stdout)["fingerprint"]
        relabeled = self.surface()
        relabeled[0]["id"] = "prompt-renamed"
        relabeled.insert(
            0, {"id": "overlap", "kind": "system_prompt", "paths": ["AGENTS.md"]}
        )
        self.assertEqual(
            original,
            json.loads(self.run_audit(self.manifest(relabeled)).stdout)["fingerprint"],
        )
        self.write("AGENTS.md", "When building, load the `build` skill twice.\n")
        self.assertNotEqual(
            original,
            json.loads(self.run_audit(self.manifest(relabeled)).stdout)["fingerprint"],
        )


if __name__ == "__main__":
    unittest.main()

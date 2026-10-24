#!/usr/bin/env python3
"""Regression tests for capability inventory and gap analysis (RFC-0013)."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "openharness_inventory.py"


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="ohp_inventory_"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        (self.root / "AGENTS.md").write_text("instructions\n", encoding="utf-8")
        (self.root / "skills").mkdir()
        (self.root / "skills" / "a.md").write_text("skill\n", encoding="utf-8")
        self.manifest = self.write_manifest(
            [
                {
                    "id": "prompt",
                    "kind": "system_prompt",
                    "paths": ["AGENTS.md"],
                    "always_on": True,
                },
                {"id": "skill", "kind": "skills", "paths": ["skills/*.md"]},
                {
                    "id": "off",
                    "kind": "plugins",
                    "paths": ["plugins/*.ts"],
                    "enabled": False,
                },
            ]
        )

    def write_manifest(self, components):
        path = self.root / "harness.json"
        path.write_text(
            json.dumps(
                {"schema": "harness.manifest.v1", "name": "t", "components": components}
            ),
            encoding="utf-8",
        )
        return path

    def write_requirements(self, requirements):
        path = self.root / "requirements.json"
        path.write_text(
            json.dumps(
                {"schema": "openharness.requirements.v1", "requirements": requirements}
            ),
            encoding="utf-8",
        )
        return path

    def run_inventory(self, *extra):
        return subprocess.run(
            [
                sys.executable,
                "-B",
                str(SCRIPT),
                "--manifest",
                str(self.manifest),
                *extra,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_inventory_without_requirements_is_clean(self):
        result = self.run_inventory()
        self.assertEqual(result.returncode, 0, result.stdout)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["coverage"], 1.0)
        self.assertEqual(payload["components"]["skills"]["enabled"], 1)
        self.assertEqual(payload["components"]["plugins"]["enabled"], 0)
        self.assertIn("plugins", payload["kinds_missing"])
        self.assertEqual(len(payload["fingerprint"]), 64)

    def test_met_requirement_passes(self):
        path = self.write_requirements([{"id": "prompting", "kind": "system_prompt"}])
        result = self.run_inventory("--requirements", str(path))
        self.assertEqual(result.returncode, 0, result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["requirements"], {"total": 1, "met": 1})
        self.assertEqual(payload["gaps"], [])

    def test_unmet_required_gap_blocks(self):
        path = self.write_requirements([{"id": "extensions", "kind": "plugins"}])
        result = self.run_inventory("--requirements", str(path))
        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["ok"])
        self.assertEqual(
            payload["gaps"][0]["reason"], "no enabled component of kind plugins"
        )

    def test_optional_gap_does_not_block(self):
        path = self.write_requirements(
            [{"id": "extensions", "kind": "plugins", "required": False}]
        )
        result = self.run_inventory("--requirements", str(path))
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertFalse(json.loads(result.stdout)["gaps"][0]["required"])

    def test_disabled_named_component_is_a_gap(self):
        path = self.write_requirements(
            [{"id": "plugins-on", "kind": "plugins", "component": "off"}]
        )
        result = self.run_inventory("--requirements", str(path))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(
            json.loads(result.stdout)["gaps"][0]["reason"], "component off is disabled"
        )

    def test_wrong_kind_for_named_component_is_a_gap(self):
        path = self.write_requirements(
            [{"id": "x", "kind": "memory", "component": "prompt"}]
        )
        result = self.run_inventory("--requirements", str(path))
        self.assertEqual(result.returncode, 1)
        self.assertIn("not memory", json.loads(result.stdout)["gaps"][0]["reason"])

    def test_unknown_component_is_a_gap(self):
        path = self.write_requirements(
            [{"id": "x", "kind": "memory", "component": "ghost"}]
        )
        result = self.run_inventory("--requirements", str(path))
        self.assertEqual(result.returncode, 1)
        self.assertIn("not declared", json.loads(result.stdout)["gaps"][0]["reason"])

    def test_unknown_kind_is_a_declaration_error(self):
        path = self.write_requirements([{"id": "x", "kind": "wizardry"}])
        result = self.run_inventory("--requirements", str(path))
        self.assertEqual(result.returncode, 2)
        self.assertIn("kind must be one of", json.loads(result.stdout)["error"])

    def test_duplicate_requirement_id_is_a_declaration_error(self):
        path = self.write_requirements(
            [{"id": "same", "kind": "skills"}, {"id": "same", "kind": "skills"}]
        )
        result = self.run_inventory("--requirements", str(path))
        self.assertEqual(result.returncode, 2)
        self.assertIn("duplicate requirement id", json.loads(result.stdout)["error"])

    def test_unknown_requirement_field_is_refused(self):
        path = self.write_requirements([{"id": "x", "kind": "skills", "priority": 1}])
        result = self.run_inventory("--requirements", str(path))
        self.assertEqual(result.returncode, 2)
        self.assertIn("unknown fields", json.loads(result.stdout)["error"])

    def test_missing_manifest_exits_two(self):
        self.manifest = self.root / "missing.json"
        result = self.run_inventory()
        self.assertEqual(result.returncode, 2)
        self.assertIn("error", json.loads(result.stdout))

    def test_output_is_bounded_and_deterministic(self):
        path = self.write_requirements(
            [{"id": f"gap-{index}", "kind": "plugins"} for index in range(40)]
        )
        first = self.run_inventory("--requirements", str(path))
        second = self.run_inventory("--requirements", str(path))
        self.assertEqual(first.returncode, 1)
        self.assertLessEqual(len(first.stdout.encode("utf-8")), 2500)
        self.assertEqual(first.stdout, second.stdout)


if __name__ == "__main__":
    unittest.main()

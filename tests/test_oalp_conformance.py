#!/usr/bin/env python3
"""Comprehensive conformance test suite for OpenAgent Loop Protocol (OALP).

Verifies schema contracts, internal skill initialization tools, multi-language
starter templates, and schema validator policies under complete isolation.
"""

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from skills.loop.scripts.init_loop import init_project
from skills.loop.scripts.validate_loop import validate_loop, _load_yaml

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = ROOT / "docs" / "standards" / "schemas"
TEMPLATES_DIR = ROOT / "skills" / "loop" / "assets" / "templates"


class OALPConformanceTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="oalp_test_"))

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_json_schemas_validity(self):
        """Verify all normative JSON schemas are valid and parseable."""
        schemas = ["profile.schema.json", "loop.schema.json", "journal.schema.json", "coverage.schema.json"]
        for s_name in schemas:
            schema_file = SCHEMAS_DIR / s_name
            self.assertTrue(schema_file.is_file(), f"Missing schema: {s_name}")
            data = json.loads(schema_file.read_text(encoding="utf-8"))
            self.assertIn("$schema", data)
            self.assertIn("type", data)
            self.assertEqual(data["type"], "object")

    def test_starter_templates_conformance(self):
        """Verify that Python, Rust, Go, and Node starter templates contain all required profile fields."""
        templates = ["profile.python.yaml", "profile.rust.yaml", "profile.go.yaml", "profile.node.yaml"]
        required_fields = ["schema", "project", "target", "metric", "paths", "boundaries", "pipeline", "gates", "completion"]
        for t_name in templates:
            t_file = TEMPLATES_DIR / t_name
            self.assertTrue(t_file.is_file(), f"Missing template: {t_name}")
            content = t_file.read_text(encoding="utf-8")
            data = _load_yaml(content)
            for req in required_fields:
                self.assertIn(req, data, f"Template {t_name} missing required field '{req}'")
            self.assertEqual(data["schema"], "loop.profile.v1")

    def test_init_project_and_validate_all_templates(self):
        """Verify init_project scaffolds compliant repositories for all supported language templates."""
        for tmpl in ["python", "rust", "go", "node"]:
            proj_dir = self.temp_dir / f"proj_{tmpl}"
            proj_dir.mkdir(parents=True)

            rc = init_project(proj_dir, target=f"Optimize {tmpl} service", template=tmpl)
            self.assertEqual(rc, 0)

            # Validate directory structure
            loop_dir = proj_dir / ".agents" / "loop"
            self.assertTrue(loop_dir.is_dir())
            self.assertTrue((loop_dir / "knowledge" / "profile.yaml").is_file())
            self.assertTrue((loop_dir / "knowledge" / "invariants.md").is_file())
            self.assertTrue((loop_dir / "loop.json").is_file())
            self.assertTrue((loop_dir / "coverage.json").is_file())
            self.assertTrue((loop_dir / "plans" / "next_moves.json").is_file())

            # Validate using internal validator
            errors = validate_loop(proj_dir)
            self.assertEqual(errors, [], f"Template {tmpl} produced validation errors: {errors}")

    def test_validate_detects_missing_seam(self):
        """Verify validate_loop reports an error when profile.yaml is missing."""
        loop_dir = self.temp_dir / ".agents" / "loop"
        loop_dir.mkdir(parents=True)
        (loop_dir / "loop.json").write_text('{"target": "t", "status": "ACTIVE"}', encoding="utf-8")
        (loop_dir / "coverage.json").write_text('{}', encoding="utf-8")

        errors = validate_loop(self.temp_dir)
        self.assertTrue(any("profile.yaml" in e for e in errors), f"Expected missing profile error, got: {errors}")


if __name__ == "__main__":
    unittest.main()

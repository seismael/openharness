#!/usr/bin/env python3
"""Unit tests for init_loop and validate_loop scripts."""

import json
from pathlib import Path
import sys
import tempfile
import unittest

# Ensure the scripts directory is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from init_loop import init_project
from validate_loop import validate_loop


class TestLoopScripts(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_canonical_agents_loop_init_and_validate(self):
        # 1. Initialize empty directory with default canonical .agents/loop
        target = "Reduce memory allocations to zero"
        res = init_project(self.project_dir, target=target)
        self.assertEqual(res, 0)

        # 2. Check canonical structure exists under .agents/loop
        self.assertTrue((self.project_dir / ".agents" / "loop" / "env.json").is_file())
        self.assertTrue((self.project_dir / ".agents" / "loop" / "loop.json").is_file())
        self.assertTrue((self.project_dir / ".agents" / "loop" / "coverage.json").is_file())
        self.assertTrue((self.project_dir / ".agents" / "loop" / "knowledge" / "profile.yaml").is_file())
        self.assertTrue((self.project_dir / ".agents" / "loop" / "knowledge" / "index.md").is_file())
        self.assertTrue((self.project_dir / ".agents" / "subagents" / "diagnostician.yaml").is_file())
        self.assertTrue((self.project_dir / ".agents" / "subagents" / "architect.yaml").is_file())

        # 3. Check loop.json and env.json content
        loop_data = json.loads((self.project_dir / ".agents" / "loop" / "loop.json").read_text(encoding="utf-8"))
        self.assertEqual(loop_data["target"], target)
        self.assertEqual(loop_data["status"], "ACTIVE")

        env_data = json.loads((self.project_dir / ".agents" / "loop" / "env.json").read_text(encoding="utf-8"))
        self.assertEqual(env_data["loop_dir"], ".agents\\loop" if "\\" in env_data["loop_dir"] else ".agents/loop")

        # 4. Validate project passes with zero errors
        errors = validate_loop(self.project_dir)
        self.assertEqual(errors, [])

    def test_legacy_dual_init_and_validate(self):
        # Initialize with legacy separate .loop directory
        target = "Legacy test target"
        res = init_project(self.project_dir, target=target, use_legacy_dual=True)
        self.assertEqual(res, 0)

        self.assertTrue((self.project_dir / ".loop" / "loop.json").is_file())
        self.assertTrue((self.project_dir / ".agents" / "subagents" / "diagnostician.yaml").is_file())

        errors = validate_loop(self.project_dir)
        self.assertEqual(errors, [])

    def test_validate_detects_missing_loop(self):
        errors = validate_loop(self.project_dir)
        self.assertIn("Missing loop directory (expected .agents/loop or .loop)", errors)

    def test_validate_detects_root_scratch_contamination(self):
        init_project(self.project_dir, target="Test Target")
        scratch_file = self.project_dir / "_tmp_bad_script.py"
        scratch_file.write_text("print('bad')", encoding="utf-8")

        errors = validate_loop(self.project_dir)
        self.assertTrue(any("Root scratch contamination" in err for err in errors))


if __name__ == "__main__":
    unittest.main()

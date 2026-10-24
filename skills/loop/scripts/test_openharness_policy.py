#!/usr/bin/env python3
"""Regression tests for portable policy evaluation (RFC-0015)."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "openharness_policy.py"


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="ohp_policy_"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def policy(self, rules, default=None):
        document = {"schema": "openharness.policy.v1", "rules": rules}
        if default is not None:
            document["default"] = default
        path = self.root / "policy.json"
        path.write_text(json.dumps(document), encoding="utf-8")
        return path

    def run_policy(self, path, *extra):
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "--policy", str(path), *extra],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def test_unmatched_action_asks_by_default(self):
        path = self.policy([])
        result = self.run_policy(path, "--tool", "shell")
        self.assertEqual(result.returncode, 3)
        self.assertEqual(json.loads(result.stdout)["verdict"], "ask")

    def test_allow_rule_exits_zero(self):
        path = self.policy(
            [
                {
                    "id": "tests",
                    "match": {"tool": "shell", "command_regex": "^python -m pytest"},
                    "verdict": "allow",
                    "reason": "declared pipeline",
                }
            ],
            default="deny",
        )
        result = self.run_policy(
            path, "--tool", "shell", "--command", "python -m pytest -q"
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["rule"], "tests")
        self.assertEqual(payload["reason"], "declared pipeline")

    def test_last_match_wins(self):
        path = self.policy(
            [
                {"id": "broad", "match": {"tool": "shell"}, "verdict": "allow"},
                {
                    "id": "narrow",
                    "match": {"tool": "shell", "command_regex": "rm -rf"},
                    "verdict": "deny",
                    "reason": "destructive",
                },
            ]
        )
        result = self.run_policy(path, "--tool", "shell", "--command", "rm -rf build")
        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["matched"], ["broad", "narrow"])
        self.assertEqual(payload["verdict"], "deny")

    def test_later_allow_can_reopen_an_earlier_deny(self):
        path = self.policy(
            [
                {"id": "deny-all", "match": {"tool": "shell"}, "verdict": "deny"},
                {
                    "id": "allow-readonly",
                    "match": {"tool": "shell", "command_regex": "^git status"},
                    "verdict": "allow",
                },
            ]
        )
        result = self.run_policy(path, "--tool", "shell", "--command", "git status")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_path_glob_matches_normalized_separator(self):
        path = self.policy(
            [
                {
                    "id": "secrets",
                    "match": {"path_glob": ".env*"},
                    "verdict": "deny",
                    "reason": "secret material",
                }
            ]
        )
        result = self.run_policy(path, "--path", ".env.local")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["rule"], "secrets")

    def test_rule_needing_absent_input_does_not_match(self):
        path = self.policy(
            [
                {
                    "id": "needs-command",
                    "match": {"tool": "shell", "command_regex": "true"},
                    "verdict": "deny",
                }
            ],
            default="allow",
        )
        result = self.run_policy(path, "--tool", "shell")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(json.loads(result.stdout)["matched"], [])

    def test_invalid_regex_is_refused(self):
        path = self.policy(
            [{"id": "bad", "match": {"command_regex": "([unclosed"}, "verdict": "deny"}]
        )
        result = self.run_policy(path, "--command", "anything")
        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid command_regex", json.loads(result.stdout)["error"])

    def test_duplicate_rule_id_is_refused(self):
        path = self.policy(
            [
                {"id": "same", "match": {"tool": "a"}, "verdict": "allow"},
                {"id": "same", "match": {"tool": "b"}, "verdict": "deny"},
            ]
        )
        result = self.run_policy(path, "--tool", "a")
        self.assertEqual(result.returncode, 2)

    def test_unknown_match_key_is_refused(self):
        path = self.policy(
            [{"id": "x", "match": {"tool_name": "a"}, "verdict": "deny"}]
        )
        result = self.run_policy(path, "--tool", "a")
        self.assertEqual(result.returncode, 2)

    def test_empty_match_is_refused(self):
        path = self.policy([{"id": "x", "match": {}, "verdict": "deny"}])
        result = self.run_policy(path, "--tool", "a")
        self.assertEqual(result.returncode, 2)

    def test_no_selectors_is_refused(self):
        result = self.run_policy(self.policy([]))
        self.assertEqual(result.returncode, 2)

    def test_wrong_schema_is_refused(self):
        path = self.root / "policy.json"
        path.write_text(
            json.dumps({"schema": "other.v1", "rules": []}), encoding="utf-8"
        )
        result = self.run_policy(path, "--tool", "a")
        self.assertEqual(result.returncode, 2)

    def test_output_is_deterministic(self):
        path = self.policy(
            [{"id": "a", "match": {"tool": "shell"}, "verdict": "allow"}]
        )
        first = self.run_policy(path, "--tool", "shell")
        second = self.run_policy(path, "--tool", "shell")
        self.assertEqual(first.stdout, second.stdout)


if __name__ == "__main__":
    unittest.main()

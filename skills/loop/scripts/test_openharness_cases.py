#!/usr/bin/env python3
"""Regression tests for the declared-case runner (RFC-0012)."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "openharness_cases.py"
FP = "c" * 64


def py(code):
    return f'"{sys.executable}" -c "{code}"'


class CaseRunnerTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="ohp_cases_"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)

    def declare(self, cases, document=False):
        payload = {"schema": "openharness.cases.v1", "cases": cases} if document else cases
        path = self.root / "cases.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def run_cases(self, path, *extra):
        return subprocess.run(
            [
                sys.executable,
                "-B",
                str(SCRIPT),
                "--cases",
                str(path),
                "--workdir",
                str(self.root),
                *extra,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
        )

    def test_passing_cases_exit_zero(self):
        path = self.declare(
            [
                {
                    "id": "prints",
                    "command": py("print('ready')"),
                    "expect": {"stdout_contains": "ready"},
                },
                {
                    "id": "exits",
                    "command": py("raise SystemExit(0)"),
                    "expect": {"exit_code": 0},
                },
            ]
        )
        result = self.run_cases(path)
        self.assertEqual(result.returncode, 0, result.stdout)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["passed"], 2)
        self.assertEqual(payload["failed"], 0)

    def test_failing_predicate_exits_one(self):
        path = self.declare(
            [
                {
                    "id": "loud",
                    "command": py("print('noise')"),
                    "expect": {"stdout_contains": "ready"},
                }
            ]
        )
        result = self.run_cases(path)
        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["failed"], 1)
        self.assertEqual(payload["results"][0]["detail"], "expected output text not found")

    def test_wrong_exit_code_is_reported(self):
        path = self.declare(
            [
                {
                    "id": "boom",
                    "command": py("raise SystemExit(3)"),
                    "expect": {"exit_code": 0},
                }
            ]
        )
        result = self.run_cases(path)
        self.assertEqual(result.returncode, 1)
        self.assertIn("exit 3, expected 0", json.loads(result.stdout)["results"][0]["detail"])

    def test_timeout_is_distinct_from_failure(self):
        path = self.declare(
            [
                {
                    "id": "slow",
                    "command": py("import time; time.sleep(10)"),
                    "timeout_s": 1,
                }
            ]
        )
        result = self.run_cases(path)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["results"][0]["status"], "timeout")

    def test_artifact_predicate(self):
        path = self.declare(
            [
                {
                    "id": "writes",
                    "command": py("open('out.txt','w').write('x')"),
                    "expect": {"artifact": "out.txt"},
                }
            ]
        )
        result = self.run_cases(path)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertTrue((self.root / "out.txt").is_file())

    def test_missing_artifact_fails(self):
        path = self.declare(
            [
                {
                    "id": "absent",
                    "command": py("pass"),
                    "expect": {"artifact": "ghost.txt"},
                }
            ]
        )
        result = self.run_cases(path)
        self.assertEqual(result.returncode, 1)
        self.assertIn("artifact missing", json.loads(result.stdout)["results"][0]["detail"])

    def test_unknown_expect_key_is_a_declaration_error(self):
        path = self.declare([{"id": "bad", "command": py("pass"), "expect": {"latency_ms": 5}}])
        result = self.run_cases(path)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["problems"][0]["code"], "case.expect_unknown")

    def test_duplicate_ids_are_refused(self):
        path = self.declare(
            [
                {"id": "same", "command": py("pass")},
                {"id": "same", "command": py("pass")},
            ]
        )
        result = self.run_cases(path)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["problems"][0]["code"], "case.id_duplicate")

    def test_missing_command_is_refused(self):
        path = self.declare([{"id": "hollow"}])
        result = self.run_cases(path)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["problems"][0]["code"], "case.command_missing")

    def test_dry_run_does_not_execute(self):
        path = self.declare(
            [
                {
                    "id": "never",
                    "command": py("raise SystemExit(7)"),
                    "expect": {"exit_code": 7},
                }
            ]
        )
        result = self.run_cases(path, "--dry-run")
        self.assertEqual(result.returncode, 0, result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["mode"], "dry-run")
        self.assertEqual(payload["count"], 1)

    def test_only_selects_a_subset(self):
        path = self.declare(
            [
                {"id": "one", "command": py("pass")},
                {"id": "two", "command": py("raise SystemExit(4)")},
            ]
        )
        result = self.run_cases(path, "--only", "one")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(json.loads(result.stdout)["cases"], 1)

    def test_unknown_only_id_is_refused(self):
        path = self.declare([{"id": "one", "command": py("pass")}])
        result = self.run_cases(path, "--only", "ghost")
        self.assertEqual(result.returncode, 2)
        self.assertIn("unknown case ids", json.loads(result.stdout)["error"])

    def test_receipt_is_stamped_with_fingerprint(self):
        path = self.declare([{"id": "one", "command": py("pass")}])
        receipt = self.root / "probe.receipt.json"
        result = self.run_cases(path, "--receipt", str(receipt), "--fingerprint", FP)
        self.assertEqual(result.returncode, 0, result.stdout)
        payload = json.loads(receipt.read_text(encoding="utf-8-sig"))
        self.assertEqual(payload["harness_fingerprint"], FP)
        self.assertTrue(payload["ok"])

    def test_object_document_is_accepted(self):
        path = self.declare([{"id": "one", "command": py("pass")}], document=True)
        result = self.run_cases(path)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_unknown_document_key_is_refused(self):
        path = self.root / "cases.json"
        path.write_text(
            json.dumps({"cases": [{"id": "one", "command": py("pass")}], "extra": True}),
            encoding="utf-8",
        )
        result = self.run_cases(path)
        self.assertEqual(result.returncode, 2)
        self.assertIn("unknown document keys", json.loads(result.stdout)["error"])

    def test_invalid_json_exits_two(self):
        path = self.root / "cases.json"
        path.write_text("{not json", encoding="utf-8")
        result = self.run_cases(path)
        self.assertEqual(result.returncode, 2)

    def test_output_is_bounded_and_deterministic(self):
        path = self.declare(
            [
                {
                    "id": f"case-{index:02d}",
                    "command": py("pass"),
                    "expect": {"exit_code": 0},
                }
                for index in range(80)
            ]
        )
        first = self.run_cases(path)
        second = self.run_cases(path)
        self.assertEqual(first.returncode, 0, first.stdout)
        self.assertLessEqual(len(first.stdout.encode("utf-8")), 2500)
        self.assertEqual(first.stdout, second.stdout)


if __name__ == "__main__":
    unittest.main()

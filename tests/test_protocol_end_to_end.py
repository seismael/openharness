#!/usr/bin/env python3
"""End-to-end composition: audit -> case receipt -> journal -> projections.

Each helper has its own regression suite. This one proves the artifacts compose:
the fingerprint the audit emits is the one the receipt carries, the receipt the
journal cites, and the journal the projection reads. It also proves drift is
detected rather than averaged away.
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "loop" / "scripts"
FP = "d" * 64


def py(code):
    return f'"{sys.executable}" -c "{code}"'


class ProtocolEndToEndTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="ohp_e2e_"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        self.write("AGENTS.md", "Read the runbook before changing the pipeline.\n")
        self.write(
            "skills/build/SKILL.md",
            "---\nname: build\ndescription: Build things\n---\nBody\n",
        )
        self.write(
            "harness.json",
            json.dumps(
                {
                    "schema": "harness.manifest.v1",
                    "name": "e2e",
                    "root": ".",
                    "components": [
                        {
                            "id": "prompt",
                            "kind": "system_prompt",
                            "paths": ["AGENTS.md"],
                            "always_on": True,
                        },
                        {
                            "id": "build",
                            "kind": "skills",
                            "paths": ["skills/*/SKILL.md"],
                        },
                    ],
                }
            ),
        )
        self.write(
            "cases.json",
            json.dumps(
                {
                    "schema": "openharness.cases.v1",
                    "cases": [
                        {
                            "id": "one",
                            "command": py("pass"),
                            "expect": {"exit_code": 0},
                        },
                        {
                            "id": "two",
                            "command": py("print('ok')"),
                            "expect": {"stdout_contains": "ok"},
                        },
                    ],
                }
            ),
        )
        self.write(
            "requirements.json",
            json.dumps(
                {
                    "schema": "openharness.requirements.v1",
                    "requirements": [
                        {"id": "entry", "kind": "system_prompt"},
                        {"id": "skills", "kind": "skills"},
                    ],
                }
            ),
        )
        self.write(
            "policy.json",
            json.dumps(
                {
                    "schema": "openharness.policy.v1",
                    "default": "ask",
                    "rules": [
                        {
                            "id": "declared",
                            "match": {"tool": "shell", "command_regex": "^python -B"},
                            "verdict": "allow",
                        },
                        {
                            "id": "no-destructive",
                            "match": {"tool": "shell", "command_regex": "rm -rf"},
                            "verdict": "deny",
                            "reason": "destructive",
                        },
                    ],
                }
            ),
        )

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def run_script(self, name, *args):
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPTS / name), *args],
            cwd=str(self.root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=300,
        )

    def audit_fingerprint(self):
        result = self.run_script(
            "openharness_audit.py", "--manifest", "harness.json", "--fingerprint-only"
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        return json.loads(result.stdout)["fingerprint"]

    def journal(self, *entries):
        path = self.root / "journal.jsonl"
        path.write_text("\n".join(json.dumps(item) for item in entries) + "\n", encoding="utf-8")
        return path

    def test_full_chain_composes(self):
        fingerprint = self.audit_fingerprint()
        self.assertRegex(fingerprint, r"^[a-f0-9]{64}$")

        probe = self.run_script(
            "openharness_cases.py",
            "--cases",
            "cases.json",
            "--workdir",
            ".",
            "--receipt",
            "probe.receipt.json",
            "--fingerprint",
            fingerprint,
        )
        self.assertEqual(probe.returncode, 0, probe.stdout)
        receipt = json.loads((self.root / "probe.receipt.json").read_text(encoding="utf-8"))
        self.assertTrue(receipt["ok"])
        self.assertEqual(receipt["harness_fingerprint"], fingerprint)
        self.assertEqual(receipt["passed"], 2)

        adopted = {
            "ts": "2026-10-24T00:00:00Z",
            "iteration": 1,
            "front": "improve",
            "hypothesis": "Trimming the prompt keeps both cases green",
            "decision": "adopted",
            "scope": "invariant",
            "deficiency": "context-management",
            "cases": ["one", "two"],
            "metric_before": 10.0,
            "metric_after": 12.0,
            "contrast": "mitigated",
            "harness_fingerprint": fingerprint,
            "evidence_ref": "probe.receipt.json",
            "rationale": "both declared cases passed on the audited state",
            "cost": {"tokens_in": 100, "tokens_out": 50, "usd": 0.5},
        }
        failed = {
            "ts": "2026-10-24T00:10:00Z",
            "iteration": 2,
            "front": "debug",
            "hypothesis": "The cache invalidates on write",
            "decision": "rejected",
            "scope": "local",
            "cases": ["one"],
            "failure": {"class": "wrong-premise", "detail": "invalidation was correct"},
            "rationale": "the premise was false",
            "cost": {"tool_calls": 4},
        }
        journal = self.journal(adopted, failed)

        verify = self.run_script(
            "openharness_verify.py",
            "--journal",
            str(journal),
            "--fingerprint",
            fingerprint,
        )
        self.assertEqual(verify.returncode, 0, verify.stdout)

        telemetry = json.loads(
            self.run_script("openharness_telemetry.py", "--journal", str(journal)).stdout
        )
        self.assertEqual(telemetry["iterations"], 2)
        self.assertEqual(telemetry["decisions"]["adopted"], 1)
        self.assertEqual(telemetry["gain_total"], 2.0)
        self.assertEqual(telemetry["cost"]["usd"], 0.5)
        self.assertEqual(telemetry["cost_per_gain"]["usd"], 0.25)
        self.assertEqual(telemetry["evidence_coverage"], 1.0)

        failures = json.loads(
            self.run_script("openharness_failures.py", "--journal", str(journal)).stdout
        )
        self.assertEqual(failures["classes"], {"wrong-premise": 1})
        self.assertEqual(failures["repeated"], [])
        self.assertEqual(failures["rate"], 0.5)

        inventory = json.loads(
            self.run_script(
                "openharness_inventory.py",
                "--manifest",
                "harness.json",
                "--requirements",
                "requirements.json",
            ).stdout
        )
        self.assertTrue(inventory["ok"])
        self.assertEqual(inventory["coverage"], 1.0)
        self.assertEqual(inventory["fingerprint"], fingerprint)

    def test_policy_verdicts_are_distinct(self):
        args = ["--policy", "policy.json", "--tool", "shell", "--command"]
        allow = self.run_script("openharness_policy.py", *args, "python -B -m unittest")
        deny = self.run_script("openharness_policy.py", *args, "rm -rf build")
        ask = self.run_script("openharness_policy.py", *args, "Get-Content README.md")
        self.assertEqual(allow.returncode, 0, allow.stdout)
        self.assertEqual(deny.returncode, 1, deny.stdout)
        self.assertEqual(ask.returncode, 3, ask.stdout)
        self.assertEqual(json.loads(deny.stdout)["reason"], "destructive")

    def test_drift_makes_the_record_stale(self):
        fingerprint = self.audit_fingerprint()
        journal = self.journal(
            {
                "ts": "2026-10-24T00:00:00Z",
                "iteration": 1,
                "front": "improve",
                "hypothesis": "The trimmed prompt stays green",
                "decision": "adopted",
                "scope": "invariant",
                "cases": ["one", "two"],
                "metric_before": 1.0,
                "metric_after": 2.0,
                "contrast": "mitigated",
                "harness_fingerprint": fingerprint,
                "evidence_ref": "probe.receipt.json",
                "rationale": "both cases passed",
            }
        )
        self.assertEqual(
            self.run_script(
                "openharness_verify.py",
                "--journal",
                str(journal),
                "--fingerprint",
                fingerprint,
            ).returncode,
            0,
        )

        self.write("AGENTS.md", "A different instruction changes the state.\n")
        drifted = self.audit_fingerprint()
        self.assertNotEqual(fingerprint, drifted)
        result = self.run_script(
            "openharness_verify.py",
            "--journal",
            str(journal),
            "--fingerprint",
            drifted,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn(
            "fingerprint.stale",
            [item["code"] for item in json.loads(result.stdout)["findings"]],
        )


if __name__ == "__main__":
    unittest.main()

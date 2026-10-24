"""CLI contract: exit codes, determinism, drift attribution, and report formats."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ElementTree
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "tests" / "fixtures" / "harness"
INIT_FIXTURE = ROOT / "tests" / "fixtures" / "init"
SCRIPTS = ROOT / "skills" / "loop" / "scripts"
COMMANDS = (
    "init",
    "lock",
    "plan",
    "audit",
    "verify",
    "select",
    "cases",
    "telemetry",
    "inventory",
    "failures",
    "policy",
    "report",
)


class CliContractTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="ohp_cli_")
        self.addCleanup(self.temporary.cleanup)
        self.workdir = Path(self.temporary.name) / "harness"
        shutil.copytree(FIXTURE, self.workdir)

    def run_cli(self, *args: str, workdir: Path | None = None):
        environment = dict(os.environ)
        environment["PYTHONPATH"] = os.pathsep.join(
            filter(None, [str(SCRIPTS), environment.get("PYTHONPATH", "")])
        )
        return subprocess.run(
            [sys.executable, "-B", "-m", "openharness", *args],
            cwd=str(workdir or self.workdir),
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=300,
        )

    def test_every_command_has_help(self):
        for command in COMMANDS:
            with self.subTest(command=command):
                result = self.run_cli(command, "--help")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("usage:", result.stdout.lower())

    def test_usage_and_finding_exit_codes(self):
        bad = self.run_cli("audit", "--manifest", "absent.json")
        self.assertEqual(bad.returncode, 2)
        self.assertIn("cannot read manifest", bad.stdout)

        ask = self.run_cli(
            "policy", "--policy", "policy.json", "--tool", "shell", "--command", "ls"
        )
        self.assertEqual(ask.returncode, 3)
        self.assertEqual(json.loads(ask.stdout)["verdict"], "ask")

        deny = self.run_cli(
            "policy",
            "--policy",
            "policy.json",
            "--tool",
            "shell",
            "--command",
            "rm -rf x",
        )
        self.assertEqual(deny.returncode, 1)

        missing_lock = self.run_cli("plan", "--check")
        self.assertEqual(missing_lock.returncode, 2)

        locked_check = self.run_cli("lock", "--check", "--output", "absent.lock")
        self.assertEqual(locked_check.returncode, 2)

    def test_lock_is_deterministic_and_plan_checks_it(self):
        first = self.run_cli("lock")
        self.assertEqual(first.returncode, 0, first.stderr)
        content = (self.workdir / "harness.lock").read_text(encoding="utf-8")
        second = self.run_cli("lock")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual((self.workdir / "harness.lock").read_text(encoding="utf-8"), content)

        clean = self.run_cli("plan", "--check")
        self.assertEqual(clean.returncode, 0, clean.stderr)
        self.assertIn("no drift", clean.stdout)

        match = self.run_cli("lock", "--check")
        self.assertEqual(match.returncode, 0, match.stderr)
        self.assertTrue(json.loads(match.stdout)["match"])

    def test_plan_attributes_each_change(self):
        self.assertEqual(self.run_cli("lock").returncode, 0)
        (self.workdir / "AGENTS.md").write_text("changed instructions\n", encoding="utf-8")
        (self.workdir / "skills" / "extra").mkdir()
        (self.workdir / "skills" / "extra" / "SKILL.md").write_text(
            "---\nname: extra\ndescription: Extra\n---\nBody\n", encoding="utf-8"
        )
        (self.workdir / "policy.json").write_text(
            (self.workdir / "policy.json").read_text(encoding="utf-8") + "\n",
            encoding="utf-8",
        )

        drift = self.run_cli("plan", "--check")
        self.assertEqual(drift.returncode, 1, drift.stderr)
        self.assertIn("~ AGENTS.md (agents)", drift.stdout)
        self.assertIn("+ skills/extra/SKILL.md (skills)", drift.stdout)
        self.assertIn("declaration: policy", drift.stdout)

        payload = json.loads(self.run_cli("plan", "--format", "json").stdout)
        self.assertFalse(payload["ok"])
        changes = {(item["change"], item["path"]) for item in payload["changes"]}
        self.assertIn(("modified", "AGENTS.md"), changes)
        self.assertIn(("added", "skills/extra/SKILL.md"), changes)

    def test_init_discovers_and_never_overwrites(self):
        target = Path(self.temporary.name) / "fresh"
        shutil.copytree(INIT_FIXTURE, target)

        created = self.run_cli("init", "--name", "fresh", workdir=target)
        self.assertEqual(created.returncode, 0, created.stdout)
        self.assertTrue((target / "harness.json").is_file())
        self.assertTrue((target / "harness.lock").is_file())
        manifest = json.loads((target / "harness.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema"], "harness.manifest.v1")
        self.assertEqual({item["id"] for item in manifest["components"]}, {"agents", "skills"})
        self.assertEqual(
            self.run_cli("audit", "--manifest", "harness.json", workdir=target).returncode,
            0,
        )
        self.assertEqual(self.run_cli("plan", "--check", workdir=target).returncode, 0)

        sentinel = (target / "harness.json").read_text(encoding="utf-8")
        refused = self.run_cli("init", workdir=target)
        self.assertEqual(refused.returncode, 1)
        self.assertEqual((target / "harness.json").read_text(encoding="utf-8"), sentinel)

    def test_init_reports_an_empty_repository(self):
        target = Path(self.temporary.name) / "empty"
        target.mkdir()
        result = self.run_cli("init", workdir=target)
        self.assertEqual(result.returncode, 1)
        self.assertIn("no agent harness surface", result.stdout)
        self.assertFalse((target / "harness.json").exists())

    def test_report_formats_are_valid(self):
        self.assertEqual(self.run_cli("lock").returncode, 0)

        markdown = self.run_cli(
            "report", "--requirements", "requirements.json", "--format", "markdown"
        )
        self.assertEqual(markdown.returncode, 0, markdown.stdout)
        text = (self.workdir / "harness-report.md").read_text(encoding="utf-8")
        self.assertIn("# Harness report: fixture", text)
        self.assertIn("## Lockfile", text)

        sarif = self.run_cli("report", "--requirements", "requirements.json", "--format", "sarif")
        self.assertEqual(sarif.returncode, 0, sarif.stdout)
        document = json.loads((self.workdir / "harness-report.sarif").read_text(encoding="utf-8"))
        self.assertEqual(document["version"], "2.1.0")
        self.assertEqual(len(document["runs"]), 1)

        junit = self.run_cli("report", "--requirements", "requirements.json", "--format", "junit")
        self.assertEqual(junit.returncode, 0, junit.stdout)
        suite = ElementTree.parse(self.workdir / "harness-report.xml").getroot()
        self.assertEqual(suite.tag, "testsuite")

        payload = self.run_cli("report", "--requirements", "requirements.json", "--format", "json")
        self.assertEqual(payload.returncode, 0, payload.stdout)
        report = json.loads((self.workdir / "harness-report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["schema"], "openharness.report.v1")
        self.assertTrue(report["ok"])
        self.assertTrue(report["lock"]["match"])

    def test_report_executes_declared_cases(self):
        result = self.run_cli(
            "report",
            "--requirements",
            "requirements.json",
            "--cases",
            "cases.json",
            "--execute",
            "--format",
            "json",
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        report = json.loads((self.workdir / "harness-report.json").read_text(encoding="utf-8"))
        self.assertTrue(report["cases"]["executed"])
        self.assertEqual(report["cases"]["passed"], 2)

    def test_report_fails_on_findings(self):
        result = self.run_cli("report", "--manifest", "harness-broken.json")
        self.assertEqual(result.returncode, 1, result.stdout)
        receipt = json.loads(result.stdout)
        self.assertFalse(receipt["ok"])
        self.assertGreater(receipt["counts"]["error"], 0)


if __name__ == "__main__":
    unittest.main()

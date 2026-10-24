#!/usr/bin/env python3
"""Adapter conformance: every claimed mechanism has an artifact that exists (RFC-0015)."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADAPTER = ROOT / "adapters" / "opencode"
SCRIPTS = ROOT / "skills" / "loop" / "scripts"
LEVELS = {"native", "adapter", "documented"}
MECHANISMS = (
    "Harness audit",
    "Iteration contract",
    "Anonymous selection",
    "Declared cases",
    "Telemetry",
    "Inventory",
    "Failure taxonomy",
    "Portable policy",
)


class AdapterConformanceTests(unittest.TestCase):
    def read(self, path):
        return Path(path).read_text(encoding="utf-8")

    def matrix_rows(self):
        readme = self.read(ADAPTER / "README.md")
        section = readme.split("## Enforcement matrix", 1)
        self.assertEqual(len(section), 2, "adapter README has no enforcement matrix")
        body = section[1].split("\n## ", 1)[0]
        rows = {}
        for line in body.splitlines():
            if not line.startswith("| ") or line.startswith("| :") or "---" in line:
                continue
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if len(cells) >= 3 and cells[0] in MECHANISMS:
                rows[cells[0]] = cells
        return body, rows

    def test_matrix_covers_every_mechanism_once(self):
        _, rows = self.matrix_rows()
        self.assertEqual(sorted(rows), sorted(MECHANISMS))
        for name, cells in rows.items():
            level = cells[2].strip("`")
            self.assertIn(level, LEVELS, f"{name}: unknown level {level}")

    def test_every_adapter_mechanism_names_an_existing_artifact(self):
        _, rows = self.matrix_rows()
        for name, cells in rows.items():
            artifact = re.search(r"`(openharness_[a-z_]+\.py)`", cells[1])
            self.assertIsNotNone(artifact, f"{name}: no script artifact")
            self.assertTrue(
                (SCRIPTS / artifact.group(1)).is_file(),
                f"{name}: artifact {artifact.group(1)} does not exist",
            )

    def test_documented_level_states_the_host_limitation(self):
        body, rows = self.matrix_rows()
        documented = [name for name, cells in rows.items() if cells[2].strip("`") == "documented"]
        self.assertTrue(documented, "no mechanism is honestly marked documented")
        self.assertIn("host limitation", body)

    def test_command_exposes_every_sub_mode(self):
        command = self.read(ADAPTER / "commands" / "openharness.md")
        for sub_mode in (
            "inventory",
            "cases",
            "measure",
            "failures",
            "policy",
            "select",
            "verify",
        ):
            self.assertIn(f"`{sub_mode}", command, f"missing sub-mode {sub_mode}")
        for script in set(re.findall(r"openharness_[a-z_]+\.py", command)):
            self.assertTrue((SCRIPTS / script).is_file(), f"missing script {script}")

    def test_command_frontmatter_is_minimal(self):
        command = self.read(ADAPTER / "commands" / "openharness.md")
        self.assertTrue(command.startswith("---\n"))
        frontmatter = command.split("---", 2)[1]
        keys = [line.split(":", 1)[0].strip() for line in frontmatter.splitlines() if line.strip()]
        self.assertEqual(keys, ["description"])

    def test_agent_is_read_only_and_may_run_only_projections(self):
        agent = self.read(ADAPTER / "agents" / "harness-editor.md")
        self.assertIn("mode: subagent", agent)
        self.assertIn("action: edit", agent)
        self.assertIn("effect: deny", agent)
        for script in (
            "openharness_audit.py",
            "openharness_inventory.py",
            "openharness_verify.py",
            "openharness_telemetry.py",
            "openharness_failures.py",
        ):
            self.assertIn(script, agent)
        self.assertNotIn("openharness_policy.py", agent.split("---", 2)[2])
        body = agent.split("---", 2)[2]
        self.assertIn("closed taxonomy", body)
        self.assertIn("harness gap", body)

    def test_adapter_does_not_claim_token_measurement(self):
        for relative in (
            "README.md",
            "commands/openharness.md",
            "agents/harness-editor.md",
        ):
            text = self.read(ADAPTER / relative).lower()
            for phrase in ("measured tokens", "token measurement", "tokens measured"):
                self.assertNotIn(phrase, text, f"{relative} claims token measurement")


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Comprehensive conformance test suite for Open Harness Protocol (OHP).

Verifies schema contracts, internal skill initialization tools, multi-language
starter templates, polyglot archetypes, deterministic environment manifests,
and AST semantic code extraction under complete isolation.
"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from skills.loop.scripts.ast_slice import extract_polyglot_symbol, extract_python_symbol
from skills.loop.scripts.init_loop import init_project
from skills.loop.scripts.validate_loop import _load_yaml, validate_loop

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = ROOT / "docs" / "standards" / "schemas"
TEMPLATES_DIR = ROOT / "skills" / "loop" / "assets" / "templates"


class OHPConformanceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="ohp_test_"))

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_json_schemas_validity(self):
        """Verify all normative JSON schemas are valid and parseable."""
        schemas = [
            "profile.schema.json",
            "loop.schema.json",
            "journal.schema.json",
            "coverage.schema.json",
            "openharness.schema.json",
            "cases.schema.json",
            "policy.schema.json",
            "lock.schema.json",
            "context.schema.json",
        ]
        for s_name in schemas:
            schema_file = SCHEMAS_DIR / s_name
            self.assertTrue(schema_file.is_file(), f"Missing schema: {s_name}")
            data = json.loads(schema_file.read_text(encoding="utf-8"))
            self.assertIn("$schema", data)
            self.assertIn("type", data)
            self.assertEqual(data["type"], "object")

    def test_starter_templates_conformance(self):
        """Verify that Python, Rust, Go, and Node starter templates contain all required profile fields."""
        templates = [
            "profile.python.yaml",
            "profile.rust.yaml",
            "profile.go.yaml",
            "profile.node.yaml",
        ]
        required_fields = [
            "schema",
            "project",
            "target",
            "metric",
            "paths",
            "boundaries",
            "pipeline",
            "gates",
            "completion",
        ]
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

    def test_polyglot_archetype_deep_conformance(self):
        """Verify 4 distinct polyglot project archetypes initialize with exact target semantics."""
        archetypes = [
            (
                "python",
                "Maximize inference batch throughput (> 1,000 samples/sec)",
                "python_bin",
            ),
            (
                "rust",
                "Eliminate all heap allocations on the hot path (zero alloc)",
                "test_cmd",
            ),
            ("go", "Reduce p99 database query latency under 5ms", "loop_dir"),
            (
                "node",
                "Reduce initial bundle size under 150KB and TTFB under 80ms",
                "scratch_dir",
            ),
        ]

        for tmpl, target_str, check_key in archetypes:
            proj_dir = self.temp_dir / f"archetype_{tmpl}"
            proj_dir.mkdir(parents=True)

            rc = init_project(proj_dir, target=target_str, template=tmpl)
            self.assertEqual(rc, 0)

            loop_dir = proj_dir / ".agents" / "loop"

            # Check env.json
            env_file = loop_dir / "env.json"
            self.assertTrue(env_file.is_file())
            env_data = json.loads(env_file.read_text(encoding="utf-8"))
            self.assertIn(check_key, env_data)
            self.assertEqual(env_data["project_name"], proj_dir.name)

            # Check loop.json target preservation
            loop_data = json.loads((loop_dir / "loop.json").read_text(encoding="utf-8"))
            self.assertEqual(loop_data["target"], target_str)
            self.assertEqual(loop_data["status"], "ACTIVE")

            # Check profile.yaml target substitution
            profile_content = (loop_dir / "knowledge" / "profile.yaml").read_text(encoding="utf-8")
            self.assertIn(target_str, profile_content)

            # Check subagent personas are created in both .agents/subagents/ and .opencode/agent/
            subagents_dir = proj_dir / ".agents" / "subagents"
            self.assertTrue(subagents_dir.is_dir())
            opencode_dir = proj_dir / ".opencode" / "agent"
            self.assertTrue(opencode_dir.is_dir())
            for persona in ["diagnostician", "architect", "verifier", "synthesizer"]:
                self.assertTrue(
                    (opencode_dir / f"{persona}.md").is_file(),
                    f"Missing OpenCode persona: {persona}",
                )
                self.assertTrue(
                    (subagents_dir / f"{persona}.yaml").is_file(),
                    f"Missing subagent persona: {persona}",
                )

    def test_polyglot_ast_slicing_integration(self):
        """Verify zero-dependency AST semantic slicing across Python, Rust, Go, and TypeScript."""
        # 1. Python Native AST
        py_code = (
            "import os\n\n"
            "class Engine:\n"
            "    def run(self):\n"
            "        pass\n\n"
            "def optimize_hot_path(x: int) -> int:\n"
            "    # Critical loop\n"
            "    y = x * 2\n"
            "    return y + 1\n\n"
            "def secondary():\n"
            "    pass\n"
        )
        res_py = extract_python_symbol(py_code, "engine.py", "optimize_hot_path")
        self.assertIsNotNone(res_py)
        self.assertEqual(res_py["symbol"], "optimize_hot_path")
        self.assertEqual(res_py["kind"], "function")
        self.assertEqual(res_py["start_line"], 7)
        self.assertEqual(res_py["end_line"], 10)
        self.assertIn("return y + 1", res_py["code"])

        # 2. Rust polyglot fallback
        rust_code = (
            "use std::sync::Arc;\n\n"
            "pub fn process_event(event_id: u64) -> Result<(), Error> {\n"
            "    let payload = fetch(event_id)?;\n"
            "    validate(&payload);\n"
            "    Ok(())\n"
            "}\n\n"
            "fn auxiliary() {}\n"
        )
        res_rust = extract_polyglot_symbol(rust_code, "lib.rs", "process_event")
        self.assertIsNotNone(res_rust)
        self.assertEqual(res_rust["symbol"], "process_event")
        self.assertEqual(res_rust["start_line"], 3)
        self.assertEqual(res_rust["end_line"], 7)
        self.assertIn("validate(&payload)", res_rust["code"])

        # 3. Go polyglot fallback
        go_code = (
            "package main\n\n"
            "func RouteQuery(ctx context.Context, q string) (*Result, error) {\n"
            "    resp := execute(q)\n"
            "    return resp, nil\n"
            "}\n"
        )
        res_go = extract_polyglot_symbol(go_code, "main.go", "RouteQuery")
        self.assertIsNotNone(res_go)
        self.assertEqual(res_go["symbol"], "RouteQuery")
        self.assertEqual(res_go["start_line"], 3)
        self.assertEqual(res_go["end_line"], 6)

        # 4. TypeScript/Node polyglot fallback
        ts_code = (
            "import { Request, Response } from 'express';\n\n"
            "export function handleMetrics(req: Request, res: Response) {\n"
            "    const report = buildReport();\n"
            "    res.json(report);\n"
            "}\n"
        )
        res_ts = extract_polyglot_symbol(ts_code, "handler.ts", "handleMetrics")
        self.assertIsNotNone(res_ts)
        self.assertEqual(res_ts["symbol"], "handleMetrics")
        self.assertEqual(res_ts["start_line"], 3)
        self.assertEqual(res_ts["end_line"], 6)

    def test_validate_detects_missing_seam(self):
        """Verify validate_loop reports an error when profile.yaml is missing."""
        loop_dir = self.temp_dir / ".agents" / "loop"
        loop_dir.mkdir(parents=True)
        (loop_dir / "loop.json").write_text('{"target": "t", "status": "ACTIVE"}', encoding="utf-8")
        (loop_dir / "coverage.json").write_text("{}", encoding="utf-8")

        errors = validate_loop(self.temp_dir)
        self.assertTrue(
            any("profile.yaml" in e for e in errors),
            f"Expected missing profile error, got: {errors}",
        )


class HarnessOptimizationConformanceTests(unittest.TestCase):
    """RFC-0009: the audit is deterministic, bounded, and refuses invalid manifests."""

    SCRIPT = ROOT / "skills" / "loop" / "scripts" / "openharness_audit.py"

    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp(prefix="ohp_harness_"))
        self.addCleanup(shutil.rmtree, self.temp_dir, ignore_errors=True)

    def write(self, relative, text):
        path = self.temp_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def manifest(self, components, budget=None):
        payload = {
            "schema": "harness.manifest.v1",
            "name": "conformance",
            "root": ".",
            "components": components,
        }
        if budget is not None:
            payload["budget"] = budget
        return self.write("harness.json", json.dumps(payload))

    def audit(self, path):
        return subprocess.run(
            [sys.executable, "-B", str(self.SCRIPT), "--manifest", str(path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def fixture(self):
        self.write("AGENTS.md", "When building, load the `build` skill.\n")
        self.write(
            "skills/build/SKILL.md",
            "---\nname: build\ndescription: Build things\n---\nBody\n",
        )
        return [
            {
                "id": "prompt",
                "kind": "system_prompt",
                "paths": ["AGENTS.md"],
                "always_on": True,
            },
            {"id": "build", "kind": "skills", "paths": ["skills/*/SKILL.md"]},
        ]

    def test_receipt_satisfies_bounded_projection(self):
        result = self.audit(self.manifest(self.fixture(), {"always_on_tokens": 1000}))
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertLessEqual(len(result.stdout.encode("utf-8")), 2500)
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt["schema"], "openharness.receipt.v1")
        for key in ("totals", "findings", "counts", "ok", "truncated"):
            self.assertIn(key, receipt)
        self.assertEqual(
            set(receipt["totals"]),
            {"always_on_tokens", "total_tokens", "files", "components"},
        )

    def test_audit_is_byte_identical_across_runs(self):
        path = self.manifest(self.fixture())
        self.assertEqual(self.audit(path).stdout, self.audit(path).stdout)

    def test_invalid_manifest_is_refused_without_receipt(self):
        path = self.manifest(self.fixture())
        path.write_text('{"schema": "harness.manifest.v0", "components": []}', encoding="utf-8")
        result = self.audit(path)
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertIn("error", payload)
        self.assertNotIn("totals", payload)

    def test_unreachable_component_is_an_error(self):
        components = self.fixture()
        self.write("AGENTS.md", "When deploying, read the runbook.\n")
        result = self.audit(self.manifest(components))
        self.assertEqual(result.returncode, 1)
        codes = [item["code"] for item in json.loads(result.stdout)["findings"]]
        self.assertIn("reachability.orphan", codes)

    def test_budget_violation_is_an_error(self):
        result = self.audit(self.manifest(self.fixture(), {"always_on_tokens": 1}))
        self.assertEqual(result.returncode, 1)
        codes = [item["code"] for item in json.loads(result.stdout)["findings"]]
        self.assertIn("budget.always_on_exceeded", codes)

    def test_reference_protocol_declares_scope_and_probe_rules(self):
        text = (ROOT / "skills" / "loop" / "references" / "openharness.md").read_text(
            encoding="utf-8"
        )
        for token in ("invariant", "local", "probe", "budget"):
            self.assertIn(token, text.lower())

    def test_opencode_adapter_uses_current_frontmatter(self):
        """V2 rejects the legacy `tools`/`permission` keys; keep the adapter loadable."""
        agent = (ROOT / "adapters" / "opencode" / "agents" / "harness-editor.md").read_text(
            encoding="utf-8"
        )
        command = (ROOT / "adapters" / "opencode" / "commands" / "openharness.md").read_text(
            encoding="utf-8"
        )
        self.assertTrue(agent.startswith("---\n"))
        self.assertIn("mode: subagent", agent)
        self.assertIn("permissions:", agent)
        for legacy in ("\ntools:", "\npermission:", "\ndisable:", "\nmaxSteps:"):
            self.assertNotIn(legacy, agent)
        self.assertIn("description:", command.split("---", 2)[1])
        self.assertNotIn("template:", command.split("---", 2)[1])

    def test_adapter_declares_every_component_kind(self):
        readme = (ROOT / "adapters" / "opencode" / "README.md").read_text(encoding="utf-8")
        for kind in (
            "system_prompt",
            "guardrails",
            "memory",
            "tool_guidance",
            "subagents",
            "skills",
            "scripts",
            "plugins",
        ):
            self.assertIn(f"`{kind}`", readme)


class ProtocolSeriesConformanceTests(unittest.TestCase):
    """RFC-0010 through RFC-0015: every declared mechanism has a contract and an artifact."""

    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_rfc_series_is_complete_and_indexed(self):
        index = self.read("docs/standards/README.md")
        for number in range(1, 18):
            label = f"rfc-{number:04d}"
            self.assertEqual(
                len(list((ROOT / "docs" / "standards").glob(f"{label}-*.md"))),
                1,
                f"missing or duplicated {label}",
            )
            self.assertIn(f"({label}-", index, f"{label} is not indexed")

    def test_journal_schema_declares_iteration_contract(self):
        schema = json.loads(self.read("docs/standards/schemas/journal.schema.json"))
        properties = schema["properties"]
        self.assertIn("preserved", properties["decision"]["enum"])
        self.assertEqual(properties["scope"]["enum"], ["invariant", "local"])
        self.assertEqual(
            properties["contrast"]["enum"],
            ["mitigated", "unchanged", "regressed", "unproven"],
        )
        self.assertEqual(properties["cases"]["type"], "array")
        self.assertEqual(
            set(properties["cost"]["properties"]),
            {"tokens_in", "tokens_out", "tool_calls", "retries", "wall_steps", "usd"},
        )
        self.assertEqual(properties["promote_global"]["type"], "boolean")
        self.assertIn("harness_fingerprint", properties)
        self.assertEqual(len(properties["failure"]["properties"]["class"]["enum"]), 9)

    def test_profile_and_cases_schema_agree_on_the_case_object(self):
        profile = json.loads(self.read("docs/standards/schemas/profile.schema.json"))
        cases = json.loads(self.read("docs/standards/schemas/cases.schema.json"))
        profile_case = profile["properties"]["cases"]["items"]
        standalone = cases["$defs"]["case"]
        self.assertEqual(set(profile_case["properties"]), set(standalone["properties"]))
        self.assertEqual(set(profile_case["required"]), {"id"})
        self.assertEqual(set(standalone["required"]), {"id", "command"})
        self.assertEqual(
            set(standalone["properties"]["expect"]["properties"]),
            {"exit_code", "stdout_contains", "artifact"},
        )
        self.assertFalse(standalone["properties"]["expect"]["additionalProperties"])

    def test_policy_schema_matches_the_evaluator_contract(self):
        schema = json.loads(self.read("docs/standards/schemas/policy.schema.json"))
        script = self.read("skills/loop/scripts/openharness/commands/policy.py")
        ids = self.read("skills/loop/scripts/openharness/schemas.py")
        self.assertEqual(schema["properties"]["schema"]["enum"], ["openharness.policy.v1"])
        self.assertIn('POLICY = "openharness.policy.v1"', ids)
        self.assertIn("CONTRACT = POLICY", script)
        self.assertEqual(schema["properties"]["default"]["default"], "ask")
        match = schema["$defs"]["rule"]["properties"]["match"]
        self.assertEqual(set(match["properties"]), {"tool", "path_glob", "command_regex"})
        self.assertEqual(match["minProperties"], 1)

    def test_every_protocol_script_has_a_regression_suite(self):
        scripts = ROOT / "skills" / "loop" / "scripts"
        for name in (
            "openharness_audit",
            "openharness_verify",
            "openharness_select",
            "openharness_cases",
            "openharness_telemetry",
            "openharness_inventory",
            "openharness_failures",
            "openharness_policy",
        ):
            self.assertTrue((scripts / f"{name}.py").is_file(), f"missing {name}.py")
            self.assertTrue((scripts / f"test_{name}.py").is_file(), f"missing test_{name}.py")

    def test_references_are_linked_from_the_skill(self):
        skill = self.read("skills/loop/SKILL.md")
        for reference in (
            "contrastive-iteration.md",
            "measurement.md",
            "capability-and-failure.md",
            "openharness.md",
        ):
            self.assertTrue(
                (ROOT / "skills" / "loop" / "references" / reference).is_file(),
                f"missing reference {reference}",
            )
            self.assertIn(reference, skill)


if __name__ == "__main__":
    unittest.main()

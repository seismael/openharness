"""In-process tests for the openharness package.

The command-line suites run every command as a subprocess, which proves the
installed behavior but measures no coverage. These tests call the same functions
directly, so the deterministic surface is exercised and measured in-process.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import shutil
import tempfile
import unittest
from collections.abc import Callable
from pathlib import Path
from typing import Any

from openharness import cli, digest, drift, errors, jsonio, manifest, receipts, schemas
from openharness.commands import (
    audit as audit_command,
)
from openharness.commands import (
    cases as cases_command,
)
from openharness.commands import (
    failures as failures_command,
)
from openharness.commands import (
    init as init_command,
)
from openharness.commands import (
    inventory as inventory_command,
)
from openharness.commands import (
    lock as lock_command,
)
from openharness.commands import (
    plan as plan_command,
)
from openharness.commands import (
    policy as policy_command,
)
from openharness.commands import (
    report as report_command,
)
from openharness.commands import (
    select as select_command,
)
from openharness.commands import (
    telemetry as telemetry_command,
)
from openharness.commands import (
    verify as verify_command,
)

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "tests" / "fixtures" / "harness"


def capture(call: Callable[..., int], *args: Any) -> tuple[int, str]:
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream):
        code = call(*args)
    return code, stream.getvalue()


def parse(module: Any, argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    module.configure(parser)
    return parser.parse_args([str(item) for item in (argv or [])])


class HarnessCase(unittest.TestCase):
    """A private copy of the golden fixture for every test."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="ohp_units_")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "harness"
        shutil.copytree(FIXTURE, self.root)

    def path(self, name: str) -> str:
        return str(self.root / name)

    def write(self, name: str, text: str) -> Path:
        target = self.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return target

    def write_json(self, name: str, payload: Any) -> Path:
        return self.write(name, json.dumps(payload))

    def lock(self) -> None:
        code, output = capture(
            lock_command.run,
            parse(
                lock_command,
                ["--manifest", self.path("harness.json"), "--output", self.path("harness.lock")],
            ),
        )
        self.assertEqual(code, errors.EXIT_OK, output)

    def manifest(self, **overrides: Any) -> dict[str, Any]:
        document = json.loads((self.root / "harness.json").read_text(encoding="utf-8"))
        document.update(overrides)
        return document


class JsonIOTests(unittest.TestCase):
    def test_serializations_are_stable(self) -> None:
        payload = {"b": 2, "a": 1}
        self.assertEqual(jsonio.compact(payload), '{"a":1,"b":2}')
        self.assertEqual(jsonio.spaced(payload), '{"a": 1, "b": 2}')
        self.assertEqual(jsonio.pretty(payload), '{\n  "a": 1,\n  "b": 2\n}')
        self.assertEqual(jsonio.byte_size("\u00e9"), 2)

    def test_bounded_uses_reducers_until_it_fits(self) -> None:
        small = {"a": 1}
        self.assertEqual(jsonio.bounded(small), '{"a":1}')

        big = {"a": "x" * 4000}
        reduced = jsonio.bounded(big, [lambda payload: {"a": "y"}, lambda p: p])
        self.assertEqual(reduced, '{"a":"y"}')

    def test_read_json_reports_stable_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            missing = Path(temporary) / "absent.json"
            with self.assertRaises(errors.OpenHarnessError) as caught:
                jsonio.read_json(missing)
            self.assertIn("cannot read document", caught.exception.message)

            broken = Path(temporary) / "broken.json"
            broken.write_text("{", encoding="utf-8")
            with self.assertRaises(errors.OpenHarnessError) as caught:
                jsonio.read_json(broken, "lock")
            self.assertIn("lock is not valid JSON", caught.exception.message)

    def test_load_jsonl_reports_line_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "journal.jsonl"
            entries, error = jsonio.load_jsonl(path)
            self.assertIsNone(entries)
            self.assertIn("cannot read journal", error or "")

            path.write_text('{"a":1}\n\n[1]\n', encoding="utf-8")
            entries, error = jsonio.load_jsonl(path)
            self.assertIsNone(entries)
            self.assertIn("line 3 is not a JSON object", error or "")

            path.write_text("{", encoding="utf-8")
            entries, error = jsonio.load_jsonl(path)
            self.assertIsNone(entries)
            self.assertIn("line 1 is not valid JSON", error or "")

            path.write_text('{"a":1}\n', encoding="utf-8")
            entries, error = jsonio.load_jsonl(path)
            self.assertEqual(entries, [{"a": 1}])
            self.assertIsNone(error)

    def test_write_text_creates_parents_with_lf(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "nested" / "file.json"
            jsonio.write_text(target, "{}\n")
            self.assertEqual(target.read_bytes(), b"{}\n")


class DigestTests(HarnessCase):
    def test_hashes_and_relative_paths(self) -> None:
        self.assertEqual(digest.sha256_text("a"), digest.sha256_bytes(b"a"))
        self.assertEqual(len(digest.sha256_file(self.root / "AGENTS.md")), 64)
        self.assertEqual(digest.relative_path(self.root / "AGENTS.md", self.root), "AGENTS.md")

        with self.assertRaises(ValueError):
            digest.relative_path(Path(tempfile.gettempdir()) / "elsewhere.md", self.root)

    def test_state_fingerprint_deduplicates(self) -> None:
        first = digest.state_fingerprint([self.root / "AGENTS.md"], self.root)
        second = digest.state_fingerprint(
            [self.root / "AGENTS.md", self.root / "AGENTS.md"], self.root
        )
        self.assertEqual(first, second)
        self.assertEqual(len(first), 64)


class ManifestTests(HarnessCase):
    def test_load_manifest_accepts_the_fixture(self) -> None:
        document, error = manifest.load_manifest(self.root / "harness.json")
        self.assertIsNone(error)
        self.assertEqual(document["name"], "fixture")

    def test_load_manifest_rejects_each_invalid_shape(self) -> None:
        invalid = {
            "not-object": [],
            "wrong-schema": {"schema": "other", "components": [{}]},
            "no-components": {"schema": schemas.MANIFEST, "components": []},
            "component-not-object": {"schema": schemas.MANIFEST, "components": [1]},
            "missing-id": {"schema": schemas.MANIFEST, "components": [{"kind": "skills"}]},
            "unknown-kind": {
                "schema": schemas.MANIFEST,
                "components": [{"id": "a", "kind": "nope", "paths": ["x"]}],
            },
            "bad-paths": {
                "schema": schemas.MANIFEST,
                "components": [{"id": "a", "kind": "skills", "paths": []}],
            },
            "bad-names": {
                "schema": schemas.MANIFEST,
                "components": [{"id": "a", "kind": "skills", "paths": ["x"], "trigger_names": [1]}],
            },
            "bad-budget": {
                "schema": schemas.MANIFEST,
                "components": [{"id": "a", "kind": "skills", "paths": ["x"]}],
                "budget": [],
            },
            "negative-budget": {
                "schema": schemas.MANIFEST,
                "components": [{"id": "a", "kind": "skills", "paths": ["x"]}],
                "budget": {"total_tokens": -1},
            },
        }
        for index, (label, payload) in enumerate(invalid.items()):
            with self.subTest(case=label):
                produced = self.write_json(f"invalid-{index}.json", payload)
                document, error = manifest.load_manifest(produced)
                self.assertIsNone(document)
                self.assertTrue(error)

    def test_load_manifest_rejects_duplicate_ids(self) -> None:
        produced = self.write_json(
            "duplicate.json",
            {
                "schema": schemas.MANIFEST,
                "components": [
                    {"id": "a", "kind": "skills", "paths": ["x"]},
                    {"id": "a", "kind": "skills", "paths": ["y"]},
                ],
            },
        )
        document, error = manifest.load_manifest(produced)
        self.assertIsNone(document)
        self.assertIn("duplicate component id", error or "")

    def test_require_manifest_raises_declaration_error(self) -> None:
        with self.assertRaises(errors.DeclarationError):
            manifest.require_manifest(self.root / "absent.json")

    def test_helpers(self) -> None:
        self.assertEqual(manifest.estimate_tokens("abcde"), 2)
        self.assertEqual(manifest.normalize("  A   B "), "a b")
        self.assertEqual(
            manifest.markdown_links("[a](x.md) [b](https://e) [c](#top)"),
            ["x.md"],
        )
        files = manifest.matched_files(self.root, ["skills/*/SKILL.md"])
        self.assertEqual(len(files), 1)
        names = manifest.declared_names({"trigger_names": ["build"]}, files)
        self.assertIn("build", names)

    def test_audit_reports_every_finding_kind(self) -> None:
        self.write("skills/dup/extra.md", "the same long line repeated across components\n")
        self.write("skills/orphan/SKILL.md", "---\nname: orphan\ndescription: x\n---\nBody\n")
        self.write("skills/build/SKILL.md", "the same long line repeated across components\n")
        self.write(
            "AGENTS.md",
            "See [missing](gone.md).\nthe same long line repeated across components\n",
        )
        self.write("empty.md", "   \n")
        produced = self.write_json(
            "harness-findings.json",
            {
                "schema": schemas.MANIFEST,
                "name": "findings",
                "root": ".",
                "budget": {"always_on_tokens": 1, "total_tokens": 1},
                "components": [
                    {
                        "id": "agents",
                        "kind": "system_prompt",
                        "paths": ["AGENTS.md"],
                        "always_on": True,
                    },
                    {"id": "skills", "kind": "skills", "paths": ["skills/*/SKILL.md"]},
                    {"id": "empty", "kind": "memory", "paths": ["empty.md"]},
                    {"id": "absent", "kind": "plugins", "paths": ["nothing/*.json"]},
                ],
            },
        )
        document = manifest.require_manifest(produced)
        result = manifest.audit(document, produced)
        codes = {item["code"] for item in result["findings"]}
        self.assertIn("component.empty", codes)
        self.assertIn("link.missing", codes)
        self.assertIn("component.missing", codes)
        self.assertIn("duplication.line", codes)
        self.assertIn("reachability.orphan", codes)
        self.assertIn("budget.always_on_exceeded", codes)
        self.assertIn("budget.total_exceeded", codes)
        self.assertFalse(result["ok"])

    def test_audit_of_a_disabled_component(self) -> None:
        produced = self.write_json(
            "harness-disabled.json",
            {
                "schema": schemas.MANIFEST,
                "components": [
                    {"id": "agents", "kind": "system_prompt", "paths": ["AGENTS.md"]},
                    {
                        "id": "off",
                        "kind": "skills",
                        "paths": ["skills/*/SKILL.md"],
                        "enabled": False,
                    },
                ],
            },
        )
        result = manifest.audit(manifest.require_manifest(produced), produced)
        disabled = next(row for row in result["components"] if row["id"] == "off")
        self.assertFalse(disabled["enabled"])
        self.assertEqual(disabled["files"], [])


class ReceiptTests(unittest.TestCase):
    def test_findings_and_counts(self) -> None:
        item = receipts.finding("code", "warn", "component", "detail")
        self.assertEqual(item["severity"], "warn")
        self.assertEqual(
            receipts.count_severities([item, receipts.finding("c", "error", "x", "y")]),
            {"error": 1, "warn": 1, "info": 0},
        )

    def test_errors_carry_exit_codes(self) -> None:
        self.assertEqual(errors.OpenHarnessError("x").exit_code, errors.EXIT_USAGE)
        self.assertEqual(errors.DeclarationError("x").exit_code, errors.EXIT_USAGE)


class VerifyTests(HarnessCase):
    def test_every_contract_finding_is_reachable(self) -> None:
        entries = [
            {"iteration": "bad"},
            {
                "iteration": 1,
                "decision": "bogus",
                "scope": "bogus",
                "contrast": "bogus",
                "metric_before": 1,
                "metric_after": 2,
            },
            {
                "iteration": 1,
                "ts": "t",
                "front": "f",
                "hypothesis": "h",
                "decision": "adopted",
                "scope": "invariant",
                "cases": ["a"],
                "contrast": "unchanged",
                "metric_before": 1,
                "metric_after": 5,
                "harness_fingerprint": "a" * 64,
                "promote_global": True,
            },
            {
                "iteration": 2,
                "ts": "t",
                "front": "f",
                "hypothesis": "h",
                "decision": "preserved",
                "scope": "local",
                "contrast": "regressed",
                "metric_before": 5,
                "metric_after": 1,
            },
            {
                "iteration": 3,
                "ts": "t",
                "front": "f",
                "hypothesis": "h",
                "decision": "adopted",
                "scope": "local",
                "evidence_ref": "receipt.json",
                "rationale": "measured",
                "contrast": "mitigated",
                "promote_global": True,
            },
            {
                "iteration": 4,
                "ts": "t",
                "front": "f",
                "hypothesis": "h",
                "decision": "adopted",
                "contrast": "mitigated",
            },
        ]
        result = verify_command.verify(
            entries, direction="maximize", tolerance=0.0, fingerprint="b" * 64
        )
        codes = {item["code"] for item in result["findings"]}
        for expected in (
            "iteration.invalid",
            "iteration.duplicate",
            "entry.field_missing",
            "decision.invalid",
            "scope.invalid",
            "contrast.invalid",
            "scope.missing",
            "evidence.missing",
            "rationale.missing",
            "invariant.single_case",
            "scope.promotion",
            "contrast.unmeasured",
            "contrast.inconsistent",
            "fingerprint.stale",
            "preserve.justification",
        ):
            self.assertIn(expected, codes)
        self.assertFalse(result["ok"])

    def test_delta_verdict_and_minimize(self) -> None:
        self.assertIsNone(verify_command.delta_verdict("a", 1, "maximize", 0.0))
        self.assertEqual(verify_command.delta_verdict(10, 12, "maximize", 0.0), "mitigated")
        self.assertEqual(verify_command.delta_verdict(10, 8, "minimize", 0.0), "mitigated")
        self.assertEqual(verify_command.delta_verdict(10, 10, "maximize", 0.0), "unchanged")

    def test_bounded_drops_findings(self) -> None:
        payload = {
            "schema": schemas.VERIFY,
            "entries": 1,
            "counts": {},
            "ok": False,
            "findings": [{"detail": "x" * 400} for _ in range(20)],
        }
        text = verify_command.bounded(payload)
        self.assertLessEqual(jsonio.byte_size(text), 2500)
        self.assertTrue(json.loads(text)["truncated"])

    def test_run_reports_usage_for_a_missing_journal(self) -> None:
        code, output = capture(
            verify_command.run, parse(verify_command, ["--journal", self.path("absent.jsonl")])
        )
        self.assertEqual(code, errors.EXIT_USAGE)
        self.assertIn("cannot read journal", output)

    def test_run_clean_journal(self) -> None:
        code, output = capture(
            verify_command.run, parse(verify_command, ["--journal", self.path("journal.jsonl")])
        )
        self.assertEqual(code, errors.EXIT_OK)
        self.assertTrue(json.loads(output)["ok"])


class TelemetryTests(HarnessCase):
    def test_summary_separates_gain_from_regression(self) -> None:
        entries = [
            {"iteration": "bad"},
            {
                "iteration": 1,
                "decision": "adopted",
                "contrast": "mitigated",
                "evidence_ref": "receipt.json",
                "metric_before": 10,
                "metric_after": 14,
                "deficiency": "context-management",
                "cost": {"tokens_in": 100, "tokens_out": 50, "usd": 2, "retries": "x"},
            },
            {
                "iteration": 2,
                "decision": "unknown",
                "contrast": "unknown",
                "metric_before": 14,
                "metric_after": 10,
                "deficiency": "context-management",
            },
            {"iteration": 3, "decision": "rejected"},
        ]
        summary = telemetry_command.summarize(entries, direction="maximize")
        self.assertEqual(summary["invalid"], 1)
        self.assertEqual(summary["decisions"]["unclassified"], 1)
        self.assertEqual(summary["contrasts"]["unclassified"], 1)
        self.assertEqual(summary["gain_total"], 4)
        self.assertEqual(summary["regression_total"], -4)
        self.assertEqual(summary["evidence_coverage"], 1.0)
        self.assertIsNotNone(summary["cost_per_gain"])

    def test_summary_without_gain_has_no_cost_per_gain(self) -> None:
        summary = telemetry_command.summarize([{"iteration": 1, "decision": "rejected"}])
        self.assertIsNone(summary["cost_per_gain"])

    def test_bounded_and_run(self) -> None:
        payload = {
            "schema": schemas.TELEMETRY,
            "direction": "maximize",
            "iterations": 1,
            "decisions": {},
            "contrasts": {},
            "cost": {},
            "gain_total": 0,
            "padding": "x" * 3000,
        }
        self.assertTrue(json.loads(telemetry_command.bounded(payload))["truncated"])

        code, output = capture(
            telemetry_command.run,
            parse(telemetry_command, ["--journal", self.path("journal.jsonl")]),
        )
        self.assertEqual(code, errors.EXIT_OK)
        self.assertTrue(json.loads(output)["ok"])

        code, output = capture(
            telemetry_command.run,
            parse(telemetry_command, ["--journal", self.path("absent.jsonl")]),
        )
        self.assertEqual(code, errors.EXIT_USAGE)


class CasesTests(HarnessCase):
    def test_load_cases_accepts_both_shapes(self) -> None:
        bare = self.write_json("bare.json", [{"id": "a", "command": "python -c pass"}])
        self.assertEqual(len(cases_command.load_cases(bare)), 1)

        produced = self.write_json("bad-cases.json", {"cases": {}})
        with self.assertRaises(cases_command.CaseError):
            cases_command.load_cases(produced)

        produced = self.write_json("unknown-cases.json", {"unknown": 1, "cases": []})
        with self.assertRaises(cases_command.CaseError):
            cases_command.load_cases(produced)

        broken = self.write("broken-cases.json", "{")
        with self.assertRaises(cases_command.CaseError):
            cases_command.load_cases(broken)

    def test_validate_reports_every_problem(self) -> None:
        problems = cases_command.validate(
            [
                "not-an-object",
                {
                    "id": "",
                    "command": "",
                    "timeout_s": 0,
                    "budget_tokens": -1,
                    "expect": [],
                    "unknown": True,
                },
                {"id": "dup", "command": "python -c pass", "expect": {"bad": 1}},
                {"id": "dup", "command": "python -c pass", "expect": {"exit_code": "x"}},
            ]
        )
        codes = {item["code"] for item in problems}
        for expected in (
            "case.not_object",
            "case.unknown_field",
            "case.id_missing",
            "case.command_missing",
            "case.timeout_invalid",
            "case.budget_invalid",
            "case.expect_invalid",
            "case.expect_unknown",
            "case.id_duplicate",
        ):
            self.assertIn(expected, codes)

    def test_dry_run_only_and_bounded(self) -> None:
        code, output = capture(
            cases_command.run,
            parse(
                cases_command,
                ["--cases", self.path("cases.json"), "--dry-run", "--only", "one"],
            ),
        )
        self.assertEqual(code, errors.EXIT_OK)
        self.assertEqual(json.loads(output)["count"], 2)

        code, output = capture(
            cases_command.run,
            parse(
                cases_command, ["--cases", self.path("cases.json"), "--dry-run", "--only", "absent"]
            ),
        )
        self.assertEqual(code, errors.EXIT_OK)

        payload = {
            "schema": schemas.CASES_RECEIPT,
            "results": [{"id": "x", "status": "fail"}],
            "padding": "x" * 3000,
        }
        self.assertTrue(json.loads(cases_command.bounded(payload))["truncated"])

    def test_execution_paths(self) -> None:
        cases = [
            {"id": "pass", "command": 'python -c "print(1)"', "expect": {"exit_code": 0}},
            {
                "id": "fail",
                "command": 'python -c "raise SystemExit(1)"',
                "expect": {"exit_code": 0},
            },
            {
                "id": "text",
                "command": "python -c \"print('nope')\"",
                "expect": {"stdout_contains": "yes"},
            },
            {"id": "artifact", "command": "python -c pass", "expect": {"artifact": "absent.txt"}},
        ]
        produced = self.write_json("execute.json", {"schema": schemas.CASES, "cases": cases})
        receipt = cases_command.execute_cases(cases, self.root)
        self.assertEqual(receipt["passed"], 1)
        self.assertEqual(receipt["failed"], 3)
        self.assertFalse(receipt["ok"])

        code, _output = capture(
            cases_command.run,
            parse(
                cases_command,
                [
                    "--cases",
                    produced,
                    "--workdir",
                    str(self.root),
                    "--receipt",
                    self.path("receipt.json"),
                ],
            ),
        )
        self.assertEqual(code, errors.EXIT_FINDINGS)
        self.assertTrue((self.root / "receipt.json").is_file())

        code, _output = capture(
            cases_command.run,
            parse(
                cases_command,
                ["--cases", self.path("cases.json"), "--workdir", self.path("absent")],
            ),
        )
        self.assertEqual(code, errors.EXIT_USAGE)

        invalid = self.write_json("invalid-case.json", {"cases": [{"id": "x"}]})
        code, _output = capture(
            cases_command.run, parse(cases_command, ["--cases", invalid, "--dry-run"])
        )
        self.assertEqual(code, errors.EXIT_USAGE)


class SelectTests(HarnessCase):
    def test_creation_choice_and_unseal(self) -> None:
        argv = ["--candidates", self.path("candidates")]
        code, output = capture(select_command.run, parse(select_command, argv))
        self.assertEqual(code, errors.EXIT_OK)
        selection = json.loads(output)
        self.assertEqual(selection["count"], 2)
        self.assertEqual([item["id"] for item in selection["candidates"]], ["cand-a", "cand-b"])

        code, output = capture(
            select_command.run,
            parse(select_command, [*argv, "--choose", "cand-a", "--reason", "clearer"]),
        )
        self.assertEqual(code, errors.EXIT_FINDINGS)
        self.assertIn("probe receipt", output)

        code, output = capture(
            select_command.run,
            parse(
                select_command,
                [*argv, "--choose", "cand-a", "--reason", "clearer", "--allow-unprobed"],
            ),
        )
        self.assertEqual(code, errors.EXIT_OK)
        self.assertTrue(json.loads(output)["unproven"])

        code, output = capture(
            select_command.run,
            parse(select_command, [*argv, "--choose", "cand-z", "--reason", "x"]),
        )
        self.assertEqual(code, errors.EXIT_USAGE)

        code, output = capture(
            select_command.run, parse(select_command, [*argv, "--choose", "cand-a"])
        )
        self.assertEqual(code, errors.EXIT_USAGE)

        code, output = capture(select_command.run, parse(select_command, [*argv, "--unseal"]))
        self.assertEqual(code, errors.EXIT_OK)
        self.assertIn("alpha.txt", output)

    def test_missing_directory_and_empty_inputs(self) -> None:
        code, _output = capture(
            select_command.run,
            parse(select_command, ["--candidates", self.path("absent")]),
        )
        self.assertEqual(code, errors.EXIT_USAGE)

        empty = self.root / "empty"
        empty.mkdir()
        code, _output = capture(
            select_command.run, parse(select_command, ["--candidates", str(empty)])
        )
        self.assertEqual(code, errors.EXIT_USAGE)

        code, _output = capture(
            select_command.run,
            parse(select_command, ["--candidates", str(empty), "--unseal"]),
        )
        self.assertEqual(code, errors.EXIT_USAGE)

    def test_bounded_trims_long_selection(self) -> None:
        payload = {
            "schema": schemas.SELECTION,
            "candidates": [{"id": f"cand-{index}"} for index in range(30)],
            "count": 30,
            "chosen": None,
            "ok": True,
            "padding": "x" * 3000,
        }
        self.assertTrue(json.loads(select_command.bounded(payload))["truncated"])

    def test_discovery_skips_receipts(self) -> None:
        directory = self.root / "candidates"
        (directory / "alpha.txt.receipt.json").write_text("{}", encoding="utf-8")
        names = [path.name for path in select_command.discover(directory)]
        self.assertNotIn("alpha.txt.receipt.json", names)


class InventoryTests(HarnessCase):
    def test_build_and_gaps(self) -> None:
        requirements = [
            {"id": "entry", "kind": "system_prompt", "component": "agents"},
            {"id": "missing-component", "kind": "skills", "component": "absent", "required": False},
            {"id": "wrong-kind", "kind": "memory", "component": "agents", "required": False},
            {"id": "kind", "kind": "skills"},
            {"id": "optional", "kind": "memory", "required": False},
        ]
        payload = inventory_command.build(
            manifest.require_manifest(self.root / "harness.json"),
            self.root / "harness.json",
            requirements,
        )
        reasons = {gap["id"]: gap["reason"] for gap in payload["gaps"]}
        self.assertIn("is not declared", reasons["missing-component"])
        self.assertIn("not memory", reasons["wrong-kind"])
        self.assertIn("no enabled component", reasons["optional"])
        self.assertTrue(payload["ok"])
        self.assertIn("memory", payload["kinds_missing"])

        blocking = inventory_command.build(
            manifest.require_manifest(self.root / "harness.json"),
            self.root / "harness.json",
            [{"id": "memory", "kind": "memory"}],
        )
        self.assertFalse(blocking["ok"])

    def test_disabled_component_gap(self) -> None:
        produced = self.write_json(
            "disabled.json",
            {
                "schema": schemas.MANIFEST,
                "components": [
                    {"id": "agents", "kind": "system_prompt", "paths": ["AGENTS.md"]},
                    {
                        "id": "off",
                        "kind": "skills",
                        "paths": ["skills/*/SKILL.md"],
                        "enabled": False,
                    },
                ],
            },
        )
        payload = inventory_command.build(
            manifest.require_manifest(produced),
            produced,
            [{"id": "s", "kind": "skills", "component": "off"}],
        )
        self.assertIn("is disabled", payload["gaps"][0]["reason"])

    def test_requirements_validation(self) -> None:
        invalid_documents = {
            "not-object": [],
            "unknown": {"unknown": 1, "requirements": []},
            "not-list": {"requirements": {}},
            "not-object-item": {"requirements": [1]},
            "missing-id": {"requirements": [{"kind": "skills"}]},
            "duplicate": {
                "requirements": [
                    {"id": "a", "kind": "skills"},
                    {"id": "a", "kind": "skills"},
                ]
            },
            "bad-kind": {"requirements": [{"id": "a", "kind": "nope"}]},
            "unknown-field": {"requirements": [{"id": "a", "kind": "skills", "x": 1}]},
            "bad-flags": {"requirements": [{"id": "a", "kind": "skills", "required": "yes"}]},
        }
        for label, payload in invalid_documents.items():
            with self.subTest(case=label):
                produced = self.write_json(f"req-{label}.json", payload)
                with self.assertRaises(inventory_command.InventoryError):
                    inventory_command.load_requirements(produced)

        broken = self.write("req-broken.json", "{")
        with self.assertRaises(inventory_command.InventoryError):
            inventory_command.load_requirements(broken)
        with self.assertRaises(inventory_command.InventoryError):
            inventory_command.load_requirements(self.root / "absent.json")

    def test_bounded_and_run(self) -> None:
        payload = {
            "schema": schemas.INVENTORY,
            "gaps": [{"id": str(index)} for index in range(20)],
            "components": {},
            "padding": "x" * 3000,
        }
        self.assertTrue(json.loads(inventory_command.bounded(payload))["truncated"])

        code, _output = capture(
            inventory_command.run,
            parse(
                inventory_command,
                [
                    "--manifest",
                    self.path("harness.json"),
                    "--requirements",
                    self.path("requirements.json"),
                ],
            ),
        )
        self.assertEqual(code, errors.EXIT_OK)

        code, _output = capture(
            inventory_command.run,
            parse(
                inventory_command,
                [
                    "--manifest",
                    self.path("harness-broken.json"),
                    "--requirements",
                    self.path("requirements.json"),
                ],
            ),
        )
        self.assertEqual(code, errors.EXIT_FINDINGS)

        bad = self.write_json("bad-req.json", {"requirements": [1]})
        code, _output = capture(
            inventory_command.run,
            parse(
                inventory_command,
                ["--manifest", self.path("harness.json"), "--requirements", bad],
            ),
        )
        self.assertEqual(code, errors.EXIT_USAGE)

        code, _output = capture(
            inventory_command.run,
            parse(inventory_command, ["--manifest", self.path("absent.json")]),
        )
        self.assertEqual(code, errors.EXIT_USAGE)


class FailuresTests(HarnessCase):
    def test_classification_and_recurrence(self) -> None:
        entries = [
            {"iteration": 1, "failure": "bad"},
            {"iteration": 2, "failure": {"class": "unknown"}},
            {"iteration": 3, "failure": {"class": "unclassified"}},
            {"iteration": 4, "failure": {"class": "wrong-premise", "detail": "x"}},
            {"iteration": 5, "failure": {"class": "wrong-premise", "detail": "y"}},
        ]
        payload = failures_command.classify(entries, recurrence=2)
        codes = {item["code"] for item in payload["findings"]}
        self.assertIn("failure.invalid", codes)
        self.assertIn("failure.unclassified", codes)
        self.assertIn("failure.undiagnosed", codes)
        self.assertIn("failure.recurring", codes)
        self.assertFalse(payload["ok"])

    def test_bounded_and_run(self) -> None:
        payload = {
            "schema": schemas.FAILURES,
            "iterations": 1,
            "failures": [],
            "rate": 0.0,
            "classes": {},
            "repeated": [],
            "counts": {},
            "ok": True,
        }
        self.assertEqual(failures_command.bounded(payload), jsonio.compact(payload))

        code, _output = capture(
            failures_command.run,
            parse(failures_command, ["--journal", self.path("journal.jsonl")]),
        )
        self.assertEqual(code, errors.EXIT_OK)

        code, _output = capture(
            failures_command.run,
            parse(failures_command, ["--journal", self.path("journal.jsonl"), "--recurrence", "1"]),
        )
        self.assertEqual(code, errors.EXIT_USAGE)

        code, _output = capture(
            failures_command.run,
            parse(failures_command, ["--journal", self.path("absent.jsonl")]),
        )
        self.assertEqual(code, errors.EXIT_USAGE)


class PolicyTests(HarnessCase):
    def test_evaluation_and_matching(self) -> None:
        policy = policy_command.load_policy(self.root / "policy.json")
        allow = policy_command.evaluate(
            policy, {"tool": "shell", "command": "python -B -m unittest"}
        )
        self.assertEqual((allow["verdict"], allow["ok"]), ("allow", True))
        deny = policy_command.evaluate(policy, {"tool": "shell", "command": "rm -rf build"})
        self.assertEqual((deny["verdict"], deny["ok"]), ("deny", False))
        ask = policy_command.evaluate(policy, {"tool": "shell", "command": "ls"})
        self.assertEqual(ask["verdict"], "ask")
        self.assertEqual(ask["rule"], None)

        self.assertFalse(policy_command.matches(policy["rules"][0], {}))
        self.assertFalse(policy_command.matches(policy["rules"][0], {"tool": "edit"}))
        path_rule = {
            "match": {"path_glob": "src/*.py"},
            "pattern": None,
        }
        self.assertFalse(policy_command.matches(path_rule, {}))
        self.assertTrue(policy_command.matches(path_rule, {"path": "src\\app.py"}))
        self.assertFalse(policy_command.matches(path_rule, {"path": "lib/app.py"}))

    def test_policy_validation(self) -> None:
        valid_rule = {
            "id": "r",
            "match": {"tool": "shell"},
            "verdict": "allow",
        }
        invalid_documents = {
            "not-object": [],
            "wrong-schema": {"schema": "x", "rules": []},
            "unknown": {"schema": schemas.POLICY, "rules": [], "x": 1},
            "bad-default": {"schema": schemas.POLICY, "default": "nope", "rules": []},
            "not-list": {"schema": schemas.POLICY, "rules": {}},
            "rule-not-object": {"schema": schemas.POLICY, "rules": [1]},
            "missing-id": {
                "schema": schemas.POLICY,
                "rules": [{"match": {"tool": "x"}, "verdict": "allow"}],
            },
            "duplicate": {"schema": schemas.POLICY, "rules": [valid_rule, valid_rule]},
            "unknown-field": {
                "schema": schemas.POLICY,
                "rules": [dict(valid_rule, x=1)],
            },
            "bad-verdict": {
                "schema": schemas.POLICY,
                "rules": [dict(valid_rule, verdict="nope")],
            },
            "bad-match": {"schema": schemas.POLICY, "rules": [dict(valid_rule, match={})]},
            "unknown-match": {
                "schema": schemas.POLICY,
                "rules": [dict(valid_rule, match={"x": "y"})],
            },
            "empty-value": {
                "schema": schemas.POLICY,
                "rules": [dict(valid_rule, match={"tool": " "})],
            },
            "bad-regex": {
                "schema": schemas.POLICY,
                "rules": [dict(valid_rule, match={"command_regex": "("})],
            },
        }
        for label, payload in invalid_documents.items():
            with self.subTest(case=label):
                produced = self.write_json(f"policy-{label}.json", payload)
                with self.assertRaises(policy_command.PolicyError):
                    policy_command.load_policy(produced)

        broken = self.write("policy-broken.json", "{")
        with self.assertRaises(policy_command.PolicyError):
            policy_command.load_policy(broken)
        with self.assertRaises(policy_command.PolicyError):
            policy_command.load_policy(self.root / "absent.json")

    def test_bounded_and_run_exit_codes(self) -> None:
        payload = {
            "schema": schemas.POLICY,
            "matched": [str(index) for index in range(20)],
            "verdict": "allow",
            "ok": True,
            "padding": "x" * 3000,
        }
        self.assertTrue(json.loads(policy_command.bounded(payload))["truncated"])

        argv = ["--policy", self.path("policy.json"), "--tool", "shell", "--command", "python -B x"]
        code, _output = capture(policy_command.run, parse(policy_command, argv))
        self.assertEqual(code, errors.EXIT_OK)

        code, _output = capture(
            policy_command.run,
            parse(
                policy_command,
                [
                    "--policy",
                    self.path("policy.json"),
                    "--tool",
                    "shell",
                    "--command",
                    "rm -rf x",
                ],
            ),
        )
        self.assertEqual(code, errors.EXIT_FINDINGS)

        code, _output = capture(
            policy_command.run,
            parse(policy_command, ["--policy", self.path("policy.json")]),
        )
        self.assertEqual(code, errors.EXIT_USAGE)

        code, _output = capture(
            policy_command.run,
            parse(policy_command, ["--policy", self.path("absent.json"), "--tool", "shell"]),
        )
        self.assertEqual(code, errors.EXIT_USAGE)


class LockAndPlanTests(HarnessCase):
    def lock(self, *extra: str) -> tuple[int, str]:
        return capture(
            lock_command.run,
            parse(
                lock_command,
                [
                    "--manifest",
                    self.path("harness.json"),
                    "--output",
                    self.path("harness.lock"),
                    *extra,
                ],
            ),
        )

    def plan(self, *extra: str) -> tuple[int, str]:
        return capture(
            plan_command.run,
            parse(
                plan_command,
                [
                    "--manifest",
                    self.path("harness.json"),
                    "--lock",
                    self.path("harness.lock"),
                    *extra,
                ],
            ),
        )

    def test_lock_write_check_and_drift(self) -> None:
        code, output = self.lock()
        self.assertEqual(code, errors.EXIT_OK)
        self.assertTrue(json.loads(output)["written"])
        first = (self.root / "harness.lock").read_text(encoding="utf-8")
        self.assertEqual(self.lock()[0], errors.EXIT_OK)
        self.assertEqual((self.root / "harness.lock").read_text(encoding="utf-8"), first)

        code, output = self.lock("--check")
        self.assertEqual(code, errors.EXIT_OK)
        self.assertTrue(json.loads(output)["match"])

        self.write("AGENTS.md", "changed\n")
        code, output = self.lock("--check")
        self.assertEqual(code, errors.EXIT_FINDINGS)
        payload = json.loads(output)
        self.assertFalse(payload["match"])
        self.assertEqual(payload["changes"][0]["change"], "modified")
        self.assertIn("agents", payload["component_ids"])

        code, output = self.lock("--policy", self.path("policy.json"))
        self.assertEqual(code, errors.EXIT_OK)
        lock = json.loads((self.root / "harness.lock").read_text(encoding="utf-8"))
        self.assertIn("policy", lock["declarations"])

        code, output = capture(
            lock_command.run,
            parse(lock_command, ["--manifest", self.path("absent.json")]),
        )
        self.assertEqual(code, errors.EXIT_USAGE)

        broken = self.write("broken.lock", '{"schema": "other"}')
        code, output = capture(
            lock_command.run,
            parse(
                lock_command,
                ["--manifest", self.path("harness.json"), "--output", broken, "--check"],
            ),
        )
        self.assertEqual(code, errors.EXIT_USAGE)

    def test_plan_text_json_and_check(self) -> None:
        self.lock()
        code, output = self.plan()
        self.assertEqual(code, errors.EXIT_OK)
        self.assertIn("no drift", output)

        self.write("AGENTS.md", "changed\n")
        code, output = self.plan()
        self.assertEqual(code, errors.EXIT_OK)
        self.assertIn("~ AGENTS.md (agents)", output)

        code, output = self.plan("--check")
        self.assertEqual(code, errors.EXIT_FINDINGS)

        code, output = self.plan("--format", "json")
        self.assertEqual(code, errors.EXIT_OK)
        payload = json.loads(output)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["summary"]["modified"], 1)

        payload["changes"] = [{"detail": "x" * 400} for _ in range(30)]
        self.assertTrue(plan_command._shrink(payload)["truncated"])

    def test_plan_reports_usage_without_a_lock(self) -> None:
        code, output = self.plan("--check")
        self.assertEqual(code, errors.EXIT_USAGE)
        self.assertIn("cannot read lock", output)

    def test_plan_formats_component_changes(self) -> None:
        self.lock()
        state = {"fingerprint_before": "a", "fingerprint_after": "b"}
        text = plan_command.format_text(
            "fixture",
            "harness.lock",
            state,
            [
                {"change": "component-added", "component": "new", "path": None, "tokens_after": 5},
                {
                    "change": "component-removed",
                    "component": "old",
                    "path": None,
                    "tokens_before": 5,
                },
                {
                    "change": "removed",
                    "component": "agents",
                    "path": "AGENTS.md",
                    "tokens_before": 5,
                },
                {
                    "change": "declaration",
                    "component": None,
                    "path": "policy.json",
                    "declaration": "policy",
                },
                {"change": "odd", "component": "x", "path": "y"},
            ],
        )
        self.assertIn("+ component new", text)
        self.assertIn("- component old", text)
        self.assertIn("- AGENTS.md", text)
        self.assertIn("declaration: policy", text)
        self.assertIn("? y", text)

    def test_drift_compare_component_level(self) -> None:
        locked = {
            "fingerprint": "a",
            "components": [
                {
                    "id": "kept",
                    "tokens": 1,
                    "files": [{"path": "a.md", "sha256": "1", "tokens": 1}],
                },
                {"id": "gone", "tokens": 1, "files": []},
            ],
            "declarations": {"policy": {"path": "policy.json", "sha256": "1"}},
        }
        actual = {
            "fingerprint": "b",
            "components": [
                {
                    "id": "kept",
                    "tokens": 2,
                    "files": [{"path": "a.md", "sha256": "2", "tokens": 2}],
                },
                {"id": "new", "tokens": 3, "files": []},
            ],
            "declarations": {"cases": {"path": "cases.json", "sha256": "2"}},
        }
        changes = drift.compare(locked, actual)
        kinds = {(item["change"], item["component"]) for item in changes}
        self.assertIn(("component-added", "new"), kinds)
        self.assertIn(("component-removed", "gone"), kinds)
        self.assertIn(("modified", "kept"), kinds)
        self.assertIn(("declaration", None), kinds)
        summary = drift.summarize(locked, actual, changes)
        self.assertTrue(summary["drift"])
        self.assertEqual(drift.token_delta(changes[0]), -1)

    def test_drift_compare_add_and_remove_files(self) -> None:
        locked = {
            "fingerprint": "a",
            "components": [
                {"id": "c", "tokens": 1, "files": [{"path": "gone.md", "sha256": "1", "tokens": 1}]}
            ],
            "declarations": {},
        }
        actual = {
            "fingerprint": "b",
            "components": [
                {"id": "c", "tokens": 2, "files": [{"path": "new.md", "sha256": "2", "tokens": 2}]}
            ],
            "declarations": {},
        }
        kinds = {item["change"] for item in drift.compare(locked, actual)}
        self.assertEqual(kinds, {"added", "removed"})

    def test_drift_helpers(self) -> None:
        document = manifest.require_manifest(self.root / "harness.json")
        lock = drift.build_lock(document, self.root / "harness.json")
        self.assertEqual(lock["schema"], schemas.LOCK)
        receipt = manifest.audit(document, self.root / "harness.json")
        self.assertEqual(len(drift.component_records(receipt)), 2)
        declarations = drift.declaration_records(self.root / "harness.json")
        self.assertEqual(set(declarations), {"policy", "cases", "requirements"})
        with self.assertRaises(errors.DeclarationError):
            drift.load_lock(self.write("bad.lock", "[]"))
        with self.assertRaises(errors.DeclarationError):
            drift.load_lock(self.write("wrong.lock", '{"schema": "other"}'))
        with self.assertRaises(errors.DeclarationError):
            drift.load_lock(self.write("empty.lock", f'{{"schema": "{schemas.LOCK}"}}'))


class InitTests(HarnessCase):
    def test_discovers_the_full_surface(self) -> None:
        for name in (
            "README.md",
            ".cursor/rules/style.mdc",
            ".github/instructions/x.instructions.md",
            ".opencode/commands/run.md",
            ".opencode/agents/reviewer.md",
            "scripts/tool.py",
            "tools/mcp_server.py",
            "MEMORY.md",
        ):
            self.write(name, "text\n")
        self.write("skills/build/SKILL.md", "---\nname: build\n---\nBody\n")
        components = init_command.discover(self.root)
        ids = {item["id"] for item in components}
        self.assertTrue(
            {
                "agents",
                "readme",
                "rules",
                "commands",
                "subagents",
                "scripts",
                "plugins",
                "guardrails",
                "memory",
            }
            <= ids
        )
        agents = next(item for item in components if item["id"] == "agents")
        self.assertTrue(agents["always_on"])

    def test_run_writes_then_refuses(self) -> None:
        code, output = capture(
            init_command.run,
            parse(
                init_command,
                [
                    "--root",
                    str(self.root),
                    "--name",
                    "fresh",
                    "--manifest",
                    "generated.json",
                    "--lock",
                    "generated.lock",
                ],
            ),
        )
        self.assertEqual(code, errors.EXIT_OK, output)
        self.assertTrue((self.root / "generated.json").is_file())
        self.assertTrue((self.root / "generated.lock").is_file())

        code, output = capture(
            init_command.run,
            parse(init_command, ["--root", str(self.root), "--manifest", "generated.json"]),
        )
        self.assertEqual(code, errors.EXIT_FINDINGS)

        payload = {"schema": schemas.INIT, "components": [{"id": "x" * 200}] * 20}
        self.assertTrue(init_command._shrink(payload)["truncated"])

    def test_run_on_an_empty_and_absent_root(self) -> None:
        empty = Path(self.temporary.name) / "empty"
        empty.mkdir()
        code, output = capture(init_command.run, parse(init_command, ["--root", str(empty)]))
        self.assertEqual(code, errors.EXIT_FINDINGS)
        self.assertIn("no agent harness surface", output)

        code, output = capture(
            init_command.run,
            parse(init_command, ["--root", str(empty / "absent")]),
        )
        self.assertEqual(code, errors.EXIT_USAGE)


class ReportTests(HarnessCase):
    def report(self, *extra: str) -> tuple[int, str]:
        return capture(
            report_command.run,
            parse(
                report_command,
                [
                    "--manifest",
                    self.path("harness.json"),
                    "--lock",
                    self.path("harness.lock"),
                    *extra,
                ],
            ),
        )

    def test_every_format_renders(self) -> None:
        self.lock()
        for fmt, name in (
            ("json", "report.json"),
            ("markdown", "report.md"),
            ("sarif", "report.sarif"),
            ("junit", "report.xml"),
        ):
            with self.subTest(format=fmt):
                code, output = self.report(
                    "--requirements",
                    self.path("requirements.json"),
                    "--format",
                    fmt,
                    "--output",
                    self.path(name),
                )
                self.assertEqual(code, errors.EXIT_OK, output)
                text = (self.root / name).read_text(encoding="utf-8")
                self.assertTrue(text)
                self.assertTrue(json.loads(output)["ok"])

    def test_report_composes_cases_journal_and_findings(self) -> None:
        self.lock()
        code, output = self.report(
            "--requirements",
            self.path("requirements.json"),
            "--cases",
            self.path("cases.json"),
            "--journal",
            self.path("journal.jsonl"),
            "--execute",
            "--format",
            "json",
            "--output",
            self.path("report.json"),
        )
        self.assertEqual(code, errors.EXIT_OK, output)
        document = json.loads((self.root / "report.json").read_text(encoding="utf-8"))
        self.assertEqual(document["cases"]["passed"], 2)
        self.assertEqual(document["telemetry"]["iterations"], 3)
        self.assertTrue(document["lock"]["match"])

        code, output = self.report(
            "--manifest",
            self.path("harness-broken.json"),
            "--format",
            "markdown",
            "--output",
            self.path("broken.md"),
        )
        self.assertEqual(code, errors.EXIT_FINDINGS)
        self.assertIn("# Harness report", (self.root / "broken.md").read_text(encoding="utf-8"))

    def test_report_rejects_unusable_inputs(self) -> None:
        code, _output = capture(
            report_command.run,
            parse(report_command, ["--manifest", self.path("absent.json")]),
        )
        self.assertEqual(code, errors.EXIT_USAGE)

        self.lock()
        bad_cases = self.write_json("bad-cases.json", {"cases": [{"id": "x"}]})
        code, _output = self.report("--cases", bad_cases)
        self.assertEqual(code, errors.EXIT_USAGE)

        code, _output = self.report("--journal", self.path("absent.jsonl"))
        self.assertEqual(code, errors.EXIT_USAGE)

        bad_requirements = self.write_json("bad-req.json", {"requirements": [1]})
        code, _output = self.report("--requirements", bad_requirements)
        self.assertEqual(code, errors.EXIT_USAGE)

        payload = {
            "schema": schemas.REPORT,
            "changes": list(range(20)),
            "findings": list(range(20)),
        }
        self.assertTrue(report_command._shrink(payload)["truncated"])

    def test_sarif_and_junit_include_inventory_gaps(self) -> None:
        self.lock()
        self.report(
            "--requirements",
            self.path("requirements.json"),
            "--format",
            "sarif",
            "--output",
            self.path("report.sarif"),
        )
        sarif = json.loads((self.root / "report.sarif").read_text(encoding="utf-8"))
        self.assertEqual(sarif["runs"][0]["tool"]["driver"]["name"], "openharness")

        self.write_json(
            "requirements-blocking.json",
            {"schema": schemas.REQUIREMENTS, "requirements": [{"id": "m", "kind": "memory"}]},
        )
        code, _output = self.report(
            "--requirements",
            self.path("requirements-blocking.json"),
            "--format",
            "junit",
            "--output",
            self.path("blocking.xml"),
        )
        self.assertEqual(code, errors.EXIT_FINDINGS)
        self.assertIn(
            "openharness.inventory", (self.root / "blocking.xml").read_text(encoding="utf-8")
        )


class CommandLineTests(unittest.TestCase):
    def test_parser_lists_every_command(self) -> None:
        parser = cli.build_parser()
        actions = [
            action for action in parser._actions if isinstance(action, argparse._SubParsersAction)
        ]
        names = set(actions[0].choices)
        self.assertEqual(
            names,
            {
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
            },
        )

    def test_main_without_a_command_is_a_usage_error(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()) as stream:
            code = cli.main([])
        self.assertEqual(code, errors.EXIT_USAGE)
        self.assertIn("usage:", stream.getvalue())

    def test_version_and_unknown_command_exit_through_argparse(self) -> None:
        with (
            contextlib.redirect_stdout(io.StringIO()) as stream,
            self.assertRaises(SystemExit) as caught,
        ):
            cli.main(["--version"])
        self.assertEqual(caught.exception.code, 0)
        self.assertIn("openharness", stream.getvalue())

        with (
            contextlib.redirect_stderr(io.StringIO()),
            self.assertRaises(SystemExit) as caught,
        ):
            cli.main(["nope"])
        self.assertEqual(caught.exception.code, 2)

    def test_dispatch_reaches_a_command(self) -> None:
        with tempfile.TemporaryDirectory():
            code, output = capture(
                cli.main,
                [
                    "audit",
                    "--manifest",
                    str(FIXTURE / "harness.json"),
                    "--fingerprint-only",
                ],
            )
            self.assertEqual(code, errors.EXIT_OK)
            self.assertIn("fingerprint", output)


class AuditCommandTests(HarnessCase):
    def test_serialize_truncates_oversized_receipts(self) -> None:
        receipt = {
            "schema": schemas.RECEIPT,
            "manifest": "fixture",
            "fingerprint": "f" * 64,
            "totals": {"components": 1, "files": 1, "always_on_tokens": 1, "total_tokens": 1},
            "counts": {"error": 0, "warn": 0, "info": 0},
            "findings": [{"detail": "x" * 300} for _ in range(20)],
            "truncated": False,
            "dropped_findings": 0,
            "ok": False,
        }
        text = audit_command.serialize(receipt)
        self.assertLessEqual(jsonio.byte_size(text), 2500)
        self.assertTrue(json.loads(text)["truncated"])

    def test_run_paths(self) -> None:
        code, output = capture(
            audit_command.run, parse(audit_command, ["--manifest", self.path("harness.json")])
        )
        self.assertEqual(code, errors.EXIT_OK)
        self.assertTrue(json.loads(output)["ok"])

        code, output = capture(
            audit_command.run,
            parse(audit_command, ["--manifest", self.path("harness-broken.json")]),
        )
        self.assertEqual(code, errors.EXIT_FINDINGS)

        code, output = capture(
            audit_command.run, parse(audit_command, ["--manifest", self.path("absent.json")])
        )
        self.assertEqual(code, errors.EXIT_USAGE)


if __name__ == "__main__":
    unittest.main()

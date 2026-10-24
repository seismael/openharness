"""Run declared evaluation cases against a harness state (RFC-0012)."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path
from typing import Any

from .. import jsonio
from ..errors import EXIT_FINDINGS, EXIT_OK, EXIT_USAGE, OpenHarnessError
from ..schemas import CASES, CASES_RECEIPT

HELP = "run declared evaluation cases"
DESCRIPTION = "Run declared evaluation cases."

CONTRACT = CASES
RECEIPT_SCHEMA = CASES_RECEIPT
DEFAULT_TIMEOUT = 120
MAX_TIMEOUT = 3600
EXPECT_KEYS = {"exit_code", "stdout_contains", "artifact"}
CASE_KEYS = {"id", "description", "command", "expect", "timeout_s", "budget_tokens"}
SUMMARY_KEYS = {"schema", "cases"}


class CaseError(OpenHarnessError):
    """A declaration problem that prevents execution."""


def bounded(payload: dict[str, Any]) -> str:
    """Keep the verdict inside 2500 bytes; detail is droppable, totals are not."""
    return jsonio.bounded(payload, (_drop_results,))


def _drop_results(payload: dict[str, Any]) -> dict[str, Any]:
    trimmed = dict(payload)
    results = trimmed.pop("results", None)
    if results is not None:
        trimmed["failed_ids"] = [item["id"] for item in results if item.get("status") != "pass"][
            :12
        ]
        trimmed["truncated"] = True
    return trimmed


def load_cases(path: str | Path) -> list[Any]:
    """Accept a bare array or a document with a ``cases`` array."""
    try:
        raw = Path(path).read_text(encoding="utf-8-sig")
    except OSError as error:
        raise CaseError(f"cannot read cases: {error}") from error
    try:
        document = json.loads(raw)
    except json.JSONDecodeError as error:
        raise CaseError(f"cases are not valid JSON: {error}") from error
    if isinstance(document, list):
        return document
    if not isinstance(document, dict):
        raise CaseError("cases must be an array or an object with a cases array")
    unknown = sorted(set(document) - SUMMARY_KEYS)
    if unknown:
        raise CaseError(f"unknown document keys: {', '.join(unknown)}")
    cases = document.get("cases")
    if not isinstance(cases, list):
        raise CaseError("document key 'cases' must be an array")
    return cases


def validate_case(case: Any, index: int) -> list[dict[str, Any]]:
    """Return a list of declaration errors for one case."""
    problems: list[dict[str, Any]] = []
    if not isinstance(case, dict):
        return [{"code": "case.not_object", "case": index, "detail": "must be an object"}]
    label = case.get("id") if isinstance(case.get("id"), str) else f"#{index + 1}"
    unknown = sorted(set(case) - CASE_KEYS)
    if unknown:
        problems.append({"code": "case.unknown_field", "case": label, "detail": ", ".join(unknown)})
    identifier = case.get("id")
    if not isinstance(identifier, str) or not identifier.strip():
        problems.append(
            {
                "code": "case.id_missing",
                "case": label,
                "detail": "id must be a non-empty string",
            }
        )
    command = case.get("command")
    if not isinstance(command, str) or not command.strip():
        problems.append(
            {
                "code": "case.command_missing",
                "case": label,
                "detail": "command is required",
            }
        )
    timeout = case.get("timeout_s", DEFAULT_TIMEOUT)
    if isinstance(timeout, bool) or not isinstance(timeout, int) or not 1 <= timeout <= MAX_TIMEOUT:
        problems.append(
            {
                "code": "case.timeout_invalid",
                "case": label,
                "detail": f"timeout_s must be an integer in 1..{MAX_TIMEOUT}",
            }
        )
    budget = case.get("budget_tokens")
    if budget is not None and (
        isinstance(budget, bool) or not isinstance(budget, int) or budget < 0
    ):
        problems.append(
            {
                "code": "case.budget_invalid",
                "case": label,
                "detail": "budget_tokens must be a non-negative integer",
            }
        )
    expect = case.get("expect", {})
    if not isinstance(expect, dict):
        problems.append(
            {
                "code": "case.expect_invalid",
                "case": label,
                "detail": "expect must be an object",
            }
        )
    else:
        unknown_expect = sorted(set(expect) - EXPECT_KEYS)
        if unknown_expect:
            problems.append(
                {
                    "code": "case.expect_unknown",
                    "case": label,
                    "detail": ", ".join(unknown_expect),
                }
            )
        code = expect.get("exit_code")
        if code is not None and (isinstance(code, bool) or not isinstance(code, int)):
            problems.append(
                {
                    "code": "case.expect_invalid",
                    "case": label,
                    "detail": "exit_code must be an integer",
                }
            )
    return problems


def validate(cases: list[Any]) -> list[dict[str, Any]]:
    problems: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, case in enumerate(cases):
        problems.extend(validate_case(case, index))
        if isinstance(case, dict) and isinstance(case.get("id"), str):
            identifier = case["id"]
            if identifier in seen:
                problems.append(
                    {
                        "code": "case.id_duplicate",
                        "case": identifier,
                        "detail": "id already used",
                    }
                )
            seen.add(identifier)
    return problems


def evaluate(case: dict[str, Any], workdir: Path) -> dict[str, Any]:
    """Execute one case and return its result record."""
    identifier = case["id"]
    command = case["command"]
    timeout = case.get("timeout_s", DEFAULT_TIMEOUT)
    expect = case.get("expect", {})
    started = time.perf_counter()
    record: dict[str, Any] = {"id": identifier, "status": "fail", "detail": ""}
    try:
        completed = subprocess.run(
            command,
            shell=True,
            cwd=str(workdir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        record["status"] = "timeout"
        record["detail"] = f"exceeded {timeout}s"
        record["ms"] = int((time.perf_counter() - started) * 1000)
        return record
    except OSError as error:
        record["status"] = "error"
        record["detail"] = f"cannot execute: {error}"
        record["ms"] = int((time.perf_counter() - started) * 1000)
        return record

    record["ms"] = int((time.perf_counter() - started) * 1000)
    record["exit_code"] = completed.returncode
    output = (completed.stdout or "") + (completed.stderr or "")
    if "exit_code" in expect and completed.returncode != expect["exit_code"]:
        record["detail"] = f"exit {completed.returncode}, expected {expect['exit_code']}"
        return record
    needle = expect.get("stdout_contains")
    if isinstance(needle, str) and needle not in output:
        record["detail"] = "expected output text not found"
        return record
    artifact = expect.get("artifact")
    if isinstance(artifact, str) and not (Path(workdir) / artifact).exists():
        record["detail"] = f"artifact missing: {artifact}"
        return record
    record["status"] = "pass"
    return record


def select_cases(cases: list[dict[str, Any]], only: str | None = None) -> list[dict[str, Any]]:
    """Apply ``--only``, refusing unknown ids so a typo cannot silently skip a case."""
    if not only:
        return cases
    wanted = [item.strip() for item in only.split(",") if item.strip()]
    known = {case["id"] for case in cases}
    missing = [item for item in wanted if item not in known]
    if missing:
        raise CaseError(f"unknown case ids: {', '.join(missing)}")
    chosen = set(wanted)
    return [case for case in cases if case["id"] in chosen]


def execute_cases(
    cases: list[dict[str, Any]],
    workdir: Path,
    only: str | None = None,
    fingerprint: str = "",
) -> dict[str, Any]:
    selected = select_cases(cases, only)
    results = [evaluate(case, workdir) for case in selected]
    passed = sum(1 for item in results if item["status"] == "pass")
    receipt: dict[str, Any] = {
        "schema": RECEIPT_SCHEMA,
        "mode": "executed",
        "cases": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
        "truncated": False,
        "ok": passed == len(results),
    }
    budget = sum(
        case.get("budget_tokens", 0) or 0
        for case in selected
        if isinstance(case.get("budget_tokens"), int)
    )
    if budget:
        receipt["declared_budget_tokens"] = budget
    if fingerprint:
        receipt["harness_fingerprint"] = fingerprint
    return receipt


def configure(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--cases", required=True, help="Path to a JSON case declaration")
    parser.add_argument(
        "--workdir", default=".", help="Directory commands run in (default: current)"
    )
    parser.add_argument("--only", help="Comma-separated case ids to run")
    parser.add_argument(
        "--dry-run", action="store_true", help="Validate declarations without executing"
    )
    parser.add_argument("--receipt", help="Write the receipt to this path")
    parser.add_argument(
        "--fingerprint",
        default="",
        help="Harness state fingerprint to stamp on the receipt",
    )


def run(args: argparse.Namespace) -> int:
    try:
        cases = load_cases(args.cases)
    except CaseError as error:
        print(jsonio.spaced({"schema": CONTRACT, "ok": False, "error": str(error)}))
        return EXIT_USAGE

    problems = validate(cases)
    if problems:
        payload = {
            "schema": CONTRACT,
            "ok": False,
            "problems": problems[:12],
            "counts": {"error": len(problems)},
        }
        print(jsonio.compact(payload))
        return EXIT_USAGE

    if args.dry_run:
        try:
            selected = select_cases(cases, args.only)
        except CaseError as error:
            print(jsonio.spaced({"schema": CONTRACT, "ok": False, "error": str(error)}))
            return EXIT_USAGE
        payload = {
            "schema": CONTRACT,
            "mode": "dry-run",
            "cases": [
                {
                    "id": case["id"],
                    "command": case["command"],
                    "timeout_s": case.get("timeout_s", DEFAULT_TIMEOUT),
                }
                for case in selected
            ],
            "count": len(selected),
            "ok": True,
        }
        print(bounded(payload))
        return EXIT_OK

    workdir = Path(args.workdir)
    if not workdir.is_dir():
        print(
            jsonio.spaced(
                {
                    "schema": CONTRACT,
                    "ok": False,
                    "error": f"not a directory: {workdir}",
                }
            )
        )
        return EXIT_USAGE

    try:
        receipt = execute_cases(cases, workdir, only=args.only, fingerprint=args.fingerprint)
    except CaseError as error:
        print(jsonio.spaced({"schema": CONTRACT, "ok": False, "error": str(error)}))
        return EXIT_USAGE

    text = bounded(receipt)
    if args.receipt:
        Path(args.receipt).write_text(text + "\n", encoding="utf-8", newline="\n")
    print(text)
    return EXIT_OK if receipt["ok"] else EXIT_FINDINGS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    configure(parser)
    return run(parser.parse_args(argv))

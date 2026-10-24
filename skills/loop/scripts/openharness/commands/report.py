"""Compose every measurement into one reviewable report (JSON, Markdown, SARIF, JUnit)."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape, quoteattr

from .. import __version__, jsonio
from ..commands import cases as cases_command
from ..commands import inventory as inventory_command
from ..commands import telemetry as telemetry_command
from ..drift import build_lock, compare, load_lock, summarize
from ..errors import EXIT_FINDINGS, EXIT_OK, EXIT_USAGE, OpenHarnessError
from ..journal import load_entries
from ..manifest import measure, require_manifest
from ..schemas import REPORT, REPORT_RECEIPT

HELP = "compose audit, inventory, lock, cases, and telemetry"
DESCRIPTION = "Write one harness report in JSON, Markdown, SARIF, or JUnit."

FORMATS = {
    "json": "harness-report.json",
    "markdown": "harness-report.md",
    "sarif": "harness-report.sarif",
    "junit": "harness-report.xml",
}
LEVELS = {"error": "error", "warn": "warning", "info": "note"}


def _sarif(report: dict[str, Any]) -> dict[str, Any]:
    findings = report["audit"]["findings"]
    rules = [{"id": code, "name": code} for code in sorted({item["code"] for item in findings})]
    results = [
        {
            "ruleId": item["code"],
            "level": LEVELS.get(item["severity"], "note"),
            "message": {"text": item["detail"]},
            "logicalLocations": [{"fullyQualifiedName": item["component"], "kind": "module"}],
        }
        for item in findings
    ]
    return {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "openharness",
                        "version": __version__,
                        "informationUri": "https://github.com/seismael/openharness",
                        "rules": rules,
                    }
                },
                "results": results,
            }
        ],
    }


def _junit(report: dict[str, Any]) -> str:
    findings = report["audit"]["findings"]
    blocking = [
        gap for gap in (report.get("inventory") or {}).get("gaps", []) if gap.get("required", True)
    ]
    rows: list[str] = []
    for item in findings:
        label = f"{item['component']}: {item['code']}"
        rows.append(
            "  <testcase classname={classname} name={name}>"
            "<failure message={message}>{detail}</failure></testcase>".format(
                classname=quoteattr("openharness.audit"),
                name=quoteattr(label),
                message=quoteattr(item["detail"]),
                detail=escape(item["detail"]),
            )
        )
    for gap in blocking:
        detail = str(gap.get("reason", ""))
        rows.append(
            "  <testcase classname={classname} name={name}>"
            "<failure message={message}>{detail}</failure></testcase>".format(
                classname=quoteattr("openharness.inventory"),
                name=quoteattr(str(gap.get("id"))),
                message=quoteattr(detail),
                detail=escape(detail),
            )
        )
    if not rows:
        rows.append('  <testcase classname="openharness" name="harness"/>')
    total = len(rows)
    failures = len(findings) + len(blocking)
    return "\n".join(
        [
            '<?xml version="1.0" encoding="utf-8"?>',
            f'<testsuite name="openharness" tests="{total}" failures="{failures}" '
            f'errors="0" skipped="0">',
            *rows,
            "</testsuite>",
            "",
        ]
    )


def _row(*values: Any) -> str:
    return "| " + " | ".join(str(value).replace("|", "\\|") for value in values) + " |"


def _markdown(report: dict[str, Any]) -> str:
    audit = report["audit"]
    lines = [
        f"# Harness report: {report['manifest']}",
        "",
        f"- Fingerprint: `{report['fingerprint']}`",
        f"- Components: {audit['totals']['components']}",
        f"- Files: {audit['totals']['files']}",
        f"- Always-on tokens: {audit['totals']['always_on_tokens']}",
        f"- Total tokens: {audit['totals']['total_tokens']}",
        f"- Findings: {audit['counts']['error']} error, "
        f"{audit['counts']['warn']} warn, {audit['counts']['info']} info",
        f"- Verdict: {'clean' if report['ok'] else 'attention required'}",
        "",
        "## Findings",
        "",
    ]
    if audit["findings"]:
        lines.append(_row("Severity", "Code", "Component", "Detail"))
        lines.append(_row(":---", ":---", ":---", ":---"))
        for item in audit["findings"]:
            lines.append(_row(item["severity"], item["code"], item["component"], item["detail"]))
    else:
        lines.append("No findings.")

    inventory = report.get("inventory")
    if inventory is not None:
        lines.extend(
            [
                "",
                "## Capability inventory",
                "",
                f"- Coverage: {inventory['coverage']}",
                f"- Requirements met: {inventory['requirements']['met']} "
                f"of {inventory['requirements']['total']}",
            ]
        )
        if inventory["gaps"]:
            lines.extend(["", _row("Requirement", "Kind", "Required", "Reason")])
            lines.append(_row(":---", ":---", ":---", ":---"))
            for gap in inventory["gaps"]:
                lines.append(
                    _row(
                        gap["id"],
                        gap["kind"],
                        "yes" if gap["required"] else "no",
                        gap["reason"],
                    )
                )

    lock = report.get("lock")
    if lock is not None:
        lines.extend(
            [
                "",
                "## Lockfile",
                "",
                f"- Lock: `{lock['path']}`",
                f"- Present: {'yes' if lock['present'] else 'no'}",
                f"- Match: {'yes' if lock.get('match') else 'no'}",
            ]
        )
        if lock.get("changes"):
            lines.append(f"- Changes: {len(lock['changes'])}")

    cases = report.get("cases")
    if cases is not None:
        lines.extend(
            [
                "",
                "## Declared cases",
                "",
                f"- Declared: {cases['declared']}",
                f"- Executed: {'yes' if cases['executed'] else 'no'}",
            ]
        )
        if cases["executed"]:
            lines.append(f"- Passed: {cases['passed']} of {cases['declared']}")

    telemetry = report.get("telemetry")
    if telemetry is not None:
        lines.extend(
            [
                "",
                "## Telemetry",
                "",
                f"- Iterations: {telemetry['iterations']}",
                f"- Adoption rate: {telemetry['adoption_rate']}",
                f"- Measured gain: {telemetry['gain_total']}",
                f"- Regression total: {telemetry['regression_total']}",
            ]
        )

    lines.append("")
    return "\n".join(lines)


def render(report: dict[str, Any], fmt: str) -> str:
    if fmt == "markdown":
        return _markdown(report)
    if fmt == "sarif":
        return jsonio.pretty(_sarif(report)) + "\n"
    if fmt == "junit":
        return _junit(report)
    return jsonio.pretty(report) + "\n"


def configure(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--manifest",
        default="harness.json",
        help="Path to harness.manifest.v1 (default: harness.json)",
    )
    parser.add_argument("--requirements", help="Path to a requirements declaration")
    parser.add_argument("--cases", help="Path to a case declaration")
    parser.add_argument("--journal", help="Path to journal.jsonl for telemetry")
    parser.add_argument(
        "--lock", default="harness.lock", help="Lockfile path (default: harness.lock)"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute declared cases instead of only validating them",
    )
    parser.add_argument(
        "--workdir",
        help="Directory case commands run in (default: the manifest directory)",
    )
    parser.add_argument(
        "--format",
        choices=tuple(FORMATS),
        default="json",
        help="Report format (default: json)",
    )
    parser.add_argument("--output", help="Report path (default depends on the format)")


def _shrink(payload: dict[str, Any]) -> dict[str, Any]:
    trimmed = dict(payload)
    for key in ("changes", "findings"):
        if key in trimmed:
            trimmed[key] = trimmed[key][:8]
    trimmed["truncated"] = True
    return trimmed


def run(args: argparse.Namespace) -> int:
    try:
        manifest = require_manifest(args.manifest)
        audit_receipt, file_stats = measure(manifest, args.manifest)

        inventory_payload: dict[str, Any] | None = None
        if args.requirements:
            requirements = inventory_command.load_requirements(args.requirements)
            inventory_payload = inventory_command.build(manifest, args.manifest, requirements)

        lock_payload: dict[str, Any] | None = None
        lock_file = Path(args.lock)
        if lock_file.is_file():
            locked = load_lock(lock_file)
            actual = build_lock(
                manifest,
                args.manifest,
                {"requirements": args.requirements, "cases": args.cases},
                measured=(audit_receipt, file_stats),
            )
            changes = compare(locked, actual)
            state = summarize(locked, actual, changes)
            lock_payload = {
                "path": args.lock.replace("\\", "/"),
                "present": True,
                "match": not state["drift"],
                "changes": changes,
            }

        cases_payload: dict[str, Any] | None = None
        if args.cases:
            declarations = cases_command.load_cases(args.cases)
            problems = cases_command.validate(declarations)
            if problems:
                raise OpenHarnessError(
                    "invalid case declaration: " + "; ".join(item["code"] for item in problems[:3])
                )
            cases_payload = {
                "declared": len(declarations),
                "executed": False,
                "ok": True,
            }
            if args.execute:
                workdir = (
                    Path(args.workdir) if args.workdir else Path(args.manifest).resolve().parent
                )
                if not workdir.is_dir():
                    raise OpenHarnessError(f"not a directory: {workdir}")
                receipt = cases_command.execute_cases(
                    declarations, workdir, fingerprint=audit_receipt["fingerprint"]
                )
                cases_payload = {
                    "declared": len(declarations),
                    "executed": True,
                    "passed": receipt["passed"],
                    "failed": receipt["failed"],
                    "ok": receipt["ok"],
                }

        telemetry_payload: dict[str, Any] | None = None
        if args.journal:
            entries, error = load_entries(args.journal)
            if error is not None:
                raise OpenHarnessError(error)
            assert entries is not None
            telemetry_payload = telemetry_command.summarize(entries)
    except OpenHarnessError as error:
        print(jsonio.spaced({"schema": REPORT_RECEIPT, "ok": False, "error": error.message}))
        return EXIT_USAGE

    ok = bool(audit_receipt["ok"])
    if inventory_payload is not None:
        ok = ok and bool(inventory_payload["ok"])
    if lock_payload is not None:
        ok = ok and bool(lock_payload["match"])
    if cases_payload is not None:
        ok = ok and bool(cases_payload["ok"])

    report = {
        "schema": REPORT,
        "ok": ok,
        "manifest": audit_receipt["manifest"],
        "fingerprint": audit_receipt["fingerprint"],
        "audit": {
            "ok": audit_receipt["ok"],
            "counts": audit_receipt["counts"],
            "totals": audit_receipt["totals"],
            "findings": audit_receipt["findings"],
        },
        "inventory": inventory_payload,
        "lock": lock_payload,
        "cases": cases_payload,
        "telemetry": telemetry_payload,
    }

    output = Path(args.output or FORMATS[args.format])
    document = render(report, args.format)
    jsonio.write_text(output, document)
    receipt = {
        "schema": REPORT_RECEIPT,
        "ok": ok,
        "format": args.format,
        "output": str(output).replace("\\", "/"),
        "bytes": jsonio.byte_size(document),
        "fingerprint": report["fingerprint"],
        "counts": report["audit"]["counts"],
        "changes": len((lock_payload or {}).get("changes", [])),
    }
    print(jsonio.bounded(receipt, [_shrink]))
    return EXIT_OK if ok else EXIT_FINDINGS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    configure(parser)
    return run(parser.parse_args(argv))

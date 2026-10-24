"""Classify recorded iteration failures into a fixed taxonomy (RFC-0014)."""

from __future__ import annotations

import argparse
from collections import Counter
from typing import Any

from .. import jsonio
from ..errors import EXIT_FINDINGS, EXIT_OK, EXIT_USAGE
from ..journal import load_entries
from ..schemas import FAILURES

HELP = "classify recorded iteration failures"
DESCRIPTION = "Classify recorded iteration failures."

CONTRACT = FAILURES
CLASSES = (
    "tool-misuse",
    "context-loss",
    "wrong-premise",
    "dead-end",
    "unsafe-action",
    "spec-ambiguity",
    "environment",
    "data-quality",
    "unclassified",
)


def bounded(payload: dict[str, Any]) -> str:
    text = jsonio.compact(payload)
    if jsonio.byte_size(text) <= jsonio.MAX_BYTES:
        return text
    trimmed = {
        "schema": payload["schema"],
        "iterations": payload["iterations"],
        "failures": payload["failures"],
        "rate": payload["rate"],
        "classes": payload["classes"],
        "repeated": payload["repeated"],
        "counts": payload["counts"],
        "ok": payload["ok"],
        "truncated": True,
    }
    return jsonio.compact(trimmed)


def classify(entries: list[dict[str, Any]], recurrence: int = 2) -> dict[str, Any]:
    classes: Counter[str] = Counter()
    findings: list[dict[str, Any]] = []
    failures = 0

    for entry in entries:
        iteration = entry.get("iteration")
        record = entry.get("failure")
        if record is None:
            continue
        failures += 1
        if not isinstance(record, dict):
            findings.append(
                {
                    "code": "failure.invalid",
                    "severity": "error",
                    "iteration": iteration,
                    "detail": "failure must be an object",
                }
            )
            classes["unclassified"] += 1
            continue
        name = record.get("class")
        if name not in CLASSES:
            findings.append(
                {
                    "code": "failure.unclassified",
                    "severity": "error",
                    "iteration": iteration,
                    "detail": f"unknown failure class: {name!r}",
                }
            )
            classes["unclassified"] += 1
            continue
        classes[name] += 1
        if name == "unclassified" and not record.get("detail"):
            findings.append(
                {
                    "code": "failure.undiagnosed",
                    "severity": "warn",
                    "iteration": iteration,
                    "detail": "unclassified failure without a detail note",
                }
            )

    repeated = [
        {"class": name, "count": count}
        for name, count in sorted(classes.items())
        if count >= recurrence and name != "unclassified"
    ]
    for item in repeated:
        findings.append(
            {
                "code": "failure.recurring",
                "severity": "warn",
                "iteration": None,
                "detail": f"{item['class']} occurred {item['count']} times: harness gap, not incident",
            }
        )

    valid = sum(1 for entry in entries if isinstance(entry.get("iteration"), int))
    counts = Counter(item["severity"] for item in findings)
    return {
        "schema": CONTRACT,
        "iterations": valid,
        "failures": failures,
        "rate": round(failures / valid, 4) if valid else 0.0,
        "classes": dict(sorted(classes.items())),
        "taxonomy": list(CLASSES),
        "repeated": repeated,
        "findings": findings,
        "counts": {
            "error": counts.get("error", 0),
            "warn": counts.get("warn", 0),
            "info": counts.get("info", 0),
        },
        "truncated": False,
        "ok": counts.get("error", 0) == 0,
    }


def configure(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--journal", required=True, help="Path to journal.jsonl")
    parser.add_argument(
        "--recurrence",
        type=int,
        default=2,
        help="Occurrences of one class treated as a harness gap (default: 2)",
    )


def run(args: argparse.Namespace) -> int:
    if args.recurrence < 2:
        print(
            jsonio.spaced(
                {
                    "schema": CONTRACT,
                    "ok": False,
                    "error": "recurrence must be at least 2",
                }
            )
        )
        return EXIT_USAGE

    entries, error = load_entries(args.journal)
    if error is not None:
        print(jsonio.spaced({"schema": CONTRACT, "ok": False, "error": error}))
        return EXIT_USAGE

    assert entries is not None
    payload = classify(entries, recurrence=args.recurrence)
    print(bounded(payload))
    return EXIT_OK if payload["ok"] else EXIT_FINDINGS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    configure(parser)
    return run(parser.parse_args(argv))

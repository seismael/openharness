#!/usr/bin/env python3
"""Classify recorded iteration failures into a fixed taxonomy (RFC-0014).

A failure class is a diagnosis, not a label of convenience. The taxonomy is
closed so recurrence can be counted: one occurrence is an incident, the same
class occurring again is evidence that the harness, not the iteration, is the
cause.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

CONTRACT = "openharness.failures.v1"
MAX_BYTES = 2500
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


def bounded(payload):
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    if len(text.encode("utf-8")) <= MAX_BYTES:
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
    return json.dumps(trimmed, sort_keys=True, separators=(",", ":"))


def load_entries(path):
    try:
        text = Path(path).read_text(encoding="utf-8-sig")
    except OSError as error:
        return None, f"cannot read journal: {error}"
    entries = []
    for index, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            return None, f"line {index} is not valid JSON: {error}"
        if not isinstance(value, dict):
            return None, f"line {index} is not a JSON object"
        entries.append(value)
    return entries, None


def classify(entries, recurrence=2):
    classes = Counter()
    findings = []
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


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Classify recorded iteration failures."
    )
    parser.add_argument("--journal", required=True, help="Path to journal.jsonl")
    parser.add_argument(
        "--recurrence",
        type=int,
        default=2,
        help="Occurrences of one class treated as a harness gap (default: 2)",
    )
    args = parser.parse_args(argv)
    if args.recurrence < 2:
        print(
            json.dumps(
                {
                    "schema": CONTRACT,
                    "ok": False,
                    "error": "recurrence must be at least 2",
                },
                sort_keys=True,
            )
        )
        return 2

    entries, error = load_entries(args.journal)
    if error is not None:
        print(
            json.dumps(
                {"schema": CONTRACT, "ok": False, "error": error}, sort_keys=True
            )
        )
        return 2

    payload = classify(entries, recurrence=args.recurrence)
    print(bounded(payload))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

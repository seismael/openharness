#!/usr/bin/env python3
"""Aggregate journal cost and contrast into a bounded telemetry projection (RFC-0011).

Telemetry answers three questions the journal already contains the data for:
what was tried, what moved, and what it cost. It aggregates recorded fields only.
It never estimates tokens and never infers a gain that was not measured.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

CONTRACT = "openharness.telemetry.v1"
MAX_BYTES = 2500
COST_KEYS = ("tokens_in", "tokens_out", "tool_calls", "retries", "wall_steps", "usd")
ADOPTING = {"adopted", "preserved"}
KNOWN_DECISIONS = {"adopted", "rejected", "inconclusive", "informational", "preserved"}
KNOWN_CONTRASTS = {"mitigated", "unchanged", "regressed", "unproven"}


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value


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


def gain(entry, direction):
    """Measured improvement, or None when the entry has no usable measurements."""
    before = number(entry.get("metric_before"))
    after = number(entry.get("metric_after"))
    if before is None or after is None:
        return None
    delta = after - before
    return delta if direction == "maximize" else -delta


def summarize(entries, direction="maximize", tolerance=0.0):
    decisions = Counter()
    contrasts = Counter()
    deficiencies = {}
    totals = {}
    costed = 0
    gain_total = 0.0
    regression_total = 0.0
    measured = 0
    adopting = 0
    evidenced = 0
    invalid = 0

    for entry in entries:
        iteration = entry.get("iteration")
        if isinstance(iteration, bool) or not isinstance(iteration, int):
            invalid += 1
            continue

        decision = entry.get("decision")
        decisions[decision if decision in KNOWN_DECISIONS else "unclassified"] += 1
        contrast = entry.get("contrast")
        if contrast is not None:
            contrasts[contrast if contrast in KNOWN_CONTRASTS else "unclassified"] += 1

        if decision in ADOPTING:
            adopting += 1
            if entry.get("evidence_ref"):
                evidenced += 1

        cost = entry.get("cost")
        if isinstance(cost, dict):
            recorded = False
            for key in COST_KEYS:
                value = number(cost.get(key))
                if value is not None:
                    totals[key] = round(totals.get(key, 0) + value, 6)
                    recorded = True
            if recorded:
                costed += 1

        value = gain(entry, direction)
        if value is None:
            continue
        measured += 1
        if value > tolerance:
            gain_total += value
        elif value < -tolerance:
            regression_total += value

        deficiency = entry.get("deficiency")
        if isinstance(deficiency, str) and deficiency.strip():
            row = deficiencies.setdefault(
                deficiency.strip(),
                {"iterations": 0, "adopted": 0, "mitigated": 0, "gain": 0.0},
            )
            row["iterations"] += 1
            if decision == "adopted":
                row["adopted"] += 1
            if contrast == "mitigated":
                row["mitigated"] += 1
            if value > tolerance:
                row["gain"] = round(row["gain"] + value, 6)

    tokens = totals.get("tokens_in", 0) + totals.get("tokens_out", 0)
    cost_per_gain = None
    if gain_total > 0:
        usd = totals.get("usd")
        cost_per_gain = {
            "usd": round(usd / gain_total, 6) if usd else None,
            "tokens": round(tokens / gain_total, 2) if tokens else None,
        }

    return {
        "schema": CONTRACT,
        "direction": direction,
        "tolerance": tolerance,
        "iterations": len(entries) - invalid,
        "invalid": invalid,
        "decisions": dict(sorted(decisions.items())),
        "contrasts": dict(sorted(contrasts.items())),
        "adoption_rate": round(adopting / len(entries), 4) if entries else 0.0,
        "mitigation_rate": (
            round(contrasts["mitigated"] / measured, 4) if measured else 0.0
        ),
        "evidence_coverage": round(evidenced / adopting, 4) if adopting else 0.0,
        "costed_iterations": costed,
        "cost": dict(sorted(totals.items())),
        "tokens_total": tokens,
        "measured": measured,
        "gain_total": round(gain_total, 6),
        "regression_total": round(regression_total, 6),
        "cost_per_gain": cost_per_gain,
        "deficiencies": dict(sorted(deficiencies.items())),
        "truncated": False,
    }


def bounded(payload):
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    if len(text.encode("utf-8")) <= MAX_BYTES:
        return text
    minimal = {
        "schema": payload["schema"],
        "direction": payload["direction"],
        "iterations": payload["iterations"],
        "decisions": payload["decisions"],
        "contrasts": payload["contrasts"],
        "cost": payload["cost"],
        "gain_total": payload["gain_total"],
        "truncated": True,
    }
    return json.dumps(minimal, sort_keys=True, separators=(",", ":"))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Project journal telemetry.")
    parser.add_argument("--journal", required=True, help="Path to journal.jsonl")
    parser.add_argument(
        "--direction",
        choices=("maximize", "minimize"),
        default="maximize",
        help="Metric direction used to sign measured gain",
    )
    parser.add_argument(
        "--tolerance", type=float, default=0.0, help="Delta treated as no movement"
    )
    args = parser.parse_args(argv)

    entries, error = load_entries(args.journal)
    if error is not None:
        print(
            json.dumps(
                {"schema": CONTRACT, "ok": False, "error": error}, sort_keys=True
            )
        )
        return 2

    payload = summarize(entries, direction=args.direction, tolerance=args.tolerance)
    payload["ok"] = True
    print(bounded(payload))
    return 0


if __name__ == "__main__":
    sys.exit(main())

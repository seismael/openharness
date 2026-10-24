"""Validate journal entries against the iteration contract (RFC-0010)."""

from __future__ import annotations

import argparse
import json
from typing import Any

from .. import jsonio
from ..errors import EXIT_FINDINGS, EXIT_OK, EXIT_USAGE
from ..journal import load_entries
from ..receipts import count_severities
from ..schemas import VERIFY

HELP = "validate a journal against the iteration contract"
DESCRIPTION = "Validate a loop journal against RFC-0010."

DECISIONS = {"adopted", "rejected", "inconclusive", "informational", "preserved"}
SCOPES = {"invariant", "local"}
CONTRASTS = {"mitigated", "unchanged", "regressed", "unproven"}
ADOPTING = {"adopted", "preserved"}


def bounded(payload: dict[str, Any]) -> str:
    """Keep the verdict and counts inside 2500 bytes, dropping detail if needed."""
    text = jsonio.compact(payload)
    if jsonio.byte_size(text) <= jsonio.MAX_BYTES:
        return text
    findings = payload.get("findings")
    if isinstance(findings, list):
        dropped = 0
        while findings and jsonio.byte_size(text) > jsonio.MAX_BYTES:
            findings.pop()
            dropped += 1
            payload["dropped_findings"] = dropped
            payload["truncated"] = True
            text = jsonio.compact(payload)
        if jsonio.byte_size(text) <= jsonio.MAX_BYTES:
            return text
    minimal = {
        "schema": payload.get("schema"),
        "entries": payload.get("entries"),
        "counts": payload.get("counts"),
        "ok": payload.get("ok"),
        "truncated": True,
    }
    return jsonio.compact(minimal)


def delta_verdict(before: Any, after: Any, direction: str, tolerance: float) -> str | None:
    """Map a measured delta onto the contrast vocabulary."""
    if not isinstance(before, (int, float)) or not isinstance(after, (int, float)):
        return None
    delta = after - before
    if not isinstance(delta, (int, float)) or isinstance(delta, bool):
        return None
    gain = delta if direction == "maximize" else -delta
    if gain > tolerance:
        return "mitigated"
    if gain < -tolerance:
        return "regressed"
    return "unchanged"


def verify(
    entries: list[dict[str, Any]],
    direction: str = "maximize",
    tolerance: float = 0.0,
    fingerprint: str = "",
) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    seen: dict[int, bool] = {}

    def add(code: str, severity: str, iteration: int, detail: str) -> None:
        findings.append(
            {
                "code": code,
                "severity": severity,
                "iteration": iteration,
                "detail": detail,
            }
        )

    for entry in entries:
        iteration = entry.get("iteration")
        if not isinstance(iteration, int) or isinstance(iteration, bool):
            add("iteration.invalid", "error", -1, "iteration must be an integer")
            continue
        if iteration in seen:
            add("iteration.duplicate", "error", iteration, "iteration id already used")
        seen[iteration] = True

        for field in ("ts", "front", "hypothesis", "decision"):
            if not entry.get(field):
                add("entry.field_missing", "error", iteration, field)

        decision = entry.get("decision")
        if decision is not None and decision not in DECISIONS:
            add("decision.invalid", "error", iteration, str(decision))

        scope = entry.get("scope")
        if scope is not None and scope not in SCOPES:
            add("scope.invalid", "error", iteration, str(scope))

        contrast = entry.get("contrast")
        if contrast is not None and contrast not in CONTRASTS:
            add("contrast.invalid", "error", iteration, str(contrast))

        if decision in ADOPTING:
            if scope is None:
                add(
                    "scope.missing",
                    "error",
                    iteration,
                    "adoption requires a declared scope",
                )
            if not entry.get("evidence_ref"):
                add(
                    "evidence.missing",
                    "error",
                    iteration,
                    "adoption requires evidence_ref",
                )
            if not entry.get("rationale"):
                add(
                    "rationale.missing",
                    "error",
                    iteration,
                    "adoption requires a rationale",
                )
            if scope == "invariant":
                cases = entry.get("cases") or []
                if len({str(case) for case in cases}) < 2:
                    add(
                        "invariant.single_case",
                        "error",
                        iteration,
                        "an invariant change needs at least two cases",
                    )
            if scope == "local" and entry.get("promote_global") is True:
                add(
                    "scope.promotion",
                    "error",
                    iteration,
                    "local evidence cannot be promoted to a global default",
                )

        if contrast in {"mitigated", "unchanged", "regressed"}:
            expected = delta_verdict(
                entry.get("metric_before"),
                entry.get("metric_after"),
                direction,
                tolerance,
            )
            if expected is None:
                add(
                    "contrast.unmeasured",
                    "warn",
                    iteration,
                    "contrast claim without before/after metrics",
                )
            elif expected != contrast:
                add(
                    "contrast.inconsistent",
                    "warn",
                    iteration,
                    f"declared {contrast}, metrics imply {expected}",
                )

        recorded = entry.get("harness_fingerprint")
        if fingerprint and recorded and recorded != fingerprint:
            add(
                "fingerprint.stale",
                "error",
                iteration,
                "recorded harness state does not match the audited manifest state",
            )

        if decision == "preserved" and not entry.get("rationale"):
            add(
                "preserve.justification",
                "error",
                iteration,
                "preserving the current harness requires an observation",
            )

    counts = count_severities(findings)
    return {
        "schema": VERIFY,
        "entries": len(entries),
        "direction": direction,
        "tolerance": tolerance,
        "findings": findings,
        "counts": counts,
        "truncated": False,
        "dropped_findings": 0,
        "ok": counts["error"] == 0,
    }


def configure(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--journal", required=True, help="Path to journal.jsonl")
    parser.add_argument(
        "--direction",
        choices=("maximize", "minimize"),
        default="maximize",
        help="Metric direction used to sanity-check contrast claims",
    )
    parser.add_argument("--tolerance", type=float, default=0.0, help="Delta treated as unchanged")
    parser.add_argument(
        "--fingerprint",
        default="",
        help="Current harness state fingerprint (from openharness audit)",
    )


def run(args: argparse.Namespace) -> int:
    entries, error = load_entries(args.journal)
    if error is not None:
        print(jsonio.spaced({"schema": VERIFY, "ok": False, "error": error}))
        return EXIT_USAGE

    assert entries is not None
    result = verify(
        entries,
        direction=args.direction,
        tolerance=args.tolerance,
        fingerprint=args.fingerprint,
    )
    payload = bounded(result)
    print(payload)
    return EXIT_OK if json.loads(payload).get("ok") else EXIT_FINDINGS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    configure(parser)
    return run(parser.parse_args(argv))

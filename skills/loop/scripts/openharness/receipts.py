"""Receipt vocabulary: findings and their severity counts."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

SEVERITIES = ("error", "warn", "info")


def finding(code: str, severity: str, component: str, detail: str) -> dict[str, Any]:
    return {
        "code": code,
        "severity": severity,
        "component": component,
        "detail": detail,
    }


def count_severities(findings: Iterable[dict[str, Any]]) -> dict[str, int]:
    counts = {severity: 0 for severity in SEVERITIES}
    for item in findings:
        counts[item["severity"]] += 1
    return counts

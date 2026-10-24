#!/usr/bin/env python3
"""Inventory the declared harness surface and report capability gaps (RFC-0013).

The inventory answers two questions about a harness manifest: what capability is
actually present and reachable, and which declared requirements no present
component satisfies. It reuses the audit's file matching so inventory and audit
cannot disagree about what exists.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from openharness_audit import audit, load_manifest

CONTRACT = "openharness.inventory.v1"
MAX_BYTES = 2500
KINDS = (
    "system_prompt",
    "guardrails",
    "memory",
    "tool_guidance",
    "subagents",
    "skills",
    "scripts",
    "plugins",
)
REQUIREMENT_KEYS = {
    "id",
    "kind",
    "component",
    "requires_files",
    "required",
    "description",
}


class InventoryError(Exception):
    """A declaration problem that prevents the inventory."""


def bounded(payload):
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    if len(text.encode("utf-8")) <= MAX_BYTES:
        return text
    trimmed = dict(payload)
    trimmed["gaps"] = trimmed.get("gaps", [])[:8]
    trimmed["components"] = {}
    trimmed["truncated"] = True
    return json.dumps(trimmed, sort_keys=True, separators=(",", ":"))


def load_requirements(path):
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except OSError as error:
        raise InventoryError(f"cannot read requirements: {error}") from error
    except json.JSONDecodeError as error:
        raise InventoryError(f"requirements are not valid JSON: {error}") from error
    if not isinstance(document, dict):
        raise InventoryError("requirements document must be an object")
    unknown = sorted(set(document) - {"schema", "requirements"})
    if unknown:
        raise InventoryError(f"unknown document keys: {', '.join(unknown)}")
    requirements = document.get("requirements")
    if not isinstance(requirements, list):
        raise InventoryError("document key 'requirements' must be an array")
    problems = []
    seen = set()
    for index, requirement in enumerate(requirements):
        label = f"#{index + 1}"
        if not isinstance(requirement, dict):
            problems.append(f"{label} must be an object")
            continue
        identifier = requirement.get("id")
        if not isinstance(identifier, str) or not identifier.strip():
            problems.append(f"{label} requires a non-empty id")
        elif identifier in seen:
            problems.append(f"{identifier}: duplicate requirement id")
        else:
            seen.add(identifier)
            label = identifier
        if requirement.get("kind") not in KINDS:
            problems.append(f"{label}: kind must be one of {', '.join(KINDS)}")
        unknown_fields = sorted(set(requirement) - REQUIREMENT_KEYS)
        if unknown_fields:
            problems.append(f"{label}: unknown fields {', '.join(unknown_fields)}")
        for flag in ("requires_files", "required"):
            if flag in requirement and not isinstance(requirement[flag], bool):
                problems.append(f"{label}: {flag} must be a boolean")
    if problems:
        raise InventoryError("; ".join(problems[:6]))
    return requirements


def inventory(receipt):
    """Summarize component rows per kind."""
    summary = {}
    for kind in KINDS:
        rows = [row for row in receipt["components"] if row["kind"] == kind]
        enabled = [row for row in rows if row["enabled"]]
        summary[kind] = {
            "total": len(rows),
            "enabled": len(enabled),
            "files": sum(len(row["files"]) for row in enabled),
            "tokens": sum(row["tokens"] for row in enabled),
            "components": [row["id"] for row in enabled],
        }
    return summary


def gaps(requirements, summary, rows):
    """Return (met, gap records) for the declared requirements."""
    by_id = {row["id"]: row for row in rows}
    met = 0
    found = []
    for requirement in requirements:
        identifier = requirement["id"]
        kind = requirement["kind"]
        required = requirement.get("required", True)
        reason = ""
        component = requirement.get("component")
        if component is not None:
            row = by_id.get(component)
            if row is None:
                reason = f"component {component} is not declared"
            elif row["kind"] != kind:
                reason = f"component {component} is {row['kind']}, not {kind}"
            elif not row["enabled"]:
                reason = f"component {component} is disabled"
            elif not row["files"]:
                reason = f"component {component} matches no files"
        elif not summary[kind]["enabled"]:
            reason = f"no enabled component of kind {kind}"
        elif requirement.get("requires_files", True) and not summary[kind]["files"]:
            reason = f"no enabled {kind} component matches files"
        if reason:
            found.append(
                {"id": identifier, "kind": kind, "reason": reason, "required": required}
            )
        else:
            met += 1
    return met, found


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Inventory a harness surface and report gaps."
    )
    parser.add_argument(
        "--manifest", required=True, help="Path to a harness.manifest.v1 JSON file"
    )
    parser.add_argument("--requirements", help="Path to a requirements declaration")
    args = parser.parse_args(argv)

    manifest, error = load_manifest(args.manifest)
    if error is not None:
        print(
            json.dumps(
                {"schema": CONTRACT, "ok": False, "error": error}, sort_keys=True
            )
        )
        return 2

    requirements = []
    if args.requirements:
        try:
            requirements = load_requirements(args.requirements)
        except InventoryError as error:
            print(
                json.dumps(
                    {"schema": CONTRACT, "ok": False, "error": str(error)},
                    sort_keys=True,
                )
            )
            return 2

    receipt = audit(manifest, args.manifest)
    summary = inventory(receipt)
    met, found = gaps(requirements, summary, receipt["components"])
    missing_kinds = [kind for kind in KINDS if not summary[kind]["enabled"]]
    blocking = [item for item in found if item["required"]]
    payload = {
        "schema": CONTRACT,
        "manifest": receipt["manifest"],
        "fingerprint": receipt["fingerprint"],
        "components": summary,
        "kinds_missing": missing_kinds,
        "requirements": {"total": len(requirements), "met": met},
        "gaps": found,
        "coverage": round(met / len(requirements), 4) if requirements else 1.0,
        "truncated": False,
        "ok": not blocking,
    }
    print(bounded(payload))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())

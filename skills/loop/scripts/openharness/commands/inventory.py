"""Inventory the declared harness surface and report capability gaps (RFC-0013)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .. import jsonio
from ..errors import EXIT_FINDINGS, EXIT_OK, EXIT_USAGE, DeclarationError
from ..manifest import audit, load_manifest
from ..schemas import INVENTORY, KINDS

HELP = "inventory a harness surface and report gaps"
DESCRIPTION = "Inventory a harness surface and report gaps."

CONTRACT = INVENTORY
REQUIREMENT_KEYS = {
    "id",
    "kind",
    "component",
    "requires_files",
    "required",
    "description",
}


class InventoryError(DeclarationError):
    """A declaration problem that prevents the inventory."""


def bounded(payload: dict[str, Any]) -> str:
    text = jsonio.compact(payload)
    if jsonio.byte_size(text) <= jsonio.MAX_BYTES:
        return text
    trimmed = dict(payload)
    trimmed["gaps"] = trimmed.get("gaps", [])[:8]
    trimmed["components"] = {}
    trimmed["truncated"] = True
    return jsonio.compact(trimmed)


def load_requirements(path: str | Path) -> list[dict[str, Any]]:
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
    problems: list[str] = []
    seen: set[str] = set()
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


def inventory(receipt: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Summarize component rows per kind."""
    summary: dict[str, dict[str, Any]] = {}
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


def gaps(
    requirements: list[dict[str, Any]],
    summary: dict[str, dict[str, Any]],
    rows: list[dict[str, Any]],
) -> tuple[int, list[dict[str, Any]]]:
    """Return (met, gap records) for the declared requirements."""
    by_id = {row["id"]: row for row in rows}
    met = 0
    found: list[dict[str, Any]] = []
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
            found.append({"id": identifier, "kind": kind, "reason": reason, "required": required})
        else:
            met += 1
    return met, found


def build(
    manifest: dict[str, Any],
    manifest_path: str | Path,
    requirements: list[dict[str, Any]],
) -> dict[str, Any]:
    """Return the inventory receipt for an already loaded manifest."""
    receipt = audit(manifest, manifest_path)
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
    return payload


def configure(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--manifest", required=True, help="Path to a harness.manifest.v1 JSON file")
    parser.add_argument("--requirements", help="Path to a requirements declaration")


def run(args: argparse.Namespace) -> int:
    manifest, error = load_manifest(args.manifest)
    if error is not None:
        print(jsonio.spaced({"schema": CONTRACT, "ok": False, "error": error}))
        return EXIT_USAGE

    requirements: list[dict[str, Any]] = []
    if args.requirements:
        try:
            requirements = load_requirements(args.requirements)
        except InventoryError as error:
            print(jsonio.spaced({"schema": CONTRACT, "ok": False, "error": str(error)}))
            return EXIT_USAGE

    assert manifest is not None
    payload = build(manifest, args.manifest, requirements)
    print(bounded(payload))
    return EXIT_OK if payload["ok"] else EXIT_FINDINGS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    configure(parser)
    return run(parser.parse_args(argv))

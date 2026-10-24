"""Harness manifest loading, measurement, and the deterministic audit.

The audit is the primitive every other command composes with: it establishes
which files form the harness, how large each component is, and what is wrong
with the surface. It reads files and nothing else.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .digest import relative_path, state_fingerprint
from .errors import DeclarationError
from .receipts import count_severities, finding
from .schemas import KINDS, MANIFEST, RECEIPT

MANIFEST_SCHEMA = MANIFEST
RECEIPT_SCHEMA = RECEIPT

MAX_RECEIPT_BYTES = 2500
CHARS_PER_TOKEN = 4
MAX_FINDINGS_PER_COMPONENT = 10
DUPLICATE_MIN_CHARS = 40

REACHABILITY_KINDS = ("skills", "subagents")
SEVERITY_RANK = {"info": 0, "warn": 1, "error": 2}

LINK = re.compile(r"\]\(\s*<?([^)>\s]+)>?\s*\)")
EXTERNAL = ("http://", "https://", "mailto:", "#", "data:")
FRONTMATTER_NAME = re.compile(r"^name:\s*([^\s#]+)", re.MULTILINE)


def estimate_tokens(text: str) -> int:
    """Deterministic character-based estimate; never a model tokenizer."""
    return (len(text) + CHARS_PER_TOKEN - 1) // CHARS_PER_TOKEN


def normalize(line: str) -> str:
    """Collapse whitespace and case so formatting drift cannot hide duplication."""
    return " ".join(line.split()).lower()


def load_manifest(path: str | Path) -> tuple[dict[str, Any] | None, str | None]:
    """Return ``(manifest, error_message)``."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except OSError as error:
        return None, f"cannot read manifest: {error}"
    except json.JSONDecodeError as error:
        return None, f"manifest is not valid JSON: {error}"
    if not isinstance(data, dict):
        return None, "manifest must be a JSON object"
    if data.get("schema") != MANIFEST:
        return None, f"manifest schema must be {MANIFEST}"
    components = data.get("components")
    if not isinstance(components, list) or not components:
        return None, "manifest requires a non-empty components array"
    seen: set[str] = set()
    for index, component in enumerate(components):
        if not isinstance(component, dict):
            return None, f"component {index} must be an object"
        identifier = component.get("id")
        if not isinstance(identifier, str) or not identifier.strip():
            return None, f"component {index} requires a non-empty id"
        if identifier in seen:
            return None, f"duplicate component id: {identifier}"
        seen.add(identifier)
        if component.get("kind") not in KINDS:
            return (
                None,
                f"component {identifier} has unknown kind: {component.get('kind')!r}",
            )
        paths = component.get("paths")
        if (
            not isinstance(paths, list)
            or not paths
            or not all(isinstance(item, str) and item for item in paths)
        ):
            return (
                None,
                f"component {identifier} requires a non-empty paths array of strings",
            )
        names = component.get("trigger_names")
        if names is not None and (
            not isinstance(names, list) or not all(isinstance(item, str) for item in names)
        ):
            return (
                None,
                f"component {identifier} trigger_names must be an array of strings",
            )
    budget = data.get("budget", {})
    if not isinstance(budget, dict):
        return None, "budget must be an object"
    for key in ("always_on_tokens", "total_tokens"):
        value = budget.get(key)
        if value is not None and (
            not isinstance(value, int) or isinstance(value, bool) or value < 0
        ):
            return None, f"budget.{key} must be a non-negative integer"
    return data, None


def require_manifest(path: str | Path) -> dict[str, Any]:
    """Load a manifest or raise the declaration error a CLI reports as usage."""
    manifest, error = load_manifest(path)
    if error is not None:
        raise DeclarationError(error)
    assert manifest is not None
    return manifest


def matched_files(root: Path, patterns: list[str]) -> list[Path]:
    files: list[Path] = []
    for pattern in patterns:
        for candidate in sorted(root.glob(pattern)):
            if candidate.is_file() and candidate not in files:
                files.append(candidate)
    return files


def markdown_links(text: str) -> list[str]:
    targets: list[str] = []
    for match in LINK.finditer(text):
        target = match.group(1).strip()
        if target and not target.lower().startswith(EXTERNAL):
            targets.append(target.split("#", 1)[0])
    return targets


def declared_names(component: dict[str, Any], files: list[Path]) -> list[str]:
    names = list(component.get("trigger_names") or [])
    for path in files:
        try:
            head = path.read_text(encoding="utf-8-sig", errors="replace")[:800]
        except OSError:
            continue
        match = FRONTMATTER_NAME.search(head)
        if match:
            names.append(match.group(1).strip())
        names.append(path.parent.name)
    unique: list[str] = []
    for name in names:
        if name and name not in unique:
            unique.append(name)
    return unique


def audit(manifest: dict[str, Any], manifest_path: str | Path) -> dict[str, Any]:
    """Measure every declared component and return the audit receipt."""
    manifest_file = Path(manifest_path).resolve()
    root = (manifest_file.parent / manifest.get("root", ".")).resolve()
    always_on_text: list[str] = []
    state_files: list[Path] = []
    rows: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    normalized_index: dict[str, set[str]] = {}

    for component in manifest["components"]:
        identifier = component["id"]
        kind = component["kind"]
        enabled = component.get("enabled", True)
        always_on = bool(component.get("always_on", False))
        files = matched_files(root, component["paths"]) if enabled else []
        state_files.extend(files)
        tokens = 0
        texts: list[tuple[Path, str]] = []

        for path in files:
            try:
                text = path.read_text(encoding="utf-8-sig", errors="replace")
            except OSError:
                findings.append(finding("component.unreadable", "error", identifier, str(path)))
                continue
            if not text.strip():
                findings.append(finding("component.empty", "warn", identifier, str(path)))
                continue
            tokens += estimate_tokens(text)
            texts.append((path, text))
            if path.suffix.lower() == ".md":
                missing = 0
                for target in markdown_links(text):
                    if missing >= MAX_FINDINGS_PER_COMPONENT:
                        break
                    if not (path.parent / target).exists():
                        missing += 1
                        findings.append(
                            finding(
                                "link.missing",
                                "warn",
                                identifier,
                                f"{path.name} -> {target}",
                            )
                        )

        if enabled and not files:
            findings.append(
                finding(
                    "component.missing",
                    "error",
                    identifier,
                    ", ".join(component["paths"]),
                )
            )

        if always_on and enabled:
            always_on_text.extend(text for _, text in texts)

        for _, text in texts:
            for line in text.splitlines():
                key = normalize(line)
                if len(key) < DUPLICATE_MIN_CHARS or key.startswith("<"):
                    continue
                normalized_index.setdefault(key, set()).add(identifier)

        rows.append(
            {
                "id": identifier,
                "kind": kind,
                "enabled": enabled,
                "always_on": always_on,
                "files": [relative_path(path, root) for path in files],
                "tokens": tokens,
                "_names": declared_names(component, files) if kind in REACHABILITY_KINDS else [],
            }
        )

    haystack = "\n".join(always_on_text).lower()
    for row in rows:
        if (
            (row["kind"] in REACHABILITY_KINDS and row["enabled"] and not row["always_on"])
            and row["_names"]
            and not any(name.lower() in haystack for name in row["_names"])
        ):
            findings.append(
                finding(
                    "reachability.orphan",
                    "error",
                    row["id"],
                    "no trigger reference from an always-on component: " + ", ".join(row["_names"]),
                )
            )

    duplicates = [
        finding("duplication.line", "warn", ",".join(sorted(owners)), text[:120])
        for text, owners in sorted(normalized_index.items())
        if len(owners) > 1
    ]
    findings.extend(duplicates[:MAX_FINDINGS_PER_COMPONENT])

    budget = manifest.get("budget", {})
    always_on_tokens = sum(row["tokens"] for row in rows if row["always_on"] and row["enabled"])
    total_tokens = sum(row["tokens"] for row in rows if row["enabled"])
    always_on_budget = budget.get("always_on_tokens")
    total_budget = budget.get("total_tokens")
    if always_on_budget is not None and always_on_tokens > always_on_budget:
        findings.append(
            finding(
                "budget.always_on_exceeded",
                "error",
                "-",
                f"{always_on_tokens} > {always_on_budget}",
            )
        )
    if total_budget is not None and total_tokens > total_budget:
        findings.append(
            finding(
                "budget.total_exceeded",
                "error",
                "-",
                f"{total_tokens} > {total_budget}",
            )
        )

    for row in rows:
        row.pop("_names", None)

    counts = count_severities(findings)

    return {
        "schema": RECEIPT,
        "manifest": manifest.get("name", manifest_file.stem),
        "root": str(root),
        "fingerprint": state_fingerprint(state_files, root),
        "components": rows,
        "totals": {
            "always_on_tokens": always_on_tokens,
            "total_tokens": total_tokens,
            "files": sum(len(row["files"]) for row in rows),
            "components": len(rows),
        },
        "findings": findings,
        "counts": counts,
        "truncated": False,
        "dropped_findings": 0,
        "ok": counts["error"] == 0,
    }

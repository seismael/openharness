"""Lockfile construction and drift comparison.

A lock records exactly what the harness was when it was accepted: the
fingerprint, every component's files with their hashes and token estimates, and
the hashes of the declarations the audit composes with. Drift is therefore a
content question, never a timestamp or an environment question.
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from . import __version__, jsonio
from .digest import sha256_file
from .manifest import estimate_tokens, measure
from .schemas import LOCK

DECLARATION_NAMES = ("policy", "cases", "requirements")
DEFAULT_DECLARATIONS = {
    "policy": "policy.json",
    "cases": "cases.json",
    "requirements": "requirements.json",
}


def _display(path: Path, base: Path) -> str:
    """Manifest-relative POSIX path; an absolute path is never recorded."""
    try:
        return Path(os.path.relpath(path.resolve(), base)).as_posix()
    except ValueError:
        return path.name


def _file_records(
    root: Path,
    paths: list[str],
    stats: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for relative in sorted(paths):
        measured = (stats or {}).get(relative)
        if measured is not None:
            records.append(
                {
                    "path": relative,
                    "sha256": measured["sha256"],
                    "tokens": measured["tokens"],
                }
            )
            continue
        path = root / relative
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue
        records.append(
            {
                "path": relative,
                "sha256": sha256_file(path),
                "tokens": estimate_tokens(text),
            }
        )
    return records


def component_records(
    receipt: Mapping[str, Any],
    stats: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Turn audit rows into lock components with per-file identity.

    ``stats`` is the measurement pass that produced the receipt; when present it
    removes the second read of every file.
    """
    root = Path(str(receipt["root"]))
    records: list[dict[str, Any]] = []
    for row in receipt["components"]:
        records.append(
            {
                "id": row["id"],
                "kind": row["kind"],
                "enabled": row["enabled"],
                "always_on": row["always_on"],
                "tokens": row["tokens"],
                "files": _file_records(root, list(row["files"]), stats),
            }
        )
    return records


def declaration_records(
    manifest_path: str | Path, overrides: Mapping[str, str | None] | None = None
) -> dict[str, dict[str, str]]:
    """Hash the declarations that shape the audit, when they exist."""
    base = Path(manifest_path).resolve().parent
    chosen = dict(DEFAULT_DECLARATIONS)
    for name, value in (overrides or {}).items():
        if name in chosen and value:
            chosen[name] = value
    records: dict[str, dict[str, str]] = {}
    for name, relative in chosen.items():
        path = base / relative
        if not path.is_file():
            continue
        records[name] = {"path": _display(path, base), "sha256": sha256_file(path)}
    return records


def build_lock(
    manifest: Mapping[str, Any],
    manifest_path: str | Path,
    overrides: Mapping[str, str | None] | None = None,
    measured: tuple[Mapping[str, Any], Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Compute the lock document for the current state.

    ``measured`` is an existing ``(receipt, stats)`` pair from :func:`measure`,
    so a caller that already measured the tree does not read it again.
    """
    receipt: Mapping[str, Any]
    stats: Mapping[str, Any]
    if measured is None:
        receipt, stats = measure(dict(manifest), manifest_path)
    else:
        receipt, stats = measured
    return {
        "schema": LOCK,
        "manifest": receipt["manifest"],
        "fingerprint": receipt["fingerprint"],
        "budget": dict(sorted(dict(manifest.get("budget", {})).items())),
        "totals": receipt["totals"],
        "components": component_records(receipt, stats),
        "declarations": declaration_records(manifest_path, overrides),
        "generator": {"name": "openharness", "version": __version__},
    }


def load_lock(path: str | Path) -> dict[str, Any]:
    """Read and minimally validate a lock document."""
    from .errors import DeclarationError

    document = jsonio.read_json(path, "lock")
    if not isinstance(document, dict):
        raise DeclarationError("lock must be a JSON object")
    if document.get("schema") != LOCK:
        raise DeclarationError(f"lock schema must be {LOCK}")
    for key in ("fingerprint", "components", "declarations"):
        if key not in document:
            raise DeclarationError(f"lock is missing '{key}'")
    return document


def compare(locked: Mapping[str, Any], actual: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return the ordered list of content changes between lock and state."""
    changes: list[dict[str, Any]] = []
    locked_components = {item["id"]: item for item in locked.get("components", [])}
    actual_components = {item["id"]: item for item in actual.get("components", [])}

    for component_id in sorted(set(locked_components) | set(actual_components)):
        before = locked_components.get(component_id)
        after = actual_components.get(component_id)
        if before is None:
            assert after is not None
            changes.append(
                {
                    "change": "component-added",
                    "component": component_id,
                    "path": None,
                    "tokens_before": None,
                    "tokens_after": after.get("tokens", 0),
                }
            )
            continue
        if after is None:
            changes.append(
                {
                    "change": "component-removed",
                    "component": component_id,
                    "path": None,
                    "tokens_before": before.get("tokens", 0),
                    "tokens_after": None,
                }
            )
            continue
        before_files = {item["path"]: item for item in before.get("files", [])}
        after_files = {item["path"]: item for item in after.get("files", [])}
        for path in sorted(set(before_files) | set(after_files)):
            old = before_files.get(path)
            new = after_files.get(path)
            if old is None and new is not None:
                changes.append(
                    {
                        "change": "added",
                        "component": component_id,
                        "path": path,
                        "tokens_before": None,
                        "tokens_after": new.get("tokens"),
                    }
                )
            elif new is None and old is not None:
                changes.append(
                    {
                        "change": "removed",
                        "component": component_id,
                        "path": path,
                        "tokens_before": old.get("tokens"),
                        "tokens_after": None,
                    }
                )
            elif old is not None and new is not None and old.get("sha256") != new.get("sha256"):
                changes.append(
                    {
                        "change": "modified",
                        "component": component_id,
                        "path": path,
                        "tokens_before": old.get("tokens"),
                        "tokens_after": new.get("tokens"),
                    }
                )

    before_declarations = locked.get("declarations", {})
    after_declarations = actual.get("declarations", {})
    for name in sorted(set(before_declarations) | set(after_declarations)):
        old = before_declarations.get(name)
        new = after_declarations.get(name)
        if old == new:
            continue
        changes.append(
            {
                "change": "declaration",
                "component": None,
                "path": (new or old or {}).get("path", name),
                "tokens_before": None,
                "tokens_after": None,
                "declaration": name,
            }
        )
    return changes


def summarize(
    locked: Mapping[str, Any], actual: Mapping[str, Any], changes: list[dict[str, Any]]
) -> dict[str, Any]:
    counts = {name: 0 for name in ("added", "removed", "modified", "declaration")}
    for item in changes:
        key = item["change"]
        if key in counts:
            counts[key] += 1
    return {
        "fingerprint_before": locked.get("fingerprint"),
        "fingerprint_after": actual.get("fingerprint"),
        "changes": len(changes),
        **counts,
        "drift": bool(changes) or locked.get("fingerprint") != actual.get("fingerprint"),
    }


def token_delta(change: Mapping[str, Any]) -> int:
    before = change.get("tokens_before") or 0
    after = change.get("tokens_after") or 0
    return int(after) - int(before)

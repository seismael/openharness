"""Canonical JSON, bounded emission, and deterministic file access.

Two serializations exist on purpose: ``compact`` is the canonical receipt form
(sorted keys, no whitespace), and ``pretty`` is the reviewable form used for
lockfiles and reports. Nothing here reads the clock, the environment, or the
network.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from .errors import OpenHarnessError

MAX_BYTES = 2500

Reducer = Callable[[dict[str, Any]], dict[str, Any]]


def compact(payload: Mapping[str, Any]) -> str:
    """Canonical receipt serialization."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def spaced(payload: Mapping[str, Any]) -> str:
    """Sorted serialization with default separators, used by error receipts."""
    return json.dumps(payload, sort_keys=True)


def pretty(payload: Mapping[str, Any]) -> str:
    """Reviewable serialization for files that humans edit or diff."""
    return json.dumps(payload, indent=2, sort_keys=True)


def byte_size(text: str) -> int:
    return len(text.encode("utf-8"))


def bounded(payload: dict[str, Any], reducers: Sequence[Reducer] = ()) -> str:
    """Return canonical JSON capped at 2500 bytes.

    Each reducer maps the full payload to a smaller projection. The first
    projection that fits wins; if none fits, the last projection is returned so
    the verdict is always present.
    """
    text = compact(payload)
    if byte_size(text) <= MAX_BYTES:
        return text
    for reduce in reducers:
        text = compact(reduce(payload))
        if byte_size(text) <= MAX_BYTES:
            return text
    return text


def read_json(path: str | Path, label: str = "document") -> Any:
    """Read a JSON document, raising a usage error with a stable message."""
    try:
        raw = Path(path).read_text(encoding="utf-8-sig")
    except OSError as error:
        raise OpenHarnessError(f"cannot read {label}: {error}") from error
    try:
        return json.loads(raw)
    except json.JSONDecodeError as error:
        raise OpenHarnessError(f"{label} is not valid JSON: {error}") from error


def load_jsonl(
    path: str | Path, label: str = "journal"
) -> tuple[list[dict[str, Any]] | None, str | None]:
    """Return ``(entries, error)`` for a JSON Lines ledger."""
    try:
        text = Path(path).read_text(encoding="utf-8-sig")
    except OSError as error:
        return None, f"cannot read {label}: {error}"
    entries: list[dict[str, Any]] = []
    for number, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            return None, f"line {number} is not valid JSON: {error}"
        if not isinstance(value, dict):
            return None, f"line {number} is not a JSON object"
        entries.append(value)
    return entries, None


def write_text(path: str | Path, text: str) -> Path:
    """Write UTF-8 text with LF endings, creating parent directories."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    temporary.replace(target)
    return target

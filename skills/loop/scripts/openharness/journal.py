"""Reading the iteration journal, shared by verify, telemetry, and failures."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .jsonio import load_jsonl


def load_entries(path: str | Path) -> tuple[list[dict[str, Any]] | None, str | None]:
    """Return ``(entries, error)`` for a journal file."""
    return load_jsonl(path, "journal")


def number(value: Any) -> int | float | None:
    """Return a usable number, or None for booleans and non-numbers."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value

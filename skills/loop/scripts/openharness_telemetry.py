#!/usr/bin/env python3
"""Compatibility shim for the packaged OpenHarness telemetry command."""

from __future__ import annotations

import sys

from openharness.commands.telemetry import (
    COST_KEYS,
    bounded,
    configure,
    gain,
    main,
    summarize,
)
from openharness.journal import load_entries, number

__all__ = [
    "COST_KEYS",
    "bounded",
    "configure",
    "gain",
    "load_entries",
    "main",
    "number",
    "summarize",
]

if __name__ == "__main__":
    sys.exit(main())

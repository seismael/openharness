#!/usr/bin/env python3
"""Compatibility shim for the packaged OpenHarness select command."""

from __future__ import annotations

import sys

from openharness.commands.select import (
    anonymize,
    bounded,
    configure,
    discover,
    main,
    receipts_present,
)

__all__ = [
    "anonymize",
    "bounded",
    "configure",
    "discover",
    "main",
    "receipts_present",
]

if __name__ == "__main__":
    sys.exit(main())

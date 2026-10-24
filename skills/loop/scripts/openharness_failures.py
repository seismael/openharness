#!/usr/bin/env python3
"""Compatibility shim for the packaged OpenHarness failures command."""

from __future__ import annotations

import sys

from openharness.commands.failures import CLASSES, bounded, classify, configure, main
from openharness.journal import load_entries

__all__ = ["CLASSES", "bounded", "classify", "configure", "load_entries", "main"]

if __name__ == "__main__":
    sys.exit(main())

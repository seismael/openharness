#!/usr/bin/env python3
"""Portable entry point for an installed skill that has no console script.

Usage: ``python <skill>/scripts/openharness_cli.py <command> [options]``.
"""

from __future__ import annotations

import sys

from openharness.cli import main

if __name__ == "__main__":
    sys.exit(main())

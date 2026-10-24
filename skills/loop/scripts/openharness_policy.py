#!/usr/bin/env python3
"""Compatibility shim for the packaged OpenHarness policy command."""

from __future__ import annotations

import sys

from openharness.commands.policy import (
    CONTRACT,
    PolicyError,
    bounded,
    configure,
    evaluate,
    load_policy,
    main,
    matches,
)

__all__ = [
    "CONTRACT",
    "PolicyError",
    "bounded",
    "configure",
    "evaluate",
    "load_policy",
    "main",
    "matches",
]

if __name__ == "__main__":
    sys.exit(main())

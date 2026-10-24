#!/usr/bin/env python3
"""Compatibility shim for the packaged OpenHarness verify command."""

from __future__ import annotations

import sys

from openharness.commands.verify import (
    ADOPTING,
    CONTRASTS,
    DECISIONS,
    SCOPES,
    bounded,
    configure,
    delta_verdict,
    main,
    verify,
)
from openharness.journal import load_entries

__all__ = [
    "ADOPTING",
    "CONTRASTS",
    "DECISIONS",
    "SCOPES",
    "bounded",
    "configure",
    "delta_verdict",
    "load_entries",
    "main",
    "verify",
]

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Compatibility shim for the packaged OpenHarness inventory command."""

from __future__ import annotations

import sys

from openharness.commands.inventory import (
    InventoryError,
    bounded,
    build,
    configure,
    gaps,
    inventory,
    load_requirements,
    main,
)
from openharness.manifest import audit, load_manifest

__all__ = [
    "InventoryError",
    "audit",
    "bounded",
    "build",
    "configure",
    "gaps",
    "inventory",
    "load_manifest",
    "load_requirements",
    "main",
]

if __name__ == "__main__":
    sys.exit(main())

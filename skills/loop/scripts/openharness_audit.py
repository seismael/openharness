#!/usr/bin/env python3
"""Compatibility shim for the packaged OpenHarness audit command.

The implementation lives in ``openharness.commands.audit``. This path is kept so
an installed skill and existing automation keep working until 2.0.
"""

from __future__ import annotations

import sys

from openharness.commands.audit import (
    MAX_RECEIPT_BYTES,
    audit,
    configure,
    load_manifest,
    main,
    serialize,
)
from openharness.manifest import (
    KINDS,
    MANIFEST_SCHEMA,
    RECEIPT_SCHEMA,
    estimate_tokens,
    matched_files,
    state_fingerprint,
)
from openharness.schemas import MANIFEST, RECEIPT

__all__ = [
    "KINDS",
    "MANIFEST",
    "MANIFEST_SCHEMA",
    "MAX_RECEIPT_BYTES",
    "RECEIPT",
    "RECEIPT_SCHEMA",
    "audit",
    "configure",
    "estimate_tokens",
    "load_manifest",
    "main",
    "matched_files",
    "serialize",
    "state_fingerprint",
]

if __name__ == "__main__":
    sys.exit(main())

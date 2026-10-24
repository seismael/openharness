#!/usr/bin/env python3
"""Compatibility shim for the packaged OpenHarness cases command."""

from __future__ import annotations

import sys

from openharness.commands.cases import (
    CONTRACT,
    DEFAULT_TIMEOUT,
    MAX_TIMEOUT,
    RECEIPT_SCHEMA,
    CaseError,
    bounded,
    configure,
    evaluate,
    execute_cases,
    load_cases,
    main,
    run,
    validate,
    validate_case,
)

__all__ = [
    "CONTRACT",
    "DEFAULT_TIMEOUT",
    "MAX_TIMEOUT",
    "RECEIPT_SCHEMA",
    "CaseError",
    "bounded",
    "configure",
    "evaluate",
    "execute_cases",
    "load_cases",
    "main",
    "run",
    "validate",
    "validate_case",
]

if __name__ == "__main__":
    sys.exit(main())

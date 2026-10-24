"""The ``openharness`` command line.

One binary, one exit-code contract: ``0`` clean, ``1`` findings or drift, ``2``
usage or invalid input, ``3`` ask. Commands share primitives but never share a
verdict: each one prints its own bounded receipt.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

from . import __version__
from .commands import (
    audit,
    cases,
    context,
    failures,
    init,
    inventory,
    lock,
    plan,
    policy,
    report,
    select,
    telemetry,
    verify,
)
from .errors import EXIT_USAGE

COMMANDS = (
    ("init", init),
    ("lock", lock),
    ("plan", plan),
    ("audit", audit),
    ("context", context),
    ("verify", verify),
    ("select", select),
    ("cases", cases),
    ("telemetry", telemetry),
    ("inventory", inventory),
    ("failures", failures),
    ("policy", policy),
    ("report", report),
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="openharness",
        description="Deterministic control plane for agent harnesses.",
    )
    parser.add_argument("--version", action="version", version=f"openharness {__version__}")
    subparsers = parser.add_subparsers(dest="subcommand", metavar="command")
    for name, module in COMMANDS:
        subparser = subparsers.add_parser(name, help=module.HELP, description=module.DESCRIPTION)
        module.configure(subparser)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args: Any = parser.parse_args(argv)
    if not args.subcommand:
        parser.print_help(sys.stderr)
        return EXIT_USAGE
    for name, module in COMMANDS:
        if name == args.subcommand:
            return module.run(args)
    parser.error(f"unknown command: {args.subcommand}")
    return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())

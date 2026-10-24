"""Record or verify the harness lockfile (RFC-0016)."""

from __future__ import annotations

import argparse
from typing import Any

from .. import jsonio
from ..drift import build_lock, compare, load_lock, summarize
from ..errors import EXIT_FINDINGS, EXIT_OK, EXIT_USAGE, OpenHarnessError
from ..manifest import require_manifest
from ..schemas import LOCK_RECEIPT

HELP = "record or verify the harness lockfile"
DESCRIPTION = "Record or verify the harness lockfile (harness.lock)."

DEFAULT_LOCK = "harness.lock"


def _receipt(
    lock_path: str,
    lock: dict[str, Any],
    *,
    written: bool,
    match: bool | None = None,
    changes: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    components = lock.get("components", [])
    payload: dict[str, Any] = {
        "schema": LOCK_RECEIPT,
        "ok": True,
        "lock": lock_path.replace("\\", "/"),
        "manifest": lock.get("manifest"),
        "fingerprint": lock.get("fingerprint"),
        "components": len(components),
        "files": sum(len(item.get("files", [])) for item in components),
        "tokens": lock.get("totals", {}).get("total_tokens", 0),
        "written": written,
    }
    if match is not None:
        payload["match"] = match
        payload["drift"] = len(changes or [])
        payload["ok"] = match
    return payload


def _shrink(payload: dict[str, Any]) -> dict[str, Any]:
    return {key: payload[key] for key in payload if key != "component_ids"}


def configure(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--manifest",
        default="harness.json",
        help="Path to harness.manifest.v1 (default: harness.json)",
    )
    parser.add_argument(
        "--output", default=DEFAULT_LOCK, help="Lockfile path (default: harness.lock)"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Compare the current state with the lock; exit 1 on drift",
    )
    parser.add_argument("--policy", help="Path to the policy declaration to hash")
    parser.add_argument("--cases", help="Path to the cases declaration to hash")
    parser.add_argument("--requirements", help="Path to the requirements declaration to hash")


def run(args: argparse.Namespace) -> int:
    try:
        manifest = require_manifest(args.manifest)
        overrides = {
            "policy": args.policy,
            "cases": args.cases,
            "requirements": args.requirements,
        }
        actual = build_lock(manifest, args.manifest, overrides)

        if not args.check:
            jsonio.write_text(args.output, jsonio.pretty(actual) + "\n")
            print(jsonio.bounded(_receipt(args.output, actual, written=True), [_shrink]))
            return EXIT_OK

        locked = load_lock(args.output)
        changes = compare(locked, actual)
        state = summarize(locked, actual, changes)
        payload = _receipt(
            args.output,
            actual,
            written=False,
            match=not state["drift"],
            changes=changes,
        )
        if changes:
            payload["changes"] = changes[:24]
            payload["component_ids"] = sorted(
                {item["component"] for item in changes if item.get("component")}
            )
        print(jsonio.bounded(payload, [_shrink]))
        return EXIT_OK if payload["match"] else EXIT_FINDINGS
    except OpenHarnessError as error:
        print(jsonio.spaced({"schema": LOCK_RECEIPT, "ok": False, "error": error.message}))
        return EXIT_USAGE


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    configure(parser)
    return run(parser.parse_args(argv))

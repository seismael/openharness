"""Explain drift between the lockfile and the current harness state (RFC-0016)."""

from __future__ import annotations

import argparse
from typing import Any

from .. import jsonio
from ..drift import build_lock, compare, load_lock, summarize, token_delta
from ..errors import EXIT_FINDINGS, EXIT_OK, EXIT_USAGE, OpenHarnessError
from ..manifest import require_manifest
from ..schemas import PLAN

HELP = "explain drift between the lockfile and the harness"
DESCRIPTION = "Explain drift between the harness lockfile and the current state."

MARKS = {
    "added": "+",
    "removed": "-",
    "modified": "~",
    "declaration": "~",
    "component-added": "+",
    "component-removed": "-",
}


def format_text(
    manifest_name: str,
    lock_path: str,
    state: dict[str, Any],
    changes: list[dict[str, Any]],
) -> str:
    lines = [
        f"openharness plan: {manifest_name}",
        f"lock: {lock_path}",
        f"fingerprint: locked {state['fingerprint_before']} actual {state['fingerprint_after']}",
    ]
    if not changes:
        lines.append("no drift")
        return "\n".join(lines)

    for item in changes:
        mark = MARKS.get(item["change"], "?")
        if item["change"] == "declaration":
            lines.append(f"{mark} {item['path']} (declaration: {item.get('declaration')})")
            continue
        if item["path"] is None:
            delta = token_delta(item)
            lines.append(f"{mark} component {item['component']} ({delta:+d} tokens)")
            continue
        delta = token_delta(item)
        suffix = f" {delta:+d} tokens"
        lines.append(f"{mark} {item['path']} ({item['component']}){suffix}")

    components = {item["component"] for item in changes if item.get("component")}
    lines.append(f"drift: {len(changes)} change(s) across {len(components)} component(s)")
    return "\n".join(lines)


def configure(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--manifest",
        default="harness.json",
        help="Path to harness.manifest.v1 (default: harness.json)",
    )
    parser.add_argument(
        "--lock", default="harness.lock", help="Lockfile path (default: harness.lock)"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 when the state differs from the lock",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument("--policy", help="Path to the policy declaration to hash")
    parser.add_argument("--cases", help="Path to the cases declaration to hash")
    parser.add_argument("--requirements", help="Path to the requirements declaration to hash")


def _shrink(payload: dict[str, Any]) -> dict[str, Any]:
    trimmed = dict(payload)
    trimmed["changes"] = trimmed.get("changes", [])[:24]
    trimmed["truncated"] = True
    return trimmed


def run(args: argparse.Namespace) -> int:
    try:
        manifest = require_manifest(args.manifest)
        overrides = {
            "policy": args.policy,
            "cases": args.cases,
            "requirements": args.requirements,
        }
        actual = build_lock(manifest, args.manifest, overrides)
        locked = load_lock(args.lock)
    except OpenHarnessError as error:
        print(jsonio.spaced({"schema": PLAN, "ok": False, "error": error.message}))
        return EXIT_USAGE

    changes = compare(locked, actual)
    state = summarize(locked, actual, changes)
    drift = bool(state["drift"])

    if args.format == "json":
        payload = {
            "schema": PLAN,
            "ok": not drift,
            "manifest": actual.get("manifest"),
            "lock": args.lock.replace("\\", "/"),
            "fingerprint": {
                "locked": state["fingerprint_before"],
                "actual": state["fingerprint_after"],
            },
            "changes": changes,
            "summary": {
                "changes": state["changes"],
                "added": state["added"],
                "removed": state["removed"],
                "modified": state["modified"],
                "declarations": state["declaration"],
                "drift": drift,
            },
        }
        print(jsonio.bounded(payload, [_shrink]))
    else:
        print(format_text(str(actual.get("manifest")), args.lock, state, changes))

    if args.check and drift:
        return EXIT_FINDINGS
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    configure(parser)
    return run(parser.parse_args(argv))

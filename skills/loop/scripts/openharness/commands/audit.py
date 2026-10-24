"""Audit a declared harness surface (RFC-0009)."""

from __future__ import annotations

import argparse
import json
from typing import Any

from .. import jsonio
from ..errors import EXIT_FINDINGS, EXIT_OK, EXIT_USAGE
from ..manifest import MAX_RECEIPT_BYTES, audit, load_manifest
from ..schemas import RECEIPT

HELP = "audit a harness surface"
DESCRIPTION = "Audit an agent harness surface."


def configure(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--manifest", required=True, help="Path to a harness.manifest.v1 JSON file")
    parser.add_argument(
        "--fingerprint-only",
        action="store_true",
        help="Print only the harness state fingerprint (cheap identity check)",
    )


def serialize(receipt: dict[str, Any]) -> str:
    """Emit the smallest receipt that still reports the verdict, capped at 2500 bytes."""
    payload = jsonio.compact(receipt)
    if jsonio.byte_size(payload) <= MAX_RECEIPT_BYTES:
        return payload
    findings = receipt["findings"]
    while len(findings) > 1:
        findings.pop()
        receipt["dropped_findings"] += 1
        receipt["truncated"] = True
        payload = jsonio.compact(receipt)
        if jsonio.byte_size(payload) <= MAX_RECEIPT_BYTES:
            return payload
    minimal = {
        "schema": receipt["schema"],
        "manifest": receipt["manifest"],
        "fingerprint": receipt["fingerprint"],
        "totals": receipt["totals"],
        "counts": receipt["counts"],
        "truncated": True,
        "dropped_findings": len(receipt["findings"]) + receipt["dropped_findings"],
        "ok": receipt["ok"],
    }
    return jsonio.compact(minimal)


def run(args: argparse.Namespace) -> int:
    manifest, error = load_manifest(args.manifest)
    if error is not None:
        print(jsonio.spaced({"schema": RECEIPT, "ok": False, "error": error}))
        return EXIT_USAGE

    assert manifest is not None
    receipt = audit(manifest, args.manifest)
    if args.fingerprint_only:
        print(json.dumps({"fingerprint": receipt["fingerprint"]}, sort_keys=True))
        return EXIT_OK

    payload = serialize(receipt)
    print(payload)
    parsed = json.loads(payload)
    return EXIT_OK if parsed.get("ok") else EXIT_FINDINGS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    configure(parser)
    return run(parser.parse_args(argv))

"""Budget a harness surface into resident, loadable, and executable context (RFC-0017).

The audit answers *what is wrong*. This command answers *what does the surface
cost*, split by the way a host spends it: tokens every session pays, tokens paid
only when a component is loaded, and executable code that never enters the
context window. Every number comes from the same measurement pass as the audit,
so the split cannot disagree with the receipt.
"""

from __future__ import annotations

import argparse
from typing import Any

from .. import jsonio
from ..errors import EXIT_FINDINGS, EXIT_OK, EXIT_USAGE
from ..manifest import load_manifest, measure
from ..schemas import CONTEXT

HELP = "budget resident, loadable, and executable context"
DESCRIPTION = "Split harness tokens by context layer and check declared budgets."

LAYERS = ("resident", "loadable", "executable")
EXECUTABLE_KINDS = ("scripts", "plugins")
DEFAULT_TOP = 8
TEXT_TOP = 5


def layer_of(kind: str, always_on: bool) -> str:
    """Resident is always on; executable never enters context; the rest is loadable."""
    if always_on:
        return "resident"
    if kind in EXECUTABLE_KINDS:
        return "executable"
    return "loadable"


def _share(tokens: int, total: int) -> int:
    if total <= 0:
        return 0
    return round(100 * tokens / total)


def build(
    manifest: dict[str, Any], receipt: dict[str, Any], top: int = DEFAULT_TOP
) -> dict[str, Any]:
    """Compose the context budget from an audit receipt."""
    totals = {layer: 0 for layer in LAYERS}
    kinds: dict[str, dict[str, Any]] = {}
    entries: list[dict[str, Any]] = []

    for component in receipt["components"]:
        if not component["enabled"]:
            continue
        layer = layer_of(component["kind"], component["always_on"])
        tokens = int(component["tokens"])
        totals[layer] += tokens
        row = kinds.setdefault(
            component["kind"],
            {"kind": component["kind"], "components": 0, "tokens": 0, "resident": 0},
        )
        row["components"] += 1
        row["tokens"] += tokens
        row["resident"] += tokens if layer == "resident" else 0
        entries.append(
            {
                "id": component["id"],
                "kind": component["kind"],
                "layer": layer,
                "tokens": tokens,
            }
        )

    total = sum(totals.values())
    ordered = sorted(entries, key=lambda item: (-item["tokens"], item["id"]))
    largest = [
        {**entry, "share": _share(entry["tokens"], total)}
        for entry in ordered[:top]
        if entry["tokens"] > 0
    ]
    levers = [
        {
            "action": "trim" if entry["layer"] == "resident" else "defer",
            "component": entry["id"],
            "tokens": entry["tokens"],
            "share": _share(entry["tokens"], total),
        }
        for entry in ordered
        if entry["tokens"] > 0
    ]

    budget: dict[str, dict[str, Any]] = {}
    declared = manifest.get("budget", {})
    for name, layer_tokens in (
        ("always_on_tokens", totals["resident"]),
        ("total_tokens", total),
    ):
        limit = declared.get(name)
        if limit is None:
            continue
        budget[name] = {
            "limit": limit,
            "actual": layer_tokens,
            "headroom": limit - layer_tokens,
            "ok": layer_tokens <= limit,
        }

    return {
        "schema": CONTEXT,
        "manifest": receipt["manifest"],
        "fingerprint": receipt["fingerprint"],
        "tokens": {**totals, "total": total},
        "components": len(entries),
        "kinds": [kinds[kind] for kind in sorted(kinds)],
        "largest": largest,
        "levers": levers,
        "budget": budget,
        "truncated": False,
        "ok": all(item["ok"] for item in budget.values()),
    }


def _reduce(payload: dict[str, Any]) -> dict[str, Any]:
    trimmed = dict(payload)
    trimmed["kinds"] = trimmed.get("kinds", [])[:6]
    trimmed["largest"] = trimmed.get("largest", [])[:5]
    trimmed["levers"] = trimmed.get("levers", [])[:5]
    trimmed["truncated"] = True
    return trimmed


def _minimal(payload: dict[str, Any]) -> dict[str, Any]:
    """Last-resort projection that still validates against the context schema."""
    return {
        "schema": payload["schema"],
        "manifest": payload["manifest"],
        "fingerprint": payload["fingerprint"],
        "tokens": payload["tokens"],
        "components": payload["components"],
        "kinds": [],
        "largest": [],
        "levers": [],
        "budget": payload["budget"],
        "truncated": True,
        "ok": payload["ok"],
    }


def bounded(payload: dict[str, Any]) -> str:
    return jsonio.bounded(payload, (_reduce, _minimal))


def render_text(payload: dict[str, Any]) -> str:
    """Human-readable projection; still deterministic and byte-capped."""
    tokens = payload["tokens"]
    lines = [
        f"openharness context: {payload['manifest']}",
        f"fingerprint {payload['fingerprint'][:16]}",
    ]
    for layer in LAYERS:
        lines.append(f"{layer:<11} {tokens[layer]:>8} tokens")
    lines.append(f"{'total':<11} {tokens['total']:>8} tokens")
    for name, item in payload["budget"].items():
        verdict = "ok" if item["ok"] else "OVER"
        lines.append(
            f"budget {name}: {item['actual']}/{item['limit']} "
            f"({item['headroom']} headroom, {verdict})"
        )
    largest = payload.get("largest", [])[:TEXT_TOP]
    if largest:
        lines.append("largest:")
        for item in largest:
            lines.append(f"  {item['id']} [{item['layer']}] {item['tokens']} ({item['share']}%)")
    text = "\n".join(lines) + "\n"
    while jsonio.byte_size(text) > jsonio.MAX_BYTES and len(lines) > 1:
        lines.pop()
        text = "\n".join(lines) + "\n"
    return text


def configure(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--manifest",
        default="harness.json",
        help="Path to harness.manifest.v1 (default: harness.json)",
    )
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="json",
        help="Output form (default: json)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=DEFAULT_TOP,
        help=f"Largest components to list (default: {DEFAULT_TOP})",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 1 when a declared budget is exceeded",
    )


def run(args: argparse.Namespace) -> int:
    if args.top < 1 or args.top > 100:
        print(jsonio.spaced({"schema": CONTEXT, "ok": False, "error": "--top must be 1..100"}))
        return EXIT_USAGE
    manifest, error = load_manifest(args.manifest)
    if error is not None:
        print(jsonio.spaced({"schema": CONTEXT, "ok": False, "error": error}))
        return EXIT_USAGE
    assert manifest is not None

    receipt, _ = measure(manifest, args.manifest)

    payload = build(manifest, receipt, args.top)
    if args.format == "text":
        print(render_text(payload), end="")
    else:
        print(bounded(payload))
    if args.check and not payload["ok"]:
        return EXIT_FINDINGS
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    configure(parser)
    return run(parser.parse_args(argv))

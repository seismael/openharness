"""Discover an existing harness and declare it (zero-config bootstrap)."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from .. import jsonio
from ..drift import build_lock
from ..errors import EXIT_FINDINGS, EXIT_OK, OpenHarnessError
from ..manifest import audit
from ..schemas import INIT

HELP = "discover a harness and write its declaration"
DESCRIPTION = "Discover the agent surfaces in a repository and write harness.json."

RULES: tuple[tuple[str, str, tuple[str, ...], bool], ...] = (
    (
        "agents",
        "system_prompt",
        (
            "AGENTS.md",
            "CLAUDE.md",
            "GEMINI.md",
            ".github/copilot-instructions.md",
        ),
        True,
    ),
    ("readme", "system_prompt", ("README.md",), False),
    (
        "rules",
        "tool_guidance",
        (
            ".cursor/rules/*.mdc",
            ".cursor/rules/*.md",
            ".github/instructions/*.instructions.md",
        ),
        False,
    ),
    (
        "commands",
        "tool_guidance",
        (
            ".opencode/commands/*.md",
            ".claude/commands/*.md",
            ".agents/commands/*.md",
        ),
        False,
    ),
    (
        "skills",
        "skills",
        (
            "skills/*/SKILL.md",
            ".claude/skills/*/SKILL.md",
            ".opencode/skills/*/SKILL.md",
            ".agents/skills/*/SKILL.md",
        ),
        False,
    ),
    (
        "subagents",
        "subagents",
        (
            ".opencode/agents/*.md",
            ".opencode/agent/*.md",
            ".claude/agents/*.md",
            ".agents/agents/*.md",
        ),
        False,
    ),
    ("scripts", "scripts", ("scripts/*.py", "tools/*.py"), False),
    ("plugins", "plugins", ("tools/mcp_server.py", ".mcp.json", "mcp.json"), False),
    ("guardrails", "guardrails", ("policy.json",), False),
    (
        "memory",
        "memory",
        ("MEMORY.md", ".agents/memory/*.md", ".opencode/memory/*.md"),
        False,
    ),
)


def _round_up(value: int, step: int) -> int:
    return ((value + step - 1) // step) * step


def discover(root: Path) -> list[dict[str, Any]]:
    """Return manifest components for every declared surface that exists."""
    components: list[dict[str, Any]] = []
    for identifier, kind, patterns, always_on in RULES:
        matched: list[str] = []
        for pattern in patterns:
            for candidate in sorted(root.glob(pattern)):
                if not candidate.is_file():
                    continue
                relative = candidate.relative_to(root).as_posix()
                if relative not in matched:
                    matched.append(relative)
        if not matched:
            continue
        component: dict[str, Any] = {
            "id": identifier,
            "kind": kind,
            "paths": matched,
        }
        if always_on:
            component["always_on"] = True
        components.append(component)
    return components


def build_manifest(
    name: str, components: list[dict[str, Any]], budget: dict[str, int]
) -> dict[str, Any]:
    return {
        "schema": "harness.manifest.v1",
        "name": name,
        "root": ".",
        "budget": budget,
        "components": components,
    }


def configure(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", default=".", help="Repository root to discover (default: .)")
    parser.add_argument("--name", help="Manifest name (default: the root directory name)")
    parser.add_argument(
        "--manifest",
        default="harness.json",
        help="Manifest path to write (default: harness.json)",
    )
    parser.add_argument(
        "--lock",
        default="harness.lock",
        help="Lockfile path to write (default: harness.lock)",
    )


def _shrink(payload: dict[str, Any]) -> dict[str, Any]:
    trimmed = dict(payload)
    trimmed["components"] = trimmed.get("components", [])[:8]
    trimmed["truncated"] = True
    return trimmed


def run(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    manifest_path = root / args.manifest
    lock_path = root / args.lock
    try:
        if not root.is_dir():
            raise OpenHarnessError(f"not a directory: {root}")
        if manifest_path.exists():
            raise OpenHarnessError(
                f"{args.manifest} already exists; run 'openharness lock' to refresh the lock",
                EXIT_FINDINGS,
            )

        components = discover(root)
        if not components:
            raise OpenHarnessError(
                "no agent harness surface found (looked for AGENTS.md, skills, commands, "
                "subagents, scripts, MCP, policy, and memory)",
                EXIT_FINDINGS,
            )

        name = args.name or root.name
        # Measure first, then budget with headroom so the first audit is honest.
        provisional = build_manifest(name, components, {})
        measured = audit(provisional, manifest_path)
        always_on = measured["totals"]["always_on_tokens"]
        total = measured["totals"]["total_tokens"]
        budget = {
            "always_on_tokens": max(2000, _round_up(int(always_on * 1.25), 500)),
            "total_tokens": max(10000, _round_up(int(total * 1.25), 5000)),
        }
        manifest = build_manifest(name, components, budget)

        jsonio.write_text(manifest_path, jsonio.pretty(manifest) + "\n")
        lock = build_lock(manifest, manifest_path)
        jsonio.write_text(lock_path, jsonio.pretty(lock) + "\n")
    except OpenHarnessError as error:
        print(jsonio.spaced({"schema": INIT, "ok": False, "error": error.message}))
        return error.exit_code

    payload = {
        "schema": INIT,
        "ok": True,
        "name": name,
        "manifest": args.manifest.replace("\\", "/"),
        "lock": args.lock.replace("\\", "/"),
        "fingerprint": lock["fingerprint"],
        "components": [
            {"id": item["id"], "kind": item["kind"], "files": len(item["files"])}
            for item in lock["components"]
        ],
        "files": measured["totals"]["files"],
        "tokens": {
            "always_on": measured["totals"]["always_on_tokens"],
            "total": measured["totals"]["total_tokens"],
        },
        "budget": budget,
        "next": [
            "openharness audit --manifest harness.json",
            "openharness plan --check",
        ],
    }
    print(jsonio.bounded(payload, [_shrink]))
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    configure(parser)
    return run(parser.parse_args(argv))

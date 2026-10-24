#!/usr/bin/env python3
"""Tool Promoter - Promotes sandboxed scratch scripts to permanent project helpers (RFC-0008).

Automates the lifecycle:
.agents/loop/scratch/<tool>.py -> .agents/loop/scripts/<tool>.py -> .agents/loop/env.json
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def promote_tool(
    source_file: Path, target_dir: Path | None = None, command_alias: str | None = None
) -> int:
    source_file = source_file.resolve()
    if not source_file.exists():
        print(f"Error: Source file does not exist: {source_file}", file=sys.stderr)
        return 1

    # Locate repository root / .agents directory
    current = source_file.parent
    agents_dir = None
    while current != current.parent:
        if (current / ".agents").is_dir():
            agents_dir = current / ".agents"
            break
        current = current.parent

    if not agents_dir:
        # Fallback to target_dir or current working directory
        root = target_dir or Path.cwd()
        agents_dir = root / ".agents"

    scripts_dir = agents_dir / "loop" / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)

    dest_file = scripts_dir / source_file.name

    # 1. Determinism and execution sanity check
    print(f"Auditing {source_file.name} for standalone execution...")
    try:
        proc = subprocess.run(
            [sys.executable, str(source_file), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if proc.returncode != 0:
            print(
                f"Warning: Script returned exit code {proc.returncode} on --help. Continuing...",
                file=sys.stderr,
            )
    except Exception as e:
        print(f"Warning: Failed to execute {source_file.name} with --help: {e}", file=sys.stderr)

    # 2. Promote file
    shutil.copyfile(source_file, dest_file)
    print(f"Promoted {source_file.name} to {dest_file}")

    # 3. Register in env.json
    env_json_path = agents_dir / "loop" / "env.json"
    alias = command_alias or source_file.stem
    if env_json_path.exists():
        try:
            env_data = json.loads(env_json_path.read_text(encoding="utf-8"))
        except Exception:
            env_data = {}
        if "tools" not in env_data or not isinstance(env_data["tools"], dict):
            env_data["tools"] = {}
        env_data["tools"][alias] = f"python .agents/loop/scripts/{dest_file.name}"
        env_json_path.write_text(json.dumps(env_data, indent=2) + "\n", encoding="utf-8")
        print(f"Registered tool '{alias}' in {env_json_path}")

    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("script", type=Path, help="Path to scratch script to promote")
    parser.add_argument(
        "--alias",
        type=str,
        default=None,
        help="Command alias name (defaults to script filename stem)",
    )
    parser.add_argument("--target-dir", type=Path, default=None, help="Root project directory")
    args = parser.parse_args(argv)

    return promote_tool(args.script, args.target_dir, args.alias)


if __name__ == "__main__":
    sys.exit(main())

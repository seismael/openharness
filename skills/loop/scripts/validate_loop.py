#!/usr/bin/env python3
"""Validate the integrity, schema conformance, and token bounds of a project's .loop and .agents."""

import argparse
import json
from pathlib import Path
import re
import sys

try:
    import yaml
except ImportError:
    yaml = None


def _parse_yaml_basic(text: str) -> dict:
    """Fallback parser for top-level YAML keys when PyYAML is not installed."""
    result = {}
    for line in text.splitlines():
        line = line.rstrip()
        if not line or line.strip().startswith("#"):
            continue
        # Match top-level keys: identifier followed by colon
        m = re.match(r"^([a-zA-Z0-9_\-\.]+)\s*:\s*(.*)$", line)
        if m:
            key = m.group(1).strip()
            val = m.group(2).strip()
            result[key] = val
    return result


def _load_yaml(text: str) -> dict:
    if yaml is not None:
        return yaml.safe_load(text)
    return _parse_yaml_basic(text)


def validate_loop(project_dir: Path) -> list[str]:
    errors = []
    agents_dir = project_dir / ".agents"

    # Resolve loop_dir: preferred canonical is .agents/loop, fallback is .loop
    if (agents_dir / "loop").is_dir():
        loop_dir = agents_dir / "loop"
    elif (project_dir / ".loop").is_dir():
        loop_dir = project_dir / ".loop"
    else:
        errors.append("Missing loop directory (expected .agents/loop or .loop)")
        return errors

    # Check env.json if present
    env_file = loop_dir / "env.json"
    if env_file.is_file():
        try:
            edata = json.loads(env_file.read_text(encoding="utf-8"))
            for req_key in ["python_bin", "test_cmd", "loop_dir"]:
                if req_key not in edata:
                    errors.append(f"{loop_dir.name}/env.json missing required key: '{req_key}'")
        except Exception as e:
            errors.append(f"{loop_dir.name}/env.json is invalid JSON: {e}")

    # Check loop.json
    loop_json_file = loop_dir / "loop.json"
    if not loop_json_file.is_file():
        errors.append(f"Missing {loop_dir.name}/loop.json")
    else:
        try:
            data = json.loads(loop_json_file.read_text(encoding="utf-8"))
            for key in ["target", "status"]:
                if key not in data:
                    errors.append(f"{loop_dir.name}/loop.json missing required key: '{key}'")
            status_val = data.get("status", "")
            valid_statuses = {"ACTIVE", "DONE", "STOPPED", "PAUSED", "BLOCKED", "in_progress", "completed", "blocked"}
            if status_val not in valid_statuses:
                errors.append(f"{loop_dir.name}/loop.json invalid status: {status_val}")
        except Exception as e:
            errors.append(f"{loop_dir.name}/loop.json is invalid JSON: {e}")

    # Check coverage.json
    coverage_file = loop_dir / "coverage.json"
    if not coverage_file.is_file():
        # Fallback check
        alt_coverage = project_dir / "docs" / "knowledge" / "coverage.json"
        if not alt_coverage.is_file():
            errors.append(f"Missing coverage ledger (expected {loop_dir.name}/coverage.json or docs/knowledge/coverage.json)")
    else:
        try:
            json.loads(coverage_file.read_text(encoding="utf-8"))
        except Exception as e:
            errors.append(f"{loop_dir.name}/coverage.json is invalid JSON: {e}")

    # Check profile.yaml
    profile_file = loop_dir / "knowledge" / "profile.yaml"
    if not profile_file.is_file():
        alt_profile = project_dir / "docs" / "knowledge" / "profile.yaml"
        if not alt_profile.is_file():
            errors.append(f"Missing profile.yaml (expected {loop_dir.name}/knowledge/profile.yaml or docs/knowledge/profile.yaml)")
        else:
            profile_file = alt_profile

    if profile_file.is_file():
        try:
            pdata = _load_yaml(profile_file.read_text(encoding="utf-8"))
            if not isinstance(pdata, dict):
                errors.append(f"{profile_file}: profile must be a YAML mapping")
            else:
                for req in ["schema", "project", "target", "metric", "paths", "boundaries", "pipeline", "gates", "completion"]:
                    if req not in pdata:
                        errors.append(f"{profile_file} missing required section: '{req}'")
        except Exception as e:
            errors.append(f"{profile_file} is invalid YAML: {e}")

    # Check index.md token bounds (< 400 words as bounded projection)
    index_file = loop_dir / "knowledge" / "index.md"
    if not index_file.is_file():
        alt_index = project_dir / "docs" / "knowledge" / "index.md"
        if alt_index.is_file():
            index_file = alt_index
    if index_file.is_file():
        text = index_file.read_text(encoding="utf-8")
        words = len(text.split())
        if words > 500:
            errors.append(f"{index_file} exceeds token bounds ({words} words > 500 words)")

    # Check root scratch contamination (INV-09 / AP-TOKEN-01)
    for p in project_dir.glob("_tmp_*.py"):
        errors.append(f"Root scratch contamination detected: {p.name} must be moved to {loop_dir.name}/scratch/")
    for p in project_dir.glob("scratch*.py"):
        errors.append(f"Root scratch contamination detected: {p.name} must be moved to {loop_dir.name}/scratch/")

    # Check .agents subagents if directory exists
    if agents_dir.is_dir():
        subagents_dir = agents_dir / "subagents"
        if subagents_dir.is_dir():
            for sf in subagents_dir.glob("*.yaml"):
                try:
                    sdata = _load_yaml(sf.read_text(encoding="utf-8"))
                    if not isinstance(sdata, dict) or "name" not in sdata or "role" not in sdata:
                        errors.append(f"{sf}: subagent persona must define 'name' and 'role'")
                except Exception as e:
                    errors.append(f"{sf}: invalid YAML: {e}")

    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd(), help="Target repository directory")
    args = parser.parse_args(argv)

    errors = validate_loop(args.project_dir.resolve())
    if errors:
        print(f"Validation FAILED for {args.project_dir}:", file=sys.stderr)
        for err in errors:
            print(f"- {err}", file=sys.stderr)
        return 1
    print(f"Validation PASSED for {args.project_dir}: standard .loop and .agents valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

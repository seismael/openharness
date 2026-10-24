#!/usr/bin/env python3
"""Deterministic validator for project knowledge bases (Obsidian/Markdown wikis).

Usage:
    python validate_knowledge.py <path_to_knowledge_dir>

Checks:
    - index.md exists and acts as Map of Content (MOC).
    - File size limits: index.md <= 2,048 bytes; top-level leaves <= 3,072 bytes.
      Sub-leaves (markdown in sub-folders) hold granular detail and are exempt.
    - Link integrity: all [target](path.md) and [[wikilinks]] resolve to a file
      anywhere in the knowledge base (Obsidian-style, so sub-leaf links work).
    - Orphan check: every top-level leaf must be linked from index.md.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

MAX_INDEX_BYTES = 2048
MAX_LEAF_BYTES = 3072

# Optional autonomous-loop artifacts (see the loop skill). Validated only if present.
LOOP_COVERAGE_SCHEMA = "loop.coverage.v1"
LOOP_PROFILE_SCHEMA = "loop.profile.v1"

MD_LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+\.md)(?:#[^)]+)?\)")
WIKI_LINK_PATTERN = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")


class KnowledgeValidationError(ValueError):
    """Validation failure in knowledge base structure."""


def extract_links(content: str) -> set[str]:
    """Extract referenced filenames from both markdown and wikilinks."""
    targets = set()
    for _, md_path in MD_LINK_PATTERN.findall(content):
        # Ignore external URLs
        if not (md_path.startswith("http://") or md_path.startswith("https://")):
            targets.add(Path(md_path).name)

    for wiki_target in WIKI_LINK_PATTERN.findall(content):
        name = wiki_target.strip()
        if not name.endswith(".md"):
            name = f"{name}.md"
        targets.add(name)

    return targets


def _load_json_object(path: Path, label: str, errors: list[str]) -> dict | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{label} is not valid JSON: {exc}")
        return None
    if not isinstance(payload, dict):
        errors.append(f"{label} must contain a JSON object at the top level")
        return None
    return payload


def validate_loop_artifacts(kb_dir: Path) -> list[str]:
    """Validate optional loop artifacts (coverage.json / profile.json) if present.

    These belong to the autonomous-loop skill; absence is fine. A YAML profile is
    authoritatively validated by the loop runner (which has PyYAML), so only the JSON
    form is checked here to keep this validator dependency-free.
    """
    errors: list[str] = []

    coverage = kb_dir / "coverage.json"
    if not coverage.is_file() and (kb_dir.parent / "coverage.json").is_file():
        coverage = kb_dir.parent / "coverage.json"
    if coverage.is_file():
        payload = _load_json_object(coverage, "coverage.json", errors)
        if payload is not None:
            if payload.get("schema") != LOOP_COVERAGE_SCHEMA:
                errors.append(f"coverage.json schema must be '{LOOP_COVERAGE_SCHEMA}'")
            if not isinstance(payload.get("fronts"), dict) or not payload.get("fronts"):
                errors.append("coverage.json must contain a non-empty 'fronts' mapping")

    profile = kb_dir / "profile.json"
    if profile.is_file():
        payload = _load_json_object(profile, "profile.json", errors)
        if payload is not None and payload.get("schema") != LOOP_PROFILE_SCHEMA:
            errors.append(f"profile.json schema must be '{LOOP_PROFILE_SCHEMA}'")

    return errors


def validate_knowledge_base(directory: Path | str) -> list[str]:
    """Validate a knowledge base directory. Returns list of errors (empty if valid)."""
    kb_dir = Path(directory).resolve()
    errors: list[str] = []

    if not kb_dir.is_dir():
        return [f"Directory not found: {kb_dir}"]

    index_path = kb_dir / "index.md"
    if not index_path.is_file():
        return [f"Missing index.md (Map of Content) in {kb_dir}"]

    all_md_files = {p.name: p for p in kb_dir.glob("*.md")}

    # Check size limits
    index_size = index_path.stat().st_size
    if index_size > MAX_INDEX_BYTES:
        errors.append(
            f"index.md exceeds byte ceiling: {index_size} bytes (limit {MAX_INDEX_BYTES} bytes)"
        )

    for name, path in all_md_files.items():
        if name == "index.md":
            continue
        size = path.stat().st_size
        if size > MAX_LEAF_BYTES:
            errors.append(
                f"{name} exceeds leaf byte ceiling: {size} bytes (limit {MAX_LEAF_BYTES} bytes)"
            )

    # Check index links to all leaves
    index_content = index_path.read_text(encoding="utf-8")
    index_targets = extract_links(index_content)

    for name in all_md_files:
        if name != "index.md" and name not in index_targets:
            errors.append(f"Orphan leaf: '{name}' is not indexed in index.md")

    # Check link integrity across all leaves, including sub-leaf splits
    known_targets = {p.name for p in kb_dir.rglob("*.md")}
    for name, path in all_md_files.items():
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"File {name} is not valid UTF-8")
            continue

        targets = extract_links(content)
        for target in targets:
            if target not in known_targets:
                errors.append(f"Broken link in {name}: target '{target}' does not exist")

    errors.extend(validate_loop_artifacts(kb_dir))

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a Project Knowledge Base.")
    parser.add_argument("directory", help="Path to knowledge directory")
    args = parser.parse_args()

    errors = validate_knowledge_base(args.directory)
    if errors:
        print("KNOWLEDGE BASE VALIDATION FAILED:", file=sys.stderr)
        for err in errors:
            print(f"  - ERROR: {err}", file=sys.stderr)
        return 1

    print("VALID: Knowledge base adheres to token-efficient MOC structure and link integrity.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

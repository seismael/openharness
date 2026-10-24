#!/usr/bin/env python3
"""Validate the public skill bundles and their documented release surface."""

import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

from install_skill import IGNORED_DIRS, ignored, reject_symlink_ancestors

ROOT = Path(__file__).resolve().parent.parent
TEXT_SUFFIXES = {".md", ".py", ".sh", ".json", ".yaml", ".yml", ".toml", ".txt"}
PUBLIC_DOCUMENTS = (
    "README.md",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "LICENSE",
    "docs",
    "adapters",
)
PRIVATE_MARKERS = re.compile(
    r"skill://|skill-[0-9a-f]{32}|(?<![A-Za-z0-9_.-])/(?:workspace|mnt/data)/|/root/\.codex/"
)
LINK = re.compile(r"\[[^\]]*\]\(\s*(?:<([^>]+)>|([^\s)]+))(?:\s+['\"][^)]*)?\s*\)")
REFERENCE_LINK = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*(?:<([^>]+)>|(\S+))", re.MULTILINE)


def flat_string(value):
    value = value.strip()
    if not value:
        raise ValueError("expected a nonempty string")
    if value.startswith('"'):
        parsed = json.loads(value)
        if isinstance(parsed, str):
            return parsed
    elif value.startswith("'"):
        if re.fullmatch(r"'(?:[^']|'')*'", value):
            return value[1:-1].replace("''", "'")
    elif (
        value[0] not in "|>[{&*!%@`"
        and ": " not in value
        and " #" not in value
        and value.lower() not in {"true", "false", "null", "~", "yes", "no", "on", "off"}
        and not re.fullmatch(r"[-+]?\d+(?:\.\d+)?|\d{4}-\d\d-\d\d", value)
    ):
        return value
    raise ValueError("expected a flat string")


def check_links(path, text, skill, errors):
    for match in (*LINK.finditer(text), *REFERENCE_LINK.finditer(text)):
        target = match.group(1) or match.group(2)
        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        linked = (path.parent / unquote(parsed.path)).resolve()
        if linked != skill and skill not in linked.parents:
            errors.append(f"{path.relative_to(ROOT)}: link escapes skill: {target}")
        elif not linked.exists():
            errors.append(f"{path.relative_to(ROOT)}: missing link target: {target}")


def check_frontmatter(skill, errors):
    path = skill / "SKILL.md"
    reject_symlink_ancestors(path)
    if not path.is_file():
        errors.append(f"{skill.name}: missing SKILL.md")
        return
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---" or "---" not in lines[1:]:
        errors.append(f"{skill.name}: SKILL.md needs YAML frontmatter")
        return
    end = lines.index("---", 1)
    fields = {}
    for line in lines[1:end]:
        match = re.fullmatch(r"(name|description):[ \t]+(.+)", line)
        if not match or match.group(1) in fields:
            errors.append(f"{skill.name}: frontmatter permits only one name and description string")
            continue
        key, value = match.groups()
        try:
            value = flat_string(value)
        except (ValueError, TypeError):
            errors.append(f"{skill.name}: {key} must be a flat string")
        fields[key] = value
    name = fields.get("name", "")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64 or name != skill.name:
        errors.append(
            f"{skill.name}: name must match the directory and use lowercase hyphenated text"
        )
    if not 1 <= len(fields.get("description", "")) <= 1024:
        errors.append(f"{skill.name}: description must contain 1-1024 characters")
    if len(lines[end + 1 :]) > 500:
        errors.append(f"{skill.name}: SKILL.md body exceeds 500 lines")


def inspect_path(base, errors, skill=None):
    if not base.exists() and not base.is_symlink():
        return
    reject_symlink_ancestors(base)
    entries = [base] if base.is_file() else base.rglob("*")
    for path in entries:
        relative = path.relative_to(ROOT)
        if path.is_symlink():
            errors.append(f"{relative}: symlinks are not allowed in the release")
            continue
        if any(
            part in IGNORED_DIRS
            or part in {".env", ".venv", "sessions", "credentials"}
            or ignored(part)
            for part in relative.parts
        ):
            errors.append(f"{relative}: runtime or private path in release content")
            continue
        if not path.is_file() or (path.suffix not in TEXT_SUFFIXES and path.name != "LICENSE"):
            continue
        text = path.read_text(encoding="utf-8")
        if PRIVATE_MARKERS.search(text):
            errors.append(f"{relative}: internal path or identifier in public content")
        if skill is not None and path.suffix == ".md":
            check_links(path, text, skill, errors)


def main():
    errors = []
    try:
        reject_symlink_ancestors(ROOT / "skills")
        skills = sorted((ROOT / "skills").iterdir())
        if not skills:
            errors.append("No skill bundles found")
        for skill in skills:
            reject_symlink_ancestors(skill)
            if not skill.is_dir():
                errors.append(f"skills/{skill.name}: expected a skill directory")
                continue
            check_frontmatter(skill, errors)
            inspect_path(skill, errors, skill)
        for name in PUBLIC_DOCUMENTS:
            inspect_path(ROOT / name, errors)
    except (OSError, UnicodeError, ValueError) as error:
        errors.append(str(error))
    if errors:
        print(
            "Release checks failed:\n" + "\n".join(f"- {error}" for error in errors),
            file=sys.stderr,
        )
        return 1
    print(f"Release checks passed: {len(skills)} skill bundle(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

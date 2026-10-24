#!/usr/bin/env python3
"""Copy one bundled skill to an explicitly chosen, new directory."""

import argparse
import os
import re
import shutil
import sys
from pathlib import Path

IGNORED_DIRS = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".cache",
    "node_modules",
    ".git",
    "logs",
    "state",
}
IGNORED_SUFFIXES = (".pyc", ".pyo", ".log", ".sqlite", ".sqlite3", ".db")


def report(message, error=False):
    stream = sys.stderr if error else sys.stdout
    encoding = stream.encoding or "utf-8"
    print(message.encode(encoding, "backslashreplace").decode(encoding), file=stream)


def ignored(name):
    """Exclude local caches and runtime database/log files from a copy."""
    lower = name.lower()
    base = re.sub(r"-(?:wal|shm|journal)$", "", lower)
    return name in IGNORED_DIRS or base.endswith(IGNORED_SUFFIXES)


def reject_symlink_ancestors(path):
    for candidate in (path, *path.parents):
        if candidate.is_symlink():
            raise ValueError(f"Symlinks are not supported: {candidate}")


def inspect_source(source):
    """Check the whole bundle before copying, including excluded entries."""
    files = []
    for directory, directories, filenames in os.walk(source, followlinks=False):
        for name in directories + filenames:
            entry = Path(directory) / name
            if entry.is_symlink():
                raise ValueError(f"Symlinks are not supported: {entry}")
            if not (entry.is_file() or entry.is_dir()):
                raise ValueError(f"Unsupported file type: {entry}")
            relative = entry.relative_to(source)
            if entry.is_file() and not any(ignored(part) for part in relative.parts):
                files.append(relative)
    return files


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", required=True, help="Bundled skill directory name")
    parser.add_argument(
        "--to",
        required=True,
        metavar="EXACT_DESTINATION",
        help="New directory that will contain SKILL.md",
    )
    parser.add_argument("--check", action="store_true", help="Validate and report; write nothing")
    args = parser.parse_args(argv)
    try:
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", args.skill) or len(args.skill) > 64:
            raise ValueError(
                "Skill must be a lowercase, hyphen-separated name (up to 64 characters)"
            )
        repository = Path(os.path.abspath(__file__)).parent.parent
        source = repository / "skills" / args.skill
        requested_destination = Path(os.path.expanduser(args.to)).absolute()
        reject_symlink_ancestors(requested_destination)
        destination = Path(os.path.abspath(requested_destination))
        reject_symlink_ancestors(source)
        reject_symlink_ancestors(destination)
        if not source.is_dir() or not (source / "SKILL.md").is_file():
            raise ValueError(f"Bundled skill not found: {args.skill}")
        if destination == source or source in destination.parents:
            raise ValueError("Destination must not be inside the source skill")
        if destination.exists():
            raise ValueError(f"Destination already exists; refusing to overwrite: {destination}")
        files = inspect_source(source)
        if args.check:
            report(f"Check passed: would copy {len(files)} files from {source} to {destination}")
            return 0
        shutil.copytree(
            source,
            destination,
            ignore=lambda directory, names: [name for name in names if ignored(name)],
        )
        report(f"Installed {args.skill}: {len(files)} files copied to {destination}")
        return 0
    except (OSError, ValueError) as error:
        report(f"Error: {error}", error=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

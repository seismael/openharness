"""Content identity: file hashes, the harness fingerprint, and canonical order."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def relative_path(path: Path, root: Path) -> str:
    """Repository-relative POSIX path, so hashes and receipts are portable."""
    return str(path.relative_to(root)).replace("\\", "/")


def state_fingerprint(files: Iterable[Path], root: Path) -> str:
    """Identity of the exact harness state: sha256 over sorted (path, content).

    Duplicate paths are hashed once, so the identity depends on harness content
    and not on how components happen to overlap.
    """
    digest = hashlib.sha256()
    seen: set[str] = set()
    ordered = sorted(files, key=lambda path: relative_path(path, root))
    for path in ordered:
        relative = relative_path(path, root)
        if relative in seen:
            continue
        seen.add(relative)
        content = sha256_file(path)
        digest.update(f"{relative}\0{content}\n".encode())
    return digest.hexdigest()

"""Content identity: file hashes, the harness fingerprint, and canonical order."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
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


def fingerprint_from_hashes(hashes: Mapping[str, str]) -> str:
    """Identity from precomputed ``relative path -> sha256`` content hashes.

    This is the single definition of the harness fingerprint: callers that
    already read the tree pass their hash map instead of hashing it again.
    """
    digest = hashlib.sha256()
    for relative in sorted(hashes):
        digest.update(f"{relative}\0{hashes[relative]}\n".encode())
    return digest.hexdigest()


def state_fingerprint(files: Iterable[Path], root: Path) -> str:
    """Identity of the exact harness state: sha256 over sorted (path, content).

    Duplicate paths are hashed once, so the identity depends on harness content
    and not on how components happen to overlap.
    """
    hashes: dict[str, str] = {}
    for path in files:
        relative = relative_path(path, root)
        if relative in hashes:
            continue
        hashes[relative] = sha256_file(path)
    return fingerprint_from_hashes(hashes)

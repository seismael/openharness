#!/usr/bin/env python3
"""Stage, review, apply, and roll back local UTF-8 config file changes.

No network, subprocesses, credential discovery, config parsing, or deletion plans.
See references/changes-and-validation.md for the contract and limitations.
"""

import argparse
import base64
import difflib
import hashlib
import json
import os
import stat
import sys
import tempfile
from pathlib import Path

LIMIT = 2 * 1024 * 1024


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encode(data):
    return None if data is None else base64.b64encode(data).decode("ascii")


def decode(data):
    require(data is None or isinstance(data, str), "Invalid encoded file content")
    return None if data is None else base64.b64decode(data, validate=True)


def safe_path(value):
    require(isinstance(value, str) and value, "Expected a nonempty path string")
    path = Path(value)
    require(path.is_absolute() and ".." not in path.parts, "Use absolute paths without ..")
    for item in [path, *path.parents]:
        require(not item.is_symlink(), "Symlink path refused: " + str(item))
        if item.exists():
            info = item.lstat()
            require(
                not (getattr(info, "st_file_attributes", 0) & 0x400),
                "Windows reparse point refused: " + str(item),
            )
    return path


def inside(path, root):
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def read_file(path):
    path = safe_path(str(path))
    if not path.exists():
        return None, None
    info = path.stat()
    require(
        stat.S_ISREG(info.st_mode) and info.st_nlink == 1,
        "Only ordinary single-link files supported: " + str(path),
    )
    require(info.st_size <= LIMIT, "File exceeds 2 MiB: " + str(path))
    data = path.read_bytes()
    require(len(data) <= LIMIT, "File exceeds 2 MiB: " + str(path))
    data.decode("utf-8")
    return data, stat.S_IMODE(info.st_mode)


def atomic_write(path, data, mode):
    safe_path(str(path))
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    safe_path(str(path))
    fd, temporary = tempfile.mkstemp(prefix=".characterize-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            # Windows cannot unlink a read-only temporary after replacement fails.
            os.chmod(temporary, 0o600)
            os.unlink(temporary)


def save_json(path, value):
    atomic_write(path, json_bytes(value), 0o600)


def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def load_object(path):
    raw, _ = read_file(path)
    require(raw is not None, "Missing " + path.name)
    value = json.loads(raw)
    require(isinstance(value, dict), "Expected a JSON object in " + path.name)
    return value, raw


def scope_roots(value):
    require(isinstance(value, list) and value, "At least one scope root is required")
    roots = [safe_path(x) for x in value]
    require(all(p.is_dir() and p != Path(p.anchor) for p in roots), "Invalid scope root")
    return roots


def check_nested_targets(paths):
    identities = {os.path.normcase(str(path)) for path in paths}
    require(
        not any(
            os.path.normcase(str(parent)) in identities for path in paths for parent in path.parents
        ),
        "Nested file targets",
    )


def load_bundle(directory):
    folder = safe_path(str(Path(directory).absolute()))
    plan, raw = load_object(folder / "bundle.json")
    require(type(plan.get("version")) is int and plan["version"] == 1, "Unsupported bundle version")
    roots = scope_roots(plan["roots"])
    require(
        not any(inside(folder, root) or inside(root, folder) for root in roots),
        "Bundle and target roots must not overlap",
    )
    require(isinstance(plan["files"], list), "Expected a files list")
    seen = set()
    for entry in plan["files"]:
        require(isinstance(entry, dict), "Expected a file entry object")
        path = safe_path(entry["path"])
        require(any(inside(path, root) and path != root for root in roots), "Target outside scope")
        identity = os.path.normcase(str(path))
        require(identity not in seen, "Duplicate target")
        seen.add(identity)
        before, after = decode(entry["before"]), decode(entry["after"])
        require(after is not None, "Deletion plans are unsupported")
        for data in [before, after]:
            if data is not None:
                require(len(data) <= LIMIT, "File exceeds 2 MiB")
                data.decode("utf-8")
        require(
            entry["before_sha256"] == (None if before is None else sha(before)),
            "Invalid before hash",
        )
        require(entry["after_sha256"] == sha(after), "Invalid after hash")
        require(before != after, "No-op entry")
        require(type(entry["mode"]) is int and 0 <= entry["mode"] <= 0o777, "Invalid file mode")
        require(
            (before is None and entry["before_mode"] is None)
            or (
                before is not None
                and type(entry["before_mode"]) is int
                and entry["before_mode"] == entry["mode"]
            ),
            "Invalid original file mode",
        )
    paths = [Path(e["path"]) for e in plan["files"]]
    check_nested_targets(paths)
    return folder, plan, sha(raw)


def stage(args):
    spec_path = safe_path(str(Path(args.spec).absolute()))
    spec, _ = load_object(spec_path)
    roots = scope_roots(spec["roots"])
    require(isinstance(spec["writes"], list), "Expected a writes list")
    folder = safe_path(str(Path(args.bundle).absolute()))
    require(not folder.exists(), "Use a new bundle directory")
    require(
        not any(inside(folder, root) or inside(root, folder) for root in roots),
        "Bundle and target roots must not overlap",
    )
    files, seen = [], set()
    for change in spec["writes"]:
        require(isinstance(change, dict), "Expected a write entry object")
        target = safe_path(change["path"])
        require(
            any(inside(target, root) and target != root for root in roots), "Target outside scope"
        )
        identity = os.path.normcase(str(target))
        require(identity not in seen, "Duplicate target")
        seen.add(identity)
        before, before_mode = read_file(target)
        after, _ = read_file(safe_path(change["source"]))
        require(after is not None, "Missing proposed source")
        mode = (0o666 if os.name == "nt" else 0o600) if before is None else before_mode
        require(mode <= 0o777, "Special permission bits are unsupported")
        if before == after:
            continue
        files.append(
            {
                "path": str(target),
                "before": encode(before),
                "after": encode(after),
                "before_sha256": None if before is None else sha(before),
                "after_sha256": sha(after),
                "before_mode": before_mode,
                "mode": mode,
            }
        )
    targets = [Path(e["path"]) for e in files]
    check_nested_targets(targets)
    proposal = json_bytes({"version": 1, "roots": [str(p) for p in roots], "files": files})
    require(len(proposal) <= LIMIT, "Bundle too large; divide into reviewable change sets")
    folder.mkdir(parents=True, mode=0o700)
    atomic_write(folder / "bundle.json", proposal, 0o600)
    _, _, digest = load_bundle(str(folder))
    print(json.dumps({"bundle": str(folder), "files": len(files), "sha256": digest}))


def review(args):
    _, plan, digest = load_bundle(args.bundle)
    print(
        json.dumps(
            {
                "sha256": digest,
                "roots": plan["roots"],
                "files": [
                    {k: e[k] for k in ["path", "before_sha256", "after_sha256"]}
                    for e in plan["files"]
                ],
            },
            indent=2,
        )
    )
    if args.diff:
        for entry in plan["files"]:
            before = (decode(entry["before"]) or b"").decode().splitlines(keepends=True)
            after = decode(entry["after"]).decode().splitlines(keepends=True)
            sys.stdout.writelines(
                difflib.unified_diff(
                    before,
                    after,
                    fromfile=entry["path"] + " (before)",
                    tofile=entry["path"] + " (after)",
                )
            )


def check_current(entry, allow_after=False):
    data, mode = read_file(Path(entry["path"]))
    if data == decode(entry["before"]) and mode == entry["before_mode"]:
        return "before"
    if allow_after and data == decode(entry["after"]) and mode == entry["mode"]:
        return "after"
    raise ValueError("File drift; inspect before continuing: " + entry["path"])


def apply(args):
    folder, plan, digest = load_bundle(args.bundle)
    require(args.sha256 == digest, "Bundle hash differs from reviewed proposal")
    journal_path = folder / "journal.json"
    require(
        not journal_path.exists(),
        "Bundle already attempted; inspect journal or create a fresh bundle",
    )
    for entry in plan["files"]:
        check_current(entry)
    journal = {"sha256": digest, "state": "applying", "attempted": []}
    save_json(journal_path, journal)
    try:
        for index, entry in enumerate(plan["files"]):
            check_current(entry)
            journal["attempted"].append(index)
            save_json(journal_path, journal)
            atomic_write(Path(entry["path"]), decode(entry["after"]), entry["mode"])
        journal["state"] = "applied"
        save_json(journal_path, journal)
    except Exception:
        journal["state"] = "interrupted"
        save_json(journal_path, journal)
        raise
    print(json.dumps({"state": "applied", "files": len(plan["files"]), "sha256": digest}))


def rollback(args):
    folder, plan, digest = load_bundle(args.bundle)
    require(args.sha256 == digest, "Bundle hash differs from reviewed proposal")
    journal, _ = load_object(folder / "journal.json")
    require(journal["sha256"] == digest, "Journal/bundle mismatch")
    require(
        journal["state"] in ["applying", "applied", "interrupted", "rolled-back"],
        "Unknown journal state",
    )
    indexes = journal["attempted"]
    require(
        isinstance(indexes, list)
        and all(type(index) is int for index in indexes)
        and indexes == list(range(len(indexes)))
        and len(indexes) <= len(plan["files"]),
        "Invalid journal",
    )
    for index in indexes:
        check_current(plan["files"][index], allow_after=True)
    for index in reversed(indexes):
        entry = plan["files"][index]
        if check_current(entry, allow_after=True) == "before":
            continue
        path = Path(entry["path"])
        before = decode(entry["before"])
        if before is None:
            path.unlink()
        else:
            atomic_write(path, before, entry["before_mode"])
    journal["state"] = "rolled-back"
    save_json(folder / "journal.json", journal)
    print(json.dumps({"state": "rolled-back", "files": len(indexes)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    command = sub.add_parser("stage")
    command.add_argument("--spec", required=True)
    command.add_argument("--bundle", required=True)
    command.set_defaults(fn=stage)
    command = sub.add_parser("review")
    command.add_argument("--bundle", required=True)
    command.add_argument(
        "--diff", action="store_true", help="Print raw local diffs; do not expose secrets"
    )
    command.set_defaults(fn=review)
    for name, fn in [("apply", apply), ("rollback", rollback)]:
        command = sub.add_parser(name)
        command.add_argument("--bundle", required=True)
        command.add_argument(
            "--sha256",
            required=True,
            help="Digest of the reviewed bundle; not an authorization grant",
        )
        command.set_defaults(fn=fn)
    args = parser.parse_args()
    try:
        args.fn(args)
    except (ValueError, OSError, KeyError, TypeError) as error:
        print("ERROR: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

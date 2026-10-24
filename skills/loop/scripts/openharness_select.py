#!/usr/bin/env python3
"""Anonymize candidate deliverables and record an adoption choice (RFC-0010).

The selector sees deliverables without their originating harness. The mapping is written to
a separate sealed file that the selector must not read. Deterministic, model-free.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

CONTRACT = "openharness.selection.v1"
MAX_BYTES = 2500
SKIP_SUFFIXES = (".receipt.json", ".selection.json", ".mapping.json")


def bounded(payload):
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    if len(text.encode("utf-8")) <= MAX_BYTES:
        return text
    trimmed = {
        "schema": payload.get("schema"),
        "candidates": payload.get("candidates", [])[:8],
        "count": payload.get("count"),
        "chosen": payload.get("chosen"),
        "ok": payload.get("ok"),
        "truncated": True,
    }
    return json.dumps(trimmed, sort_keys=True, separators=(",", ":"))


def discover(directory):
    files = []
    for path in sorted(Path(directory).iterdir()):
        if not path.is_file():
            continue
        if path.name.endswith(SKIP_SUFFIXES) or path.name in {
            "selection.json",
            "mapping.json",
        }:
            continue
        files.append(path)
    return files


def anonymize(files):
    """Name candidates by content order so the label carries no authoring signal."""
    hashed = []
    for path in files:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        hashed.append((digest, path))
    hashed.sort(key=lambda item: item[0])
    anon = {}
    for index, (digest, path) in enumerate(hashed):
        label = f"cand-{chr(ord('a') + index)}" if index < 26 else f"cand-{index + 1}"
        anon[label] = {"path": path, "sha256": digest}
    return anon


def receipts_present(files):
    missing = [
        path.name
        for path in files
        if not path.with_name(path.name + ".receipt.json").is_file()
    ]
    return missing


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Anonymize candidates and record a choice."
    )
    parser.add_argument(
        "--candidates", required=True, help="Directory holding candidate outputs"
    )
    parser.add_argument("--choose", help="Anonymous candidate id to adopt")
    parser.add_argument(
        "--reason", default="", help="Observation supporting the choice"
    )
    parser.add_argument(
        "--unseal", action="store_true", help="Print the sealed mapping"
    )
    parser.add_argument(
        "--allow-unprobed",
        action="store_true",
        help="Permit choosing a candidate without a probe receipt (recorded as unproven)",
    )
    args = parser.parse_args(argv)

    directory = Path(args.candidates)
    if not directory.is_dir():
        print(
            json.dumps(
                {"schema": CONTRACT, "ok": False, "error": "not a directory"},
                sort_keys=True,
            )
        )
        return 2

    selection_path = directory / "selection.json"
    mapping_path = directory / "mapping.json"

    if args.unseal:
        if not mapping_path.is_file():
            print(
                json.dumps(
                    {"schema": CONTRACT, "ok": False, "error": "no seal"},
                    sort_keys=True,
                )
            )
            return 2
        print(mapping_path.read_text(encoding="utf-8-sig").strip())
        return 0

    files = discover(directory)
    if not files:
        print(
            json.dumps(
                {"schema": CONTRACT, "ok": False, "error": "no candidates"},
                sort_keys=True,
            )
        )
        return 2

    if not selection_path.is_file():
        anon = anonymize(files)
        mapping = {label: str(entry["path"].name) for label, entry in anon.items()}
        mapping_path.write_text(
            json.dumps(mapping, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        selection = {
            "schema": CONTRACT,
            "count": len(anon),
            "candidates": [
                {
                    "id": label,
                    "sha256": entry["sha256"],
                    "size": entry["path"].stat().st_size,
                }
                for label, entry in anon.items()
            ],
            "chosen": None,
            "reason": "",
            "mode": "existing-output",
            "ok": True,
        }
        selection_path.write_text(
            json.dumps(selection, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(bounded(selection))
        return 0

    selection = json.loads(selection_path.read_text(encoding="utf-8-sig"))
    if not args.choose:
        print(bounded(selection))
        return 0

    valid = {item["id"] for item in selection.get("candidates", [])}
    if args.choose not in valid:
        print(
            json.dumps(
                {
                    "schema": CONTRACT,
                    "ok": False,
                    "error": f"unknown candidate {args.choose}",
                },
                sort_keys=True,
            )
        )
        return 2
    if not args.reason.strip():
        print(
            json.dumps(
                {"schema": CONTRACT, "ok": False, "error": "reason required"},
                sort_keys=True,
            )
        )
        return 2

    missing = receipts_present(files)
    if missing and not args.allow_unprobed:
        print(
            json.dumps(
                {
                    "schema": CONTRACT,
                    "ok": False,
                    "error": "candidate lacks a probe receipt",
                    "missing": missing,
                },
                sort_keys=True,
            )
        )
        return 1

    selection["chosen"] = args.choose
    selection["reason"] = args.reason.strip()
    selection["mode"] = "existing-output"
    selection["unproven"] = bool(missing)
    selection["ok"] = True
    selection_path.write_text(
        json.dumps(selection, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(bounded(selection))
    return 0


if __name__ == "__main__":
    sys.exit(main())

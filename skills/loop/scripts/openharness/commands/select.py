"""Anonymize candidate deliverables and record an adoption choice (RFC-0010)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .. import jsonio
from ..digest import sha256_file
from ..errors import EXIT_FINDINGS, EXIT_OK, EXIT_USAGE
from ..schemas import SELECTION

HELP = "anonymize candidates and record a choice"
DESCRIPTION = "Anonymize candidates and record a choice."

SKIP_SUFFIXES = (".receipt.json", ".selection.json", ".mapping.json")
CONTRACT = SELECTION


def bounded(payload: dict[str, Any]) -> str:
    return jsonio.bounded(payload, (_drop_candidates,))


def _drop_candidates(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": payload.get("schema"),
        "candidates": payload.get("candidates", [])[:8],
        "count": payload.get("count"),
        "chosen": payload.get("chosen"),
        "ok": payload.get("ok"),
        "truncated": True,
    }


def discover(directory: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(directory.iterdir()):
        if not path.is_file():
            continue
        if path.name.endswith(SKIP_SUFFIXES) or path.name in {
            "selection.json",
            "mapping.json",
        }:
            continue
        files.append(path)
    return files


def anonymize(files: list[Path]) -> dict[str, dict[str, Any]]:
    """Name candidates by content order so the label carries no authoring signal."""
    hashed = [(sha256_file(path), path) for path in files]
    hashed.sort(key=lambda item: item[0])
    anon: dict[str, dict[str, Any]] = {}
    for index, (digest_value, path) in enumerate(hashed):
        label = f"cand-{chr(ord('a') + index)}" if index < 26 else f"cand-{index + 1}"
        anon[label] = {"path": path, "sha256": digest_value}
    return anon


def receipts_present(files: list[Path]) -> list[str]:
    return [
        path.name for path in files if not path.with_name(path.name + ".receipt.json").is_file()
    ]


def configure(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--candidates", required=True, help="Directory holding candidate outputs")
    parser.add_argument("--choose", help="Anonymous candidate id to adopt")
    parser.add_argument("--reason", default="", help="Observation supporting the choice")
    parser.add_argument("--unseal", action="store_true", help="Print the sealed mapping")
    parser.add_argument(
        "--allow-unprobed",
        action="store_true",
        help="Permit choosing a candidate without a probe receipt (recorded as unproven)",
    )


def run(args: argparse.Namespace) -> int:
    directory = Path(args.candidates)
    if not directory.is_dir():
        print(jsonio.spaced({"schema": CONTRACT, "ok": False, "error": "not a directory"}))
        return EXIT_USAGE

    selection_path = directory / "selection.json"
    mapping_path = directory / "mapping.json"

    if args.unseal:
        if not mapping_path.is_file():
            print(jsonio.spaced({"schema": CONTRACT, "ok": False, "error": "no seal"}))
            return EXIT_USAGE
        print(mapping_path.read_text(encoding="utf-8-sig").strip())
        return EXIT_OK

    files = discover(directory)
    if not files:
        print(jsonio.spaced({"schema": CONTRACT, "ok": False, "error": "no candidates"}))
        return EXIT_USAGE

    if not selection_path.is_file():
        anon = anonymize(files)
        mapping = {label: str(entry["path"].name) for label, entry in anon.items()}
        jsonio.write_text(mapping_path, jsonio.pretty(mapping) + "\n")
        selection: dict[str, Any] = {
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
        jsonio.write_text(selection_path, jsonio.pretty(selection) + "\n")
        print(bounded(selection))
        return EXIT_OK

    selection = json.loads(selection_path.read_text(encoding="utf-8-sig"))
    if not args.choose:
        print(bounded(selection))
        return EXIT_OK

    valid = {item["id"] for item in selection.get("candidates", [])}
    if args.choose not in valid:
        print(
            jsonio.spaced(
                {
                    "schema": CONTRACT,
                    "ok": False,
                    "error": f"unknown candidate {args.choose}",
                }
            )
        )
        return EXIT_USAGE
    if not args.reason.strip():
        print(jsonio.spaced({"schema": CONTRACT, "ok": False, "error": "reason required"}))
        return EXIT_USAGE

    missing = receipts_present(files)
    if missing and not args.allow_unprobed:
        print(
            jsonio.spaced(
                {
                    "schema": CONTRACT,
                    "ok": False,
                    "error": "candidate lacks a probe receipt",
                    "missing": missing,
                }
            )
        )
        return EXIT_FINDINGS

    selection["chosen"] = args.choose
    selection["reason"] = args.reason.strip()
    selection["mode"] = "existing-output"
    selection["unproven"] = bool(missing)
    selection["ok"] = True
    selection_path.write_text(jsonio.pretty(selection) + "\n", encoding="utf-8", newline="\n")
    print(bounded(selection))
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    configure(parser)
    return run(parser.parse_args(argv))

"""Evaluate a portable action policy deterministically (RFC-0015)."""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
from pathlib import Path
from typing import Any

from .. import jsonio
from ..errors import EXIT_ASK, EXIT_FINDINGS, EXIT_OK, EXIT_USAGE, DeclarationError
from ..schemas import POLICY

HELP = "evaluate a portable action policy"
DESCRIPTION = "Evaluate a portable action policy."

CONTRACT = POLICY
VERDICTS = ("allow", "ask", "deny")
MATCH_KEYS = {"tool", "path_glob", "command_regex"}
RULE_KEYS = {"id", "match", "verdict", "reason"}


class PolicyError(DeclarationError):
    """A policy document or request that cannot be evaluated."""


def load_policy(path: str | Path) -> dict[str, Any]:
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except OSError as error:
        raise PolicyError(f"cannot read policy: {error}") from error
    except json.JSONDecodeError as error:
        raise PolicyError(f"policy is not valid JSON: {error}") from error
    if not isinstance(document, dict):
        raise PolicyError("policy must be an object")
    if document.get("schema") != CONTRACT:
        raise PolicyError(f"schema must be {CONTRACT}")
    unknown = sorted(set(document) - {"schema", "description", "default", "rules"})
    if unknown:
        raise PolicyError(f"unknown policy keys: {', '.join(unknown)}")
    default = document.get("default", "ask")
    if default not in VERDICTS:
        raise PolicyError(f"default must be one of {', '.join(VERDICTS)}")
    rules = document.get("rules")
    if not isinstance(rules, list):
        raise PolicyError("policy key 'rules' must be an array")

    compiled: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, rule in enumerate(rules):
        label = f"rule #{index + 1}"
        if not isinstance(rule, dict):
            raise PolicyError(f"{label} must be an object")
        identifier = rule.get("id")
        if not isinstance(identifier, str) or not identifier.strip():
            raise PolicyError(f"{label} requires a non-empty id")
        if identifier in seen:
            raise PolicyError(f"{identifier}: duplicate rule id")
        seen.add(identifier)
        label = identifier
        unknown_rule = sorted(set(rule) - RULE_KEYS)
        if unknown_rule:
            raise PolicyError(f"{label}: unknown fields {', '.join(unknown_rule)}")
        verdict = rule.get("verdict")
        if verdict not in VERDICTS:
            raise PolicyError(f"{label}: verdict must be one of {', '.join(VERDICTS)}")
        match = rule.get("match")
        if not isinstance(match, dict) or not match:
            raise PolicyError(f"{label}: match must be a non-empty object")
        unknown_match = sorted(set(match) - MATCH_KEYS)
        if unknown_match:
            raise PolicyError(f"{label}: unknown match keys {', '.join(unknown_match)}")
        for key, value in match.items():
            if not isinstance(value, str) or not value.strip():
                raise PolicyError(f"{label}: match.{key} must be a non-empty string")
        pattern = None
        if "command_regex" in match:
            try:
                pattern = re.compile(match["command_regex"])
            except re.error as error:
                raise PolicyError(f"{label}: invalid command_regex: {error}") from error
        compiled.append(
            {
                "id": identifier,
                "verdict": verdict,
                "reason": rule.get("reason", ""),
                "match": match,
                "pattern": pattern,
            }
        )
    return {"default": default, "rules": compiled}


def matches(rule: dict[str, Any], request: dict[str, Any]) -> bool:
    """A rule matches only when every declared condition is satisfied."""
    match = rule["match"]
    if "tool" in match:
        if request.get("tool") is None:
            return False
        if request["tool"].lower() != match["tool"].lower():
            return False
    if "path_glob" in match:
        if request.get("path") is None:
            return False
        normalized = request["path"].replace("\\", "/")
        if not fnmatch.fnmatch(normalized, match["path_glob"]):
            return False
    if "command_regex" in match:
        if request.get("command") is None:
            return False
        if rule["pattern"].search(request["command"]) is None:
            return False
    return True


def evaluate(policy: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    matched: list[str] = []
    verdict = policy["default"]
    rule_id = None
    reason = "no rule matched"
    for rule in policy["rules"]:
        if not matches(rule, request):
            continue
        matched.append(rule["id"])
        verdict = rule["verdict"]
        rule_id = rule["id"]
        reason = rule["reason"]
    return {
        "schema": CONTRACT,
        "verdict": verdict,
        "rule": rule_id,
        "reason": reason,
        "matched": matched[:16],
        "ok": verdict != "deny",
    }


def bounded(payload: dict[str, Any]) -> str:
    text = jsonio.compact(payload)
    if jsonio.byte_size(text) <= jsonio.MAX_BYTES:
        return text
    payload["matched"] = payload["matched"][:4]
    payload["truncated"] = True
    return jsonio.compact(payload)


def configure(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--policy", required=True, help="Path to an openharness.policy.v1 document")
    parser.add_argument("--tool", help="Tool or command surface being invoked")
    parser.add_argument("--path", help="Path the action targets")
    parser.add_argument("--command", help="Command text the action would execute")


def run(args: argparse.Namespace) -> int:
    request: dict[str, Any] = {}
    if args.tool is not None:
        request["tool"] = args.tool
    if args.path is not None:
        request["path"] = args.path
    if args.command is not None:
        request["command"] = args.command
    if not request:
        print(
            jsonio.spaced(
                {
                    "schema": CONTRACT,
                    "ok": False,
                    "error": "at least one of --tool, --path, --command is required",
                }
            )
        )
        return EXIT_USAGE

    try:
        policy = load_policy(args.policy)
    except PolicyError as error:
        print(jsonio.spaced({"schema": CONTRACT, "ok": False, "error": str(error)}))
        return EXIT_USAGE

    payload = evaluate(policy, request)
    print(bounded(payload))
    if payload["verdict"] == "allow":
        return EXIT_OK
    if payload["verdict"] == "deny":
        return EXIT_FINDINGS
    return EXIT_ASK


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    configure(parser)
    return run(parser.parse_args(argv))

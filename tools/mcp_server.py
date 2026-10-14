#!/usr/bin/env python3
"""Zero-dependency Model Context Protocol (MCP) server for OpenAgent Loop Protocol (OALP).

Exposes .agents/loop state, moves, and verification tools to MCP-compatible
IDEs and agents (Cursor, Windsurf, Claude Desktop, Antigravity).
"""

import json
import os
from pathlib import Path
import subprocess
import sys


def get_loop_dir(root: Path) -> Path:
    agents_loop = root / ".agents" / "loop"
    if agents_loop.is_dir():
        return agents_loop
    legacy_loop = root / ".loop"
    if legacy_loop.is_dir():
        return legacy_loop
    return agents_loop


def tool_loop_status(root: Path, _args: dict) -> dict:
    loop_dir = get_loop_dir(root)
    state_file = loop_dir / "loop.json"
    if not state_file.is_file():
        return {"error": f"No active loop found at {state_file}. Initialize .agents/loop or run skills/loop/scripts/init_loop.py first."}
    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
        return {
            "status": data.get("status", "unknown"),
            "iteration": data.get("iteration", 0),
            "champion": data.get("champion", {}),
            "active_front": data.get("active_front", "orient"),
            "loop_path": str(loop_dir),
        }
    except Exception as exc:
        return {"error": f"Failed to parse loop.json: {exc}"}


def tool_loop_step(root: Path, _args: dict) -> dict:
    loop_dir = get_loop_dir(root)
    moves_file = loop_dir / "plans" / "next_moves.json"
    if not moves_file.is_file():
        return {
            "queue_empty": True,
            "directive": "Escalate to First-Principles Diagnostics (diagnose/research front) to replenish next_moves.json."
        }
    try:
        moves = json.loads(moves_file.read_text(encoding="utf-8"))
        if not isinstance(moves, list) or not moves:
            return {
                "queue_empty": True,
                "directive": "Escalate to First-Principles Diagnostics to synthesize 2-3 new hypotheses."
            }
        top_move = moves[0]
        return {
            "queue_empty": False,
            "next_move": top_move,
            "remaining_queue_length": len(moves) - 1
        }
    except Exception as exc:
        return {"error": f"Failed to read next_moves.json: {exc}"}


def tool_loop_journal(root: Path, args: dict) -> dict:
    limit = args.get("limit", 5)
    loop_dir = get_loop_dir(root)
    journal_file = loop_dir / "journal.jsonl"
    if not journal_file.is_file():
        return {"entries": [], "count": 0}
    try:
        lines = [line.strip() for line in journal_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        recent = [json.loads(line) for line in lines[-limit:]]
        return {"entries": recent, "total_recorded": len(lines)}
    except Exception as exc:
        return {"error": f"Failed to parse journal.jsonl: {exc}"}


def tool_loop_verify(root: Path, _args: dict) -> dict:
    loop_dir = get_loop_dir(root)
    profile_file = loop_dir / "knowledge" / "profile.yaml"
    if not profile_file.is_file():
        return {"error": "Missing profile.yaml in knowledge/"}
    # Return verification contract details
    return {
        "status": "ready",
        "message": "Execute pipeline commands defined in profile.yaml under projection wrapping (suppressing stdout). Commit candidate changes before running."
    }


TOOLS = {
    "loop_status": {
        "description": "Inspect active champion, iteration, current front, and status of the autonomous loop.",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": tool_loop_status,
    },
    "loop_step": {
        "description": "Get the highest Expected-Value move from next_moves.json or replenishment directive.",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": tool_loop_step,
    },
    "loop_journal": {
        "description": "Read recent chronological audit entries and receipts from journal.jsonl.",
        "inputSchema": {
            "type": "object",
            "properties": {"limit": {"type": "integer", "default": 5}},
        },
        "handler": tool_loop_journal,
    },
    "loop_verify": {
        "description": "Check verification readiness and rules from repository profile.yaml.",
        "inputSchema": {"type": "object", "properties": {}},
        "handler": tool_loop_verify,
    },
}


def handle_request(request: dict, root: Path) -> dict:
    msg_id = request.get("id")
    method = request.get("method")
    params = request.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "agentic-loop-mcp", "version": "1.0.0"},
            },
        }

    if method == "tools/list":
        tools_list = [
            {"name": name, "description": spec["description"], "inputSchema": spec["inputSchema"]}
            for name, spec in TOOLS.items()
        ]
        return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": tools_list}}

    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        if tool_name not in TOOLS:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"},
            }
        result = TOOLS[tool_name]["handler"](root, arguments)
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
            },
        }

    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": -32601, "message": f"Method not supported: {method}"},
    }


def main():
    root = Path(os.environ.get("AGENTIC_LOOP_ROOT", os.environ.get("OPENLOOP_ROOT", os.getcwd()))).resolve()
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
            response = handle_request(request, root)
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
        except json.JSONDecodeError:
            continue


if __name__ == "__main__":
    main()

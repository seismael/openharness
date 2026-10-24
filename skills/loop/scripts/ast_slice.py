#!/usr/bin/env python3
"""AST Slicer - Zero-dependency semantic code extraction tool.

Extracts targeted functions, methods, or classes from source files to prevent
ingesting entire multi-hundred-line files into LLM context.
Supports Python (native AST) and polyglot fallback (regex-based).
"""

import argparse
import ast
import json
import re
import sys
from pathlib import Path


def extract_python_symbol(source_text: str, file_path: str, target_symbol: str) -> dict | None:
    try:
        tree = ast.parse(source_text, filename=file_path)
    except SyntaxError:
        return None

    lines = source_text.splitlines()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and (
            node.name == target_symbol
        ):
            start_line = node.lineno
            end_line = getattr(node, "end_lineno", start_line)
            # Slice lines (1-indexed)
            sliced_lines = lines[start_line - 1 : end_line]
            kind = "class" if isinstance(node, ast.ClassDef) else "function"
            return {
                "file": file_path,
                "symbol": target_symbol,
                "kind": kind,
                "start_line": start_line,
                "end_line": end_line,
                "total_lines": len(sliced_lines),
                "code": "\n".join(sliced_lines),
            }

    return None


def list_python_symbols(source_text: str, file_path: str) -> list[dict]:
    try:
        tree = ast.parse(source_text, filename=file_path)
    except SyntaxError:
        return []

    symbols = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            kind = "class" if isinstance(node, ast.ClassDef) else "function"
            symbols.append(
                {
                    "symbol": node.name,
                    "kind": kind,
                    "start_line": node.lineno,
                    "end_line": getattr(node, "end_lineno", node.lineno),
                }
            )
    return symbols


def extract_polyglot_symbol(source_text: str, file_path: str, target_symbol: str) -> dict | None:
    lines = source_text.splitlines()
    pattern = re.compile(rf"(?:class|def|fn|func|function|pub fn)\s+{re.escape(target_symbol)}\b")

    start_line = None
    for i, line in enumerate(lines):
        if pattern.search(line):
            start_line = i + 1
            break

    if start_line is None:
        return None

    # Simple brace counter or indentation block
    end_line = len(lines)
    brace_depth = 0
    started_braces = False

    for j in range(start_line - 1, len(lines)):
        line = lines[j]
        brace_depth += line.count("{") - line.count("}")
        if "{" in line:
            started_braces = True
        if started_braces and brace_depth <= 0:
            end_line = j + 1
            break
        # For python indentation fallback
        if (
            not started_braces
            and j > start_line - 1
            and line.strip()
            and not line.startswith(" ")
            and not line.startswith("\t")
        ):
            end_line = j
            break

    sliced_lines = lines[start_line - 1 : end_line]
    return {
        "file": file_path,
        "symbol": target_symbol,
        "kind": "symbol",
        "start_line": start_line,
        "end_line": end_line,
        "total_lines": len(sliced_lines),
        "code": "\n".join(sliced_lines),
    }


def slice_symbol(
    file_path: Path, target_symbol: str | None = None, list_symbols: bool = False
) -> dict:
    if not file_path.exists():
        return {"error": f"File not found: {file_path}"}

    try:
        source_text = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return {"error": f"Failed to read {file_path}: {e}"}

    file_str = str(file_path)

    if list_symbols:
        if file_str.endswith(".py"):
            syms = list_python_symbols(source_text, file_str)
            return {"file": file_str, "symbols": syms}
        return {"file": file_str, "symbols": []}

    if not target_symbol:
        return {"error": "Target symbol required when not listing"}

    res = None
    if file_str.endswith(".py"):
        res = extract_python_symbol(source_text, file_str, target_symbol)

    if res is None:
        res = extract_polyglot_symbol(source_text, file_str, target_symbol)

    if res is None:
        return {"error": f"Symbol '{target_symbol}' not found in {file_str}"}

    return res


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="Path to source file")
    parser.add_argument(
        "symbol", nargs="?", default=None, help="Symbol name (function, class, method)"
    )
    parser.add_argument("--list", action="store_true", help="List all top-level symbols in file")
    parser.add_argument(
        "--raw", action="store_true", help="Print raw code directly instead of JSON"
    )
    args = parser.parse_args(argv)

    result = slice_symbol(args.file.resolve(), args.symbol, args.list)

    if "error" in result:
        print(f"Error: {result['error']}", file=sys.stderr)
        return 1

    if args.raw and "code" in result:
        print(result["code"])
    else:
        print(json.dumps(result, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())

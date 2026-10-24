#!/usr/bin/env python3
"""Regenerate the frozen command snapshots in ``tests/golden``.

Run this only when a command's output is intentionally changed. A refactor that
does not change behavior must leave every snapshot byte-identical, which is what
``tests/test_golden_commands.py`` enforces.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))

from golden_specs import FIXTURES, GOLDEN, SPECS  # noqa: E402

SCRIPTS = ROOT / "skills" / "loop" / "scripts"


def normalize(text: str, root: Path) -> str:
    plain = str(root)
    escaped = plain.replace("\\", "\\\\")
    return text.replace(escaped, "<ROOT>").replace(plain, "<ROOT>")


def invoke(argv: list[str], workdir: Path) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = os.pathsep.join(
        filter(None, [str(SCRIPTS), environment.get("PYTHONPATH", "")])
    )
    return subprocess.run(
        [sys.executable, "-B", *argv],
        cwd=str(workdir),
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=300,
    )


def run_spec(name: str, spec: dict) -> str:
    source = FIXTURES[spec.get("fixture", "harness")]
    workdir = source
    temporary = None
    if spec.get("copies_fixture"):
        temporary = Path(tempfile.mkdtemp(prefix="ohp_golden_"))
        workdir = temporary / source.name
        shutil.copytree(source, workdir)
    try:
        for prelude in spec.get("prelude", ()):
            completed = invoke(["-m", "openharness", *prelude], workdir)
            if completed.returncode != 0:
                raise SystemExit(f"{name} prelude failed: {completed.stderr}")
        script = spec.get("script")
        if script:
            argv = [str(SCRIPTS / script[0]), *script[1:]]
        else:
            argv = ["-m", "openharness", *spec["cli"]]
        completed = invoke(argv, workdir)
        if completed.returncode not in (0, 1, 3):
            raise SystemExit(f"{name} exited {completed.returncode}: {completed.stderr}")
        if "Traceback (most recent call last)" in completed.stderr:
            raise SystemExit(f"{name} raised an exception:\n{completed.stderr}")
        return normalize(completed.stdout, workdir)
    finally:
        if temporary is not None:
            shutil.rmtree(temporary, ignore_errors=True)


def main() -> int:
    GOLDEN.mkdir(parents=True, exist_ok=True)
    for name, spec in SPECS.items():
        text = run_spec(name, spec)
        (GOLDEN / f"{name}.txt").write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote tests/golden/{name}.txt ({len(text.encode('utf-8'))} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Behavior freeze: every command must reproduce its baked snapshot byte-for-byte.

The snapshots in ``tests/golden`` were captured before the package refactor. This
test runs legacy commands through their script path (proving the shim still
behaves) and every command through the unified CLI (proving the port is
faithful).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))

from golden_specs import FIXTURES, GOLDEN, SPECS  # noqa: E402

SCRIPTS = ROOT / "skills" / "loop" / "scripts"


def normalize(text: str, root: Path) -> str:
    plain = str(root)
    escaped = plain.replace("\\", "\\\\")
    return text.replace(escaped, "<ROOT>").replace(plain, "<ROOT>")


class GoldenCommandTests(unittest.TestCase):
    def invoke(self, argv: list[str], workdir: Path) -> subprocess.CompletedProcess[str]:
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

    def workdir(self, spec: dict) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
        source = FIXTURES[spec.get("fixture", "harness")]
        if not spec.get("copies_fixture"):
            return source, None
        temporary = tempfile.TemporaryDirectory(prefix="ohp_golden_")
        target = Path(temporary.name) / source.name
        shutil.copytree(source, target)
        return target, temporary

    def test_snapshots_are_frozen_for_script_and_cli(self):
        for name, spec in SPECS.items():
            expected = (GOLDEN / f"{name}.txt").read_text(encoding="utf-8")
            modes: dict[str, list[str]] = {}
            if spec.get("script"):
                modes["script"] = [
                    str(SCRIPTS / spec["script"][0]),
                    *spec["script"][1:],
                ]
            modes["cli"] = ["-m", "openharness", *spec["cli"]]
            for mode, argv in modes.items():
                with self.subTest(command=name, mode=mode):
                    workdir, temporary = self.workdir(spec)
                    try:
                        for prelude in spec.get("prelude", ()):
                            warmup = self.invoke(["-m", "openharness", *prelude], workdir)
                            self.assertEqual(warmup.returncode, 0, warmup.stderr)
                        completed = self.invoke(argv, workdir)
                    finally:
                        if temporary is not None:
                            temporary.cleanup()
                    self.assertIn(
                        completed.returncode,
                        (0, 1, 3),
                        f"{mode}: {completed.stderr}",
                    )
                    self.assertEqual(
                        normalize(completed.stdout, workdir),
                        expected,
                        f"{mode} output drifted for {name}",
                    )

    def test_version_and_usage_exit_codes(self):
        fixture = FIXTURES["harness"]
        version = self.invoke(["-m", "openharness", "--version"], fixture)
        self.assertEqual(version.returncode, 0, version.stderr)
        self.assertEqual(version.stdout.strip(), "openharness 0.2.0")

        usage = self.invoke(["-m", "openharness"], fixture)
        self.assertEqual(usage.returncode, 2)
        self.assertIn("usage:", usage.stderr.lower())

        unknown = self.invoke(["-m", "openharness", "nope"], fixture)
        self.assertEqual(unknown.returncode, 2)

    def test_repeated_runs_are_byte_identical(self):
        first = self.invoke(
            ["-m", "openharness", "audit", "--manifest", "harness.json"],
            FIXTURES["harness"],
        )
        second = self.invoke(
            ["-m", "openharness", "audit", "--manifest", "harness.json"],
            FIXTURES["harness"],
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)


if __name__ == "__main__":
    unittest.main()

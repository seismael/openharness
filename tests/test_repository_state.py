"""Repository hygiene: fixtures the suite depends on must be committed.

A clean clone once lacked two fixture skill bundles because a root-level
``build/`` ignore rule matched them, so the suite passed only on the machine
that happened to have the untracked files. This guard makes that class of
defect fail loudly instead of silently depending on working-tree state.
"""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"
RUNTIME_ARTIFACTS = {"installed.lock", "selection.json", "mapping.json"}
RUNTIME_SUFFIXES = (".receipt.json",)


def is_runtime_artifact(path: Path) -> bool:
    if path.name in RUNTIME_ARTIFACTS or path.name.endswith(RUNTIME_SUFFIXES):
        return True
    return "__pycache__" in path.parts


class TrackedFixtureTests(unittest.TestCase):
    def test_every_fixture_file_is_committed(self):
        listed = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "-z", "--", "tests/fixtures"],
            capture_output=True,
            check=False,
        )
        self.assertEqual(
            listed.returncode,
            0,
            "git is required to prove fixture files are committed: "
            + listed.stderr.decode("utf-8", "replace"),
        )
        tracked = {
            Path(item.decode("utf-8")).as_posix() for item in listed.stdout.split(b"\0") if item
        }
        present = {
            path.relative_to(ROOT).as_posix()
            for path in FIXTURES.rglob("*")
            if path.is_file() and not is_runtime_artifact(path)
        }
        self.assertEqual(sorted(present - tracked), [])


if __name__ == "__main__":
    unittest.main()

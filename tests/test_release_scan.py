"""The release scan must ignore generated caches but refuse private directories.

Running the test suite writes ``__pycache__`` directories inside the skill
bundles. The release scan previously treated those as shipped release content,
so a checkout passed before ``pytest`` and failed after it. Generated caches are
never part of a bundle; private state directories still are refused.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
SPEC = importlib.util.spec_from_file_location(
    "check_release_under_test", TOOLS / "check_release.py"
)
check_release = importlib.util.module_from_spec(SPEC)
sys.path.insert(0, str(TOOLS))
try:
    SPEC.loader.exec_module(check_release)
finally:
    sys.path.remove(str(TOOLS))


class ReleaseScanTests(unittest.TestCase):
    def scan(self, base: Path, root: Path) -> list[str]:
        errors: list[str] = []
        with patch.object(check_release, "ROOT", root):
            check_release.inspect_path(base, errors)
        return errors

    def test_generated_caches_are_not_release_content(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name).resolve()
            skill = root / "skills" / "demo"
            cache = skill / "__pycache__"
            cache.mkdir(parents=True)
            (cache / "module.cpython-313.pyc").write_bytes(b"")
            (skill / "demo.egg-info").mkdir()
            (skill / "SKILL.md").write_text(
                "---\nname: demo\ndescription: Demo\n---\nBody\n", encoding="utf-8"
            )
            self.assertEqual(self.scan(skill, root), [])

    def test_private_directories_are_still_refused(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name).resolve()
            skill = root / "skills" / "demo"
            (skill / ".venv" / "bin").mkdir(parents=True)
            errors = self.scan(skill, root)
            self.assertTrue(errors)
            self.assertTrue(all("runtime or private path" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()

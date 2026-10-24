"""Exercise the installer CLI using an isolated, synthetic skill repository."""

import contextlib
import importlib.util
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

INSTALLER = Path(__file__).resolve().parents[1] / "tools" / "install_skill.py"


class InstallSkillTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.repository = self.root / "repository"
        (self.repository / "tools").mkdir(parents=True)
        self.cli = self.repository / "tools" / "install_skill.py"
        shutil.copy2(INSTALLER, self.cli)
        self.source = self.repository / "skills" / "enhance"
        (self.source / "references").mkdir(parents=True)
        (self.source / "SKILL.md").write_text(
            "---\nname: enhance\ndescription: Example skill\n---\nBody\n"
        )
        (self.source / "references" / "guide.md").write_text("Example reference\n")
        self.destination = self.root / "new-parent" / "installed-skill"
        spec = importlib.util.spec_from_file_location("install_skill_under_test", self.cli)
        assert spec is not None and spec.loader is not None
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def run_cli(self, *extra, skill="enhance", destination=None, env=None):
        return subprocess.run(
            [
                sys.executable,
                "-B",
                str(self.cli),
                "--skill",
                skill,
                "--to",
                str(destination or self.destination),
                *extra,
            ],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
            env=env,
        )

    def run_inprocess(self, *extra, skill="enhance", destination=None):
        """Run the installer in-process so a simulated link needs no OS privilege."""
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = self.module.main(
                [
                    "--skill",
                    skill,
                    "--to",
                    str(destination or self.destination),
                    *extra,
                ]
            )
        return code, stdout.getvalue(), stderr.getvalue()

    def simulated_symlinks(self, *paths):
        real = Path.is_symlink
        marked = {str(Path(path)) for path in paths}

        def fake(candidate):
            return str(candidate) in marked or real(candidate)

        return patch.object(Path, "is_symlink", fake)

    def assert_refused(self, result):
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn("Error:", result.stderr)

    def test_copies_bundle_and_excludes_runtime_files(self):
        for name in (
            "cache.pyc",
            "activity.log",
            "history.sqlite",
            "history.sqlite-wal",
            "history.db-shm",
        ):
            (self.source / name).write_text("local state")
        for name in ("__pycache__", ".pytest_cache", "logs", "state"):
            (self.source / name).mkdir()
            (self.source / name / "data.txt").write_text("local state")
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        copied = sorted(
            path.relative_to(self.destination).as_posix()
            for path in self.destination.rglob("*")
            if path.is_file()
        )
        self.assertEqual(copied, ["SKILL.md", "references/guide.md"])
        self.assertEqual(
            (self.destination / "references/guide.md").read_text(), "Example reference\n"
        )

    def test_check_reports_plan_without_creating_parent(self):
        before = sorted(str(path.relative_to(self.root)) for path in self.root.rglob("*"))
        result = self.run_cli("--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("would copy 2 files", result.stdout)
        self.assertFalse(self.destination.parent.exists())
        self.assertEqual(
            before, sorted(str(path.relative_to(self.root)) for path in self.root.rglob("*"))
        )

    def test_unicode_destination_with_ascii_output(self):
        destination = self.root / "caf\u00e9" / "\u6280\u80fd"
        env = dict(os.environ, PYTHONIOENCODING="ascii")
        for extra in (("--check",), ()):
            with self.subTest(extra=extra):
                result = self.run_cli(*extra, destination=destination, env=env)
                self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((destination / "SKILL.md").is_file())
        self.assert_refused(self.run_cli(destination=destination, env=env))

    def test_refuses_existing_directory_without_changing_it(self):
        self.destination.mkdir(parents=True)
        sentinel = self.destination / "keep.txt"
        sentinel.write_text("keep")
        for extra in ((), ("--check",)):
            with self.subTest(extra=extra):
                self.assert_refused(self.run_cli(*extra))
        self.assertEqual(list(self.destination.iterdir()), [sentinel])
        self.assertEqual(sentinel.read_text(), "keep")

    def test_refuses_existing_file(self):
        self.destination.parent.mkdir()
        self.destination.write_text("keep")
        self.assert_refused(self.run_cli())
        self.assertEqual(self.destination.read_text(), "keep")

    def test_refuses_skill_traversal_and_invalid_names(self):
        for name in ("../enhance", "enhance/../../outside", "/tmp/enhance", "Enhance", "a" * 65):
            with self.subTest(name=name):
                self.assert_refused(self.run_cli(skill=name))
        self.assertFalse(self.destination.parent.exists())

    def test_refuses_nested_source_destination(self):
        destination = self.source / "nested" / "copy"
        self.assert_refused(self.run_cli(destination=destination))
        self.assertFalse(destination.parent.exists())

    def test_refuses_symlink_in_source_even_if_excluded(self):
        (self.source / "cache.pyc").write_text("local state")
        with self.simulated_symlinks(self.source / "cache.pyc"):
            code, _, stderr = self.run_inprocess()
        self.assertEqual(code, 1)
        self.assertIn("Symlinks are not supported", stderr)
        self.assertFalse(self.destination.parent.exists())

    def test_refuses_symlink_source_ancestor(self):
        with self.simulated_symlinks(self.repository / "skills"):
            code, _, stderr = self.run_inprocess()
        self.assertEqual(code, 1)
        self.assertIn("Symlinks are not supported", stderr)
        self.assertFalse(self.destination.parent.exists())

    def test_refuses_symlink_destination_and_ancestor(self):
        outside = self.root / "outside"
        outside.mkdir()
        with self.simulated_symlinks(self.destination.parent):
            code, _, stderr = self.run_inprocess()
        self.assertEqual(code, 1)
        self.assertIn("Symlinks are not supported", stderr)
        normalized = self.root / "normalized"
        with self.simulated_symlinks(normalized):
            code, _, _ = self.run_inprocess(
                destination=self.destination.parent / ".." / "normalized"
            )
        self.assertEqual(code, 1)
        self.assertEqual(list(outside.iterdir()), [])
        dangling = self.root / "dangling"
        with self.simulated_symlinks(dangling):
            code, _, stderr = self.run_inprocess(destination=dangling)
        self.assertEqual(code, 1)
        self.assertIn("Symlinks are not supported", stderr)


if __name__ == "__main__":
    unittest.main()

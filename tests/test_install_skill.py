"""Exercise the installer CLI using an isolated, synthetic skill repository."""

import errno
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

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

    def symlink(self, target, link, directory=False):
        try:
            link.symlink_to(target, target_is_directory=directory)
        except NotImplementedError:
            self.skipTest("Platform does not support symlinks")
        except OSError as error:
            if (
                error.errno in {errno.ENOSYS, errno.ENOTSUP}
                or getattr(error, "winerror", None) == 1314
            ):
                self.skipTest("Platform does not permit symlink creation")
            raise

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
        self.symlink(self.source / "SKILL.md", self.source / "cache.pyc")
        self.assert_refused(self.run_cli())
        self.assertFalse(self.destination.parent.exists())

    def test_refuses_symlink_source_ancestor(self):
        original = self.repository / "skills"
        moved = self.repository / "real-skills"
        original.rename(moved)
        self.symlink(moved, original, directory=True)
        self.assert_refused(self.run_cli())
        self.assertFalse(self.destination.parent.exists())

    def test_refuses_symlink_destination_and_ancestor(self):
        outside = self.root / "outside"
        outside.mkdir()
        self.symlink(outside, self.destination.parent, directory=True)
        self.assert_refused(self.run_cli())
        self.assert_refused(self.run_cli(destination=self.destination.parent / ".." / "normalized"))
        self.assertEqual(list(outside.iterdir()), [])
        dangling = self.root / "dangling"
        self.symlink(self.root / "missing", dangling)
        self.assert_refused(self.run_cli(destination=dangling))
        self.assertTrue(dangling.is_symlink())


if __name__ == "__main__":
    unittest.main()

"""Regression checks with isolated temporary files; no live config or network."""

import argparse
import contextlib
import importlib.util
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).with_name("change_bundle.py")
SPEC = importlib.util.spec_from_file_location("change_bundle", SCRIPT)
bundle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bundle)


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / "project"
        self.root.mkdir()
        self.target = self.root / "config.jsonc"
        self.original = b'// existing comment\r\n{"value": 1, "unrelated": true}\r\n'
        self.target.write_bytes(self.original)
        self.proposed = self.base / "proposed"
        self.proposed.write_bytes(b'// existing comment\r\n{"value": 2, "unrelated": true}\r\n')
        self.folder = self.base / "bundle"

    def stage(self, extra=None):
        spec = self.base / "spec.json"
        writes = [{"path": str(self.target), "source": str(self.proposed)}]
        writes.extend(extra or [])
        spec.write_text(json.dumps({"roots": [str(self.root)], "writes": writes}))
        with contextlib.redirect_stdout(io.StringIO()):
            bundle.stage(argparse.Namespace(spec=str(spec), bundle=str(self.folder)))
        _, _, digest = bundle.load_bundle(str(self.folder))
        return argparse.Namespace(bundle=str(self.folder), sha256=digest)

    def invoke(self, fn, args):
        with contextlib.redirect_stdout(io.StringIO()):
            fn(args)

    def test_apply_restore_exact_bytes_and_mode(self):
        original_mode = self.target.stat().st_mode & 0o777
        args = self.stage()
        self.assertEqual(self.target.read_bytes(), self.original)
        self.invoke(bundle.apply, args)
        self.assertEqual(self.target.read_bytes(), self.proposed.read_bytes())
        self.assertEqual(self.target.stat().st_mode & 0o777, original_mode)
        self.invoke(bundle.rollback, args)
        self.assertEqual(self.target.read_bytes(), self.original)
        self.assertEqual(self.target.stat().st_mode & 0o777, original_mode)
        self.invoke(bundle.rollback, args)

    def test_created_file_removed_on_rollback(self):
        created = self.root / "agents" / "new.md"
        args = self.stage([{"path": str(created), "source": str(self.proposed)}])
        self.invoke(bundle.apply, args)
        self.assertTrue(created.is_file())
        self.invoke(bundle.rollback, args)
        self.assertFalse(created.exists())

    def test_preapply_drift_changes_nothing(self):
        second = self.root / "second"
        args = self.stage([{"path": str(second), "source": str(self.proposed)}])
        second.write_text("someone else created this")
        with self.assertRaisesRegex(ValueError, "drift"):
            self.invoke(bundle.apply, args)
        self.assertEqual(self.target.read_bytes(), self.original)

    def test_wrong_digest_changes_nothing(self):
        args = self.stage()
        args.sha256 = "0" * 64
        with self.assertRaisesRegex(ValueError, "hash"):
            self.invoke(bundle.apply, args)
        self.assertEqual(self.target.read_bytes(), self.original)

    def test_rollback_preserves_later_edits(self):
        args = self.stage()
        self.invoke(bundle.apply, args)
        self.target.write_text("later user edit")
        with self.assertRaisesRegex(ValueError, "drift"):
            self.invoke(bundle.rollback, args)
        self.assertEqual(self.target.read_text(), "later user edit")

    def test_partial_apply_can_recover(self):
        second = self.root / "second"
        args = self.stage([{"path": str(second), "source": str(self.proposed)}])
        real_write = bundle.atomic_write

        def fail_second(path, data, mode):
            if path == second:
                raise OSError("simulated write failure")
            return real_write(path, data, mode)

        with (
            patch.object(bundle, "atomic_write", side_effect=fail_second),
            self.assertRaisesRegex(OSError, "simulated"),
        ):
            self.invoke(bundle.apply, args)
        self.assertEqual(self.target.read_bytes(), self.proposed.read_bytes())
        self.invoke(bundle.rollback, args)
        self.assertEqual(self.target.read_bytes(), self.original)
        self.assertFalse(second.exists())

    def test_noops_omitted_and_bundle_not_reapplied(self):
        self.proposed.write_bytes(self.original)
        args = self.stage()
        _, plan, _ = bundle.load_bundle(str(self.folder))
        self.assertEqual(plan["files"], [])
        self.invoke(bundle.apply, args)
        with self.assertRaisesRegex(ValueError, "already attempted"):
            self.invoke(bundle.apply, args)

    def test_out_of_scope_refused(self):
        with self.assertRaisesRegex(ValueError, "outside scope"):
            self.stage([{"path": str(self.base / "outside"), "source": str(self.proposed)}])
        self.assertFalse(self.folder.exists())

    def simulated_symlinks(self, *paths):
        """Mark paths as links so the guard is exercised without OS privileges."""
        real = Path.is_symlink
        marked = {str(Path(path)) for path in paths}

        def fake(candidate):
            return str(candidate) in marked or real(candidate)

        return patch.object(Path, "is_symlink", fake)

    def test_symlink_refused(self):
        link = self.root / "linked"
        with self.simulated_symlinks(link), self.assertRaisesRegex(ValueError, "Symlink"):
            self.stage([{"path": str(link), "source": str(self.proposed)}])
        self.assertFalse(self.folder.exists())

    def test_nested_file_targets_refused(self):
        missing = self.root / "missing"
        with self.assertRaisesRegex(ValueError, "Nested"):
            self.stage(
                [
                    {"path": str(missing), "source": str(self.proposed)},
                    {"path": str(missing / "child"), "source": str(self.proposed)},
                ]
            )

    def test_cli_review_default_does_not_print_content(self):
        args = self.stage()
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "review", "--bundle", args.bundle],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertNotIn("unrelated", result.stdout)
        self.assertIn(args.sha256, result.stdout)

    def test_cli_nonobject_json_is_a_clean_error(self):
        args = self.stage()
        plan_path = self.folder / "bundle.json"
        original_plan = plan_path.read_bytes()
        for command, path, options in [
            (
                "stage",
                self.base / "invalid-spec.json",
                [
                    "--spec",
                    str(self.base / "invalid-spec.json"),
                    "--bundle",
                    str(self.base / "unused"),
                ],
            ),
            ("review", plan_path, ["--bundle", args.bundle]),
            (
                "rollback",
                self.folder / "journal.json",
                ["--bundle", args.bundle, "--sha256", args.sha256],
            ),
        ]:
            with self.subTest(command=command):
                plan_path.write_bytes(original_plan)
                path.write_text("[]", encoding="utf-8")
                result = subprocess.run(
                    [sys.executable, str(SCRIPT), command, *options], capture_output=True, text=True
                )
                self.assertEqual(result.returncode, 1)
                self.assertIn("ERROR:", result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(self.target.read_bytes(), self.original)

    def test_malformed_bundle_fields_refused(self):
        self.stage()
        plan_path = self.folder / "bundle.json"
        original_plan = plan_path.read_text(encoding="utf-8")
        mutations = [
            lambda plan: plan.update(version=True),
            lambda plan: plan.update(roots=str(self.root)),
            lambda plan: plan.update(files={}),
            lambda plan: plan.update(files=[[]]),
            lambda plan: plan["files"][0].update(mode=True, before_mode=True),
            lambda plan: plan["files"][0].update(before=None, before_sha256=None),
            lambda plan: plan["files"][0].update(after=7),
            lambda plan: plan["files"][0].update(after_sha256="0" * 64),
        ]
        for index, mutate in enumerate(mutations):
            with self.subTest(case=index):
                plan = json.loads(original_plan)
                mutate(plan)
                plan_path.write_text(json.dumps(plan), encoding="utf-8")
                with self.assertRaises(ValueError):
                    bundle.load_bundle(str(self.folder))
                self.assertEqual(self.target.read_bytes(), self.original)

    def test_boolean_journal_index_refused_without_rollback(self):
        args = self.stage()
        self.invoke(bundle.apply, args)
        journal = self.folder / "journal.json"
        journal.write_text(
            json.dumps({"sha256": args.sha256, "state": "applied", "attempted": [False]}),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "Invalid journal"):
            self.invoke(bundle.rollback, args)
        self.assertEqual(self.target.read_bytes(), self.proposed.read_bytes())

    def test_bundle_limit_includes_paths_and_metadata_before_creation(self):
        self.proposed.write_bytes(b"x")
        extra = [
            {"path": str(self.root / ("config-" + str(index))), "source": str(self.proposed)}
            for index in range(500)
        ]
        spec = {
            "roots": [str(self.root)],
            "writes": [{"path": str(self.target), "source": str(self.proposed)}, *extra],
        }
        limit = max(70000, len(json.dumps(spec).encode("utf-8")) + 1024)
        with (
            patch.object(bundle, "LIMIT", limit),
            self.assertRaisesRegex(ValueError, "Bundle too large"),
        ):
            self.stage(extra)
        self.assertFalse(self.folder.exists())
        self.assertEqual(self.target.read_bytes(), self.original)

    def test_permission_drift_refused_before_apply(self):
        args = self.stage()
        self.target.chmod(0o400)
        with self.assertRaisesRegex(ValueError, "drift"):
            self.invoke(bundle.apply, args)
        self.assertEqual(self.target.read_bytes(), self.original)
        self.assertFalse((self.folder / "journal.json").exists())

    def test_new_files_and_bundle_are_private_with_permissive_umask(self):
        created = self.root / "new.json"
        requested = []
        real_chmod = os.chmod
        real_mkdir = Path.mkdir

        def chmod(path, mode, *args, **kwargs):
            requested.append(stat.S_IMODE(mode))
            return real_chmod(path, mode, *args, **kwargs)

        def mkdir(path, *args, **kwargs):
            if kwargs.get("mode") is not None:
                requested.append(kwargs["mode"])
            return real_mkdir(path, *args, **kwargs)

        old_umask = os.umask(0)
        try:
            with (
                patch.object(bundle.os, "chmod", chmod),
                patch.object(Path, "mkdir", mkdir),
            ):
                args = self.stage([{"path": str(created), "source": str(self.proposed)}])
                self.invoke(bundle.apply, args)
        finally:
            os.umask(old_umask)
        self.assertIn(0o700, requested)
        self.assertIn(0o600, requested)
        if os.name != "nt":
            self.assertEqual(stat.S_IMODE(self.folder.stat().st_mode), 0o700)
            for path in [created, self.folder / "bundle.json", self.folder / "journal.json"]:
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_symlink_introduced_after_stage_refused(self):
        args = self.stage()
        self.target.unlink()
        with self.simulated_symlinks(self.target), self.assertRaisesRegex(ValueError, "Symlink"):
            self.invoke(bundle.apply, args)
        self.assertFalse(self.target.exists())
        self.assertFalse((self.folder / "journal.json").exists())

    def test_hardlinked_target_refused(self):
        try:
            os.link(self.target, self.root / "alias")
        except OSError:
            self.skipTest("hardlinks unavailable")
        with self.assertRaisesRegex(ValueError, "single-link"):
            self.stage()
        self.assertFalse(self.folder.exists())

    def test_invalid_utf8_and_duplicate_targets_refused(self):
        self.proposed.write_bytes(b"\xff")
        with self.assertRaises(UnicodeDecodeError):
            self.stage()
        self.proposed.write_bytes(b"valid")
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.stage([{"path": str(self.target), "source": str(self.proposed)}])
        self.assertFalse(self.folder.exists())
        self.assertEqual(self.target.read_bytes(), self.original)

    def test_keyboard_interrupt_after_replacement_can_recover(self):
        args = self.stage()
        real_write = bundle.atomic_write

        def interrupt_after_write(path, data, mode):
            real_write(path, data, mode)
            if path == self.target:
                raise KeyboardInterrupt()

        with (
            patch.object(bundle, "atomic_write", side_effect=interrupt_after_write),
            self.assertRaises(KeyboardInterrupt),
        ):
            self.invoke(bundle.apply, args)
        journal = json.loads((self.folder / "journal.json").read_text())
        self.assertEqual(journal["state"], "applying")
        self.assertEqual(journal["attempted"], [0])
        self.invoke(bundle.rollback, args)
        self.assertEqual(self.target.read_bytes(), self.original)

    def test_interrupted_rollback_can_be_retried(self):
        second = self.root / "second"
        second.write_bytes(b"second original")
        args = self.stage([{"path": str(second), "source": str(self.proposed)}])
        self.invoke(bundle.apply, args)
        real_write = bundle.atomic_write

        def interrupt_after_write(path, data, mode):
            real_write(path, data, mode)
            if path == second:
                raise KeyboardInterrupt()

        with (
            patch.object(bundle, "atomic_write", side_effect=interrupt_after_write),
            self.assertRaises(KeyboardInterrupt),
        ):
            self.invoke(bundle.rollback, args)
        self.assertEqual(second.read_bytes(), b"second original")
        self.invoke(bundle.rollback, args)
        self.assertEqual(self.target.read_bytes(), self.original)
        self.assertEqual(second.read_bytes(), b"second original")

    def test_failed_replacement_cleans_readonly_temporary(self):
        self.target.chmod(0o444)
        self.addCleanup(self.target.chmod, 0o600)
        real_unlink = os.unlink
        removed = []

        def require_writable_before_unlink(path):
            self.assertTrue(Path(path).stat().st_mode & stat.S_IWUSR)
            removed.append(path)
            real_unlink(path)

        with (
            patch.object(bundle.os, "replace", side_effect=PermissionError("replacement refused")),
            patch.object(bundle.os, "unlink", side_effect=require_writable_before_unlink),
            self.assertRaisesRegex(PermissionError, "replacement refused"),
        ):
            bundle.atomic_write(self.target, b"proposed", 0o444)
        self.assertEqual(len(removed), 1)
        self.assertEqual(list(self.root.glob(".characterize-*")), [])
        self.assertEqual(self.target.read_bytes(), self.original)


if __name__ == "__main__":
    unittest.main()

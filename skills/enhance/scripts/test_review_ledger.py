# ruff: noqa: RUF001 -- unicode session and source values are deliberate test data
"""Run with python3 -B -m unittest discover -s <skill>/scripts -p test_review_ledger.py."""

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

SCRIPT = Path(__file__).with_name("review_ledger.py").resolve()


class LedgerTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="enhance-ledger-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.db = self.root / "review.sqlite3"

    def run_cli(self, *args, ok=True):
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "--db", str(self.db), *args],
            cwd=self.root,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0 if ok else 1, result.stderr)
        return json.loads(result.stdout if ok else result.stderr)

    def load(self, sessions, source="tool:profile", ok=True):
        path = self.root / "manifest.json"
        path.write_text(json.dumps({"source": source, "sessions": sessions}), encoding="utf-8")
        return self.run_cli("inventory", "--manifest", str(path), ok=ok)

    @staticmethod
    def session(id="s2", revision="r1"):
        return dict(id=id, revision=revision, locator=f"session:{id}", project="project:one")

    def record(self, status="reviewed", revision="r1", session="s2", **kwargs):
        return self.run_cli(
            "record",
            "--source",
            "tool:profile",
            "--session",
            session,
            "--revision",
            revision,
            "--status",
            status,
            "--cursor",
            "message:9",
            **kwargs,
        )

    def test_unchanged_idempotent_and_late_session(self):
        self.assertEqual(self.load([self.session()])["added"], 1)
        self.record()
        before = self.run_cli("show")
        self.assertEqual(self.load([self.session()])["unchanged"], 1)
        self.assertFalse(self.record()["changed"])
        self.assertEqual(self.run_cli("show"), before)
        self.load([self.session("s1")])  # Older ID arrives after review; absent s2 retained.
        result = self.run_cli("show")
        self.assertEqual(result["counts"]["total"], 2)
        self.assertEqual([r["session"] for r in result["pending"]], ["s1"])
        self.assertEqual(self.run_cli("pending", "--source", "another"), [])

    def test_appended_revision_partial_blocked_and_stale_atomicity(self):
        self.load([self.session()])
        self.record()
        self.load([self.session(revision="r2")])
        result = self.run_cli("show")
        row = result["sessions"][0]
        self.assertEqual(
            (row["latest_status"], row["last_reviewed_revision"], row["last_reviewed_cursor"]),
            ("unreviewed", "r1", "message:9"),
        )
        self.assertIsNone(row["cursor"])
        self.assertIn("stale", self.record(ok=False)["error"])
        self.assertEqual(self.run_cli("show"), result)
        for status in ("partial", "blocked"):
            self.record(status, "r2")
            row = self.run_cli("pending")[0]
            self.assertEqual(row["latest_status"], status)
            self.assertEqual(row["last_reviewed_revision"], "r1")
        self.record("reviewed", "r2")
        self.assertEqual(self.run_cli("pending"), [])

    def test_duplicate_manifest_has_no_partial_mutation(self):
        self.load([self.session()])
        before = self.run_cli("show")
        error = self.load([self.session("new"), self.session(), self.session()], ok=False)
        self.assertIn("duplicate", error["error"])
        self.assertEqual(self.run_cli("show"), before)

    def test_prior_checkpoint_survives_revision_changes_without_certifying_coverage(self):
        self.load([self.session()])
        self.run_cli(
            "record",
            "--source",
            "tool:profile",
            "--session",
            "s2",
            "--revision",
            "r1",
            "--status",
            "partial",
            "--cursor",
            "event:40",
            "--note",
            "Through event 40.",
        )
        self.assertIsNone(self.run_cli("pending")[0]["prior_checkpoint_revision"])
        self.load([self.session(revision="r2")])
        row = self.run_cli("pending")[0]
        self.assertEqual(
            (row["latest_revision"], row["latest_status"], row["cursor"], row["note"]),
            ("r2", "unreviewed", None, None),
        )
        self.assertEqual(
            (
                row["prior_checkpoint_revision"],
                row["prior_checkpoint_status"],
                row["prior_checkpoint_cursor"],
                row["prior_checkpoint_note"],
            ),
            ("r1", "partial", "event:40", "Through event 40."),
        )
        self.assertIsNone(row["last_reviewed_revision"])
        self.record(revision="r2")
        row = self.run_cli("show")["sessions"][0]
        self.assertEqual(
            (row["latest_status"], row["last_reviewed_revision"], row["prior_checkpoint_revision"]),
            ("reviewed", "r2", "r1"),
        )
        self.load([self.session(revision="r3")])
        self.record(status="blocked", revision="r3")
        self.load([self.session(revision="r4")])
        row = self.run_cli("pending")[0]
        self.assertEqual(
            (
                row["latest_status"],
                row["cursor"],
                row["last_reviewed_revision"],
                row["prior_checkpoint_revision"],
                row["prior_checkpoint_status"],
                row["prior_checkpoint_cursor"],
            ),
            ("unreviewed", None, "r2", "r3", "blocked", "message:9"),
        )
        self.assertEqual(self.run_cli("show", "--summary")["counts"]["pending"], 1)

    def test_decision_does_not_change_review_coverage(self):
        self.load([self.session()])
        before = self.run_cli("show")
        path = self.root / "decision.json"
        decision = dict(
            id="d1",
            scope="global:tool:profile",
            status="proposed",
            evidence=[dict(source="tool:profile", session="s2", revision="r1")],
            rationale="Compact\n outputs\x00 help.",
            target="config:global",
            before_hash="sha256:before",
            after_hash="sha256:after",
        )
        path.write_text(json.dumps(decision), encoding="utf-8")
        self.assertTrue(self.run_cli("decision", "--file", str(path))["changed"])
        self.assertFalse(self.run_cli("decision", "--file", str(path))["changed"])
        result = self.run_cli("decisions")[0]["decision"]
        self.assertEqual(result["rationale"], "Compact outputs help.")
        self.assertEqual(result["evidence"], decision["evidence"])
        decision["status"] = "verified"
        path.write_text(json.dumps(decision), encoding="utf-8")
        self.run_cli("decision", "--file", str(path))
        self.assertEqual(self.run_cli("decisions")[0]["decision"]["status"], "verified")
        self.assertEqual(self.run_cli("show"), before)

    def test_reject_unknown_and_unversioned_database(self):
        for version in (99, 0):
            with self.subTest(version=version):
                if self.db.exists():
                    self.db.unlink()
                with closing(sqlite3.connect(self.db)) as db, db:
                    db.execute("CREATE TABLE sentinel (value TEXT)")
                    db.execute("INSERT INTO sentinel VALUES ('keep')")
                    db.execute(f"PRAGMA user_version={version}")
                self.assertIn("database", self.run_cli("show", ok=False)["error"])
                with closing(sqlite3.connect(self.db)) as db, db:
                    self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], version)
                    self.assertEqual(db.execute("SELECT value FROM sentinel").fetchone()[0], "keep")
                    self.assertEqual(
                        db.execute(
                            "SELECT count(*) FROM sqlite_master WHERE type='table'"
                        ).fetchone()[0],
                        1,
                    )

    def test_reject_raw_payload_and_bound_notes(self):
        invalid = self.session()
        invalid["transcript"] = "not accepted"
        self.load([invalid], ok=False)
        self.load([self.session()])
        self.run_cli(
            "record",
            "--source",
            "tool:profile",
            "--session",
            "s2",
            "--revision",
            "r1",
            "--status",
            "partial",
            "--note",
            "x" * 513,
            ok=False,
        )
        self.assertEqual(self.run_cli("pending")[0]["latest_status"], "unreviewed")

    def test_concurrent_inventories_preserve_both_sessions(self):
        processes = []
        for index in range(4):
            path = self.root / f"manifest-{index}.json"
            path.write_text(
                json.dumps({"source": "tool:profile", "sessions": [self.session(f"s{index}")]}),
                encoding="utf-8",
            )
            processes.append(
                subprocess.Popen(
                    [
                        sys.executable,
                        "-B",
                        str(SCRIPT),
                        "--db",
                        str(self.db),
                        "inventory",
                        "--manifest",
                        str(path),
                    ],
                    cwd=self.root,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
            )
        for process in processes:
            stdout, stderr = process.communicate(timeout=35)
            self.assertEqual(process.returncode, 0, stderr)
            self.assertEqual(json.loads(stdout)["added"], 1)
        self.assertEqual(self.run_cli("show")["counts"]["total"], 4)

    def test_pagination_and_compact_summary(self):
        self.load([self.session(f"s{index}") for index in range(4)])
        self.record(session="s1")
        self.assertEqual(
            [row["session"] for row in self.run_cli("pending", "--limit", "1", "--offset", "1")],
            ["s2"],
        )
        self.assertEqual(len(self.run_cli("pending", "--offset", "2")), 1)
        self.assertEqual(self.run_cli("pending", "--offset", "99"), [])
        full, compact = self.run_cli("show"), self.run_cli("show", "--summary")
        self.assertEqual(
            compact, {"schema_version": full["schema_version"], "counts": full["counts"]}
        )
        path = self.root / "decisions.json"
        for index in range(3):
            path.write_text(
                json.dumps(
                    dict(
                        id=f"d{index}",
                        scope="global:tool",
                        status="proposed",
                        evidence=[dict(source="tool:profile", session="s0", revision="r1")],
                    )
                ),
                encoding="utf-8",
            )
            self.run_cli("decision", "--file", str(path))
        page = self.run_cli("decisions", "--limit", "1", "--offset", "1")
        self.assertEqual([row["decision"]["id"] for row in page], ["d1"])
        for command, flag, value in (("pending", "--limit", "0"), ("decisions", "--offset", "-1")):
            result = subprocess.run(
                [sys.executable, "-B", str(SCRIPT), "--db", str(self.db), command, flag, value],
                cwd=self.root,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2)

    def test_collect_pending_worklist_before_recording_reviews(self):
        self.load([self.session(f"s{index}") for index in range(6)])
        self.record(session="s1")
        self.record(status="blocked", session="s3")
        worklist = []
        while True:
            page = self.run_cli("pending", "--limit", "2", "--offset", str(len(worklist)))
            if not page:
                break
            worklist.extend(page)
        self.assertEqual([row["session"] for row in worklist], ["s0", "s2", "s3", "s4", "s5"])
        # Only mutate coverage after enumeration; an unresolved row can remain pending.
        for row in worklist:
            if row["latest_status"] != "blocked":
                self.record(session=row["session"], revision=row["latest_revision"])
        self.assertEqual([row["session"] for row in self.run_cli("pending")], ["s3"])
        self.assertEqual(self.run_cli("show", "--summary")["counts"]["reviewed"], 5)

    def test_non_ascii_metadata_round_trips_under_ascii_output(self):
        env = dict(os.environ, PYTHONIOENCODING="ascii:strict")

        def ascii_cli(*args, ok=True):
            result = subprocess.run(
                [sys.executable, "-B", str(SCRIPT), "--db", str(self.db), *args],
                cwd=self.root,
                capture_output=True,
                env=env,
            )
            self.assertEqual(result.returncode, 0 if ok else 1, result.stderr)
            return json.loads((result.stdout if ok else result.stderr).decode("ascii"))

        path = self.root / "manifest.json"
        row = self.session(id="会話")
        manifest = dict(source="profile:α", sessions=[row])
        path.write_text(json.dumps(manifest), encoding="utf-8")
        result = ascii_cli("inventory", "--manifest", str(path))
        self.assertEqual((result["source"], result["added"]), ("profile:α", 1))
        before = ascii_cli("show")
        self.assertEqual(before["sessions"][0]["session"], "会話")
        decision = dict(
            id="décision",
            scope="global:profile:α",
            status="proposed",
            evidence=[dict(source="profile:α", session="会話", revision="r1")],
        )
        path.write_text(json.dumps(decision), encoding="utf-8")
        self.assertEqual(ascii_cli("decision", "--file", str(path))["id"], "décision")
        self.assertEqual(ascii_cli("decisions")[0]["decision"], decision)
        manifest["sessions"].append(row)
        path.write_text(json.dumps(manifest), encoding="utf-8")
        error = ascii_cli("inventory", "--manifest", str(path), ok=False)
        self.assertEqual(error["error"], "duplicate session id: 会話")
        self.assertEqual(ascii_cli("show"), before)


if __name__ == "__main__":
    unittest.main()

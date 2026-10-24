#!/usr/bin/env python3
"""Metadata-only incremental review ledger. Python 3 standard library; JSON I/O.

Locators are never opened. Callers supply stable identities and fingerprints,
exclude secrets/transcripts, and review actual content before recording coverage.
Each inventory is authoritative for revisions it includes, never for deletions.
"""

import argparse
import json
import sqlite3
import sys
import unicodedata
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

VERSION = 1
REVIEW_STATUSES = ("partial", "reviewed", "blocked")
DECISION_STATUSES = (
    "proposed",
    "applied",
    "verified",
    "rejected",
    "deferred",
    "reverted",
    "failed",
)
SCHEMA = (
    "CREATE TABLE sessions (source TEXT, id TEXT, revision TEXT NOT NULL, "
    "locator TEXT NOT NULL, project TEXT, first_seen TEXT NOT NULL, "
    "last_changed TEXT NOT NULL, PRIMARY KEY(source,id))",
    "CREATE TABLE reviews (source TEXT, session TEXT, revision TEXT, "
    "status TEXT NOT NULL CHECK(status IN ('partial','reviewed','blocked')), "
    "cursor TEXT, note TEXT, updated TEXT NOT NULL, "
    "PRIMARY KEY(source,session,revision), "
    "FOREIGN KEY(source,session) REFERENCES sessions(source,id))",
    "CREATE TABLE decisions (id TEXT PRIMARY KEY, data TEXT NOT NULL, updated TEXT NOT NULL)",
)


def stamp():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def string(value, field, limit=512, nullable=False):
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f"{field} must be a nonempty string of at most {limit} characters")
    if any(unicodedata.category(c).startswith("C") for c in value):
        raise ValueError(f"{field} contains control or invisible formatting characters")
    return value


def note(value, field="note"):
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    value = " ".join(
        "".join(" " if unicodedata.category(c).startswith("C") else c for c in value).split()
    )
    if len(value) > 512:
        raise ValueError(f"{field} exceeds 512 sanitized characters")
    return value or None


def fields(obj, required, optional=()):
    if not isinstance(obj, dict) or not set(required) <= obj.keys():
        raise ValueError(f"expected object with fields: {', '.join(required)}")
    if obj.keys() - set(required) - set(optional):
        raise ValueError("unexpected fields; supply compact metadata only")


def read_json(path):
    if Path(path).stat().st_size > 16 * 1024 * 1024:
        raise ValueError("metadata file exceeds 16 MiB")
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def manifest(path):
    obj = read_json(path)
    fields(obj, ("source", "sessions"))
    string(obj["source"], "source")
    if not isinstance(obj["sessions"], list):
        raise ValueError("sessions must be an array")
    seen = set()
    for row in obj["sessions"]:
        fields(row, ("id", "revision", "locator", "project"))
        for key in ("id", "revision", "locator"):
            string(row[key], key, 2048 if key == "locator" else 512)
        string(row["project"], "project", nullable=True)
        if row["id"] in seen:
            raise ValueError(f"duplicate session id: {row['id']}")
        seen.add(row["id"])
    return obj


def decision(path):
    obj = read_json(path)
    fields(
        obj,
        ("id", "scope", "evidence", "status"),
        ("rationale", "target", "before_hash", "after_hash", "verification"),
    )
    for key in ("id", "scope", "status", "before_hash", "after_hash", "target"):
        if key in obj:
            string(obj[key], key, 2048 if key == "target" else 512)
    if obj["status"] not in DECISION_STATUSES:
        raise ValueError("invalid decision status")
    if not isinstance(obj["evidence"], list) or not 1 <= len(obj["evidence"]) <= 100:
        raise ValueError("evidence must contain 1 to 100 compact references")
    for ref in obj["evidence"]:
        fields(ref, ("source", "session", "revision"), ("locator",))
        for key, value in ref.items():
            string(value, key, 2048 if key == "locator" else 512)
    for key in ("rationale", "verification"):
        if key in obj:
            obj[key] = note(obj[key], key)
    return obj


@contextmanager
def database(path):
    db = sqlite3.connect(path, timeout=30, isolation_level=None)
    db.row_factory = sqlite3.Row
    try:
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("BEGIN IMMEDIATE")  # Serialized writers; checks and writes are atomic.
        version = db.execute("PRAGMA user_version").fetchone()[0]
        if version == 0:
            if db.execute("SELECT 1 FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchone():
                raise ValueError("refusing unversioned nonempty database")
            for sql in SCHEMA:
                db.execute(sql)
            db.execute(f"PRAGMA user_version={VERSION}")
        elif version != VERSION:
            raise ValueError(f"unsupported database version {version}; expected {VERSION}")
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def inventory(db, obj):
    counts = dict(added=0, changed=0, unchanged=0)
    now = stamp()
    for row in obj["sessions"]:
        old = db.execute(
            "SELECT revision,locator,project FROM sessions WHERE source=? AND id=?",
            (obj["source"], row["id"]),
        ).fetchone()
        values = (row["revision"], row["locator"], row["project"])
        if old is None:
            db.execute(
                "INSERT INTO sessions VALUES (?,?,?,?,?,?,?)",
                (obj["source"], row["id"], *values, now, now),
            )
            counts["added"] += 1
        elif tuple(old) != values:
            db.execute(
                "UPDATE sessions SET revision=?,locator=?,project=?,last_changed=? "
                "WHERE source=? AND id=?",
                (*values, now, obj["source"], row["id"]),
            )
            counts["changed"] += 1
        else:
            counts["unchanged"] += 1
    return {"source": obj["source"], **counts}


def coverage(db, source=None, pending_only=False, limit=None, offset=0):
    conditions, params = [], []
    if source is not None:
        conditions.append("s.source=?")
        params.append(source)
    if pending_only:
        conditions.append("(r.status IS NULL OR r.status<>'reviewed')")
    where = "WHERE " + " AND ".join(conditions) + " " if conditions else ""
    params.extend((limit if limit is not None else -1, offset))
    rows = db.execute(
        "SELECT s.source,s.id AS session,s.revision AS latest_revision,s.locator,s.project,"
        "COALESCE(r.status,'unreviewed') AS latest_status,r.cursor,r.note,r.updated AS review_updated,"
        "(SELECT revision FROM reviews WHERE source=s.source AND session=s.id AND status='reviewed' "
        "ORDER BY updated DESC,revision DESC LIMIT 1) AS last_reviewed_revision,"
        "(SELECT cursor FROM reviews WHERE source=s.source AND session=s.id AND status='reviewed' "
        "ORDER BY updated DESC,revision DESC LIMIT 1) AS last_reviewed_cursor,"
        "p.revision AS prior_checkpoint_revision,p.status AS prior_checkpoint_status,"
        "p.cursor AS prior_checkpoint_cursor,p.note AS prior_checkpoint_note "
        "FROM sessions s LEFT JOIN reviews r ON r.source=s.source AND r.session=s.id "
        "AND r.revision=s.revision "
        "LEFT JOIN reviews p ON p.source=s.source AND p.session=s.id AND p.revision="
        "(SELECT revision FROM reviews WHERE source=s.source AND session=s.id AND revision<>s.revision "
        "ORDER BY updated DESC,revision DESC LIMIT 1) "
        + where
        + "ORDER BY s.source,s.id LIMIT ? OFFSET ?",
        params,
    ).fetchall()
    return [dict(row) for row in rows]


def summary(db):
    counts = dict.fromkeys(("unreviewed", *REVIEW_STATUSES), 0)
    for row in db.execute(
        "SELECT COALESCE(r.status,'unreviewed') AS status,count(*) AS n "
        "FROM sessions s LEFT JOIN reviews r ON r.source=s.source AND r.session=s.id "
        "AND r.revision=s.revision GROUP BY COALESCE(r.status,'unreviewed')"
    ):
        counts[row["status"]] = row["n"]
    total = sum(counts.values())
    return {
        "schema_version": VERSION,
        "counts": {"total": total, "pending": total - counts["reviewed"], **counts},
    }


def record(db, args):
    for key in ("source", "session", "revision"):
        string(getattr(args, key), key)
    cursor = string(args.cursor, "cursor", 2048, nullable=True)
    clean_note = note(args.note)
    current = db.execute(
        "SELECT revision FROM sessions WHERE source=? AND id=?", (args.source, args.session)
    ).fetchone()
    if current is None or current[0] != args.revision:
        raise ValueError(
            "unknown session or stale revision; inventory and review latest content first"
        )
    old = db.execute(
        "SELECT status,cursor,note FROM reviews WHERE source=? AND session=? AND revision=?",
        (args.source, args.session, args.revision),
    ).fetchone()
    values = (args.status, cursor, clean_note)
    if old is not None and tuple(old) == values:
        return {"changed": False, "status": args.status}
    db.execute(
        "INSERT INTO reviews VALUES (?,?,?,?,?,?,?) ON CONFLICT(source,session,revision) "
        "DO UPDATE SET status=excluded.status,cursor=excluded.cursor,note=excluded.note,"
        "updated=excluded.updated",
        (args.source, args.session, args.revision, *values, stamp()),
    )
    return {"changed": True, "status": args.status}


def save_decision(db, obj):
    data = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    old = db.execute("SELECT data FROM decisions WHERE id=?", (obj["id"],)).fetchone()
    if old and old[0] == data:
        return {"id": obj["id"], "changed": False}
    db.execute(
        "INSERT INTO decisions VALUES (?,?,?) ON CONFLICT(id) DO UPDATE "
        "SET data=excluded.data,updated=excluded.updated",
        (obj["id"], data, stamp()),
    )
    return {"id": obj["id"], "changed": True}


def integer_at_least(minimum):
    def parse(value):
        try:
            number = int(value)
        except ValueError:
            raise argparse.ArgumentTypeError("must be an integer") from None
        if number < minimum:
            raise argparse.ArgumentTypeError(f"must be at least {minimum}")
        return number

    return parse


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db", required=True, help="SQLite metadata ledger; parent directory must exist"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("inventory").add_argument("--manifest", required=True)
    pending_parser = sub.add_parser("pending")
    pending_parser.add_argument("--source")
    review = sub.add_parser("record")
    for key in ("source", "session", "revision"):
        review.add_argument("--" + key, required=True)
    review.add_argument("--status", required=True, choices=REVIEW_STATUSES)
    review.add_argument("--cursor")
    review.add_argument("--note")
    sub.add_parser("show").add_argument("--summary", action="store_true")
    sub.add_parser("decision").add_argument("--file", required=True)
    decisions_parser = sub.add_parser("decisions")
    for paginated in (pending_parser, decisions_parser):
        paginated.add_argument("--limit", type=integer_at_least(1))
        paginated.add_argument("--offset", type=integer_at_least(0), default=0)
    args = parser.parse_args(argv)
    try:
        obj = (
            manifest(args.manifest)
            if args.command == "inventory"
            else (decision(args.file) if args.command == "decision" else None)
        )
        with database(args.db) as db:
            if args.command == "inventory":
                result = inventory(db, obj)
            elif args.command == "record":
                result = record(db, args)
            elif args.command == "decision":
                result = save_decision(db, obj)
            elif args.command == "decisions":
                result = [
                    {"decision": json.loads(row["data"]), "updated": row["updated"]}
                    for row in db.execute(
                        "SELECT data,updated FROM decisions ORDER BY id LIMIT ? OFFSET ?",
                        (args.limit if args.limit is not None else -1, args.offset),
                    )
                ]
            elif args.command == "pending":
                result = coverage(db, args.source, True, args.limit, args.offset)
            else:
                result = summary(db)
                if not args.summary:
                    rows = coverage(db)
                    result.update(
                        pending=[row for row in rows if row["latest_status"] != "reviewed"],
                        sessions=rows,
                    )
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0
    except (ValueError, OSError, sqlite3.Error) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

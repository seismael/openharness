"""Golden command specifications shared by the snapshot test and its updater.

Each specification names the same command twice: through the legacy script path
(where one exists) and through the unified CLI. Both must produce the frozen
output. ``prelude`` commands run first in the same isolated copy, so snapshots
that need a lockfile can be taken without committing one to the fixture.
"""

from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures" / "harness"
INIT_FIXTURE = HERE / "fixtures" / "init"
GOLDEN = HERE / "golden"

FIXTURES = {"harness": FIXTURE, "init": INIT_FIXTURE}

SPECS = {
    "audit": {
        "script": ("openharness_audit.py", "--manifest", "harness.json"),
        "cli": ("audit", "--manifest", "harness.json"),
    },
    "audit-fingerprint": {
        "script": (
            "openharness_audit.py",
            "--manifest",
            "harness.json",
            "--fingerprint-only",
        ),
        "cli": ("audit", "--manifest", "harness.json", "--fingerprint-only"),
    },
    "audit-broken": {
        "script": ("openharness_audit.py", "--manifest", "harness-broken.json"),
        "cli": ("audit", "--manifest", "harness-broken.json"),
    },
    "verify": {
        "script": ("openharness_verify.py", "--journal", "journal.jsonl"),
        "cli": ("verify", "--journal", "journal.jsonl"),
    },
    "verify-stale": {
        "script": (
            "openharness_verify.py",
            "--journal",
            "journal-stale.jsonl",
            "--fingerprint",
            "b" * 64,
        ),
        "cli": (
            "verify",
            "--journal",
            "journal-stale.jsonl",
            "--fingerprint",
            "b" * 64,
        ),
    },
    "select": {
        "script": ("openharness_select.py", "--candidates", "candidates"),
        "cli": ("select", "--candidates", "candidates"),
        "copies_fixture": True,
    },
    "cases-dry-run": {
        "script": ("openharness_cases.py", "--cases", "cases.json", "--dry-run"),
        "cli": ("cases", "--cases", "cases.json", "--dry-run"),
    },
    "telemetry": {
        "script": ("openharness_telemetry.py", "--journal", "journal.jsonl"),
        "cli": ("telemetry", "--journal", "journal.jsonl"),
    },
    "inventory": {
        "script": (
            "openharness_inventory.py",
            "--manifest",
            "harness.json",
            "--requirements",
            "requirements.json",
        ),
        "cli": (
            "inventory",
            "--manifest",
            "harness.json",
            "--requirements",
            "requirements.json",
        ),
    },
    "failures": {
        "script": ("openharness_failures.py", "--journal", "journal.jsonl"),
        "cli": ("failures", "--journal", "journal.jsonl"),
    },
    "policy-allow": {
        "script": (
            "openharness_policy.py",
            "--policy",
            "policy.json",
            "--tool",
            "shell",
            "--command",
            "python -B -m unittest",
        ),
        "cli": (
            "policy",
            "--policy",
            "policy.json",
            "--tool",
            "shell",
            "--command",
            "python -B -m unittest",
        ),
    },
    "policy-deny": {
        "script": (
            "openharness_policy.py",
            "--policy",
            "policy.json",
            "--tool",
            "shell",
            "--command",
            "rm -rf build",
        ),
        "cli": (
            "policy",
            "--policy",
            "policy.json",
            "--tool",
            "shell",
            "--command",
            "rm -rf build",
        ),
    },
    "policy-ask": {
        "script": (
            "openharness_policy.py",
            "--policy",
            "policy.json",
            "--tool",
            "shell",
            "--command",
            "Get-Content README.md",
        ),
        "cli": (
            "policy",
            "--policy",
            "policy.json",
            "--tool",
            "shell",
            "--command",
            "Get-Content README.md",
        ),
    },
    "lock": {
        "script": None,
        "cli": ("lock",),
        "copies_fixture": True,
    },
    "plan": {
        "script": None,
        "cli": ("plan", "--check"),
        "copies_fixture": True,
        "prelude": [("lock",)],
    },
    "plan-json": {
        "script": None,
        "cli": ("plan", "--check", "--format", "json"),
        "copies_fixture": True,
        "prelude": [("lock",)],
    },
    "init": {
        "script": None,
        "cli": ("init", "--name", "fixture"),
        "fixture": "init",
        "copies_fixture": True,
    },
    "report-markdown": {
        "script": None,
        "cli": (
            "report",
            "--manifest",
            "harness.json",
            "--requirements",
            "requirements.json",
            "--cases",
            "cases.json",
            "--journal",
            "journal.jsonl",
            "--format",
            "markdown",
            "--output",
            "report.md",
        ),
        "copies_fixture": True,
        "prelude": [("lock",)],
    },
    "report-junit": {
        "script": None,
        "cli": (
            "report",
            "--manifest",
            "harness.json",
            "--requirements",
            "requirements.json",
            "--format",
            "junit",
            "--output",
            "report.xml",
        ),
        "copies_fixture": True,
    },
}

"""Schema identifiers. One place, so a contract name cannot drift per command."""

from __future__ import annotations

MANIFEST = "harness.manifest.v1"
RECEIPT = "openharness.receipt.v1"
VERIFY = "openharness.verify.v1"
SELECTION = "openharness.selection.v1"
CASES = "openharness.cases.v1"
CASES_RECEIPT = "openharness.cases.receipt.v1"
TELEMETRY = "openharness.telemetry.v1"
INVENTORY = "openharness.inventory.v1"
FAILURES = "openharness.failures.v1"
POLICY = "openharness.policy.v1"
LOCK = "openharness.lock.v1"
LOCK_RECEIPT = "openharness.lock.receipt.v1"
PLAN = "openharness.plan.v1"
REPORT = "openharness.report.v1"
REPORT_RECEIPT = "openharness.report.receipt.v1"
INIT = "openharness.init.v1"
REQUIREMENTS = "openharness.requirements.v1"
CONTEXT = "openharness.context.v1"

KINDS = (
    "system_prompt",
    "guardrails",
    "memory",
    "tool_guidance",
    "subagents",
    "skills",
    "scripts",
    "plugins",
)

# Roadmap

The roadmap is ordered by evidence, not by feature count. Each milestone names
the question it answers and the artifact that proves it.

## v0.2 — lock and drift (current)

**Question:** can a team version its harness and review changes to it?

- Packaged `openharness` CLI, stable exit codes, compatibility shims.
- `harness.lock`, `openharness plan`, `openharness init`.
- Composed report in JSON, Markdown, SARIF, and JUnit.
- GitHub Action and PyPI release with provenance.

**Proof:** editing one line of an always-on instruction produces a correct,
attributed drift failure; the action is green on this repository.

## v0.3 — context budget and rendering

**Question:** where does the context budget actually go, and can one declaration
drive several hosts?

- Context budget: resident, loadable, and executable layers with per-kind
  totals, largest components, and named levers — shipped as `openharness
  context` (RFC-0017).
- `openharness render --target claude,codex,cursor,gemini,opencode`.
- Byte-stable rendered configuration and `--check` to catch hand edits.
- JUnit/SARIF enrichment from the context receipt.

**Proof:** a three-host fixture renders byte-stable configuration, and a hand
edit is caught by `--check`.

## v0.4 — transfer evidence and rigor

**Question:** does a harness change transfer across hosts, and do gains compound?

- Host receipts and a transfer matrix that names non-transfer.
- Paired repeats, minimum detectable effect, sequential stopping for binary
  cases, and a Pareto archive over quality, cost, and latency.
- A compounding metric in telemetry.
- RFC-0018 (transfer and validity), RFC-0019 (rendering).

**Proof:** a published cross-host transfer study with reproducible receipts.

## v1.0 — freeze

- Stable schema URLs and a published compatibility policy.
- Adapter conformance suite with observed-runtime evidence.
- Licensing split: code MIT, specification CC-BY-4.0.
- Decision on donating the specification to a neutral foundation.

## Deliberately excluded

No agent runtime, no model gateway, no hosted service, no security scanner, no
benchmark runner, no prompt marketplace, and no second policy engine. Where a
host, MCP, the Agent Control Specification, or an evaluation harness already
owns a concern, OpenHarness emits or ingests and documents the boundary.

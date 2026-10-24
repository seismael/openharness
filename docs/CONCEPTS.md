# Concepts

## The harness is the product

A model in a terminal is not an agent. The agent is the model plus everything that shapes how it works: the always-on instructions, the procedures it can load, the commands it can invoke, the subagents it can delegate to, the tools and MCP servers it can reach, the scripts it can run, and the policies that bound it. That collection is the *harness*.

Model quality is measured exhaustively. Harness quality is usually folklore. OpenHarness makes the harness explicit, measurable, and versioned.

## Five primitives

### 1. Declaration

`harness.json` names the harness: components with an `id`, a `kind`, glob `paths`, and optional `always_on` and `trigger_names`. The eight kinds are `system_prompt`, `guardrails`, `memory`, `tool_guidance`, `subagents`, `skills`, `scripts`, and `plugins`.

`requirements.json` says what must exist. `cases.json` says what must keep working. `policy.json` says what is permitted. Each is a separate document so a change to one is reviewable on its own.

### 2. Measurement

`audit` reads every matched file and reports tokens, files, findings, and a fingerprint. The token number is a deterministic character estimate, not a tokenizer: it is a budget instrument, not a billing instrument. The fingerprint is SHA-256 over sorted `(relative path, content hash)` pairs, so it identifies the harness state and nothing else.

### 3. Identity

The fingerprint is the join key across artifacts. An audit stamps it, a case receipt carries it, a journal entry records it, and `verify` rejects an entry whose recorded fingerprint does not match the audited state. That is how "which harness produced this result?" becomes a lookup instead of an investigation.

### 4. Lock and drift

`harness.lock` records the state a team accepted: per-file hashes, token estimates, budgets, and declaration hashes. `plan` compares the current state to the lock and attributes each difference to a file, a component, or a declaration. Drift is a content question, so it is reproducible and reviewable; no timestamps, no environment, no host.

### 5. Evidence

A change is adopted only with evidence: the cases that were run, the reference to the receipt, the measured before and after, the scope of the claim, and the cost. `verify` enforces the contract; `telemetry` aggregates it; `failures` classifies what went wrong; `select` removes authorship bias from a comparison.

## What "deterministic" buys

- The same declaration and tree produce the same bytes on every platform.
- A receipt is small enough (2500 bytes) to put in a log line, a PR comment, or a journal entry.
- No network, no model, no clock, no environment variable changes a verdict. A CI failure is reproducible locally.
- Golden snapshots can freeze command output, so a refactor is provably behavior-preserving.

Determinism is also a boundary. OpenHarness cannot tell you whether a prompt is *good*; it can tell you whether the harness is coherent, whether it changed, whether your declared cases still pass, and what the effort cost. Judgement stays with the model and the reviewer.

## The evidence ladder

Not every claim has the same support. The project uses four levels, and documentation labels which one applies:

1. **Declared** — a document says so. No execution.
2. **Helper-tested** — a deterministic test exercised the helper on synthetic fixtures.
3. **Runtime-observed** — a specific host version discovered the skill or enforced the policy; the version, platform, and date are recorded.
4. **Outcome-measured** — comparable real work shows a quality or cost effect.

A green CI run proves levels 1 and 2 for this repository. It never proves level 3 for a host that was not run, and it never proves level 4. The compatibility table keeps those columns separate on purpose.

## Boundaries with the rest of the ecosystem

| Concern | Owned by | OpenHarness position |
| :--- | :--- | :--- |
| Instruction format | AGENTS.md and host conventions | Reads and declares it; does not invent a competing format. |
| Procedure packaging | Agent Skills (`SKILL.md`) | Ships skills in that format and measures their cost. |
| Runtime policy enforcement | Hosts, the Agent Control Specification, gateways | Evaluates a portable policy and emits a verdict; does not intercept actions. |
| Task-level evaluation | Harbor, Terminal-Bench, and similar | Runs the cases a project declares; does not own task suites or leaderboards. |
| Prompt optimization | Research optimizers and training loops | Records whether a change helped; does not generate candidates. |
| Observability and tracing | OpenTelemetry and vendor platforms | Emits bounded receipts and fingerprints that those systems can ingest. |

The rule: if another standard already owns the artifact, emit it or consume it. Competing would duplicate work and weaken adoption.

## Why the CLI is one binary

A dozen scripts with duplicated helpers drift. One package means one definition of bounded output, one journal loader, one numeric coercion, one exit-code contract, and one place to fix a schema. The legacy script paths remain as shims so installed skills and existing automation keep working; they will be removed at 2.0.

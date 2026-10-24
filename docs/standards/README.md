# Open Harness Protocol (OHP) Standards Initiative

An open, vendor-neutral, domain-agnostic specification for **Deterministic, Dual-Gated, In-Session Continuous AI Engineering**.

---

## 1. Charter & Mission

The mission of the **Open Harness Protocol (OHP)** Standards Initiative is to transition autonomous AI coding agents from fragile, prompt-driven chat assistants into **rigorous, teleological, self-directed research engineers**.

Current AI software development tools suffer from severe architectural limitations:
1. **Interactive Prompt Babysitting:** Humans must formulate step-by-step tasks, execute unit tests, copy-paste snippets, and manually evaluate outputs.
2. **Naive Autonomous Sprawl:** Unconstrained agents execute unbounded tool calls, pollute context windows, hallucinate non-existent files, silently break system invariants, and incur astronomical API costs ($15–$50/hour).
3. **Loss of Historical Compounding:** Most agents possess zero memory of failed experiments, repeatedly retrying previously falsified hypotheses.
4. **Premature Halting:** When a static list of prompt instructions or parameter knobs is exhausted, conventional agents halt and wait for human guidance instead of autonomously diagnosing root bottlenecks.

**OHP standardizes the interface between cognitive LLM engines and target repositories**, establishing:
- A standardized repository topology (`.agents/` and `.agents/loop/`).
- A declarative project seam (`profile.yaml`) that completely abstracts repository physics from cognitive execution.
- A 12-front engineering taxonomy covering the complete software engineering lifecycle.
- A mathematical dual-gate verification contract that strictly guarantees zero regressions.
- A self-replenishing queue protocol preventing premature agent idling.
- A radical token projection protocol enabling multi-hour, multi-day non-stop execution at negligible cost (<$0.20 per 10 hours).

---

## 2. Specification Series (RFCs)

The standard is organized as a modular series of Request for Comments (RFCs):

| RFC | Title | Scope | Status |
| :--- | :--- | :--- | :--- |
| **[RFC-0001](rfc-0001-openharness-protocol.md)** | **Core Protocol & Repository Topology** | Directory layout, declarative `profile.yaml`, state ledgers, lifecycle state machine | **Proposed Standard** |
| **[RFC-0002](rfc-0002-dual-gate-verification.md)** | **Dual-Gate Verification & Safety Invariants** | Mathematical formulation of gate acceptance, git snapshot transitions, rollback protocol | **Proposed Standard** |
| **[RFC-0003](rfc-0003-teleological-target-seeking.md)** | **Teleological Target-Seeking & Dynamic Replenishment** | Self-replenishing move queues, First-Principles bottleneck diagnosis, simulation freedom | **Proposed Standard** |
| **[RFC-0004](rfc-0004-streaming-output-projection.md)** | **Streaming Output Projection & Radical Token Economics** | Command wrapping, scalar JSON projections, context prefix invariance, prompt caching | **Proposed Standard** |
| **[RFC-0005](rfc-0005-universal-harness-adapters.md)** | **Universal Harness Adapter Interface** | Standard adapter contract for Claude Code, Antigravity, OpenCode, Cursor, and CI/CD | **Proposed Standard** |
| **[RFC-0006](rfc-0006-subagent-orchestration-and-skill-activation.md)** | **Subagent Orchestration & Dynamic Skill Activation** | Orchestrator-worker split, mandatory delegation thresholds, dynamic skill activation ladder | **Proposed Standard** |
| **[RFC-0007](rfc-0007-cognitive-depth-ladder.md)** | **Cognitive Depth Ladder & First-Principles Escalation** | 4-tier abstraction hierarchy, mandatory depth escalation, local minima saturation rules | **Proposed Standard** |
| **[RFC-0008](rfc-0008-dynamic-tool-synthesis.md)** | **Dynamic Tool & Capability Synthesis Protocol** | Just-in-time tool authoring, scratch-to-helper promotion, environment manifest registration | **Proposed Standard** |
| **[RFC-0009](rfc-0009-openharness.md)** | **OpenHarness Harness Optimization Protocol** | Harness component taxonomy, deterministic audit receipts, proposal scopes, probe evidence, composition budget | **Proposed Standard** |
| **[RFC-0010](rfc-0010-contrastive-iteration.md)** | **Contrastive Iteration** | Scope declaration, deficiency-targeted contrast verdicts, anonymous adoption, evidence-gated retention, preservation | **Proposed Standard** |
| **[RFC-0011](rfc-0011-iteration-telemetry.md)** | **Iteration Telemetry** | Recorded-only cost aggregation, separated gain and regression totals, cost per gain, missing-data honesty | **Proposed Standard** |
| **[RFC-0012](rfc-0012-declared-evaluation-cases.md)** | **Declared Evaluation Cases** | Deterministic case declarations, failure/timeout/error distinction, probe receipts, matched conditions | **Proposed Standard** |
| **[RFC-0013](rfc-0013-capability-inventory.md)** | **Capability Inventory and Gap Analysis** | Per-kind inventory from the audited manifest, declared requirements, blocking and optional gaps | **Proposed Standard** |
| **[RFC-0014](rfc-0014-failure-taxonomy.md)** | **Failure Taxonomy** | Closed nine-class cause vocabulary, recurrence as harness gap, separated failure rate | **Proposed Standard** |
| **[RFC-0015](rfc-0015-portable-policy-and-enforcement.md)** | **Portable Action Policy and Adapter Enforcement** | Last-match-wins policy evaluation, allow/ask/deny verdicts, adapter enforcement matrix | **Proposed Standard** |
| **[RFC-0016](rfc-0016-harness-lockfile-and-drift-plan.md)** | **Harness Lockfile and Drift Plan** | Content-addressed lock, per-file attribution, declaration hashes, check-mode gating | **Proposed Standard** |
| **[RFC-0017](rfc-0017-context-budget.md)** | **Context Budget** | Resident, loadable, and executable token layers, named levers, declared-budget verdicts | **Proposed Standard** |

---

## 3. Schemas & Normative Artifacts

Formal machine-readable JSON schemas validating OHP compliant repositories:

- [`schemas/profile.schema.json`](schemas/profile.schema.json): Schema for repository declarative seam (`profile.yaml`).
- [`schemas/loop.schema.json`](schemas/loop.schema.json): Schema for the active loop runtime state (`loop.json`).
- [`schemas/journal.schema.json`](schemas/journal.schema.json): Schema for the append-only chronological audit ledger (`journal.jsonl`).
- [`schemas/coverage.schema.json`](schemas/coverage.schema.json): Schema for the 12-front breadth coverage ledger (`coverage.json`).
- [`schemas/openharness.schema.json`](schemas/openharness.schema.json): Schema for the audited harness manifest (`harness.json`) and its bounded audit receipt.
- [`schemas/cases.schema.json`](schemas/cases.schema.json): Schema for a declared evaluation case set consumed by a deterministic runner.
- [`schemas/policy.schema.json`](schemas/policy.schema.json): Schema for a portable, last-match-wins action policy.
- [`schemas/lock.schema.json`](schemas/lock.schema.json): Schema for the content-addressed harness lockfile and its drift inputs.
- [`schemas/context.schema.json`](schemas/context.schema.json): Schema for the context-budget receipt with layer totals and named levers.

---

## 4. Reference Implementation

The normative reference implementation of the Open Harness Protocol is maintained in this repository:
- Core engine: [`skills/loop/SKILL.md`](../../skills/loop/SKILL.md)
- Dispatch policy: [`skills/loop/references/dispatch-policy.md`](../../skills/loop/references/dispatch-policy.md)
- Front taxonomy: [`skills/loop/references/front-taxonomy.md`](../../skills/loop/references/front-taxonomy.md)
- Seed templates: [`skills/loop/assets/templates/`](../../skills/loop/assets/templates/)
- Test harness: [`tests/`](../../tests/)

---

## 5. Participation & Adoption

We welcome contributors, AI tool vendors, and enterprise engineering teams to collaborate on evolving the standard. See [CONTRIBUTING.md](../../CONTRIBUTING.md) for details on submitting RFC errata and extensions.

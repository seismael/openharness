# OpenHarness & The Open Harness Protocol (OHP)

Portable skills and the open architecture for making AI agents **autonomous, continuous, invariant-safe, and economically viable** in enterprise software development and computational research.

---

## The Standardization Objective: Open Harness Protocol (OHP)

Current AI engineering is polarized between two inadequate paradigms:
1. **The Copilot / Chatbot Paradigm:** Requires continuous human micromanagement, prompt babysitting, manual testing, and copy-pasting of isolated code snippets.
2. **The Naive Autonomous Agent Paradigm:** Executes open-ended tasks with unconstrained tool sprawl, hallucination cascades, context window bloat ($15–$50/hour), and silent regression of system invariants.

**OpenHarness establishes the Open Harness Protocol (OHP):** A vendor-neutral, domain-agnostic open standard for **Deterministic, Dual-Gated, In-Session Continuous AI Engineering**. 

Our objective is to standardize how autonomous agents interact with any repository—transforming AI from an interactive prompt chatbot into a self-directed, teleological research engineer that explores codebases, diagnoses bottlenecks, formulates minimal falsifiable candidates, verifies changes against mathematical dual gates, and compounds knowledge without human intervention.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              THE THREE AGENTIC PARADIGMS                               │
├──────────────────────────┬─────────────────────────────┬───────────────────────────────┤
│ 1. Copilots / Chatbots   │ 2. Naive Autonomous Agents  │ 3. Open Harness Protocol    │
├──────────────────────────┼─────────────────────────────┼───────────────────────────────┤
│ • Human writes prompt    │ • Open-ended task prompt    │ • Single target directive     │
│ • LLM generates snippet  │ • Arbitrary tool execution  │ • Declarative seam: profile   │
│ • Human tests & reviews  │ • Unchecked file rewrites   │ • 12-Front systematic audit   │
│ • High human friction    │ • Hallucination cascades    │ • In-session bounded steps    │
│ • Zero compounding memory│ • Token burns ($20–$50/hr)  │ • Strict dual-gate safety     │
│ • Trapped in chat box    │ • Collateral breakage       │ • Compounding immutable memory│
│                          │                             │ • Ultra-low cost ($0.19/10.5h)│
└──────────────────────────┴─────────────────────────────┴───────────────────────────────┘
```

### The Standards Initiative & Formal RFC Series

To transition this architecture from an internal capability into a universal, vendor-neutral industry standard, we have established the **OHP Standards Track**. Any agent runtime (Antigravity, OpenCode, Claude Code, Cursor, Copilot, Cline, Aider) and any software repository (Python, Rust, Go, TypeScript, C++) can implement or conform to the specification:

- **[OHP Working Group Charter & Overview](docs/standards/README.md)**: Mission, governance, roadmap, and RFC lifecycle.
- **The Complete Normative RFC Series:**
  - **[RFC-0001: Core Protocol & Repository Topology](docs/standards/rfc-0001-openharness-protocol.md)**: Standard `.agents/loop/` layout, declarative `profile.yaml`, state ledgers, and 12-front lifecycle.
  - **[RFC-0002: Dual-Gate Verification Protocol](docs/standards/rfc-0002-dual-gate-verification.md)**: Mathematical formulation of gate acceptance, git snapshot transitions, and atomic rollbacks.
  - **[RFC-0003: Teleological Target-Seeking Protocol](docs/standards/rfc-0003-teleological-target-seeking.md)**: Expected-Value move dispatch, self-replenishing queues, and the Simulation Freedom Invariant.
  - **[RFC-0004: Streaming Output Projection](docs/standards/rfc-0004-streaming-output-projection.md)**: Output projection filters, scalar JSON extraction, and radical token economics ($0.19/10.5h).
  - **[RFC-0005: Universal Harness Adapters](docs/standards/rfc-0005-universal-harness-adapters.md)**: Cross-platform adapter contract for Claude Code, Antigravity, OpenCode, Cursor, and CI/CD.
- **Normative JSON Schemas:**
  - [`profile.schema.json`](docs/standards/schemas/profile.schema.json): Declarative seam validation contract.
  - [`loop.schema.json`](docs/standards/schemas/loop.schema.json): Runtime state tracking contract.
  - [`journal.schema.json`](docs/standards/schemas/journal.schema.json): Append-only chronological audit ledger contract.
  - [`coverage.schema.json`](docs/standards/schemas/coverage.schema.json): 12-front breadth coverage verification contract.
- **Internal Tools & Multi-Language Starters:**
  - Internal Skill Tools: Zero-dependency scripts in `skills/loop/scripts/` (`init_loop.py`, `validate_loop.py`) used by the agent and CI for initialization and schema validation.
  - Starter Profiles: [Python](skills/loop/assets/templates/profile.python.yaml), [Rust](skills/loop/assets/templates/profile.rust.yaml), [Go](skills/loop/assets/templates/profile.go.yaml), and [Node.js](skills/loop/assets/templates/profile.node.yaml).

---

## Comparative Analysis: `obra/superpowers` vs. OpenHarness (OHP)

While popular skill frameworks like **`obra/superpowers`** have brought valuable discipline to human-in-the-loop "vibe coding", they operate under fundamentally different assumptions than **OpenHarness (OHP)**:

| Vector | `obra/superpowers` | OpenHarness (OHP) |
| :--- | :--- | :--- |
| **Operating Paradigm** | **Interactive Pairing**: 2–5 min micro-tasks while human sits at chat prompt | **Autonomous Macro-Loop**: 10+ hours non-stop unattended execution |
| **Target-Seeking** | **Static Checklist**: Halts when initial tasks finish; asks human what to do next | **Teleological Closed Loop**: Prohibited from halting; auto-replenishes via diagnostics |
| **Verification & Safety** | **Standard TDD**: Unit tests pass/fail in git worktree branches | **Mathematical Dual Gates**: Metric gain $+$ zero invariant regressions $+$ atomic git rollback |
| **Memory & Compounding** | **Ephemeral**: Context window & git commits (lost upon context compaction) | **Durable Schemas**: Disk-backed state ledgers (`loop.json`, `journal.jsonl`, `decisions/`) |
| **Token Economics** | **Raw Command Streaming**: Burns $5–$20/hr via verbose build/test outputs | **Projection Wrapping**: Scalar receipts + static prefix caching (**$0.19 / 10.5h**) |
| **Domain Scope** | Code-centric software feature development | Universal: software features, systems latency, algorithmic trading, ML, compilers |

> See the full technical whitepaper: **[docs/architecture/superpowers-vs-ohp.md](docs/architecture/superpowers-vs-ohp.md)**.

---

## Universal Harness Compatibility & Adapters

OpenHarness is designed to integrate natively with **zero repository lock-in** across all leading AI coding harnesses:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              SUPPORTED AGENT RUNTIMES                                  │
├────────────────────┬──────────────────────────────────────┬────────────────────────────┤
│ Harness            │ Native Integration Surface           │ Activation Method          │
├────────────────────┼──────────────────────────────────────┼────────────────────────────┤
│ **Claude Code**    │ Official Plugin & Marketplace        │ `/plugin install`, `/loop` │
│ **Antigravity**    │ Global/Local Skills & Subagents      │ `/loop "<target>"`         │
│ **OpenCode**       │ In-Session Skill Protocol & DB       │ Headless session prompt    │
│ **Cursor/Windsurf**│ Model Context Protocol (MCP) Server  │ `tools/mcp_server.py`      │
│ **Headless CI/CD** │ Scheduled Overnight Runner           │ GitHub Actions / Cron      │
└────────────────────┴──────────────────────────────────────┴────────────────────────────┘
```

- **Claude Code 1-Click Installation:**
  ```bash
  /plugin marketplace add seismael/openharness
  /plugin install openharness@openharness-marketplace
  ```
- **Cursor / Windsurf MCP Server:**
  Add `tools/mcp_server.py` to your MCP configuration to expose `loop_status`, `loop_step`, and `loop_verify` directly in IDE chats.
- **Harness Integration Guide:** Detailed step-by-step connection recipes available in **[docs/guides/harness-integration.md](docs/guides/harness-integration.md)**.

---

## Harness Optimization (RFC-0009)

The harness is the part of the agent a loop iteration can actually change: instructions,
guardrails, memory, tool guidance, subagents, skills, scripts, and plugins. OpenHarness
measures it instead of describing it.

```bash
# 1. Declare the surface once, in harness.json (schema: harness.manifest.v1)
# 2. Audit it: deterministic, no model calls, no writes, byte-identical on an unchanged tree
python skills/loop/scripts/openharness_audit.py --manifest harness.json
```

The audit reports per-component token estimates, always-on and total budget violations,
unreachable skills or subagents, duplicated instruction lines, and broken local links. It
emits a receipt capped at 2,500 bytes and exits non-zero on any error-severity finding.

Adoption is scoped. Every harness change is declared `invariant` (must be probed on at
least two cells) or `local` (may not become a global default), and no change is adopted
without a probe receipt for that exact harness state. A clean audit is necessary, never
sufficient: it cannot prove that an instruction is obeyed or that a behavior transfers to
another model. See **[RFC-0009](docs/standards/rfc-0009-openharness.md)** and the
[operating reference](skills/loop/references/openharness.md).

---

## The Autonomous Loop Architecture

The architecture decouples the **Domain-Agnostic Cognitive Engine** from the **Project-Specific Physics** through standardized repository seams:

```
<project-root>/
└── .agents/                                 # Standardized Unified Agent Topology
    ├── loop/                                # The Autonomous Loop Engine & Memory Brain
    │   ├── loop.json                        # Active iteration, champion state, status
    │   ├── journal.jsonl                    # Immutable, append-only chronological audit ledger
    │   ├── coverage.json                    # 12-Front breadth coverage guarantee ledger
    │   ├── issues.jsonl                     # Prioritized defect and regression backlog
    │   ├── env.json                         # Deterministic toolchain manifest (binaries, test cmds)
    │   ├── plans/
    │   │   └── next_moves.json              # Dynamic, expected-value ranked move queue
    │   ├── knowledge/                       # Living project wiki & invariant store
    │   │   ├── profile.yaml                 # The declarative project seam
    │   │   ├── invariants.md                # Non-negotiable safety limits & system axioms
    │   │   ├── capabilities.md              # Discovered system surfaces and tools
    │   │   ├── baselines.md                 # Certified benchmark ground truth
    │   │   └── decisions/                   # Immutable ledger of all prior adoptions/rejections
    │   ├── scratch/                         # Sandboxed throwaway diagnostic probes (<= 2.5KB)
    │   └── scripts/                         # Promoted reusable forensic tools
    ├── skills/                              # Native & dynamically synthesized project skills
    └── subagents/                           # Specialized read-only personas invoked on demand
```
*(Note: For backward compatibility, if `.agents/loop/` is absent, the engine gracefully binds to `.loop/`.)*

### 1. The Declarative Seam: `profile.yaml`
**Zero project-specific detail belongs in the cognitive engine.** The engine operates identically whether optimizing quantitative trading algorithms, cloud microservice latency, compiler passes, or ML models. All project physics live in `profile.yaml`:

```yaml
schema: loop.profile.v1
project: "my-service"
target: "Reduce P99 API response latency under 10ms without increasing memory footprint"
metric: "benchmarks/results.json:summary.p99_latency_ms"
predicate: "p99_latency_ms < 10.0 AND memory_rss_mb <= 512"

paths:
  loop: ".agents/loop"
  agents: ".agents"

boundaries:
  - "Zero regressions in existing unit and integration test suites"
  - "No weakened assertions or skipped validation gates"
  - "Memory footprint must remain strictly <= 512MB under 10k RPS load"

pipeline:
  - id: evaluate
    kind: evaluate
    command: "cargo bench --bench latency"
    artifact: "target/criterion/report.json"
  - id: test
    kind: test
    command: "cargo test --all"

gates:
  objective: "Candidate P99 latency strictly decreases vs incumbent champion"
  invariants: "All test and validation suites pass 100% green"

completion:
  rule: "predicate_met OR coverage_complete"
  require_coverage: true
  require_delivery: true                      # Clean git working tree, commits ahead of origin
```

### 2. The 12-Front Engineering Taxonomy
Rather than relying on unguided "trial-and-error" or random parameter sweeps, the loop explores codebases across **12 distinct engineering fronts**:

| Front | Core Purpose | Terminal Evidence |
| :--- | :--- | :--- |
| **`orient`** | Establish ground truth & verify clean state | Reproduced baseline metric + clean git tree |
| **`discover`** | Inventory unused codebase surfaces & features | Documented capabilities in `capabilities.md` |
| **`audit`** | Detect divergence from contracts, specs, and invariants | Evidence findings with line citations |
| **`diagnose`** | Pinpoint dominant bottlenecks and loss vectors | Bounded diagnostic artifact (gap/funnel) |
| **`research`** | Formulate data-backed, falsifiable hypotheses | Bounded synthesis backed by empirical data |
| **`debug`** | Resolve defects, inconsistencies, and safety holes | Fixed defect + regression test |
| **`improve`** | Formulate minimal candidate mechanism diffs | Dual-gated adoption commit |
| **`harden`** | Enforce risk envelopes, limits, and security bounds | Enforced invariant gate + regression test |
| **`performance`** | Optimize execution speed, throughput, and memory | Measured profile meeting target |
| **`pipeline`** | Verify reproducibility and CI artifact provenance | Reproducibility check passing |
| **`knowledge`** | Compound all positive & negative findings | Immutable entries in `decisions/` & journal |
| **`plan`** | Dynamically rank next moves by Expected Value | Decomposed target in `plans/next_moves.json` |

### 3. The Dual-Gate Safety Contract
In enterprise software engineering, an improvement on one metric that introduces regressions elsewhere is a defect, not progress. The protocol enforces a mathematical contract:
$$\text{Gate Acceptance} = (\Delta \text{Primary Objective} > 0) \land (\forall I \in \text{Invariants}, \, \text{Status}(I) = \text{PASS})$$
- Every candidate diff is staged via a pre-evaluation git snapshot (`feat(candidate): ...`).
- If the primary metric improves and all invariants pass: **ADOPTED** (`feat(adopt): ...`).
- If either gate fails: **REVERTED IMMEDIATELY** (`git reset --hard HEAD~1`).
- The negative outcome is permanently recorded in `decisions/` and `journal.jsonl` to ensure the engine **never repeats a falsified avenue**.

### 4. Teleological Target-Seeking & The Self-Replenishing Queue
A true autonomous agent does not stop when a static checklist runs out:
- **Never Halt on Closed Lists:** When every pre-listed knob or axis has reached a terminal outcome, the engine is **forbidden from halting or asking for permission**.
- **First-Principles Diagnostics:** The engine ascends the abstraction ladder to run leakage forensics (e.g., MFE give-back, suppressed candidate signals, cross-sectional component drag).
- **Hypothesis Generation:** Formulates 2–3 novel structural mechanisms from empirical data, refills `plans/next_moves.json`, and immediately dispatches the top-ranked move.
- **Simulation Freedom:** Notes mentioning "operator-gated" apply strictly to live production deployment. In headless evaluation (`eval`), the engine is **100% authorized** to prototype, simulate, and falsify anything without human intervention.

### 5. Radical Token Economics
Traditional agents burn massive token budgets by streaming raw multi-megabyte terminal outputs into context. OHP achieves industrial efficiency through three architectural pillars:
- **Projection Filtering:** Commands are wrapped to suppress noisy output (`Out-Null`) and return only single-line scalar JSON receipts (`net_pnl`, `trades`, `fees`, `latency_ms`). New inputs are bounded to ~150–250 tokens per turn.
- **Prefix Invariance & Prompt Caching:** System prompts, skill instructions, and project memory leaves (`profile.yaml`, `invariants.md`, `env.json`) remain byte-static at the context head, maximizing provider KV-cache hits.
- **Automated Window Compaction:** Context growth is managed smoothly, preventing token degradation while preserving the active disk-backed state.

---

## Empirical Proof: 10.5 Hours in Apex Quant Trading

The architecture was subjected to rigorous overnight validation on **Apex**, an institutional quantitative cryptocurrency trading platform processing tick-level market data:

- **Duration:** **10 hours, 25 minutes** continuous non-stop execution (132 engine turns).
- **Domain Deliverables:**
  - Formulated, coded, and unit-tested a continuous `drawdown_scale` model in core risk allocation modules.
  - Authored 5 comprehensive unit tests in `tests/test_capital_allocator.py`.
  - Passed `ruff check`, `ruff format`, schema validation, and >1,360 unit regression tests.
  - Executed 12 full-month multi-asset simulation backtests (>3.7 million market events).
  - Subjected its own code to falsification; detected net degradation on crash regimes; **honestly rejected its own diff**, and committed decision **D-190**.
  - Verified historical baseline control pools across 2023 to **28 decimal places of exact float parity**.
  - Authored 2 clean semantic git commits (`a23fdcd`, `7ebc9af`).
- **Token Metrics:**
  - Total Cached Tokens Read: **14,832,896 tokens** (~14.8M).
  - DeepSeek Prompt Cache Hit Rate: **96.93%**.
  - **Total Cost for Entire 10.5h Session:** **$0.1938** (less than **20 CENTS**).
  - Average Cost per Turn: **~$0.00147** ($\sim \frac{1}{7}\text{th}$ of 1 cent).

---

## Industry Standardization & Commercialization Roadmap

We are standardizing this architecture across three production tiers:

```
                                  COMMERCIAL ROADMAP
                                          │
    ┌─────────────────────────────────────┼─────────────────────────────────────┐
    ▼                                     ▼                                     ▼
[Tier 1: Native In-Harness Integration] [Tier 2: Nightly CI/CD Optimizer]  [Tier 3: Enterprise Governance Hub]
• Open Harness Protocol (OHP)        • Automated overnight research     • Immutable audit ledger
• Native Plugins & MCP Server           • Headless in-session runner       • SOC2 & regulatory compliance
• Zero external CLI friction            • Automated PR with receipts       • Risk & safety guarantees
```

### Tier 1: The Open Protocol & Native In-Harness Integration
- Vendor-neutral specification defining `.agents/`, `profile.yaml`, and `journal.jsonl`.
- 100% native integration into Claude Code (`.claude-plugin/`), Cursor/Windsurf (`tools/mcp_server.py`), Antigravity (`/loop`), and OpenCode.
- Zero external CLI binaries, daemons, or background wrappers needed: the agent is the engine.

### Tier 2: The Nightly CI/CD Autonomous Optimizer ("Overnight Research as a Service")
- Deployed as a scheduled GitHub Action or Kubernetes Job running from 11:00 PM to 5:00 AM.
- Explores 15–20 hypotheses per night against the repository's `profile.yaml`.
- Submits an automated morning Pull Request with complete mathematical receipts:
  > *"PR #142: Reduced P99 microservice latency by 14.2% across 3 load benchmarks. Zero invariant regressions across 840 tests. Cost: $0.18."*

### Tier 3: Enterprise Governance & Regulatory Compliance
- Financial institutions, medical device software, and defense contractors cannot deploy "black-box" AI modifications.
- The append-only cryptographic `journal.jsonl` provides an unalterable paper trail verifying exact baselines, rejected diffs, and proof of zero safety invariant violations.

---

## Bundled Skills Suite

| Skill | Purpose |
|---|---|
| [Loop](skills/loop/SKILL.md) | Execute autonomous continuous optimization loops endlessly across diagnosis, candidate testing, and git compounding via `/loop "<target>"`. |
| [Audit](skills/audit/SKILL.md) | Audit local or remote repositories against user goals and domain risks, resolve findings, and produce verified implementation plans. |
| [Knowledge](skills/knowledge/SKILL.md) | Maintain an indexed, token-efficient, Obsidian-compatible local Markdown wiki to prevent context drift and eliminate redundant exploration scans. |
| [Characterize](skills/characterize/SKILL.md) | Translate goals, domains, workflows, and constraints into a minimal native setup; interview only where evidence leaves consequential choices unresolved. |
| [Enhance](skills/enhance/SKILL.md) | Learn from actual sessions, diagnose wasted effort, and improve native settings and workflows at the correct global, project, agent, or task scope. |

See [Autonomous Optimization Guide](docs/guides/autonomous-loop.md) for cross-platform agent execution patterns.

---

## Installation

Clone this repository or download its source. Copy the **whole** selected directory under `skills/` into one supported skill location:

```sh
git clone https://github.com/seismael/openharness.git
cd openharness
python tools/install_skill.py --skill loop --to ~/.agents/skills/loop --check
python tools/install_skill.py --skill loop --to ~/.agents/skills/loop
```

The shared installer accepts any bundled skill (`loop`, `audit`, `knowledge`, `characterize`, `enhance`). See [Installation Guide](docs/INSTALLATION.md) for OpenCode, Claude Code, Gemini CLI, Antigravity CLI (`agy`), and Antigravity IDE.

---

## Development & Regression Testing

```sh
python tools/check_release.py
python -B -m unittest discover -s skills/loop/scripts -p 'test_*.py' -v
python -B -m unittest discover -s skills/characterize/scripts -p 'test_*.py' -v
python -B -m unittest discover -s skills/enhance/scripts -p 'test_*.py' -v
python -B -m unittest discover -s skills/audit-project/scripts -p 'test_*.py' -v
python -B -m unittest discover -s tests -p 'test_*.py' -v
```

See [Validation](docs/VALIDATION.md) for reproducible behavior scenarios and [Contributing](CONTRIBUTING.md) for change requirements.

---

## License

[MIT](LICENSE), Copyright (c) 2026 seismael.

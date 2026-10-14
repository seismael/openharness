# RFC-0001: OpenAgent Loop Protocol (OALP) Core Specification

- **RFC Number:** 0001
- **Title:** OpenAgent Loop Protocol (OALP) Core Specification
- **Status:** Proposed Standard (Working Draft)
- **Category:** Standards Track
- **Version:** 1.0.0-draft
- **Date:** October 2026
- **Authors:** Seismael & Antigravity Advanced Agentic Engineering Team

---

## Abstract

This document specifies the core protocol, repository topology, state ledgers, and cognitive execution lifecycle of the **OpenAgent Loop Protocol (OALP)**. OALP defines a vendor-neutral, domain-agnostic standard for autonomous, continuous, dual-gated AI software engineering. By decoupling repository-specific physics from cognitive LLM orchestration through a declarative seam (`profile.yaml`), enforcing dual-gate mathematical verification, and formalizing a self-replenishing dispatch queue, OALP enables artificial intelligence agents to conduct hours or days of uninterrupted empirical research and development at radical token efficiency.

---

## 1. Terminology & Conformance

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 [RFC 2119] [RFC 8174] when, and only when, they appear in all capitals, as shown here.

An **OALP-Compliant Engine** is any autonomous LLM agent runtime, CLI, or orchestration framework that implements the execution semantics, dual-gate invariants, and state management defined herein.

An **OALP-Compliant Repository** is any software repository that implements the directory topology, declarative seam (`profile.yaml`), and state ledgers specified in Section 3.

---

## 2. Motivation & Architectural Principles

Contemporary AI developer tooling is dominated by two suboptimal patterns:
1. **Interactive Prompt Turn-Taking:** The human operator acts as a manual test-runner and context-paster, causing cognitive fatigue and throttling agentic throughput.
2. **Unguided Autonomous Drift:** Autonomous agents lacking formal state machines execute noisy shell commands, pollute context windows, hallucinate non-existent surfaces, break undocumented invariants, and generate massive financial waste through token thrashing.

OALP addresses these limitations through four foundational axioms:
- **Axiom 1: Declarative Decoupling.** The cognitive engine SHALL contain zero domain-specific code. All targets, commands, paths, metrics, and invariant bounds MUST reside in the repository seam.
- **Axiom 2: Dual-Gate Invariant Safety.** Progress is strictly defined as an increase in the primary objective metric subject to zero regressions across all certified invariant gates. Any regression SHALL trigger an immediate, atomic git rollback.
- **Axiom 3: Compounding Immutable Memory.** All trials, whether adopted, rejected, or inconclusive, MUST be recorded in append-only cryptographic or structured ledgers. The engine SHALL never repeat a falsified avenue.
- **Axiom 4: Teleological Persistence.** An autonomous agent MUST NOT halt when a pre-populated list of parameter options is exhausted. It SHALL escalate to First-Principles diagnostic exploration to replenish its hypothesis backlog until the target is formally met.
- **Axiom 5: Radical Token Efficiency.** The agent SHALL communicate with repository processes via projected scalar receipts, keeping per-turn context expansion strictly bounded.

---

## 3. Standardized Repository Topology

An OALP-compliant repository SHALL structure its agentic memory and tool assets under the `.agents/` root directory.

```
<project-root>/
└── .agents/
    ├── loop/                                # OALP Engine Durable State & Memory
    │   ├── loop.json                        # Active iteration, champion state, status
    │   ├── journal.jsonl                    # Immutable, append-only chronological audit ledger
    │   ├── coverage.json                    # 12-Front breadth coverage guarantee ledger
    │   ├── issues.jsonl                     # Prioritized defect and regression backlog
    │   ├── env.json                         # Deterministic toolchain manifest
    │   ├── plans/
    │   │   └── next_moves.json              # Dynamic, expected-value ranked move queue
    │   ├── knowledge/                       # Repository living wiki & invariant store
    │   │   ├── profile.yaml                 # The declarative project seam (REQUIRED)
    │   │   ├── invariants.md                # System invariants & boundary conditions
    │   │   ├── capabilities.md              # Discovered execution surfaces & APIs
    │   │   ├── baselines.md                 # Certified incumbent ground truth
    │   │   └── decisions/                   # Immutable ledger of all prior adoptions/rejections
    │   ├── scratch/                         # Ephemeral diagnostic probes (<= 2500 bytes)
    │   └── scripts/                         # Promoted reusable diagnostic tools
    ├── skills/                              # Native & dynamically synthesized project skills
    └── subagents/                           # Specialized read-only personas
```

### 3.1 Backward Compatibility
For legacy installations, if `.agents/loop/` does not exist but `.loop/` is present at the repository root, an OALP engine MUST gracefully bind to `.loop/` without error.

---

## 4. The Declarative Seam: `profile.yaml`

The file `.agents/loop/knowledge/profile.yaml` (or `.loop/knowledge/profile.yaml`) defines the contract between the repository and the OALP engine.

### 4.1 Specification Schema

```yaml
schema: loop.profile.v1                       # MUST be 'loop.profile.v1'
project: string                              # Unique identifier of the target project
target: string                               # Plain-text teleological objective statement
metric: string                               # Path to evaluation receipt and scalar JSON key
predicate: string                            # Boolean termination expression over metric keys

paths:
  loop: string                               # Relative path to loop state directory
  agents: string                             # Relative path to agents directory

boundaries:                                  # System invariants that must never be violated
  - string

pipeline:                                    # Ordered sequence of commands to execute
  - id: string                               # Unique step identifier (e.g., 'evaluate', 'test')
    kind: string                             # Step type: 'evaluate' | 'test' | 'lint' | 'build'
    command: string                          # Shell command string
    artifact: string                         # (Optional) Expected output file receipt

gates:
  objective: string                          # Rule for evaluating primary objective gain
  invariants: string                         # Rule for verifying invariant gate passage

completion:
  rule: string                               # e.g., 'predicate_met OR coverage_complete'
  require_coverage: boolean                  # If true, all 12 fronts must reach terminal status
  require_delivery: boolean                  # If true, git working tree must be clean
```

### 4.2 Metric Address Syntax
The `metric` string MUST follow the format `<file-path>:<json-pointer-or-key-path>`.
Example: `benchmarks/results.json:summary.p99_latency_ms` specifies reading `summary.p99_latency_ms` from `benchmarks/results.json`.

---

## 5. Durable State Ledgers

All OALP state files MUST adhere to valid JSON or JSONL formats and be machine-parseable.

### 5.1 Active Loop State (`loop.json`)
The `loop.json` document records the current execution pointer and champion ground truth:

```json
{
  "schema": "loop.v1",
  "status": "in_progress",
  "iteration": 73,
  "champion": {
    "commit": "7ebc9af",
    "metric_value": 0.0842,
    "timestamp": "2026-10-14T01:39:12Z"
  },
  "active_front": "improve",
  "target_predicate": "p99_latency_ms < 10.0"
}
```

The `status` field MUST be one of: `"in_progress"`, `"completed"`, or `"blocked"`.

### 5.2 Append-Only Journal (`journal.jsonl`)
Every step or turn executed by the engine MUST append exactly one JSON object to `journal.jsonl`:

```json
{
  "ts": "2026-10-14T01:39:12Z",
  "iteration": 72,
  "front": "improve",
  "hypothesis": "Replace coarse-grained table lock with lock-free concurrent hash ring for partition routing",
  "candidate_commit": "a23fdcd",
  "metric_before": 1420.50,
  "metric_after": 1985.20,
  "decision": "adopted",
  "decision_ref": "D-190",
  "invariant_checks": {
    "unit_tests": "PASS",
    "memory_safety": "PASS"
  },
  "rationale": "Eliminated reader lock contention on high-concurrency partition lookups, increasing throughput by +39.7% with zero regression on race detectors."
}
```

### 5.3 Coverage Ledger (`coverage.json`)
The `coverage.json` ledger tracks progress across all 12 engineering fronts:

```json
{
  "schema": "coverage.v1",
  "fronts": {
    "orient": { "status": "exhausted", "evidence": "Baseline reproduced at commit 0b4e21a" },
    "discover": { "status": "exhausted", "evidence": "Mapped all risk allocation modules in capabilities.md" },
    "audit": { "status": "covered", "evidence": "Audit complete; 3 issues logged in issues.jsonl" },
    "diagnose": { "status": "active", "evidence": "Analyzing 2024 missed momentum entry candles" }
  }
}
```

The `status` for each front MUST be one of: `"unstarted"`, `"active"`, `"covered"`, or `"exhausted"`.

---

## 6. The 12-Front Engineering Taxonomy

OALP defines twelve canonical fronts of software and system research:

1. **`orient`**: Establish ground truth, inspect git status, verify clean working tree, and reproduce the current champion baseline metric.
2. **`discover`**: Systematically inspect repository capabilities, uncalled functions, hidden flags, and unused modules; catalog findings in `capabilities.md`.
3. **`audit`**: Check divergence between code implementation, documentation, and declared contracts; record actionable defects in `issues.jsonl`.
4. **`diagnose`**: Pinpoint empirical loss vectors, suppressed signals, latency hotspots, or resource leaks using bounded diagnostic probes.
5. **`research`**: Conduct data-backed causal analysis and formulate testable, falsifiable engineering hypotheses.
6. **`debug`**: Fix known defects, resolve regressions, or repair broken assertions, backed by a regression test.
7. **`improve`**: Formulate minimal architectural or algorithmic candidate mechanism diffs to advance the primary objective.
8. **`harden`**: Enforce defensive bounds, edge-case assertions, risk envelopes, and security guards.
9. **`performance`**: Optimize wall-clock execution time, throughput, memory footprint, or algorithmic complexity.
10. **`pipeline`**: Validate toolchain health, test speed, CI determinism, and artifact provenance.
11. **`knowledge`**: Synthesize learnings, update living architectural wiki documents, and record immutable entries in `decisions/`.
12. **`plan`**: Decompose the high-level objective, rank candidate avenues by Expected Value ($\text{EV} = P(\text{success}) \times \text{Impact} / \text{Cost}$), and maintain `plans/next_moves.json`.

---

## 7. Dual-Gate Verification Protocol

An OALP engine MUST NOT adopt any candidate change that fails either the objective gate or the invariant gate.

### 7.1 Mathematical Contract
Let $M(S)$ denote the objective metric value for repository state $S$. Let $I_1(S), I_2(S), \dots, I_k(S)$ denote the verification status ($\text{PASS} = 1, \text{FAIL} = 0$) of all defined invariant suites.

Acceptance of a candidate state $S_{\text{candidate}}$ over incumbent champion $S_{\text{champion}}$ is defined as:

$$\text{Accept}(S_{\text{candidate}}) \iff \left( M(S_{\text{candidate}}) \succ M(S_{\text{champion}}) \right) \land \left( \bigwedge_{j=1}^{k} I_j(S_{\text{candidate}}) = 1 \right)$$

where $\succ$ denotes strict monotonic improvement according to the directionality specified in `profile.yaml`.

### 7.2 Pre-Evaluation Git Snapshot Transition
To guarantee reproducibility and prevent uncommitted mutation contamination:
1. The engine MUST commit all proposed modifications to git prior to initiating evaluation:
   `git commit -m "feat(candidate): <concise hypothesis description>"`
2. The engine executes the evaluation pipeline specified in `profile.yaml`.
3. If `Accept(S_candidate)` is TRUE:
   - The engine updates `loop.json` with the new champion commit.
   - The engine commits adoption records or amends commit message: `feat(adopt): ...`.
4. If `Accept(S_candidate)` is FALSE:
   - The engine MUST immediately roll back the working tree:
     `git reset --hard HEAD~1`
   - The engine MUST record the rejection in `decisions/` and append the empirical failure receipt to `journal.jsonl`.

---

## 8. Teleological Target-Seeking & Self-Replenishing Queue Protocol

A central design defect of early AI agents is halting when a pre-configured move queue or parameter checklist is exhausted. OALP mandates active replenishment:

```
┌────────────────────────────────────────────────────────┐
│                   DISPATCH CYCLE                       │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
             Is next_moves.json empty?
             ├───────────────┬───────────────────────────┐
             │ YES           │ NO                        │
             ▼               ▼                           │
   [First-Principles]    Pop highest-EV move             │
   [Diagnostic Probes]       │                           │
             │               ▼                           │
             │       Execute Front Step                  │
             │               │                           │
             │               ▼                           │
   Replenish 2-3 moves   Run Dual-Gate                   │
   in next_moves.json    Verification                    │
             │               │                           │
             └───────────────┴───────────────────────────┘
```

1. **Mandatory Continuation:** If all items in `plans/next_moves.json` have reached a terminal outcome (adopted or rejected) and the target predicate is not satisfied, the engine SHALL NOT halt.
2. **First-Principles Diagnostic Escalation:** The engine MUST transition to the `diagnose` or `research` front:
   - In distributed systems & datastores: Analyze connection pool starvation, lock contention, and queue backlog give-backs.
   - In quantitative & numerical engines: Analyze suppressed potential, opportunity costs, and peak-to-realized metric give-backs.
   - In web & microservices: Analyze latency breakdown by subsystem, flamegraphs, and thread contention.
   - In compilers & systems runtimes: Inspect instruction caches, memory layout, and branch prediction misses.
3. **Queue Replenishment:** From the diagnostic findings, the engine MUST synthesize 2–3 new structural hypotheses, insert them into `plans/next_moves.json`, and immediately resume the dispatch cycle.
4. **Simulation Freedom Invariant:** Annotations or documentation mentioning "operator-gated" or "requires human decision" apply strictly to live production environments. In headless evaluation (`eval` simulation), an OALP engine possesses **100% unconditional authorization** to simulate, benchmark, prototype, and falsify any architectural candidate.

---

## 9. Token Economics & Output Projection Wrapping

Unconstrained command streaming can exhaust LLM context windows within a dozen turns. An OALP engine MUST adhere to strict projection wrapping:

1. **Command Output Suppression:** Benchmark, compilation, and test commands producing voluminous stdout MUST redirect or suppress raw logs:
   - PowerShell: `command | Out-Null`
   - POSIX Shell: `command > /dev/null 2>&1`
2. **Scalar JSON Receipts:** The engine MUST extract only the final scalar result dictionary from the artifact file (e.g., `{"p99_latency_ms": 8.42, "tests_passed": 1280}`).
3. **Input Token Cap:** Per-turn terminal feedback returned to the model context MUST NOT exceed 2,500 bytes (~500 tokens), targeting a nominal budget of 150–250 tokens per step.
4. **Context Prefix Invariance:** The static instructions, `profile.yaml`, and system topology MUST remain byte-identical at the head of the prompt context across all iterations to achieve $\ge 90\%$ prompt cache hit rates with modern LLM inference APIs.

---

## 10. Security & Invariant Safety Considerations

1. **Hermetic Boundaries:** Candidates SHALL NOT modify files outside the repository boundary or access unauthorized network endpoints during evaluation.
2. **Protected Branches:** An OALP engine MUST NOT force-push or alter protected git branches (`origin/main`, `origin/master`) without explicit authorization configured in `profile.yaml`.
3. **Secret Isolation:** API credentials, private tokens, and environment secrets MUST NOT be written to `journal.jsonl`, `scratch/`, or committed to the repository history.

---

## 11. Appendix: Conformance Checklist

To certify a repository or agent framework as **OALP v1.0 Compliant**, the implementation MUST pass the following checks:

- [ ] Topology contains `.agents/loop/` (or `.loop/`) with all required state ledgers.
- [ ] Declarative seam `profile.yaml` validates against `profile.schema.json`.
- [ ] Engine executes all 12 fronts according to the dispatch priority ladder.
- [ ] Pre-evaluation git snapshot is created before every candidate benchmark.
- [ ] Immediate hard rollback is executed upon any invariant violation or metric drop.
- [ ] Every iteration generates an append-only entry in `journal.jsonl`.
- [ ] Engine automatically replenishes `plans/next_moves.json` upon queue exhaustion.
- [ ] Engine operates at $\ge 90\%$ prompt cache efficiency via output projection wrapping.

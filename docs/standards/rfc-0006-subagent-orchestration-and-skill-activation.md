# RFC-0006: Subagent Orchestration & Dynamic Skill Activation Protocol

- **RFC Number:** 0006
- **Title:** Subagent Orchestration & Dynamic Skill Activation Protocol
- **Status:** Proposed Standard (Working Draft)
- **Category:** Standards Track
- **Version:** 1.0.0-draft
- **Date:** October 2026
- **Authors:** Seismael & Antigravity Advanced Agentic Engineering Team

---

## Abstract

This document defines the normative requirements for **Subagent Orchestration** and **Dynamic Skill Activation** in the OpenAgent Loop Protocol (OALP). First-generation autonomous loops frequently exhibit "monolithic inline execution," where a single executive agent executes deep codebase searches, heavy multi-megabyte log parsing, indicator calculation, and code modifications within a single parent context window. This behavior inflates context to millions of tokens, accelerates context compaction, degrades reasoning depth, and induces false handoff anxiety. RFC-0006 specifies an **Orchestrator-Worker Split**, defines strict **Delegation Thresholds**, establishes the **Front-to-Skill Dynamic Activation Ladder**, and details native harness adaptation across OpenCode, Claude Code, and Antigravity.

---

## 1. Terminology & Conformance

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 [RFC 2119].

- **Session Orchestrator (Parent Agent):** The top-level executive agent running inside the primary session. It holds the loop state machine, decides the active move, executes git commits, and enforces invariant gates.
- **Worker Subagent (Child Agent):** An isolated, ephemeral, read-only agent spawned to perform deep exploratory searches, AST cross-references, or log digestion in a segregated context window.
- **Dynamic Skill Activation:** The explicit, in-session loading of domain-specific instructions and procedures into context only when the corresponding engineering front is active.

---

## 2. Motivation: The Monolithic Context Degradation Anti-Pattern

Empirical analysis of long-running autonomous loop sessions demonstrates that when agents perform all actions monolithically:
1. **Context Bloat:** 1,000+ tool calls (grepping tens of files, reading wide test suites, inspecting 80MB execution logs) inflate the parent context past 2M tokens.
2. **Context Compaction Disruption:** Frequent automated compactions discard nuanced transient observations, requiring repeated re-orientation.
3. **Budget & Handoff Anxiety:** As context grows, models exhibit learned hesitations, falsely concluding that large context mandates terminating the loop and yielding to the user.
4. **Skill Neglect:** Specialized domain skills registered in the environment sit completely unused because the agent relies on raw shell commands and generic pretraining rather than formal skill runbooks.

---

## 3. The Orchestrator-Worker Architecture

OALP mandates a strict functional separation between executive decisions and exploratory compute:

```
┌─────────────────────────────────────────────────────────────┐
│                 PARENT SESSION ORCHESTRATOR                 │
│  - Owns .agents/loop/ (loop.json, journal.jsonl)            │
│  - Evaluates Dual Gates (RFC-0002)                          │
│  - Dispatches Moves via Expected Value (RFC-0003)           │
│  - Applies Code Diffs & Makes Semantic Git Commits          │
│  - Context Budget: Terse, Bounded, Permanent State Only     │
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
       Spawns Subagents                Loads Specialized Skills
       (Isolated Contexts)             (Front-Specific Knowledge)
               │                               │
               ▼                               ▼
┌─────────────────────────────┐ ┌─────────────────────────────┐
│     SPECIALIZED WORKERS     │ │    DYNAMIC DOMAIN SKILLS    │
│  - Diagnostician (Forensics)│ │  - Latency / Profiling      │
│  - Architect (Design/Specs) │ │  - Resource Leak Diagnosis  │
│  - Verifier (Gate Audits)   │ │  - Cross-Workload Matrix    │
│  - Synthesizer (Log Bounds) │ │  - Formal Specification     │
│  * Output: <= 2,500 bytes   │ │  * Loaded dynamically       │
└─────────────────────────────┘ └─────────────────────────────┘
```

---

## 4. Mandatory Subagent Delegation Thresholds

An OALP Orchestrator **MUST NOT** perform deep exploration or large-scale data digestion directly in its main conversation turn. An Orchestrator **SHALL** delegate the task to a read-only subagent whenever any of the following conditions are met:

1. **Broad File System Exploration:** Any task requiring inspection or pattern-matching across $> 3$ files where the target path is not pre-known.
2. **Heavy File Digestion:** Reading or parsing any log, dataset partition, or ledger exceeding $50\text{ KB}$ (e.g. `traces.jsonl`, `metrics.jsonl`, `decisions.jsonl`).
3. **Spec Alignment & Cross-Reference Sweeps:** Auditing adherence across multiple normative documents or work packages.
4. **Multi-Step Diagnostic Probing:** Formulating counterfactual loss attribution that requires multi-query iterative scripting.

### 4.1 Subagent Contract & Deliverable Bounds
When dispatching a subagent, the Orchestrator MUST enforce:
- **Read-Only Invariant:** Subagents MUST NOT edit code, delete files, or make git commits.
- **Strict Output Projection:** Subagents MUST return a structured, bounded finding $\le 2,500$ bytes containing:
  1. Root cause summary ($\le 5$ bullet points).
  2. Exact evidence locations (`path:line` format).
  3. Actionable recommendation with concrete parameters/interfaces.

---

## 5. Generic Semantic Front-to-Skill Matching Protocol

An OALP Orchestrator operating within an environment exposing modular domain skills MUST NOT ignore registered skills. Prior to dispatching work on an engineering front, the Orchestrator SHALL dynamically inspect available host skills (`.agents/skills/`, `.opencode/skills/`, or host tools) and bind them to the active engineering front according to their semantic archetypes.

### 5.1 Canonical Semantic Front-to-Skill Dispatch Matrix

| Canonical Front | Target Objective / Operation | Matched Domain Skill Archetype | Dedicated Persona |
| :--- | :--- | :--- | :--- |
| **`diagnose`** | Bottleneck profiling, latency decomposition, error clustering | `*-diagnosis`, `*-profiling`, `*-metrics` | `diagnostician` |
| **`audit`** | Interface compliance, safety boundary checks, static linting | `*-audit`, `*-lint`, `*-security` | `verifier` |
| **`research`** | Theoretical bounds, literature/spec review, capability mining | `*-research`, `*-spec`, `*-oracle` | `synthesizer` |
| **`improve`** | Algorithmic refactoring, caching, data structure optimization | `*-optimization`, `*-refactor`, `*-tuning` | `architect` |
| **`harden`** | Regression defense, determinism checks, edge-case testing | `*-validation`, `*-fuzzing`, `*-testing` | `verifier` |
| **`pipeline`** | Build system, CI matrix, receipt aggregation | `*-pipeline`, `*-ci`, `*-build` | `synthesizer` |
| **`knowledge`** | Map of Content indexing, invariant compounding | `knowledge`, `*-docs` | `synthesizer` |

---

## 6. Harness Persona Harmonization

To guarantee complete portability across agent harnesses, project scaffolding MUST declare specialized agent personas in formats natively discoverable by each host runtime:

1. **OpenCode:** Materialized as Markdown definitions in `.opencode/agent/<name>.md`.
2. **Claude Code / MCP:** Materialized as tool definitions or plugin agent descriptors in `.claude-plugin/` and `tools/mcp_server.py`.
3. **Antigravity / Generic OALP:** Materialized as declarative YAML descriptors in `.agents/subagents/<name>.yaml`.

Scaffolding tools (such as `skills/loop/scripts/init_loop.py`) MUST generate both `.agents/subagents/*.yaml` and `.opencode/agent/*.md` to ensure zero runtime friction across all environments.

---

## 7. Non-Normative Case Study: High-Frequency Systems Skill Mapping

> [!NOTE]
> The mapping below illustrates how a complex real-world project (such as a high-frequency trading platform) binds its domain-specific skills into OALP's generic canonical fronts.

| Canonical Front | Real-World Domain Skill | Assigned Role |
| :--- | :--- | :--- |
| `diagnose` | `entry-gate-diagnosis` (missed opportunities) | Diagnostician |
| `diagnose` | `exit-quality-diagnosis` (peak vs realized metric give-back) | Diagnostician |
| `improve` | `cross-cell-generalization` (multi-asset evaluation) | Verifier |
| `improve` | `experiment-design` (combinatorial matrix testing) | Architect |
| `research` | `oracle-divergence-diagnosis` (theoretical limit analysis) | Synthesizer |
| `harden` | `validation-holdout-discipline` (overfitting prevention) | Verifier |

# RFC-0008: Dynamic Tool & Capability Synthesis Protocol

- **RFC Number:** 0008
- **Title:** Dynamic Tool & Capability Synthesis Protocol
- **Status:** Proposed Standard (Working Draft)
- **Category:** Standards Track
- **Version:** 1.0.0-draft
- **Date:** October 2026
- **Authors:** Seismael & Antigravity Advanced Agentic Engineering Team

---

## Abstract

This document defines the normative requirements for **Dynamic Tool and Capability Synthesis** in the OpenAgent Loop Protocol (OALP). Autonomous engineering loops frequently encounter diagnostic, verification, or data-extraction requirements that are not provided out-of-the-box by the target codebase. RFC-0008 establishes the formal lifecycle for **Just-In-Time (JIT) Tool Synthesis**, specifying how an autonomous engine authors, isolates, audits, and promotes bespoke CLI tools into `.agents/loop/scripts/` and registers them in `.agents/loop/env.json` and `capabilities.md` for permanent, zero-overhead reusability.

---

## 1. Terminology & Conformance

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 [RFC 2119].

- **Scratch Probe:** An ephemeral, non-committed script authored in `.agents/loop/scratch/` for one-off diagnostic or data-slicing purposes.
- **Promoted Tool:** A deterministic, zero-external-dependency script validated and installed into `.agents/loop/scripts/` and declared in `.agents/loop/env.json`.
- **Manifest Registration:** The formal declaration of a tool's invocation syntax, expected arguments, and output contract in the project's deterministic environment manifest.

---

## 2. Motivation: The Ephemeral Tooling Anti-Pattern

In typical AI coding sessions:
1. An agent writes a temporary script (`_test_extract.py`, `dump.py`) directly in the workspace root or in a random temp directory.
2. The script leaves git worktrees dirty, introduces uncommitted dependencies, and is discarded or lost when the context window compacts.
3. In subsequent iterations, the agent inevitably re-invents the exact same utility from scratch, burning thousands of tokens and introducing variance.

OALP standardizes tool creation as a first-class engineering lifecycle.

---

## 3. The 4-Stage Tool Synthesis Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Sandboxed Probing (.agents/loop/scratch/)                │
│    - Fast, ephemeral exploratory probe                      │
│    - Never pollutes git root (INV-09 compliance)            │
│    - Produces bounded output (<= 2,500 bytes)               │
└──────────────────────────────┬──────────────────────────────┘
                               │ Verified useful across iterations
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Audit & Hardening Gate                                   │
│    - Standard CLI argument parsing (argparse / click / flag)│
│    - Zero external dependencies (standard library only)     │
│    - Deterministic exit codes (0 = success, non-zero = fail)│
└──────────────────────────────┬──────────────────────────────┘
                               │ Passed Hardening Gate
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Promotion to Scripts (.agents/loop/scripts/)             │
│    - Installed into canonical project scripts directory     │
│    - Documented with markdown docstring & usage examples    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Manifest & Knowledge Registration                        │
│    - Added to .agents/loop/env.json under "tools"           │
│    - Documented in .agents/loop/knowledge/capabilities.md   │
│    - Instantly discoverable by all future loop iterations   │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Promotion Criteria & Invariants

An engine SHALL NOT promote a scratch script to `.agents/loop/scripts/` unless it satisfies the following criteria:

1. **Zero External Dependencies:** The tool MUST use only the standard library of the project's primary runtime (e.g. standard library Python, Go, Rust, or Node.js) or dependencies already declared in the project's lockfile.
2. **Deterministic Output Contract:** The tool MUST emit clean, machine-parseable JSON or byte-bounded text ($\le 2,500$ bytes).
3. **Execution Idempotence:** Running the tool multiple times with identical inputs MUST produce identical outputs without side-effects on repository state.
4. **Isolated Path Resolution:** All read/write targets MUST resolve relative to declared arguments or environment variables; hardcoded machine paths are strictly forbidden.

---

## 5. Environment Manifest Registration (`env.json`)

Upon successful promotion, the tool MUST be registered in `.agents/loop/env.json`:

```json
{
  "tools": {
    "ast_slice": "python .agents/loop/scripts/ast_slice.py",
    "receipt_diff": "python .agents/loop/scripts/receipt_diff.py",
    "gate_sweep": "python .agents/loop/scripts/gate_sweep.py"
  }
}
```

Future iterations and subagents consult `env.json` directly, eliminating token-wasting discovery greps and ensuring consistent multi-agent reusability.

# RFC-0005: Universal Harness Adapter Interface for OHP

- **RFC Number:** 0005
- **Title:** Universal Harness Adapter Interface for Open Harness Protocol
- **Status:** Proposed Standard (Working Draft)
- **Category:** Standards Track
- **Version:** 1.0.0-draft
- **Date:** October 2026
- **Authors:** Seismael & Antigravity Advanced Agentic Engineering Team

---

## Abstract

This document defines the normative requirements for **Harness Adapters** that connect arbitrary AI agent runtimes (such as Claude Code, Google Antigravity, OpenCode, Cursor, Windsurf, Copilot Workspace, and headless CI runners) to an OHP-compliant repository. By specifying standard invocation surfaces, state synchronization mechanisms, output projection filtering, and subagent delegation protocols, this RFC ensures cross-platform portability without modifying target repository physics.

---

## 1. Conformance Requirements

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 [RFC 2119].

A **Compliant Harness Adapter** is any module, plugin, server, or script that bridges a host agent environment with the `.agents/` repository topology in accordance with the contracts defined herein.

---

## 2. Adapter Responsibilities & Architecture

An OHP Harness Adapter SHALL fulfill four fundamental obligations:

```
┌────────────────────────────────────────────────────────┐
│                   HOST AGENT RUNTIME                   │
│   (Claude Code, Antigravity, Cursor, OpenCode, CI/CD)  │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│               OHP HARNESS ADAPTER LAYER               │
├────────────────────────────────────────────────────────┤
│ 1. Seam Discovery: Locates .agents/loop/ & profile.yaml│
│ 2. Tool Binding: Maps skills, slash cmds & MCP tools   │
│ 3. Projection Wrapping: Enforces scalar stdout filters │
│ 4. State Ledger Sync: Commits to journal.jsonl & loop  │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│                  TARGET REPOSITORY                     │
│    (Git working tree, build tools, evaluation suites)  │
└────────────────────────────────────────────────────────┘
```

---

## 3. Seam Discovery Protocol

1. **Resolution Order:** An adapter MUST search for the repository declarative seam in the following order:
   - Primary: `<project-root>/.agents/loop/knowledge/profile.yaml`
   - Legacy: `<project-root>/.loop/knowledge/profile.yaml`
   - Secondary Fallback: `<project-root>/docs/knowledge/profile.yaml`
2. **Missing Seam Behavior:** If no profile is found, the agent SHALL scaffold the repository using its internal initialization routine (`init_loop.py`) from an appropriate starter template.

---

## 4. Invocation Surfaces

An adapter SHOULD expose at least one of the following standard interaction surfaces:

### 4.1 Slash Command Interface
For chat-based harnesses supporting slash commands (Claude Code, Antigravity):
- `/loop "<target>"`: Launches or resumes the autonomous optimization loop.
- `/audit "<focus>"`: Launches a read-only audit against user goals and invariants.

### 4.2 Model Context Protocol (MCP) Interface
For IDEs and desktop harnesses supporting the Model Context Protocol (Cursor, Windsurf, Claude Desktop):
- The adapter MUST expose `loop_status`, `loop_step`, `loop_verify`, and `loop_journal`.
- The MCP tools MUST return valid JSON strings conforming to OHP schemas.

### 4.3 Headless CI/CD Runner Interface
For CI/CD runners and containerized environments:
- The adapter SHALL support non-interactive execution via the host agent runtime's native headless invocation (e.g., `opencode run "/loop ..."` or `claude -p "/loop ..."`), driving the optimization cycle until completion criteria are met without human intervention.

---

## 5. Output Projection & Token Protection Contract

Host runtimes frequently leak large stdout/stderr streams into LLM context. An OHP adapter MUST enforce output suppression:

1. **Shell Command Execution:**
   - Any evaluation command defined in `profile.yaml` MUST have its raw stdout suppressed at the process boundary.
   - On Windows: Append `| Out-Null` or redirect `> $null 2>&1`.
   - On POSIX: Redirect `> /dev/null 2>&1`.
2. **Scalar Extraction:**
   - The adapter SHALL inspect the artifact file designated in `profile.yaml`, parse its contents, and return only the target scalar metric to the model.
   - The returned message payload MUST NOT exceed 2,500 bytes.

---

## 6. Subagent Delegation Protocol

When a host runtime supports subagent invocation (e.g. `invoke_subagent` in Antigravity or multi-agent dispatch in Claude Code):
1. **Read-Only Personas:** Subagents dispatched for `orient`, `discover`, `diagnose`, or `audit` MUST operate with read-only filesystem permissions.
2. **Bounded Synthesis:** Subagents MUST return concise structured summaries (<= 2,500 bytes) rather than dumping raw file contents into the parent context.
3. **Single Mutating Thread:** Only the primary loop engine SHALL execute git commits, diff applications, and rollbacks.

---

## 7. Compliance Verification

An adapter is certified compliant when it successfully executes the automated test suite in `tests/test_harness_adapter.py` (or equivalent test runner), confirming:
- Accurate schema validation of `profile.yaml`.
- Zero context leakage of raw benchmark stdout.
- Exact git rollback execution upon simulated invariant failure.

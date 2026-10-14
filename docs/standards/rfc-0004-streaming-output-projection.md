# RFC-0004: Streaming Output Projection & Radical Token Economics

- **RFC Number:** 0004
- **Title:** Streaming Output Projection & Radical Token Economics
- **Status:** Proposed Standard (Working Draft)
- **Category:** Standards Track
- **Version:** 1.0.0-draft
- **Date:** October 2026
- **Authors:** Seismael & Antigravity Advanced Agentic Engineering Team

---

## Abstract

This document defines the normative requirements for **Streaming Output Projection** and **Radical Token Economics** in the OpenAgent Loop Protocol (OALP). Unconstrained AI coding agents rapidly deplete LLM context windows by streaming raw compilation, test runner, and benchmark outputs directly into conversational history. This specification mandates process-level stdout suppression, single-line scalar JSON projection wrapping, context prefix invariance, and prompt cache alignment, enabling multi-hour, multi-day autonomous research sessions at negligible operating expense (<$0.20 per 10 hours).

---

## 1. Terminology & Conformance

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 [RFC 2119].

**Output Projection:** The process of capturing a command's raw multi-megabyte terminal output, redirecting it to disk or `/dev/null`, and extracting only the minimal scalar metrics required by the cognitive engine.

---

## 2. Motivation: The Token Burn Catastrophe

In standard agentic frameworks, executing a test suite or backtester results in thousands of lines of terminal output being echoed directly into the agent's context window.

```
Standard Agent:
LLM -> runs pytest -> 25,000 tokens of raw stdout streamed into context
Result: Context window saturates in 15 turns; costs $15–$50/hour; triggers lossy compaction.

OALP Engine:
LLM -> runs pytest | Out-Null -> reads single-line scalar JSON receipt (150 tokens)
Result: Runs 130+ turns continuously; costs <$0.20 total; 96.9% prompt cache hit rate.
```

OALP eliminates token waste through two core mechanisms: **Projection Filtering** and **Prefix Invariance**.

---

## 3. Output Projection Filtering Contract

An OALP engine MUST NOT stream raw stdout or stderr of evaluation pipelines into the LLM context.

### 3.1 Process-Level Suppression
All commands executed as part of the pipeline defined in `profile.yaml` SHALL suppress stdout at the operating system process boundary:
- **Windows PowerShell:** `command | Out-Null` or `command > $null 2>&1`
- **POSIX Shells:** `command > /dev/null 2>&1`

### 3.2 Scalar JSON Receipts
Evaluation results MUST be written to an artifact file (e.g., `target/results.json`, `build/receipt.json`).
- The engine SHALL extract only the specific scalar keys declared in `profile.yaml`:
  Example: `{"net_pnl": 1042.50, "p99_latency_ms": 8.42, "tests_passed": 1280}`
- The projected receipt returned to the model context MUST NOT exceed **2,500 bytes** (~500 tokens), targeting a nominal budget of **150–250 tokens per turn**.

---

## 4. Context Prefix Invariance & Prompt Caching

Modern LLM inference providers (Anthropic, DeepSeek, Google, OpenAI) implement KV-cache prompt caching: static prompt prefixes that remain byte-identical across requests are served from GPU memory at an 80%–90% price discount and near-zero latency.

### 4.1 Byte-Static Prefix Rule
To maximize prompt cache hit rates, an OALP engine MUST maintain static prefix ordering:
1. **Head (Static):** System prompt, protocol rules, tool definitions, declarative seam (`profile.yaml`), system invariants (`invariants.md`), toolchain manifest (`env.json`).
2. **Middle (Infrequent):** Architectural wiki summary (`knowledge/index.md`).
3. **Tail (Dynamic):** Active turn receipts, current iteration candidate diff, latest scalar outcome.

An engine MUST NOT insert dynamic timestamps, random IDs, or changing counters into the static prefix head.

### 4.2 Cache Efficiency Target
An OALP-compliant engine SHOULD achieve an average **Prompt Cache Hit Rate of $\ge 90\%$** across sessions exceeding 20 iterations.

---

## 5. Automated Context Compaction Invariance

When long-running agent sessions reach maximum context capacity:
1. The host runtime's automated summarization or compaction algorithm MAY truncate conversation history.
2. Because all OALP state is durably persisted on disk (`loop.json`, `journal.jsonl`, `decisions/`, `coverage.json`), the engine **survives context compaction with zero cognitive drift**.
3. Upon compaction, the engine resumes seamlessly by re-reading `loop.json` and continuing the dispatch cycle.

---

## 6. Empirical Proof: Apex Quantitative Benchmark

The OALP token economics standard was validated in an overnight production audit on **Apex**, an institutional cryptocurrency trading platform:

| Metric | Measured Value | Standard Threshold |
| :--- | :--- | :--- |
| **Session Duration** | 10 hours, 25 minutes | $\ge 6$ hours |
| **Engine Iterations / Turns** | 132 turns | $\ge 50$ turns |
| **Total Cached Tokens Read** | 14,832,896 tokens | — |
| **Prompt Cache Hit Rate** | **96.93%** | $\ge 90.0\%$ |
| **Total Session API Cost** | **$0.1938** (less than $0.20) | $\le \$2.00$ |
| **Average Cost per Turn** | **$0.00147** (~1/7th of 1 cent) | $\le \$0.02$ |

This establishes OALP as the most economically viable autonomous agent protocol in industry literature.

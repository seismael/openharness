# RFC-0002: Dual-Gate Verification & Mathematical Invariant Protocol

- **RFC Number:** 0002
- **Title:** Dual-Gate Verification & Mathematical Invariant Protocol
- **Status:** Proposed Standard (Working Draft)
- **Category:** Standards Track
- **Version:** 1.0.0-draft
- **Date:** October 2026
- **Authors:** Seismael & Antigravity Advanced Agentic Engineering Team

---

## Abstract

This document specifies the normative requirements for the **Dual-Gate Verification Protocol** in the Open Harness Protocol (OHP). In autonomous software engineering and computational optimization, improvements on a primary metric must not introduce silent regressions across existing system invariants. This specification defines the mathematical contract for candidate acceptance, pre-evaluation git snapshot semantics, invariant test suite classification, atomic rollback procedures, and synthetic fixture realignment rules.

---

## 1. Terminology & Conformance

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 [RFC 2119].

A candidate state $S_{\text{candidate}}$ is defined as a mutation applied to a base repository state $S_{\text{champion}}$ via code, configuration, or algorithmic modifications.

---

## 2. Motivation

Traditional autonomous agents frequently introduce subtle collateral damage:
- An optimization targeting API latency may increase memory consumption or leak thread handles.
- A candidate optimization may boost throughput on synthetic workloads while causing catastrophic tail latency degradation under bursty production traffic.
- A refactored algorithm may satisfy unit tests while failing numerical float parity against baseline receipts.

OHP eliminates collateral regression through a strict, deterministic **Dual-Gate Contract**.

---

## 3. The Dual-Gate Mathematical Contract

Acceptance of a candidate state $S_{\text{candidate}}$ over the incumbent champion state $S_{\text{champion}}$ SHALL be governed by the following conjunction:

$$\text{Accept}(S_{\text{candidate}}) \iff \left( M(S_{\text{candidate}}) \succ M(S_{\text{champion}}) \right) \land \left( \bigwedge_{j=1}^{k} I_j(S_{\text{candidate}}) = 1 \right)$$

Where:
- $M(S)$ is the scalar or vector objective evaluation function defined in `profile.yaml`.
- $\succ$ denotes strict monotonic improvement according to the directionality specified in `profile.yaml` (e.g., lower latency, higher Sharpe ratio, smaller memory footprint).
- $I_1, I_2, \dots, I_k$ denote the set of certified system invariants (unit test suites, linting checks, type checkers, memory bounds, numerical float parity controls).
- $I_j(S) = 1$ indicates that invariant suite $j$ passed with zero failures, zero errors, and zero regression warnings.

If any invariant evaluates to $0$, $\text{Accept}(S_{\text{candidate}})$ MUST evaluate to `FALSE`, regardless of the magnitude of improvement in $M(S)$.

---

## 4. Git State Machine & Atomic Rollback Protocol

To ensure reproducible provenance and prevent uncommitted workspace corruption, every candidate mutation MUST pass through three distinct git states:

```
                  ┌───────────────────────────────┐
                  │    Incumbent Champion S_0     │
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                     [Apply Candidate Mutation]
                                  │
                                  ▼
                  ┌───────────────────────────────┐
                  │    Pre-Evaluation Snapshot    │
                  │   git commit: feat(candidate) │
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                      [Execute Pipeline & Gates]
                                  │
                 ┌────────────────┴────────────────┐
                 │                                 │
        [Both Gates PASS]                 [Either Gate FAILS]
                 │                                 │
                 ▼                                 ▼
   ┌───────────────────────────┐     ┌───────────────────────────┐
   │         ADOPTED           │     │     ATOMIC ROLLBACK       │
   │ git commit --amend or     │     │ git reset --hard HEAD~1   │
   │ feat(adopt): <hypothesis> │     │ Record D-xxx in decisions/│
   │ Update loop.json champion │     │ Append rejection receipt  │
   └───────────────────────────┘     └───────────────────────────┘
```

### 4.1 Pre-Evaluation Snapshot Requirement
An OHP engine MUST NOT execute benchmark or evaluation commands on an uncommitted or dirty working tree.
- The engine SHALL stage and commit the working tree prior to initiating evaluation:
  `git commit -m "feat(candidate): [front] <concise hypothesis statement>"`
- This snapshot guarantees that evaluation artifacts map cryptographically to an exact git commit hash.

### 4.2 Atomic Rollback Semantics
Upon rejection ($\text{Accept}(S_{\text{candidate}}) = \text{FALSE}$):
- The engine MUST execute an immediate hard rollback to restore the incumbent champion:
  `git reset --hard HEAD~1`
- The engine SHALL clean any untracked evaluation artifacts:
  `git clean -fd`
- The engine MUST record the failure rationale, empirical receipts, and root cause in `knowledge/decisions/D-<iteration>.md` and append an entry to `journal.jsonl`.
- The engine MUST NOT retry the identical code diff in subsequent iterations.

---

## 5. Invariant Classification & Verification Hierarchy

An OHP-compliant repository SHALL classify its verification gates into three tiers:

| Tier | Category | Scope | Execution Frequency |
| :--- | :--- | :--- | :--- |
| **Tier 1: Fast Invariants** | Unit tests, static typing, linters (`ruff`, `cargo check`) | Target subsystem (< 10 seconds) | Evaluated before running benchmarks |
| **Tier 2: System Invariants** | Full test suite, integration tests, contract checks | Whole repository (< 60 seconds) | Evaluated concurrently with benchmark |
| **Tier 3: Control Pools** | Historical baseline controls, out-of-sample holdouts | Certified ground truth dataset | Evaluated prior to final adoption commit |

---

## 6. Synthetic Fixture Realignment vs. Regressions

When an architectural improvement intentionally alters nominal baseline outputs (e.g. changing an allocation formula or optimizing a data layout), static unit tests asserting old nominal outputs will fail.

An OHP engine MUST distinguish between **functional regressions** and **stale nominal fixtures**:
1. **Disallowed Fixture Weakening:** An engine MUST NOT delete assertions, weaken bounds, or skip tests to force an invariant gate to pass.
2. **Authorized Realignment:** If an improved mechanism changes expected scalar outputs, the engine MAY update the expected nominal values in test fixtures IF AND ONLY IF:
   - The test was verifying the old formula's nominal value, not an architectural boundary.
   - The updated fixture assertion reflects the exact mathematical output of the newly adopted champion.
   - The fixture update is committed in the same atomic commit as the mechanism change.

---

## 7. Numerical Determinism & Float Parity Receipts

In computational, scientific, and quantitative repositories:
- Candidates MUST be evaluated against historical control pools to verify that unchanged codepaths retain exact numerical determinism.
- Control pool checks SHOULD assert floating-point parity up to IEEE 754 double-precision tolerances (or exact 28-decimal parity in fixed-point arithmetic).
- Rejection receipts MUST record the exact numerical divergence observed (e.g., `+18.4ms p99 latency`, `-12.4% throughput`, or `+4.2MB heap allocation`).

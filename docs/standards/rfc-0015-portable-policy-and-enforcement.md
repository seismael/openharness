# RFC-0015: Portable Action Policy and Adapter Enforcement

- **RFC Number:** 0015
- **Title:** Portable Action Policy and Adapter Enforcement
- **Status:** Proposed Standard (Working Draft)
- **Category:** Standards Track
- **Version:** 1.0.0-draft
- **Date:** October 2026
- **Authors:** Seismael & Antigravity Advanced Agentic Engineering Team

---

## Abstract

This document defines a **portable action policy**: a small ordered rule set evaluated locally, in-session, with last-match-wins semantics, producing one of three verdicts — `allow`, `ask`, or `deny`. The same document and the same evaluation apply on every adapter, so a constraint written once is enforced everywhere it can be, and **declared** everywhere it cannot. The second half of this document defines how an adapter reports the difference instead of implying coverage it does not have.

---

## 1. Terminology & Conformance

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 [RFC 2119].

- **Request:** The declarative description of an action: `tool`, `path`, `command`, or a subset.
- **Rule:** An id, a `match` object, a `verdict`, and an optional `reason`.
- **Match condition:** `tool` (case-insensitive equality), `path_glob` (shell glob over the forward-slash normalized path), `command_regex` (regular expression searched in the command text).
- **Verdict:** `allow` (proceed), `ask` (require confirmation), `deny` (refuse).
- **Default:** The verdict when no rule matches. It MUST be `ask` unless declared otherwise.

---

## 2. Motivation

Guardrails normally live in one host's configuration syntax. Move the work to another runtime and the constraint is gone, while the documentation still claims it exists. That is worse than having no constraint: the agent believes it is bounded.

A policy document decouples **what must not happen** from **which runtime enforces it**. Evaluation is pure and synchronous, so every adapter can run the same rules, and the ones that cannot must say so.

---

## 3. Policy Document

```json
{
  "schema": "openharness.policy.v1",
  "default": "ask",
  "rules": [
    {"id": "read-only-tools", "match": {"tool": "read"}, "verdict": "allow"},
    {"id": "declared-pipeline", "match": {"tool": "shell", "command_regex": "^python -m pytest\\b"},
     "verdict": "allow", "reason": "the project's declared pipeline"},
    {"id": "no-secret-reads", "match": {"path_glob": "**/.env*"}, "verdict": "deny",
     "reason": "secret material is out of scope"},
    {"id": "no-destructive", "match": {"tool": "shell", "command_regex": "\\brm\\s+-rf\\b"},
     "verdict": "deny", "reason": "destructive command"}
  ]
}
```

- **POL-01** A policy MUST declare `schema: openharness.policy.v1`. Unknown top-level or rule fields MUST be rejected, because an unread constraint is an absent constraint.
- **POL-02** Rule ids MUST be non-empty and unique. The id is what appears in the audit trail.
- **POL-03** A `match` object MUST contain at least one condition, and every condition present MUST hold for the rule to match. An empty match would match everything unconditionally.
- **POL-04** A condition whose input was not supplied MUST NOT be treated as satisfied. A rule requiring `command_regex` does not match a path-only request.
- **POL-05** Evaluation MUST be last-match-wins: each matching rule overwrites the previous verdict. Later rules refine earlier ones, so a broad allow can be narrowed without reordering the document.
- **POL-06** When no rule matches, the verdict MUST be the document's `default`, and the default MUST be `ask` unless the document explicitly declares otherwise.
- **POL-07** Verdicts MUST be exactly `allow`, `ask`, or `deny`. There is no numeric score and no implicit coercion.
- **POL-08** The `reason` of the deciding rule MUST be surfaced. A denial without a reason cannot be corrected.
- **POL-09** Evaluation MUST be local, synchronous, and model-free. A policy that needs a network call is not enforceable in the moment it matters.
- **POL-10** An invalid regular expression, duplicate id, unknown field, or wrong schema MUST fail evaluation with exit `2` before any action is taken. A policy that silently degrades is worse than none.
- **POL-11** The projection MUST be bounded at 2500 bytes and MUST be deterministic for identical requests.
- **POL-12** Exit codes MUST be `0` for `allow`, `1` for `deny`, `3` for `ask`, and `2` for an unusable policy or request. `ask` is deliberately not `0`: an unconfirmed action is not an approval.

---

## 4. Adapter Enforcement Matrix

An adapter MUST publish, for each mechanism this series defines, how it is enforced in that host. Exactly one level applies per mechanism:

| Level | Meaning |
| :--- | :--- |
| `native` | The host enforces it without the agent's cooperation. |
| `adapter` | The adapter's command, agent, or script enforces it deterministically. |
| `documented` | The protocol requires it, the host cannot enforce it, and the documentation says so explicitly. |

`documented` is an honest gap, not a failure. The prohibited state is an adapter that implies enforcement it does not provide.

| Mechanism | Artifact | OpenCode binding |
| :--- | :--- | :--- |
| Harness audit | `openharness_audit.py` | `adapter` — `/openharness` runs it before any change |
| Iteration contract | `openharness_verify.py` | `adapter` — `/openharness` validates the journal entry |
| Anonymous selection | `openharness_select.py` | `adapter` — used when more than one candidate exists |
| Declared cases | `openharness_cases.py` | `adapter` — probe receipts are produced with it |
| Telemetry | `openharness_telemetry.py` | `adapter` — reported, never inferred |
| Inventory | `openharness_inventory.py` | `adapter` — read at the start of an optimization run |
| Failure taxonomy | `openharness_failures.py` | `adapter` — classifies failures before the next iteration |
| Portable policy | `openharness_policy.py` | `documented` — the host has its own permission model; the script is the reference evaluation |

- **POL-13** An adapter README MUST contain this matrix with all eight mechanisms, each bound to one level and one artifact.
- **POL-14** A mechanism marked `adapter` MUST name an artifact that exists in the repository and is invoked by the adapter's command or agent. The conformance test verifies both.
- **POL-15** A mechanism marked `documented` MUST state the host limitation in the same section. Silence reads as enforcement.

---

## 5. Interaction with the Loop

- **POL-16** A `deny` verdict is terminal for that action. The loop MUST NOT retry a denied action through another surface or a differently worded command.
- **POL-17** An `ask` verdict blocks autonomous continuation until a human answers. The loop MAY continue on an unrelated front, and MUST record the pending question.
- **POL-18** A policy change is an `invariant` candidate: it MUST be probed on at least two cases, including one denial case, before adoption.

---

## 6. Reference Implementation

- Evaluator: [`skills/loop/scripts/openharness_policy.py`](../../skills/loop/scripts/openharness_policy.py)
- Regression suite: [`skills/loop/scripts/test_openharness_policy.py`](../../skills/loop/scripts/test_openharness_policy.py)
- Policy schema: [`schemas/policy.schema.json`](schemas/policy.schema.json)
- Adapter matrix: [`adapters/opencode/README.md`](../../adapters/opencode/README.md)
- Adapter conformance test: [`tests/test_harness_adapter.py`](../../tests/test_harness_adapter.py)

---

## 7. Conformance

An implementation is conforming when it evaluates a policy document locally with last-match-wins semantics, refuses an empty match, treats absent inputs as non-matching, defaults to `ask`, returns the deciding rule and reason, fails closed on an invalid document, distinguishes `allow` from `ask` in its exit code, and publishes an enforcement matrix that names a real artifact for every mechanism it claims to enforce.

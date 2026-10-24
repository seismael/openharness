# RFC-0016: Harness Lockfile and Drift Plan

- **RFC Number:** 0016
- **Title:** Harness Lockfile and Drift Plan
- **Status:** Proposed Standard (Working Draft)
- **Category:** Standards Track
- **Version:** 1.0.0-draft
- **Date:** October 2026
- **Authors:** Seismael & Antigravity Advanced Agentic Engineering Team

---

## Abstract

This document defines **`harness.lock`**, a content-addressed record of an accepted agent harness, and the **plan** operation that explains how the current tree differs from it. The lock turns an agent harness into a reviewable engineering artifact: a change to an instruction, a skill, a command, a policy, or a case set becomes an attributed diff with a stable identity. The plan is deterministic, needs no network or model call, and can gate continuous integration.

---

## 1. Terminology & Conformance

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 [RFC 2119].

- **Harness state:** The set of files matched by an accepted manifest, plus the declaration documents the audit composes with.
- **Fingerprint:** SHA-256 over sorted `(relative POSIX path, SHA-256 of content)` pairs, one pair per unique path. It identifies content and nothing else.
- **Lock:** The document described in Section 3.
- **Drift:** Any difference in content, membership, or declaration hash between the lock and the current state.
- **Change:** One drift record, attributed to a file, a component, or a declaration.

---

## 2. Motivation

A prompt, a skill, and a command file are code that shapes production behavior, yet they are usually reviewed by memory. Two failures follow:

1. **Silent drift.** Someone edits an always-on instruction or a policy, CI stays green, and the next incident is explained by "the agent got worse".
2. **Unreviewable growth.** Always-on context expands release by release, and nobody can say what it costs or when it changed.

A lockfile solves both with a familiar mechanism. Infrastructure tools version the desired state and plan the difference; package managers version dependencies with a lock. The harness deserves the same treatment.

---

## 3. Lockfile Document

The lock is a JSON object:

```json
{
  "schema": "openharness.lock.v1",
  "manifest": "example",
  "fingerprint": "<64 hex>",
  "budget": { "always_on_tokens": 4000, "total_tokens": 150000 },
  "totals": {
    "always_on_tokens": 511,
    "total_tokens": 91426,
    "files": 40,
    "components": 7
  },
  "components": [
    {
      "id": "agents",
      "kind": "system_prompt",
      "enabled": true,
      "always_on": true,
      "tokens": 511,
      "files": [
        { "path": "AGENTS.md", "sha256": "<64 hex>", "tokens": 511 }
      ]
    }
  ],
  "declarations": {
    "policy": { "path": "policy.json", "sha256": "<64 hex>" },
    "cases": { "path": "cases.json", "sha256": "<64 hex>" },
    "requirements": { "path": "requirements.json", "sha256": "<64 hex>" }
  },
  "generator": { "name": "openharness", "version": "0.2.0" }
}
```

### 3.1 Requirements

- `schema` MUST be `openharness.lock.v1`.
- `fingerprint` MUST equal the fingerprint of the accepted state.
- `components` MUST preserve manifest order. `files` MUST be sorted by path.
- Every `sha256` MUST be lowercase hexadecimal over the exact file bytes.
- `declarations` MUST include every declaration document that existed when the lock was taken. An absent declaration MUST be omitted, not recorded as null.
- `generator` MUST record the producing tool and version. It MUST be excluded from drift comparison, so upgrading the tool alone does not report drift.
- The document MUST serialize with sorted keys and two-space indentation, ending with a newline.

### 3.2 Token estimates

`tokens` is the deterministic character estimate used by the audit: `ceil(code_points / 4)`. It is a budget instrument, not a model tokenizer, and MUST NOT be presented as billing data.

---

## 4. Drift

The plan operation recomputes the lock from the current tree and compares it with the recorded lock.

A change record MUST contain:

| Field | Meaning |
| :--- | :--- |
| `change` | `added`, `removed`, `modified`, `declaration`, `component-added`, or `component-removed`. |
| `component` | Component id, or null for a declaration change. |
| `path` | Repository-relative path, or null for a component-level change. |
| `tokens_before` | Previous estimate, or null when the file did not exist. |
| `tokens_after` | Current estimate, or null when the file no longer exists. |
| `declaration` | Declaration name, present only for `declaration` changes. |

A file is `modified` when both copies exist and their `sha256` differs. It is `added` or `removed` when membership differs. Changes MUST be ordered by component and then path, so two runs produce identical output.

### 4.1 Human projection

The default projection is one line per change:

```text
~ AGENTS.md (agents) +5 tokens
+ skills/release/SKILL.md (skills) +212 tokens
- docs/old-runbook.md (readme) -340 tokens
~ policy.json (declaration: policy)
drift: 4 change(s) across 3 component(s)
```

`~` means modified, `+` added, `-` removed. The token delta is signed and derived from `tokens_after - tokens_before`.

### 4.2 Verdict

`plan` MUST exit `0` when the state matches and `1` when it does not, when invoked in check mode. Without check mode it is informational and MUST exit `0`, because a preview is not a failure. Invalid input MUST exit `2`.

---

## 5. Determinism

The lock and plan MUST NOT read the clock, the environment, the network, or a model. Given identical bytes, they MUST produce identical output on Linux, macOS, and Windows. Paths in the lock MUST use `/` and MUST be relative to the manifest directory; an absolute path MUST NOT appear.

---

## 6. Conformance

An implementation conforms when it can:

1. Produce a lock whose fingerprint equals the audit fingerprint for the same state.
2. Reproduce the lock byte-for-byte from an unchanged tree.
3. Detect a one-line change in an always-on file and attribute it to that file and component.
4. Detect an added and a removed file.
5. Detect a declaration change by hash.
6. Ignore `generator.version` when comparing.
7. Exit `0`, `1`, and `2` as specified.

The reference implementation proves each item in `tests/test_cli_contract.py` and freezes the output in `tests/golden/`.

---

## 7. Security Considerations

- The lock is evidence of content, not of authorship. Signing or commit review remains the repository's responsibility.
- A declaration is an input. Reviewing `harness.json` and `policy.json` is part of reviewing the lock.
- A lockfile can be regenerated to hide a change. CI MUST run check mode against a committed lock; the diff, not the regeneration, is the review artifact.
- Hashes cover content only. File modes, symlink targets, and ownership are out of scope; hosts and repositories enforce those.

---

## 8. References

- [RFC-0009](rfc-0009-openharness.md): harness surface and audit receipt.
- [RFC-0012](rfc-0012-declared-evaluation-cases.md): declared cases whose hashes the lock records.
- [RFC-0015](rfc-0015-portable-policy-and-enforcement.md): portable policy whose hash the lock records.
- [lock.schema.json](schemas/lock.schema.json): machine-readable contract.

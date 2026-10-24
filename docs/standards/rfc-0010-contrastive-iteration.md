# RFC-0010: Contrastive Iteration

- **RFC Number:** 0010
- **Title:** Contrastive Iteration
- **Status:** Proposed Standard (Working Draft)
- **Category:** Standards Track
- **Version:** 1.0.0-draft
- **Date:** October 2026
- **Authors:** Seismael & Antigravity Advanced Agentic Engineering Team

---

## Abstract

This document defines how an OHP loop improves a **harness** — the eight components in RFC-0009 — without a ground-truth verifier for every possible task. It adds four things the existing series leaves implicit: a declared scope for every change, a behavioral contrast vocabulary tied to a named deficiency, an anonymous adoption step when more than one candidate exists, and an evidence gate on retained knowledge. It introduces no new state root: every record lands in the loop's existing journal, knowledge base, and receipts.

---

## 1. Terminology & Conformance

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 [RFC 2119].

- **Iteration:** One trip around the loop's execution cycle, recorded as one journal entry.
- **Candidate:** One bounded change to the harness or the project under evaluation.
- **Case:** One declared evaluation input. A project decides what a case is — a test, a task, a fixture, a scenario, or any other evaluation unit. The protocol does not prescribe how many cases a project declares, only that its claims name the ones they rest on.
- **Probe:** Execution of an exact harness state against one or more cases.
- **Deficiency:** The named behavior class a candidate targets (planning, tool-use, context-management, delegation, knowledge, procedure, constraint, reliability, cost).
- **Contrast:** The behavioral verdict of a probe relative to the reference execution: `mitigated`, `unchanged`, `regressed`, or `unproven`.
- **Evidence entry:** A retained lesson in `.agents/loop/knowledge/` that cites a receipt.

This document names abstractions only. A conforming implementation MUST NOT bind a domain's instance vocabulary into schema fields, filenames, or state paths.

---

## 2. Motivation

Three failure modes recur in harness optimization:

1. **Unmeasured adoption.** A change is adopted because its author describes it well. Without an execution of that exact harness state, the claim describes a proposal, not a system.
2. **Scope drift.** A change that helps one case is silently treated as a general improvement, so a local win becomes a global regression.
3. **Knowledge inflation.** Lessons are retained because they sound true, then reused as premises. Retained text becomes an unverified dependency.

Contrastive iteration addresses all three with records the loop already produces.

---

## 3. The Contrastive Iteration

```
1. Reference   -- run the current harness on the declared cases
2. Propose     -- declare scope, deficiency, cases, and falsifier
3. Probe       -- execute the candidate on the same cases, matched conditions
4. Contrast    -- classify the result against the deficiency
5. Compose     -- merge supported edits, adopt one candidate, or preserve
6. Record      -- journal entry with fingerprint, contrast, decision, evidence
7. Compound    -- retain an evidence entry, or record why nothing was retained
```

A conforming implementation MUST complete steps 2 through 6 for any change it adopts. Matched conditions mean the same model, the same case set, and the same pipeline; a probe under different conditions yields `unproven`, not a verdict.

---

## 4. Scope Declaration

- **CIT-01** Every adopted candidate MUST declare `scope: invariant` or `scope: local`.
- **CIT-02** An `invariant` candidate MUST be probed on at least two distinct cases before adoption. A single-case win MUST NOT be reported as an invariant improvement.
- **CIT-03** A `local` candidate MUST NOT be promoted to a global default on the same evidence. Recording `promote_global: true` with `scope: local` is a violation, not a shortcut.
- **CIT-04** When two or more candidates are explored, at least one SHOULD be `invariant` and at least one SHOULD be `local`; a round covering only one scope MUST record why the other is inapplicable.

---

## 5. Contrast Vocabulary

A probe MUST be classified as exactly one of:

| Verdict | Meaning |
| :--- | :--- |
| `mitigated` | The targeted deficiency improved beyond the declared tolerance. |
| `unchanged` | Behavior moved within tolerance; the candidate did not address the deficiency. |
| `regressed` | The change made the targeted deficiency or an invariant worse. |
| `unproven` | No reference execution, no matched conditions, or no matching harness fingerprint. |

A `mitigated` claim without before/after measurements MUST downgrade to `unproven`. Contrast is evidence about behavior, never proof of correctness.

---

## 6. Anonymous Selection

When more than one candidate exists, adoption MUST be decided against **anonymized deliverables**: the selector sees the output, the request, and the source material, and MUST NOT see which harness produced which output. The selector MUST return one existing output and MUST NOT synthesize a new one. The mapping between anonymous identifiers and originating harnesses MUST be stored separately from the selection record. A candidate without a probe receipt MAY be chosen only when the record marks the result `unproven`.

---

## 7. Evidence-Gated Retention

- **CIT-05** An evidence entry MUST cite at least one contrast with a recorded fingerprint.
- **CIT-06** When evidence is insufficient, the loop MUST record that nothing was retained, with the reason. Silence is not permitted, and neither is a speculative entry.
- **CIT-07** Entries SHALL be organized per scope (project and domain), ordered, and read in that order, so a later entry may build on earlier retained evidence but not on later entries.

---

## 8. Preservation and Fallback

- **CIT-08** Preserving the current harness is a valid outcome. It MUST be recorded as `decision: preserved` with the observation that justified it.
- **CIT-09** A stage that fails MUST be recorded as a fallback with its reason. Silent continuation is prohibited: the next iteration must not believe a stage succeeded.

Forced change on every iteration is a defect, not diligence.

---

## 9. State Identity

- **CIT-10** Every journal entry for an adopting decision MUST record `harness_fingerprint` as defined by RFC-0009 HOP-11. A recorded fingerprint that does not match the audited manifest state is `fingerprint.stale` and MUST block adoption.

---

## 10. Reference Implementation

- Validator: [`skills/loop/scripts/openharness_verify.py`](../../skills/loop/scripts/openharness_verify.py)
- Selector: [`skills/loop/scripts/openharness_select.py`](../../skills/loop/scripts/openharness_select.py)
- State fingerprint: [`skills/loop/scripts/openharness_audit.py`](../../skills/loop/scripts/openharness_audit.py)
- Operating reference: [`skills/loop/references/contrastive-iteration.md`](../../skills/loop/references/contrastive-iteration.md)
- Regression suites: [`skills/loop/scripts/test_openharness_verify.py`](../../skills/loop/scripts/test_openharness_verify.py), [`skills/loop/scripts/test_openharness_select.py`](../../skills/loop/scripts/test_openharness_select.py)

---

## 11. Conformance

An implementation is conforming when it validates journal entries against CIT-01 through CIT-10, refuses an adopting decision that lacks scope, evidence, or rationale, refuses an `invariant` adoption with fewer than two cases, rejects stale fingerprints, and keeps every projection bounded at 2500 bytes. Anonymous selection is conforming when the selection record contains no originating harness names and the mapping is stored separately.

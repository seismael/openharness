# RFC-0009: OpenHarness Harness Optimization Protocol

- **RFC Number:** 0009
- **Title:** OpenHarness Harness Optimization Protocol
- **Status:** Proposed Standard (Working Draft)
- **Category:** Standards Track
- **Version:** 1.0.0-draft
- **Date:** October 2026
- **Authors:** Seismael & Antigravity Advanced Agentic Engineering Team

---

## Abstract

This document defines the normative requirements for measuring, proposing, probing, and adopting changes to an **agent harness**: the prompts, guardrails, memory, tool guidance, subagents, skills, scripts, and plugins that surround a model. A harness change is cheap to author and hard to falsify, so the protocol fixes three things the existing series leaves open: a declarative surface that can be audited without a model, two declared proposal scopes (`invariant` and `local`) with different evidence requirements, and a bounded, deterministic audit receipt that can be stored beside a decision. The protocol is host-agnostic: an adapter conforming to RFC-0005 declares how a given runtime binds the eight components.

---

## 1. Terminology & Conformance

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 [RFC 2119].

- **Harness:** The complete system around a frozen model that determines how it acts: instructions, guardrails, memory, tool guidance, subagents, skills, scripts, and plugins.
- **Component:** One of the eight harness surfaces, declared in a manifest with a kind, one or more path globs, and an always-on flag.
- **Harness Manifest:** The declarative `harness.manifest.v1` document describing the surface to be audited.
- **Audit Receipt:** The bounded `openharness.receipt.v1` projection produced by a conforming audit.
- **Probe:** One execution of an exact harness state against an evaluation, producing a receipt.
- **Proposal Scope:** The declared reach of a change: `invariant` (should hold everywhere) or `local` (fits a declared subset).

---

## 2. Motivation

Three failure modes recur whenever a harness is edited without a contract:

1. **Unmeasured surface.** The harness grows silently. Always-on text competes directly with the model's own output budget, so a harness can improve apparent coverage while reducing usable capability. No number is recorded, so the trade is invisible.
2. **Unreachable capability.** A skill or subagent is installed but never named by any always-on component, so it can never trigger. It is paid for in maintenance and returns nothing.
3. **Self-assessed adoption.** A change is adopted because its author describes it well. Without execution evidence for that exact harness state, the claim is an opinion about a proposal, not a measurement of a system.

A harness change also has a scope problem that ordinary feature work does not: a change that helps one task family can silently degrade every other one. Declaring scope before probing is what makes the difference visible.

---

## 3. Component Taxonomy

A conforming manifest MUST declare components using exactly these kinds:

| Kind | Normative meaning |
| :--- | :--- |
| `system_prompt` | Text that establishes role, objective, and standing constraints. |
| `guardrails` | Prohibitions, permission rules, and stop conditions. |
| `memory` | Durable notes, wiki index, and retained decisions. |
| `tool_guidance` | When and how to use available tools. |
| `subagents` | Delegated roles with their own context. |
| `skills` | On-demand workflows loaded by trigger. |
| `scripts` | Deterministic helpers invoked by the agent. |
| `plugins` | Middleware that acts inside the tool loop. |

An adapter conforming to RFC-0005 MAY bind a kind to any native mechanism; the taxonomy constrains the role, not the storage format. A harness need not populate every kind, but it MUST NOT invent kinds beyond this list.

---

## 4. Harness Manifest

A conforming implementation MUST accept `harness.manifest.v1` as defined in
[`schemas/openharness.schema.json`](schemas/openharness.schema.json), with these semantics:

1. `root` resolves component globs and defaults to `.` relative to the manifest.
2. `paths` are glob patterns; a component whose patterns match no file is a missing component.
3. `always_on: true` marks text loaded on every turn; it is the only text counted against the always-on budget.
4. `enabled: false` excludes a component from measurement entirely, including its findings.
5. `trigger_names` MAY pin the names that make a `skills` or `subagents` component reachable; when absent, an implementation SHOULD derive them from frontmatter metadata and the owning directory name.

---

## 5. Audit Invariants

- **HOP-01 Determinism.** An audit MUST be deterministic and MUST NOT call a model or network service. Two audits of an unchanged tree MUST produce byte-identical receipts.
- **HOP-02 Budget.** An audit MUST report estimated tokens per component, per always-on total, and per harness total, and MUST report a violation when a declared budget is exceeded.
- **HOP-03 Reachability.** An audit MUST report a `skills` or `subagents` component that no enabled always-on component references.
- **HOP-04 Duplication.** An audit MUST report a normalized instruction line repeated across two or more components.
- **HOP-05 Integrity.** An audit MUST report a declared path that matches no file, and a markdown link inside a component that resolves to nothing.
- **HOP-06 Bounded Output.** A receipt MUST NOT exceed 2500 bytes. When detail must be dropped to respect the cap, the verdict, totals, and counts MUST survive, and the receipt MUST declare `truncated` and the number of dropped findings.
- **HOP-07 Severity Contract.** Budget, reachability, missing-component, and unknown-kind findings are errors; duplication, stale links, and empty files are warnings. An implementation MUST exit non-zero when at least one error is present.
- **HOP-08 Scope Declaration.** Before evaluation, every harness change MUST be declared `invariant` or `local`. An `invariant` change MUST be probed on at least two distinct evaluation cases before adoption; a `local` change MUST NOT be promoted to a global default on the same evidence.
- **HOP-09 Probe Evidence.** No harness change may be adopted without a probe receipt for that exact harness state. Where the project declares a primary metric, that metric decides; behavioral comparison is a tiebreaker only.
- **HOP-10 Composition Budget.** A composed harness MUST be re-audited. A composition that exceeds the declared budget MUST be rejected rather than adopted.
- **HOP-11 State Fingerprint.** An audit MUST report a `fingerprint`: the SHA-256 digest of the sorted sequence of matched component paths and their content hashes. The fingerprint identifies the exact harness state a receipt describes. An adoption decision recorded against a different fingerprint MUST be treated as `fingerprint.stale` and MUST NOT be adopted on that evidence.

The series continues with [RFC-0010](rfc-0010-contrastive-iteration.md) (scope, contrast, anonymous adoption, evidence-gated retention), [RFC-0011](rfc-0011-iteration-telemetry.md) (recorded-only cost and gain projection), [RFC-0012](rfc-0012-declared-evaluation-cases.md) (declared cases and probe receipts), [RFC-0013](rfc-0013-capability-inventory.md) (inventory and gap analysis), [RFC-0014](rfc-0014-failure-taxonomy.md) (failure taxonomy), and [RFC-0015](rfc-0015-portable-policy-and-enforcement.md) (portable policy and adapter enforcement).

---

## 6. Adoption Procedure

```
1. Audit       -- current manifest -> receipt; store it beside the decision record
2. Declare     -- candidate change + scope (invariant | local)
3. Probe       -- execute the candidate on the required cases; capture receipts
4. Compose     -- only from probed candidates; re-audit the composition
5. Gate        -- primary metric first, invariant soundness second
6. Compound    -- adopt with receipts, or revert and record the failure mode
```

A clean audit is necessary, not sufficient: it establishes budget, reachability, and structural integrity, never that an instruction is obeyed or that a behavior transfers to another model or runtime.

---

## 7. Reference Implementation

The normative reference implementation of this RFC is maintained with the loop engine:

- Audit tool: [`skills/loop/scripts/openharness_audit.py`](../../skills/loop/scripts/openharness_audit.py)
- Operating reference: [`skills/loop/references/openharness.md`](../../skills/loop/references/openharness.md)
- Regression suite: [`skills/loop/scripts/test_openharness_audit.py`](../../skills/loop/scripts/test_openharness_audit.py)
- Conformance tests: [`tests/test_ohp_conformance.py`](../../tests/test_ohp_conformance.py)

---

## 8. Conformance

An implementation is conforming when it (a) validates `harness.manifest.v1`, (b) satisfies HOP-01 through HOP-07 and HOP-11 on the normative fixtures, (c) rejects an invalid manifest without emitting a partial receipt, and (d) respects the 2500-byte cap under adversarial input. HOP-08 through HOP-10 are procedural obligations on the loop engine and are evidenced by decision records rather than by a single process invocation.

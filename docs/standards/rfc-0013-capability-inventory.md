# RFC-0013: Capability Inventory and Gap Analysis

- **RFC Number:** 0013
- **Title:** Capability Inventory and Gap Analysis
- **Status:** Proposed Standard (Working Draft)
- **Category:** Standards Track
- **Version:** 1.0.0-draft
- **Date:** October 2026
- **Authors:** Seismael & Antigravity Advanced Agentic Engineering Team

---

## Abstract

This document defines how a harness reports **which capabilities it actually has** and **which declared requirements nothing satisfies**. The inventory is derived from the same declaration and the same file matching as the [RFC-0009](rfc-0009-openharness.md) audit, so the two can never disagree about what exists. Gap analysis is declared, not inferred: a requirement is a statement the project makes, and a gap is a requirement with a named reason why no present component meets it.

---

## 1. Terminology & Conformance

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 [RFC 2119].

- **Capability:** An enabled component of one of the eight harness kinds, together with the files it actually matches.
- **Inventory:** The per-kind count of declared, enabled, file-backed components and their estimated tokens.
- **Requirement:** A declared capability the project states it needs, with a kind and optionally a specific component.
- **Gap:** A requirement that no present, enabled, file-backed component satisfies, with a reason.
- **Blocking gap:** A gap in a requirement marked `required` (the default). Non-blocking gaps are reported but do not fail the inventory.

---

## 2. Motivation

Optimization without inventory fixes the wrong thing. An agent that cannot see what exists will propose adding a capability the harness already has, or will reinforce a component that matches no file and therefore never reaches a turn. Three specific failures follow:

1. **Phantom capability.** A component is declared in the manifest but its globs match nothing, so its tokens are zero and its guidance is unreachable.
2. **Silent absence.** A capability the project depends on is simply missing, and nothing in the harness says so.
3. **Prose-based belief.** The project believes it has a capability because an instruction mentions it, while no component implements it.

Inventory makes all three observable in one deterministic artifact.

---

## 3. Requirements Declaration

A requirements document names what the project needs:

```json
{
  "schema": "openharness.requirements.v1",
  "requirements": [
    {"id": "delegation", "kind": "subagents", "component": "verifier"},
    {"id": "extension-hooks", "kind": "plugins", "required": false},
    {"id": "knowledge-index", "kind": "memory", "requires_files": true}
  ]
}
```

- **INV-01** Every requirement MUST have a non-empty `id`, unique in the document, and a `kind` from the eight harness kinds.
- **INV-02** A requirement document MUST NOT contain unknown fields. An ignored requirement is a requirement the project believes it has.
- **INV-03** `component`, when present, names one component that MUST exist, MUST be of the declared kind, and MUST be enabled.
- **INV-04** `requires_files` defaults to `true`: a component whose globs match nothing does not satisfy a requirement.
- **INV-05** `required` defaults to `true`. A project that cannot name which requirements are optional has not decided what it needs.
- **INV-06** A requirement MUST describe a capability, never a specific mitigation. Requirements are stable; mitigations are iterations.

---

## 4. Inventory

- **INV-07** The inventory MUST use the audit's file matching. Duplicating glob resolution in a second implementation guarantees eventual disagreement.
- **INV-08** The inventory MUST report, per kind: declared components, enabled components, matched files, estimated tokens, and the enabled component ids.
- **INV-09** The inventory MUST report `kinds_missing`: kinds with no enabled component at all. This is a statement about the surface, not a verdict.
- **INV-10** Token figures are the audit's deterministic character-based estimate and MUST be presented as such. They compare component sizes; they do not predict billing.

---

## 5. Gap Analysis

- **INV-11** A gap MUST name a concrete reason: component not declared, component of another kind, component disabled, component matching no files, no enabled component of the kind, or no enabled component matching files.
- **INV-12** `coverage` MUST be reported with its denominator: the count of met requirements over the count of declared requirements, and `1.0` when nothing is declared. A coverage figure without a denominator is decoration.
- **INV-13** The inventory MUST exit `0` when no blocking gap exists, `1` when at least one does, and `2` when the manifest or the requirements cannot be read or are invalid.
- **INV-14** The projection MUST be deterministic and stay within 2500 bytes; gaps MAY be truncated, the counts and the verdict MUST survive.
- **INV-15** Closing a gap is an ordinary candidate. It MUST declare a scope and produce a probe like any other change; a gap is a reason to look, not evidence that a proposed fix works.

---

## 6. Reference Implementation

- Inventory: [`skills/loop/scripts/openharness_inventory.py`](../../skills/loop/scripts/openharness_inventory.py)
- Regression suite: [`skills/loop/scripts/test_openharness_inventory.py`](../../skills/loop/scripts/test_openharness_inventory.py)
- Manifest contract: [`schemas/openharness.schema.json`](schemas/openharness.schema.json)
- Operating reference: [`skills/loop/references/capability-and-failure.md`](../../skills/loop/references/capability-and-failure.md)

---

## 7. Conformance

An implementation is conforming when it derives the inventory from the audited manifest rather than from prose, rejects unknown requirement fields, treats file-less components as non-satisfying, reports every gap with a concrete reason, reports coverage with its denominator, distinguishes blocking from optional gaps in its exit code, and keeps its projection deterministic and bounded.

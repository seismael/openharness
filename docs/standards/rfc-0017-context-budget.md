# RFC-0017: Context Budget

- **RFC Number:** 0017
- **Title:** Context Budget
- **Status:** Proposed Standard (Working Draft)
- **Category:** Standards Track
- **Version:** 1.0.0-draft
- **Date:** October 2026
- **Authors:** Seismael & Antigravity Advanced Agentic Engineering Team

---

## Abstract

This document defines the **context budget**: a deterministic split of a declared
harness into the tokens every session pays, the tokens paid only when a component
is loaded, and the executable code that never enters a context window. It turns
the audit's single token total into an accountable structure with named levers
and declared-budget verdicts, so harness growth can be reviewed and gated like
any other engineering change.

---

## 1. Terminology & Conformance

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD",
"SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be
interpreted as described in BCP 14 [RFC 2119].

- **Layer:** One of `resident`, `loadable`, or `executable`.
- **Resident:** A component the host loads on every turn.
- **Loadable:** An enabled component that enters context only when activated.
- **Executable:** An enabled component that runs as code and does not consume
  context by existing.
- **Lever:** A named, quantified action that would change the budget.
- **Headroom:** Declared limit minus actual tokens; negative when exceeded.

---

## 2. Motivation

A single token total cannot answer the two questions that decide whether a
harness is affordable:

1. **What does every turn cost before the task starts?** Always-on
   instructions are paid on every request, so their cost is multiplied by the
   session length.
2. **What is recoverable?** A loadable skill or subagent is free until it is
   used; disabling or deferring it is a real budget lever. An executable script
   is not a context cost at all, yet a naive total counts it as if it were.

Reporting these layers separately makes the difference between "the harness is
large" and "the harness is expensive on every turn" explicit, and lets a team
choose the cheaper correction.

---

## 3. Layer Assignment

Every enabled component MUST be assigned to exactly one layer:

| Condition | Layer |
| :--- | :--- |
| `always_on` is `true` | `resident` |
| `kind` is `scripts` or `plugins` | `executable` |
| Otherwise | `loadable` |

Disabled components MUST be excluded from every total. Assignment MUST be a pure
function of the manifest and MUST NOT depend on host behavior, file names, or
execution order.

### 3.1 Token estimates

`tokens` MUST be the same deterministic estimate the audit uses:
`ceil(code_points / 4)`. It is a budget instrument, not a model tokenizer, and
MUST NOT be presented as billing data.

---

## 4. Receipt

The budget receipt is a JSON object:

```json
{
  "schema": "openharness.context.v1",
  "manifest": "example",
  "fingerprint": "<64 hex>",
  "tokens": { "resident": 511, "loadable": 2048, "executable": 0, "total": 2559 },
  "components": 7,
  "kinds": [
    { "kind": "system_prompt", "components": 1, "tokens": 511, "resident": 511 }
  ],
  "largest": [
    { "id": "skills", "kind": "skills", "layer": "loadable", "tokens": 1200, "share": 46 }
  ],
  "levers": [
    { "action": "defer", "component": "skills", "tokens": 1200, "share": 46 }
  ],
  "budget": {
    "always_on_tokens": { "limit": 4000, "actual": 511, "headroom": 3489, "ok": true }
  },
  "truncated": false,
  "ok": true
}
```

### 4.1 Requirements

- `schema` MUST be `openharness.context.v1`.
- `fingerprint` MUST equal the audit fingerprint for the same state.
- `tokens.total` MUST equal the sum of the three layers.
- `kinds` MUST be sorted by kind and MUST contain one row per enabled kind.
- `largest` MUST be ordered by descending tokens, then by component id, and MUST
  NOT contain zero-token components.
- `levers` MUST contain one record per non-zero enabled component, ordered like
  `largest`. `action` MUST be `trim` for `resident` components and `defer`
  otherwise.
- `share` MUST be the integer percentage of `tokens.total`, rounded half away
  from zero, and MUST be `0` when the total is `0`.
- `budget` MUST contain an entry only for a limit declared in the manifest.
  `headroom` MUST be `limit - actual` and MAY be negative.
- `ok` MUST be `true` only when every declared budget entry is within its limit.
- The document MUST serialize canonically (sorted keys, no whitespace) and MUST
  NOT exceed 2500 bytes.

---

## 5. Verdict

`context` MUST exit `0` on a valid measurement, `2` on invalid input, and `1`
when check mode is requested and a declared budget is exceeded. Without check
mode the command is informational and MUST exit `0` even when `ok` is `false`,
because a measurement is not a failure. The receipt `ok` field always reports the
budget verdict, so a caller never needs to parse prose.

A text projection MAY be offered. It MUST be deterministic, MUST derive only
from the receipt, and MUST remain within the same byte cap.

---

## 6. Determinism

The budget MUST NOT read the clock, the environment, the network, or a model.
Given identical bytes it MUST produce identical output on Linux, macOS, and
Windows. It MUST reuse the audit's measurement pass rather than walking or
hashing the tree again, so the fingerprint, per-component tokens, and layer
totals cannot disagree.

---

## 7. Conformance

An implementation conforms when it can:

1. Assign each enabled component to exactly one layer by the table in Section 3.
2. Reproduce the same receipt byte-for-byte from an unchanged tree.
3. Show `tokens.total` equal to the sum of the layers and to the audit total.
4. Report headroom, including a negative value, for each declared limit.
5. Exit `0`, `1`, and `2` as specified.
6. Keep the receipt within 2500 bytes while preserving the verdict.

The reference implementation proves each item in `tests/test_openharness_units.py`
and freezes the output in `tests/golden/`.

---

## 8. Security Considerations

- The receipt is evidence of declared cost, not of runtime usage. Hosts measure
  actual consumption; this document measures the surface they are given.
- Token estimates are heuristic. A budget MUST be set with margin and reviewed
  when the estimate changes.
- The budget MUST NOT be used to justify deleting guardrails. A smaller harness
  that omits a required invariant is a regression, and the inventory declares
  those requirements.

---

## 9. References

- [RFC-0004](rfc-0004-streaming-output-projection.md): token economics.
- [RFC-0009](rfc-0009-openharness.md): harness surface, audit, and token estimates.
- [RFC-0013](rfc-0013-capability-inventory.md): required capabilities a budget must not remove.
- [RFC-0016](rfc-0016-harness-lockfile-and-drift-plan.md): fingerprint the budget reuses.
- [context.schema.json](schemas/context.schema.json): machine-readable contract.

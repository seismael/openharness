# RFC-0011: Iteration Telemetry

- **RFC Number:** 0011
- **Title:** Iteration Telemetry
- **Status:** Proposed Standard (Working Draft)
- **Category:** Standards Track
- **Version:** 1.0.0-draft
- **Date:** October 2026
- **Authors:** Seismael & Antigravity Advanced Agentic Engineering Team

---

## Abstract

This document defines how a loop reports what its own history cost and what that cost bought. Telemetry is a **projection of recorded journal fields**, not a new measurement system: it aggregates only what an iteration actually wrote, refuses to estimate what it did not measure, and never nets a regression against a gain. The output is one bounded object so a caller can read the state of an optimization effort in a single tool result.

---

## 1. Terminology & Conformance

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 [RFC 2119].

- **Iteration record:** One line of `journal.jsonl`, as defined by [`journal.schema.json`](schemas/journal.schema.json).
- **Measured delta:** `metric_after - metric_before`, present only when both are numbers.
- **Signed gain:** The measured delta oriented by the metric's declared direction: unchanged for `maximize`, negated for `minimize`.
- **Gain total:** The sum of signed gains strictly above tolerance. Regressions are never subtracted from it.
- **Regression total:** The sum of signed gains strictly below negative tolerance. Reported separately.
- **Costed iteration:** An iteration whose record carries at least one numeric `cost` field.
- **Telemetry projection:** The single bounded object this specification defines.

---

## 2. Motivation

A loop that reports only its wins is indistinguishable from a loop that reports nothing. Three specific distortions recur:

1. **Cost blindness.** Iterations are compared on outcome alone, so an equal outcome at ten times the cost looks equal.
2. **Netting.** A large win and a large regression are summed into a comfortable middle, hiding both.
3. **Imputed measurement.** When cost is missing, the reporter substitutes an estimate from text length and presents it as measurement. The estimate then becomes a premise.

Telemetry exists to make the first two visible and the third impossible.

---

## 3. Measurement Principles

- **TEL-01** A projection MUST aggregate recorded fields only. It MUST NOT derive cost from content length, call counts it did not observe, or any character-based token approximation.
- **TEL-02** A missing value MUST be reported as missing. A projection MUST NOT emit `0` for a cost field that no iteration recorded. Zero is a measurement; absence is not.
- **TEL-03** Gains and regressions MUST be reported in separate totals. A projection MUST NOT publish a net figure.
- **TEL-04** A signed gain MUST be computed with the metric's declared `direction`. Reversing direction silently inverts every verdict downstream, so the direction MUST be echoed in the projection.
- **TEL-05** `cost_per_gain` MUST name its numerator unit and MUST be absent when the gain total is not positive. Division by zero and division by a non-improvement are both meaningless.
- **TEL-06** Every numeric field MUST be rounded to a fixed precision before serialization, so the same journal always yields byte-identical output.
- **TEL-07** The projection MUST stay within 2500 bytes. Detail — per-deficiency rows first — MAY be dropped, but the verdict fields, the iteration count, the decision and contrast tallies, the cost totals, and the gain total MUST survive truncation, and the object MUST be marked `truncated`.

---

## 4. Projection Fields

| Field | Meaning |
| :--- | :--- |
| `schema` | `openharness.telemetry.v1` |
| `direction` | `maximize` or `minimize`, echoed from the request |
| `tolerance` | Delta treated as no movement |
| `iterations` | Records with a valid integer `iteration` |
| `invalid` | Records rejected for a missing or non-integer `iteration` |
| `decisions` | Count per decision, with `unclassified` for unknown values |
| `contrasts` | Count per recorded contrast, with `unclassified` for unknown values |
| `adoption_rate` | Adopting decisions divided by all records |
| `mitigation_rate` | `mitigated` contrasts divided by records that carry a measured delta |
| `evidence_coverage` | Adopting decisions with an `evidence_ref`, divided by adopting decisions |
| `costed_iterations` | Records carrying at least one numeric cost field |
| `cost` | Sum per recorded cost key; keys nobody recorded are absent |
| `tokens_total` | `tokens_in + tokens_out`, present only through `cost` |
| `measured` | Records with a usable measured delta |
| `gain_total` | Sum of positive signed gains |
| `regression_total` | Sum of negative signed gains, negative by construction |
| `cost_per_gain` | `{usd, tokens}` per unit of gain, or `null` |
| `deficiencies` | Per named deficiency: iterations, adopted, mitigated, gain |
| `truncated` | Whether detail was dropped to fit the byte budget |

`adoption_rate`, `mitigation_rate`, and `evidence_coverage` are rates over their own denominators, which are reported alongside them as `iterations`, `measured`, and `adopting` counts. A rate without its denominator is not evidence.

---

## 5. Reading the Projection

- **A high adoption rate with low evidence coverage** means the loop is changing the harness faster than it is recording why. Stop and repair the record before the next change.
- **A positive gain total with a large regression total** means the changes are not uniformly better; the scopes are probably too broad.
- **A falling cost per gain with a stable gain total** is the only shape that indicates genuine efficiency improvement.
- **Costed iterations far below iterations** means the cost claim is unsupported. The loop SHOULD record cost for every iteration it claims was measured, even when the cost is an observed step count rather than a bill.

---

## 6. Reference Implementation

- Projection: [`skills/loop/scripts/openharness_telemetry.py`](../../skills/loop/scripts/openharness_telemetry.py)
- Regression suite: [`skills/loop/scripts/test_openharness_telemetry.py`](../../skills/loop/scripts/test_openharness_telemetry.py)
- Record contract: [`schemas/journal.schema.json`](schemas/journal.schema.json)
- Operating reference: [`skills/loop/references/measurement.md`](../../skills/loop/references/measurement.md)

---

## 7. Conformance

An implementation is conforming when it reads iteration records without inventing fields, reports gains and regressions separately, omits unrecorded cost keys, withholds `cost_per_gain` unless gain is positive, echoes the metric direction, keeps its output deterministic and within 2500 bytes, and never substitutes a character-based token estimate for a measured cost.

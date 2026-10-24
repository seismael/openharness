# RFC-0014: Failure Taxonomy

- **RFC Number:** 0014
- **Title:** Failure Taxonomy
- **Status:** Proposed Standard (Working Draft)
- **Category:** Standards Track
- **Version:** 1.0.0-draft
- **Date:** October 2026
- **Authors:** Seismael & Antigravity Advanced Agentic Engineering Team

---

## Abstract

This document defines a closed vocabulary for **why an iteration failed**, and the aggregation that turns that vocabulary into evidence about the harness. A failure class is a diagnosis of cause, not a description of a symptom. The set is closed so recurrence can be counted, and recurrence is what distinguishes an incident from a harness defect.

---

## 1. Terminology & Conformance

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 [RFC 2119].

- **Failure:** A recorded iteration that did not achieve its declared effect.
- **Failure class:** One value from the closed taxonomy in §3, describing the cause.
- **Recurrence:** The same class appearing `n` or more times, where `n` defaults to 2.
- **Diagnosis note:** The `detail` observation that supports the chosen class.

---

## 2. Motivation

Two habits make failure data useless:

1. **Free-text causes.** Each failure is described in its own words, so nothing aggregates and the same defect is diagnosed three ways.
2. **Symptom labelling.** A test failure is labelled `test-failure`, which is true of every failure and therefore distinguishes none.

A closed, cause-oriented taxonomy makes recurrence visible. That is the whole point: the second occurrence of a class is a statement about the harness.

---

## 3. Taxonomy

| Class | Definition | Typical evidence | Harness implication |
| :--- | :--- | :--- | :--- |
| `tool-misuse` | The right tool was chosen and called wrongly. | Invalid argument, wrong flag, ignored exit code. | Tool guidance is ambiguous or absent. |
| `context-loss` | Required information was available and not in context when needed. | Re-reading the same file, forgetting a constraint, contradicting an earlier decision. | Retrieval, memory, or projection budget. |
| `wrong-premise` | The iteration was correct given a false belief. | A falsified assumption about behavior, ownership, or prior state. | Missing or unrevisited evidence entries. |
| `dead-end` | The approach was valid but could not terminate within budget. | Repeated widening search, no falsifier, no stopping rule. | Dispatch policy or saturation rule. |
| `unsafe-action` | The iteration touched something it should not have. | Out-of-scope write, unapproved destructive command. | Guardrails or policy rules. |
| `spec-ambiguity` | The target did not determine what counted as success. | Two readings of the request, both defensible. | Profile predicate or completion criteria. |
| `environment` | The host, toolchain, or network prevented execution. | Missing binary, denied permission, unavailable service. | Environment manifest or setup step. |
| `data-quality` | The input was malformed, stale, or incomplete. | Corrupt fixture, truncated output, wrong revision. | Validation step before evaluation. |
| `unclassified` | No diagnosis was reached. | A failure noted without a cause. | The loop stopped diagnosing too early. |

- **FAI-01** A recorded failure class MUST be exactly one of the nine values above. No free-text class is permitted.
- **FAI-02** A class MUST name a cause. A class that would be true of every failure carries no information.
- **FAI-03** `unclassified` MUST NOT be used when a cause is identifiable. Reaching for it is a signal to diagnose, not to record.
- **FAI-04** An `unclassified` failure SHOULD carry a diagnosis note. Without one, the record cannot be improved later.
- **FAI-05** An unknown or missing class MUST be aggregated as `unclassified` and reported as a contract violation. It MUST NOT be dropped, because dropping it hides the defect in the record itself.

---

## 4. Aggregation

- **FAI-06** The projection MUST report: total iterations, total failures, the failure rate, a count per observed class, and the class list of the taxonomy.
- **FAI-07** A class reaching the recurrence threshold MUST be reported as a **harness gap candidate**, not as an incident. The finding names the class and its count.
- **FAI-08** `unclassified` MUST NOT be reported as a recurring gap. Recurring ignorance is a process failure, not a class of defect.
- **FAI-09** Recurrence defaults to 2 and MUST be at least 2. A threshold of 1 would classify every failure as a harness defect and make the distinction meaningless.
- **FAI-10** Failures MUST NOT be netted against adoptions. A loop that adopted ten changes and failed ten times has a failure rate of one half, whatever its net outcome.
- **FAI-11** A class MUST NOT be reassigned after the fact to avoid recurrence. Reclassification is a new observation with its own record.
- **FAI-12** The projection MUST stay within 2500 bytes and MUST be deterministic. Findings MAY be truncated; counts and the verdict MUST survive.

---

## 5. Using the Taxonomy

- **A recurring `context-loss`** points at memory and budget, not at the agent's attention.
- **A recurring `wrong-premise`** points at evidence retention: the loop is reasoning from beliefs it never checked.
- **A recurring `tool-misuse`** points at tool guidance, and the fix is usually shorter, not longer.
- **A recurring `dead-end`** points at the stopping rule: the loop needs a saturation condition, not more effort.
- **`spec-ambiguity` once** is normal. **`spec-ambiguity` twice on the same target** means the profile is underspecified, and no candidate change will fix it.

---

## 6. Reference Implementation

- Aggregator: [`skills/loop/scripts/openharness_failures.py`](../../skills/loop/scripts/openharness_failures.py)
- Regression suite: [`skills/loop/scripts/test_openharness_failures.py`](../../skills/loop/scripts/test_openharness_failures.py)
- Record contract: [`schemas/journal.schema.json`](schemas/journal.schema.json)
- Operating reference: [`skills/loop/references/capability-and-failure.md`](../../skills/loop/references/capability-and-failure.md)

---

## 7. Conformance

An implementation is conforming when it accepts only the nine classes, aggregates an unknown class as `unclassified` while reporting a violation, requires a threshold of at least two for recurrence, reports recurring classes as harness gap candidates, excludes `unclassified` from recurrence, reports failures separately from adoptions, and emits a deterministic bounded projection.

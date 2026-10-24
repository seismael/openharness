# RFC-0012: Declared Evaluation Cases

- **RFC Number:** 0012
- **Title:** Declared Evaluation Cases
- **Status:** Proposed Standard (Working Draft)
- **Category:** Standards Track
- **Version:** 1.0.0-draft
- **Date:** October 2026
- **Authors:** Seismael & Antigravity Advanced Agentic Engineering Team

---

## Abstract

This document defines how a loop declares the evaluation inputs it optimizes against, and how a runner executes them deterministically. A **case** binds one identifier to one command and one set of observable expectations. The runner is a predicate evaluator: it reports whether the declared expectations held. It does not judge output quality, does not call a model, and does not claim a measurement it did not take. Declared cases are what make the reference execution in [RFC-0010](rfc-0010-contrastive-iteration.md) reproducible rather than remembered.

---

## 1. Terminology & Conformance

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 [RFC 2119].

- **Case:** One declared evaluation input: an id, a command, and optional expectations.
- **Case set:** The ordered collection of cases an iteration is probed against.
- **Predicate:** An observable condition on a completed command: exit code, output substring, or artifact existence.
- **Probe receipt:** The runner's record of one execution of a case set against one harness state.
- **Dry run:** Validation of the declaration without executing any command.
- **Matched conditions:** The same case set, the same working directory state, and the same harness fingerprint.

---

## 2. Motivation

A loop without declared cases measures whatever its author happened to run. Three consequences follow:

1. **Irreproducible references.** The "before" run cannot be repeated, so no contrast is a comparison.
2. **Drifting evaluation.** The test suite used to accept a change is quietly different from the one used to reject the last one.
3. **Self-assessment.** The agent that produced an output also decides whether the output is good, with no observable predicate in between.

Declared cases fix all three by moving evaluation into a small deterministic artifact.

---

## 3. Case Declaration

A case is a JSON object:

```json
{
  "id": "unit",
  "description": "Fast suite must stay green",
  "command": "python -m pytest -q",
  "expect": {"exit_code": 0, "stdout_contains": "passed"},
  "timeout_s": 300,
  "budget_tokens": 4000
}
```

- **CAS-01** Every case MUST have a non-empty `id`, unique within its set, and a non-empty `command`.
- **CAS-02** A declaration MUST NOT contain unknown fields. An unrecognized field is an error, not an extension point, because a silently ignored expectation is a false pass.
- **CAS-03** `expect` MUST be limited to `exit_code` (integer), `stdout_contains` (string), and `artifact` (path). A predicate outside this set MUST be rejected.
- **CAS-04** `timeout_s` MUST default to 120 and MUST be an integer in `1..3600`. A case that exceeds it is `timeout`, which is distinct from `fail`.
- **CAS-05** `budget_tokens`, when present, is a **declared** ceiling for the invocation, not a measurement. A runner MUST NOT report token consumption it did not observe.
- **CAS-06** Declarations MUST be loadable without a YAML parser. The canonical carriers are a JSON case document and the `cases` array of the profile seam; both describe the same objects.
- **CAS-07** An `artifact` predicate MUST be resolved relative to the declared working directory.

---

## 4. Execution

- **CAS-08** A runner MUST execute each case in the declared working directory and MUST evaluate predicates on the combined output of stdout and stderr.
- **CAS-09** A runner MUST stop evaluating a case after its first failed predicate and MUST record which predicate failed in human-readable form.
- **CAS-10** A case set runs to completion even when an earlier case fails. Aborting early hides the shape of the regression.
- **CAS-11** A case whose process cannot be started is `error`, distinct from `fail` and `timeout`.
- **CAS-12** Exit codes MUST be `0` when every case passed, `1` when any case failed, timed out, or errored, and `2` when the declaration, the case id selection, or the working directory is invalid. A declaration error MUST NOT execute anything.
- **CAS-13** `--dry-run` MUST validate and report the selected cases without executing a command.
- **CAS-14** When a fingerprint is supplied, the probe receipt MUST record it, so the receipt is usable as the evidence reference required by RFC-0010 CIT-05.
- **CAS-15** The stdout projection MUST stay within 2500 bytes and MUST be byte-identical for identical inputs. Per-case results MAY be dropped; totals and the verdict MUST survive.

---

## 5. Matched Conditions

- **CAS-16** A contrast between two probe receipts is valid only when the case set, the working directory state, and the harness fingerprint match. A difference in any of the three makes the result `unproven`, not `mitigated` or `regressed`.
- **CAS-17** A case set used for an `invariant` claim MUST contain at least two distinct cases, per RFC-0010 CIT-02. Cases SHOULD be chosen to disagree: two cases that can only pass together add no discriminating power.
- **CAS-18** A case set SHOULD be extended when a previously unobserved failure class is discovered, so the class becomes permanently observable. Removing a case requires a recorded reason, because removal destroys the comparability of every earlier receipt.

---

## 6. Reference Implementation

- Runner: [`skills/loop/scripts/openharness_cases.py`](../../skills/loop/scripts/openharness_cases.py)
- Regression suite: [`skills/loop/scripts/test_openharness_cases.py`](../../skills/loop/scripts/test_openharness_cases.py)
- Declaration schema: [`schemas/cases.schema.json`](schemas/cases.schema.json)
- Profile field: [`schemas/profile.schema.json`](schemas/profile.schema.json)
- Operating reference: [`skills/loop/references/measurement.md`](../../skills/loop/references/measurement.md)

---

## 7. Conformance

An implementation is conforming when it validates declarations before executing, rejects unknown case and predicate fields, evaluates only exit code, output text, and artifact existence, distinguishes `fail` from `timeout` and `error`, stamps the harness fingerprint onto the receipt, refuses to run on a declaration error, keeps `--dry-run` side-effect free, and emits a deterministic projection within 2500 bytes.

# Capability inventory and failure taxonomy

Two questions before an optimization run, and two after it: **what does the harness
actually have**, and **why did the last attempts fail**. RFC-0013 and RFC-0014 are the
normative contracts; this is how to use them.

## Inventory the surface

Derive the inventory from the audited manifest, never from prose:

```sh
python "scripts/openharness_inventory.py" --manifest harness.json --requirements requirements.json
```

Declare what the project needs, not what it wishes it had:

```json
{
  "schema": "openharness.requirements.v1",
  "requirements": [
    {"id": "delegation", "kind": "subagents", "component": "verifier"},
    {"id": "extension-hooks", "kind": "plugins", "required": false},
    {"id": "knowledge-index", "kind": "memory"}
  ]
}
```

A requirement names a kind, and optionally one component. A component that is disabled, of
another kind, or matching no files is a gap. `requires_files` defaults to true, because a
declared component with no files reaches no turn.

Read the result:

- `kinds_missing` — whole kinds with no enabled component. A statement, not a verdict.
- `gaps` — each with a concrete reason, and whether it blocks.
- `coverage` — met over declared, always with its denominator.

Exit `0` means no blocking gap, `1` means at least one, `2` means the manifest or the
requirements are unusable. Closing a gap is a normal candidate: declare a scope, probe it.

## Classify the failures

Every failed iteration records one class from the closed set:

| Class | The cause is | The harness fix is usually |
| :--- | :--- | :--- |
| `tool-misuse` | wrong call or ignored result | shorter tool guidance |
| `context-loss` | needed information not in context | retrieval, memory, projection budget |
| `wrong-premise` | a false belief about behavior or state | evidence retention |
| `dead-end` | valid approach, no stopping rule | dispatch or saturation policy |
| `unsafe-action` | touched what it should not | guardrails or policy rules |
| `spec-ambiguity` | success was never determined | profile predicate |
| `environment` | host, toolchain, or network blocked it | environment manifest |
| `data-quality` | input malformed, stale, or incomplete | validation before evaluation |
| `unclassified` | no diagnosis | diagnose before recording |

```json
{"ts": "2026-10-24T00:00:00Z", "iteration": 7, "front": "debug",
 "hypothesis": "The retry loop is the source of the double write",
 "decision": "rejected", "failure": {"class": "wrong-premise", "detail": "the second write came from the caller"}}
```

```sh
python "scripts/openharness_failures.py" --journal .agents/loop/journal.jsonl
```

A class reaching the recurrence threshold (2 by default) is reported as a **harness gap
candidate**, not an incident. That is the whole value: one occurrence is bad luck, the same
class twice is a defect in the harness. `unclassified` is excluded from recurrence, because
recurring ignorance is a process failure and needs diagnosing, not counting.

Do not reassign a class to avoid a recurrence flag. Reclassification is a new observation and
gets its own record.

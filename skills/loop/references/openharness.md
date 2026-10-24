# Harness optimization

The harness is the system around the model: instructions, guardrails, memory, tool
guidance, subagents, skills, scripts, and plugins. It is the part a loop iteration can
actually change without touching model weights, so it must be measured before it is
edited and proven before it is adopted. RFC-0009 defines that contract; this reference
is how the loop applies it.

## 1. Audit before proposing

Declare the surface once, in `harness.json` at the project root:

```json
{
  "schema": "harness.manifest.v1",
  "name": "project-harness",
  "budget": { "always_on_tokens": 24000, "total_tokens": 60000 },
  "components": [
    { "id": "prompt", "kind": "system_prompt", "paths": ["AGENTS.md"], "always_on": true },
    { "id": "guards", "kind": "guardrails", "paths": [".opencode/rules/*.md"], "always_on": true },
    { "id": "skills", "kind": "skills", "paths": ["skills/*/SKILL.md"] },
    { "id": "agents", "kind": "subagents", "paths": [".opencode/agent/*.md"] }
  ]
}
```

Run the deterministic audit:

```sh
openharness audit --manifest harness.json
```

Exit `0` means no error-severity finding, `1` means at least one, `2` means the manifest
itself is invalid. The receipt is capped at 2500 bytes and reports totals, per-component
token estimates, and findings. It never calls a model and never writes, so two runs on an
unchanged tree are byte-identical. In a skill-only installation without the console
script, use `python <loop-skill-dir>/scripts/openharness_cli.py audit --manifest harness.json`.

## 1a. Lock the accepted state

Once the surface is clean, record it and gate later edits:

```sh
openharness lock
openharness plan --check
```

`harness.lock` stores the fingerprint, every file's SHA-256 and token estimate, the
budget, and the hashes of the policy, cases, and requirements declarations. `plan
--check` exits `1` on any difference and attributes it to a file or declaration, so a
review sees the harness change rather than a regenerated artifact. Re-lock only as part
of an intentional change, and commit the lock with that change.

## 2. Two proposal scopes

Every harness change MUST be declared before it is tested:

- `invariant` — should hold for any task in this project. It must be probed on at least
  two different cases before adoption; a single-case win is not evidence.
- `local` — fits one task family or one runtime condition. It may be adopted for that
  scope only, and MUST NOT be promoted to a global default on the strength of the same
  probe.

Never present a `local` win as a general improvement, and never average an `invariant`
change over cases where it silently regressed a required invariant.

## 3. Probe receipts

A candidate may not be adopted on the strength of its own description. Each candidate
needs at least one execution receipt: the evaluation actually run on that exact harness
state, with the metric and the invariant result recorded. When a required metric exists,
the metric decides; behavioral comparison is a tiebreaker for changes whose effect is not
expressible as a scalar, not a replacement for the metric.

Record the state identity with the receipt:

```sh
openharness audit --manifest harness.json --fingerprint-only
```

The fingerprint is a SHA-256 digest over the sorted component paths and contents. A receipt
for one fingerprint says nothing about a different harness state; recording an adoption
against a stale one is a contract violation, not a rounding error.

## 4. Composition and budget

Compose only from probed candidates. Reject a composition that pushes always-on text past
the declared budget: always-on tokens compete directly with the agent's own output budget,
so a harness that wins on coverage and loses on usable output has not improved. Re-audit
after composition; a clean compose is still a new harness state.

## 5. Where this sits in the loop

| Loop phase | Harness work |
| :--- | :--- |
| Orient | re-audit if any harness file changed since the last receipt |
| Dispatch | treat a budget, orphan, duplication, or stale-link finding as a candidate source |
| Candidate | one scoped edit, declared `invariant` or `local`, snapshot before evaluation |
| Evaluate + Gate | metric gate first, invariant gate second, probe receipt recorded |
| Compound | adopt or revert; append the receipt digest to the decision record |

Orphan findings deserve attention on their own: a skill or subagent that no always-on
component ever mentions is loaded into the harness but can never trigger, which costs
maintenance and buys nothing.

## 6. The rest of the mechanism set

The audit is the first of the deterministic commands. Each is local, bounded at 2500
bytes, and answers one question:

| Command | Question | Contract |
| :--- | :--- | :--- |
| `openharness audit` | What is the surface, and does it hold together? | RFC-0009 |
| `openharness verify` | Is this journal entry coherent? | RFC-0010 |
| `openharness select` | Which output wins, without knowing its author? | RFC-0010 |
| `openharness cases` | Did the declared cases behave as expected? | RFC-0012 |
| `openharness telemetry` | What did the effort cost and what did it buy? | RFC-0011 |
| `openharness inventory` | Which declared capabilities actually exist? | RFC-0013 |
| `openharness failures` | Why did iterations fail, and is a class recurring? | RFC-0014 |
| `openharness policy` | Is this action allowed, denied, or undecided? | RFC-0015 |
| `openharness lock` | What state did we accept? | RFC-0016 |
| `openharness plan` | What changed since we accepted it? | RFC-0016 |

The historical `openharness_*.py` script paths remain as compatibility shims and print
exactly what the matching subcommand prints.

Read [contrastive iteration](contrastive-iteration.md) for the adoption contract,
[measurement](measurement.md) for cases and cost, and
[capability and failure](capability-and-failure.md) for inventory and taxonomy. Use the
audit before proposing, the cases before claiming, and the taxonomy before diagnosing.

## 7. Scope limits

The audit measures declared text and declared structure. It cannot prove that an
instruction is obeyed, that a permission is enforced, or that a behavior transfers to
another model or runtime. Those remain execution questions, answered by evidence, not by
a clean receipt.

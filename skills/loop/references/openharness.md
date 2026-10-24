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
python skills/loop/scripts/openharness_audit.py --manifest harness.json
```

Exit `0` means no error-severity finding, `1` means at least one, `2` means the manifest
itself is invalid. The receipt is capped at 2500 bytes and reports totals, per-component
token estimates, and findings. It never calls a model and never writes, so two runs on an
unchanged tree are byte-identical.

## 2. Two proposal scopes

Every harness change MUST be declared before it is tested:

- `invariant` — should hold for any task in this project. It must be probed on at least
  two different cells before adoption; a single-cell win is not evidence.
- `local` — fits one task family or one runtime condition. It may be adopted for that
  scope only, and MUST NOT be promoted to a global default on the strength of the same
  probe.

Never present a `local` win as a general improvement, and never average an `invariant`
change over cells where it silently regressed a required invariant.

## 3. Probe receipts

A candidate may not be adopted on the strength of its own description. Each candidate
needs at least one execution receipt: the evaluation actually run on that exact harness
state, with the metric and the invariant result recorded. When a required metric exists,
the metric decides; behavioral comparison is a tiebreaker for changes whose effect is not
expressible as a scalar, not a replacement for the metric.

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

## 6. Scope limits

The audit measures declared text and declared structure. It cannot prove that an
instruction is obeyed, that a permission is enforced, or that a behavior transfers to
another model or runtime. Those remain execution questions, answered by evidence, not by
a clean receipt.

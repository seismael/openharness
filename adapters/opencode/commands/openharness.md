---
description: Audit the declared harness surface, then gate one scoped harness change
---

Operate the OpenHarness harness-optimization protocol (OHP RFC-0009) on $ARGUMENTS.

Load the `loop` skill and read its `references/openharness.md`; follow it exactly. Do not
invent a variant of it.

1. **Locate the manifest.** Expect `harness.json` at the project root. If it is absent,
   draft one with the 8 declared kinds that actually exist here — `system_prompt`,
   `guardrails`, `memory`, `tool_guidance`, `subagents`, `skills`, `scripts`, `plugins` —
   and set `always_on: true` only for text loaded on every turn. Show the draft before
   relying on it.
2. **Audit.** Run
   `python "<loop-skill-dir>/scripts/openharness_audit.py" --manifest harness.json`,
   resolving `<loop-skill-dir>` to wherever the `loop` skill is installed (for example
   `.opencode/skills/loop` or `~/.config/opencode/skills/loop`).
   Exit `0` means no error-severity finding, `1` means at least one, `2` means the manifest
   is invalid. Report the receipt totals and each finding with its code. Never weaken the
   audit, remove a component, or raise a budget to make a finding disappear.
3. **Propose at most one change** when asked to improve the surface. Declare its scope:
   `invariant` (must hold for every task, needs a probe on at least two different cells) or
   `local` (valid only for the declared subset, never promoted to a global default).
4. **Gate.** No adoption without a probe receipt for that exact harness state. Primary
   metric first, invariant soundness second. Re-audit any composition and reject it if it
   exceeds the declared budget.
5. **Report** the receipt digest, the scope, the probe evidence, and what remains unproven.
   A clean audit never proves that an instruction is obeyed or that behavior transfers to
   another model or runtime.

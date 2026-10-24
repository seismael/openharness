---
description: Audit the declared harness surface, then gate one scoped harness change
---

Operate the OpenHarness harness-optimization protocol (OHP RFC-0009 through RFC-0015) on
$ARGUMENTS.

Load the `loop` skill and read its `references/openharness.md`,
`references/contrastive-iteration.md`, `references/measurement.md`, and
`references/capability-and-failure.md`; follow them exactly. Do not invent a variant.

Read the first word of `$ARGUMENTS` as the sub-mode. With no sub-mode, run steps 1–6 below.

| Sub-mode | Action |
| :--- | :--- |
| `audit` | Steps 1–6. |
| `inventory [requirements.json]` | `openharness_inventory.py --manifest harness.json [--requirements ...]`. Report `kinds_missing`, each gap with its reason, and `coverage` with its denominator. |
| `cases <cases.json>` | `openharness_cases.py --cases <cases.json> --dry-run`, then run it. Never widen a predicate to make a case pass. |
| `measure` | `openharness_telemetry.py --journal .agents/loop/journal.jsonl`. Report gain and regression separately; `cost_per_gain` only when gain is positive. |
| `failures` | `openharness_failures.py --journal .agents/loop/journal.jsonl`. A class is a cause; a recurring class is a harness gap, not an incident. |
| `policy --tool/--path/--command ...` | `openharness_policy.py --policy policy.json ...`. `deny` is terminal; `ask` blocks autonomous continuation until answered. |
| `select <dir>` | `openharness_select.py --candidates <dir>`. Read only the anonymized selection, never `mapping.json`, before choosing. |
| `verify` | `openharness_verify.py --journal .agents/loop/journal.jsonl --fingerprint <sha256>`. Exit `1` blocks adoption. |

Every script lives in the installed `loop` skill's `scripts/` directory. Exit codes are
uniform: `0` clean, `1` contract violation or failed predicate, `2` unusable input, `3` ask.

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
   `invariant` (must hold for every task, needs a probe on at least two different cases) or
   `local` (valid only for the declared subset, never promoted to a global default).
4. **Gate.** No adoption without a probe receipt for that exact harness state. Primary
   metric first, invariant soundness second. Re-audit any composition and reject it if it
   exceeds the declared budget. Validate the journal entry with `openharness_verify.py`;
   `contrast.inconsistent` is a warning that the deficiency was not what moved.
5. **Report** the receipt digest, the scope, the probe evidence, and what remains unproven.
   A clean audit never proves that an instruction is obeyed or that behavior transfers to
   another model or runtime.
6. **Record the cost.** Put the observed cost fields in the journal entry. When no cost was
   observed, omit them; never estimate. Preserve the current harness with
   `decision: preserved` when that is the supported outcome.


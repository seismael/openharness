# Schemas and declarations

OpenHarness uses JSON, not YAML, for every declaration it evaluates. That keeps the runtime standard-library only and makes the documents directly testable. Normative JSON Schemas live in [`docs/standards/schemas/`](standards/schemas/).

## `harness.json` — the surface

Schema: `harness.manifest.v1` · [openharness.schema.json](standards/schemas/openharness.schema.json)

```json
{
  "schema": "harness.manifest.v1",
  "name": "example",
  "root": ".",
  "budget": { "always_on_tokens": 4000, "total_tokens": 150000 },
  "components": [
    {
      "id": "agents",
      "kind": "system_prompt",
      "paths": ["AGENTS.md"],
      "always_on": true
    },
    {
      "id": "skills",
      "kind": "skills",
      "paths": ["skills/*/SKILL.md"],
      "trigger_names": ["release"]
    }
  ]
}
```

| Field | Rules |
| :--- | :--- |
| `schema` | Exactly `harness.manifest.v1`. |
| `name` | Used in receipts. Defaults to the manifest filename stem. |
| `root` | Directory the globs resolve against, relative to the manifest. |
| `budget.always_on_tokens` | Non-negative integer; exceeded becomes an error finding. |
| `budget.total_tokens` | Non-negative integer; exceeded becomes an error finding. |
| `components[].id` | Unique, non-empty string. |
| `components[].kind` | One of `system_prompt`, `guardrails`, `memory`, `tool_guidance`, `subagents`, `skills`, `scripts`, `plugins`. |
| `components[].paths` | Non-empty array of globs. Matched files are deduplicated per component. |
| `components[].always_on` | Boolean. Always-on text is the haystack for reachability. |
| `components[].enabled` | Boolean, default `true`. Disabled components are not matched. |
| `components[].trigger_names` | Optional strings used by the reachability check. |

The audit derives, for each component: matched files, token estimate, and a row in the receipt. Errors are findings with severity `error`; warnings do not fail the command.

## `requirements.json` — what must exist

Schema: `openharness.requirements.v1`

```json
{
  "schema": "openharness.requirements.v1",
  "requirements": [
    { "id": "always-on-entry", "kind": "system_prompt", "component": "agents" },
    { "id": "product-skills", "kind": "skills" },
    { "id": "memory", "kind": "memory", "required": false }
  ]
}
```

| Field | Rules |
| :--- | :--- |
| `id` | Unique, non-empty. |
| `kind` | One of the eight component kinds. |
| `component` | Optional id; when present, that component must exist, match the kind, be enabled, and match files. |
| `requires_files` | Boolean, default `true`; when `false`, an empty matched set still satisfies the requirement. |
| `required` | Boolean, default `true`; `false` gaps are reported but do not fail the inventory. |
| `description` | Optional text. |

## `cases.json` — what must keep working

Schema: `openharness.cases.v1` · [cases.schema.json](standards/schemas/cases.schema.json)

```json
{
  "schema": "openharness.cases.v1",
  "cases": [
    {
      "id": "unit",
      "description": "The unit suite passes",
      "command": "python -m pytest -q",
      "expect": { "exit_code": 0 },
      "timeout_s": 300,
      "budget_tokens": 0
    },
    {
      "id": "cli",
      "command": "python -m openharness --version",
      "expect": { "exit_code": 0, "stdout_contains": "openharness" }
    }
  ]
}
```

| Field | Rules |
| :--- | :--- |
| `id` | Unique, non-empty. |
| `command` | Shell command, run in `--workdir`. Required. |
| `expect.exit_code` | Integer. |
| `expect.stdout_contains` | Substring matched against stdout plus stderr. |
| `expect.artifact` | Path that must exist after the command, relative to `--workdir`. |
| `timeout_s` | Integer in `1..3600`, default `120`. |
| `budget_tokens` | Non-negative integer; summed into the receipt when present. |
| `description` | Optional text. |

Unknown fields are declaration errors. Only run a case file you trust: cases execute shell commands.

## `policy.json` — what is permitted

Schema: `openharness.policy.v1` · [policy.schema.json](standards/schemas/policy.schema.json)

```json
{
  "schema": "openharness.policy.v1",
  "description": "Repository guardrails",
  "default": "ask",
  "rules": [
    {
      "id": "verification",
      "match": { "tool": "shell", "command_regex": "^python -B" },
      "verdict": "allow",
      "reason": "the declared verification commands"
    },
    {
      "id": "no-destructive",
      "match": { "tool": "shell", "command_regex": "rm -rf" },
      "verdict": "deny",
      "reason": "recursive deletion needs a human decision"
    }
  ]
}
```

A rule matches only when every declared condition matches. Evaluation is ordered and last-match-wins, so a later specific rule refines an earlier broad one. The request may carry `tool`, `path`, and `command`. `default` applies when no rule matches.

The verdict is `allow`, `ask`, or `deny`. OpenHarness evaluates; the host enforces. See [COMPATIBILITY.md](COMPATIBILITY.md) for what is observed versus documented.

## `harness.lock` — the accepted state

Schema: `openharness.lock.v1` · [lock.schema.json](standards/schemas/lock.schema.json)

```json
{
  "schema": "openharness.lock.v1",
  "manifest": "example",
  "fingerprint": "…64 hex…",
  "budget": { "always_on_tokens": 4000, "total_tokens": 150000 },
  "totals": {
    "always_on_tokens": 511,
    "total_tokens": 91426,
    "files": 40,
    "components": 7
  },
  "components": [
    {
      "id": "agents",
      "kind": "system_prompt",
      "enabled": true,
      "always_on": true,
      "tokens": 511,
      "files": [{ "path": "AGENTS.md", "sha256": "…64 hex…", "tokens": 511 }]
    }
  ],
  "declarations": {
    "policy": { "path": "policy.json", "sha256": "…64 hex…" }
  },
  "generator": { "name": "openharness", "version": "0.2.0" }
}
```

Determinism rules:

- Components keep manifest order; files are sorted by path.
- Hashes are over exact bytes; paths are repository-relative with `/`.
- `generator.version` is excluded from drift comparison, so a tool upgrade alone does not fail CI.
- Absent declarations are omitted, not recorded as null.

## Context budget receipt

Schema: `openharness.context.v1` · [context.schema.json](standards/schemas/context.schema.json)

`openharness context` reuses the audit's measurement pass and splits enabled tokens into three layers: `resident` (always on), `loadable` (enabled, loaded on demand), and `executable` (`scripts` and `plugins`, which never enter context). Disabled components are excluded. It lists the largest components, one lever per non-zero component (`trim` or `defer`), and a headroom verdict for each declared budget. `tokens.total` always equals the audit total.

## Receipts

Every command emits one of these, canonically serialized and capped at 2500 bytes:

| Schema | Command |
| :--- | :--- |
| `openharness.receipt.v1` | audit |
| `openharness.context.v1` | context |
| `openharness.verify.v1` | verify |
| `openharness.selection.v1` | select |
| `openharness.cases.v1` / `.cases.receipt.v1` | cases (declaration / execution) |
| `openharness.telemetry.v1` | telemetry |
| `openharness.inventory.v1` | inventory |
| `openharness.failures.v1` | failures |
| `openharness.policy.v1` | policy |
| `openharness.lock.receipt.v1` | lock |
| `openharness.plan.v1` | plan (`--format json`) |
| `openharness.report.v1` / `.report.receipt.v1` | report (document / receipt) |
| `openharness.init.v1` | init |

Every receipt reports a verdict field (`ok` or `verdict`), severity or category counts, and `schema`. When a receipt would exceed 2500 bytes, detail is dropped first; verdict, totals, and counts are never dropped.

## `journal.jsonl` — iteration evidence

Schema: [journal.schema.json](standards/schemas/journal.schema.json). One JSON object per line. Required fields: `ts`, `iteration` (unique integer), `front`, `hypothesis`, `decision`. Adoption additionally requires `scope`, `evidence_ref`, and `rationale`; an `invariant` scope requires at least two distinct cases. Optional fields include `contrast`, `metric_before`, `metric_after`, `cases`, `deficiency`, `failure`, `cost`, and `harness_fingerprint`.

`openharness verify` validates the contract; `telemetry` and `failures` project it. The journal is the evidence ledger, not a log: write it only from recorded results.

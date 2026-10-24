# Quickstart

This page takes a repository from "an agent works here sometimes" to "the harness is declared, locked, measured, and gated in CI" in five commands.

## 1. Install

```sh
pipx install openharness
openharness --version
```

`pipx` keeps the CLI isolated; `python -m pip install openharness` works too. Python 3.10 or later.

## 2. Discover the harness

From the repository root:

```sh
openharness init
```

`init` looks for the surfaces a harness actually uses:

- always-on instructions: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md`
- project documentation: `README.md`
- host rules: `.cursor/rules/*.mdc`, `.github/instructions/*.instructions.md`
- skills: `skills/*/SKILL.md`, plus `.claude`, `.opencode`, `.agents` skill roots
- commands and subagents under the host directories
- scripts, MCP configuration, `policy.json`, and memory files

It writes `harness.json` and `harness.lock` and prints what it found. It refuses to overwrite an existing manifest. Starting from an empty directory is a finding, not a crash.

```json
{
  "schema": "harness.manifest.v1",
  "name": "your-repo",
  "root": ".",
  "budget": { "always_on_tokens": 2000, "total_tokens": 10000 },
  "components": [
    { "id": "agents", "kind": "system_prompt", "paths": ["AGENTS.md"], "always_on": true },
    { "id": "skills", "kind": "skills", "paths": ["skills/*/SKILL.md"] }
  ]
}
```

Budgets are generated with 25% headroom over the measured state, rounded up. Edit them down once you know what you are willing to pay for.

## 3. Audit

```sh
openharness audit --manifest harness.json
```

The receipt reports components, files, always-on tokens, total tokens, findings, and the fingerprint. Exit `0` means clean, `1` means findings, `2` means the manifest itself is invalid.

Findings worth fixing first:

| Code | Meaning |
| :--- | :--- |
| `component.missing` | A declared glob matches nothing. |
| `link.missing` | A Markdown link inside the harness points nowhere. |
| `reachability.orphan` | A skill or subagent is never referenced from an always-on component. |
| `duplication.line` | The same long line appears in more than one component. |
| `budget.always_on_exceeded` | The always-on surface costs more than declared. |

## 4. Lock and plan

```sh
openharness lock
openharness plan --check
```

`lock` writes `harness.lock`, which records the fingerprint, every file's SHA-256 and token estimate, the budget, and the hashes of `policy.json`, `cases.json`, and `requirements.json`.

`plan --check` exits `0` when the tree matches the lock and `1` when it does not. Without `--check`, it is informational and exits `0`; use it to preview a change.

```text
openharness plan: your-repo
lock: harness.lock
fingerprint: locked 8cd422… actual 0d6cae…
~ AGENTS.md (agents) +5 tokens
+ skills/release/SKILL.md (skills) +212 tokens
- docs/old-runbook.md (readme) -340 tokens
~ policy.json (declaration: policy)
drift: 4 change(s) across 3 component(s)
```

Prefixes mean the same thing they mean in a diff: `~` changed, `+` added, `-` removed.

## 5. Gate CI

Daily verification:

```sh
openharness report --manifest harness.json --requirements requirements.json \
  --cases cases.json --journal .agents/loop/journal.jsonl --format markdown
```

The report writes `harness-report.md` and prints a bounded receipt. Use `--format sarif` for code scanning, `--format junit` for test dashboards, and `--format json` for machines. Add `--execute` only when you intend the declared commands to run.

GitHub Actions:

```yaml
name: harness
on: [pull_request]
permissions:
  contents: read
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: seismael/openharness@v1
        with:
          manifest: harness.json
          requirements: requirements.json
          lock: harness.lock
          comment: true
```

## Where to go next

- Declare what the harness must contain: **[docs/SCHEMAS.md](SCHEMAS.md)**, `requirements.json`.
- Declare what a change must not break: `cases.json` and RFC-0012.
- Declare what an agent may do: `policy.json` and RFC-0015.
- Record iteration evidence: the loop skill's journal contract, RFC-0010 and RFC-0011.
- Compare two candidate outputs without knowing their author: `openharness select`, RFC-0010.
- Diagnose recurring failures: `openharness failures`, RFC-0014.

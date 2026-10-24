# OpenCode adapter (OpenHarness)

Binds the eight OHP harness kinds to native OpenCode surfaces and installs the
`/openharness` command plus the read-only `harness-editor` subagent. Verified against
OpenCode V2 command and agent formats; undocumented for V1.

## Kind bindings

| OHP kind | Native OpenCode surface |
| :--- | :--- |
| `system_prompt` | `AGENTS.md` (project) and the global instructions file |
| `guardrails` | `permissions` rules, `opencode.jsonc` denials, plugin enforcement |
| `memory` | project knowledge files and wiki index |
| `tool_guidance` | tool sections of instructions, `tool_output` caps, LSP/formatter settings |
| `subagents` | `.opencode/agents/*.md` with `mode: subagent` |
| `skills` | `.opencode/skills/*/SKILL.md` (or `~/.config/opencode/skills/`) |
| `scripts` | helper scripts invoked by the agent |
| `plugins` | `.opencode/plugins/*.ts` |

## Install

Global install (recommended — the command works in every project):

```bash
mkdir -p ~/.config/opencode/commands ~/.config/opencode/agents
cp adapters/opencode/commands/openharness.md ~/.config/opencode/commands/openharness.md
cp adapters/opencode/agents/harness-editor.md ~/.config/opencode/agents/harness-editor.md
```

Project install:

```bash
mkdir -p .opencode/commands .opencode/agents
cp adapters/opencode/commands/openharness.md .opencode/commands/openharness.md
cp adapters/opencode/agents/harness-editor.md .opencode/agents/harness-editor.md
```

Either way, install the `loop` skill from this repository first
(`python tools/install_skill.py --skill loop --to <skills-dir>/loop`); the command loads its
`references/openharness.md` and runs the audit script it ships. The command resolves that
skill directory from wherever it is installed, so no project-relative path is required.

## Declare the surface

```json
{
  "schema": "harness.manifest.v1",
  "name": "project-harness",
  "budget": { "always_on_tokens": 24000, "total_tokens": 60000 },
  "components": [
    { "id": "prompt", "kind": "system_prompt", "paths": ["AGENTS.md"], "always_on": true },
    { "id": "settings", "kind": "guardrails", "paths": ["opencode.jsonc"], "always_on": true },
    { "id": "skills", "kind": "skills", "paths": [".opencode/skills/*/SKILL.md"] },
    { "id": "agents", "kind": "subagents", "paths": [".opencode/agents/*.md"] },
    { "id": "plugins", "kind": "plugins", "paths": [".opencode/plugins/*.ts"] }
  ]
}
```

## Use

```text
/openharness <what you want to change>
```

The command audits the declared surface, reports findings by code, and refuses to adopt a
change without a probe receipt for that exact harness state. The `harness-editor` subagent
can be launched for a read-only proposal pass; it cannot edit files.

## Verify

```bash
python skills/loop/scripts/openharness_audit.py --manifest harness.json
```

Exit `0` = no error findings, `1` = errors present, `2` = invalid manifest. The receipt is
capped at 2,500 bytes and is byte-identical across runs on an unchanged tree.

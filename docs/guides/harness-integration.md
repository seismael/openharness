# Universal Harness Integration Guide

How to integrate **OpenHarness** and the **Open Harness Protocol (OHP)** natively across all major AI agent runtimes and developer environments.

---

## Supported Agent Runtimes

| Harness | Integration Mechanism | Command / Activation | Memory Persistence |
| :--- | :--- | :--- | :--- |
| **Claude Code** | Native Plugin / Skills directory | `/loop "<target>"`, `/audit` | `.agents/loop/` |
| **Google Antigravity (CLI & IDE)** | Native Skills + Slash Commands | `/loop "<target>"`, Subagents | `.agents/loop/` |
| **OpenCode** | Global / Workspace Skills | Headless in-session prompt | `.agents/loop/` + DB |
| **Cursor / Windsurf** | Model Context Protocol (MCP) + Rules | MCP Tools: `loop_status`, etc. | `.agents/loop/` |
| **Headless CI/CD (GitHub Actions)** | Native Agent Runner (`opencode run`, `claude -p`) | Scheduled nightly cron | Git PR with receipts |

---

## 1. Anthropic Claude Code

Claude Code supports OpenHarness either via its official plugin system or via direct skill installation.

### Option A: Plugin Installation (Recommended)
Add the marketplace and install with two commands:
```bash
/plugin marketplace add seismael/openharness
/plugin install openharness@openharness-marketplace
```

### Option B: Local Project Installation
Copy the skills directly to `.claude/skills/` in your repository:
```bash
python tools/install_skill.py --skill loop --to .claude/skills/loop
python tools/install_skill.py --skill audit --to .claude/skills/audit
```

### Launching the Autonomous Loop in Claude Code
```bash
/loop "Optimize database connection pooling in src/db.rs to reduce P99 query latency under 5ms without increasing memory"
```

---

## 2. Google Antigravity (CLI & IDE)

Antigravity natively discovers Agent Skills placed in the user directory or project root.

### Installation
Link or install the bundled skills into Antigravity's global skills directory:
```bash
# Global installation (available to all projects)
python tools/install_skill.py --skill loop --to ~/.gemini/antigravity-cli/skills/loop
python tools/install_skill.py --skill audit --to ~/.gemini/antigravity-cli/skills/audit
python tools/install_skill.py --skill knowledge --to ~/.gemini/antigravity-cli/skills/knowledge
```

### Usage in Antigravity
Launch with the slash command:
```bash
/loop "Execute autonomous loop on this repository to achieve target in docs/knowledge/profile.yaml"
```
Antigravity automatically leverages `invoke_subagent` to delegate high-volume diagnostic analysis to read-only subagents, preserving the primary context window.

---

## 3. OpenCode

OpenCode discovers skills from `~/.config/opencode/skills/` or repository-level `.opencode/skills/`.

### Installation
```bash
# Workspace-specific installation
python tools/install_skill.py --skill loop --to .opencode/skills/loop
python tools/install_skill.py --skill knowledge --to .opencode/skills/knowledge
```

### Execution
Initiate an in-session loop with the standard prompt:
```text
Execute the autonomous optimization loop according to skills/loop/SKILL.md:
- Target is declared in .agents/loop/knowledge/profile.yaml.
- Stage minimal candidates via git snapshots before running benchmarks.
- Enforce dual-gate verification (gain + zero regressions).
- Record all results in .agents/loop/journal.jsonl.
```

---

## 4. Cursor & Windsurf (via MCP Server)

For IDE-based agents like Cursor and Windsurf, OpenHarness provides a zero-dependency **Model Context Protocol (MCP)** server: `tools/mcp_server.py`.

### Configuring MCP in Cursor
Add the following to your Cursor MCP configuration (`~/.cursor/mcp.json` or project settings):

```json
{
  "mcpServers": {
    "agentic-loop": {
      "command": "python",
      "args": ["tools/mcp_server.py"],
      "env": {
        "AGENTIC_LOOP_ROOT": "."
      }
    }
  }
}
```

### Available MCP Tools
- **`loop_status`**: Returns current iteration, champion commit, metric ground truth, and active front.
- **`loop_step`**: Returns the highest Expected-Value move from `plans/next_moves.json`.
- **`loop_verify`**: Executes the verification pipeline defined in `profile.yaml` and reports pass/fail receipts.
- **`loop_journal`**: Fetches recent chronological iteration receipts from `journal.jsonl`.

### Project Rule Integration (`.cursorrules`)
Include the following directive in `.cursorrules`:
```text
When executing autonomous optimization or refactoring tasks:
1. Always check loop state using the `loop_status` tool.
2. Commit working tree changes before running evaluations (`feat(candidate): ...`).
3. If tests or invariants fail, immediately roll back (`git reset --hard HEAD~1`).
4. Suppress verbose CLI output and return scalar JSON receipts only.
```

---

## 5. Headless CI/CD Runners (GitHub Actions)

Deploy OHP as an overnight research workflow running on a scheduled cron:

```yaml
name: Nightly Autonomous Optimization
on:
  schedule:
    - cron: '0 23 * * *' # Every night at 11:00 PM UTC

jobs:
  optimize:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Environment
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Execute Overnight Autonomous Loop
        env:
          OPENCODE_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
        run: |
          opencode run --prompt "/loop 'Execute nightly autonomous optimization per .agents/loop/knowledge/profile.yaml'"

      - name: Create Pull Request with Mathematical Receipts
        uses: peter-evans/create-pull-request@v6
        with:
          title: "Autonomous Optimization: Verified Invariant-Safe Improvements"
          branch: "agents/nightly-improvements"
          body-path: ".agents/loop/plans/nightly_pr_summary.md"
```

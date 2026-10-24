# Guide: Running the Autonomous Optimization Loop Across AI Agent Hosts

This guide explains how to operate the generic, token-efficient, and deterministic **Autonomous Optimization Loop** across multiple AI coding agent environments including **Antigravity CLI/IDE**, **OpenCode**, **Claude Code**, and **Codex CLI**.

---

## 1. Overview of the Autonomous Loop

The Autonomous Optimization Loop is a structured, 5-stage engineering pipeline designed to allow AI agents to iteratively improve complex software repositories, systems, and quantitative models without human intervention at every intermediate step:

1. **Stage 1: Autonomous Reconnaissance & Invariant Mapping**
   - The agent reads `<project>/docs/knowledge/index.md` (< 400 tokens) to orient paths, configs, and constraints without running blind `find` or `ls` scans.
2. **Stage 2: Empirical Gap Diagnosis & Causal Forensics**
   - The agent decomposes opportunity gaps between current performance and theoretical potential using CLI diagnostics.
3. **Stage 3: Surgical Candidate Formulation & Pre-Evaluation Snapshot Gate**
   - The agent makes minimal, targeted code/config edits and commits them to Git prior to running evaluations, ensuring immutable evaluation artifacts and preventing `RuntimeIdentityError`.
4. **Stage 4: Dual-Gate Verification & Synthetic Fixture Realignment**
   - The candidate is tested for both primary metric gain and invariant preservation. Test fixtures asserting outdated nominal values are updated cleanly in the same commit.
5. **Stage 5: Compounding Knowledge Persistence & Atomic Publication**
   - The agent logs findings to `docs/audit/findings/`, records decisions in `docs/knowledge/decisions.md`, updates `known_defects.md`, and pushes commits upstream.

### 1.1 Generic, agnostic, and front-driven

The loop engine is identical for every repository; a single declarative **project profile**
(`.loop/knowledge/profile.yaml` or `docs/knowledge/profile.yaml`) supplies what to optimize, what to examine, how to run it,
and when to stop. The loop explores the project across **all fronts** — audit, discover,
research, diagnose, debug, improve, harden, performance, pipeline, knowledge, plan,
orientation — choosing the next move from accumulated evidence (defect > uncovered front >
largest diagnosed gap > structural candidate > parameter last), never a groundless sweep.
A **coverage ledger** (`.loop/coverage.json`) proves every required front/sub-axis
reached a terminal status before the loop may finish. See
[front taxonomy](../../skills/loop/references/front-taxonomy.md),
[dispatch policy](../../skills/loop/references/dispatch-policy.md),
[coverage ledger](../../skills/loop/references/coverage-ledger.md),
[pipeline contract](../../skills/loop/references/pipeline-contract.md),
[project profile](../../skills/loop/references/project-profile.md),
[graceful control](../../skills/loop/references/graceful-control.md),
[agent ecosystem](../../skills/loop/references/agent-ecosystem.md),
[token economy](../../skills/loop/references/token-economy.md), and the
[in-session loop](../../skills/loop/references/in-session-loop.md).

The loop runs **100% in-session**: the agent is the engine, taking one atomic step at a time and
continuing until the target is met or it is stopped. Its architecture is cleanly partitioned into two root directories:
- **`.loop/`**: The loop's durable runtime and knowledge brain — state (`loop.json`), append-only audit journal (`journal.jsonl`), coverage ledger (`coverage.json`), issue ledger (`issues.jsonl`), plans (`plans/`), indexed project wiki (`knowledge/`), sandboxed scratchpad (`scratch/`), and helper scripts (`scripts/`).
- **`.agents/`**: Project-useful executable assets created or used by the loop — reusable skills (`skills/`) and specialist personas (`subagents/`).

The loop can be stopped gracefully at any moment simply by saying "stop the loop" or placing `.loop/STOP`. It persists current state in `.loop/loop.json` and resumes seamlessly without losing progress. There are zero background daemons, wrappers, or external CLI processes.

---

## 2. Environment-Specific Instructions

### A. Google Antigravity (CLI & IDE)

In Antigravity CLI (`agy`) or Antigravity IDE:

1. **Skill Installation**:
   Ensure `skills/loop`, `skills/audit`, and `skills/knowledge` are linked or placed in `~/.gemini/antigravity-cli/skills/` or `.agents/skills/`.
2. **Autonomous Loop Activation (`/loop "<target>"`):**
   Launch with the `/loop` slash command and target description for continuous, non-stop autonomous execution:
   ```
   /loop "Execute the autonomous continuous optimization loop on this repository following skills/loop/SKILL.md to achieve the target objective in docs/knowledge/profile.yaml."
   ```
   *(Note: This uses the specialized in-session `/loop` skill, cleanly separated from Antigravity's native `/goal` command to prevent any behavioral or naming collisions.)*
   
   The agent autonomously:
   1. Reads `docs/knowledge/index.md` and `profile.yaml` to orient paths, metrics, and closed frontiers.
   2. Follows the dispatch priority ladder (defect > uncovered front > diagnosed gap > mechanism).
   3. Consumes only byte-bounded projections (<= 2500 bytes per artifact); never writes ad-hoc extraction scripts.
   4. Formulates minimal falsifiable candidates, committing working tree before evaluating.
   5. Enforces dual-gate verification (primary metric improvement + zero invariant regressions).
   6. Records findings in `docs/knowledge/decisions/`, updates `coverage.json` and `loop.json`, and recurs immediately without conversational chatter.
3. **Native Execution Features**:
   - The agent operates continuously under `/loop` until completion criteria are met or genuinely blocked.
   - The agent uses `invoke_subagent` to delegate raw artifact digestion and multi-file exploration to read-only subagents, consuming only compact summaries (<= 2500 bytes).
   - The agent maintains absolute token frugality and zero conversational chatter.

---

### B. OpenCode

In OpenCode:

1. **Skill Configuration**:
   Place or symlink `openharness/skills/` into your OpenCode skills directory (e.g. `~/.config/opencode/skills/` or repository root `.opencode/`).
2. **Initial Prompt**:
   ```
   Run the autonomous optimization loop for this project:
   - Refer to skills/loop/SKILL.md for the 5-stage protocol.
   - Use docs/knowledge/ for repository facts, data topology, and invariants.
   - Always commit candidate changes before running background evaluations.
   - Verify both primary metric gain and invariant test passes.
   - Record findings in docs/audit/ and update decisions in docs/knowledge/.
   - Push verified improvements to origin/main.
   ```
3. **Tips for OpenCode**:
   - Remind the model to stay token-frugal and not output conversational pleasantries.
   - Ensure OpenCode's terminal permissions allow running git commits and tests.

---

### C. Claude Code

In Claude Code (`claude` CLI):

1. **Skill Configuration**:
   Copy or link `skills/audit` and `skills/knowledge` into `.claude/skills/` or reference them directly in `CLAUDE.md`.
2. **Initial Prompt**:
   ```
   Start the autonomous optimization cycle following skills/loop/SKILL.md.
   Begin by checking docs/knowledge/index.md, run the baseline evaluation, and identify the top opportunity gap.
   Ensure every candidate is committed before running evaluations, tests pass, and knowledge leaves are updated.
   ```
3. **Tips for Claude Code**:
   - Instruct Claude Code to keep individual terminal outputs bounded (`head -n 50` or using structured JSON).
   - Use git commands cleanly without leaving uncommitted files.

---

### D. OpenAI Codex CLI

In OpenAI Codex CLI:

1. **Skill Configuration**:
   Install via `python tools/install_skill.py --skill audit --to ~/.codex/skills/audit`.
2. **Command / Prompt**:
   ```
   $audit Run the autonomous optimization loop following skills/loop/SKILL.md.
   Focus on maximizing the target objective while strictly upholding project invariants.
   Commit working tree before each evaluation run and document all accepted findings.
   ```

---

## 3. Best Practices for Human Supervisors

- **Permissions**: Grant the agent terminal execution and git permissions so it can autonomously commit, evaluate, test, and push.
- **Knowledge Base as Source of Truth**: Encourage the agent to read and update `docs/knowledge/` leaves (`invariants.md`, `decisions.md`, `known_defects.md`). This guarantees that context survives session restarts and context truncations.
- **Pre-Evaluation Snapshots**: Ensure the agent always commits candidate code before running evaluations. Dirty worktrees cause evaluator provenance checks to fail.
- **Verification Gates**: Never accept candidates that fail invariant unit tests, even if they show short-term metric improvements.

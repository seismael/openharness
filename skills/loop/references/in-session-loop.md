# In-Session Loop: The Self-Contained Autonomous Engine

The loop is **not a process, a daemon, a plugin, or a CLI wrapper**. It is a way of working that the
agent performs **inside its own session**: a single, sequential, continuous, self-managed loop that
reads durable state from the project, takes **one atomic step at a time**, records the step, and
immediately continues. The agent *is* the engine. This makes it generic (any project), agnostic
(any domain), and fully portable (a skill plus standard project directories — nothing to install,
nothing outside the repository to trust).

---

## 1. The Unified Directory Standard: `.agents/` as Canonical Root

The loop manages its execution through a standardized, single-root `.agents/` architecture:

```
<project-root>/
└── .agents/                                # Unified Agentic Root Directory
    ├── loop/                               # Loop State, Plans, Knowledge, and Workspace Tools
    │   ├── loop.json                       # Current durable state (target, status, step, metrics, resume pointer)
    │   ├── env.json                        # Deterministic tool manifest (python_bin, test_cmd, entry_point)
    │   ├── journal.jsonl                   # Terse append-only step journal
    │   ├── coverage.json                   # Front-driven breadth guarantee ledger
    │   ├── issues.jsonl                    # Canonical defect/issue ledger (schema loop.issue.v1)
    │   ├── STOP                            # Ephemeral stop sentinel (if user/script requests stop)
    │   ├── plans/                          # Generated strategic & tactical plans
    │   │   ├── master_plan.md              # Decomposed target roadmap
    │   │   └── next_moves.json             # Ranked prioritized moves
    │   ├── knowledge/                      # Indexed knowledge base (wiki)
    │   │   ├── index.md                    # Root entrypoint (< 400 tokens) with indexed links
    │   │   ├── invariants.md               # Non-negotiable boundaries, axioms, rules
    │   │   ├── capabilities.md             # Discovered CLI commands, test runners, benchmarks
    │   │   ├── baselines.md                # Incumbent metric baselines and receipts
    │   │   ├── decisions/                  # Cumulative decision records
    │   │   │   └── log.md                  # Log of accepted, rejected, and inert candidates
    │   │   └── profile.yaml                # Declarative project seam (loop.profile.v1)
    │   ├── scratch/                        # Sandboxed temporary work (auto-cleaned or isolated)
    │   └── scripts/                        # Deterministic helper tools & validators developed for the loop
    │
    ├── skills/                             # Installed portable skills (loop, audit, knowledge, etc.)
    └── subagents/                          # Specialized personas created or invoked on demand
        ├── diagnostician.yaml              # Causal root-cause & bottleneck specialist
        ├── architect.yaml                  # Structural design & invariant specialist
        ├── verifier.yaml                   # Dual-gate & regression verification specialist
        └── synthesizer.yaml                # Log digestion & bounded projection specialist
```

*(Note: For backward compatibility, if `.agents/loop/` is not present but `.loop/` is present at the repository root, the loop gracefully binds to `.loop/`.)*

---

## 2. The In-Session Execution Cycle

```
repeat
  1. Read state     .agents/loop/loop.json (or fallback) + coverage.json + journal.jsonl tail + knowledge
  2. Check stop     if "stop the loop" or STOP sentinel present -> persist, set STOPPED, yield cleanly
  3. Dispatch       choose the single next step (dispatch policy); record in plans/next_moves.json
  4. Delegate       delegate heavy exploration/diagnostics to read-only subagents in .agents/subagents/
  5. Act            do exactly that one step; commit pre-evaluation snapshot (feat(candidate): ...)
  6. Verify         run the step's gate (invariants always; objective for economic changes)
  7. Persist        append journal.jsonl; update coverage.json, loop.json, decisions log
  8. Continue       go to 1 immediately
until the target is met with coverage complete, or an actionable issue blocks progress,
      or the user says stop
```

- **Continue immediately (The Zero-Yield Rule).** Do NOT end the turn or emit pure conversational markdown
  while actionable work remains. In agentic host runtimes (OpenCode, Claude Code, Antigravity), an assistant
  turn with text and zero tool calls automatically causes the host to wait for operator input (`finish_reason: "stop"`).
  To keep the loop running continuously, every turn completing a step MUST simultaneously co-emit or immediately
  chain the tool call initiating the next step (e.g. journal update -> next move read -> diagnostic probe).
- **One step at a time.** No batching unrelated work; each iteration is a coherent unit with
  its own evidence and gate, so progress is auditable and resumable.
- **Auto-Compaction & Anti-Anxiety.** Context size or token accumulation is NEVER a reason to hand off or stop.
  Host runtimes perform automatic context compaction. The loop state is durably preserved on disk in `.agents/loop/`.
  When compaction occurs, read `loop.json` and immediately resume the active move via tool call.
- **Graceful stop anytime.** Saying *"stop the loop"* or writing `.loop/STOP` halts the loop cleanly
  after the active step, preserving full state — see [graceful control](graceful-control.md).
- **Instant resume.** Invoking `/loop` or `/loop continue` continues immediately from `.loop/loop.json`
  without duplicated effort or frontier amnesia.

---

## 3. Durable State Reference

State lives in files inside `.loop/`, so the loop survives context compaction, conversation truncation,
and session restarts.

| File | Purpose | Shape |
| :--- | :--- | :--- |
| `.loop/loop.json` | Target objective, status, sub-targets, resume pointer | `{target, status: ACTIVE\|DONE\|STOPPED\|BLOCKED, sub_targets: [{id, statement, status}], updated_at}` |
| `.loop/coverage.json` | Breadth proof across all required fronts | see [coverage ledger](coverage-ledger.md) |
| `.loop/journal.jsonl` | Terse append-only step record | `{step, front, axis, action, evidence, outcome, ts}` |
| `.loop/issues.jsonl` | Canonical findings ledger | schema `loop.issue.v1` |
| `.loop/plans/` | Decomposed roadmaps and ranked next moves | `master_plan.md`, `next_moves.json` |
| `.loop/knowledge/` | Project wiki for persistent knowledge compounding | `index.md`, `invariants.md`, `capabilities.md`, `decisions/` |
| `.loop/scratch/` | Temporary working sandbox for one-off probes | clean workspace, never in repo root |
| `.loop/scripts/` | Deterministic helper scripts and analyzers | reusable project utilities |

**Compaction is expected and harmless.** If the conversation is summarized, re-read these
files; they — not the transcript — are the source of truth. A brand-new session resumes by reading
them and running the loop from step 1.

---

## 4. Director-Specialist Delegation

Keep the main session small and token-frugal by delegating breadth and heavy analysis to
specialized subagents hosted under `.agents/` — see [agent ecosystem](agent-ecosystem.md).

- **The main session Director is the only writer.** It applies every code change and creates every git commit.
- **Subagents are strictly read-only analysts.** They explore ASTs, digest large test logs, or profile
  traces, returning compact summaries (≤ 2,500 bytes with exact `path:line` evidence).

---

## 5. Token Economy

Maximizing useful work per token is non-negotiable — see [token economy](token-economy.md):
- **Index-first navigation**: Read `.loop/knowledge/index.md` (< 400 tokens) to navigate without blind filesystem sweeps.
- **Byte-bounded projections only**: Consume pre-projected, size-capped views (≤ 2,500 bytes per artifact).
- **Zero ad-hoc scratch scripts in root**: All scratch scripts go into `.loop/scratch/`.
- **Frontier discipline**: Always check `do_not_repeat` in `.loop/loop.json` and prior decisions before sweeping.
- **Continuous tool execution**: Never pause for conversational pleasantries while actionable moves remain.

---

## 6. Portability

The entire engine is **this skill plus the project's `.loop/` and `.agents/` directories**. Any
tool-calling agent host (Antigravity, OpenCode, Claude Code, Codex) runs it identically. There
is no external component to install, version, or trust.

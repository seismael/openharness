---
name: loop
description: Autonomous continuous optimization engine for software, quantitative trading, and systems engineering. Takes a single target description via `/loop "<target>"` and runs endless autonomous iterative cycles of diagnosis, candidate formulation, pre-evaluation snapshot, dual-gate verification, and knowledge compounding without stopping or asking intermediate questions. Runs entirely in-session, sequentially and self-managed, with no external process or plugin.
---

# Loop (Autonomous Continuous Optimization Engine)

Run an endless, autonomous, target-directed optimization loop **inside this session**. The user
supplies a single target description via `/loop "<target>"` (e.g. `/loop "improve net profit across all symbols"`
or `/loop "reduce p99 latency under 5ms"`). The agent derives every operational detail, reads
the project's durable state (`.agents/loop/loop.json` or fallback `.loop/loop.json`), takes **one atomic step at a time**, records it, and continues
— sequentially and self-managed — until the target is met, it is genuinely blocked, or the user stops it.

The loop is **generic, agnostic, and portable**: it is this skill plus the project's standard
unified **`.agents/`** architecture:
- **`.agents/loop/`**: The project loop's brain, durable state (`loop.json`), audit journal (`journal.jsonl`),
  breadth ledger (`coverage.json`), issue ledger (`issues.jsonl`), generated plans (`plans/`),
  knowledge wiki (`knowledge/`), sandboxed scratchpad (`scratch/`), helper scripts (`scripts/`),
  and deterministic tool manifest (`env.json`).
- **`.agents/skills/`**: The project's native and dynamically synthesized skills.
- **`.agents/subagents/`**: The project's specialized personas created or invoked on demand.
*(Note: For backward compatibility, if `.agents/loop/` is absent but `.loop/` exists, the engine gracefully binds to `.loop/`.)*

Nothing external is installed, and no background daemon or CLI wrapper process is used. It explores
the project across **all fronts** — orient, discover, audit, diagnose, research, debug, improve, harden,
performance, pipeline, knowledge, plan — deciding the next step from accumulated evidence, never
arbitrarily. See the [in-session loop](references/in-session-loop.md),
[self-evolution](references/self-evolution.md),
[graceful control](references/graceful-control.md),
[agent ecosystem](references/agent-ecosystem.md),
[token economy](references/token-economy.md),
[front taxonomy](references/front-taxonomy.md),
[dispatch policy](references/dispatch-policy.md),
[coverage ledger](references/coverage-ledger.md),
[pipeline contract](references/pipeline-contract.md),
and [project profile](references/project-profile.md).

## Operating Contract

- **Single-Sentence Autonomous Activation & Target Grounding**: The user specifies only the high-level target
  via `/loop "<target>"` (e.g. `/loop "maximise profit of the application to reach max potential and realistic profit we can achieve"`).
  Never demand manual clarification or restrict yourself to arbitrary narrow slices unless strictly required.
  Autonomously discover the authoritative metric pipeline, invariants, and theoretical limits from project code and data.
- **Just-In-Time Capability Evolution**: The loop self-manages its capability suite dynamically. It authors
  sandboxed forensic scratch scripts (`.agents/loop/scratch/`), promotes reusable helpers (`.agents/loop/scripts/`),
  materializes specialized read-only subagents (`.agents/subagents/`), and generates project skills (`.agents/skills/`)
  based on empirical need as findings emerge.
- **Sequential Deep Thinking**: Proceed step-by-step through a deliberate cognitive cycle: sense, diagnose,
  hypothesize with data, execute minimal change, dual-gate verify, compound knowledge, and evolve plans.
- **Graceful Stop Anytime ("stop the loop")**: The user can stop the loop at any moment simply by
  saying "stop the loop", "pause", or by writing a sentinel `.agents/loop/STOP` (or `.loop/STOP`). The loop completes its
  current atomic step cleanly, flushes the journal, sets status `STOPPED` in `loop.json`,
  records the exact resume pointer, and yields cleanly.
- **Seamless Resume from Current State**: Invoking `/loop` or `/loop continue` immediately picks up
  from `loop.json` and the journal tail without loss of state, frontier amnesia, or duplicated effort.
- **Zero Conversational Chatter & Zero Standalone Yield**: Output concise, structured progress summaries
  ONLY co-emitted alongside or directly followed by the next tool call. NEVER emit a chat-only markdown turn
  without a tool call while the loop is active; in host runtimes (OpenCode, Claude Code), emitting text without
  a tool call terminates the turn and yields to the user. Every iteration turn MUST include the tool call
  executing or setting up the next step.
- **Profile-Driven Boot**: Read the [project profile](references/project-profile.md)
  (`.agents/loop/knowledge/profile.yaml`, `.loop/knowledge/profile.yaml`, or `docs/knowledge/profile.yaml`); if absent, bootstrap the wiki
  and run capability-discovery, then seed `index.md`, `capabilities.md`, and the profile.
- **Continuous Loop Recurrence & Unbroken Chaining (In-Session Execution)**: Perform one atomic step per iteration,
  persist it to the journal, and continue immediately without human prompts. Chain steps mechanically:
  `Tool: write journal/loop.json` -> `Tool: read/pop plans/next_moves.json` -> `Tool: execute step N+1`.
  Never yield the turn for conversational pleasantries or standalone summaries while actionable work remains
  on the dispatch ladder — see [in-session loop](references/in-session-loop.md).
- **Anti-Anxiety & Auto-Compaction Resilience**: Context size or token count is NEVER a valid reason
  to pause, yield, or hand off during an active loop. The host runtime manages context growth via automatic
  compaction. All critical state is durably persisted on disk in `.agents/loop/`. If compaction occurs,
  the agent immediately resumes from `.agents/loop/loop.json` via tool call without asking for user permission.
- **Token Economy & Deterministic Manifest**: Maximize useful work per token. Read `.agents/loop/env.json` for
  exact tool paths (`python_bin`, `test_cmd`) to avoid token-wasting discovery greps. Never stream raw logs,
  trade ticks, or multi-megabyte artifacts into context. Consume only byte-bounded projections
  (≤ 2,500 bytes per artifact) from canonical pipeline commands. Never write ad-hoc extraction
  scripts to the project root; keep temporary scratch work strictly inside `.agents/loop/scratch/`.
- **Specialist Agent Orchestration**: Delegate breadth, deep AST searches, and large log digestion
  to read-only specialized subagents (`.agents/subagents/`). Subagents return strictly bounded
  summaries (≤ 2,500 bytes with exact `path:line` evidence); only the main session director applies
  and commits changes.
- **Frontier Discipline & Closed Axes**: In the Orient phase, always review prior outcomes in
  `decisions/` and the `do_not_repeat` registry in `.loop/loop.json`. Never re-sweep an axis already
  proven exhausted or economically closed without fresh structural evidence.
- **Autonomous Target-Seeking & Continuous Hypothesis Generation**: The target is an outcome,
  never a static checklist. When existing candidate parameters or axes are exhausted, the engine
  MUST NOT declare "nothing to do", halt, or yield the turn. Escalate immediately to
  First-Principles Diagnostics (forensic analysis of suppressed signals, missing trades, MFE give-back,
  and cross-sectional variance) to generate novel structural hypotheses and replenish the queue.
  Documentation notes mentioning "operator-gated" apply strictly to live production deployment;
  in headless simulation/EVAL, the engine has unrestricted authority to simulate and test anything.
- **Coverage Guarantee**: Maintain the [coverage ledger](references/coverage-ledger.md):
  every required front/sub-axis must reach a terminal status. A metric may not be blamed
  while any required axis is unexamined.
- **Evidence-Based Dispatch**: Choose the next move with the [dispatch policy](references/dispatch-policy.md)
  — defect > uncovered front > largest diagnosed gap > structural candidate > parameter
  (last) > hygiene. Reason from data, code, wiki, and prior outcomes; never act without grounds.
- **Pipeline Only**: Execute the project's declared canonical [pipeline](references/pipeline-contract.md)
  stages. Never hand-roll analysis or produce numbers the pipeline cannot reproduce from a
  committed snapshot.
- **Pre-Evaluation Snapshot Protocol**: Before long-running evaluators/benchmarks/backtests,
  stage and commit candidate changes (`feat(candidate): ...`) for immutable, collision-free
  artifacts.
- **Dual-Gate Verification**: Every candidate promotion requires (1) **Primary Metric
  Improvement** — a measurable gain in the objective; and (2) **Invariant Soundness** —
  zero violations of the project's boundaries, axioms, or safety limits. Neither gate may
  be weakened to pass.
- **Continuous Knowledge Compounding**: For every accepted or rejected candidate, record
  the finding, append the decision, update `capabilities.md` with any new surface, and push
  upstream. Rejections and inert results are knowledge too.
- **Failure Recovery**: If a candidate fails either gate, revert to the baseline, record the
  failure mode, and proceed to the next hypothesis.

---

## The Execution Cycle

```
1. Orient          -- .agents/loop/loop.json (or fallback) + knowledge + capabilities; ensure a current baseline
2. Check Stop      -- verify no STOP sentinel (.agents/loop/STOP or .loop/STOP) or user stop directive
3. Dispatch        -- choose the next front/step by the dispatch policy
4. Delegate        -- delegate heavy analysis to read-only subagents in .agents/
5. Diagnose        -- run pipeline diagnostic stage; localize dominant gap
6. Candidate       -- one bounded, falsifiable change; snapshot to git
7. Evaluate+Gate   -- pipeline run; objective + invariant gates
8. Compound        -- adopt (commit+push) or revert; update knowledge AND coverage ledger
9. Continue        -- immediately; stop only when target met, blocked, or operator stops
```

Full lifecycle mechanics, including the sequential in-session loop, graceful control, and resume
semantics, are in the [loop protocol](references/loop-protocol.md).

# Loop Protocol: Autonomous Continuous Optimization Engine

Detailed operational mechanics for executing a target-directed, endless, autonomous
optimization loop **in-session**. The engine is generic and portable; the
[project profile](../assets/templates/profile.template.yaml) supplies every project
specific. The loop itself is defined in the [in-session loop](in-session-loop.md),
[graceful control](graceful-control.md), [agent ecosystem](agent-ecosystem.md),
and [token economy](token-economy.md).

---

## 1. Target Deconstruction & Formulation

From the profile (or a supplied target):

1. **Target Objective** — the scalar/vector `metric` to optimize (read from the profile).
2. **Operational Constraints** — `modes`, `boundaries`, stop criteria.
3. **Repository Context** — never ask the user for paths. Read `.loop/knowledge/index.md`
   (or `docs/knowledge/index.md`), then `capabilities.md`, then the profile. If absent, execute auto-bootstrapping:
   - Scan package manifests (`Cargo.toml`, `go.mod`, `pyproject.toml`, `package.json`, `Makefile`).
   - Run capability discovery to identify native build, test, and benchmark surfaces.
   - Initialize `.loop/` and `.agents/` structures.
   - Seed `.loop/knowledge/index.md`, `capabilities.md`, `.loop/coverage.json` (from `coverage.template.json`),
     and `.loop/knowledge/profile.yaml` (from `profile.template.yaml`) before proceeding.

Write the objective and its sub-targets to `.loop/loop.json`.

---

## 2. The Front-Driven, Sequential Loop

The loop is a dispatcher over **fronts** (see the [front taxonomy](front-taxonomy.md)),
executed one atomic step at a time, continuously, inside the session.

### Step 1: Orient
- Confirm repository state (branch, clean/dirty) and read `.loop/loop.json`, `.loop/coverage.json`,
  and the `.loop/journal.jsonl` tail.
- If no recent baseline artifact exists, run the profile's `evaluate` stage once to reproduce
  ground truth. Record it in the `orient` front.

### Step 2: Check Stop Directive
- Check for user stop message or presence of `.loop/STOP` sentinel file.
- If detected, persist status `STOPPED` in `.loop/loop.json`, flush journal, and yield cleanly
  per [graceful control](graceful-control.md).

### Step 3: Dispatch & Delegate
- Apply the [dispatch policy](dispatch-policy.md): pick the single step that most advances
  the target. Update ranked moves in `.loop/plans/next_moves.json`.
- For deep AST search, large log digestion, or complex profiling, delegate to read-only specialists
  hosted under `.agents/subagents/` per [agent ecosystem](agent-ecosystem.md).

### Step 4: Diagnose
- Run the relevant pipeline `diagnose` stage; consume only byte-bounded projections
  (≤ 2,500 bytes per artifact per [token economy](token-economy.md)). Localize the single largest
  component of drag or opportunity.

### Step 5: Candidate & Snapshot
- The main director makes the minimal localized code/config edit.
- Commit the snapshot: `feat(candidate): test hypothesis for <gap_id>`.
- Never evaluate an uncommitted worktree.

### Step 6: Evaluate & Dual-Gate
- Launch pipeline `evaluate`/`experiment` stages headless.
- **Gate A (Objective)**: metric strictly superior (per profile).
- **Gate B (Invariants)**: every boundary/axiom/limit test passes.

### Step 7: Decide & Compound
- **Pass**: write finding, append decision to `.loop/knowledge/decisions/log.md`, update
  `capabilities.md`, push, and mark coverage sub-axis `ADOPTED`.
- **Fail**: git revert candidate back to baseline, record failure mode in decisions log
  (an *inert* result is recorded, never adopted), and mark axis `COVERED-EXHAUSTED` if frontier is closed.
- Always update `.loop/coverage.json` and append a `.loop/journal.jsonl` record for the step.

### Step 8: Continue (Endless Recurrence)
- Persist the step to `.loop/loop.json`, then **immediately** go to Step 1. Do not stop between steps.
- Stop only when: the `target` criteria are met **and** coverage is complete; an actionable issue
  leaves you genuinely blocked (record `status: BLOCKED` with reason); or the operator stops the loop.

---

## 3. Completion

The loop may conclude only when **all** hold:

1. The [coverage ledger](coverage-ledger.md) is complete (every required axis terminal; no open defect).
2. The issue ledger (`.loop/issues.jsonl`) has no open actionable item.
3. The `target` criteria are met (or the frontier is provably exhausted with empirical evidence).

On completion, set `.loop/loop.json` `status: DONE`, summarize verified deltas, and yield.

## 4. Boundaries

This is development tooling. It obeys `profile.modes` and `profile.boundaries`, never
performs a production action, and never weakens determinism, safety, or correctness.

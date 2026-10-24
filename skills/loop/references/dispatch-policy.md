# Dispatch Policy: Deciding What To Do Next

At every step the loop answers one question: **given everything accumulated so far, what
single move most advances the target right now?** The answer must be *reasoned from
evidence*, never arbitrary. "Unrestricted" means the loop may pursue any admissible
direction the data supports — it does **not** mean acting without grounds. Flipping
parameters, guessing, or jumping to a candidate before diagnosis is exactly the "stupid
next step" the policy forbids.

## Priority ladder (highest first)

1. **Open defect or safety hole.** Anything shown incorrect, unsafe, or inconsistent in
   any front. A defect outranks all improvement work.
2. **Uncovered front.** An `UNEXPLORED` front (breadth guarantee) — examine it enough to
   reach a terminal status, then return to value work.
3. **Largest diagnosed opportunity.** The single biggest localized gap on the target
   metric, per case, from a real diagnostic artifact — never from a hunch.
4. **Structural candidate.** A bounded change to *mechanism* (not a constant) that the
   diagnosis indicates; verified against the target metric and invariants.
5. **Parameter candidate — last.** A constant/config change, and only when a diagnosis
   shows it binds the effective system. An inert (execution-identical) result is a
   rejection, recorded, never "adopted".
6. **Hygiene.** Knowledge compounding, pipeline/integrity, docs — when nothing
   value-bearing is actionable, or as the mandated close of any accepted change.

## Tie-breaks

- Expected value: the move with the larger credible upside (or larger risk removed).
- Cost: prefer the cheaper move when expected values are close.
- Irreversibility: prefer a reversible move when still uncertain; snapshot before any
  long-running evaluation.
- Freshness: prefer the front that has been untouched longest among equals.

## Reasoning discipline

- **Diagnose before you change.** A candidate without a reproducing artifact is
  speculation; record it as a hypothesis, not a change.
- **One bounded, falsifiable change per step**, with a stated kill-criterion *before*
  running anything. If the kill-criterion fires, revert and record — do not spin.
- **Learn from rejections.** An inert or regressed candidate is knowledge: record it and
  re-rank. Repeatedly re-testing the same rejected class is a policy violation.
- **Respect the bounded frontier.** When a class of candidates is empirically exhausted,
  say so with evidence and move to a higher-leverage class.
- **Cognitive Depth Escalation (RFC-0007).** If two (2) consecutive evaluations at Cognitive Tier $N$
  fail or yield $< 1\%$ improvement, Tier $N$ is declared saturated. The engine is algorithmically prohibited
  from dispatching another Tier $N$ move and MUST escalate to Tier $N+1$ (Tier 1 Parameter $\rightarrow$
  Tier 2 Algorithmic $\rightarrow$ Tier 3 Subsystem $\rightarrow$ Tier 4 First-Principles).
- **Never Halt on Closed Lists (Self-Replenishing Queue Protocol).** The target is an outcome,
  not a static checklist. When every candidate on the active list has reached a terminal outcome:
  1. The engine MUST NOT halt, yield the turn, or declare "nothing to do".
  2. The engine must immediately escalate up the abstraction ladder to **First-Principles Diagnostics**:
     - *Leakage / Degradation Forensics*: Quantify where the objective metric is lost (e.g. theoretical peak throughput vs realized p99 latency, cache hit degradation vs memory bandwidth).
     - *Suppressed Potential / Funnel Forensics*: Quantify candidate code paths, requests, or transactions that were filtered or throttled out but had positive value (missed throughput vector).
     - *Cross-Sectional / Workload Decomposition*: Decompose performance by component/subsystem/workload to isolate persistent drags vs performance drivers.
  3. Formulate 2–3 novel structural mechanisms or filter relaxations from the diagnostic data.
  4. Replenish `plans/next_moves.json` and immediately dispatch the #1 ranked move.
- **Dynamic Skill Activation & Subagent Delegation Ladder.** Never proceed with generic heuristics when
  registered domain skills exist. Prior to dispatching work on an engineering front, the engine MUST
  inspect host capabilities (`.agents/skills/`, `.opencode/skills/`, or host tools) and activate the corresponding
  skill via host tools (e.g. `skill({ id: "<skill>" })`). Exploratory sprawls (> 3 files or > 50 KB logs) MUST
  be delegated to read-only subagents:
  | Canonical Engineering Front | Target Objective / Operation | Matched Domain Skill Archetype | Assigned Subagent Persona |
  | :--- | :--- | :--- | :--- |
  | **`diagnose`** | Bottleneck profiling, latency decomposition, error clustering | `*-diagnosis`, `*-profiling`, `*-metrics` | `diagnostician` |
  | **`audit`** | Interface compliance, safety boundary checks, linting | `*-audit`, `*-lint`, `*-security` | `verifier` |
  | **`research`** | Theoretical bounds, literature/spec review, capability mining | `*-research`, `*-spec`, `*-oracle` | `synthesizer` |
  | **`improve`** | Algorithmic refactoring, caching, data structure optimization | `*-optimization`, `*-refactor`, `*-tuning` | `architect` |
  | **`harden`** | Regression defense, determinism checks, edge-case testing | `*-validation`, `*-fuzzing`, `*-testing` | `verifier` |
  | **`pipeline`** | Build system, CI matrix, receipt aggregation | `*-pipeline`, `*-ci`, `*-build` | `synthesizer` |
- **Simulation Freedom Invariant.** Documentation notes mentioning "operator-gated", "operator decision",
  or "manual approval" apply *strictly* to live production deployment. In headless research/evaluation
  mode (`eval`), the loop is **100% authorized and required** to prototype, simulate, and falsify any
  structural hypothesis without asking for human permission or yielding the turn.

## Anti-patterns (explicitly rejected)

- Random or ungrounded parameter sweeps; "try things and see".
- Adopting a change that is execution-identical (inert) or that regresses any case.
- Declaring success, or blaming the target metric, while a front is unexamined.
- Weakening an invariant, gate, or safety limit to make a metric look better.
- Producing numbers the pipeline cannot reproduce from a committed snapshot.

# RFC-0003: Teleological Target-Seeking & Self-Replenishing Queue Protocol

- **RFC Number:** 0003
- **Title:** Teleological Target-Seeking & Self-Replenishing Queue Protocol
- **Status:** Proposed Standard (Working Draft)
- **Category:** Standards Track
- **Version:** 1.0.0-draft
- **Date:** October 2026
- **Authors:** Seismael & Antigravity Advanced Agentic Engineering Team

---

## Abstract

This document defines the normative requirements for **Teleological Target-Seeking** and the **Self-Replenishing Queue Protocol** in the Open Harness Protocol (OHP). Conventional AI coding agents operate as checklist executors that halt when a predetermined prompt or list of candidate knobs is exhausted. OHP formalizes cybernetic goal-directed behavior, establishing an Expected-Value dispatch hierarchy, dynamic queue replenishment via First-Principles diagnostics, and the Simulation Freedom Invariant, ensuring autonomous continuous progress until teleological criteria are satisfied.

---

## 1. Terminology & Conformance

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in BCP 14 [RFC 2119].

**Teleology:** In the context of OHP, the property of an autonomous system whereby actions are continuously selected, evaluated, and adapted to minimize the distance between current repository performance and a declared objective predicate.

---

## 2. Motivation: The Checklist Halting Failure Mode

First-generation AI coding agents exhibit a common structural failure mode:
1. The operator asks the agent to improve a system.
2. The agent brainstorms 3–5 initial parameter tweaks or surface changes.
3. The agent tests the 3–5 items.
4. When all items are adopted or rejected, the agent halts, yields its turn, and asks the human: *"I have tested all options. What should I do next?"*

This behavior confuses **"the predefined checklist of parameter knobs is exhausted"** with **"the objective is exhausted"**. In complex engineering, parameter sweeps represent the lowest tier of optimization. The true profit and performance frontiers lie in diagnosing architectural bottlenecks, uncalled capabilities, and suppressed signals.

---

## 3. Cybernetic Target-Seeking State Machine

An OHP engine operates as a closed-loop cybernetic feedback controller:

```
                            DECLARATIVE TARGET (profile.yaml)
                                          │
                                          ▼
                             ┌─────────────────────────┐
                             │    Error Signal E(t)    │
                             │  E(t) = Target - M(S)   │
                             └────────────┬────────────┘
                                          │
                                          ▼
┌───────────────────────┐    ┌─────────────────────────┐
│ Dynamic Replenishment │    │   Dispatch Controller   │
│ First-Principles      │◄───┤   next_moves.json empty?│
│ Diagnostic Forensics  │    └────────────┬────────────┘
└───────────────────────┘                 │ NO (Pop top EV move)
                                          ▼
                             ┌─────────────────────────┐
                             │   Execute Front Step    │
                             │   (Minimal Candidate)   │
                             └────────────┬────────────┘
                                          │
                                          ▼
                             ┌─────────────────────────┐
                             │   Dual-Gate Evaluate    │
                             │   & Compound Memory     │
                             └─────────────────────────┘
```

The loop SHALL terminate IF AND ONLY IF:
1. The target boolean predicate defined in `profile.yaml` evaluates to `TRUE`; OR
2. All 12 engineering fronts have reached terminal status (`exhausted` or `covered` with certified baseline proof) and no positive-EV hypotheses can be synthesized; OR
3. The operator explicitly halts the engine via a stop file (`.agents/loop/STOP`).

---

## 4. Move Queue Dynamics (`plans/next_moves.json`)

The active hypothesis backlog MUST be maintained in `plans/next_moves.json` as a prioritized queue.

### 4.1 Expected Value (EV) Ranking Formula
Every candidate move in `next_moves.json` SHALL be prioritized according to its Expected Value:

$$\text{EV} = P(\text{success}) \times \frac{\text{Impact}}{\text{Cost}}$$

Where:
- $P(\text{success}) \in (0, 1]$: Estimated empirical probability of advancing the target without invariant breakage.
- $\text{Impact} \in [1, 10]$: Magnitude of potential improvement toward the target predicate.
- $\text{Cost} \in [1, 10]$: Verification runtime, complexity, and blast radius of the candidate diff.

### 4.2 Dispatch Priority Hierarchy
When ranking competing moves, the engine MUST adhere to the canonical priority ladder:

1. **Priority 1: Unresolved Defect or Invariant Regression (`debug`, `harden`)**
   Any known defect in `issues.jsonl` or broken assertion must be repaired before seeking performance gains.
2. **Priority 2: Uncovered Engineering Front (`audit`, `discover`, `pipeline`)**
   Ensures the codebase surface is thoroughly surveyed before optimization begins.
3. **Priority 3: Empirical Bottleneck Diagnosis (`diagnose`, `research`)**
   Diagnostic probes that measure opportunity cost, suppressed signals, or latency breakdowns.
4. **Priority 4: Structural Mechanism Diff (`improve`, `performance`)**
   Architectural refactors, algorithmic changes, and feature enhancements.
5. **Priority 5: Parameter Knob Tuning (Last)**
   Micro-parameter adjustment is permitted only after structural mechanisms are established.

---

## 5. Self-Replenishing Queue Protocol

### 5.1 Prohibition Against Halting on Empty Queues
When `plans/next_moves.json` is empty or all listed items have reached terminal outcomes, the engine **SHALL NOT halt, yield its turn, or request human guidance** if the target predicate remains unmet.

### 5.2 First-Principles Diagnostic Escalation
Upon queue exhaustion, the engine MUST automatically transition into the `diagnose` or `research` front:
- **Causal Forensics:** Decompose system loss vectors (e.g. why did 78% of potential entries fail to trigger? Which function consumes 64% of frame time?).
- **Capability Mining:** Re-examine `capabilities.md` for uncalled modules, dormant interfaces, or alternative data structures.
- **Leakage Analysis:** Quantify the gap between theoretical maximum efficiency and empirical realization.

### 5.3 Hypothesis Synthesis & Replenishment
From the diagnostic findings, the engine MUST:
1. Synthesize 2–3 novel, falsifiable structural hypotheses.
2. Insert them into `plans/next_moves.json` complete with front, rationale, and estimated EV.
3. Immediately pop the highest-EV move and dispatch the next iteration without conversational latency.

---

## 6. The Simulation Freedom Invariant

In enterprise software engineering, documentation often contains notes such as *"operator-gated"*, *"requires manual approval"*, or *"human authorization needed"*.

An OHP engine SHALL enforce the following strict boundary:
1. **Live Production vs. Headless Evaluation:** Restrictions regarding operator gates apply **strictly to live production environments** (deploying to mainnet, updating live customer databases, altering production cloud infrastructure).
2. **Unconditional Simulation Authority:** In headless evaluation (`eval` mode, test environments, simulation harnesses, backtesters), an OHP engine possesses **100% unconditional authorization** to prototype, simulate, benchmark, and falsify any candidate mechanism, formula, or architecture.
3. An engine MUST NOT pause or yield its turn in simulation on the grounds of inherited production conservatism.

---

## 7. The Unbroken In-Session Chaining Invariant (Zero Standalone Chat Yield)

In host agentic runtimes (OpenCode, Claude Code, Cursor, Antigravity):
1. **Mechanical Turn Yielding:** If an assistant turn completes generation containing only markdown/text and **zero tool calls**, the LLM provider API terminates with `finish_reason: "stop"`. The host runtime cannot differentiate between a mid-loop status update and an intentional termination; it automatically yields the turn and blocks waiting for operator input.
2. **Prohibition Against Standalone Chat Turns:** During an active loop session, an engine **SHALL NOT** emit a response consisting solely of conversational markdown without a co-emitted tool call.
3. **Mandatory Mechanical Chaining:** Every assistant turn completing an iteration step MUST simultaneously co-emit or immediately chain the tool call executing or setting up the next step:
   $$\text{Step } N \text{ (persist journal/state)} \longrightarrow \text{Read/Pop } \text{next\_moves.json} \longrightarrow \text{Dispatch Step } N+1$$
4. **Permitted Termination Conditions:** An engine SHALL emit a tool-call-free terminal turn IF AND ONLY IF:
   - The declarative target predicate in `profile.yaml` is mathematically satisfied with certified coverage; OR
   - An ephemeral sentinel file `.agents/loop/STOP` (or `.loop/STOP`) is detected on disk; OR
   - The operator explicitly typed `"stop the loop"`.

---

## 8. Auto-Compaction Resilience & Anti-Anxiety Directive

1. **Context & Budget Anxiety Prohibition:** Context window accumulation or token count **SHALL NEVER** constitute a valid justification for an engine to pause, yield the turn, or trigger a human handoff.
2. **Compaction Invariance:** Modern host runtimes execute deterministic, non-destructive context compaction. Furthermore, OHP guarantees that all critical state (active iteration, incumbent baseline, journal, coverage ledger, issues queue, and next moves) is durably anchored to the local filesystem under `.agents/loop/`.
3. **Immediate Post-Compaction Resumption:** If an automatic context compaction event occurs, the engine MUST immediately execute a tool call reading `.agents/loop/loop.json` and `.agents/loop/plans/next_moves.json`, and resume the active move without seeking human permission or waiting for chat input.

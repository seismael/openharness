# Comparative Analysis: `obra/superpowers` vs. OpenHarness (OHP)

A technical whitepaper comparing **Interactive Agent Skills** with the **Open Harness Protocol (OHP)** for autonomous, continuous, invariant-safe engineering.

---

## 1. Executive Summary

The emergence of AI coding agents has catalyzed two distinct engineering paradigms:
1. **Interactive Micro-Task Discipline (e.g., `obra/superpowers`):** A methodology designed to constrain human-in-the-loop pair programming. It forces agents to brainstorm, specify, plan in 2–5 minute increments, and apply red/green Test-Driven Development (TDD) while the human developer actively guides the session.
2. **Autonomous Teleological Closed Loops (Open Harness Protocol - OHP):** A cybernetic architecture designed for unattended, continuous systems research and development. It enables agents to operate independently for hours or days, methodically exploring codebases across 12 engineering fronts, enforcing mathematical dual-gate safety invariants, and compounding discoveries into durable disk-backed ledgers at radical token efficiency.

This document analyzes the architectural divergence between these two approaches, evaluates their trade-offs, and demonstrates how they compose into a unified two-tier agentic system.

---

## 2. Comprehensive Comparison Matrix

| Dimension | `obra/superpowers` | OpenHarness (OHP) |
| :--- | :--- | :--- |
| **Primary Mission** | Curbing "vibe coding" hallucinations during interactive development | Autonomous, non-stop optimization of systems, code, and quantitative models |
| **Operating Horizon** | 2–5 minute turns; requires continuous human prompt turn-taking | 6–12+ hours continuous unattended execution (e.g., overnight research) |
| **Autonomy Model** | Bounded checklist execution; halts when initial plan tasks are done | Teleological target-seeking; self-replenishing queue via First-Principles diagnostics |
| **Safety & Verification** | Standard red/green unit testing (TDD); git worktree branches | Mathematical Dual Gates: $\Delta\text{Metric} > 0 \land \forall I \in \text{Invariants}, \text{PASS}$ with atomic rollback |
| **Compounding Memory** | Ephemeral; stored in conversation context and commit messages | Durable disk-backed schemas: `loop.json`, `journal.jsonl`, `decisions/`, `coverage.json` |
| **Token Economics** | Unwrapped streaming of build, test, and shell logs ($5–$20/hr) | Projection wrapping + byte-static prefix caching (**$0.19 / 10.5h**, >96% cache hit rate) |
| **Cognitive Surface** | 4–6 development skills (brainstorm, spec, plan, tdd, review) | 12 canonical engineering fronts covering orientation to hardening |
| **Domain Portability** | Primarily general software feature development | Universal: software features, distributed systems latency, algorithmic trading, ML, compilers |
| **Toolchain Coupling** | Host-specific (Claude Code plugins, Cursor rules) | Universal: standard Agent Skills format, CLI harness, and MCP server |

---

## 3. Deep Architectural Differences

### 3.1 Interactive Pairing vs. Cybernetic Target-Seeking
`obra/superpowers` is built around human oversight:
- The human prompts the agent with a feature request.
- The agent brainstorms solutions, presents options, and awaits approval.
- The agent breaks work into a checklist of micro-tasks and executes them sequentially.
- When the checklist ends, the agent **halts and asks what to do next**.

In contrast, OHP implements a **cybernetic closed loop**:
- The human or CI system supplies an objective target and safety predicate via `profile.yaml`.
- The engine dispatches moves based on expected value across 12 engineering fronts.
- When all pre-listed moves are exhausted, the engine is **explicitly forbidden from halting**. It executes First-Principles diagnostic probes (e.g. signal suppression, MFE give-back, latency bottleneck flamegraphs) to discover new opportunities, replenishes `next_moves.json`, and continues uninterrupted.

```
Superpowers Flow:
Prompt ──► Brainstorm ──► Human Approval ──► Plan ──► Micro-Tasks ──► HALT

OHP Closed Loop:
Target Directive ──► Orient ──► Audit/Diagnose ──► Minimal Candidate ──► Dual-Gate Verify
       ▲                                                                       │
       │                                                                       ▼
       └─────── Replenish Queue ◄── Diagnostics ◄── Queue Exhausted? ◄─── Adopt/Revert
```

### 3.2 Verification: Standard TDD vs. Dual-Gate Mathematical Invariants
`superpowers` relies on conventional Test-Driven Development:
- Write a failing test.
- Implement minimal code to pass the test.
- Refactor and run code review.

While effective for standard CRUD applications, TDD is insufficient for complex systems:
- An algorithmic change in a quantitative model can pass unit tests while degrading net PnL across market regimes.
- A database indexing change can speed up a read query while introducing memory bloat or deadlocks under concurrency.

OHP introduces the **Dual-Gate Safety Contract**:
$$\text{Accept}(S_{\text{candidate}}) \iff \left( M(S_{\text{candidate}}) \succ M(S_{\text{champion}}) \right) \land \left( \bigwedge_{j=1}^{k} I_j(S_{\text{candidate}}) = 1 \right)$$
1. **Pre-Evaluation Git Snapshot:** Before initiating evaluation, all proposed changes are committed (`feat(candidate)`).
2. **Dual Verification:** The candidate must demonstrate primary metric improvement AND maintain 100% green pass rates across all invariant suites.
3. **Automated Rollback:** If either gate fails, the engine executes an immediate hard rollback (`git reset --hard HEAD~1`), records the failure receipt in `decisions/D-xxx.md`, and logs the attempt in `journal.jsonl`. The agent never repeats a failed hypothesis.

### 3.3 Token Economics & Production Viability
Under `superpowers`, terminal commands stream raw output into the LLM context. Running `cargo test`, `pytest`, or compilation commands adds 5,000–30,000 tokens of noisy output per turn. Within 20–30 turns, the context window saturates, triggering lossy compaction and costing $15–$50 per developer session.

OHP achieves industrial economic viability through three mechanisms:
1. **Output Projection Wrapping:** Commands suppress raw terminal output (`command | Out-Null` or `> /dev/null`) and extract only single-line scalar JSON receipts (`{"p99_latency_ms": 8.42, "tests": 1280}`). Feedback is bounded to ~150–250 tokens per turn.
2. **Context Prefix Invariance:** System instructions, repository topology, and declarative configurations remain byte-identical at the context head, maximizing prompt cache reuse (achieving **96.93% prompt cache hit rates** on DeepSeek/Claude).
3. **Empirical Result:** 10.5 hours of continuous backtesting and refactoring (132 engine turns) cost **$0.1938 total** (~$0.00147 per turn).

---

## 4. The Unified Two-Tier Architecture

`superpowers` and OHP are not mutually exclusive; they address different phases of the software lifecycle. We recommend deploying them as a unified two-tier stack:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        THE UNIFIED AGENTIC STACK                       │
├────────────────────────────────────────────────────────────────────────┤
│ TIER A: Interactive Pairing Mode (The Superpowers Suite)               │
│ • Use Case: Human sitting at keyboard brainstorming and building       │
│ • Workflow: Brainstorming, architectural specs, interactive TDD        │
│ • Grounding: Constrained by knowledge/ and invariants.md               │
├────────────────────────────────────────────────────────────────────────┤
│ TIER B: Autonomous Closed-Loop Mode (The OHP Engine)                  │
│ • Use Case: Human away from keyboard; overnight research; scheduled CI │
│ • Workflow: 12-front audit, dual-gate verification, replenishment      │
│ • Grounding: Governed by profile.yaml and durable disk ledgers         │
└────────────────────────────────────────────────────────────────────────┘
```

Both tiers share the same single source of truth in `.agents/`:
- Interactive changes in Tier A adhere to `invariants.md`.
- Autonomous discoveries in Tier B compound into `decisions/` and `journal.jsonl`, ready for human review in the morning.

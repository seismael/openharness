# Token Economy: Maximizing Performance at Lowest Token Usage

The single most critical operational constraint in autonomous agentic loops is **token efficiency**.
Every token wasted on unprojected logs, redundant directory scans, exploratory greps, or conversational chatter directly
degrades reasoning performance, pollutes context windows, and increases latency.

This reference codifies the **Six Non-Negotiable Pillars of Token Efficiency** enforced by the loop.

---

## 1. The Six Pillars of Token Economy

### Pillar 0: Deterministic Environment Manifest (`env.json`)
- **Forbidden**: Never run exploratory `grep`, `glob`, or `find` commands searching for python interpreters (`.venv/Scripts/python.exe`), test runners (`pytest`), or CLI entry points.
- **Rule**: Always consult `.agents/loop/env.json` directly.
- **Mechanism**: The manifest provides exact, unambiguous paths to the project runtime:
  ```json
  {
    "python_bin": ".venv/Scripts/python.exe",
    "test_cmd": ".venv/Scripts/pytest.exe",
    "entry_point": "python -m <package>",
    "loop_dir": ".agents/loop",
    "scratch_dir": ".agents/loop/scratch"
  }
  ```
  Eliminates 2–4 wasted discovery tool calls (1,000–2,500 tokens) on every loop turn.

### Pillar 1: Index-First Navigation (< 400 tokens)
- **Forbidden**: Never run open-ended tree scans (`find .`, `ls -R`, recursive directory listings) or ingest entire documentation suites.
- **Rule**: Always start by reading `.agents/loop/knowledge/index.md` (or fallback `.loop/knowledge/index.md`).
- **Mechanism**: The index is an Obsidian-compatible Markdown document strictly bounded to < 400 tokens.
  It maps all repository concepts directly to specific leaf documents (`invariants.md`, `capabilities.md`,
  `baselines.md`, `decisions/log.md`). The agent navigates directly to the exact file required without exploratory token burn.

### Pillar 2: Byte-Bounded Context Projections (≤ 2,500 bytes)
- **Forbidden**: Never stream raw logs, benchmark traces, trade tick series, or multi-megabyte JSON into conversation context.
- **Rule**: Consume only pre-projected, byte-bounded diagnostic views capped at **2,500 bytes per artifact**.
- **Mechanism**: Use canonical pipeline commands that emit summarized projections (e.g. `diagnostic packet`,
  `cargo bench -- --output-format=json | jq ...`, `pytest -q --tb=short`). When reading files, view only targeted line ranges
  or use `grep -n -C 3` rather than whole-file ingestion.

### Pillar 3: Sandboxed Scratchpad (`.agents/loop/scratch/` and `.agents/loop/scripts/`)
- **Forbidden**: Never litter the project root or source directories with temporary extraction scripts (`_tmp_*.py`, `scratch.py`).
- **Rule**: Any temporary scratch script or data file must reside strictly inside `.agents/loop/scratch/` (or fallback `.loop/scratch/`). Deterministic, reusable
  diagnostic utilities must reside in `.agents/loop/scripts/`.
- **Mechanism**: Keeps the project tree 100% clean, protects git worktrees from pollution, and prevents dirty-tree build failures.

### Pillar 4: Subagent Air-Gapping
- **Forbidden**: Never parse massive compiler outputs, backtest logs, or thousands of AST nodes in the main director session.
- **Rule**: Delegate high-volume analysis to read-only subagents hosted in `.agents/subagents/`.
- **Mechanism**: Subagents ingest large outputs, isolate root causes, and return strictly bounded summaries (≤ 2,500 bytes)
  containing only findings, exact `file:line` locations, and quantitative metrics. The main context window stays small and fast.

### Pillar 5: Frontier Memory & Zero Repetition
- **Forbidden**: Never re-test parameter ranges, filters, or architectural ideas that were already evaluated and rejected.
- **Rule**: In the Orient phase, always consult the `do_not_repeat` registry in `loop.json` and `knowledge/decisions/log.md`.
- **Mechanism**: Once an economic frontier is proven closed or exhausted, it is recorded with its mathematical bound.
  The dispatch ladder immediately prunes it from future consideration.

---

## 2. Ultra-Lean Dynamic Step Projections (< 500 Tokens)

When driving loop steps across sessions or multi-step runners, avoid repeating hundreds of lines of static instructional boilerplate.
Instead, use an **ultra-lean dynamic projection diff**:

```markdown
# Autonomous Loop Step {step_number}
**Target:** {target_summary}
**Active Move:** {current_move_title} (Plan: .agents/loop/plans/next_moves.json)
**Previous Step:** {last_step_status} ({last_step_summary})
**Environment:** Use `.agents/loop/env.json` for paths. Consult `.agents/loop/knowledge/index.md`.
Execute sequential thinking in session. Verify rigorously before committing.
```

- **Tail-Bounded Journal Injection**: Never load the entire `journal.jsonl`. Inject only the last **2 step summaries** ($\le 200$ tokens).
- **Prompt Size Reduction**: Reduces per-step prompt size from ~3,200 tokens to under 500 tokens (**> 80% prompt reduction**).

---

## 3. Iteration Token Budget

A well-architected loop iteration follows a strict token budget:

| Phase | Target Token Consumption | Actions |
| :--- | :--- | :--- |
| **0. Manifest & Orient** | 200 – 400 tokens | Consult `env.json` + `loop.json` + `index.md` + last 2 journal entries. |
| **1. Dispatch** | 150 – 300 tokens | Evaluate priority ladder, select single next move. |
| **2. Diagnose** | 400 – 800 tokens | Ingest bounded diagnostic projection (≤ 2,500 bytes). |
| **3. Candidate** | 300 – 600 tokens | Formulate minimal diff, commit pre-evaluation snapshot. |
| **4. Evaluate & Gate** | 400 – 800 tokens | Run evaluator headless; consume bounded pass/fail receipts. |
| **5. Compound & Recur** | 150 – 300 tokens | Update decisions log, append 1 journal line, recur. |
| **Total per Iteration** | **1,600 – 3,200 tokens** | **Over 10x more cost-efficient than ad-hoc chat iterations.** |

---

## 4. Anti-Patterns (Immediate Disqualification)

1. Outputting conversational pleasantries ("Sure! I will now run tests...", "Here is what I've done so far...").
2. Dumping hundreds of lines of passing test outputs into context.
3. Reading whole multi-thousand-line source files when a 20-line function edit was needed.
4. Running exploratory `find` or `grep` commands across virtual environments.
5. Writing throwaway scripts in workspace root to parse JSON files.
6. Re-running evaluations that already failed without altering code mechanism or data.

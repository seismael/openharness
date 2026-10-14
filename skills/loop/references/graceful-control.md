# Graceful Control: Stop, Pause, and Seamless Resume

The loop is fully autonomous, but remains completely under operator control at all times.
There is **no daemon, background PID worker, or detached runner**. The agent is the engine,
running in-session. This document defines the protocol for stopping gracefully, pausing, and
resuming instantly from durable on-disk state.

---

## 1. Graceful Stop Mechanisms

The loop can be stopped at any time through either of two standard mechanisms:

### A. Interactive Natural Language Directive
The user can type any clear stop directive in the active conversation:
- `"stop the loop"`
- `"pause the loop"`
- `"stop"` or `"pause"`
- `"halt and report status"`

When the agent receives this message, it **does not abandon work midway or corrupt state**. It:
1. Completes or safely aborts the active atomic step:
   - If an evaluation is running, records the outcome or cleanly reverts the candidate working tree to baseline.
   - If the candidate passed dual gates, commits and adopts before halting.
2. Updates `.loop/loop.json`:
   - `status: "STOPPED"`
   - Records `stopped_at_step`, `last_front`, `last_axis`, and `resume_pointer`.
3. Appends a record to `.loop/journal.jsonl`:
   - `{step: N, front: "<front>", axis: "<axis>", action: "stop", outcome: "STOPPED_BY_OPERATOR", ts: "<ISO>"}`
4. Emits a clean, 3-line status summary and ends the turn:
   ```
   [LOOP STOPPED] Target: "<target>"
   Status: Safely paused at Step N on front: <front> (axis: <axis>).
   Resume: Run /loop or /loop continue to resume immediately.
   ```

### B. Filesystem Sentinel (`.loop/STOP`)
External scripts, test harnesses, or tools can stop the loop by creating a sentinel file:
```
touch .loop/STOP
```
or in PowerShell:
```powershell
New-Item -Path ".loop\STOP" -ItemType File -Force
```
Between every step, the in-session loop checks for the presence of `.loop/STOP`. If detected:
- The agent halts immediately before dispatching the next move.
- Sets `.loop/loop.json` status to `STOPPED`.
- Flushes the journal.
- Cleans up `.loop/STOP` upon confirmed stop.
- Yields cleanly to the user.

---

## 2. Seamless Resume Protocol

Because all loop cognition, journal entries, frontier status, and plans live inside **`.loop/`**,
resuming requires zero memory of the prior session context.

### Invocation:
The operator resumes the loop simply by invoking:
```
/loop
```
or:
```
/loop continue
```
or with a refined/new target:
```
/loop "<refined target>"
```

### Resume Mechanics:
1. **Read State**: The agent reads `.loop/loop.json`.
2. **Verify Clean Worktree**: Confirms `git status` is clean at the incumbent baseline. If an abandoned
   candidate snapshot from a crashed run exists, it reverts it to the incumbent baseline.
3. **Re-Read Frontiers & Ledger**: Loads `.loop/coverage.json` and the last 10 lines of `.loop/journal.jsonl`.
4. **Remove Sentinel**: Removes `.loop/STOP` if present.
5. **Update State**: Sets `.loop/loop.json` `status: "ACTIVE"`.
6. **Dispatch Next Atomic Move**: Picks up from the highest-priority move on the dispatch ladder
   (`next_moves.json`) without re-sweeping exhausted axes.

---

## 3. Checkpoint & State Safety Guarantees

| Invariant | Guarantee |
| :--- | :--- |
| **Atomic Step Integrity** | Every step is a single commit or revert. Stopping never leaves broken syntax or uncommitted diffs. |
| **Zero Frontier Amnesia** | Every tested hypothesis and its empirical outcome are recorded in `journal.jsonl` and `decisions/log.md`. Resuming never repeats exhausted parameters. |
| **Compaction Immunity** | Even if host session memory is summarized or truncated, reading `.loop/loop.json` immediately restores 100% operational context. |
| **Zero Background Zombies** | Since all execution is in-session, stopping the session terminates all tool calls cleanly. There are no dangling detached background processes. |

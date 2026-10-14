# Agent Ecosystem: On-Demand Specialists and Subagents

The optimization loop operates using the **Director-Specialist Pattern**.
The main in-session loop acts as the **Director** (the sole writer to the project codebase and git).
To preserve tokens and ensure deep domain rigor, the Director delegates bounded analysis to
**Specialists** hosted under **`.agents/`**.

---

## 1. Directory Structure: `.agents/`

```
<project-root>/
└── .agents/
    ├── skills/                  # Installed portable skills
    │   ├── loop/                # The in-session loop engine
    │   ├── audit/               # Domain risk and codebase audit
    │   ├── knowledge/           # Indexed wiki manager
    │   ├── characterize/        # Agent setup tailoring
    │   └── enhance/             # Workflow and efficiency tuner
    └── subagents/               # Specialized personas (built on demand)
        ├── diagnostician.yaml   # Causal root-cause and bottleneck specialist
        ├── architect.yaml       # Structural design and invariant specialist
        ├── verifier.yaml        # Dual-gate and regression verification specialist
        └── synthesizer.yaml     # Log digestion and bounded projection specialist
```

---

## 2. Standard Specialist Personas

When tackling complex optimization, the loop deploys or invokes standard specialized personas:

### A. Diagnostician (`.agents/subagents/diagnostician.yaml`)
- **Role**: Causal Root-Cause & Profiling Specialist.
- **Tools**: Read-only (file viewing, grep, benchmark/profiler analysis).
- **Mandate**: Localizes the single dominant component of drag, latency, memory leak, or opportunity gap.
- **Contract**: Never suggests random code changes; produces a falsifiable hypothesis with exact `file:line` citations.

### B. Architect (`.agents/subagents/architect.yaml`)
- **Role**: Structural Design & Invariant Specialist.
- **Tools**: Read-only codebase synthesis and architecture modeling.
- **Mandate**: Formulates minimal, decoupled mechanism changes (not just parameter tweaks). Ensures zero violations of project architectural boundaries and invariants.
- **Contract**: Emits a targeted, atomic candidate plan specifying the minimal diff required.

### C. Verifier (`.agents/subagents/verifier.yaml`)
- **Role**: Dual-Gate Verification & Regression Specialist.
- **Tools**: Read-only test execution and artifact inspection.
- **Mandate**: Validates both Gate A (primary metric gain) and Gate B (zero invariant regression).
- **Contract**: Validates whether test fixtures were updated nominally or if real regressions occurred.

### D. Synthesizer (`.agents/subagents/synthesizer.yaml`)
- **Role**: Log Digestion & Bounded Projection Specialist.
- **Tools**: Read-only log parsing and AST summarization.
- **Mandate**: Consumes multi-megabyte evaluator outputs, trace files, or compiler errors and boils them down to a strictly bounded projection (≤ 2,500 bytes).
- **Contract**: Never dumps raw logs into conversation context.

---

## 3. Dynamic On-Demand Subagent Generation

When the loop encounters a novel project domain (e.g. GPU kernel optimization, distributed consensus,
smart contract formal verification), it dynamically builds a new specialist under `.agents/subagents/`:

1. **Detect Need**: A sub-axis in `.loop/coverage.json` requires domain-specific tooling or heavy AST inspection.
2. **Materialize Persona**: The loop writes `.agents/subagents/<specialist>.yaml` defining:
   - System prompt with domain axioms and boundary constraints.
   - Required read-only tools.
   - Strict return format contract (≤ 2,500 bytes with line references).
3. **Invoke across Harnesses**:
   - **Antigravity / Generic**:
     ```yaml
     Subagent:
       TypeName: research
       Role: "Causal Forensics Specialist"
       Prompt: "Analyze missed trades in .agents/loop/scratch/gap.json. Identify top 3 suppressions with path:line."
     ```
   - **OpenCode**:
     ```javascript
     subagent({
       agent: "diagnostician", // or "researcher", "verifier", "synthesizer"
       description: "Analyze missed trades in gap.json",
       prompt: "OBJECTIVE: Produce <= 20 lines identifying top 3 suppressions with path:line evidence. Read-only."
     })
     ```
   - **Claude Code / MCP**:
     Invoke `run_command` via isolated child agent or MCP subagent server.
4. **Consume Bounded Output**: The main director ingests only the compact summary (<= 2,500 bytes) and applies the change.

---

## 4. Director-Only Write Invariant

To guarantee absolute determinism and prevent race conditions:
- **Subagents are strictly read-only analysts.** They never edit files, stage commits, or push branches.
- **The main session Director is the sole writer.** It reviews evidence from specialists, applies the minimal surgical diff, commits the pre-evaluation snapshot, and executes adoption.
- **Context Protection Guarantee:** Heavy file scans (> 3 files) and multi-megabyte artifact parsing (> 50 KB) MUST be executed in subagents, shielding the Director's context window from explosive token expansion.

# Audit method

## Domain reasoning before recommendations

Build a compact model of the project: whose problem it solves, which outcomes matter, what constraints are intrinsic, what users actually adopt, and which requirements its implementation claims to satisfy. Read implementation and tests alongside the README; do not mistake marketing claims for verified behavior. If goals are missing, infer cautiously, record the inference, and ask only when competing interpretations materially alter a finding.

For unfamiliar or high-consequence domains, establish vocabulary, invariants, failure costs, and authoritative sources before recommending changes. Examples: distinguish causal evaluation from future-data leakage in offline simulation; retry from exactly-once effects in distributed systems; crash consistency from application consistency in storage. These are examples of reasoning depth, not a fixed list of supported domains. Do not claim expertise based on role-play alone.

**Constraint Realism and Professional Expertise**: Never propose bypassing, canceling, or ignoring fundamental domain constraints (e.g., structural operating costs, network latency, hardware limits, mandatory security boundaries) simply to make a symptom go away. Findings must be deeply thought out and goal-oriented. Solutions must logically resolve the root cause *within* the harsh reality of the production environment. A "solution" that avoids or removes a mandatory constraint is invalid.

**Autonomous Project Reconnaissance & Data Discovery**: The auditor operates in completely unknown environments and must never rely on hardcoded paths, pre-configured file names, or assumed directory layouts. Upon entering a project, the auditor must autonomously map the environment:
1. *Manifests & Entry Points*: Discover build and package descriptors (`Cargo.toml`, `pyproject.toml`, `package.json`, `go.mod`, `pom.xml`, `CMakeLists.txt`, `Makefile`) to identify runtime, language, external dependencies, and main entry points.
2. *Source & Topology*: Locate primary source roots (`src/`, `lib/`, `app/`, `internal/`), public interfaces, configuration files (`config/`, `etc/`, `.env*`), and architecture documentation (`docs/`, `spec/`, `README*`).
3. *Runtime Evidence & Data Lakes*: Locate operational artifacts, execution logs, diagnostics, telemetry, performance benchmarks, and data stores (`logs/`, `data/`, `reports/`, `artifacts/`, hidden run directories like `.<project>/`).
4. *Code vs Data Cross-Referencing*: Never audit source code in isolation. Cross-reference runtime logs, error counters, performance profiles, and telemetry outputs against code logic to mathematically and empirically prove failure hypotheses before declaring a root cause.

**Root-Cause Engineering over Parameter Bypasses**: Never suggest simple configuration tweaks, threshold adjustments, or safety overrides (bypasses) as primary solutions. A bypass masks the symptom. You must deeply investigate the code and behavioral data to find the *structural* or *algorithmic* root cause. Your recommendations must represent significant, deeply thought-out engineering solutions (e.g., redesigning an I/O pipeline, eliminating a concurrency bottleneck, rewriting state synchronization) rather than merely tuning a configuration variable to make an error disappear.

**Cross-Boundary Causality**: Never isolate a failure to a single component without verifying its downstream contracts. If a component (e.g., an ingestion pipeline, a scheduler, an optimizer) fails to achieve its intended outcome, mathematically trace its data flow through downstream boundaries (e.g., queue managers, rate limiters, storage engines, network adapters) to find the exact point of constraint mismatch. Expert auditors resolve systemic contradictions, not just local symptoms.

**Empirical vs Nominal Fidelity**: Compare nominal system design (e.g., designed throughput, SLA targets, theoretical computational complexity, algorithmic bounds) against empirical realization data in telemetry, benchmark outputs, and execution profiles. When empirical performance drastically diverges from theoretical targets (e.g., an expected $O(N)$ pipeline collapsing to $O(N^2)$, or expected low-latency delivery degraded by hidden queue serialization), rigorously audit the lifecycle execution mechanics and boundary handoffs to eliminate the structural biases destroying system performance.

**Strict Output Token Economy & Zero-Chatter Protocol**: The auditor must deliver the highest density of useful findings per generated token:
1. *No Conversational Fluff*: Strictly eliminate conversational filler, polite preambles ("Great question!", "That was a fantastic exercise!"), restatements of user input, self-congratulatory remarks, and meta-commentary.
2. *Direct Information Delivery*: Begin responses immediately with the dense finding, exact source citation (file, line number, symbol), and empirical proof.
3. *High Signal-to-Noise Ratio*: Use concise markdown tables, bullet points, and surgical code diffs. Avoid explanatory prose where structured facts suffice.
4. *Targeted Input Slices*: Use precise search tools (`grep`, bounded line inspection) rather than loading entire source or data files into context. Never stream multi-megabyte logs or raw datasets.

**Pre-Evaluation Snapshot Protocol**: Before launching any long-running test execution, simulation, historical backtest, or benchmark process, the agent MUST guarantee that the repository working tree is in an immutable, committed, or cleanly stashed state. Modifying source files or configuration while an asynchronous evaluation is running in the background causes runtime source identity drift and publication failures. Always commit or stash candidate modifications before kicking off background evaluators.

**Synthetic Fixture Realignment vs. Runtime Defects**: When a verified architectural or domain improvement is applied, legacy synthetic unit tests that hardcode obsolete or pre-improvement behavior may fail. The auditor must explicitly distinguish between:
1. *Stale Synthetic Fixtures*: Tests asserting superseded nominal values or outdated mock states. These fixtures MUST be cleanly realigned to the improved canonical behavior in the same atomic commit.
2. *True Runtime Regressions*: Unintended breaks in downstream system invariants or interface contracts.

**Dual-Gate Verification (Objective Metric + Invariant Soundness)**: Every proposed optimization or remediation must pass two orthogonal gates before adoption:
1. *Objective Metric Gate*: Demonstrable empirical improvement on primary target metrics (e.g., higher throughput, reduced latency, improved payoff ratio, or positive net gain).
2. *Invariant Soundness Gate*: Zero violation of fundamental system invariants (e.g., conservation laws, double-entry balance, clock monotonicity, absence of race conditions, and zero unhandled errors). Never promote an apparent metric gain achieved by corrupting system invariants.

Separate product value, architectural fitness, and implementation correctness. A correct implementation can solve the wrong problem; a valuable concept can have unacceptable defects. An established alternative is neither automatic disqualification nor proof that rebuilding it adds value. Compare observable capabilities, integration burden, operational cost, maturity, and unmet user needs. Label adoption and commercial claims as hypotheses without user/customer evidence.

## Coverage map

Create project-specific coverage entries under these applicable domains; subdivide large areas by subsystem or flow. For every entry record evidence/basis, scope, status and next step. `reviewed` means the stated scope was examined, not that every defect was excluded. An inventory or file listing alone is not review. Use `not_applicable` with a reason; use `unreviewed`, `partial`, or `blocked` for gaps.

| Domain | Questions to investigate |
|---|---|
| Purpose and domain fitness | Do actual workflows deliver the promised outcome? Are critical capabilities absent? Do assumptions, metrics, math and benchmarks fit the real domain? Is a simpler existing approach materially better? |
| Architecture and boundaries | Are responsibilities, dependencies, contracts, state ownership and extension boundaries coherent? Where do coupling, duplication or abstractions obstruct actual requirements? |
| Functional correctness | Trace complete success/failure paths, boundaries, null/empty values, units, ordering, parsing, numerical stability, resource lifetime, serialization and determinism. |
| Data and persistence | Check schema invariants, transactions, constraints, idempotency, deletion, backup/restore, retention, version compatibility and real migration needs. |
| Concurrency and distributed behavior | Check races, cancellation, partial failure, retries, timeouts, duplicate effects, consistency, backpressure, ordering and recovery. |
| Security and privacy | Trace trust boundaries, authorization, tenant separation, input handling, secrets, dependency risks, data exposure and abuse limits. Verify context and exploitability before severity claims. |
| Reliability and operations | Check startup/shutdown, configuration validation, health signals, observability, actionable errors, incident diagnosis, failure isolation and recovery drills. |
| Performance and economics | Identify dominant CPU, memory, I/O, network, model/token and latency costs; distinguish measured bottlenecks from guesses. Include cumulative/repeated work and resource bounds. |
| Interfaces and user experience | Check API/CLI/UI contracts, accessibility where relevant, predictable errors, discoverability, defaults, interoperability and documentation examples. |
| Tests and evidence | Do tests check meaningful outcomes and failure modes? Are fixtures representative and independent of implementation? Can quality/performance claims be reproduced? |
| Build, release and supply chain | Check dependency pinning, reproducibility, platforms, artifacts, packaging, CI coverage, release procedures, licensing and maintenance ownership. |
| Maintainability and alignment | Check dead paths, inconsistent naming/versioning/configuration/docs, accidental complexity, missed callers and small bugs. Distinguish a demonstrated inconsistency from personal style. |

Add domain-specific areas as needed; do not force irrelevant categories into findings. Thoroughness requires reading the implicated code, not outputting boilerplate recommendations for every row.

## Investigation passes

1. Map repository and end-to-end flows; comprehensively scan local project environments including `code` directories, `docs`, and `data`/output folders to note unknown boundaries, external systems, and generated evidence.
2. Cross-reference code logic against generated local data (e.g., logs, matrix case outputs, telemetry) to mathematically or empirically prove failure hypotheses. A finding is only "significant" if it is consistently verifiable across both the codebase and the actual data outputs.
3. Inspect component contracts, edge cases and cross-cutting behavior. Look for related occurrences of confirmed root causes.
4. Check tests, examples, docs, packaging and low-level alignment against actual behavior.
5. Reconcile alternatives, dependent findings, risk tradeoffs and coverage gaps. Do not re-run broad checks without a concrete remaining question.

Use static inspection first where execution would add little. Inspect scripts before invoking them; a repository may execute arbitrary hooks in build/test/install steps. Running tests is allowed only within current authority and a suitable isolated environment, without production credentials or external side effects. If the environment cannot reproduce a failure, record the limitation rather than inventing a result.

## Evidence and classification

A useful finding contains a violated contract or opportunity, precise evidence, causal explanation, impact, counterevidence considered and a feasible response. Prefer commit permalinks and stable symbols; line numbers alone drift. Preserve an exact safe repro, expected/actual outcome and affected versions. Never include secrets or exploitable private details in a public audit; record a sanitized finding and use an authorized private channel when necessary.

| Factor | Meaning |
|---|---|
| Kind | `defect`: contract violated; `risk`: credible failure exposure; `opportunity`: optional improvement; `alignment`: verifiable inconsistency; `question`: unresolved requirement or diagnosis. |
| Severity | `critical`: catastrophic supported impact; `high`: substantial loss/core failure; `medium`: meaningful constrained degradation; `low`: limited impact; `info`: observation/opportunity with no established harm. |
| Priority | `P0`: immediate response; `P1`: next implementation tranche; `P2`: scheduled follow-up; `P3`: optional/later. Explain urgency separately from severity. |
| Confidence | `confirmed`: reproduced or conclusively traced against a known contract; `supported`: strong evidence with explicit limits; `hypothesis`: plausible but not sufficiently established. |
| Other factors | Affected users/flows, likelihood and exposure, reach, benefit, estimated effort range, change/recovery risk, prerequisites and time constraints. Use unknown when evidence is missing. |

A severe hypothetical impact does not justify an urgent rewrite by itself. Preserve potentially serious risk while prioritizing the smallest useful validation. A low-severity issue may be urgent when it blocks a release; record why. Do not assign a vulnerability score, savings percentage, market claim or assurance rating without the needed evidence.

For major redesigns, compare retain/current + targeted fixes, incremental refactoring, replacement, and removing the capability when credible. Evaluate transition cost, data/API compatibility, operating cost and reversibility. Recommend a dramatic change only when its supported benefit justifies its total cost. Record what evidence could reverse the recommendation.

## Cost controls

Search before reading; retrieve relevant slices plus enough context to avoid false positives. When inspecting `data` or logs, heavily prioritize `grep`, file previews, or targeted SQL/jq queries over reading entire files. Token efficiency and performance are top priorities; never load unbounded data files into context. Cache the domain brief, source baseline, coverage, evidence locators, decisions and findings. Load only the next packet and prerequisite evidence on continuation. Avoid redundant assistant-written summaries of existing records. Favor a single coordinator and limited domain delegation over agents each reading the full tree.

Give an early concrete finding or coverage result; do not consume the entire budget before producing value. Checkpoint pending work honestly. Respect a user's requested full depth: bounded batches accumulate coverage and must never be described as a complete audit until the recorded scope is complete.

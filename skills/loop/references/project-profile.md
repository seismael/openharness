# Project Profile: The Agnostic Seam

Everything project-specific lives in one declarative file, `docs/knowledge/profile.yaml`.
The loop engine and its cognition are identical for every repository; the profile tells
them *what to optimize, what to examine, how to run it, and when to stop*. This is what
makes the loop generically and agnostically reusable without touching engine code.

A ready-to-edit copy is at [profile.template.yaml](../assets/templates/profile.template.yaml).
Shape and semantics:

```yaml
schema: loop.profile.v1
project: <name>
target: "<one-sentence target description the loop is working on / optimizing>"
metric: "<the objective scalar/vector and how to read it>"
predicate: "<the success predicate, if any>"        # optional; enables loop-completion
modes: [eval]                                     # allowed run modes; never a forbidden one
paths:
  loop: .loop                                  # loop runtime, state, plans, scratch, and wiki root
  agents: .agents                              # native skills and on-demand subagent personas
  coverage: .loop/coverage.json
  knowledge: .loop/knowledge
boundaries:                                       # the fixed safety envelope
  - "<invariant the loop must never weaken>"
fronts:                                           # coverage surface (see front-taxonomy)
  debug:
    required: true
    sub_axes: [a, b, ...]
  improve:
    required: true
    sub_axes: [entry, exit, risk, cost, ...]
pipeline:                                         # see pipeline-contract
  - {id: evaluate, kind: evaluate, command: "<cli>", artifact: "<path>"}
gates:                                            # see below
  objective: "<how a candidate improves the target>"
  invariants: "<the test/lint commands that must stay green>"
completion:
  rule: "<target criteria met | coverage complete | budget>"
  require_coverage: true
  require_delivery: true                          # clean tree, HEAD == origin
```

## Field semantics

- **`target` / `metric` / `predicate`** — the loop optimizes `metric` toward `target`; if `predicate` is present
  the host may declare `completed` when it is met *and* coverage is complete.
- **`paths`** — canonical paths for loop operation:
  - `loop`: standard `.loop` directory holding state (`loop.json`), plans, knowledge wiki, scratch, and scripts.
  - `agents`: standard `.agents` directory holding installed skills and on-demand specialized personas (`subagents/`).
  - `coverage`: breadth guarantee ledger (default `.loop/coverage.json`).
  - `knowledge`: indexed project wiki (default `.loop/knowledge`).
- **`modes`** — the allowed run modes. The engine must refuse anything outside them; a
  profile never lists a forbidden mode.
- **`boundaries`** — the fixed envelope (determinism, safety, correctness). The loop may
  explore any direction *inside* it; it never weakens an item here.
- **`fronts`** — the coverage surface. `required: false` bounds a front out of the
  completion gate with a reason. Sub-axis names are the project's own.
- **`pipeline` / `gates`** — how work is executed and verified (see
  [pipeline-contract.md](pipeline-contract.md)).
- **`completion`** — when the loop may stop: target criteria met, coverage complete, or budget.

## Rules

- **One seam.** No project detail belongs in the engine. If the engine needs a new knob,
  add it to the profile schema, not to engine code.
- **Honest.** Every command must be real and runnable; never invent a capability (fall
  back to `discover`).
- **Validated.** The knowledge validator checks the profile's shape and that every front
  sub-axis and pipeline id is non-empty and unique.

---

## Multi-Ecosystem Examples (True Domain Agnosticism)

### 1. Rust Systems Service (`Cargo.toml`)
```yaml
schema: loop.profile.v1
project: "hyper-cache"
target: "Reduce P99 cache lookup latency under 100 microseconds"
metric: "cargo bench latency in us"
predicate: "P99 < 100.0 AND throughput > 1_000_000"
modes: [dev]
paths:
  loop: ".loop"
  agents: ".agents"
  coverage: ".loop/coverage.json"
  knowledge: ".loop/knowledge"
boundaries:
  - "zero unsafe code without explicit audit"
  - "no memory leaks"
fronts:
  orient: {required: true}
  diagnose: {required: true, sub_axes: [lock_contention, cache_misses]}
  improve: {required: true, sub_axes: [data_layout, lock_free_queue, inlining]}
  harden: {required: true}
pipeline:
  - {id: evaluate, kind: evaluate, command: "cargo bench --bench lookup", artifact: "target/criterion/report.json"}
  - {id: diagnose, kind: diagnose, command: "cargo flamegraph --bench lookup", artifact: "flamegraph.svg"}
gates:
  objective: "cargo bench P99 latency strictly decreases"
  invariants: "cargo test && cargo clippy -- -D warnings"
completion:
  rule: "target criteria met OR budget"
```

### 2. Go Distributed Microservice (`go.mod`)
```yaml
schema: loop.profile.v1
project: "order-router"
target: "Eliminate memory allocation overhead in message dispatch"
metric: "allocs/op and B/op in dispatch benchmark"
predicate: "allocs/op == 0"
modes: [dev]
paths:
  loop: ".loop"
  agents: ".agents"
  coverage: ".loop/coverage.json"
  knowledge: ".loop/knowledge"
boundaries:
  - "goroutine leak free"
  - "race detector clean"
fronts:
  orient: {required: true}
  diagnose: {required: true, sub_axes: [heap_escapes, buffer_realloc]}
  improve: {required: true, sub_axes: [sync_pool, slice_prealloc, zero_copy]}
  harden: {required: true}
pipeline:
  - {id: evaluate, kind: evaluate, command: "go test -bench=BenchmarkDispatch -benchmem", artifact: "bench.txt"}
  - {id: diagnose, kind: diagnose, command: "go test -gcflags='-m' ./pkg/dispatch", artifact: "escapes.txt"}
gates:
  objective: "allocs/op strictly decreases"
  invariants: "go test -race ./... && golangci-lint run"
completion:
  rule: "target criteria met OR budget"
```

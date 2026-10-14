# Pipeline Contract: One Canonical Path End to End

The loop never hand-rolls analysis. Every step runs the **project's declared pipeline** —
an ordered set of stages, each with an exact command, the artifact it produces, and the
gate it must pass. This keeps evidence reproducible, prevents "mistaken data or
misleading info", and lets any front (audit, debug, improve, performance) plug into the
same spine.

## Stage schema (in the profile)

```yaml
pipeline:
  - id: acquire          # stable id
    kind: acquire        # acquire | evidence | evaluate | diagnose | experiment | record | view
    command: "<exact CLI invocation>"
    artifact: "<path produced>"
    gate: "<how to know it succeeded>"   # optional
```

## Kinds

| Kind | Purpose | Typical stage |
| :--- | :--- | :--- |
| `acquire` | Ensure inputs exist and are verified | data status / ingest |
| `evidence` | Produce ground-truth comparison data | oracle / reference evidence |
| `evaluate` | Run the system under test deterministically | eval / benchmark |
| `diagnose` | Localize the gap from artifacts | gap / funnel / profile |
| `experiment` | Apply a bounded candidate and evaluate it across cells | batch eval |
| `record` | Persist the decision and lineage | record / decision log |
| `view` | Read-only rollups over recorded evidence | matrix / report |

## Rules

- **Declared, not invented.** If a needed stage does not exist, that is a `pipeline` or
  `discover` front finding — record it and extend the profile, never improvise a script.
- **Byte-bounded projections.** Consume pre-projected, size-capped views; do not stream
  raw logs or recompute heavy analytics inline.
- **Snapshot before long stages.** Commit candidate changes before any evaluation so its
  artifact is reproducible and collision-free.
- **Gates are mechanical.** A stage passes only when its `gate` command/test passes; the
  objective and invariant gates of the [loop protocol](loop-protocol.md) are evaluated
  only over pipeline-produced evidence.
- **Standard Toolchain Compatibility**: The pipeline command can be ANY standard shell invocation
  available in the target environment (e.g. `cargo bench`, `go test -bench=.`, `pytest --benchmark-only`,
  `npm test`, `make`). A repository does NOT need custom diagnostic CLI commands; standard tools
  redirecting bounded output to an artifact file fulfill the contract completely.
- **Traceability.** Every adopted change cites the pipeline artifact (run id / path) that
  justified it.

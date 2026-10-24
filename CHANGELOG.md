# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `openharness context`: a deterministic context budget (RFC-0017) that splits
  enabled tokens into `resident`, `loadable`, and `executable` layers, reports
  per-kind totals, the largest components, one named lever per component, and
  headroom against every declared budget. `--check` gates on an exceeded budget
  and `--format text` prints a human projection.
- `context.schema.json`: the normative context-budget receipt contract.
- `py.typed`: the package now ships inline type information.

### Changed

- Audit, lock, plan, and report share one measurement pass. Each declared file
  is read once as exact bytes; the fingerprint is computed from those same
  hashes instead of re-reading the tree.
- `report --execute` accepts `--workdir` and hashes the same declarations it
  evaluates.

### Fixed

- `cases --only` now filters in dry-run mode and rejects unknown ids instead of
  silently ignoring the selection.
- `report --execute` validates the working directory instead of failing deep in
  the runner.
- Declaration paths outside the manifest directory stay relative in the lock
  (RFC-0016 §5).
- `select` writes `selection.json` and `mapping.json` atomically.
- Every bounded receipt is now hard-capped at 2500 bytes: a hostile payload can
  no longer exceed the limit through an unshrunk projection.
- Platform-dependent tests no longer skip. Symlink and POSIX-mode preconditions
  are simulated deterministically, so the whole suite runs on every OS.

## [0.2.0] - 2026-10-24

### Added

- A single `openharness` command with twelve subcommands: `init`, `lock`,
  `plan`, `audit`, `verify`, `select`, `cases`, `telemetry`, `inventory`,
  `failures`, `policy`, and `report`.
- `harness.lock`: a content-addressed lockfile covering the harness
  fingerprint, per-component file hashes and token estimates, budget, and the
  hashes of the policy, cases, and requirements declarations (RFC-0016).
- `openharness plan`: file-level drift attribution (`~` modified, `+` added,
  `-` removed, declaration changes) with `--check` for CI.
- `openharness init`: zero-config discovery of `AGENTS.md`, `CLAUDE.md`,
  host instruction files, skills, commands, subagents, scripts, MCP surfaces,
  policy, and memory. It never overwrites an existing manifest.
- `openharness report`: one composed document in JSON, Markdown, SARIF 2.1.0,
  or JUnit XML, with an optional `--execute` for declared cases.
- A composite GitHub Action and a PyPI release workflow with OIDC trusted
  publishing and build provenance.
- Golden command snapshots (`tests/golden`) that freeze the byte-level output
  of every command before and after the package refactor.
- A 64-character harness fingerprint remains the join key across audit,
  inventory, cases, journal verification, lock, and report.

### Changed

- The eight protocol commands are now thin compatibility shims over the
  `openharness` package. All existing script paths keep working; the shims will
  be removed at 2.0.
- The unified CLI uses one exit-code contract: `0` clean, `1` findings or
  drift, `2` usage or invalid input, `3` ask.
- The repository is linted with Ruff, type-checked with mypy, tested with
  pytest, and measured for coverage.
- Documentation is reorganised around install, concepts, commands, exit codes,
  schemas, compatibility, security, and governance.

### Fixed

- Repeated `bounded`, `load_entries`, and numeric-coercion helpers were
  consolidated, so a limit change cannot apply to one command and not another.
- `--command` on the policy command no longer collides with the subcommand
  destination.

## [0.1.0] - 2026-10-24

### Added

- RFC-0009 through RFC-0015: harness audit, contrastive iteration, telemetry,
  declared cases, capability inventory, failure taxonomy, and portable policy.
- Deterministic, model-free helpers for every declared mechanism, each bounded
  at 2500 bytes and byte-identical for identical input.
- The OpenCode adapter, the self-declared harness in this repository, and
  end-to-end composition tests.

[Unreleased]: https://github.com/seismael/openharness/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/seismael/openharness/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/seismael/openharness/releases/tag/v0.1.0

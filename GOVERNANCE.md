# Governance

## Model

OpenHarness is maintainer-led and specification-first. One maintainer
(`@seismael`) currently holds merge rights. The intent is to keep decisions
fast while the schema surface is still moving, and to widen governance before
the 1.0 freeze.

## What is normative

- `docs/standards/rfc-*.md` and `docs/standards/schemas/*.json` define the
  protocol. Code implements the protocol; it does not redefine it.
- The deterministic helpers and the `openharness` CLI are the reference
  implementation.
- Everything else (guides, adapters, examples) is informative.

## Change process

1. **Protocol change.** Open an RFC in `docs/standards/` or amend an existing
   one. State the motivation, the exact contract, compatibility impact, and
   evidence. A schema or contract change updates its RFC, schema, reference
   implementation, and tests in the same change.
2. **Implementation change.** A defect fix needs a regression. A behavior change
   needs a changelog entry and, where output is affected, an intentional golden
   snapshot update.
3. **Adapter change.** The adapter must stay honest about what the host
   enforces. Documented support and observed runtime support are different
   claims and stay in separate columns.

## Decision rules

- Determinism, bounded output, and local-only execution are non-negotiable.
  A proposal that needs a model call, a network call, or a hosted service to
  produce a verdict belongs in another layer.
- Never weaken a gate, remove a component, or raise a budget to make a finding
  disappear.
- Prefer emitting a native artifact over competing with an existing standard.
  Where a host or an established specification already owns a concern,
  OpenHarness renders or ingests and says so.

## Compatibility

- Patch releases do not change output bytes or exit codes.
- Minor releases may add commands, flags, fields, and schemas. Additive changes
  keep the previous behavior of existing flags.
- Major releases may remove compatibility shims and change defaults.
- Schema identifiers are versioned by suffix (`...v1`). A breaking schema change
  introduces a new identifier rather than mutating the old one.

## Releases

Releases are cut from `main` with a signed tag, a changelog entry, a regenerated
lockfile, green CI on all matrix platforms, and a PyPI publication by the
release workflow. A release is not complete until the installed wheel and the
installed skill both pass their smoke checks.

## Funding and affiliation

The project accepts no sponsored control over the specification. A decision to
donate the specification to a neutral foundation is deferred to the 1.0
milestone and will be documented here before it happens.

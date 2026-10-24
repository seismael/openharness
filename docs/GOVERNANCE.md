# Protocol governance

The repository-level decision rules, compatibility policy, and release process
are in [GOVERNANCE.md](../GOVERNANCE.md). This page covers how the protocol
itself changes.

## RFC lifecycle

1. **Draft.** An author opens a pull request adding `docs/standards/rfc-NNNN-<slug>.md`
   with the motivation, the contract, the compatibility impact, and the
   evidence plan. Drafts may change freely.
2. **Proposed Standard.** The RFC is indexed in
   [docs/standards/README.md](standards/README.md), a normative schema exists,
   the reference implementation conforms, and the conformance tests pass. This
   is the current status of RFC-0001 through RFC-0016.
3. **Standard.** At least one independent implementation, other than the
   reference implementation, passes the conformance suite, and no unresolved
   erratum is open.
4. **Deprecated.** A newer RFC supersedes it; the old document stays published
   with a pointer so existing adopters can migrate.

An RFC number is never reused. A breaking contract change creates a new schema
identifier (`...v2`) and a new RFC rather than mutating the accepted one.

## What requires an RFC

- A new schema or a breaking field change.
- A new verdict, severity, taxonomy entry, or exit code.
- A change to determinism, bounded-output, or privacy guarantees.
- A change to the meaning of an existing artifact.

The following do not require an RFC: a new flag that exposes an existing
computation, documentation, performance work that does not change bytes, and
adapter glue that only renders or reads an existing artifact.

## Conformance

A conforming implementation MUST satisfy the requirements of each RFC it claims.
The reference suite is `tests/test_ohp_conformance.py` plus the per-command
suites and golden snapshots. Adapters make narrower claims: an adapter that only
reads an artifact conforms to the artifact contract, not to enforcement.

Claims are labeled by evidence level, defined in [CONCEPTS.md](CONCEPTS.md):

- **Declared** — documented, not exercised.
- **Helper-tested** — deterministic tests on synthetic fixtures.
- **Runtime-observed** — a named host version and date.
- **Outcome-measured** — comparable real work.

A pull request that upgrades a claim MUST include the evidence for that level.

## Compatibility

- Schema identifiers are versioned by suffix. Old identifiers keep their meaning.
- Receipt fields may be added in a minor release. Existing fields keep their
  names, types, and meaning.
- Exit codes are part of the contract. A new code requires an RFC.
- Removing a compatibility shim requires a major release.

## Neutrality

The specification is vendor-neutral by construction: no host-specific keyword is
normative, and no adapter is privileged. A decision to donate the specification
to a neutral foundation is deferred to the 1.0 milestone and will be recorded in
[GOVERNANCE.md](../GOVERNANCE.md) before it happens.

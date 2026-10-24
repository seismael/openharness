# Validation

## Automated checks

From the repository root with Python 3.10+ and the development extras installed
(`python -m pip install -e ".[dev]"`):

```sh
ruff check .
ruff format --check .
mypy
pytest --cov=openharness --cov-report=term-missing --cov-fail-under=85
python -B tools/check_release.py
openharness audit --manifest harness.json
openharness context --manifest harness.json --check
openharness inventory --manifest harness.json --requirements requirements.json
openharness cases --cases cases.json --workdir .
openharness lock --check
openharness plan --check
python -m build
python -B tools/e2e_check.py
```

`pytest` collects every lane: `tests/`, and the five skill script directories. The legacy
`python -B -m unittest discover -s <lane> -p "test_*.py"` commands still work and run the
same tests. Tests use temporary directories and synthetic data; they make no model calls,
change no real agent settings, and activate no hooks. The suite runs without skips: platform
behavior that cannot be exercised directly (symlinks, hardlinks, reparse points, modes) is
simulated in-process instead of skipped, so every case executes on every operating system.

`tools/e2e_check.py` validates the installed product rather than the source tree. It builds
the wheel and sdist, installs each into a clean virtual environment, and checks the console
script, every command and help page, all four exit codes, every output format, `init`,
`lock`/`plan` drift attribution, `cases`, `policy`, `select`, `verify`, `telemetry`,
`inventory`, `failures`, and `report`. It also emulates the composite action's shell steps,
installs the loop skill bundle, and clones the repository to prove that committed bytes
satisfy `lock --check`, `plan --check`, and `context --check`. `--quick` keeps the wheel,
protocol, action, bundle, and clone checks while skipping the sdist install, the alternate
interpreter, and the clean-clone test suite; CI runs the quick lane on every push and pull
request. Exit `0` means every check passed, exit `1` lists the failures, and exit `2` means
the given path is not this repository.

A configured workflow is not evidence that its remote run passed; inspect the actual run
after publishing. The latest evidence for this repository is recorded below.

## What 0.2.0 adds

- **Behavior freeze.** `tests/golden/` holds the byte-exact output of every command on a
  fixed fixture. `tests/test_golden_commands.py` runs each command through both the legacy
  script path and the unified CLI and requires an exact match, before and after the
  package refactor. The thirteen snapshots captured before the refactor were reproduced
  unchanged; eight snapshots cover the new commands, for twenty-one in total.
- **CLI contract.** `tests/test_cli_contract.py` covers help for every command, the four
  exit codes, lock determinism, `--check` gating, per-file drift attribution (`~`, `+`,
  `-`, declaration), init discovery and refusal to overwrite, and all four report formats.
- **Packaging.** CI builds a wheel and sdist, installs the wheel in a clean virtual
  environment, and runs `audit`, `lock`, and `plan` from it. A separate job runs the
  composite action on this repository.
- **Static analysis.** Ruff lint and format checks cover the repository; mypy type-checks
  the `openharness` package; coverage must stay at or above 85%.

The lockfile and plan are tested on synthetic fixtures only. They prove that a given tree
produces a given content identity and attribution; they do not prove that a harness change
improves a workflow.

## Earlier evidence

RFC-0009 adds 15 harness audit regressions in the loop lane and 6 conformance cases in
`tests/`. RFC-0010 through RFC-0015 add 83 deterministic regressions in the loop lane and
10 cases in `tests/` (7 adapter conformance, 3 end-to-end composition), plus protocol-series
conformance cases. They cover scope and evidence validation, stale fingerprints, anonymized
selection and its sealed mapping, case predicate failures, timeout versus failure versus
error, recorded-only cost aggregation, separated gain and regression totals, inventory gaps
and blocking semantics, recurrence classification, last-match-wins policy evaluation, and
adapter enforcement claims. The composition case runs audit, receipt, journal,
verification, telemetry, inventory, failures, and policy over one fixture and asserts that
the fingerprint and the totals agree; it also asserts that an edited surface makes a
recorded fingerprint stale.

These establish deterministic behavior on synthetic fixtures only. They do not show that a
harness change improves a real workflow, that a host enforces a policy, or that a declared
case set is representative.

Prior release evidence (Characterize and Enhance): 44 automated tests passed locally: 23
Characterize change-bundle tests, 11 Enhance ledger tests, and 10 installer tests. The
[successful cross-platform run](https://github.com/seismael/openharness/actions/runs/37195311391)
for commit `648d407c30874ef9aec771cf9c6f1387b797f347` passed Ubuntu/Python 3.10,
Ubuntu/Python 3.13, macOS/Python 3.13, and Windows/Python 3.13 on 2026-10-04. Those runs
skipped platform-dependent cases; the current suite simulates that behavior instead, so it
reports zero skips. Live target CLI integration remains pending.

Characterize helper coverage includes exact-byte/mode restoration, created files,
scope/path restrictions, digest mismatch, content and permission drift, malformed input,
bundle limits, interrupted apply/rollback, and preserving later edits. It does not validate
target configuration semantics, prove approval, or guarantee an atomic multi-file
transaction.

Ledger coverage includes idempotence, new and late sessions, changed revisions,
stale-checkpoint refusal, partial/blocked progress, decision independence, pagination,
concurrent writers, unsupported database versions, and non-ASCII metadata. The helper
cannot prove that a human or model actually reviewed content before marking it reviewed.

## Evidence levels

The project distinguishes four levels, documented in [CONCEPTS.md](CONCEPTS.md):
declared, helper-tested, runtime-observed, and outcome-measured. A green CI run proves
declared and helper-tested behavior for this repository. It never proves runtime behavior
for a host that was not run, and it never proves an outcome.

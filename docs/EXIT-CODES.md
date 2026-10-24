# Exit codes

Every command uses the same four codes. Scripts and CI can branch on them without parsing output.

| Code | Meaning | Typical cause |
| :--- | :--- | :--- |
| `0` | Clean | The operation completed and the verdict is positive. |
| `1` | Findings or drift | Audit errors, blocking inventory gaps, failed or errored cases, policy `deny`, stale or drifting lock, invalid journal evidence, report not clean. |
| `2` | Usage or invalid input | A missing file, malformed JSON, an invalid manifest, an unknown flag, an unknown candidate, a missing lockfile, or any command invoked with no required argument. |
| `3` | Ask | The policy evaluated to `ask`: the action is neither permitted nor denied, and a human must decide. |

## Command detail

| Command | `0` | `1` | `2` | `3` |
| :--- | :--- | :--- | :--- | :--- |
| `init` | Wrote the declaration | Manifest already exists, or no surface found | Invalid flags or root | — |
| `lock` | Wrote the lock / state matches | `--check` found drift | Unreadable manifest or lock | — |
| `plan` | No drift (or informational mode) | `--check` found drift | Unreadable manifest or lock | — |
| `audit` | No error findings | Error findings (missing/empty/orphan/budget) | Invalid manifest | — |
| `verify` | No error findings | Error findings (fields, scope, evidence, stale fingerprint) | Unreadable journal | — |
| `select` | Recorded or displayed | A candidate lacks a probe receipt and `--allow-unprobed` was not passed | No candidates, unknown id, missing reason | — |
| `cases` | Every case passed | At least one case failed, timed out, or errored | Invalid case declaration | — |
| `telemetry` | Always, when the journal is readable | — | Unreadable journal | — |
| `inventory` | No blocking gaps | A required capability is missing | Invalid manifest or requirements | — |
| `failures` | No error findings (recurrence is a warning) | Invalid failure record or unknown class | Unreadable journal, recurrence below 2 | — |
| `policy` | `allow` | `deny` | Invalid policy or request | `ask` |
| `report` | Every included section is clean | Any included section is not clean | Unreadable input or invalid case declaration | — |

## Notes

- `plan` without `--check` exits `0` even when it reports drift. It is a preview. Add `--check` in CI.
- `telemetry` is a projection, not a gate. It exits `0` whenever the journal is readable, even when gains are zero or missing.
- `failures` treats recurrence as a `warn`, so a recurring class does not fail the command by itself. A malformed failure record is an `error`.
- A policy result is an evaluation, not enforcement. The host must still apply `deny` and `ask`; see RFC-0015 and [COMPATIBILITY.md](COMPATIBILITY.md).
- The compatibility scripts in `skills/loop/scripts/openharness_*.py` return exactly the same codes as their CLI subcommands.

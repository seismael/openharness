# Measurement: cases and telemetry

Two questions decide whether a harness change is real: **did the declared inputs behave
differently**, and **what did that cost**. Cases answer the first. Telemetry answers the
second. RFC-0012 and RFC-0011 are the normative contracts; this is how to use them.

## Declare the case set

Cases are any evaluation inputs your project can exercise deterministically. Keep them in a
JSON document so nothing depends on a YAML parser:

```json
{
  "schema": "openharness.cases.v1",
  "cases": [
    {"id": "unit", "command": "python -m pytest -q", "expect": {"exit_code": 0}, "timeout_s": 300},
    {"id": "cli", "command": "python -m mycli --dry-run", "expect": {"stdout_contains": "ok"}},
    {"id": "artifact", "command": "python tools/build.py", "expect": {"artifact": "dist/app.pyz"}}
  ]
}
```

Three predicates exist and only three: `exit_code`, `stdout_contains` (combined stdout and
stderr), and `artifact` (relative to the working directory). Anything else is rejected,
because an ignored expectation is a false pass.

Two cases are the minimum for an `invariant` claim. Pick cases that can disagree; two cases
that always pass together prove nothing about scope.

## Run the cases

```sh
python "scripts/openharness_cases.py" --cases cases.json --workdir . --dry-run
python "scripts/openharness_cases.py" --cases cases.json --workdir . \
  --receipt probes/it-7.receipt.json --fingerprint "$(python scripts/openharness_audit.py --manifest harness.json --fingerprint-only | python -c 'import json,sys;print(json.load(sys.stdin)["fingerprint"])')"
```

Exit `0` means every declared predicate held, `1` means something failed, timed out, or could
not start, and `2` means the declaration itself is wrong — in which case nothing ran.

`timeout` is not `fail`. A timeout means the case could not observe the behavior in the
declared budget, which is a different claim from observing it and finding it wrong.

`budget_tokens` is a declared ceiling for the invocation. The runner does not measure tokens
and never reports a number it did not observe.

## Match the conditions

A contrast is only a contrast when the case set, the working directory state, and the harness
fingerprint match. Change any one of them and the result is `unproven`, not `mitigated`. The
`--receipt` plus `--fingerprint` pair is what makes a receipt usable as the evidence required
by RFC-0010.

## Read the cost

```sh
python "scripts/openharness_telemetry.py" --journal .agents/loop/journal.jsonl --direction maximize
```

The projection reports:

- decision and contrast tallies, plus `unclassified` for values outside the contract;
- `adoption_rate`, `mitigation_rate`, and `evidence_coverage`, each over its own denominator;
- cost totals for the fields that were actually recorded — absent keys stay absent;
- `gain_total` and `regression_total` separately, never netted;
- `cost_per_gain`, or `null` when there is no positive gain to divide by.

Truncation drops per-deficiency detail first. The verdict, the tallies, the cost totals, and
the gain total always survive inside 2500 bytes.

## What the numbers do not say

Nothing in this projection says the project is better. It says which declared expectations
changed and what the loop recorded spending. A high adoption rate with low evidence coverage
is a warning, not a triumph; so is a positive gain total beside a large regression total.

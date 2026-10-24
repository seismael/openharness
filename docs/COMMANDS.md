# Command reference

Every command prints one JSON receipt (except `plan`, which prints text by default) and uses the exit codes in [EXIT-CODES.md](EXIT-CODES.md). Receipts are canonical JSON: sorted keys, no whitespace, at most 2500 bytes. Reports are written to a file and summarized on stdout.

```text
openharness [--version] <command> [options]
```

## init

Discover an existing harness and write `harness.json` plus `harness.lock`.

```sh
openharness init [--root .] [--name NAME] [--manifest harness.json] [--lock harness.lock]
```

- Discovers instruction files, rules, commands, skills, subagents, scripts, MCP surfaces, policy, and memory.
- Marks the first instruction surface as `always_on`.
- Sets budgets with 25% headroom over the measured state.
- Never overwrites an existing manifest. An empty repository is a finding (`1`).

## lock

Record or verify the content-addressed harness lockfile (RFC-0016).

```sh
openharness lock [--manifest harness.json] [--output harness.lock] [--check]
                 [--policy policy.json] [--cases cases.json] [--requirements requirements.json]
```

The lock contains the harness fingerprint, per-component file hashes and token estimates, the budget, the declaration hashes, and the generator version. `--check` compares the current tree with the lock and exits `1` on drift; the generator version is excluded from that comparison.

## plan

Explain drift between the lockfile and the current state.

```sh
openharness plan [--manifest harness.json] [--lock harness.lock] [--check]
                 [--format text|json]
```

Text output attributes each change:

```text
~ AGENTS.md (agents) +5 tokens
+ skills/release/SKILL.md (skills) +212 tokens
- docs/old-runbook.md (readme) -340 tokens
~ policy.json (declaration: policy)
```

Without `--check`, the command is a preview and exits `0`. With `--check`, any drift exits `1`.

## audit

Measure every declared component (RFC-0009).

```sh
openharness audit --manifest harness.json [--fingerprint-only]
```

Reports components, files, token totals, findings, severity counts, and the fingerprint. `--fingerprint-only` prints `{"fingerprint": "..."}`, which is the cheap identity check to store in a journal entry.

## verify

Validate journal entries against the iteration contract (RFC-0010).

```sh
openharness verify --journal journal.jsonl [--direction maximize|minimize]
                   [--tolerance 0.0] [--fingerprint HASH]
```

Checks required fields, the decision/scope/contrast vocabularies, evidence for adoption, the two-case rule for invariant changes, contrast consistency with before/after metrics, fingerprint staleness, and the justification for preserving the status quo.

## select

Anonymize candidate outputs and record an adoption choice without authorship bias.

```sh
openharness select --candidates DIR [--choose cand-a] [--reason TEXT]
                   [--unseal] [--allow-unprobed]
```

Candidates are relabelled in content-hash order; the mapping is sealed in `mapping.json`. Choosing requires a reason and, unless `--allow-unprobed` is passed, a probe receipt per candidate. The choice is recorded in `selection.json`.

## cases

Run declared evaluation cases as deterministic predicates (RFC-0012).

```sh
openharness cases --cases cases.json [--workdir .] [--only id,id]
                  [--dry-run] [--receipt PATH] [--fingerprint HASH]
```

A case declares a shell command and expectations: `exit_code`, `stdout_contains`, and `artifact`. Results distinguish `pass`, `fail`, `timeout`, and `error`. `--dry-run` validates declarations without executing. `--receipt` writes the receipt to a file for later composition.

## telemetry

Project recorded cost and contrast from the journal (RFC-0011).

```sh
openharness telemetry --journal journal.jsonl [--direction maximize|minimize] [--tolerance 0.0]
```

Aggregates only recorded fields: decisions, contrasts, adoption and mitigation rates, evidence coverage, cost totals, measured gain, regression total, and cost per gain. Missing data stays missing; nothing is estimated.

## inventory

Report which declared capabilities exist (RFC-0013).

```sh
openharness inventory --manifest harness.json [--requirements requirements.json]
```

Summarizes every kind, reports missing kinds, and lists gaps for the declared requirements. A missing requirement marked `required: false` is reported but does not fail the command. Coverage is `met / total`.

## failures

Classify recorded failures and detect recurrence (RFC-0014).

```sh
openharness failures --journal journal.jsonl [--recurrence 2]
```

The taxonomy is closed: `tool-misuse`, `context-loss`, `wrong-premise`, `dead-end`, `unsafe-action`, `spec-ambiguity`, `environment`, `data-quality`, `unclassified`. A class occurring `recurrence` or more times is reported as a harness gap, not an incident.

## policy

Evaluate a portable action policy (RFC-0015).

```sh
openharness policy --policy policy.json [--tool shell] [--path src/app.py] [--command "npm test"]
```

Rules are ordered and last-match-wins; a rule matches only when every declared condition matches. Exit `0` for `allow`, `1` for `deny`, `3` for `ask`. The verdict is an evaluation; enforcement belongs to the host.

## report

Compose audit, inventory, lock state, cases, and telemetry into one document.

```sh
openharness report [--manifest harness.json] [--requirements requirements.json]
                   [--cases cases.json] [--journal journal.jsonl] [--lock harness.lock]
                   [--execute] [--format json|markdown|sarif|junit] [--output PATH]
```

- Defaults to `harness-report.json`, `.md`, `.sarif`, or `.xml` by format.
- Prints a bounded receipt with the output path, byte count, fingerprint, and finding counts.
- `--execute` runs the declared cases; without it, cases are only validated.
- SARIF is 2.1.0 with logical locations per component; JUnit maps audit errors and blocking inventory gaps to `<failure>`.

## Compatibility scripts

The historical entry points remain as shims and print exactly what the matching subcommand prints:

```text
skills/loop/scripts/openharness_audit.py      -> openharness audit
skills/loop/scripts/openharness_verify.py     -> openharness verify
skills/loop/scripts/openharness_select.py     -> openharness select
skills/loop/scripts/openharness_cases.py      -> openharness cases
skills/loop/scripts/openharness_telemetry.py  -> openharness telemetry
skills/loop/scripts/openharness_inventory.py  -> openharness inventory
skills/loop/scripts/openharness_failures.py   -> openharness failures
skills/loop/scripts/openharness_policy.py     -> openharness policy
```

For a skill-only installation without a console script, run:

```sh
python path/to/skill/scripts/openharness_cli.py plan --check
```

The shims are retained until 2.0.

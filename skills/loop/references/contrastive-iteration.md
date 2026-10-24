# Contrastive iteration

How the loop improves the harness without a ground-truth verifier, using only artifacts it
already writes. RFC-0010 is the normative contract; this is how to run it.

## 1. Declare the case set

Cases are evaluation inputs you choose. Add them to the project seam:

```yaml
cases:
  - id: unit
    command: python -m pytest -q
    expect: { exit_code: 0 }
    timeout_s: 300
  - id: integration
    command: python -m pytest -m integration -q
    expect: { exit_code: 0 }
```

A case is whatever your project can evaluate deterministically. Two cases are the minimum
for an `invariant` claim; one is enough for a `local` claim.

## 2. Reference, then propose

Run the current harness on the declared cases. Then declare the candidate before testing it:

| Field | Value |
| :--- | :--- |
| `scope` | `invariant` or `local` |
| `deficiency` | planning, tool-use, context-management, delegation, knowledge, procedure, constraint, reliability, cost |
| `cases` | the cases this candidate will be probed on |
| `falsifier` | what observation would prove the change failed |

Propose at least one `invariant` and one `local` candidate when you explore more than one.
If you can only justify one scope, write down why the other does not apply.

## 3. Probe under matched conditions

Same model, same cases, same pipeline, and the same harness fingerprint for every probe in
a comparison. Change any of those and the result is `unproven`, not a verdict.

## 4. Classify the contrast

One of four values, no others:

- `mitigated` — the targeted deficiency improved beyond tolerance.
- `unchanged` — the candidate moved behavior within tolerance.
- `regressed` — the deficiency or an invariant got worse.
- `unproven` — no reference, unmatched conditions, or a fingerprint mismatch.

Accepting `unchanged` as a win is the most common way a loop lies to itself.

## 5. Choose anonymously when the choice is real

With one candidate there is nothing to choose. With more than one:

```sh
python "scripts/openharness_select.py" --candidates <dir>
python "scripts/openharness_select.py" --candidates <dir> --choose cand-b --reason "clearer deliverable"
```

The selector sees deliverables without their originating harness. The mapping stays in
`mapping.json` and is only for the audit trail. A candidate with no probe receipt can be
chosen only if the record marks it `unproven`.

## 6. Record and validate

Write the journal entry with `scope`, `deficiency`, `cases`, `contrast`,
`harness_fingerprint`, `evidence_ref`, and a rationale, then validate:

```sh
python "scripts/openharness_audit.py" --manifest harness.json --fingerprint-only
python "scripts/openharness_verify.py" --journal .agents/loop/journal.jsonl --fingerprint <sha256>
```

Exit `0` means the record is coherent, `1` means it violates the contract, `2` means the
journal or manifest cannot be read. `contrast.inconsistent` is a warning: the declared
verdict disagrees with the measured delta, which usually means the deficiency was not what
actually moved.

## 7. Retain only what is supported

An evidence entry must cite a contrast with a fingerprint. If nothing is supported, write
that nothing was retained and why. A retained lesson becomes a premise for every later
iteration, so an unsupported one is a permanent liability.

## 8. Preserve when preserving is right

`decision: preserved` with an observation is a legitimate outcome. You are not required to
change something every iteration; you are required to know why you did.

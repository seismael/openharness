# Working in OpenHarness

This repository ships an installable protocol product, not an application. Every change
belongs to one of five skills and is proven by the gate that product owns.

## Products and when to load them

| Product | Use it when | Entry point |
| :--- | :--- | :--- |
| `loop` | optimizing a target across iterations | `skills/loop/SKILL.md` |
| `audit` | auditing a project against its goals | `skills/audit/SKILL.md` |
| `characterize` | configuring an agent's native setup | `skills/characterize/SKILL.md` |
| `enhance` | improving an existing session or setup | `skills/enhance/SKILL.md` |
| `knowledge` | building a project wiki or capability inventory | `skills/knowledge/SKILL.md` |

Load exactly one product skill per task. Do not reimplement a helper a product already
ships.

## The CLI package

The deterministic commands live in `skills/loop/scripts/openharness/` as a standard-library
package. `pyproject.toml` maps that directory as the install root, so the same source serves
the installed skill, the wheel, and an editable install. The `openharness_*.py` files at
`skills/loop/scripts/` are compatibility shims; the implementation belongs in the package.

- Add a command as `openharness/commands/<name>.py` with `configure`, `run`, and `main`,
  then register it in `openharness/cli.py`.
- Output is canonical JSON through `openharness.jsonio`; receipts stay within 2500 bytes.
- Exit codes: `0` clean, `1` findings or drift, `2` usage or invalid input, `3` ask.
- A schema or contract change updates the RFC in `docs/standards/` and its schema in the
  same commit.
- If a command's output changes intentionally, regenerate `tests/golden` with
  `python -B tools/update_golden.py` and say so in the pull request.

## Non-negotiables

- Protocol text stays domain-agnostic. `tests/test_generic_purity.py` fails on instance
  vocabulary; add the term there when a leak is found.
- Deterministic commands call no model and no network, cap stdout at 2500 bytes, and stay
  byte-identical for identical input.
- Never weaken a gate, remove a component, or raise a budget to make a finding disappear.
- The OpenCode adapter ships the `/openharness` command and the read-only `harness-editor`
  subagent; keep both loadable and honest about what the host enforces.

## Verification

Run the narrowest lane that covers the change, then the full set before pushing:

```bash
python -B tools/check_release.py
ruff check .
ruff format --check .
mypy
pytest --cov=openharness --cov-fail-under=85
openharness audit --manifest harness.json
openharness lock --check
openharness plan --check
```

The other test lanes are `skills/{characterize,enhance,audit,knowledge}/scripts`; pytest
collects them all.

## Harness surface

`harness.json` declares this repository's own surface, `requirements.json` what it requires,
`cases.json` what it evaluates, `policy.json` what it refuses, and `harness.lock` the state
that was accepted. CI runs all of them through the protocol's own commands. A change that
trips them is not ready.

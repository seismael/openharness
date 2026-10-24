# Working in OpenHarness

This repository ships protocols and skills, not an application. Every change belongs to one
of five products and is proven by the gate that product owns.

## Products and when to load them

| Product | Use it when | Entry point |
| :--- | :--- | :--- |
| `loop` | optimizing a target across iterations | `skills/loop/SKILL.md` |
| `audit` | auditing a project against its goals | `skills/audit/SKILL.md` |
| `characterize` | configuring an agent's native setup | `skills/characterize/SKILL.md` |
| `enhance` | improving an existing session or setup | `skills/enhance/SKILL.md` |
| `knowledge` | building a project wiki or capability inventory | `skills/knowledge/SKILL.md` |

Load exactly one product skill per task. Do not reimplement a helper a product already ships.

## Non-negotiables

- Protocol text stays domain-agnostic. `tests/test_generic_purity.py` fails on instance
  vocabulary; add the term there when a leak is found.
- Deterministic helpers call no model and no network, cap stdout at 2500 bytes, and stay
  byte-identical for identical input.
- Never weaken a gate, remove a component, or raise a budget to make a finding disappear.
- A schema or contract change updates the RFC in `docs/standards/` in the same commit.
- The OpenCode adapter ships the `/openharness` command and the read-only `harness-editor`
  subagent; keep both loadable and honest about what the host enforces.

## Verification

Run the narrowest lane that covers the change, then the full set before pushing:

```bash
python tools/check_release.py
python -B -m unittest discover -s skills/loop/scripts -p "test_*.py"
python -B -m unittest discover -s tests -p "test_*.py"
```

The other lanes are `skills/{characterize,enhance,audit,knowledge}/scripts`.

## Harness surface

`harness.json` declares this repository's own surface, `requirements.json` what it requires,
`cases.json` what it evaluates, and `policy.json` what it refuses. CI runs all four through
the protocol's own helpers. A change that trips them is not ready.

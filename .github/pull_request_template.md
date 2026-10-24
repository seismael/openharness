# Pull request

## What changed

<!-- One paragraph. Name the behavior, not the files. -->

## Why

<!-- The observed failure, user need, or evidence. Link an issue when one exists. -->

## Verification

<!-- Paste the commands you ran and their result. -->

- [ ] `ruff check .` and `ruff format --check .`
- [ ] `mypy`
- [ ] `pytest --cov=openharness --cov-fail-under=85`
- [ ] `python -B tools/check_release.py`
- [ ] `openharness audit` and `openharness plan --check`

## Protocol impact

- [ ] No schema or contract change
- [ ] Schema or contract change, with the RFC and schema updated in this PR
- [ ] Output bytes changed, with the golden snapshot intentionally regenerated
- [ ] Compatibility shim behavior changed

## Checklist

- [ ] Deterministic: no clock, network, model call, or environment dependence
- [ ] Stdout stays within 2500 bytes for receipts
- [ ] No domain-specific vocabulary in `skills/` or normative standards
- [ ] No generated files, caches, or runtime state committed
- [ ] `CHANGELOG.md` updated for user-visible changes

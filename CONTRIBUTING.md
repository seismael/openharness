# Contributing

Keep each skill self-contained under `skills/<name>/`. Repository documentation, release tooling, and CI stay outside the installed skill directory. Avoid adding mandatory dependencies or an orchestration service for work a native agent can already perform.

Characterize establishes setup from user goals and current capabilities; Enhance improves it from actual session evidence. Keep each independently usable and exchange compact private records only when appropriate. The shared installer must continue to accept either complete skill bundle.

For changes to either skill:

1. Describe the observed failure or user need and the smallest supported change.
2. Explain the expected input/output, total-cost, latency, and maintenance effect. Preserve required correctness and reliability.
3. Keep global, shared-project, private-project, role, and task scope distinct; respect native permissions and explicit authorization.
4. Use current official documentation for host-specific behavior and update the checked date. Label runtime support according to evidence.
5. Run the release checker and relevant tests from [Validation](docs/VALIDATION.md), including Characterize's change-bundle suite for file-change/recovery behavior. Add a meaningful regression for a deterministic bug; do not create redundant test suites for wording changes.
6. Use synthetic or redacted fixtures and keep all runtime state out of the repository.

Do not promise universal host compatibility, exact savings, or runtime enforcement from instructions alone. Avoid copying host-specific configuration keys into the generic skill. Prefer on-demand references over expanding always-loaded descriptions or instructions.

If a host/version changes discovery or metadata behavior, include its exact version and official source, plus a minimal reproducible installation example. Separate documented support from observed live execution in the compatibility table.

---

## Open Harness Protocol (OHP) Standards Contribution

The **Open Harness Protocol (OHP)** is governed as an open, vendor-neutral specification under [`docs/standards/`](docs/standards/README.md).

### RFC Lifecycle & Proposals
1. **Proposal:** New standards proposals, extensions, or major schema revisions MUST be submitted as an RFC document under `docs/standards/rfc-XXXX-<topic>.md`.
2. **Review:** RFCs undergo open review for technical precision, RFC 2119 keyword compliance, and mathematical invariant safety.
3. **Reference Implementation:** Any proposed RFC MUST be accompanied by working reference code in `skills/loop/`, along with automated tests in `tests/test_ohp_conformance.py`.

### OHP Conformance Certification
Repositories implementing OHP may display the official conformance badge in their README:

```markdown
[![OHP v1.0 Compliant](https://img.shields.io/badge/OHP-v1.0--Compliant-blue)](https://github.com/seismael/openharness/tree/main/docs/standards)
```

To certify conformance, run the internal validator:
```bash
python skills/loop/scripts/validate_loop.py
```

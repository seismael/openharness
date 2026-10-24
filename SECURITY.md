# Security policy

## Supported versions

| Version | Supported |
| :--- | :--- |
| 0.2.x | Yes |
| 0.1.x | No |

## Reporting a vulnerability

Report vulnerabilities privately through
[GitHub Security Advisories](https://github.com/seismael/openharness/security/advisories/new).
Do not open a public issue for a suspected vulnerability. Include the version,
platform, a minimal reproduction, and the impact you observed. Expect an initial
response within seven days.

## Design boundaries

OpenHarness is a local, deterministic tool. It makes no network calls, sends no
telemetry, and needs no credentials. That removes whole classes of risk, and it
also means the project does not claim to be a runtime enforcement layer. Runtime
policy enforcement belongs to the host; OpenHarness evaluates and emits.

## What to treat as untrusted

- **Declarations.** `harness.json`, `policy.json`, `cases.json`, and
  `requirements.json` are inputs. Review them like code, because they decide
  what gets measured and what a policy permits.
- **Regular expressions.** Policy rules use `command_regex`. A pathological
  pattern can be slow. Keep patterns anchored and simple; the evaluator applies
  last-match-wins over a small rule set.
- **Commands.** `openharness cases` and `openharness report --execute` run the
  commands declared in a case file, through the shell, in the selected working
  directory. Run them only from a case file you trust, exactly as you would run
  a CI script. `openharness report` without `--execute` never runs anything.
- **Paths.** `init` and `lock` write only to explicit paths under the repository
  root. They do not follow symlinks out of the repository by design; the release
  checker rejects symlinks in published bundles.

## Supply chain

Releases are built from tagged commits in GitHub Actions, published to PyPI with
OIDC trusted publishing (no long-lived token), and attested with SLSA build
provenance. Verify with `gh attestation verify <wheel> --repo
seismael/openharness`.

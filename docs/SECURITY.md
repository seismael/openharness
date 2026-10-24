# Security model

The reporting policy and supported versions are in the repository's
[SECURITY.md](../SECURITY.md). This page documents the model behind that policy.

## Properties the design guarantees

| Property | How it holds |
| :--- | :--- |
| No network access | No command imports an HTTP client; there is no telemetry and no update check. |
| No model calls | Every verdict is computed from files and declarations. |
| No credentials | The tool reads no environment secret and writes none. |
| Deterministic output | Sorted serialization, content hashes, and no clock or environment inputs. |
| Bounded receipts | Canonical output is capped at 2500 bytes; detail is dropped before verdicts. |
| Explicit writes | Only `init`, `lock`, `select`, `cases --receipt`, and `report` write files, and only to declared paths. |

These properties reduce risk; they do not make untrusted input safe.

## Trust boundaries

### Declarations are code

`harness.json`, `requirements.json`, `cases.json`, and `policy.json` decide what
is measured, what must exist, what runs, and what is permitted. A malicious or
careless declaration can:

- include files the reviewer did not intend to publish,
- run arbitrary shell commands through `cases`,
- allow an action the policy was meant to block.

Review declaration changes exactly as you review source changes. The lockfile
makes that review visible by hashing the declarations alongside the harness.

### Case execution

`openharness cases` and `openharness report --execute` run the declared command
through the platform shell in the selected working directory. Standard output
and standard error are captured, and the child inherits the invoking process's
environment. This is equivalent to running a CI script: only execute case files
from a trusted branch, and prefer a sandboxed runner for untrusted pull
requests. `openharness report` without `--execute` never runs a command.

### Regular expressions

Policy rules may declare `command_regex`. Python's `re` engine is used directly.
A pathological pattern can consume CPU. Keep patterns anchored, avoid nested
quantifiers, and treat policy review as code review. The evaluator applies at most
one pattern per rule over one request string, which bounds the blast radius but
does not eliminate catastrophic backtracking inside a single pattern.

### Paths and symlinks

`init` and `lock` resolve paths under the manifest directory. The release checker
rejects symlinks in published bundles, and the installer refuses a symlinked
source or destination. A repository can still contain a symlink that points
outside itself; review it as you would review any file.

## What OpenHarness does not defend against

- **Runtime interception.** It does not sit between an agent and a tool call. It
  evaluates a policy; the host must enforce the verdict. See RFC-0015 and
  [COMPATIBILITY.md](COMPATIBILITY.md).
- **Prompt injection.** A malicious instruction inside a file is content the
  audit will measure, not neutralize. Instruction integrity is a host and review
  concern.
- **Malicious dependencies.** The runtime has none; the development extras
  (`pytest`, `ruff`, `mypy`, `build`) are ordinary PyPI packages and should be
  pinned and audited like any other dependency.
- **Supply-chain tampering after publication.** Releases are attested; verifying
  the attestation is the consumer's step.

## Release integrity

Releases are built from a tag in GitHub Actions, published to PyPI through OIDC
trusted publishing, and attested with build provenance. Verify a download:

```sh
gh attestation verify openharness-0.2.0-py3-none-any.whl --repo seismael/openharness
```

The workflow pins third-party actions to commit SHAs where the project has
verified them; new actions are pinned as they are adopted.

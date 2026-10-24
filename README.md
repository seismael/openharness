# OpenHarness

**The deterministic control plane for agent harnesses: declare it, lock it, measure it, prove it — on every host.**

An agent harness is everything around the model: instructions, skills, commands, subagents, tool guidance, MCP surfaces, scripts, and the policies that bound them. OpenHarness treats that harness as a versioned engineering artifact instead of an accident.

It is not an agent runtime, a model gateway, a security scanner, or a benchmark. It is the local, model-free layer that answers four questions:

| Question | Command | Artifact |
| :--- | :--- | :--- |
| What is my harness, and is it coherent? | `openharness audit` | Bounded audit receipt |
| Did it change, and exactly where? | `openharness lock` / `plan` | `harness.lock`, attributed drift |
| Does a change actually help? | `openharness cases` / `verify` / `telemetry` | Case and journal receipts |
| Which capabilities are missing, and why did work fail? | `openharness inventory` / `failures` | Gap and failure receipts |

Every command is standard-library-only Python, makes no network or model calls, caps receipts at 2500 bytes, and produces byte-identical output for identical input. That is the property that makes the rest usable in CI.

---

## Install

```sh
pipx install openharness
# or
python -m pip install openharness
```

From a clone, for development:

```sh
python -m pip install -e ".[dev]"
```

The five skills are also installable as self-contained bundles; the `loop` skill ships the same package inside `scripts/`. See **[docs/INSTALLATION.md](docs/INSTALLATION.md)**.

## Thirty seconds

```sh
cd your-repo
openharness init              # discover AGENTS.md, skills, commands, MCP, policy
openharness audit --manifest harness.json
openharness lock              # write harness.lock
openharness plan --check      # exit 0 when the tree matches the lock
```

`init` never overwrites an existing `harness.json`. If you already know your surface, write the manifest by hand; the format is one JSON object and is documented in **[docs/SCHEMAS.md](docs/SCHEMAS.md)**.

## Put it in CI

```yaml
- uses: seismael/openharness@v1
  with:
    manifest: harness.json
    requirements: requirements.json
    lock: harness.lock
    comment: true
```

The action writes a report, gates on audit findings, inventory gaps, and drift, and can keep a single updated comment on the pull request. Without the action:

```sh
openharness audit --manifest harness.json
openharness inventory --manifest harness.json --requirements requirements.json
openharness cases --cases cases.json --workdir .
openharness lock --check
openharness plan --check
```

## Commands

| Command | Purpose |
| :--- | :--- |
| `init` | Discover an existing harness and write `harness.json` plus a lock. |
| `lock` | Record the fingerprint, per-file hashes, tokens, budget, and declaration hashes. |
| `plan` | Attribute drift (`~` modified, `+` added, `-` removed) between state and lock. |
| `audit` | Measure components and report missing files, broken links, orphans, duplication, budget. |
| `verify` | Validate journal entries against the iteration contract. |
| `select` | Anonymize candidates and record an evidence-gated choice. |
| `cases` | Run declared evaluation cases as deterministic predicates. |
| `telemetry` | Aggregate recorded cost, gain, regression, and evidence coverage. |
| `inventory` | Report which declared capabilities exist and which are missing. |
| `failures` | Classify failures and detect a recurring class. |
| `policy` | Evaluate an ordered allow/ask/deny policy. |
| `report` | Compose everything into JSON, Markdown, SARIF 2.1.0, or JUnit XML. |

Full reference: **[docs/COMMANDS.md](docs/COMMANDS.md)**. Exit codes: **[docs/EXIT-CODES.md](docs/EXIT-CODES.md)**.

## The lockfile is the point

`harness.lock` is content-addressed, reviewable, and independent of time and machine:

```json
{
  "schema": "openharness.lock.v1",
  "fingerprint": "8cd422…",
  "components": [
    {
      "id": "agents",
      "kind": "system_prompt",
      "always_on": true,
      "tokens": 511,
      "files": [{ "path": "AGENTS.md", "sha256": "…", "tokens": 511 }]
    }
  ],
  "declarations": {
    "policy": { "path": "policy.json", "sha256": "…" }
  }
}
```

A pull request that edits one instruction line produces one attributed line:

```text
~ AGENTS.md (agents) +5 tokens
drift: 1 change(s) across 1 component(s)
```

That is the review primitive: harness changes become diffable, attributable, and gateable, the way infrastructure changes are.

## What this is not

- **Not runtime governance.** Microsoft's Agent Control Specification, gateways, and policy vendors own interception and enforcement. OpenHarness evaluates a portable policy and emits a verdict; it states where host enforcement is unproven.
- **Not an evaluation harness.** Harbor and Terminal-Bench own task-level agent evaluation. OpenHarness runs *your declared* cases and records whether your expectations held.
- **Not a benchmark.** It measures the harness, not the model, so its numbers do not move when a model version ships.
- **Not a prompt marketplace.** It versions what you already have.

Where an existing standard owns a concern, the project emits or ingests rather than competing. The boundary is documented in **[docs/CONCEPTS.md](docs/CONCEPTS.md)**.

## Standards

The protocol is specified as a modular RFC series with normative JSON schemas: **[docs/standards/README.md](docs/standards/README.md)**. RFC-0009 defines the harness surface and audit; RFC-0010 through RFC-0016 define contrastive iteration, telemetry, cases, inventory, failure taxonomy, portable policy, and the lockfile.

The repository applies the protocol to itself: `harness.json`, `requirements.json`, `cases.json`, `policy.json`, and `harness.lock` are committed, and CI runs the audit, inventory, cases, lock check, and drift check on every platform.

## Compatibility and honesty

OpenHarness supports Python 3.10 and later on Linux, macOS, and Windows. The CLI is tested on all three; host integrations are documented separately from observed runtime evidence in **[docs/COMPATIBILITY.md](docs/COMPATIBILITY.md)**. Instructions can guide an agent; they cannot create runtime capabilities a host does not offer, and the documentation never claims otherwise.

## Contributing, security, governance

- **[CONTRIBUTING.md](CONTRIBUTING.md)** — how to propose and verify a change.
- **[SECURITY.md](SECURITY.md)** — private reporting and the threat model.
- **[GOVERNANCE.md](GOVERNANCE.md)** — decision rules, compatibility, and releases.
- **[ROADMAP.md](ROADMAP.md)** — lock and drift now; context ledger, rendering, and transfer evidence next.
- **[CHANGELOG.md](CHANGELOG.md)** — what changed in 0.2.0.

## License

Code is MIT. The protocol specification is intended to move to CC-BY-4.0 at the 1.0 freeze; the licensing decision is recorded in [GOVERNANCE.md](GOVERNANCE.md).

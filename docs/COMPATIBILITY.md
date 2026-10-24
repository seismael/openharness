# Compatibility and evidence

Documentation checked: **2026-10-24**.

## The CLI

| Surface | Documented support | Evidence |
| :--- | :--- | :--- |
| Python 3.10–3.13 | Installed package and editable install | CI matrix on Ubuntu 3.10 and 3.13, macOS 3.13, Windows 3.13 |
| Linux, macOS, Windows | Console script, `python -m openharness`, skill launcher | CI matrix; golden snapshots normalize paths only |
| Wheel and sdist | `python -m build`, clean-venv install, CLI smoke test | CI `package` job |
| Installed skill | `scripts/` contains the package, shims, and launcher | Installer tests and release checker |
| GitHub Actions | Composite action at the repository root | CI `action` job on Ubuntu |

The CLI is deterministic across platforms: receipts contain no absolute paths except
the audit's `root` field, and the lockfile stores repository-relative POSIX paths.

## Host surfaces

This table describes the shared directory format used by the bundled skills. These are
documented installation targets, not a claim that every current or future version has
passed a live integration test. In invocation examples, replace `<skill>` with
`characterize`, `enhance`, `audit`, `knowledge`, or `loop`.

| Surface | Package/discovery evidence | Live runtime verification for this release |
|---|---|---|
| OpenCode | Official directory skills; use portable `name`/`description` frontmatter and a matching directory. | Not run in OpenCode. |
| Claude Code CLI | Official directory skills with supporting files and `/<skill>` invocation. | Not run in Claude Code. |
| Codex CLI | Official directory skills, `.agents/skills` discovery, `$<skill>` or `/skills`. | Not run in Codex CLI. |
| Gemini CLI | Official directory skills in `.gemini/skills` and `.agents/skills` aliases; `/skills list` exposes available skills. | Not run in Gemini CLI. |
| Antigravity CLI (`agy`) | Canonical official skills guide explicitly documents directory bundles, its CLI-specific global root, and slash-command registration. | Not run in agy. |
| Antigravity IDE | Same canonical format; different global root from the CLI. | Not run in the IDE. |
| Other Agent Skills hosts | Common-format candidate; verify host metadata, discovery, tools, and permissions. | Unverified. |

The development environment did not provide these local CLI executables. [Validation](VALIDATION.md) records automated results and their release scope; earlier passing results do not certify newly added skills. Helper tests and instruction scenarios do not substitute for testing a host's discovery, effective configuration, permissions, or model behavior.

## Portable contract

- Each `skills/<skill>/SKILL.md` contains standard `name` and `description` frontmatter matching its directory. Descriptions stay within the common 1,024-character limit.
- Relative references and Python scripts remain inside the skill directory. There are no embedded developer-machine paths, account-specific settings, or API keys. Installation adds no service or subscription; task access requirements still depend on the host and requested work.
- The `loop` skill ships the complete `openharness` package in `scripts/`, so the audit, lock, plan, and every other command work without a separate install. The console script is a convenience, not a requirement.
- Optional `agents/openai.yaml` provides OpenAI UI metadata only. Other hosts do not need it; it is not a replacement for their native agent configuration.
- The instruction workflow uses the host's existing model and tools. Python 3.10+ and its standard library are needed only for the installer and the deterministic commands.
- Enhance discovers native histories at execution time. Its ledger consumes normalized metadata supplied by the agent; it is not a universal parser for all proprietary session formats.
- Characterize discovers target capabilities at execution time. Its file-change helper checks drift and supports recovery; it does not generate or validate a universal configuration schema.
- Audit uses the host's authorized source-reading, research, and GitHub/git capabilities. Its optional read-only helper validates the audit artifact contract, not source-code correctness or implementation quality. Repository writes, branch rules, and remote commit verification depend on the available connection; unavailable operations remain blocked.
- Instructions can guide behavior but cannot create unsupported runtime capabilities or bypass the host's permissions.

OpenCode V2 relaxes some metadata constraints compared with the unversioned documentation. This package retains the common strict format. Antigravity has older documentation for flat skill files; this release follows its canonical surface-specific directory guide. Check the actual installed version if documentation and discovery differ.

## Policy evaluation versus enforcement

RFC-0015 separates three claims, and this release makes only the first two:

| Claim | Status in 0.2.0 |
| :--- | :--- |
| The policy document parses and validates deterministically | Tested |
| Evaluation produces the declared verdict and exit code | Tested |
| A named host version actually blocks a denied action | Not observed; recorded per adapter |

The OpenCode adapter documents which of its native permission surfaces can express
`allow`, `ask`, and `deny`. It does not claim that the host reads `policy.json`, and no
adapter may claim enforcement without a recorded runtime observation.

## Verification levels

1. **Format checked:** metadata, directory structure, and bundled references pass the release checker.
2. **Helper tested:** deterministic tests cover ledger correctness, staged file changes/recovery, audit artifact consistency, and installation behavior.
3. **Scenario reviewed:** selected prompts exercise scope, decisions, cost reasoning, and authorization in a host agent.
4. **Runtime observed:** the exact target version discovers the skill and completes representative tasks. Record product/version, OS, date, evidence, and limits before marking this level.
5. **Outcome measured:** comparable real usage establishes cost/performance and quality effects. No savings percentage is asserted by this release.

## Official sources

- [Agent Skills specification](https://agentskills.io/specification)
- [OpenCode skills](https://opencode.ai/docs/skills/)
- [OpenCode V2 skills](https://opencode.ai/v2/docs/skills)
- [Claude Code skills](https://code.claude.com/docs/en/skills)
- [Codex and ChatGPT skill authoring](https://learn.chatgpt.com/docs/build-skills)
- [Gemini CLI skills and discovery precedence](https://geminicli.com/docs/cli/skills/)
- [Antigravity skills by surface](https://antigravity.google/docs/skills/)

For a runtime test, follow [Validation](VALIDATION.md) using non-sensitive fixtures and existing connected models. Do not install or invoke additional paid services simply to claim compatibility.

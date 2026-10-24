# Installation

## The CLI

```sh
pipx install openharness       # isolated, recommended
python -m pip install openharness
```

From a clone, with the development tools:

```sh
python -m pip install -e ".[dev]"
openharness --version
```

Requires Python 3.10 or later. The package uses only the standard library at runtime. A
wheel and an sdist are published for every tagged release, with build provenance; see
[SECURITY.md](SECURITY.md) for verification.

Install the GitHub Action by referencing the repository at a major tag:

```yaml
- uses: seismael/openharness@v1
  with:
    manifest: harness.json
    requirements: requirements.json
    lock: harness.lock
```

## The skills

Install the complete selected directory under `skills/`, including its references and
scripts. Each is independently installable; the repository root is a collection. Use
Characterize for setup from goals and current configuration, Enhance for improvement from
actual sessions, and Audit for project audits and implementation plans committed to a
GitHub repository. The `loop` skill includes the `openharness` package, so its commands
work in a skill-only installation through `scripts/openharness_cli.py`.

## Choose a native location

Locations below are documented by the respective vendors as of 2026-10-04. Replace `<skill>` with `characterize`, `enhance`, `audit`, `knowledge`, or `loop`. `~` means the user home directory. Project paths are relative to the relevant workspace/repository. Custom profiles and environment overrides can change locations; verify the installed host's active configuration.

| Host | User/global skill directory | Project skill directory | Explicit use |
|---|---|---|---|
| OpenCode | `~/.config/opencode/skills/<skill>/` | `.opencode/skills/<skill>/` | Request the named skill using the native skill interface or prompt. |
| Claude Code CLI | `~/.claude/skills/<skill>/` | `.claude/skills/<skill>/` | `/<skill>` |
| Codex CLI | `~/.agents/skills/<skill>/` | `.agents/skills/<skill>/` | `$<skill>`, or select through `/skills`. |
| Gemini CLI | `~/.gemini/skills/<skill>/` | `.gemini/skills/<skill>/` | Explicitly request the named skill; inspect with `/skills list`. |
| Antigravity CLI (`agy`) | `~/.gemini/antigravity-cli/skills/<skill>/` | `.agents/skills/<skill>/` | `/<skill>` in its TUI, or explicitly name the skill. |
| Antigravity IDE | `~/.gemini/config/skills/<skill>/` | `.agents/skills/<skill>/` | Explicitly name the skill in the prompt. |

For OpenCode on Windows, verify the configuration root in your installed version; supported XDG/profile overrides can alter its default location. Antigravity's CLI and IDE have different global roots. A shared `.agents/skills` project folder can be discovered by more than one compatible host; choose a host-specific directory when you want narrower availability. Avoid duplicate same-name skills across overlapping roots.

Gemini CLI also discovers user/workspace `.agents/skills` aliases. Workspace skills outrank user skills, and the `.agents` alias outranks `.gemini` within the same scope. Check the loaded name and source before adding another copy.

Sources: [OpenCode](https://opencode.ai/docs/skills/), [Claude Code](https://code.claude.com/docs/en/skills), [Codex](https://learn.chatgpt.com/docs/build-skills), [Gemini CLI](https://geminicli.com/docs/cli/skills/), [Antigravity](https://antigravity.google/docs/skills/).

## Optional Python installer

Run from the cloned repository. The same installer works for every bundled skill; substitute its name in both `--skill` and `--to`. Use Python 3.10+ (`python3` on some systems or `py -3` on Windows).

```sh
python tools/install_skill.py --skill characterize --to ~/.claude/skills/characterize --check
python tools/install_skill.py --skill characterize --to ~/.claude/skills/characterize
```

For a project installation, supply an explicit project path:

```sh
python tools/install_skill.py --skill enhance --to /path/to/project/.opencode/skills/enhance --check
python tools/install_skill.py --skill enhance --to /path/to/project/.opencode/skills/enhance
```

Audit example:

```sh
python tools/install_skill.py --skill audit --to ~/.agents/skills/audit --check
python tools/install_skill.py --skill audit --to ~/.agents/skills/audit
```

PowerShell example for Codex:

```powershell
py -3 tools/install_skill.py --skill characterize --to "$HOME/.agents/skills/characterize" --check
py -3 tools/install_skill.py --skill characterize --to "$HOME/.agents/skills/characterize"
```

`--check` makes no changes. The installer copies only the selected skill and refuses existing destinations, symlinks, and unsafe paths. It never alters model settings, permissions, hooks, or instruction files elsewhere. Normal host sandbox approval may still apply. If a supported skill root is itself a symlink, use a reviewed native/manual installation method; do not disable its protection.

Without Python, copy the folder with your file manager and confirm `<skill>/SKILL.md`, `<skill>/references/`, and `<skill>/scripts/` remain together. Python is only necessary when using the helper utilities.

## Confirm discovery

Use the host's native skill listing/selector when available and ask it to load the installed skill. Confirm the discovered path and name. If the skill is not listed, check the installed version, active root, folder structure, disabled-skill policy, and host reload guidance. Do not overwrite global `AGENTS.md`, `CLAUDE.md`, or another instruction file with the entire skill.

Discovery is separate from target access. Characterize needs the relevant configuration and task context; Enhance also needs authorized session evidence. Begin with a proposal-only task in a disposable project and confirm scope before approving persistent behavior changes.

Audit Project needs a GitHub repository URL, a focus message, and authorized source access. Committing its artifacts also needs a supported write mechanism; installing the skill creates no GitHub account connection or additional permissions. For a first smoke check, use a disposable repository and ask for an audit of one small subsystem. Confirm that it asks about findings, creates plans rather than product changes, and reports remote publication honestly. See [Validation](VALIDATION.md) for synthetic fixtures and the expected observations.

## Updates and removal

The installer deliberately has no overwrite option. Before an update, preserve local modifications and move the existing installed skill to a private backup directory outside every skill discovery root. Install the new copy, verify discovery, and retain the backup until satisfied. Runtime ledgers stay in their separate private location.

To disable/remove a skill, use the host's native mechanism or move its installed directory outside discovery roots. Removing the skill does not automatically undo configuration changes previously approved and applied; use their recorded recovery plan.

## Other agents

Use a documented directory-skill loader if the target provides one. Otherwise, the agent can follow `SKILL.md` with its references when explicitly supplied, but automatic discovery, native invocation, history access, and enforcement remain unverified. Do not rename or transplant tool-specific settings to claim compatibility.

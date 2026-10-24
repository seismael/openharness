# Changes, validation, and recovery

## Prepare a concrete proposal

Compile verified native settings from the blueprint. Check configuration precedence and inherited effects before choosing the layer to edit. Preserve existing comments, key order where meaningful, line endings, unrelated fields, and user-owned instruction sections. Use syntax-aware edits for JSONC/TOML/YAML; do not strip comments with regex. Parse and validate the proposed result separately.

Prefer additive uniquely named profiles and narrowly scoped edits. For an existing instruction file, use a clearly delimited owned section or a documented include, without erasing other instructions. Record managed keys/sections and hashes so later invocations can detect conflicts. Do not disable existing agents or integrations merely to make the new profile cleaner.

Before approval, show the resolved user profile, mode/model/permission table, exact file/key changes, diff with secrets redacted, any new dependencies or billing route, and verification/recovery plan. If approval is still required, ask one plain question for the concrete proposal. After approval, apply, validate, and repair within scope without repeatedly asking. A material change to permissions, billing, target scope, or external effects needs a new decision.

## Deterministic file helper

Run from the complete skill folder or use an absolute script path. Python 3.10+ standard library only. It does not synthesize native settings, validate their semantics, enforce a sandbox, or grant authorization. Stage full proposed UTF-8 files after making syntax-aware edits in a private working area.

Create a local JSON spec, using actual absolute paths:

```json
{
  "roots": ["/absolute/project", "/absolute/user/config/opencode"],
  "writes": [
    {
      "path": "/absolute/project/opencode.json",
      "source": "/absolute/private-work/proposed/opencode.json"
    }
  ]
}
```

Include only approved target scopes, preferably narrow existing config/project directories. Windows paths must be absolute and escaped as JSON strings. Do not use `/` or a drive root. The bundle must be outside all target roots. Never include credentials, authentication files, or files owned by managed policy. Configuration containing inline secrets requires private local handling: backups contain exact original bytes; do not attach them to a chat or shared repository.

```sh
python3 scripts/change_bundle.py stage --spec /absolute/private-work/spec.json --bundle /absolute/private-work/bundle
python3 scripts/change_bundle.py review --bundle /absolute/private-work/bundle
```

Stage reads live files without changing them and stores original/proposed bytes and modes. It omits no-op files. Review prints paths/hashes only. `review --diff` prints **raw content**: use it only for known non-secret files or pipe through a verified local redaction step before exposing output. The blueprint, native validation, and diff remain necessary; hashes alone are not a user review.

After authorization, use the exact reviewed digest from stage/review:

```sh
python3 scripts/change_bundle.py apply --bundle /absolute/private-work/bundle --sha256 REVIEWED_DIGEST
python3 scripts/change_bundle.py rollback --bundle /absolute/private-work/bundle --sha256 REVIEWED_DIGEST
```

The digest binds the plan bytes; it does not prove user authorization. Apply verifies every original file before writing, checks again per file, and journals attempted replacements. Each file replacement is atomic on ordinary supported local filesystems; the whole change set is **not** an atomic transaction. On failure/interruption, inspect `journal.json` and run rollback within already authorized repair scope. Verify native behavior after recovery.

Rollback restores recorded originals, removes only newly created files that still match the proposed bytes/mode, and refuses later user edits. It preflights every attempted file. If drift blocks recovery, inspect and prepare a surgical merge; never overwrite later changes or use an unchecked force option. Empty directories created for new files may remain.

Limits: ordinary single-link UTF-8 files, no symlink/reparse paths, no deletion plans, 2 MiB per file and a bounded bundle size. A bundle is single-use; create a fresh one after rollback or changed proposals. POSIX permission bits are preserved, but ACLs, ownership changes, extended attributes, power-loss durability, and hostile concurrent filesystem changes are not guaranteed. Windows inherits directory ACLs; choose a private directory. If those properties matter, use the platform's native management/backup mechanism. Quiesce editors or processes actively rewriting the selected configs; hashes do not eliminate all concurrency races. No helper can bypass host access controls.

## Validation levels

1. **Static:** syntax, actual-version schema, referenced files, unique names, supported model/options, rule order, no unrelated changes. Never mistake parsing success for effective configuration.
2. **Loaded:** target discovers selected modes/skills/commands, loads intended layers, resolves provider/model, and honors reload requirements. Inspect effective state with available native diagnostics. Consider whether launching diagnostics triggers existing hooks, plugins, or model calls.
3. **Behavior:** run a small representative task against acceptance criteria; test the intended workflow/handoff and action boundaries. Use harmless probes or a sandbox/policy dry-run for permissions. Never attempt real publication, deletion, or spending merely to test a deny rule.
4. **Efficiency:** compare representative before/after usage if accessible and within the user's authorized test budget. Count all attempts. If usage evidence is unavailable, report qualitative rationale and measurement pending, not a savings percentage.

Existing approval to implement generally covers bounded in-scope local tests and repairs. Do not introduce new paid routes or large benchmark workloads implicitly. If runtime is inaccessible, deliver static results and precise commands/actions for local continuation with runtime status pending.

Check an ordinary successful task and a meaningful difficult case where feasible: an ambiguous requirement should trigger the right question, an analysis stage should respect its actual action limits, and execution should complete approved work without unnecessary gates. Include an output-quality check appropriate to the domain. Stop after required evidence is sufficient.

## Deliver and resume

Report changed paths/features, invocation/selection instructions, model and fallback choices, verification evidence, limitations, and the exact private rollback location. Record active version/hashes and authorization. Later, compare current files to the last applied state, recheck affected capabilities after upgrades, and propose the smallest change. Do not overwrite unrelated drift.

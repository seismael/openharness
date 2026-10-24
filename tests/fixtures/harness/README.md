# Fixture harness

This fixture is a minimal but complete harness declaration used by the golden
snapshot tests. It exists so command output can be frozen byte-for-byte before
the package refactor and compared afterwards.

Keep every file deterministic: no timestamps, no absolute paths, no ordering
that depends on the filesystem.

The `build` skill is referenced by `AGENTS.md` so the reachability check passes.

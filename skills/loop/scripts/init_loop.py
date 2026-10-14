#!/usr/bin/env python3
"""Initialize the standard .agents/loop or legacy .loop directory structures for a project."""

import argparse
import json
from pathlib import Path
import re
import shutil
import sys

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "assets" / "templates"


def init_project(target_dir: Path, target: str = "", force: bool = False, use_legacy_dual: bool = False, template: str = "python") -> int:
    agents_dir = target_dir / ".agents"
    if use_legacy_dual:
        loop_dir = target_dir / ".loop"
    else:
        # Default canonical: unified under .agents/loop
        # If legacy .loop already exists and .agents/loop doesn't, respect .loop unless force
        if (target_dir / ".loop").is_dir() and not (agents_dir / "loop").is_dir() and not force:
            loop_dir = target_dir / ".loop"
        else:
            loop_dir = agents_dir / "loop"

    # Create subdirectories
    for d in [
        loop_dir / "plans",
        loop_dir / "knowledge" / "decisions",
        loop_dir / "scratch",
        loop_dir / "scripts",
        agents_dir / "skills",
        agents_dir / "subagents",
    ]:
        d.mkdir(parents=True, exist_ok=True)

    # 0. Initialize env.json (Deterministic Environment Manifest)
    env_json_path = loop_dir / "env.json"
    if not env_json_path.exists() or force:
        python_bin = "python"
        for venv_cand in [
            target_dir / ".venv" / "Scripts" / "python.exe",
            target_dir / ".venv" / "bin" / "python",
            target_dir / "venv" / "Scripts" / "python.exe",
            target_dir / "venv" / "bin" / "python",
        ]:
            if venv_cand.exists():
                try:
                    python_bin = str(venv_cand.relative_to(target_dir))
                except ValueError:
                    python_bin = str(venv_cand)
                break

        env_data = {
            "project_name": target_dir.name or "project",
            "python_bin": python_bin,
            "test_cmd": "pytest",
            "entry_point": "",
            "loop_dir": str(loop_dir.relative_to(target_dir)),
            "scratch_dir": str((loop_dir / "scratch").relative_to(target_dir)),
        }
        env_json_path.write_text(json.dumps(env_data, indent=2) + "\n", encoding="utf-8")
        print(f"Created {env_json_path.relative_to(target_dir)}")

    # 1. Initialize loop.json
    loop_json_path = loop_dir / "loop.json"
    if not loop_json_path.exists() or force:
        tpl_path = TEMPLATES_DIR / "loop.template.json"
        if tpl_path.exists():
            data = json.loads(tpl_path.read_text(encoding="utf-8"))
        else:
            data = {
                "loop_id": target_dir.name or "default",
                "target": target or "Optimize system performance without regressions",
                "status": "ACTIVE",
                "step": 0,
                "stopped_at_step": None,
                "resume_pointer": {"front": "orient", "axis": "baseline", "step_index": 0},
                "sub_targets": [],
                "do_not_repeat": [],
            }
        if target:
            data["target"] = target
        loop_json_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print(f"Created {loop_json_path.relative_to(target_dir)}")

    # 2. Initialize coverage.json
    coverage_path = loop_dir / "coverage.json"
    if not coverage_path.exists() or force:
        tpl_cov = TEMPLATES_DIR / "coverage.template.json"
        if tpl_cov.exists():
            shutil.copyfile(tpl_cov, coverage_path)
            print(f"Created {coverage_path.relative_to(target_dir)}")

    # 3. Initialize knowledge/profile.yaml
    profile_path = loop_dir / "knowledge" / "profile.yaml"
    if not profile_path.exists() or force:
        tpl_prof = TEMPLATES_DIR / f"profile.{template}.yaml"
        if not tpl_prof.exists():
            tpl_prof = TEMPLATES_DIR / "profile.template.yaml"
        if tpl_prof.exists():
            content = tpl_prof.read_text(encoding="utf-8")
            if target:
                content = content.replace("<one-sentence target description the loop is working on / optimizing>", target)
                content = re.sub(r'target:\s*".*?"', f'target: "{target}"', content)
            profile_path.write_text(content, encoding="utf-8")
            print(f"Created {profile_path.relative_to(target_dir)}")

    # 4. Initialize knowledge/invariants.md
    inv_path = loop_dir / "knowledge" / "invariants.md"
    if not inv_path.exists() or force:
        inv_content = (
            "# System Invariants\n\n"
            "- All unit, integration, and regression test suites must pass 100% green.\n"
            "- No regressions in system stability, safety limits, or memory bounds.\n"
            "- Exact numerical float parity preserved against baseline control receipts.\n"
        )
        inv_path.write_text(inv_content, encoding="utf-8")
        print(f"Created {inv_path.relative_to(target_dir)}")

    # 5. Initialize plans/next_moves.json
    moves_path = loop_dir / "plans" / "next_moves.json"
    if not moves_path.exists() or force:
        initial_moves = [
            {"id": "M01", "front": "orient", "description": "Establish ground truth and verify clean baseline", "ev": 10.0},
            {"id": "M02", "front": "audit", "description": "Audit system interfaces and boundary assertions", "ev": 8.5},
            {"id": "M03", "front": "diagnose", "description": "Run diagnostic probes to locate dominant loss vectors", "ev": 8.0},
        ]
        moves_path.write_text(json.dumps(initial_moves, indent=2) + "\n", encoding="utf-8")
        print(f"Created {moves_path.relative_to(target_dir)}")

    # 6. Initialize knowledge/index.md
    index_path = loop_dir / "knowledge" / "index.md"
    if not index_path.exists() or force:
        index_content = (
            "# Project Knowledge Index\n\n"
            f"Knowledge root for {target_dir.name}. Bounded entrypoint (< 400 tokens).\n\n"
            "## Core Documents\n"
            "- [Profile](profile.yaml) — Declarative project boundaries and fronts\n"
            "- [Invariants](invariants.md) — Non-negotiable boundaries and safety constraints\n"
            "- [Capabilities](capabilities.md) — Discovered CLI tools, test runners, benchmarks\n"
            "- [Baselines](baselines.md) — Metric receipts and champion records\n"
            "- [Decisions](decisions/log.md) — Cumulative accepted and rejected candidates\n"
        )
        index_path.write_text(index_content, encoding="utf-8")
        print(f"Created {index_path.relative_to(target_dir)}")

    # 7. Initialize .agents/subagents/ with specialist personas
    agents_tpl_dir = TEMPLATES_DIR / "agents"
    if agents_tpl_dir.exists():
        for agent_file in agents_tpl_dir.glob("*.yaml"):
            dest = agents_dir / "subagents" / agent_file.name
            if not dest.exists() or force:
                shutil.copyfile(agent_file, dest)
                print(f"Created {dest.relative_to(target_dir)}")

    # 8. Initialize .opencode/agent/ with native Markdown personas for OpenCode discovery
    opencode_agent_dir = target_dir / ".opencode" / "agent"
    opencode_agent_dir.mkdir(parents=True, exist_ok=True)
    personas = {
        "diagnostician.md": (
            "---\n"
            "description: Causal root-cause, profiler, and bottleneck analysis specialist. Read-only.\n"
            "mode: subagent\n"
            "---\n\n"
            "# Diagnostician Specialist\n\n"
            "You are the read-only Causal Root-Cause & Profiling Specialist for the autonomous loop.\n"
            "Your role is to investigate missed opportunities, latency bottlenecks, and error clusters.\n\n"
            "## Rules\n"
            "- Strictly read-only: never edit files, commit changes, or alter configurations.\n"
            "- Return a concise deliverable (<= 20 lines / <= 2,500 bytes) with exact path:line citations.\n"
            "- Identify the single dominant cause, not a diffuse list of speculations.\n"
        ),
        "architect.md": (
            "---\n"
            "description: Structural design and invariant specialist. Synthesizes minimal candidate plans. Read-only.\n"
            "mode: subagent\n"
            "---\n\n"
            "# Architect Specialist\n\n"
            "You are the Structural Design & Invariant Specialist for the autonomous loop.\n"
            "Your role is to design minimal, decoupled mechanism changes that respect all repository invariants.\n\n"
            "## Rules\n"
            "- Strictly read-only: propose candidate plans without directly mutating files.\n"
            "- Return a concrete, minimal diff specification with falsifiable gates.\n"
            "- Ensure zero violation of architectural boundaries or immutable safety rules.\n"
        ),
        "verifier.md": (
            "---\n"
            "description: Dual-gate verification, test execution, and regression audit specialist. Read-only.\n"
            "mode: subagent\n"
            "---\n\n"
            "# Verifier Specialist\n\n"
            "You are the Dual-Gate Verification Specialist for the autonomous loop.\n"
            "Your role is to audit candidate changes against primary objective gain and zero invariant regressions.\n\n"
            "## Rules\n"
            "- Run declared verification commands from .agents/loop/env.json.\n"
            "- Check both Gate A (objective improvement) and Gate B (zero invariant breakage).\n"
            "- Return clear PASS/FAIL verdicts with exact quantitative evidence.\n"
        ),
        "synthesizer.md": (
            "---\n"
            "description: Large log digestion, trace parsing, and bounded projection specialist. Read-only.\n"
            "mode: subagent\n"
            "---\n\n"
            "# Synthesizer Specialist\n\n"
            "You are the Log Digestion & Bounded Projection Specialist for the autonomous loop.\n"
            "Your role is to parse multi-megabyte evaluator outputs, trace logs, or benchmark records in an isolated context.\n\n"
            "## Rules\n"
            "- Strictly read-only.\n"
            "- Boil down multi-megabyte datasets into strictly bounded projections (<= 2,500 bytes).\n"
            "- Never return raw dumps of verbose logs, trace records, or raw dumps.\n"
        ),
    }
    for fname, pcontent in personas.items():
        pdest = opencode_agent_dir / fname
        if not pdest.exists() or force:
            pdest.write_text(pcontent, encoding="utf-8")
            print(f"Created {pdest.relative_to(target_dir)}")

    print(f"Project initialized successfully at {target_dir} (loop state at {loop_dir.relative_to(target_dir)})")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-dir", type=Path, default=Path.cwd(), help="Target repository directory")
    parser.add_argument("--template", choices=["python", "rust", "go", "node"], default="python", help="Starter template profile")
    parser.add_argument("--target", type=str, default="", help="High-level loop target objective")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    parser.add_argument("--legacy-dual", action="store_true", help="Initialize separate root .loop directory instead of unified .agents/loop")
    args = parser.parse_args(argv)

    return init_project(args.target_dir.resolve(), args.target, args.force, args.legacy_dual, args.template)


if __name__ == "__main__":
    sys.exit(main())

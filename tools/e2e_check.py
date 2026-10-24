"""End-to-end validation of the installed product, outside the source tree.

Builds sdist and wheel, installs both into clean virtual environments, and
exercises every command, exit code, output format, init flow, gateway script,
adapter emulation, skill bundle, and a clean git clone. Prints one line per
check, collects every failure, and exits non-zero if any check fails.

``--quick`` drops the slow interpreter and source-distribution legs while
keeping the wheel install, protocol commands, composite-action emulation, skill
bundle, and clean-clone committed-bytes checks.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import venv
import zipfile
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parent.parent
ROOT = DEFAULT_ROOT
WORK = Path(tempfile.mkdtemp(prefix="ohp_e2e_"))
FIXTURE = ROOT / "tests" / "fixtures" / "harness"
QUICK = False
FAILURES = []
CHECKS = 0


def check(label, condition, detail=""):
    global CHECKS
    CHECKS += 1
    if condition:
        print(f"PASS {label}")
    else:
        FAILURES.append(f"{label}: {detail}")
        print(f"FAIL {label}: {detail}")


def run(argv, cwd, env=None, timeout=900):
    merged = dict(os.environ)
    merged["PYTHONIOENCODING"] = "utf-8"
    merged["PYTHONDONTWRITEBYTECODE"] = "1"
    if env:
        merged.update(env)
    return subprocess.run(
        argv,
        cwd=str(cwd),
        env=merged,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def venv_python(directory):
    base = Path(directory) / ("Scripts" if os.name == "nt" else "bin")
    return base / ("python.exe" if os.name == "nt" else "python")


def copy_fixture(name):
    target = WORK / name
    shutil.copytree(FIXTURE, target)
    return target


def version_of(python):
    return run(
        [str(python), "-c", "import openharness; print(openharness.__version__)"], WORK
    ).stdout.strip()


def main(args: argparse.Namespace) -> int:
    global ROOT, FIXTURE, QUICK
    ROOT = Path(args.root).resolve()
    FIXTURE = ROOT / "tests" / "fixtures" / "harness"
    QUICK = args.quick
    if not FIXTURE.is_dir():
        print(f"not an OpenHarness repository: {ROOT}")
        return 2
    print(f"workdir {WORK}")
    dist = WORK / "dist"
    built = run([sys.executable, "-m", "build", "--sdist", "--wheel", "--outdir", str(dist)], ROOT)
    check("build sdist+wheel", built.returncode == 0, built.stderr[-800:])
    wheels = sorted(dist.glob("*.whl"))
    sdists = sorted(dist.glob("*.tar.gz"))
    check("wheel artifact", len(wheels) == 1, str(wheels))
    check("sdist artifact", len(sdists) == 1, str(sdists))
    if not wheels:
        return finish()
    wheel = wheels[0]
    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
    check("wheel ships py.typed", "openharness/py.typed" in names)
    check(
        "wheel ships every command",
        all(
            f"openharness/commands/{name}.py" in names
            for name in (
                "init",
                "lock",
                "plan",
                "audit",
                "context",
                "verify",
                "select",
                "cases",
                "telemetry",
                "inventory",
                "failures",
                "policy",
                "report",
            )
        ),
    )
    metadata = next((name for name in names if name.endswith(".dist-info/METADATA")), None)
    if metadata:
        with zipfile.ZipFile(wheel) as archive:
            text = archive.read(metadata).decode("utf-8")
        check("metadata requires Python >= 3.10", "Requires-Python: >=3.10" in text, text[:300])
        check("metadata declares typed package", "Typing :: Typed" in text)
    entry = next((name for name in names if name.endswith(".dist-info/entry_points.txt")), None)
    if entry:
        with zipfile.ZipFile(wheel) as archive:
            text = archive.read(entry).decode("utf-8")
        check("console script entry point", "openharness = openharness.cli:main" in text, text)

    # Clean environment installed from the wheel only.
    env_a = WORK / "venv_wheel"
    venv.EnvBuilder(with_pip=True).create(env_a)
    python_a = venv_python(env_a)
    installed = run(
        [str(python_a), "-m", "pip", "install", "--quiet", "--no-index", str(wheel)], WORK
    )
    check("wheel installs offline", installed.returncode == 0, installed.stderr[-800:])
    expected = version_of(python_a)
    check("wheel import version", expected == "0.2.0", expected)

    cli = [str(python_a), "-m", "openharness"]
    module = run([str(python_a), "-m", "openharness", "--version"], WORK)
    check(
        "python -m entry point", module.returncode == 0 and expected in module.stdout, module.stderr
    )
    console = python_a.parent / ("openharness.exe" if os.name == "nt" else "openharness")
    check("console script installed", console.is_file(), str(console))

    for command in (
        "init",
        "lock",
        "plan",
        "audit",
        "context",
        "verify",
        "select",
        "cases",
        "telemetry",
        "inventory",
        "failures",
        "policy",
        "report",
    ):
        helped = run([*cli, command, "--help"], ROOT)
        check(f"help {command}", helped.returncode == 0, helped.stderr[-300:])
    check("unknown command exits 2", run([*cli, "nope"], ROOT).returncode == 2)
    check("no command exits 2", run(cli, ROOT).returncode == 2)

    fixture = copy_fixture("audit")
    audit = run([*cli, "audit", "--manifest", "harness.json"], fixture)
    check(
        "audit clean exits 0", audit.returncode == 0 and '"ok":true' in audit.stdout, audit.stdout
    )
    check("audit receipt schema", json.loads(audit.stdout)["schema"] == "openharness.receipt.v1")
    again = run([*cli, "audit", "--manifest", "harness.json"], fixture)
    check("audit byte-identical", audit.stdout == again.stdout)
    check(
        "audit broken exits 1",
        run([*cli, "audit", "--manifest", "harness-broken.json"], fixture).returncode == 1,
    )
    check(
        "audit missing manifest exits 2",
        run([*cli, "audit", "--manifest", "absent.json"], fixture).returncode == 2,
    )

    context = run([*cli, "context", "--manifest", "harness.json"], fixture)
    payload = json.loads(context.stdout)
    check("context exits 0", context.returncode == 0, context.stdout)
    check(
        "context layers sum to total",
        payload["tokens"]["resident"]
        + payload["tokens"]["loadable"]
        + payload["tokens"]["executable"]
        == payload["tokens"]["total"],
    )
    check("context check exits 0", run([*cli, "context", "--check"], fixture).returncode == 0)
    check(
        "context text format",
        "resident" in run([*cli, "context", "--format", "text"], fixture).stdout,
    )
    check("context bad top exits 2", run([*cli, "context", "--top", "0"], fixture).returncode == 2)

    lock = run([*cli, "lock"], fixture)
    check("lock writes", lock.returncode == 0 and (fixture / "harness.lock").is_file(), lock.stdout)
    lock_text = (fixture / "harness.lock").read_text(encoding="utf-8")
    run([*cli, "lock"], fixture)
    check("lock reproducible", (fixture / "harness.lock").read_text(encoding="utf-8") == lock_text)
    check("lock check clean", run([*cli, "lock", "--check"], fixture).returncode == 0)
    check("plan check clean", run([*cli, "plan", "--check"], fixture).returncode == 0)
    (fixture / "AGENTS.md").write_text("changed surface\n", encoding="utf-8")
    drifted = run([*cli, "plan", "--check"], fixture)
    check("plan check drift exits 1", drifted.returncode == 1, drifted.stdout)
    check("plan attributes AGENTS.md", "AGENTS.md" in drifted.stdout, drifted.stdout)
    check("plan preview exits 0", run([*cli, "plan"], fixture).returncode == 0)
    check("lock check drift exits 1", run([*cli, "lock", "--check"], fixture).returncode == 1)

    case_dir = copy_fixture("cases")
    dry = run([*cli, "cases", "--cases", "cases.json", "--dry-run"], case_dir)
    check(
        "cases dry-run exits 0",
        dry.returncode == 0 and json.loads(dry.stdout)["count"] == 2,
        dry.stdout,
    )
    only = run([*cli, "cases", "--cases", "cases.json", "--dry-run", "--only", "one"], case_dir)
    check("cases --only filters", only.returncode == 0 and json.loads(only.stdout)["count"] == 1)
    check(
        "cases unknown id exits 2",
        run(
            [*cli, "cases", "--cases", "cases.json", "--dry-run", "--only", "nope"], case_dir
        ).returncode
        == 2,
    )
    executed = run([*cli, "cases", "--cases", "cases.json", "--workdir", "."], case_dir)
    check(
        "cases execute pass",
        executed.returncode == 0 and json.loads(executed.stdout)["passed"] == 2,
        executed.stdout,
    )
    (case_dir / "fail.json").write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "id": "f",
                        "command": 'python -c "raise SystemExit(3)"',
                        "expect": {"exit_code": 0},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    check(
        "cases failure exits 1",
        run([*cli, "cases", "--cases", "fail.json"], case_dir).returncode == 1,
    )

    check(
        "telemetry exits 0",
        run([*cli, "telemetry", "--journal", "journal.jsonl"], fixture).returncode == 0,
    )
    check(
        "telemetry missing journal exits 2",
        run([*cli, "telemetry", "--journal", "absent.jsonl"], fixture).returncode == 2,
    )
    check(
        "inventory exits 0",
        run(
            [
                *cli,
                "inventory",
                "--manifest",
                "harness.json",
                "--requirements",
                "requirements.json",
            ],
            fixture,
        ).returncode
        == 0,
    )
    check(
        "failures exits 0",
        run([*cli, "failures", "--journal", "journal.jsonl"], fixture).returncode == 0,
    )
    check(
        "verify valid exits 0",
        run([*cli, "verify", "--journal", "journal.jsonl"], fixture).returncode == 0,
    )
    stale = run(
        [*cli, "verify", "--journal", "journal-stale.jsonl", "--fingerprint", "b" * 64], fixture
    )
    check("verify stale exits 1", stale.returncode == 1, stale.stdout)

    allow = run(
        [*cli, "policy", "--policy", "policy.json", "--tool", "shell", "--command", "python -B x"],
        fixture,
    )
    deny = run(
        [*cli, "policy", "--policy", "policy.json", "--tool", "shell", "--command", "rm -rf build"],
        fixture,
    )
    ask = run(
        [
            *cli,
            "policy",
            "--policy",
            "policy.json",
            "--tool",
            "shell",
            "--command",
            "Get-Content README.md",
        ],
        fixture,
    )
    check(
        "policy allow exits 0",
        allow.returncode == 0 and json.loads(allow.stdout)["verdict"] == "allow",
        allow.stdout,
    )
    check(
        "policy deny exits 1",
        deny.returncode == 1 and json.loads(deny.stdout)["verdict"] == "deny",
        deny.stdout,
    )
    check(
        "policy ask exits 3",
        ask.returncode == 3 and json.loads(ask.stdout)["verdict"] == "ask",
        ask.stdout,
    )

    select_dir = copy_fixture("select")
    selected = run([*cli, "select", "--candidates", "candidates"], select_dir)
    check(
        "select anonymizes",
        selected.returncode == 0 and (select_dir / "candidates" / "selection.json").is_file(),
    )
    check("select seals mapping", (select_dir / "candidates" / "mapping.json").is_file())
    chosen = run(
        [
            *cli,
            "select",
            "--candidates",
            "candidates",
            "--choose",
            "cand-a",
            "--reason",
            "e2e",
            "--allow-unprobed",
        ],
        select_dir,
    )
    check(
        "select choice recorded",
        chosen.returncode == 0 and json.loads(chosen.stdout)["chosen"] == "cand-a",
        chosen.stdout,
    )
    check(
        "select unknown exits 2",
        run(
            [*cli, "select", "--candidates", "candidates", "--choose", "cand-z"], select_dir
        ).returncode
        == 2,
    )

    report_dir = copy_fixture("report")
    run([*cli, "lock"], report_dir)
    for fmt, name in (
        ("json", "report.json"),
        ("markdown", "report.md"),
        ("sarif", "report.sarif"),
        ("junit", "report.xml"),
    ):
        result = run(
            [
                *cli,
                "report",
                "--manifest",
                "harness.json",
                "--requirements",
                "requirements.json",
                "--cases",
                "cases.json",
                "--journal",
                "journal.jsonl",
                "--format",
                fmt,
                "--output",
                name,
            ],
            report_dir,
        )
        check(f"report {fmt} exits 0", result.returncode == 0, result.stdout + result.stderr)
        target = report_dir / name
        check(f"report {fmt} exists", target.is_file())
        if fmt in {"json", "sarif"}:
            document = json.loads(target.read_text(encoding="utf-8"))
            check(f"report {fmt} parses", isinstance(document, dict))
            if fmt == "sarif":
                check(
                    "sarif driver", document["runs"][0]["tool"]["driver"]["name"] == "openharness"
                )
        elif fmt == "junit":
            import xml.etree.ElementTree as ET

            check("junit parses", ET.parse(target).getroot().tag == "testsuite")
        else:
            check("markdown content", "# Harness report:" in target.read_text(encoding="utf-8"))
    executed_report = run(
        [
            *cli,
            "report",
            "--manifest",
            "harness.json",
            "--cases",
            "cases.json",
            "--execute",
            "--format",
            "json",
            "--output",
            "exec.json",
        ],
        report_dir,
    )
    check("report --execute exits 0", executed_report.returncode == 0, executed_report.stdout)

    empty = WORK / "empty"
    empty.mkdir()
    empty_init = run([*cli, "init"], empty)
    check("init empty exits 1", empty_init.returncode == 1, empty_init.stdout)
    synthetic = WORK / "synthetic"
    (synthetic / "skills" / "demo").mkdir(parents=True)
    (synthetic / "AGENTS.md").write_text("Use the demo skill.\n", encoding="utf-8")
    (synthetic / "skills" / "demo" / "SKILL.md").write_text(
        "---\nname: demo\ndescription: Demo\n---\nBody\n", encoding="utf-8"
    )
    initialized = run([*cli, "init", "--name", "synthetic"], synthetic)
    check("init synthetic exits 0", initialized.returncode == 0, initialized.stdout)
    check("init writes manifest", (synthetic / "harness.json").is_file())
    check("init writes lock", (synthetic / "harness.lock").is_file())
    check(
        "init output audits clean",
        run([*cli, "audit", "--manifest", "harness.json"], synthetic).returncode == 0,
    )
    check("init lock matches", run([*cli, "lock", "--check"], synthetic).returncode == 0)
    check("init plan clean", run([*cli, "plan", "--check"], synthetic).returncode == 0)

    # Emulate the composite action's shell steps exactly.
    action_env = {"PYTHONPATH": str(ROOT / "skills" / "loop" / "scripts")}
    action_fixture = copy_fixture("action")
    for label, argv in (
        (
            "action report",
            [
                "report",
                "--manifest",
                "harness.json",
                "--lock",
                "harness.lock",
                "--requirements",
                "requirements.json",
                "--cases",
                "cases.json",
                "--format",
                "markdown",
                "--output",
                "harness-report.md",
            ],
        ),
        ("action audit", ["audit", "--manifest", "harness.json"]),
        (
            "action inventory",
            ["inventory", "--manifest", "harness.json", "--requirements", "requirements.json"],
        ),
    ):
        result = run(cli + argv, action_fixture, env=action_env)
        check(f"{label} exits 0", result.returncode == 0, (result.stdout + result.stderr)[-500:])
    run([*cli, "lock"], action_fixture, env=action_env)
    drift = run(
        [*cli, "plan", "--check", "--manifest", "harness.json", "--lock", "harness.lock"],
        action_fixture,
        env=action_env,
    )
    check("action drift gate exits 0", drift.returncode == 0, drift.stdout)
    check("action wrote report", (action_fixture / "harness-report.md").is_file())

    # Install the loop skill bundle and run the packaged CLI from it.
    bundle = WORK / "installed-loop"
    installer = run(
        [
            sys.executable,
            "-B",
            str(ROOT / "tools" / "install_skill.py"),
            "--skill",
            "loop",
            "--to",
            str(bundle),
        ],
        ROOT,
    )
    check("loop bundle installs", installer.returncode == 0, installer.stderr[-500:])
    bundle_cli = bundle / "scripts" / "openharness_cli.py"
    check("bundle ships CLI", bundle_cli.is_file())
    bundle_version = run([sys.executable, "-B", str(bundle_cli), "--version"], fixture)
    check(
        "bundle CLI version",
        bundle_version.returncode == 0 and expected in bundle_version.stdout,
        bundle_version.stderr,
    )
    bundle_context = run(
        [sys.executable, "-B", str(bundle_cli), "context", "--manifest", "harness.json"], fixture
    )
    check("bundle CLI context", bundle_context.returncode == 0, bundle_context.stderr)

    # Install from the sdist as a distribution proxy for a source release.
    env_b = WORK / "venv_sdist"
    if not QUICK:
        venv.EnvBuilder(with_pip=True).create(env_b)
        python_b = venv_python(env_b)
        sdist_install = run(
            [str(python_b), "-m", "pip", "install", "--quiet", str(sdists[0])], WORK
        )
        check("sdist installs", sdist_install.returncode == 0, sdist_install.stderr[-800:])
        if sdist_install.returncode == 0:
            sdist_version = run([str(python_b), "-m", "openharness", "--version"], WORK)
            check(
                "sdist CLI runs", sdist_version.returncode == 0 and expected in sdist_version.stdout
            )
            sdist_context = run(
                [str(python_b), "-m", "openharness", "context", "--manifest", "harness.json"],
                copy_fixture("sdist"),
            )
            check("sdist context runs", sdist_context.returncode == 0, sdist_context.stderr[-300:])

    # Python 3.11 runtime, matching the package's declared floor family.
    launcher = shutil.which("py") or shutil.which("py.exe")
    if launcher and not QUICK:
        env_c = WORK / "venv311"
        made = run([launcher, "-3.11", "-m", "venv", str(env_c)], WORK)
        check("python 3.11 venv", made.returncode == 0, made.stderr[-400:])
        if made.returncode == 0:
            python_c = venv_python(env_c)
            installed_c = run(
                [str(python_c), "-m", "pip", "install", "--quiet", "--no-index", str(wheel)], WORK
            )
            check(
                "python 3.11 wheel install", installed_c.returncode == 0, installed_c.stderr[-400:]
            )
            version_c = run([str(python_c), "-m", "openharness", "--version"], WORK)
            check("python 3.11 CLI runs", version_c.returncode == 0, version_c.stderr[-300:])
            fixture_c = copy_fixture("py311")
            check(
                "python 3.11 context runs",
                run(
                    [str(python_c), "-m", "openharness", "context", "--manifest", "harness.json"],
                    fixture_c,
                ).returncode
                == 0,
            )
            check(
                "python 3.11 lock/plan run",
                run([str(python_c), "-m", "openharness", "lock"], fixture_c).returncode == 0
                and run(
                    [str(python_c), "-m", "openharness", "plan", "--check"], fixture_c
                ).returncode
                == 0,
            )

    # Clean checkout: committed bytes, committed lock, and the whole suite.
    clone = WORK / "clone"
    cloned = run(["git", "clone", "--quiet", "--no-hardlinks", str(ROOT), str(clone)], WORK)
    check("git clone", cloned.returncode == 0, cloned.stderr[-400:])
    if cloned.returncode == 0:
        clone_env = {"PYTHONPATH": str(clone / "skills" / "loop" / "scripts")}
        for label, argv in (
            ("clone lock", ["lock", "--check"]),
            ("clone plan", ["plan", "--check"]),
            ("clone context", ["context", "--check"]),
        ):
            result = run([sys.executable, "-B", "-m", "openharness", *argv], clone, env=clone_env)
            check(
                f"{label} passes on committed bytes",
                result.returncode == 0,
                (result.stdout + result.stderr)[-500:],
            )
        if not QUICK:
            suite = run([sys.executable, "-B", "-m", "pytest", "-q"], clone, timeout=900)
            check(
                "clean-clone full suite passes",
                suite.returncode == 0,
                (suite.stdout + suite.stderr)[-1200:],
            )
            release = run([sys.executable, "-B", "tools/check_release.py"], clone)
            check(
                "clean-clone release checks pass",
                release.returncode == 0,
                (release.stdout + release.stderr)[-800:],
            )

    return finish()


def finish():
    print(f"\n{CHECKS} checks, {len(FAILURES)} failures")
    for failure in FAILURES:
        print(f"FAILED {failure}")
    return 0 if not FAILURES else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "root",
        nargs="?",
        default=str(DEFAULT_ROOT),
        help="repository root (default: the checkout containing this script)",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="skip the sdist install, alternate interpreter, and clean-clone test suite",
    )
    sys.exit(main(parser.parse_args()))

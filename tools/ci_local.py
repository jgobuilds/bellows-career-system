#!/usr/bin/env python3
"""Run the CI gate locally, in CI's environment rather than yours.

    python tools/ci_local.py

WHY THIS EXISTS: the local suite and CI are not the same run, and the difference
is invisible until CI goes red.

CI checks out TRACKED FILES ONLY and scaffolds `personal/userconfig.py` from
`starter/userconfig.template.py`. Your machine has a real, filled-in config and a
populated personal/ folder. So a test that quietly depends on your config — a
hard-coded city that only exists in YOUR GEO_EXCLUDE, say — passes locally every
time and fails on every push. That exact bug shipped twice before this script
existed, and both times the local suite was green.

This reproduces CI: a temp copy of the tracked tree, the template scaffolded as
the config, then the same four commands in the same order the workflow runs them.

It touches nothing in your working tree and never reads personal/.
"""

import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Mirrors .github/workflows/quality.yml. Keep in step with it: a check that runs
# there and not here rebuilds the blind spot this script exists to remove.
STEPS = [
    ("Lint (ruff)", [sys.executable, "-m", "ruff", "check", "."]),
    ("Format check (ruff)", [sys.executable, "-m", "ruff", "format", "--check", "."]),
    ("Tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests"]),
    ("Type check (mypy)", [sys.executable, "-m", "mypy", "engine"]),
]


def tracked_files() -> list[str]:
    """Tracked files PLUS untracked ones that aren't gitignored.

    `git ls-files` alone was the first version and it had the same blind spot this
    script exists to remove: a brand-new test file is untracked until `git add`,
    so it never reached the sandbox and the run came back green while containing
    the very bug being checked for. --others --exclude-standard adds exactly the
    files you are about to commit, and still excludes personal/.
    """
    out = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    )
    return sorted({line for line in out.stdout.splitlines() if line.strip()})


def build_sandbox(dest: str) -> int:
    """Copy the tracked tree and scaffold config exactly as the workflow does."""
    files = tracked_files()
    for rel in files:
        src = os.path.join(REPO, rel)
        if not os.path.isfile(src):  # a deleted-but-tracked path
            continue
        dst = os.path.join(dest, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)

    # The workflow's "Scaffold config (tests import it)" step, verbatim in effect.
    os.makedirs(os.path.join(dest, "personal", "data"), exist_ok=True)
    shutil.copy2(
        os.path.join(dest, "starter", "userconfig.template.py"),
        os.path.join(dest, "personal", "userconfig.py"),
    )
    with open(os.path.join(dest, "personal", "data", "jobs.json"), "w", encoding="utf-8") as fh:
        fh.write('{"jobs": []}\n')
    return len(files)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="bellows-ci-") as sandbox:
        n = build_sandbox(sandbox)
        print(f"CI sandbox: {n} tracked files, template config scaffolded")
        print(f"  {sandbox}\n")

        failures = []
        for name, cmd in STEPS:
            res = subprocess.run(cmd, cwd=sandbox, capture_output=True, text=True)
            ok = res.returncode == 0
            print(f"  {'PASS' if ok else 'FAIL'}  {name}")
            if not ok:
                failures.append((name, (res.stdout + res.stderr).strip()))

        if not failures:
            print("\nGreen. This is what CI will see.")
            return 0

        print(f"\n{len(failures)} step(s) failed IN CI'S ENVIRONMENT.")
        print("Your local run may well be green — that is the point of this script.\n")
        for name, output in failures:
            print(f"--- {name} " + "-" * (60 - len(name)))
            tail = output.splitlines()
            print("\n".join(tail[-40:]) if len(tail) > 40 else output)
            print()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

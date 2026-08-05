#!/usr/bin/env python3
"""
setup.py — one-command first-time setup for Bellows.

Creates your gitignored personal/ folder and copies the blank starter templates
into it (renaming <name>.template.<ext> -> <name>.<ext>), so you can go straight
to filling in your details instead of copying files by hand.

    python setup.py

Safe to re-run: it NEVER overwrites a file you've already created — it only adds
what's missing and reports what it left alone. It does NOT install the Claude
skills (that's a Claude Desktop action) and it does NOT write your career profile
(the career-profile skill interviews you for that). It just scaffolds the files.
"""

import os
import shutil

BANNER = r"""
    ____       ____
   / __ )___  / / /___ _      _______
  / __  / _ \/ / / __ \ | /| / / ___/
 / /_/ /  __/ / / /_/ / |/ |/ (__  )
/_____/\___/_/_/\____/|__/|__/____/

   AI career coach + job-search copilot
"""

REPO = os.path.dirname(os.path.abspath(__file__))
STARTER = os.path.join(REPO, "starter")
PERSONAL = os.path.join(REPO, "personal")

# starter template basename -> destination path (relative to personal/)
COPIES = {
    "userconfig.template.py": "userconfig.py",
    "career-profile.template.md": "career-profile.md",
    "writing-style.template.md": "writing-style.md",
    "reconnect-list.template.md": "reconnect-list.md",
    "resume-style-rules.template.md": "resume-style-rules.md",
    "pipeline.template.md": os.path.join("data", "pipeline.md"),
    "leads.template.md": os.path.join("data", "leads.md"),
    # The gate that runs before every application: what LinkedIn currently says, so
    # the resume can be checked against the page it will be verified against.
    "linkedin-profile-state.template.json": os.path.join("linkedin", "profile-state.json"),
}
# files to seed empty (so the local server + board work on day one)
SEED = {
    os.path.join("data", "jobs.json"): '{"jobs": []}\n',
}


# Git hooks. These are the gates, and `.git/hooks/` is never tracked by git, so a fresh
# clone has none of them and the only instruction is a copy-paste block in CONTRIBUTING
# that is easy to skip. Installing them in the step everyone already runs is the
# difference between a documented gate and an enforced one.
#
# Non-destructive: an existing hook is left exactly as it is and reported, because it
# may be one somebody wrote deliberately.
HOOKS = {
    "pre-push": [
        "#!/bin/sh",
        "# Runs the CI gate in CI's own environment before every push. A plain script,",
        "# not the pre-commit framework: that wrapper ran commit-stage hooks at push",
        "# time and hung on Windows. Installed by setup.py.",
        "exec python tools/ci_local.py",
    ],
    "commit-msg": [
        "#!/bin/sh",
        "# Keeps career details out of permanent, public commit messages.",
        "# Installed by setup.py.",
        'exec python tools/check_commit_msg.py "$1"',
    ],
}


def install_hooks():
    """(installed, left_alone, note). Never overwrites an existing hook."""
    import subprocess

    if not os.path.isdir(os.path.join(REPO, ".git")):
        return [], [], "not a git checkout, so there is nowhere to install them"

    # Respect a configured hooksPath rather than writing where git will not look.
    configured = ""
    try:
        proc = subprocess.run(
            ["git", "-C", REPO, "config", "--get", "core.hooksPath"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        configured = proc.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    hook_dir = os.path.join(REPO, configured) if configured else os.path.join(REPO, ".git", "hooks")

    try:
        os.makedirs(hook_dir, exist_ok=True)
    except OSError as e:
        return [], [], f"could not create {hook_dir} ({e})"

    installed, left = [], []
    for name, lines in HOOKS.items():
        dest = os.path.join(hook_dir, name)
        if os.path.exists(dest):
            left.append(name)
            continue
        try:
            # LF endings: these run under sh, and CRLF breaks the shebang.
            with open(dest, "w", encoding="utf-8", newline="\n") as fh:
                fh.write("\n".join(lines) + "\n")
            # Executable, or git silently skips it - which is the failure this whole
            # function exists to prevent. 0o755 is what a git hook has to be.
            os.chmod(dest, 0o755)  # noqa: S103
            installed.append(name)
        except OSError as e:
            left.append(f"{name} (failed: {e})")
    return installed, left, ""


def main():
    created, skipped, missing = [], [], []

    for d in (
        PERSONAL,
        os.path.join(PERSONAL, "data"),
        os.path.join(PERSONAL, "applications"),
        os.path.join(PERSONAL, "linkedin"),
    ):
        os.makedirs(d, exist_ok=True)

    for tmpl, dest_rel in COPIES.items():
        src = os.path.join(STARTER, tmpl)
        dest = os.path.join(PERSONAL, dest_rel)
        if not os.path.exists(src):
            missing.append("starter/" + tmpl)
            continue
        if os.path.exists(dest):
            skipped.append(dest_rel)
            continue
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copyfile(src, dest)
        created.append(dest_rel)

    for dest_rel, content in SEED.items():
        dest = os.path.join(PERSONAL, dest_rel)
        if os.path.exists(dest):
            skipped.append(dest_rel)
            continue
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(content)
        created.append(dest_rel)

    print(BANNER)
    if created:
        print("Created in personal/:")
        for c in created:
            print("  + " + c.replace("\\", "/"))
    if skipped:
        print("Left alone (already exist):")
        for s in skipped:
            print("  = " + s.replace("\\", "/"))
    if missing:
        print("Missing starter templates (skipped):")
        for m in missing:
            print("  ! " + m)

    hooked, kept, note = install_hooks()
    if hooked or kept or note:
        print("\nGit hooks:")
        for h in hooked:
            print("  + " + h + " installed")
        for k in kept:
            print("  = " + k + " already present, left alone")
        if note:
            print("  ! " + note)
        if hooked:
            print("    pre-push runs tools/ci_local.py, which reproduces CI's environment")
            print("    rather than yours. It is the difference between a green local run")
            print("    and a green build.")

    try:
        import docx  # noqa: F401 — python-docx, used by the résumé/cover builders

        dep = "python-docx: OK"
    except ImportError:
        dep = "python-docx: MISSING — run `pip install python-docx` before building résumés"
    print("\nDependencies: " + dep)

    launcher = "bellows.bat" if os.name == "nt" else "./bellows.sh"
    print(
        """
Next steps:
  1. Edit personal/userconfig.py — your targets, level, companies, comp.
  2. Install the skills in skills/ (Claude Desktop: Settings -> Capabilities -> add skill).
  3. In Claude: "Let's build my career profile" (writes personal/career-profile.md),
     then "build my writing style" (writes personal/writing-style.md).
  4. Run a sweep:          python engine/jobspy_sweep.py
  5. Open the Career Hub:  %s

Your personal/ folder is gitignored — your data never enters the repo.
"""
        % launcher
    )


if __name__ == "__main__":
    main()

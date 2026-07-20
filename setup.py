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
}
# files to seed empty (so the local server + board work on day one)
SEED = {
    os.path.join("data", "jobs.json"): '{"jobs": []}\n',
}


def main():
    created, skipped, missing = [], [], []

    for d in (PERSONAL, os.path.join(PERSONAL, "data"), os.path.join(PERSONAL, "applications")):
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

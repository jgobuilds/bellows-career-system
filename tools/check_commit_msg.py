#!/usr/bin/env python3
"""Block career details from entering commit messages.

    python tools/check_commit_msg.py <path-to-commit-msg-file>

WHY THIS EXISTS: `personal/` being gitignored protects the FILES, not the prose a
developer writes about them. A commit message is permanent, public, and sits outside
every check that guards the working tree. And the failure mode is systematic rather
than careless: bugs in this repo are usually found by running a real resume through
it, so the natural way to explain a fix is to quote the real thing that broke.

On 2026-07-24 a commit opened by naming a tool, an employer's warehouse, and the
resume bullet that got them wrong. Nothing in the tree was leaked; the message did it.

WHAT IT CHECKS: employer names are read from the gitignored profile, so the list is
never hardcoded here (this file is tracked and public). Money figures and the
achievement-shaped percentages that show up in resume bullets are matched by pattern.

Exit 1 blocks the commit. Rewrite the message to describe the DEFECT CLASS, not the
history: "developer caught an incorrect bullet; additional checks added."
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROFILE = os.path.join(ROOT, "personal", "career-profile.md")

# Corporate filler in employer headings: no identifying signal, and matching on it
# would block ordinary sentences ("the group", "company sponsorship").
FILLER = {
    "THE",
    "LLC",
    "INC",
    "GROUP",
    "COMPANY",
    "AMERICA",
    "INSURANCE",
    "FINANCIAL",
    "SERVICES",
    "DATA",
    "LIFE",
    "CORP",
    "HOLDINGS",
    "SYSTEMS",
    "SOLUTIONS",
    "TECHNOLOGIES",
}

# Real git trailers, not the "component:" prefix this repo uses on subject lines.
TRAILER = re.compile(
    r"^(Co-Authored-By|Signed-off-by|Reviewed-by|Acked-by|Tested-by|Reported-by|"
    r"Cc|Fixes|Closes|Refs|Change-Id):\s",
    re.I,
)

# Achievement-shaped numbers: the ones that appear in resume bullets, not the ones
# that appear in code review ("a 30% speedup" is fine; "$250K cancelled" is not).
MONEY = re.compile(r"\$\s?\d[\d,.]*\s?(?:K|M|k|m|million|thousand)?\b")
SCALE = re.compile(r"\b\d{1,3},\d{3}\+?\s+(?:reports|users|developers|employees|records)\b", re.I)

# Words that mean the message is discussing the USER'S RECORD rather than the code.
# They gate the stricter checks below, because the same tool name is fine in
# "add BigQuery to the skills vocabulary" and a leak in "the bullet said BigQuery".
CAREER_CONTEXT = re.compile(
    r"\b(r[ée]sum[ée]s?|cover letter|bullet|career.profile|the profile said|employer|"
    r"posting|job description|applied to)\b",
    re.I,
)
# A quoted phrase of three or more words. In a career context this is almost always
# a real line lifted from a document: the exact leak that started this file.
# DOUBLE quotes only. Treating the apostrophe as a delimiter made an ordinary
# possessive ("this repo's own") close a quote opened earlier in the sentence and
# blocked a legitimate commit.
QUOTED = re.compile(r"[\"“”]([^\"“”\n]{12,}?\s+\S+\s+\S+[^\"“”\n]*)[\"“”]")
# Warehouse / BI / DS tooling. These describe the user's stack; the ATS vendor names
# this repo actually integrates with (Greenhouse, Lever, Ashby, Workday) are not here
# on purpose, because those are a legitimate everyday code topic.
STACK_TOOLS = re.compile(
    r"\b(snowflake|bigquery|redshift|databricks|synapse|quantexa|dremio|thoughtspot|"
    r"businessobjects|dataiku|metabase|sigma|talend|informatica|elementary|atlan)\b",
    re.I,
)


def employers_from_profile(path=PROFILE):
    """Employer names as the profile states them. Empty if there is no profile —
    a contributor without one still gets the money and scale checks."""
    if not os.path.exists(path):
        return []
    names = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            # Just capture the leading ALL-CAPS run. Requiring a specific terminator
            # kept missing real headings: "THE GUARDIAN LIFE ..." yielded only "THE",
            # and a parenthetical after the name stopped the match entirely.
            m = re.match(r"^#{2,4}\s+([A-Z][A-Z0-9 &.']{2,60})", line.rstrip())
            if not m:
                continue
            # Keep every distinctive word, not just the first: the leak could name
            # any of them. Corporate filler carries no identifying signal.
            for word in m.group(1).split():
                if len(word) > 3 and word not in FILLER:
                    names.append(word.lower())
    return sorted(set(names))


def findings(message, employers=None):
    """Career details detected in a commit message, as human-readable strings."""
    employers = employers_from_profile() if employers is None else employers
    # Ignore git trailers only — Co-Authored-By carries a name by design.
    # Matching a generic "word:" prefix instead silently skipped every subject line
    # in this repo's "component: summary" convention, so nothing was ever scanned.
    body = "\n".join(ln for ln in message.splitlines() if not TRAILER.match(ln.strip()))
    low = body.lower()
    out = []
    for e in employers:
        if re.search(rf"\b{re.escape(e)}\b", low):
            out.append(f"employer name {e!r}")
    for m in MONEY.finditer(body):
        out.append(f"money figure {m.group(0).strip()!r}")
    for m in SCALE.finditer(body):
        out.append(f"scale figure {m.group(0).strip()!r}")

    # Stricter net, only where the message is already talking about the record.
    # This is what the employer-name check misses: the message that started this
    # file never named an employer — it quoted a bullet and named the warehouses.
    if CAREER_CONTEXT.search(body):
        for m in QUOTED.finditer(body):
            snippet = m.group(1).strip()
            out.append(f"quoted document text {snippet[:48]!r}")
        for m in STACK_TOOLS.finditer(body):
            out.append(f"stack tool {m.group(0)!r} in a career context")
    return sorted(set(out))


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python tools/check_commit_msg.py <commit-msg-file>")
    with open(sys.argv[1], encoding="utf-8") as fh:
        message = fh.read()
    # Comment lines are stripped by git before the message is stored.
    message = "\n".join(ln for ln in message.splitlines() if not ln.startswith("#"))

    found = findings(message)
    if not found:
        return 0

    print("BLOCKED: the commit message contains career details.\n")
    for f in found:
        print(f"  - {f}")
    print(
        "\nCommit messages are permanent and public. Describe the DEFECT CLASS and the fix,"
        "\nnot the history behind it. For example:"
        '\n\n    "Developer caught an incorrect bullet; additional checks added."'
        "\n\nReproduction detail belongs in a test (fictional) or in gitignored notes."
        "\nSee CONTRIBUTING.md > House rules."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

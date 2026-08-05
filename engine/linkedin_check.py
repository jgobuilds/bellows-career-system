#!/usr/bin/env python3
"""
linkedin_check.py — LinkedIn is a foundational step, not a nice-to-have.

    python engine/linkedin_check.py                       # is the profile current?
    python engine/linkedin_check.py <application-dir>      # ...and does the resume agree with it?

WHY THIS IS A GATE AND NOT ADVICE. LinkedIn does two jobs in a search, and both fail
silently.

  1. IT GENERATES THE LEADS. A profile that does not say what you now do is invisible to
     the recruiters searching for exactly that. Nothing tells you about the inbound you
     did not get, so this failure has no symptom at all.

  2. IT IS WHERE THE RESUME GETS VERIFIED. A recruiter with your resume open will pull up
     your profile, and any disagreement about employer, title or dates reads as a
     discrepancy rather than as a stale page. That is a credibility problem in the one
     document set where credibility is the whole product, and it is entirely avoidable.

So the resume is not really "done" until the profile it will be checked against agrees
with it. This runs at build time and says so.

THE SNAPSHOT IS HAND-MAINTAINED ON PURPOSE. LinkedIn has no read API for your own profile
worth relying on, and scraping it is against their terms. So `personal/linkedin/
profile-state.json` records what the profile CURRENTLY shows, updated by the person who
just changed it. That is a weaker guarantee than reading the live page and a much
stronger one than assuming - a stale snapshot is at least a DATED claim, and the staleness
check turns "I think I updated it" into a question with an answer.
"""

import argparse
import datetime
import json
import os
import re
import sys

import _paths  # noqa: F401  (side-effect: repo root on sys.path for `import config`)
import config

STATE = os.path.join(os.path.dirname(config.PROFILE_MD), "linkedin", "profile-state.json")

# How long before a snapshot stops meaning anything. A search moves faster than a career
# does, but a profile that has not been looked at in a quarter has usually drifted.
STALE_DAYS = 90

_MONTHS = "jan feb mar apr may jun jul aug sep oct nov dec".split()


def _norm_co(s: str | None) -> str:
    """Company names, loosely."""
    s = re.sub(r"[^a-z0-9 ]", " ", (s or "").lower())
    for junk in (
        " incorporated",
        " inc",
        " llc",
        " ltd",
        " group",
        " company",
        " corporation",
        " corp",
        " holdings",
        " financial services",
        " financial",
        " services",
    ):
        s = s.replace(junk, " ")
    s = re.sub(r"^the ", " ", " " + s)
    return " ".join(s.split())


def _same_co(a: str | None, b: str | None) -> bool:
    """Do these two strings name the same employer?

    Containment, not equality. A resume writes the legal name and a profile writes what
    people call it: "The Hartford Financial Services Group" against "The Hartford" is a
    formatting difference, not a conflict, and flagging it would be the fastest way to
    teach someone to ignore this check. Equality on the whole string is too strict to
    survive contact with how humans actually write employers.
    """
    x, y = _norm_co(a), _norm_co(b)
    if not x or not y:
        return False
    return x == y or x.startswith(y + " ") or y.startswith(x + " ") or x in y or y in x


def _norm_title(s: str | None) -> str:
    """Titles, with punctuation and conjunctions flattened.

    "Director of Data Governance and Platform & Apps" and "Director of Data Governance,
    Platform & Apps" are the SAME TITLE written two ways - and in this repo the first
    form is a documented, deliberate choice because a comma got truncated by an ATS. A
    check that cannot see past a comma would fire on a rule the system itself imposed.
    """
    s = (s or "").lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9 ]", " ", s)
    return " ".join(w for w in s.split() if w not in {"and", "of", "the", "for", "a"})


def _dates(s: str | None) -> tuple[str, ...] | None:
    """(start, end) as 'mon yyyy' tokens, or None. Accepts 'April 2024 - Present',
    'Apr 2024 – Present', '2019-2022' and the en-dash LinkedIn actually emits."""
    if not s:
        return None
    text = (s.split("|")[-1] if "|" in s else s).lower().replace("–", "-").replace("—", "-")
    out = []
    for part in text.split("-"):
        part = part.strip()
        if not part:
            continue
        if "present" in part or "current" in part:
            out.append("present")
            continue
        m = re.search(r"([a-z]{3,9})?\s*((?:19|20)\d{2})", part)
        if m:
            mon = (m.group(1) or "")[:3]
            out.append(f"{mon} {m.group(2)}".strip() if mon in _MONTHS else m.group(2))
    return tuple(out[:2]) if out else None


def load_state(path: str = STATE) -> dict | None:
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def staleness(
    state: dict | None, today: datetime.date | None = None
) -> tuple[int | None, str | None]:
    """(days_old, warning) for the snapshot's as_of date."""
    if not state:
        return None, (
            "No LinkedIn snapshot at all. Nothing can check the resume against the profile "
            "it will be verified against - create personal/linkedin/profile-state.json."
        )
    raw = (state.get("as_of") or "").strip()
    try:
        as_of = datetime.date.fromisoformat(raw[:10])
    except ValueError:
        return None, f"LinkedIn snapshot has no usable as_of date (got {raw!r})."
    days = ((today or datetime.date.today()) - as_of).days
    if days > STALE_DAYS:
        return days, (
            f"LinkedIn snapshot is {days} days old (as_of {as_of}). Past {STALE_DAYS} days a "
            "profile has usually drifted from the resume, and the drift is invisible until a "
            "recruiter finds it."
        )
    return days, None


def _resume_roles(spec: dict) -> list[tuple[str, str, str]]:
    """(company, title, location_dates) for every role in a resume spec, including the
    nested multi-role company blocks and the advisory section."""
    out: list[tuple[str, str, str]] = []
    for entry in spec.get("experience", []) or []:
        co = entry.get("company", "")
        if entry.get("roles"):
            for r in entry["roles"]:
                out.append((co, r.get("title", ""), r.get("location_dates", "")))
        else:
            out.append((co, entry.get("title", ""), entry.get("location_dates", "")))
    for entry in spec.get("advisory", []) or []:
        out.append(
            (entry.get("company", ""), entry.get("title", ""), entry.get("location_dates", ""))
        )
    return out


def compare(spec: dict, state: dict | None) -> list[str]:
    """Warnings where the resume and the recorded profile disagree.

    Only the THREE VERIFIABLE FACTS are compared - employer, title, dates. Bullet wording
    is expected to differ; LinkedIn is a different register and the optimizer skill says
    so. A wording diff is not a discrepancy, and flagging one would train people to
    ignore the real ones.
    """
    warns: list[str] = []
    if not state:
        return warns
    live = state.get("experience") or []
    for co, title, loc_dates in _resume_roles(spec):
        if not (co or title):
            continue
        matches = [e for e in live if _same_co(e.get("company"), co)]
        if not matches:
            # Deliberate naming differences are declared in the snapshot rather than
            # guessed at - a resume may say 'Self-Employed' where the profile says the
            # LLC, and that is a choice, not drift.
            for alias_from, alias_to in (state.get("aliases") or {}).items():
                if _same_co(alias_from, co):
                    matches = [e for e in live if _same_co(e.get("company"), alias_to)]
                    break
        if not matches:
            warns.append(
                f"LINKEDIN: resume lists '{title}' at {co}, which is not on the recorded "
                "profile at all. A recruiter cross-checking will not find it."
            )
            continue
        titles = {_norm_title(e.get("title")) for e in matches}
        if _norm_title(title) not in titles:
            shown = ", ".join(sorted((e.get("title") or "") for e in matches)) or "(none)"
            warns.append(
                f"LINKEDIN: title mismatch at {co}. Resume says '{title}', profile says "
                f"{shown}. Recruiters read that as a discrepancy, not a stale page."
            )
        rd = _dates(loc_dates)
        if rd:
            parsed = (_dates(e.get("dates") or e.get("location_dates")) for e in matches)
            live_dates = {d for d in parsed if d is not None}
            if live_dates and rd not in live_dates:
                shown = "; ".join(" to ".join(d) for d in sorted(live_dates))
                warns.append(
                    f"LINKEDIN: dates differ at {co}. Resume says {' to '.join(rd)}, profile "
                    f"says {shown}."
                )
    return warns


def check(
    spec: dict | None = None, path: str = STATE, today: datetime.date | None = None
) -> list[str]:
    """All LinkedIn warnings for an optional resume spec. Empty list means clear."""
    state = load_state(path)
    warns: list[str] = []
    _, stale = staleness(state, today=today)
    if stale:
        warns.append("LINKEDIN: " + stale)
    if spec:
        warns.extend(compare(spec, state))
    return warns


def main() -> int:
    ap = argparse.ArgumentParser(description="Check LinkedIn is current and agrees with a resume.")
    ap.add_argument("application", nargs="?", help="personal/applications/<name> (optional)")
    a = ap.parse_args()

    spec = None
    if a.application:
        p = a.application
        if not os.path.isabs(p):
            p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), p)
        rj = p if p.endswith(".json") else os.path.join(p, "resume.json")
        if not os.path.exists(rj):
            print(f"  no resume spec at {rj}")
            return 2
        with open(rj, encoding="utf-8") as fh:
            spec = json.load(fh)

    state = load_state()
    if state:
        days, _ = staleness(state)
        print(
            f"  profile snapshot: as_of {state.get('as_of')}"
            + (f" ({days} days old)" if days is not None else "")
        )
        print(f"  headline: {state.get('headline', '(not recorded)')[:90]}")
        print(f"  roles recorded: {len(state.get('experience') or [])}")
    else:
        print(f"  no snapshot at {STATE}")

    warns = check(spec)
    print()
    if not warns:
        print(
            "  LinkedIn is current and agrees with the resume."
            if spec
            else "  LinkedIn snapshot is current."
        )
        return 0
    print(f"  {len(warns)} issue(s) to fix BEFORE applying:")
    for w in warns:
        print(f"    - {w}")
    print(
        "\n  LinkedIn is where the resume gets verified and where inbound leads come from.\n"
        "  Update the profile, then update personal/linkedin/profile-state.json to match."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())

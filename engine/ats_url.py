#!/usr/bin/env python3
"""ats_url.py — resolve a company name to its ATS careers board.

WHAT IT IS: a pure lookup from a pipeline job's company name to the public careers
board for that company, built from the `COMPANIES` list the user already maintains
in personal/userconfig.py. The Hub shows it next to the company in the job drawer,
so validating a posting at source is one click instead of a hand-built search.

WHY IT EXISTS: a lot of pipeline rows carry aggregator URLs (Indeed, Built In) and
a "⚠ JD unvalidated - validate at source" flag. The ATS board is where the real,
current posting lives; aggregators go stale and drop details.

WHAT IT IS NOT: a per-JOB deep link. It resolves the company's board, not the exact
requisition -- the sweep records the direct posting URL in `url` when it has one.
It also invents nothing: a company that isn't in COMPANIES returns None.

    from ats_url import ats_url_for
    ats_url_for("The Hartford", config.COMPANIES)
"""

import re

_NON_ALNUM = re.compile(r"[^a-z0-9]+")
# Corporate suffixes and filler that appear in a posting's company name but never
# in an ATS slug ("Wpromote, LLC" -> "wpromote"; "JPMorganChase" -> "jpmorganchase").
_SUFFIXES = ("inc", "llc", "ltd", "corp", "corporation", "co", "company", "plc", "group", "the")


def _norm(name: str | None) -> str:
    """Company name -> comparable key: lowercase, alphanumeric only, suffixes dropped."""
    if not name:
        return ""
    key = _NON_ALNUM.sub(" ", str(name).lower()).strip()
    parts = [p for p in key.split() if p not in _SUFFIXES]
    return "".join(parts)


def careers_url(entry: dict) -> str | None:
    """The public careers board for one COMPANIES entry, or None if unbuildable."""
    ats = str(entry.get("ats") or "").lower()
    slug = entry.get("slug")
    if ats == "greenhouse" and slug:
        return f"https://job-boards.greenhouse.io/{slug}"
    if ats == "lever" and slug:
        return f"https://jobs.lever.co/{slug}"
    if ats == "ashby" and slug:
        return f"https://jobs.ashbyhq.com/{slug}"
    if ats == "smartrecruiters" and slug:
        return f"https://jobs.smartrecruiters.com/{slug}"
    if ats == "workday":
        tenant, wd, site = entry.get("tenant"), entry.get("wd"), entry.get("site")
        if tenant and wd and site:
            return f"https://{tenant}.{wd}.myworkdayjobs.com/{site}"
    return None


def ats_url_for(company: str | None, companies: list) -> str | None:
    """Resolve a pipeline company name to its ATS board URL, or None if unknown.

    Matches on the normalized company name against each entry's slug/tenant, then
    falls back to a containment check so "Pratt & Whitney (RTX)" can still find
    "rtx". Never guesses across different companies: the shorter side must be at
    least 4 characters, so "co" or "hr" can't match everything."""
    key = _norm(company)
    if not key:
        return None
    scored: list[tuple[int, str]] = []
    for entry in companies or []:
        url = careers_url(entry)
        if not url:
            continue
        for field in ("slug", "tenant"):
            cand = _norm(entry.get(field))
            if not cand:
                continue
            if cand == key:
                return url  # exact match wins immediately
            if len(cand) >= 4 and len(key) >= 4 and (cand in key or key in cand):
                scored.append((len(cand), url))
    if scored:  # longest partial match = most specific
        scored.sort(reverse=True)
        return scored[0][1]
    return None

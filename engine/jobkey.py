#!/usr/bin/env python3
"""jobkey.py — the one canonical answer to "is this the same job?"

Job identity lived in four places with four different rules (the sweep merge, the
scorer's pipeline check, the triage dedupe, and the pipeline writer), and they
disagreed — that's what let "owner" and "Owner.com" both slip in. This module is
the single source of truth they all call now.

Pure string logic: no config, no I/O, no imports beyond `re` — so it's trivially
testable and safe to import anywhere (see tests/test_jobkey.py).

  job_key(co, title)              -> normalized (company, title) tuple, the dedupe key
  existing_keys(jobs)             -> set of job_key tuples for a list of job dicts
  is_duplicate(co, title, keys)   -> already present? tolerant of company suffixes and
                                     the "- Remote"/location noise lead titles carry
"""

import re

# Company-name suffixes stripped before matching, so "Owner.com" == "owner" and
# "The Cigna Group" == "Cigna". Only one suffix is stripped.
_CO_SUFFIXES = (
    "incorporated",
    "inc",
    "llc",
    "ltd",
    "com",
    "group",
    "thegroup",
    "co",
    "corp",
    "company",
)


def norm_co(s: str | None) -> str:
    s = re.sub(r"[^a-z0-9]", "", (s or "").lower())
    for suf in _CO_SUFFIXES:
        if s.endswith(suf) and len(s) > len(suf) + 2:
            return s[: -len(suf)]
    return s


def norm_title(s: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def job_key(co: str | None, title: str | None) -> tuple[str, str]:
    """Canonical (company, title) identity tuple for a posting."""
    return (norm_co(co), norm_title(title))


def existing_keys(jobs: list[dict], co: str = "co", title: str = "role") -> set[tuple[str, str]]:
    """Set of job_key tuples for a list of job dicts (field names default to jobs.json)."""
    return {job_key(j.get(co), j.get(title)) for j in jobs}


def is_duplicate(co: str | None, title: str | None, keys: set[tuple[str, str]]) -> bool:
    """True if (co, title) already appears in `keys` (a set of job_key tuples).

    Company must match; the title matches exactly OR by containment (>=12 chars),
    which absorbs the trailing "- Remote" / "- Company - Location" noise that lead
    titles carry but stored roles don't.
    """
    c, t = norm_co(co), norm_title(title)
    for ec, et in keys:
        if ec != c or not t or not et:
            continue
        if t == et:
            return True
        short, lng = (t, et) if len(t) <= len(et) else (et, t)
        if len(short) >= 12 and short in lng:
            return True
    return False

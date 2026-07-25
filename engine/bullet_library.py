#!/usr/bin/env python3
"""bullet_library.py — the ledger of bullet phrasings that have been verified.

    python engine/bullet_library.py --check   <spec.json>   # what is unverified
    python engine/bullet_library.py --approve <spec.json>   # record as verified
    python engine/bullet_library.py --stats

WHY THIS EXISTS: two false claims reached finished documents by being COPIED
FORWARD. A phrase written once for one application was reused for the next, and
the next, so a single unverified sentence became four documents before anyone
read it against the source of truth. Both errors were invisible to every other
check: the documents parsed, scored well, and named things that were true of the
person somewhere.

WHY NOT A FIXED SET OF BULLETS: because tailoring is real. One employer's block
has ~29 distinct phrasings across the applications on record, and that variation
is legitimate — the same fact emphasized differently for different roles. A
library that forced one canonical string would be ignored within a week.

SO: this records phrasings that HAVE been checked, per employer. A phrasing that
is not in the ledger is not wrong — it is *unreviewed*, which is exactly the
state the copy-forward failures were in. Review it once against
`career-profile.md`, approve it, and it never asks again. New wording stays cheap;
unverified wording stops being invisible.

The ledger lives under `personal/` (gitignored) because the phrasings are career
content. It is a cache of human judgement, not a source of truth: the profile is
the source of truth, and deleting this file only costs a re-review.
"""

import argparse
import hashlib
import json
import os
import re
from datetime import date

import _paths  # noqa: F401  (side-effect: repo root on sys.path for `import config`)
import config
import resume_builder

LIBRARY = os.path.join(os.path.dirname(config.PROFILE_MD), "applications", "bullet-library.json")


def material_tokens(text: str) -> set[str]:
    """The parts of a bullet that can be TRUE OR FALSE, stripped of prose.

    Numbers, tools, and activity claims. Everything else is phrasing, and
    phrasing is where legitimate tailoring lives.
    """
    low = text.lower()
    toks: set[str] = set()
    # Figures: percentages, money, headcounts, scale. The claims that get checked.
    for m in re.finditer(r"\$?\d[\d,.]*\s?(?:%|k|m|million|billion|\+)?", low):
        t = m.group(0).strip()
        if any(ch.isdigit() for ch in t) and len(t) > 1:
            toks.add(re.sub(r"[.,]$", "", t))
    for tool in resume_builder.TRACKED_TOOLS:
        if tool in low:
            toks.add(f"tool:{tool}")
    for label, synonyms in resume_builder.TRACKED_CLAIMS.items():
        if any(s in low for s in synonyms):
            toks.add(f"claim:{label}")
    return toks


def fingerprint(lead: str, rest: str) -> str:
    """Kept for the ledger's record of which bullet introduced a token."""
    toks = material_tokens(f"{lead} {rest}")
    payload = "|".join(sorted(toks)) or "no-material-claims"
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def load(path: str = LIBRARY) -> dict:
    if not os.path.exists(path):
        return {"employers": {}}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save(data: dict, path: str = LIBRARY) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)


def spec_bullets(spec: dict) -> list[tuple[str, str, str]]:
    """(company, lead, rest) for every bullet, including stacked sub-roles."""
    out: list[tuple[str, str, str]] = []
    for entry in spec.get("experience", []) + spec.get("advisory", []):
        company = entry.get("company") or "?"
        for role in entry.get("roles") or [entry]:
            for bullet in role.get("bullets", []):
                out.append((company, bullet[0], bullet[1]))
    return out


def unverified(spec: dict, data: dict | None = None) -> list[dict]:
    """Bullets asserting a fact not yet verified for that employer.

    Verification is per-TOKEN, not per-bullet. Bullet-level was the second design
    and still flagged 12-14 lines per application, because tailoring does not only
    reword — it recombines, splitting and merging the same facts across different
    bullets. Every one of those flags was noise, and noise is how a gate dies.

    A token is a thing that can be true or false: a figure, a tool, an activity
    claim. Reword freely, recombine freely — silent. Introduce a fact this
    employer has never been verified to support and it surfaces, which is exactly
    what both real defects did.
    """
    data = load() if data is None else data
    known = data.get("employers", {})
    out: list[dict] = []
    for company, lead, rest in spec_bullets(spec):
        approved = set()
        for b in known.get(company, []):
            approved |= set(b.get("tokens", []))
        new = material_tokens(f"{lead} {rest}") - approved
        if new:
            out.append(
                {
                    "company": company,
                    "fp": fingerprint(lead, rest),
                    "lead": lead,
                    "rest": rest,
                    "new_tokens": sorted(new),
                }
            )
    return out


def approve(spec: dict, note: str = "", data: dict | None = None, path: str = LIBRARY) -> int:
    """Record every phrasing in a spec as reviewed. Returns the number added."""
    data = load(path) if data is None else data
    emp = data.setdefault("employers", {})
    added = 0
    for company, lead, rest in spec_bullets(spec):
        fp = fingerprint(lead, rest)
        bucket = emp.setdefault(company, [])
        if fp in {b["fp"] for b in bucket}:
            continue
        bucket.append(
            {
                "fp": fp,
                "lead": lead,
                "rest": rest,
                "tokens": sorted(material_tokens(f"{lead} {rest}")),
                "approved": date.today().isoformat(),
                "note": note,
            }
        )
        added += 1
    save(data, path)
    return added


def main() -> int:
    ap = argparse.ArgumentParser(description="Ledger of verified bullet phrasings.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", metavar="SPEC")
    g.add_argument("--approve", metavar="SPEC")
    g.add_argument("--stats", action="store_true")
    ap.add_argument("--note", default="", help="why these phrasings are correct")
    a = ap.parse_args()

    if a.stats:
        data = load()
        for co, bullets in sorted(data.get("employers", {}).items()):
            print(f"  {co[:40]:42} {len(bullets)} approved phrasing(s)")
        return 0

    path = a.check or a.approve
    with open(path, encoding="utf-8") as fh:
        spec = json.load(fh)

    if a.approve:
        n = approve(spec, note=a.note)
        print(f"  approved {n} new phrasing(s) from {os.path.basename(os.path.dirname(path))}")
        return 0

    rows = unverified(spec)
    if not rows:
        print("  Every bullet phrasing in this spec has been verified before.")
        return 0
    print(f"  {len(rows)} bullet phrasing(s) not yet verified — read each against")
    print("  career-profile.md, then re-run with --approve.\n")
    for r in rows:
        print(f"  [{r['company']}] {r['lead']}")
        print(f"      new: {', '.join(r['new_tokens'])}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

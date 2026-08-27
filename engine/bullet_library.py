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
    # Idioms that contain a number but assert no measurable claim. Narrow on
    # purpose: suppressing broadly would blunt the guard, and the whole design
    # rests on a new figure being worth one look.
    low = low.replace("fortune 500", "fortune-ranked").replace("fortune 100", "fortune-ranked")
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
            if b.get("revoked"):
                continue
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


def backlog(data: dict | None = None) -> list[dict]:
    """Everything already SHIPPED that the ledger has never checked.

    The ledger only ever grows when someone runs `--approve`, so phrasings written
    before it existed — or in a session where nobody ran it — are in documents that
    went out while being invisible here. This is the queue for closing that.

    IT IS MUCH SMALLER THAN IT LOOKS, and the reason matters. Counting distinct
    phrasings across the applications gives a number in the hundreds, which reads
    as an impossible backlog and invites either a blind bulk import (defeating the
    point) or giving up. But verification is per-TOKEN: most of those hundreds are
    rewordings of a fact already checked for that employer, and rewording is the
    legitimate half of tailoring. The queue is the far smaller set that introduces
    a claim this employer has never been verified to support.

    Ordered by how many documents use it, because a phrasing already in eight
    documents is the highest-leverage thing to check and the most expensive to
    have wrong.
    """
    import glob

    data = load() if data is None else data
    approved_fp = {b["fp"] for rows in (data.get("employers") or {}).values() for b in rows}
    approved_tok: dict[str, set] = {}
    for co, rows in (data.get("employers") or {}).items():
        approved_tok[co] = {t for b in rows if not b.get("revoked") for t in b.get("tokens", [])}

    seen: dict[tuple, dict] = {}
    root = os.path.join(os.path.dirname(LIBRARY), "*", "resume.json")
    for path in sorted(glob.glob(root)):
        try:
            with open(path, encoding="utf-8") as fh:
                spec = json.load(fh)
        except (OSError, ValueError):
            continue
        folder = os.path.basename(os.path.dirname(path))
        for co, lead, rest in spec_bullets(spec):
            key = (co, lead, rest)
            row = seen.setdefault(
                key,
                {
                    "company": co,
                    "lead": lead,
                    "rest": rest,
                    "fp": fingerprint(lead, rest),
                    "documents": [],
                },
            )
            row["documents"].append(folder)

    out = []
    for row in seen.values():
        if row["fp"] in approved_fp:
            continue
        new = sorted(
            material_tokens(f"{row['lead']}{row['rest']}") - approved_tok.get(row["company"], set())
        )
        if not new:
            continue  # a rewording of something already checked
        row["new_tokens"] = new
        row["warnings"] = _phrasing_warnings(row["company"], row["lead"], row["rest"])
        out.append(row)
    return sorted(out, key=lambda r: (-len(r["documents"]), r["company"]))


def accept(fps: set[str], note: str, data: dict | None = None, path: str = LIBRARY) -> int:
    """Approve NAMED phrasings out of the backlog, and only those.

    `--approve <spec>` takes a whole document at once, which is right when the
    document has just been reviewed end to end. It is wrong for the backlog: a
    spec that shipped months ago usually contains several fine phrasings and one
    that should never have gone out, and approving by document would sweep the bad
    one in under cover of the good ones. Reviewing by fingerprint keeps the unit of
    judgement the same as the unit of evidence.
    """
    data = load(path) if data is None else data
    emp = data.setdefault("employers", {})
    wanted = {r["fp"]: r for r in backlog(data) if r["fp"] in fps}
    added = 0
    for fp, row in wanted.items():
        bucket = emp.setdefault(row["company"], [])
        if fp in {b["fp"] for b in bucket}:
            continue
        bucket.append(
            {
                "fp": fp,
                "lead": row["lead"],
                "rest": row["rest"],
                "tokens": sorted(material_tokens(f"{row['lead']}{row['rest']}")),
                "approved": date.today().isoformat(),
                "note": note,
            }
        )
        added += 1
    save(data, path)
    return added


def _phrasing_warnings(company: str, lead: str, rest: str) -> list[str]:
    """Re-check one stored phrasing against the rules AS THEY STAND NOW."""
    import metric_registry

    spec = {
        "experience": [
            {
                "company": company,
                "title": "Role",
                "location_dates": "City, ST | May 2019 – Present",
                "bullets": [[lead, rest]],
            }
        ]
    }
    return metric_registry.warnings(spec)


# The registry marks an advisory finding "NOTE:" and everything else is a hard
# violation. Revoking on an advisory would be over-reach: "these two figures share
# a passage, check it reads right" is a prompt to look, not a verdict that the
# wording is wrong.
def _is_hard(warning: str) -> bool:
    return not warning.startswith("NOTE:")


def revalidate(data: dict | None = None) -> list[dict]:
    """Approved phrasings that TODAY'S rules reject.

    APPROVAL IS A SNAPSHOT, AND RULES MOVE. This ledger records that a human
    checked a phrasing on a date. It cannot record that the phrasing was checked
    against a rule written three weeks later — so a bullet approved in July stays
    "verified" forever, even after the claim inside it is corrected in August.

    That is not hypothetical. Four Hartford phrasings using a growth verb with the
    25-person figure sat approved here while the registry had forbidden exactly
    that pairing in prose the whole time, and `--suggest` offered one of them as a
    top-three pick for a live application. The ledger was working as designed; the
    design was missing this.
    """
    data = load() if data is None else data
    out: list[dict] = []
    for company, bullets in (data.get("employers") or {}).items():
        for b in bullets:
            if b.get("revoked"):
                continue
            warns = _phrasing_warnings(company, b.get("lead", ""), b.get("rest", ""))
            if warns:
                out.append(
                    {
                        "company": company,
                        "fp": b["fp"],
                        "text": f"{b.get('lead', '')}{b.get('rest', '')}",
                        "warnings": warns,
                        "hard": any(_is_hard(w) for w in warns),
                    }
                )
    return out


def revoke(fps: set[str], reason: str, data: dict | None = None, path: str = LIBRARY) -> int:
    """Mark phrasings as no longer usable, keeping the record of why.

    Marked, not deleted: the entry is the evidence that this wording was once
    approved, which is what makes the failure legible next time someone asks how
    a false claim reached four documents.
    """
    data = load(path) if data is None else data
    n = 0
    for bullets in (data.get("employers") or {}).values():
        for b in bullets:
            if b["fp"] in fps and not b.get("revoked"):
                b["revoked"] = {"on": date.today().isoformat(), "why": reason}
                n += 1
    save(data, path)
    return n


def suggest(jd_text: str, top: int = 5, data: dict | None = None) -> dict[str, list[dict]]:
    """Verified phrasings ranked against a posting, grouped by employer.

    THIS IS WHAT MAKES THE LEDGER A GENERATION SOURCE rather than an audit trail.
    Without it the library only ever answered "has this been checked?", so the
    fastest way to write a resume stayed "copy the last one" — which is precisely
    how a bullet propagates by never being noticed.

    It does NOT propose a canonical bullet, and it must not: the module docstring
    settles that, and it is right. One employer carries ~31 verified phrasings
    because the same fact deserves different emphasis for different postings.
    What this offers is the MENU — here are the ways you have already described
    this employer safely, best fit for this posting first — and the choosing stays
    a human job.
    """
    import resume_coverage

    data = load() if data is None else data
    jd_concepts = resume_coverage.concepts(resume_coverage.tokens(jd_text))
    out: dict[str, list[dict]] = {}
    for company, bullets in (data.get("employers") or {}).items():
        scored = []
        for b in bullets:
            if b.get("revoked"):
                continue
            text = f"{b.get('lead', '')}{b.get('rest', '')}"
            # Re-checked at SUGGESTION time, not trusted from the approval date.
            # A phrasing approved before a rule existed is not verified against it.
            if _phrasing_warnings(company, b.get("lead", ""), b.get("rest", "")):
                continue
            hits = resume_coverage.concepts(resume_coverage.tokens(text)) & jd_concepts
            scored.append({**b, "score": len(hits), "text": text})
        scored.sort(key=lambda x: -x["score"])
        out[company] = [s for s in scored if s["score"] > 0][:top]
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Ledger of verified bullet phrasings.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", metavar="SPEC")
    g.add_argument("--approve", metavar="SPEC")
    g.add_argument("--suggest", metavar="JD", help="rank verified phrasings against a posting")
    g.add_argument(
        "--revalidate",
        action="store_true",
        help="re-check every approved phrasing against the rules as they stand now",
    )
    g.add_argument(
        "--backlog",
        action="store_true",
        help="shipped phrasings the ledger has never checked, highest-leverage first",
    )
    g.add_argument(
        "--accept",
        metavar="FP[,FP...]",
        help="approve named backlog fingerprints, and only those (needs --note)",
    )
    g.add_argument("--stats", action="store_true")
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--fix", action="store_true", help="with --revalidate: revoke what fails")
    ap.add_argument("--note", default="", help="why these phrasings are correct")
    a = ap.parse_args()

    if a.stats:
        data = load()
        for co, bullets in sorted(data.get("employers", {}).items()):
            print(f"  {co[:40]:42} {len(bullets)} approved phrasing(s)")
        return 0

    if a.accept:
        if not a.note:
            print("  --accept needs --note: record WHY these were judged correct.")
            return 1
        fps = {x.strip() for x in a.accept.split(",") if x.strip()}
        n = accept(fps, note=a.note)
        print(f"  approved {n} phrasing(s) from the backlog")
        missed = fps - {b["fp"] for rows in load()["employers"].values() for b in rows}
        if missed:
            print(f"  ⚠ not found in the backlog: {', '.join(sorted(missed))}")
        return 0

    if a.backlog:
        rows = backlog()
        if not rows:
            print("  Nothing shipped is unchecked. The ledger covers every claim in every spec.")
            return 0
        print(f"  {len(rows)} shipped phrasing(s) introduce a claim this ledger has never")
        print("  checked for that employer. Ordered by how many documents use each —")
        print("  a phrasing already in eight documents is the most expensive to have wrong.\n")
        for r in rows[: a.top]:
            docs = len(r["documents"])
            print(f"  [{r['company'][:30]:32}] in {docs} document(s)")
            print(f"     {r['lead']}{r['rest'][:96]}")
            print(f"     new claim(s): {', '.join(r['new_tokens'])}")
            for w in r["warnings"]:
                print(f"     ⛔ {w[:100]}")
            print(f"     used by: {', '.join(sorted(set(r['documents']))[:4])}")
            print()
        if len(rows) > a.top:
            print(f"  ... {len(rows) - a.top} more. Raise --top to see them.")
        print("  Read each against career-profile.md, then --approve the spec it lives in.")
        return 0

    if a.revalidate:
        rows = revalidate()
        if not rows:
            print("  Every approved phrasing still passes the current rules.")
            return 0
        hard = [r for r in rows if r["hard"]]
        print(f"  {len(rows)} approved phrasing(s) fail the rules as they stand now")
        print(f"  — {len(hard)} hard violation(s), {len(rows) - len(hard)} advisory.")
        print("  Approval is a snapshot; rules move. These were checked against an")
        print("  earlier version of the truth and have been trusted ever since.\n")
        for r in rows:
            print(f"  [{r['company'][:34]}] {r['fp']}")
            print(f"     {r['text'][:104]}")
            for w in r["warnings"]:
                print(f"     ⛔ {w[:104]}")
            print()
        if a.fix:
            n = revoke(
                {r["fp"] for r in rows if r["hard"]},
                reason="failed --revalidate against current rules",
            )
            print(f"  revoked {n} hard violation(s) — kept on record, no longer offered")
            print("  Advisory findings are left alone: 'check this reads right' is a")
            print("  prompt to look, not a verdict that the wording is wrong.")
            return 0
        print("  Re-run with --fix to revoke them.")
        return 1

    if a.suggest:
        with open(a.suggest, encoding="utf-8") as fh:
            jd_text = fh.read()
        picks = suggest(jd_text, top=a.top)
        total = sum(len(v) for v in picks.values())
        if not total:
            print("  Nothing in the library scores against this posting.")
            print("  Either the library is thin for these employers, or the role is")
            print("  far enough from the record that new phrasings are the honest path.")
            return 0
        print(f"  {total} verified phrasing(s) ranked against this posting.")
        print("  These are ALREADY CHECKED against career-profile.md — reuse beats rewriting,")
        print("  and picking from here is what replaces copying the last resume.\n")
        for company, rows in picks.items():
            if not rows:
                continue
            print(f"  ── {company}")
            for r in rows:
                print(f"     [{r['score']:2}] {r['text'][:92]}")
            print()
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

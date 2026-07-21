#!/usr/bin/env python3
"""
lead_score.py — transparent first-pass triage scorer for swept leads.

WHAT IT IS (and honestly, what it is NOT):
  This gives every swept posting a fast, deterministic 0-10 TRIAGE score against
  a transparent rubric (lane / level / geo / domain), buckets it Keep/Watch/Drop,
  and dedupes against pipeline.md. It runs automatically after a sweep so the
  dashboard can show scored results instead of a raw list.

  It is NOT the authoritative fit score. The real 1-10 apply-pipeline score — the
  honest judgment of genuine fit, the tailoring plan, and promotion into the
  pipeline — still happens in chat, because that's a judgment call and a keyword
  script shouldn't fake it. Treat this as triage: it ranks what's worth my closer
  look, it doesn't replace it.

LANE-FIRST (2026-07-11 upgrade):
  The lane title patterns are broadened (data platforms / strategy / enablement /
  center of excellence / operations / analytics engineering), a data-science-LEAD
  penalty is added (you enable that lane, not lead it), and a clearly off-geo
  role is capped at Watch (remote or a commutable metro only). Domain (insurance/
  fintech) is only a +1 confidence bonus — NOT a gate — so in-lane roles in any
  industry still score as Keep.

USAGE:
  python lead_score.py [leads_raw.csv] [leads_scored.csv]
  # or import score_file(...) from server.py / jobspy_sweep.py / ats_sweep.py
"""

import csv
import os
import sys

import _paths  # noqa: F401  (side-effect: adds repo root to sys.path for `import config`)

ROOT = os.path.dirname(os.path.abspath(__file__))

# =============================================================================
# All personal settings live in ONE place: config.py. Nothing to edit here.
# =============================================================================
import career_ladder
import config as CFG
import jobkey  # the one canonical job-identity module (dedupe vs. pipeline.md)

LANE_STRONG = CFG.terms_to_regex(CFG.LANE_STRONG)
LANE_MED = CFG.terms_to_regex(CFG.LANE_MED)
LANE_ADJ = CFG.terms_to_regex(CFG.LANE_ADJ)
# Level terms can be listed by hand, or derived from a single TARGET_LEVEL via the
# career ladder. A hand-written list ALWAYS wins — someone who typed one meant it.
# The ladder exists because a bare word carries no level: "principal" and "lead" are
# below target in a director search and above it in an IC search, and this repo
# ships one config of each.
_TARGET_LEVEL = getattr(CFG, "TARGET_LEVEL", None)
_LEVEL_REACH = getattr(CFG, "LEVEL_REACH", None)  # rungs above target still worth seeing


def _level_terms():
    above = list(getattr(CFG, "LEVEL_AT_OR_ABOVE", None) or [])
    below = list(getattr(CFG, "LEVEL_BELOW", None) or [])
    if above or below or not _TARGET_LEVEL:
        return above, below
    return (
        career_ladder.terms_at_or_above(_TARGET_LEVEL, _LEVEL_REACH),
        career_ladder.terms_below(_TARGET_LEVEL),
    )


_LEVEL_ABOVE, _LEVEL_BELOW = _level_terms()
LEVEL_HI = CFG.terms_to_regex(_LEVEL_ABOVE)
LEVEL_MID = CFG.terms_to_regex(_LEVEL_BELOW)
_BELOW_REASON = (
    f"below your target level ({_TARGET_LEVEL})" if _TARGET_LEVEL else "below your target level"
)
# Geo terms come in three kinds and mixing them is what broke this before: a
# WORK MODEL ("remote", "hybrid") is not a PLACE. Leaving "hybrid" in GEO_OK meant
# "Hybrid-San Francisco Office" scored as commutable, and "remote" in GEO_GOOD meant
# "Remote - India" scored 2/2 "CT-local" — identical to Hartford. So the work-model
# words are stripped out of the place lists here rather than in userconfig, which
# repairs configs already in the wild without anyone editing a file.
_REMOTE_DEFAULT = ["remote", "anywhere", "nationwide", "work from home", "remote us", "us remote"]
_WORK_MODEL = {"hybrid", "onsite", "on site", "on-site", "in office", "in-office", "flexible"}
_remote_terms = [t.lower() for t in getattr(CFG, "GEO_REMOTE", _REMOTE_DEFAULT)]


def _places(terms):
    """Keep only real place names — drop work-model words that aren't locations."""
    drop = set(_remote_terms) | _WORK_MODEL
    return [t for t in terms if t.strip().lower() not in drop]


GEO_GOOD = CFG.terms_to_regex(_places(CFG.GEO_GOOD))
GEO_OK = CFG.terms_to_regex(_places(CFG.GEO_OK))
GEO_REMOTE = CFG.terms_to_regex(_remote_terms)
# Places you will not go. Checked against remote too: "remote" is only as good as
# the country qualifying it. Empty by default, so existing configs are unaffected.
GEO_EXCLUDE = CFG.terms_to_regex(getattr(CFG, "GEO_EXCLUDE", []))
DOMAIN = CFG.terms_to_regex(CFG.DOMAIN_BONUS)
HARD_GATE = CFG.terms_to_regex(CFG.HARD_GATES)
NOISE = CFG.terms_to_regex(CFG.NOISE)
OFF_CONTEXT = CFG.terms_to_regex(CFG.OFF_CONTEXT)
PENALTY_LANES = {label: CFG.terms_to_regex(terms) for label, terms in CFG.PENALTY_LANES.items()}
# Penalty lanes survive the OFF_CONTEXT drop (e.g. "sales enablement" contains
# "sales" — you're open to that pivot, so it must not be auto-dropped).
OFF_CONTEXT_EXEMPT = list(PENALTY_LANES.values())


def score_row(title, location):
    """Triage a posting from its TITLE and LOCATION only.

    NOTE: this never sees the JD body, so HARD_GATES can only catch what's in the
    title. A disqualifying requirement buried in the description will sail through.
    The honest gate is the apply-pipeline score in chat, which reads the whole JD.
    """
    t = title or ""
    reasons = []
    if NOISE.search(t):
        return 0, "Drop", "off-lane (noise match)"
    if HARD_GATE.search(t):
        return 0, "Drop", "hard gate: an essential requirement you can't honestly bridge"

    exempt = any(rx.search(t) for rx in OFF_CONTEXT_EXEMPT)
    if OFF_CONTEXT.search(t) and not exempt:
        return 0, "Drop", "your keyword appearing in a non-data function"

    # Lane (0-4)
    if LANE_STRONG.search(t):
        lane = 4
        reasons.append("strong lane (governance/enablement/platform)")
    elif LANE_MED.search(t):
        lane = 3
        reasons.append("data/analytics lane")
    elif LANE_ADJ.search(t):
        lane = 2
        reasons.append("adjacent lane")
    else:
        return 0, "Drop", "no data lane"

    # Penalties ALWAYS fire, even when a strong-lane word is present. A
    # "Director, Product Management - Data Platform" is still a PM-track role.
    for label, rx in PENALTY_LANES.items():
        if rx.search(t):
            lane = max(1, lane - 1)
            reasons.append(f"{label} (-1)")

    # Level (0-3)
    if LEVEL_HI.search(t):
        lvl = 3
    elif LEVEL_MID.search(t):
        lvl = 1
        reasons.append(_BELOW_REASON)
    else:
        lvl = 0
        reasons.append("no leadership level in title")

    # Geo (0-2). Exclusions are tested against the same string as everything else,
    # because "remote" is only ever as good as the country qualifying it.
    loc = location or ""
    has_good, has_ok = GEO_GOOD.search(loc), GEO_OK.search(loc)
    is_remote, excluded = GEO_REMOTE.search(loc), GEO_EXCLUDE.search(loc)
    if has_good and not excluded:
        geo = 2
        reasons.append("in your home range")
    elif is_remote and not excluded:
        geo = 2
        reasons.append("remote")
    elif has_ok and not excluded:
        geo = 1
        reasons.append("commutable-ish")
    elif has_good or has_ok:
        # An out-of-range place AND an in-range one — a multi-location posting.
        # Worth a look, but it can't be a 2: the in-range office may not be hiring.
        geo = 1
        reasons.append("multi-location: in-range option listed, verify")
    else:
        geo = 0
        reasons.append("off-geo")

    # Domain (0-1) — bonus only, never a gate.
    dom = 1 if DOMAIN.search(t) or DOMAIN.search(loc) else 0
    if dom:
        reasons.append("insurance/fintech domain")

    score = lane + lvl + geo + dom  # 0-10
    bucket = "Keep" if score >= 7 else ("Watch" if score >= 4 else "Drop")
    # You need remote or CT-commutable. A clearly off-geo role can't be a Keep.
    if geo == 0 and bucket == "Keep":
        bucket = "Watch"
        reasons.append("off-geo caps at Watch (not remote/CT)")
    return score, bucket, "; ".join(reasons)


def load_pipeline_keys(path):
    """job_key tuples for every posting already tracked in pipeline.md, for dedupe."""
    keys: set[tuple[str, str]] = set()
    if not os.path.exists(path):
        return keys
    with open(path, encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) >= 3 and cells[0].isdigit():
                role, co = cells[1], cells[2]  # | ID | Role | Company | ...
                keys.add(jobkey.job_key(co, role))
    return keys


def score_file(in_csv=None, out_csv=None, pipeline_md=None):
    in_csv = in_csv or CFG.LEADS_RAW
    out_csv = out_csv or CFG.LEADS_SCORED
    pipeline_md = pipeline_md or CFG.PIPELINE_MD
    seen = load_pipeline_keys(pipeline_md)

    rows = []
    if os.path.exists(in_csv):
        with open(in_csv, encoding="utf-8", errors="ignore") as fh:
            rows = list(csv.DictReader(fh))

    scored = []
    for r in rows:
        title = (r.get("title") or "").strip()
        company = (r.get("company") or "").strip()
        location = (r.get("location") or "").strip()
        s, bucket, why = score_row(title, location)
        if s == 0:
            continue  # drop noise / no-lane entirely
        tracked = jobkey.is_duplicate(company, title, seen)
        scored.append(
            {
                "score": s,
                "bucket": ("Tracked" if tracked else bucket),
                "title": title,
                "company": company,
                "location": location,
                "date_posted": (r.get("date_posted") or "")[:10],
                "why": why + ("; already in pipeline" if tracked else ""),
                "job_url": (r.get("job_url") or "").strip(),
                # Carried, not computed: ats_sweep is the only stage that sees a JD
                # body, so these ride through rather than being re-derived here.
                "work_auth": (r.get("work_auth") or "unstated").strip(),
                "work_auth_concern": (r.get("work_auth_concern") or "").strip(),
                "work_auth_evidence": (r.get("work_auth_evidence") or "").strip(),
            }
        )

    scored.sort(key=lambda x: (-x["score"], x["company"]))
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=[
                "score",
                "bucket",
                "title",
                "company",
                "location",
                "date_posted",
                "why",
                "job_url",
                "work_auth",
                "work_auth_concern",
                "work_auth_evidence",
            ],
        )
        w.writeheader()
        w.writerows(scored)
    return scored


def main():
    in_csv = sys.argv[1] if len(sys.argv) > 1 else None
    out_csv = sys.argv[2] if len(sys.argv) > 2 else None
    scored = score_file(in_csv, out_csv)
    keep = [x for x in scored if x["bucket"] == "Keep"]
    watch = [x for x in scored if x["bucket"] == "Watch"]
    print(
        f"scored {len(scored)} in-lane leads -> "
        f"{len(keep)} Keep, {len(watch)} Watch  (triage only; real score in chat)"
    )
    for x in scored[:15]:
        print(f"  {x['score']:>2} {x['bucket']:<8} {x['title'][:48]:48} | {x['company'][:22]}")


if __name__ == "__main__":
    raise SystemExit(main())

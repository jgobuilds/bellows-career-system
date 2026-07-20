#!/usr/bin/env python3
"""
ats_sweep.py - lane-first / title-first ATS-direct engine (runs on YOUR machine)
================================================================================
The reliable half of the upgraded apply-pipeline sweep. Instead of trusting a noisy
aggregator, this polls company ATS feeds DIRECTLY (Greenhouse, Lever, Ashby,
SmartRecruiters, Workday), pulls exactly what's open with a REAL posting date,
then keeps only titles in your lane - at ANY company/industry.

WHY THIS EXISTS (the 2026-07-11 lane-first upgrade):
  The old sweep was company-first and JobSpy/Indeed was ~7% in-lane noise. Every
  strong role you found by hand (AssetWatch, Momentive, Yahoo, ...) was IN his
  lane but at a company the old net never polled. This engine flips it: it scans a
  BROAD, cross-industry company list and filters by TITLE, so an in-lane
  "Director/Head/VP of Data ..." surfaces no matter the industry. Industry is a
  confidence tiebreaker, never a gate.

WHY LOCAL, NOT COWORK:
  The Cowork sandbox shell has no outbound network (all hosts allowlist-blocked)
  and the browser is org-policy restricted. These ATS feeds are public, keyless
  JSON and work fine from your own machine. Stdlib only - no pip install needed.

RUN:
  python ats_sweep.py                    # scan all companies, <=60 days old
  python ats_sweep.py --max-age-days 30  # tighter recency
  python ats_sweep.py --remote-only      # drop clearly-onsite roles
  python ats_sweep.py --only greenhouse  # one ATS type (greenhouse|lever|ashby|smartrecruiters|workday)

OUTPUT:
  leads_ats.csv - company,title,location,date_posted,site,job_url,search,industry
  It's the same schema jobspy_sweep.py writes, so it flows straight into
  lead_score.py and the dashboard. jobspy_sweep.py runs this automatically.

EXTEND IT:
  Add companies to COMPANIES below (that's the whole point - the list compounds).
  Resolve a company's ATS with the recipe in apply-pipeline/references/target-companies.md,
  then drop a row here. Unverified slugs simply 404 and are skipped, so it's safe
  to add speculative entries.

BOUNDARY: discovery only. Never applies. (No auto-submit - the whole system's point.)
"""

import argparse
import csv
import html as _htmllib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

import _paths  # noqa: F401  (side-effect: adds repo root to sys.path for `import config`)

ROOT = os.path.dirname(os.path.abspath(__file__))
UA = "Mozilla/5.0 (apply-pipeline ats_sweep; personal job search; low volume)"
TIMEOUT = 20
PER_CALL_PAUSE = 0.6  # be polite to public feeds

# ---------------------------------------------------------------------------
# Company list - the compounding precision cache. Broad and cross-industry ON
# PURPOSE (that's the lane-first upgrade). Seeded from
# apply-pipeline/references/target-companies.md + your own hand-found companies.
# Fields:
#   greenhouse:      {"ats":"greenhouse", "slug": "...", "industry": "..."}
#   lever:           {"ats":"lever", "slug": "...", ...}
#   ashby:           {"ats":"ashby", "slug": "...", ...}
#   smartrecruiters: {"ats":"smartrecruiters", "slug": "...", ...}
#   workday:         {"ats":"workday","tenant":"..","wd":"wd5","site":"..","industry":".."}
# 'status' is informational: "validated" (feed confirmed) vs "verify" (guess -
# will 404 harmlessly if wrong; confirm and mark validated when it returns data).
# ---------------------------------------------------------------------------
import config as CFG

# All personal settings live in config.py — nothing to edit here.
COMPANIES = CFG.COMPANIES


# searchText values for Workday (server-side filter; keeps payloads small)
WORKDAY_QUERIES = CFG.WORKDAY_QUERIES


# ---------------------------------------------------------------------------
# Delta state — remember the last run + which companies were swept. A normal
# sweep then only keeps postings NEWER than last time; any company added to
# config since the last run gets its FULL history window (never swept before).
# ---------------------------------------------------------------------------
STATE_FILE = os.path.join(CFG.DATA_DIR, "sweep_state.json")
LAST_SWEEP_META: dict[str, object] = {}  # populated by sweep(): {days_since, new_companies, delta}


def _company_key(c):
    return f"{c['ats']}:{c.get('slug') or c.get('tenant')}"


def _load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):  # missing (first run) or corrupt state file
        return {"last_run": None, "companies": []}


def _save_state(keys):
    try:
        os.makedirs(CFG.DATA_DIR, exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "last_run": datetime.now(timezone.utc).isoformat(),
                    "companies": sorted(set(keys)),
                },
                fh,
                indent=1,
            )
    except OSError as e:  # non-fatal: next sweep just re-pulls the full window
        print(f"  ! couldn't save sweep state ({e}) — next run won't use delta", file=sys.stderr)


def _days_since(iso):
    if not iso:
        return None
    try:
        dt = datetime.fromisoformat(str(iso))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt).days
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# HTTP helpers (stdlib)
# ---------------------------------------------------------------------------
def _get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def _post_json(url, body):
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "User-Agent": UA,
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


# ---------------------------------------------------------------------------
# JD text: strip HTML to plain text (feeds return the full description in JSON)
# ---------------------------------------------------------------------------
def _html_to_text(s, cap=6000):
    if not s:
        return ""
    s = _htmllib.unescape(str(s))
    s = re.sub(r"(?is)<(script|style).*?</\1>", " ", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:cap]


def _enrich_desc(r, c):
    """Fetch a JD body for feeds that don't include it in the list call (Workday,
    SmartRecruiters). Called only for in-lane keepers, so it's a few requests."""
    try:
        if r.get("site") == "workday" and r.get("_path"):
            base = f"https://{c['tenant']}.{c['wd']}.myworkdayjobs.com"
            j = _get_json(f"{base}/wday/cxs/{c['tenant']}/{c['site']}{r['_path']}")
            return _html_to_text((j.get("jobPostingInfo") or {}).get("jobDescription"))
        if r.get("site") == "smartrecruiters" and r.get("_srid"):
            j = _get_json(
                f"https://api.smartrecruiters.com/v1/companies/{c['slug']}/postings/{r['_srid']}"
            )
            secs = (j.get("jobAd") or {}).get("sections") or {}
            parts = [
                (secs.get(k) or {}).get("text", "")
                for k in ("jobDescription", "qualifications", "additionalInformation")
            ]
            return _html_to_text(" ".join(p for p in parts if p))
    except Exception:
        return ""
    return ""


# ---------------------------------------------------------------------------
# Freshness helpers - normalize everything to "days old" (or None if unknown)
# ---------------------------------------------------------------------------
def _iso_age_days(iso):
    if not iso:
        return None
    s = str(iso).strip().replace("Z", "+00:00")
    for fmt in (None,):  # try fromisoformat first
        try:
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return (datetime.now(timezone.utc) - dt).days
        except Exception:  # noqa: S110
            pass
    # epoch millis (Lever createdAt)
    try:
        ms = int(iso)
        dt = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
        return (datetime.now(timezone.utc) - dt).days
    except Exception:
        return None


def _workday_age_days(posted_on):
    """Parse Workday's relative 'Posted X Days Ago' string into an approx age."""
    if not posted_on:
        return None
    s = posted_on.lower()
    if "today" in s:
        return 0
    if "yesterday" in s:
        return 1
    m = re.search(r"(\d+)\s*\+?\s*day", s)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+)\s*\+?\s*month", s)
    if m:
        return int(m.group(1)) * 30
    return None


def _date_str_from_age(iso_or_none):
    if not iso_or_none:
        return ""
    return str(iso_or_none)[:10]


# ---------------------------------------------------------------------------
# Per-ATS fetchers -> yield normalized dict rows
#   {company,title,location,date_posted,site,job_url,search(industry),age_days,is_remote}
# ---------------------------------------------------------------------------
def fetch_greenhouse(c):
    url = f"https://boards-api.greenhouse.io/v1/boards/{c['slug']}/jobs?content=true"
    j = _get_json(url)
    rows = []
    for job in j.get("jobs", []):
        loc = ((job.get("location") or {}).get("name") or "").strip()
        date = job.get("first_published") or job.get("updated_at")
        rows.append(
            {
                "company": job.get("company_name") or c["slug"],
                "title": (job.get("title") or "").strip(),
                "location": loc,
                "date_posted": _date_str_from_age(date),
                "site": "greenhouse",
                "job_url": job.get("absolute_url") or "",
                "industry": c.get("industry", ""),
                "age_days": _iso_age_days(date),
                "is_remote": "remote" in loc.lower(),
                "description": _html_to_text(job.get("content")),
            }
        )
    return rows


def fetch_lever(c):
    url = f"https://api.lever.co/v0/postings/{c['slug']}?mode=json"
    j = _get_json(url)
    rows = []
    for job in j:
        cats = job.get("categories") or {}
        loc = (cats.get("location") or "").strip()
        created = job.get("createdAt")
        rows.append(
            {
                "company": c["slug"],
                "title": (job.get("text") or "").strip(),
                "location": loc,
                "date_posted": _date_str_from_age(
                    datetime.fromtimestamp(int(created) / 1000, tz=timezone.utc).isoformat()
                    if created
                    else ""
                ),
                "site": "lever",
                "job_url": job.get("hostedUrl") or "",
                "industry": c.get("industry", ""),
                "age_days": _iso_age_days(created),
                "is_remote": "remote" in (loc + " " + (job.get("workplaceType") or "")).lower(),
                "description": _html_to_text(job.get("descriptionPlain") or job.get("description")),
            }
        )
    return rows


def fetch_ashby(c):
    url = f"https://api.ashbyhq.com/posting-api/job-board/{c['slug']}?includeCompensation=true"
    j = _get_json(url)
    rows = []
    for job in j.get("jobs", []):
        loc = (job.get("location") or "").strip()
        date = job.get("publishedDate") or job.get("updatedAt") or job.get("publishedAt")
        rows.append(
            {
                "company": c["slug"],
                "title": (job.get("title") or "").strip(),
                "location": loc,
                "date_posted": _date_str_from_age(date),
                "site": "ashby",
                "job_url": job.get("jobUrl") or job.get("applyUrl") or "",
                "industry": c.get("industry", ""),
                "age_days": _iso_age_days(date),
                "is_remote": bool(job.get("isRemote")) or "remote" in loc.lower(),
                "description": _html_to_text(
                    job.get("descriptionPlain")
                    or job.get("descriptionHtml")
                    or job.get("description")
                ),
            }
        )
    return rows


def fetch_smartrecruiters(c):
    url = f"https://api.smartrecruiters.com/v1/companies/{c['slug']}/postings?limit=100"
    j = _get_json(url)
    rows = []
    for job in j.get("content", []):
        loc_obj = job.get("location") or {}
        loc = ", ".join(
            x for x in [loc_obj.get("city"), loc_obj.get("region"), loc_obj.get("country")] if x
        )
        if loc_obj.get("remote"):
            loc = ("Remote " + loc).strip()
        date = job.get("releasedDate")
        rows.append(
            {
                "company": job.get("company", {}).get("name") or c["slug"],
                "title": (job.get("name") or "").strip(),
                "location": loc,
                "date_posted": _date_str_from_age(date),
                "site": "smartrecruiters",
                "job_url": f"https://jobs.smartrecruiters.com/{c['slug']}/{job.get('id')}",
                "industry": c.get("industry", ""),
                "age_days": _iso_age_days(date),
                "is_remote": bool(loc_obj.get("remote")) or "remote" in loc.lower(),
                "description": "",
                "_srid": job.get("id"),
            }
        )
    return rows


def fetch_workday(c):
    base = f"https://{c['tenant']}.{c['wd']}.myworkdayjobs.com"
    list_url = f"{base}/wday/cxs/{c['tenant']}/{c['site']}/jobs"
    seen, rows = set(), []
    for q in WORKDAY_QUERIES:
        try:
            j = _post_json(
                list_url, {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": q}
            )
        except Exception:  # noqa: S112
            continue
        for job in j.get("jobPostings", []):
            path = job.get("externalPath") or ""
            if path in seen:
                continue
            seen.add(path)
            posted = job.get("postedOn") or ""
            rows.append(
                {
                    "company": c["tenant"],
                    "title": (job.get("title") or "").strip(),
                    "location": (job.get("locationsText") or "").strip(),
                    "date_posted": "",  # Workday list gives relative text only
                    "site": "workday",
                    "job_url": f"{base}/en-US/{c['site']}{path}",
                    "industry": c.get("industry", ""),
                    "age_days": _workday_age_days(posted),
                    "is_remote": "remote" in (job.get("locationsText") or "").lower(),
                    "description": "",
                    "_path": path,
                }
            )
        time.sleep(PER_CALL_PAUSE)
    return rows


FETCHERS = {
    "greenhouse": fetch_greenhouse,
    "lever": fetch_lever,
    "ashby": fetch_ashby,
    "smartrecruiters": fetch_smartrecruiters,
    "workday": fetch_workday,
}


# ---------------------------------------------------------------------------
# The sweep
# ---------------------------------------------------------------------------
def _label(c):
    return c.get("slug") or c.get("tenant") or "?"


def sweep(
    max_age_days=CFG.MAX_AGE_DAYS,
    remote_only=False,
    only=None,
    verbose=True,
    delta=True,
    full=False,
):
    """Poll every company, keep only in-lane titles (via lead_score), return rows.

    delta=True (default): existing companies only surface postings newer than the
    last run; companies added to config since then get the full max_age window.
    full=True: ignore delta, pull the full max_age window for everyone.
    """
    try:
        import lead_score

        def lane_ok(title, loc):
            return lead_score.score_row(title, loc)[0] > 0
    except Exception:
        # Fallback if lead_score can't import. STILL CONFIG-DRIVEN - there are no
        # hardcoded keywords anywhere in this system. Coarser than the real scorer
        # (no geo, domain, or penalty logic), but it uses YOUR lane, level, noise,
        # and hard gates straight from config.py.
        _lane = CFG.terms_to_regex(CFG.LANE_STRONG + CFG.LANE_MED + CFG.LANE_ADJ)
        _lvl = CFG.terms_to_regex(CFG.LEVEL_AT_OR_ABOVE + CFG.LEVEL_BELOW)
        _block = CFG.terms_to_regex(CFG.NOISE + CFG.HARD_GATES)

        def lane_ok(t, loc):
            return bool(_lane.search(t) and _lvl.search(t) and not _block.search(t))

    kept, checked, errors = [], 0, 0
    _state = _load_state()
    _last = set(_state.get("companies") or [])
    _since = _days_since(_state.get("last_run"))
    _cur_keys, _new_n = [], 0
    for c in COMPANIES:
        if only and c["ats"] != only:
            continue
        fetcher = FETCHERS.get(c["ats"])
        if not fetcher:
            continue
        checked += 1
        _key = _company_key(c)
        _cur_keys.append(_key)
        _is_new = _key not in _last
        if _is_new:
            _new_n += 1
        # full window for brand-new companies (or --full / no prior run); else delta
        eff_age = (
            max_age_days
            if (full or _is_new or _since is None or not delta)
            else min(max_age_days, max(1, _since + 1))
        )
        try:
            rows = fetcher(c)
        except urllib.error.HTTPError as e:
            if verbose:
                print(f"  - {c['ats']}:{_label(c)} HTTP {e.code} (skip)", file=sys.stderr)
            errors += 1
            time.sleep(PER_CALL_PAUSE)
            continue
        except Exception as e:
            if verbose:
                print(f"  - {c['ats']}:{_label(c)} error: {e} (skip)", file=sys.stderr)
            errors += 1
            time.sleep(PER_CALL_PAUSE)
            continue

        hits = 0
        for r in rows:
            if not r["title"]:
                continue
            if not lane_ok(r["title"], r["location"]):
                continue
            if remote_only and not r["is_remote"]:
                continue
            age = r.get("age_days")
            if eff_age is not None and age is not None and age > eff_age:
                continue
            if not r.get("description"):
                r["description"] = _enrich_desc(r, c)
            r["search"] = r.pop("industry", "")  # reuse 'search' col to carry industry
            kept.append(r)
            hits += 1
        if verbose:
            tag = "" if c.get("status") == "validated" else " [verify]"
            print(
                f"  - {c['ats']}:{_label(c)}{tag}: {len(rows)} open, {hits} in-lane",
                file=sys.stderr,
            )
        time.sleep(PER_CALL_PAUSE)

    _save_state(_cur_keys)
    LAST_SWEEP_META.clear()
    LAST_SWEEP_META.update(
        {"days_since": _since, "new_companies": _new_n, "delta": (delta and not full)}
    )

    # Dedupe on company|title
    uniq, out = set(), []
    for r in sorted(
        kept, key=lambda x: x.get("age_days") if x.get("age_days") is not None else 9999
    ):
        k = r["company"].strip().lower() + "|" + r["title"].strip().lower()
        if k in uniq:
            continue
        uniq.add(k)
        out.append(r)

    if verbose:
        print(
            f"\nATS sweep: {checked} companies polled, {errors} unreachable, "
            f"{len(out)} unique in-lane roles.",
            file=sys.stderr,
        )
    return out


CSV_COLS = [
    "company",
    "title",
    "location",
    "date_posted",
    "site",
    "job_url",
    "search",
    "description",
]


def write_csv(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_COLS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in CSV_COLS})


def main():
    ap = argparse.ArgumentParser(description="lane-first ATS-direct discovery sweep")
    ap.add_argument(
        "--max-age-days",
        type=int,
        default=CFG.MAX_AGE_DAYS,
        help="drop roles older than this when a real date exists (default 60)",
    )
    ap.add_argument(
        "--remote-only", action="store_true", help="keep only roles the ATS marks remote"
    )
    ap.add_argument(
        "--only", default=None, choices=list(FETCHERS.keys()), help="restrict to one ATS type"
    )
    ap.add_argument("--out", default=CFG.LEADS_ATS)
    ap.add_argument(
        "--full",
        action="store_true",
        help="ignore delta; pull the full --max-age-days window for every company",
    )
    args = ap.parse_args()

    rows = sweep(
        max_age_days=args.max_age_days, remote_only=args.remote_only, only=args.only, full=args.full
    )
    write_csv(rows, args.out)
    print(
        f"{len(rows)} in-lane ATS roles -> {args.out}  (swept {datetime.now():%Y-%m-%d %H:%M})",
        file=sys.stderr,
    )

    # Triage-score just like the JobSpy path, so the two nets share one scorer.
    try:
        import lead_score

        scored = lead_score.score_file(
            args.out, os.path.join(CFG.DATA_DIR, "leads_scored_ats.csv"), CFG.PIPELINE_MD
        )
        keep = sum(1 for x in scored if x["bucket"] == "Keep")
        watch = sum(1 for x in scored if x["bucket"] == "Watch")
        print(
            f"triage: {len(scored)} in-lane -> {keep} Keep, {watch} Watch -> leads_scored_ats.csv",
            file=sys.stderr,
        )
        for x in scored[:12]:
            print(
                f"  {x['score']:>2} {x['bucket']:<8} {x['title'][:46]:46} | {x['company'][:22]}",
                file=sys.stderr,
            )
    except Exception as e:
        print(f"(triage scoring skipped: {e})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

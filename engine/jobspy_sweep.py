#!/usr/bin/env python3
"""
jobspy_sweep.py — apply-pipeline's discovery sweep (runs on YOUR machine)
==============================================================================
Two legs in one command:
  1. LANE-FIRST ATS-DIRECT (ats_sweep.py) — polls company ATS feeds directly
     (Greenhouse/Lever/Ashby/SmartRecruiters/Workday) across a broad, cross-
     industry company list and keeps only in-lane titles, with REAL posting
     dates. This is the reliable core (the 2026-07-11 lane-first upgrade).
  2. JOBSPY BOARD RECALL — wraps the MIT-licensed `python-jobspy` to sweep
     Indeed + Google for the same title patterns across all companies. Optional;
     if python-jobspy isn't installed, the sweep still runs ATS-direct only.

WHY THIS RUNS LOCALLY, NOT IN COWORK:
  The Cowork sandbox blocks outbound network (all hosts allowlist-blocked) and
  the browser is org-restricted. On your own machine the ATS feeds and boards
  are reachable. ATS-direct is stdlib-only; JobSpy needs one pip install.

SETUP (one time, for the board leg):
  pip install -U python-jobspy

RUN:
  python jobspy_sweep.py                 # ATS-direct + Indeed/Google, past 7 days
  python jobspy_sweep.py --no-boards     # ATS-direct only (no python-jobspy needed)
  python jobspy_sweep.py --no-ats        # boards only (old behavior)
  python jobspy_sweep.py --hours 48      # tighter board recency window
  python jobspy_sweep.py --max-age-days 30   # tighter ATS-direct recency
  python jobspy_sweep.py --glassdoor     # add Glassdoor (city locations only)
  python jobspy_sweep.py --zip           # add ZipRecruiter (often needs --proxy)
  python jobspy_sweep.py --linkedin --proxy http://user:pass@host:port

BOARD NOTES (why the board defaults are Indeed + Google):
  Indeed + Google are the reliable, no-proxy, no-key boards. The others are
  opt-in because they routinely error without help:
    * Glassdoor  -> HTTP 400 "location not parsed" on "Remote"; give it a CITY.
    * ZipRecruiter -> HTTP 403 "forbidden aa" (anti-bot); needs a --proxy.
    * LinkedIn   -> JobSpy's most aggressive blocker; needs a --proxy.
  Per-board failures are non-fatal: a board that errors is skipped and the sweep
  continues, so you still get a CSV from whatever worked.

OUTPUT:
  leads_raw.csv  — company, title, location, date_posted, site, job_url, search
  Hand it back to apply-pipeline: it dedupes against pipeline.md, filters to your
  lane/level from career-profile.md, and VALIDATES each hit against the company's
  own ATS before it becomes a real lead. Board hits are POINTERS, not proof;
  ATS-direct hits are already source-validated.

BOUNDARY: this only DISCOVERS. It never applies. Applying stays human-in-the-loop
through apply-pipeline. (No auto-submit — that's the whole point of the system.)
"""

import argparse
import csv
import sys
import time
from datetime import datetime

import _paths  # noqa: F401  (side-effect: adds repo root to sys.path for `import config`)

# --- your search profile (edit these to retune the sweep) --------------------
# Lane-focused: data leadership (governance / enablement / platform / analytics),
# Director / AVP / VP / Head. Not DS/ML-science, not IT-ops.
import config as CFG
import jobkey  # canonical job identity for the cross-search merge

# All personal settings live in config.py — nothing to edit here.
SEARCH_TERMS = CFG.TARGET_TITLES
LOCATIONS = CFG.LOCATIONS

DEFAULT_HOURS_OLD = CFG.BOARD_HOURS_OLD
RESULTS_PER_SEARCH = CFG.RESULTS_PER_SEARCH
COUNTRY_INDEED = "USA"
PER_CALL_PAUSE = 2  # seconds between calls — eases Indeed rate-limiting

# Reliable, no-proxy defaults. Flaky boards are added via flags below.
DEFAULT_SITES = ["indeed", "google"]


def google_query(term: str, location: str, is_remote: bool) -> str:
    where = "remote" if is_remote else location
    return f"{term} {where} jobs posted this week"


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


def run_jobspy(args: argparse.Namespace) -> "list[dict]":
    """Optional board-recall leg. Returns a list of row dicts (empty if unavailable)."""
    try:
        import pandas as pd
        from jobspy import scrape_jobs
    except ImportError:
        print(
            "(python-jobspy not installed — running ATS-direct only. "
            "`pip install -U python-jobspy` to add cross-board recall.)",
            file=sys.stderr,
        )
        return []

    sites = list(DEFAULT_SITES)
    if args.glassdoor:
        sites.append("glassdoor")
    if args.zip:
        sites.append("zip_recruiter")
    if args.linkedin:
        sites.append("linkedin")
    proxies = [args.proxy] if args.proxy else None

    frames = []
    for term in SEARCH_TERMS:
        for loc, is_remote in LOCATIONS:
            call_sites = sites
            if is_remote and "glassdoor" in sites:
                call_sites = [s for s in sites if s != "glassdoor"]
            label = "remote" if is_remote else loc
            print(f"  board sweep: {term!r} @ {label!r} ...", file=sys.stderr)
            try:
                df = scrape_jobs(
                    site_name=call_sites,
                    search_term=term,
                    google_search_term=google_query(term, loc, is_remote),
                    location=loc,
                    is_remote=is_remote,
                    results_wanted=args.results,
                    hours_old=args.hours,
                    country_indeed=COUNTRY_INDEED,
                    linkedin_fetch_description=False,
                    proxies=proxies,
                )
            except Exception as e:
                print(f"    ! {term} @ {label} failed: {e}", file=sys.stderr)
                continue
            if df is not None and len(df):
                df["search"] = term
                frames.append(df)
            time.sleep(PER_CALL_PAUSE)

    if not frames:
        return []
    import pandas as pd

    alljobs = pd.concat(frames, ignore_index=True)
    cols = [c for c in CSV_COLS if c in alljobs.columns]
    return alljobs[cols].to_dict("records")


def main() -> int:
    ap = argparse.ArgumentParser(description="apply-pipeline discovery sweep (ATS-direct + boards)")
    ap.add_argument(
        "--hours",
        type=int,
        default=DEFAULT_HOURS_OLD,
        help="JobSpy: max posting age in hours (default 168 = 1 week)",
    )
    ap.add_argument(
        "--results",
        type=int,
        default=RESULTS_PER_SEARCH,
        help="JobSpy: results wanted per search/board (default 25)",
    )
    ap.add_argument(
        "--max-age-days",
        type=int,
        default=CFG.MAX_AGE_DAYS,
        help="ATS-direct: drop roles older than this when a real date exists (default 60)",
    )
    ap.add_argument("--no-ats", action="store_true", help="skip the ATS-direct leg (boards only)")
    ap.add_argument(
        "--no-boards", action="store_true", help="skip the JobSpy board leg (ATS-direct only)"
    )
    ap.add_argument(
        "--full",
        action="store_true",
        help="ignore delta; pull the full history window (ATS-direct + boards)",
    )
    ap.add_argument(
        "--glassdoor",
        action="store_true",
        help="add Glassdoor (city locations only; skips remote calls)",
    )
    ap.add_argument("--zip", action="store_true", help="add ZipRecruiter (usually needs --proxy)")
    ap.add_argument(
        "--linkedin", action="store_true", help="add LinkedIn (needs --proxy in practice)"
    )
    ap.add_argument("--proxy", default=None, help="proxy URL, e.g. http://user:pass@host:port")
    ap.add_argument(
        "--out", default=CFG.LEADS_RAW, help="output CSV path (default: <repo>/data/leads_raw.csv)"
    )
    args = ap.parse_args()

    all_rows = []
    ats_n = 0
    ats_meta = {}

    # 1) Lane-first ATS-direct leg (stdlib; the reliable core of the upgrade).
    if not args.no_ats:
        try:
            import ats_sweep

            print("Running lane-first ATS-direct sweep (company feeds)...", file=sys.stderr)
            ats_rows = ats_sweep.sweep(
                max_age_days=args.max_age_days, remote_only=False, full=args.full
            )
            ats_meta = dict(getattr(ats_sweep, "LAST_SWEEP_META", {}) or {})
            ats_n = len(ats_rows)
            all_rows.extend(ats_rows)
            if ats_meta.get("delta"):
                print(
                    f"  (delta: {ats_meta.get('new_companies', 0)} new companies pulled full history; "
                    f"others only since last run ~{ats_meta.get('days_since')}d ago)",
                    file=sys.stderr,
                )
        except Exception as e:
            print(f"(ATS-direct leg skipped: {e})", file=sys.stderr)

    # 2) JobSpy board-recall leg (optional; cross-company title recall).
    if not args.no_boards:
        # Delta-aware board window: if new sources were added this run, pull the
        # full window; otherwise only look back to the last run (floor 24h).
        # An explicit --hours always wins.
        if not args.full and args.hours == DEFAULT_HOURS_OLD and ats_meta.get("delta"):
            if ats_meta.get("new_companies"):
                args.hours = DEFAULT_HOURS_OLD
            elif ats_meta.get("days_since") is not None:
                args.hours = min(DEFAULT_HOURS_OLD, max(24, (ats_meta["days_since"] + 1) * 24))
        print(
            f"Running JobSpy board recall (Indeed + Google, last {args.hours}h)...", file=sys.stderr
        )
        all_rows.extend(run_jobspy(args))

    if not all_rows:
        print(
            "No results from either leg. If boards errored, Indeed/Google may be "
            "rate-limiting — rerun shortly. ATS-direct needs network + the company "
            "list in ats_sweep.py.",
            file=sys.stderr,
        )
        return 2

    # Merge + dedupe on canonical job identity (prefer first seen — ATS-direct sorts fresh-first).
    seen, merged = set(), []
    for r in all_rows:
        co, title = str(r.get("company", "")).strip(), str(r.get("title", "")).strip()
        if not (co or title):
            continue
        k = jobkey.job_key(co, title)
        if k in seen:
            continue
        seen.add(k)
        merged.append(r)

    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CSV_COLS)
        w.writeheader()
        for r in merged:
            w.writerow({c: ("" if r.get(c) is None else r.get(c, "")) for c in CSV_COLS})

    print(
        f"\n{len(merged)} unique postings ({ats_n} ATS-direct + boards) -> {args.out}  "
        f"(swept {datetime.now():%Y-%m-%d %H:%M})",
        file=sys.stderr,
    )

    # Triage-score (deterministic first pass; the real fit score is apply-pipeline in chat).
    try:
        import lead_score

        scored = lead_score.score_file(args.out)
        keep = sum(1 for x in scored if x["bucket"] == "Keep")
        watch = sum(1 for x in scored if x["bucket"] == "Watch")
        print(
            f"triage: {len(scored)} in-lane -> {keep} Keep, {watch} Watch "
            f"-> leads_scored.csv  (real score comes from apply-pipeline in chat)",
            file=sys.stderr,
        )
    except Exception as e:
        print(f"(triage scoring skipped: {e})", file=sys.stderr)

    print(
        'Next: tell apply-pipeline "leads have been updated, process them" — it '
        "validates each hit at the company ATS before anything becomes a real lead.",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

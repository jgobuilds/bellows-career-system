#!/usr/bin/env python3
"""triage_leads.py — the repeatable front half of "process the leads".

Reads the newest personal/data/leads_scored.csv, keeps the Keep bucket (or the
--bucket / --min-score you pass), removes anything already in the pipeline
(matched on normalized company + title, tolerant of slug-vs-display-name, e.g.
"owner" == "Owner.com"), and writes a triage worksheet scaffold to
personal/data/triage_worksheet.json plus a readable table to stdout.

The worksheet is a scaffold, not a verdict: the honest score, the strengths/gaps
`why`, tags, and routing are the JUDGMENT step an agent (or you) fills in — a
script can't score fit honestly, and shouldn't pretend to. Once filled,
`python engine/add_jobs_batch.py` writes them all into jobs.json + pipeline.md in
one idempotent pass.

    python engine/triage_leads.py                 # newest leads_scored.csv, Keep bucket
    python engine/triage_leads.py --min-score 6   # everything scored >= 6, any bucket
    python engine/triage_leads.py --leads path.csv --out worksheet.json
"""

import argparse
import csv
import datetime
import glob
import json
import os
import sys

import _paths  # noqa: F401  (adds repo root to sys.path)
import config
import jobkey  # the one canonical job-identity module: existing_keys, is_duplicate, job_key


def newest_leads():
    d = os.path.dirname(config.JOBS_JSON)
    files = sorted(
        glob.glob(os.path.join(d, "leads_scored.csv")), key=os.path.getmtime, reverse=True
    )
    return files[0] if files else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--leads", help="path to a leads_scored.csv (default: newest)")
    ap.add_argument(
        "--out", default=os.path.join(os.path.dirname(config.JOBS_JSON), "triage_worksheet.json")
    )
    ap.add_argument("--bucket", default="Keep")
    ap.add_argument(
        "--min-score",
        type=float,
        default=None,
        help="keep everything scored >= this (overrides --bucket)",
    )
    args = ap.parse_args()

    leads = args.leads or newest_leads()
    if not leads or not os.path.exists(leads):
        sys.exit("no leads_scored.csv found — run the sweep first (python engine/jobspy_sweep.py)")

    data = json.load(open(config.JOBS_JSON, encoding="utf-8"))
    jobs = data["jobs"] if isinstance(data, dict) and "jobs" in data else data
    seen = jobkey.existing_keys(jobs)

    rows = list(csv.DictReader(open(leads, encoding="utf-8")))

    def keep(r):
        if args.min_score is not None:
            try:
                return float(r.get("score", 0)) >= args.min_score
            except (TypeError, ValueError):
                return False
        return r.get("bucket") == args.bucket

    cand = [r for r in rows if keep(r)]

    new, dup = [], 0
    for r in cand:
        if jobkey.is_duplicate(r.get("company"), r.get("title"), seen):
            dup += 1
            continue
        seen.add(jobkey.job_key(r.get("company"), r.get("title")))  # de-dupe within batch too
        new.append(r)
    new.sort(key=lambda r: float(r.get("score", 0) or 0), reverse=True)

    today = datetime.date.today().isoformat()
    worksheet = [
        {
            "record": {
                "id": None,
                "posted": r.get("date_posted", ""),
                "role": r.get("title", ""),
                "co": r.get("company", ""),
                "score": None,
                "tier": "senior",
                "warm": False,
                "fit": "",
                "tags": [],
                "why": "",
                # [[status, text], ...] with status "ok" | "warn". A bare string
                # here used to break the dashboard drawer outright.
                "checks": [],
                "diff": "",
                "cover": "",
                "status": "to review",
                "applied": "",
                "doc": None,
                "url": r.get("job_url", ""),
                # Read from the JD body during the sweep. Absent on rows added
                # before this existed, and the dashboard treats absent as "unstated".
                "workAuth": r.get("work_auth", "") or "",
                "workAuthEvidence": r.get("work_auth_evidence", "") or "",
            },
            "pipeline": {"why_short": "", "flags": "", "date_added": today, "detail_block": ""},
            "_lead": {
                "heuristic_score": r.get("score"),
                "location": r.get("location"),
                "heuristic_why": r.get("why"),
            },
        }
        for r in new
    ]
    json.dump(worksheet, open(args.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    scope = args.bucket if args.min_score is None else f">= {args.min_score}"
    print(f"leads file : {leads}")
    print(f"candidates : {len(cand)} ({scope})  |  new: {len(new)}  |  already in pipeline: {dup}")
    print(f"worksheet  : {args.out}")
    print(
        "             fill in score / why (strengths + 'Gap:' ...) / tags, then run add_jobs_batch.py\n"
    )
    for r in new:
        print(
            f"  [{r.get('score', '?')!s:>3}] {r.get('company', '')[:24]:24} | {r.get('title', '')[:56]}"
        )
    if not new:
        print("  (nothing new to triage)")


if __name__ == "__main__":
    main()

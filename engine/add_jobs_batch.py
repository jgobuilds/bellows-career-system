#!/usr/bin/env python3
"""add_jobs_batch.py — idempotent batch add of triaged jobs into the pipeline.

Reads a worksheet JSON (an array of {record, pipeline} payloads — the format
triage_leads.py scaffolds and an agent fills in) and writes every new job into
jobs.json + pipeline.md in ONE pass, recounting once. It is the repeatable,
failure-resistant version of looping add_job.py:

  - Safe to re-run: a job whose id already exists, or whose company+title already
    matches a pipeline entry, is SKIPPED, not re-added — so a partial run resumes
    cleanly and never duplicates or errors on a dup.
  - Auto-numbers: a record with a null/absent id gets the next free id, so you
    never hand-number and never collide.
  - No half-writes: the whole worksheet is validated first; jobs.json and
    pipeline.md are written only after every row builds successfully.

    python engine/add_jobs_batch.py                 # personal/data/triage_worksheet.json
    python engine/add_jobs_batch.py my_batch.json
    python engine/add_jobs_batch.py --dry-run       # report what would happen, write nothing
"""

import argparse
import json
import os
import sys

import _paths  # noqa: F401  (adds repo root to sys.path)
import jobkey  # canonical job identity (existing_keys, is_duplicate, job_key)
import pipeline_store as store  # datastore repository (load/save, insert_job, normalize_doc)

REQUIRED_REC = ("role", "co", "score", "status")
REQUIRED_PL = ("why_short", "flags", "date_added", "detail_block")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "worksheet",
        nargs="?",
        default=os.path.join(os.path.dirname(store.JOBS_JSON), "triage_worksheet.json"),
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.worksheet):
        sys.exit(f"worksheet not found: {args.worksheet} (run triage_leads.py first)")
    payloads = json.load(open(args.worksheet, encoding="utf-8"))
    if not isinstance(payloads, list):
        sys.exit("worksheet must be a JSON array of {record, pipeline} objects")

    # Validate up front so a malformed/unfinished entry never half-writes the files.
    errors = []
    for i, p in enumerate(payloads):
        rec, pl = p.get("record", {}) or {}, p.get("pipeline", {}) or {}
        miss_r = [k for k in REQUIRED_REC if rec.get(k) in (None, "")]
        miss_p = [k for k in REQUIRED_PL if pl.get(k) in (None, "")]
        if miss_r or miss_p:
            errors.append(
                f"  entry {i} ({rec.get('co', '?')} / {rec.get('role', '?')}): "
                f"missing record{miss_r} pipeline{miss_p}"
            )
    if errors:
        print("worksheet not ready — fill these in first (this is the judgment step):")
        print("\n".join(errors))
        sys.exit(1)

    data = store.load_jobs()
    jobs = store.jobs_list(data)
    have_ids = {j.get("id") for j in jobs}
    have_keys = jobkey.existing_keys(jobs)
    next_id = max([i for i in have_ids if isinstance(i, int)] or [0]) + 1

    lines = store.read_pipeline()

    added, skipped = [], []
    for p in payloads:
        rec = store.normalize_doc(dict(p["record"]))
        pl = p["pipeline"]
        if rec.get("id") in have_ids or jobkey.is_duplicate(
            rec.get("co"), rec.get("role"), have_keys
        ):
            skipped.append(f"{rec.get('co')} / {rec.get('role')} (already in pipeline)")
            continue
        if not isinstance(rec.get("id"), int):
            rec["id"] = next_id
            next_id += 1
        jobs.append(rec)
        have_ids.add(rec["id"])
        have_keys.add(jobkey.job_key(rec.get("co"), rec.get("role")))
        store.insert_job(lines, rec, pl)  # raises on a broken table -> abort, nothing written
        added.append(
            f"{rec['id']:>3}  {rec['co']} — {rec['role']} (score {rec['score']}, {rec['status']})"
        )

    print(f"worksheet  : {args.worksheet}")
    print(f"to add     : {len(added)}   |   skipped (already present): {len(skipped)}")
    for a in added:
        print("  + " + a)
    for s in skipped:
        print("  · skip " + s)

    if args.dry_run:
        print("\n[dry run] nothing written.")
        return
    if not added:
        print("\nnothing new to write.")
        return

    store.save_jobs(data)
    store.write_pipeline(lines)
    summary = next((line for line in lines if line.startswith("- Added:")), "").strip()
    print(f"\nwrote {len(added)} job(s) to jobs.json + pipeline.md")
    print(f"summary: {summary}")


if __name__ == "__main__":
    main()

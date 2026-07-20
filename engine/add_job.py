#!/usr/bin/env python3
"""
add_job.py — append one scored job to the board (personal/data/jobs.json + personal/data/pipeline.md)
from a single JSON input, consistently.

Replaces the per-job throwaway "add_<company>.py" scripts. The dashboard reads
jobs.json; pipeline.md is the human-readable record. This writes both from one
input and recomputes the summary-counts line so it can't drift.

USAGE
  python engine/add_job.py <job.json>

INPUT SHAPE (see personal/applications/<company>/job.json for a live example):
  {
    "record": { ...the full jobs.json object: id, role, co, score, tier, warm,
                fit, tags, why, checks, diff, cover, status, applied, posted, doc },
    "pipeline": {
      "why_short": "one-line why for the table row",
      "flags": "integrity flags for the table row",
      "date_added": "2026-07-16",
      "detail_block": "### Job N — Co, Role\\n- **Tags:** ...\\n..."   # markdown block
    }
  }

The table row is DERIVED from record (id/role/co/score/tier/warm/status) + the
pipeline why_short/flags/date, so those never have to be hand-formatted twice.
"""

import json
import os
import sys

import _paths

_ROOT = _paths.ROOT

# Datastore reads/writes go through the repository; job identity through jobkey.
# Both are re-exported so any `add_job.is_duplicate` / `add_job.insert_pipeline`
# call-site keeps working, but new code should import jobkey / pipeline_store.
import pipeline_store as store
from jobkey import existing_keys, is_duplicate, job_key, norm_co, norm_title  # noqa: F401
from pipeline_store import (  # noqa: F401 - back-compat re-exports
    SUBMITTED,
    jobs_list,
    load_jobs,
    normalize_doc,
    save_jobs,
)

insert_pipeline = store.insert_job  # old name kept for callers


def _resolve(p: str) -> str:
    """Accept an absolute path, a cwd-relative path, or a repo-root-relative one."""
    if os.path.isabs(p) or os.path.exists(p):
        return p
    cand = os.path.join(_ROOT, p)
    return cand if os.path.exists(cand) else p


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: python add_job.py <job.json>")
    job = json.load(open(_resolve(sys.argv[1]), encoding="utf-8"))
    rec = store.normalize_doc(job["record"])
    pl = job["pipeline"]
    jid = rec["id"]

    data = store.load_jobs()
    jobs = store.jobs_list(data)
    if any(x.get("id") == jid for x in jobs):
        sys.exit(
            f"job id {jid} already in {store.JOBS_JSON} — use set-status to edit, don't re-add"
        )
    jobs.append(rec)
    store.save_jobs(data)

    lines = store.read_pipeline()
    store.insert_job(lines, rec, pl)
    store.write_pipeline(lines)

    ok = any(line.startswith("|") and line.split("|")[1].strip() == str(jid) for line in lines)
    print(f"added job {jid} ({rec['co']} — {rec['role']}, score {rec['score']}, {rec['status']})")
    print(f"  jobs.json total: {len(jobs)} · pipeline row: {'OK' if ok else 'MISSING'}")
    print(f"  summary: {next(line for line in lines if line.startswith('- Added:')).strip()}")


if __name__ == "__main__":
    main()

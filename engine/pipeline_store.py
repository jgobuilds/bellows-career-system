#!/usr/bin/env python3
"""pipeline_store.py — the one place that reads and writes the datastore.

The datastore is two files kept in lockstep: jobs.json (the machine record the
PII-free dashboard reads) and pipeline.md (the human record + source of truth).
They used to be read and written from three places (add_job, add_jobs_batch,
server) with duplicated json.load/dump and duplicated pipeline-row logic. This
module is the Repository that owns them, so the "write both + recount" invariant
lives in exactly one place.

Pure-ish: the table helpers (data_rows / recount / insert_job) operate on an
in-memory line list and are unit-tested without touching disk; only load/save/
read/write do file I/O.
"""

import json
import os
import re

import _paths  # noqa: F401  (adds repo root to sys.path)
import config

JOBS_JSON = config.JOBS_JSON
PIPELINE_MD = config.PIPELINE_MD

# Statuses that count as "submitted" for the pipeline.md Applied tally.
SUBMITTED = {
    "applied",
    "interviewing",
    "offer",
    "accepted",
    "rejected",
    "no response",
    "response",
    "declined",
    "closed",
}


# ---- jobs.json ------------------------------------------------------------
def load_jobs() -> dict:
    """Parsed jobs.json, or an empty shell if it's missing/unreadable."""
    try:
        with open(JOBS_JSON, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {"generated": "", "jobs": [], "glassdoor": {}, "resumePrefix": ""}


def save_jobs(data: dict) -> None:
    with open(JOBS_JSON, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)


def jobs_list(data: dict | list) -> list:
    """The jobs list whether jobs.json is {"jobs":[...]} or a bare list."""
    if isinstance(data, dict):
        return data.get("jobs", [])
    return data


def find_job(data: dict | list, job_id: int) -> dict | None:
    for j in jobs_list(data):
        if j.get("id") == job_id:
            return j
    return None


def normalize_doc(rec: dict) -> dict:
    """`doc` is the folder slug under personal/applications/ (e.g. "burq"), NOT a
    path. Normalize so a stray "applications/burq/" can't break the doc links."""
    if rec.get("doc"):
        rec["doc"] = os.path.basename(str(rec["doc"]).replace("\\", "/").rstrip("/"))
    return rec


# ---- pipeline.md ----------------------------------------------------------
def read_pipeline() -> list[str]:
    with open(PIPELINE_MD, encoding="utf-8") as fh:
        return fh.readlines()


def write_pipeline(lines: list[str]) -> None:
    with open(PIPELINE_MD, "w", encoding="utf-8") as fh:
        fh.writelines(lines)


def data_rows(lines: list[str]) -> list[int]:
    """Indices of table data rows (| id | ... |) whose second cell is an int."""
    idx = []
    for i, line in enumerate(lines):
        if line.startswith("|"):
            cells = line.split("|")
            if len(cells) > 8 and cells[1].strip().isdigit():
                idx.append(i)
    return idx


def recount(lines: list[str]) -> None:
    """Recompute only the objective, table-derivable counts (total, worth-a-look,
    warm, submitted) in place. The qualitative buckets (Tailored/Parked/JD-*) are
    curated by hand and mean 'cumulative/decided', so we leave them alone."""
    rows = [lines[i].split("|") for i in data_rows(lines)]
    added = len(rows)
    worth = sum(1 for c in rows if c[4].strip().isdigit() and int(c[4].strip()) >= 7)
    warm = sum(1 for c in rows if c[6].strip().lower() in ("yes", "y", "✓"))
    applied = sum(1 for c in rows if c[8].strip() in SUBMITTED)
    subs = {
        r"Added: \d+": f"Added: {added}",
        r"Worth a look \(≥7\): \d+": f"Worth a look (≥7): {worth}",
        r"Warm path: \d+": f"Warm path: {warm}",
        r"Applied: \d+": f"Applied: {applied}",
    }
    for i, line in enumerate(lines):
        if line.startswith("- Added:"):
            for pat, rep in subs.items():
                line = re.sub(pat, rep, line)
            lines[i] = line
            break


def insert_job(lines: list[str], rec: dict, pl: dict) -> list[str]:
    """Insert one row + detail block into the pipeline.md line list and recount.
    Mutates `lines` in place. Raises ValueError if the table can't be found."""
    warm = "yes" if rec.get("warm") else "no"
    row = (
        f"| {rec['id']} | {rec['role']} | {rec['co']} | {rec['score']} | {rec.get('tier', 'senior')} | "
        f"{warm} | — | {rec['status']} | {pl['why_short']} | {pl['flags']} | {pl['date_added']} |\n"
    )
    rows = data_rows(lines)
    if not rows:
        raise ValueError("no table rows found in pipeline.md — is the file intact?")
    lines.insert(rows[-1] + 1, row)  # append after the last table row

    block = pl["detail_block"].rstrip("\n") + "\n\n"
    summary_i = next(
        (i for i, line in enumerate(lines) if line.startswith("## Summary counts")), None
    )
    if summary_i is not None:
        lines.insert(summary_i, block)  # detail blocks live above the summary
    else:
        lines.append("\n" + block)
    recount(lines)
    return lines

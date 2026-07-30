#!/usr/bin/env python3
"""repair_pipeline.py — reconcile jobs.json and pipeline.md when they drift apart.

    python engine/repair_pipeline.py            # report only
    python engine/repair_pipeline.py --fix      # rebuild the missing rows

WHY THIS EXISTS. jobs.json and pipeline.md are two halves of one datastore and the
dashboard assumes they agree. Appending straight to the jobs list — one obvious line
of code that skips `pipeline_store` entirely — produces a job the board can render
but cannot UPDATE: `/api/set-status` looks for the pipeline.md row, does not find
it, and returns 404. Dragging the card fails with no obvious cause.

The failure is worse than a plain error. `set_status` writes jobs.json BEFORE the row
lookup decides the request failed, so the status changes on one side while the user
is told nothing happened, and the halves drift further with every retry.

jobs.json is treated as the record of truth here, because it carries the structured
fields (score, checks, tags, why) that a pipeline.md row is rendered FROM. So a
missing row can be rebuilt; an orphan row cannot be, and is only reported.
"""

import argparse
import sys
import textwrap

import _paths  # noqa: F401  (side-effect: repo root on sys.path)
import pipeline_store as store


def row_payload(rec: dict) -> dict:
    """The pipeline.md presentation of a job, derived from its jobs.json record."""
    why = rec.get("why") or rec.get("cover") or ""
    checks = rec.get("checks") or []
    warns = [c[1] for c in checks if isinstance(c, list) and len(c) == 2 and c[0] == "warn"]
    return {
        "why_short": (why.split(". ")[0][:118] or "—"),
        "flags": " - ".join(w.split(".")[0][:58] for w in warns[:2]) or "none",
        "date_added": rec.get("date_added") or "—",
        "detail_block": (
            f"### {rec.get('co', '?')} - {rec.get('role', '?')}\n\n"
            f"- **Score:** {rec.get('score')}  ·  **Status:** {rec.get('status')}\n"
            f"- **Tags:** {', '.join(rec.get('tags') or [])}\n"
            + (f"- **Comp:** {rec['comp']}\n" if rec.get("comp") else "")
            + f"- **Why:** {textwrap.shorten(why, 900, placeholder=' …')}\n"
            + "".join(
                f"- **{c[0].upper()}:** {c[1]}\n"
                for c in checks
                if isinstance(c, list) and len(c) == 2
            )
            + f"- **URL:** {rec.get('url', '')}\n"
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Reconcile jobs.json with pipeline.md.")
    ap.add_argument("--fix", action="store_true", help="rebuild rows missing from pipeline.md")
    a = ap.parse_args()

    data = store.load_jobs()
    lines = store.read_pipeline()
    drift = store.orphans(data, lines)
    missing, orphan = drift["missing_rows"], drift["orphan_rows"]

    if not missing and not orphan:
        print("  jobs.json and pipeline.md agree — nothing to repair.")
        return 0

    if orphan:
        print(f"  {len(orphan)} row(s) in pipeline.md with no jobs.json record: {orphan}")
        print("    Not auto-repairable — a row cannot reconstruct the structured record.")
        print("    Remove the row by hand, or restore the record.")

    if missing:
        print(f"  {len(missing)} job(s) in jobs.json with no pipeline.md row: {missing}")
        for jid in missing:
            rec = store.find_job(data, jid) or {}
            print(f"    #{jid}  {rec.get('co', '?')} / {(rec.get('role') or '?')[:44]}")
        if not a.fix:
            print("\n  Re-run with --fix to rebuild them.")
            return 1
        for jid in missing:
            found = store.find_job(data, jid)
            if found is None:  # raced with an edit; skip rather than write a blank row
                continue
            store.insert_job(lines, found, row_payload(found))
        store.write_pipeline(lines)
        print(f"\n  rebuilt {len(missing)} row(s).")

    return 0 if not orphan else 1


if __name__ == "__main__":
    sys.exit(main())

"""Tests for pipeline_store — the datastore repository (F4).

Exercises the pure table logic (data_rows / recount / insert_job) on in-memory
lines, plus jobs_list / find_job / normalize_doc — no disk I/O. Stdlib unittest.
"""

import os
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine")
)
import pipeline_store as store

SAMPLE = [
    "# Pipeline\n",
    "| ID | Role | Company | Score | Tier | Warm? | Contact | Status | Why | Flags | Date |\n",
    "|----|------|---------|-------|------|-------|---------|--------|-----|-------|------|\n",
    "| 1 | Director X | Acme | 8 | senior | yes | Jo | applied | ok | - | 2026-01-01 |\n",
    "| 2 | Head Y | Beta | 5 | senior | no | — | to review | ok | - | 2026-01-02 |\n",
    "\n",
    "## Summary counts\n",
    "- Added: 2 · Worth a look (≥7): 1 · Warm path: 1 · Applied: 1\n",
]


class TestTableHelpers(unittest.TestCase):
    def test_data_rows_finds_numbered_rows_only(self):
        self.assertEqual(len(store.data_rows(SAMPLE)), 2)

    def test_insert_job_adds_row_block_and_recounts(self):
        lines = list(SAMPLE)
        rec = {
            "id": 3,
            "role": "VP Data",
            "co": "Cprp",
            "score": 9,
            "tier": "senior",
            "warm": True,
            "status": "to review",
        }
        pl = {
            "why_short": "strong",
            "flags": "ok",
            "date_added": "2026-02-01",
            "detail_block": "### Job 3 — Cprp, VP Data\n- **Tags:** a",
        }
        store.insert_job(lines, rec, pl)
        self.assertTrue(any(line.startswith("| 3 ") for line in lines))
        self.assertTrue(any("### Job 3" in line for line in lines))
        summary = next(line for line in lines if line.startswith("- Added:"))
        self.assertIn("Added: 3", summary)
        self.assertIn("Worth a look (≥7): 2", summary)  # scores 8 and 9
        self.assertIn("Warm path: 2", summary)  # Acme + the new one

    def test_insert_job_raises_without_a_table(self):
        with self.assertRaises(ValueError):
            store.insert_job(
                ["# no table\n"],
                {"id": 1, "role": "r", "co": "c", "score": 1, "status": "x"},
                {"why_short": "", "flags": "", "date_added": "", "detail_block": "x"},
            )


class TestJobsHelpers(unittest.TestCase):
    def test_jobs_list_handles_dict_or_bare_list(self):
        self.assertEqual(store.jobs_list({"jobs": [1, 2]}), [1, 2])
        self.assertEqual(store.jobs_list([1, 2]), [1, 2])

    def test_find_job(self):
        d = {"jobs": [{"id": 1}, {"id": 2}]}
        self.assertEqual(store.find_job(d, 2), {"id": 2})
        self.assertIsNone(store.find_job(d, 9))

    def test_normalize_doc_strips_stray_path(self):
        self.assertEqual(store.normalize_doc({"doc": "applications/burq/"})["doc"], "burq")
        self.assertEqual(store.normalize_doc({"doc": "burq"})["doc"], "burq")
        self.assertIsNone(store.normalize_doc({}).get("doc"))


if __name__ == "__main__":
    unittest.main()

"""Tests for ats_match's pure scorer (F6). evaluate() is now separate from
printing, so the coverage math is testable. Config-free (resume read from a .txt).
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine")
)
import ats_match


def _resume(text):
    p = os.path.join(tempfile.gettempdir(), "_ats_resume_test.txt")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(text)
    return p


class TestEvaluate(unittest.TestCase):
    def test_present_terms_score_and_missing_are_flagged(self):
        resume = _resume("Led data governance on Snowflake and dbt with Python.")
        try:
            # databricks + airflow are lexicon skills the resume lacks -> flagged missing
            r = ats_match.evaluate(
                resume,
                "Requirements: python, dbt, data governance, snowflake, databricks, airflow.",
            )
            present = {t for t, _ in r["present"]}
            missing = {t for t, _ in r["missing"]}
            self.assertFalse(r["empty"])
            self.assertIn("data governance", present)
            self.assertIn("python", present)
            self.assertIn("databricks", missing)  # lexicon term, not on the resume
            self.assertTrue(0 <= r["pct"] <= 100)
        finally:
            os.remove(resume)

    def test_full_coverage_scores_high(self):
        resume = _resume("Python and dbt and data governance and snowflake all here.")
        try:
            r = ats_match.evaluate(resume, "Requirements: python, dbt, data governance, snowflake.")
            self.assertGreaterEqual(r["pct"], 90)
            self.assertTrue(r["passed"])
        finally:
            os.remove(resume)

    def test_empty_jd_is_flagged_not_crashed(self):
        resume = _resume("anything at all")
        try:
            r = ats_match.evaluate(resume, "")
            self.assertTrue(r["empty"])
            self.assertEqual(r["pct"], 0)
        finally:
            os.remove(resume)


if __name__ == "__main__":
    unittest.main()

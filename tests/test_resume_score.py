"""Tests for the standalone résumé health score (resume_score.score_spec).

Pure logic, config-free (imports resume_builder, which needs python-docx). Stdlib
unittest.
"""

import os
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine")
)
import resume_score


def _spec(bullets, **extra):
    """A minimal one-role spec with the given [lead, rest] bullets."""
    base = {
        "contact": "City, ST | a@b.com | 555-555-5555",
        "summary": "One clean summary paragraph.",
        "experience": [
            {
                "company": "Acme",
                "title": "Director of Data Governance",
                "location_dates": "City, ST | 2020 - 2024",
                "bullets": bullets,
            }
        ],
    }
    base.update(extra)
    return base


class TestQuantification(unittest.TestCase):
    def test_all_quantified_bullets_score_full_quant(self):
        spec = _spec([["Cut ramp", " from 5.5 to 3.5 months."], ["Lifted signups", " 31% to 45%."]])
        r = resume_score.score_spec(spec)
        self.assertEqual(r["dimensions"]["quantified"], resume_score.W_QUANT)
        self.assertEqual(r["weak_bullets"], [])

    def test_unquantified_bullet_is_flagged_and_costs_points(self):
        spec = _spec([["Rebuilt the competitive program", " end to end."]])
        r = resume_score.score_spec(spec)
        self.assertEqual(r["dimensions"]["quantified"], 0)
        self.assertEqual(len(r["weak_bullets"]), 1)

    def test_half_quantified_scores_half(self):
        spec = _spec([["Grew pipeline", " 20%."], ["Owned positioning", " across the platform."]])
        r = resume_score.score_spec(spec)
        self.assertEqual(r["dimensions"]["quantified"], round(resume_score.W_QUANT * 0.5))


class TestAtsAndStructure(unittest.TestCase):
    def test_punctuated_title_costs_ats_points(self):
        clean = resume_score.score_spec(_spec([["Grew pipeline", " 20%."]]))
        bad = _spec([["Grew pipeline", " 20%."]])
        bad["experience"][0]["title"] = "Director, Data Governance"  # comma can truncate
        worse = resume_score.score_spec(bad)
        self.assertLess(worse["dimensions"]["ats_safe"], clean["dimensions"]["ats_safe"])

    def test_missing_summary_and_contact_cost_tight_points(self):
        spec = _spec(
            [["Grew pipeline", " 20%."], ["Cut cost", " 10%."], ["Shipped", " 3 launches."]]
        )
        spec["summary"] = ""
        del spec["contact"]
        r = resume_score.score_spec(spec)
        self.assertEqual(r["dimensions"]["tight_complete"], resume_score.W_TIGHT - 10)

    def test_grade_boundaries(self):
        self.assertEqual(resume_score._grade(90), "A")
        self.assertEqual(resume_score._grade(74), "C")
        self.assertEqual(resume_score._grade(20), "F")


if __name__ == "__main__":
    unittest.main()

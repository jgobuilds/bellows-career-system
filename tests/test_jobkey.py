"""Tests for jobkey — the canonical job-identity module (F1).

Run:  python -m unittest discover -s tests
  or: python tests/test_jobkey.py
No pytest required (stdlib unittest), but `pytest tests/` also works.
"""

import os
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine")
)
import jobkey


class TestNormCo(unittest.TestCase):
    def test_suffix_stripping_makes_slug_equal_display(self):
        self.assertEqual(jobkey.norm_co("Owner.com"), jobkey.norm_co("owner"))
        self.assertEqual(jobkey.norm_co("Acme, Inc."), jobkey.norm_co("Acme"))
        self.assertEqual(jobkey.norm_co("Globex LLC"), jobkey.norm_co("Globex"))

    def test_punctuation_and_case_ignored(self):
        self.assertEqual(jobkey.norm_co("TD"), "td")
        self.assertEqual(jobkey.norm_co("  J.P. Morgan  "), jobkey.norm_co("jpmorgan"))

    def test_short_suffix_like_name_not_over_stripped(self):
        self.assertEqual(jobkey.norm_co("Co"), "co")  # too short to strip "co"


class TestIsDuplicate(unittest.TestCase):
    def keys(self, *pairs):
        return {jobkey.job_key(c, t) for c, t in pairs}

    def test_exact_match(self):
        k = self.keys(("TD", "Head of Technology Data Management"))
        self.assertTrue(jobkey.is_duplicate("TD", "Head of Technology Data Management", k))

    def test_company_slug_vs_display_name(self):
        # the "owner" vs "Owner.com" bug that motivated this module
        k = self.keys(("Owner.com", "Director of Data Platform Engineering"))
        self.assertTrue(jobkey.is_duplicate("owner", "Director of Data Platform Engineering", k))

    def test_title_noise_absorbed_by_containment(self):
        # stored clean role vs a lead title carrying "- Company - Remote" noise
        k = self.keys(("The Cigna Group", "Product Strategy Director, Provider Data"))
        self.assertTrue(
            jobkey.is_duplicate(
                "The Cigna Group",
                "Product Strategy Director - Provider Data - Cigna Healthcare - Remote",
                k,
            )
        )

    def test_distinct_roles_at_same_company_are_not_dupes(self):
        k = self.keys(("CVS Health", "Executive Director, Technology Operations"))
        self.assertFalse(
            jobkey.is_duplicate("CVS Health", "Executive Director, Digital Transformation", k)
        )

    def test_short_title_does_not_false_match_by_containment(self):
        k = self.keys(("Acme", "Director"))  # 8 chars < 12 guard
        self.assertFalse(jobkey.is_duplicate("Acme", "Director of Data Platform Engineering", k))

    def test_empty_inputs_are_safe(self):
        self.assertFalse(jobkey.is_duplicate("", "", set()))
        self.assertFalse(jobkey.is_duplicate("Acme", "", self.keys(("Acme", "Director"))))


class TestExistingKeys(unittest.TestCase):
    def test_reads_jobs_json_field_names(self):
        jobs = [{"co": "TD", "role": "Head of Data"}, {"co": "Ravel", "role": "Director of PM"}]
        keys = jobkey.existing_keys(jobs)
        self.assertIn(jobkey.job_key("TD", "Head of Data"), keys)
        self.assertEqual(len(keys), 2)


if __name__ == "__main__":
    unittest.main()

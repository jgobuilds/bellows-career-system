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

    def test_ampersand_and_the_word_and_are_the_same_title(self):
        # the board writes "&", the pipeline gets typed with "and" - one job, and
        # before the conjunction was folded every such role re-surfaced each sweep
        k = self.keys(("USAA", "Director, Data Governance and Compliance"))
        self.assertTrue(jobkey.is_duplicate("USAA", "Director, Data Governance & Compliance", k))
        self.assertEqual(
            jobkey.norm_title("Senior Director, Data Platform & Governance"),
            jobkey.norm_title("Senior Director, Data Platform and Governance"),
        )

    def test_folding_the_conjunction_does_not_merge_distinct_roles(self):
        k = self.keys(("Acme", "Director, Data Platform & Governance"))
        self.assertFalse(jobkey.is_duplicate("Acme", "Director, Data Platform & Security", k))

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


class AtsSlugSuffixTest(unittest.TestCase):
    """A slug and a company name have to resolve to the same identity.

    The ATS-direct sweep has no company name available - it knows only the slug it
    polled - so a posting arrives as "mariner-careers" while the same company sits on
    the board as "Mariner". Dedupe compared them, found no match, and re-proposed a
    role that had already been APPLIED to as a fresh lead.

    The duplicate itself is cheap. What it costs is trust in the list: one that
    re-surfaces decided roles is one people stop reading, and then a real lead goes by
    unnoticed too.
    """

    def test_a_careers_slug_matches_the_company_name(self):
        self.assertEqual(jobkey.norm_co("mariner-careers"), jobkey.norm_co("Mariner"))

    def test_the_other_common_ats_slug_suffixes(self):
        for slug, name in (
            ("acme-jobs", "Acme"),
            ("acme-hq", "Acme"),
            ("acmepeople", "Acme"),
        ):
            self.assertEqual(jobkey.norm_co(slug), jobkey.norm_co(name), slug)

    def test_a_company_whose_NAME_is_the_suffix_survives(self):
        # Stripping has a length guard so short names are not eaten. "Careers" as a
        # company name must stay "careers", not become "".
        for name in ("Careers", "Jobs", "HQ"):
            self.assertTrue(jobkey.norm_co(name), name)

    def test_the_suffix_is_only_stripped_at_the_end(self):
        # CareerBuilder and JobsOhio start with the word; they must be untouched.
        self.assertEqual(jobkey.norm_co("CareerBuilder"), "careerbuilder")
        self.assertEqual(jobkey.norm_co("JobsOhio"), "jobsohio")
        self.assertEqual(jobkey.norm_co("PeopleSoft"), "peoplesoft")

    def test_unrelated_companies_still_do_not_collide(self):
        self.assertNotEqual(jobkey.norm_co("mariner-careers"), jobkey.norm_co("Marina"))

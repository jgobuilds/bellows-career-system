"""Tests for ATS careers-board resolution (ats_url).

Pure logic, config-free. Stdlib unittest.
"""

import os
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine")
)
import ats_url

COMPANIES = [
    {"ats": "greenhouse", "slug": "assetwatch"},
    {"ats": "lever", "slug": "plaid"},
    {"ats": "ashby", "slug": "mariner-careers"},
    {"ats": "smartrecruiters", "slug": "acme"},
    {"ats": "workday", "tenant": "thehartford", "wd": "wd5", "site": "Careers_External"},
    {"ats": "workday", "tenant": "pfizer", "wd": "wd1", "site": "PfizerCareers"},
    {"ats": "greenhouse"},  # malformed: no slug -> must be skipped, not crash
]


class TestCareersUrl(unittest.TestCase):
    def test_each_ats_flavor_builds(self):
        self.assertEqual(
            ats_url.careers_url(COMPANIES[0]), "https://job-boards.greenhouse.io/assetwatch"
        )
        self.assertEqual(ats_url.careers_url(COMPANIES[1]), "https://jobs.lever.co/plaid")
        self.assertEqual(
            ats_url.careers_url(COMPANIES[2]), "https://jobs.ashbyhq.com/mariner-careers"
        )
        self.assertEqual(ats_url.careers_url(COMPANIES[3]), "https://jobs.smartrecruiters.com/acme")
        self.assertEqual(
            ats_url.careers_url(COMPANIES[4]),
            "https://thehartford.wd5.myworkdayjobs.com/Careers_External",
        )

    def test_unbuildable_entry_returns_none(self):
        self.assertIsNone(ats_url.careers_url(COMPANIES[6]))
        self.assertIsNone(ats_url.careers_url({"ats": "workday", "tenant": "x"}))  # missing wd/site
        self.assertIsNone(ats_url.careers_url({"ats": "carrier-pigeon", "slug": "x"}))


class TestResolution(unittest.TestCase):
    def test_exact_match(self):
        self.assertEqual(
            ats_url.ats_url_for("AssetWatch", COMPANIES),
            "https://job-boards.greenhouse.io/assetwatch",
        )

    def test_corporate_suffix_is_ignored(self):
        # "Wpromote, LLC" style noise must not defeat the match
        self.assertEqual(
            ats_url.ats_url_for("Plaid, Inc.", COMPANIES), "https://jobs.lever.co/plaid"
        )

    def test_the_prefix_ignored(self):
        self.assertEqual(
            ats_url.ats_url_for("The Hartford", COMPANIES),
            "https://thehartford.wd5.myworkdayjobs.com/Careers_External",
        )

    def test_partial_match_inside_a_longer_name(self):
        self.assertEqual(
            ats_url.ats_url_for("Pfizer Global Biopharma", COMPANIES),
            "https://pfizer.wd1.myworkdayjobs.com/PfizerCareers",
        )

    def test_unknown_company_returns_none(self):
        self.assertIsNone(ats_url.ats_url_for("JPMorganChase", COMPANIES))
        self.assertIsNone(ats_url.ats_url_for("", COMPANIES))
        self.assertIsNone(ats_url.ats_url_for(None, COMPANIES))

    def test_short_tokens_cannot_match_everything(self):
        # a 2-char slug must never partial-match an unrelated company
        self.assertIsNone(
            ats_url.ats_url_for("Northwind Analytics", [{"ats": "lever", "slug": "no"}])
        )

    def test_empty_company_list_is_safe(self):
        self.assertIsNone(ats_url.ats_url_for("AssetWatch", []))


if __name__ == "__main__":
    unittest.main()

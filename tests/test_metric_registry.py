"""The figure allowlist: numbers a document may carry, and on what terms.

These tests use a synthetic registry rather than the real one. The real registry
lives under the gitignored `personal/` tree, so CI never sees it, and a test that
depended on it would pass on a developer's laptop and fail on the runner.
"""

import os
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine")
)

import metric_registry

REGISTRY = {
    "not_a_claim": [r"Fortune 500", r"AGPL-3\.0"],
    "employer_aliases": {"Freelance": ["Contract Services"]},
    "never_together": [{"a": "310", "b": "85", "why": "seats overlap; never summed"}],
    "check_together": [{"a": "$775K", "b": "$18K", "why": "the $18K is inside the $775K"}],
    "metrics": [
        {
            "id": "acme.savings",
            "tokens": ["$775K"],
            "usage": "document",
            "measured": True,
            "sample": "annual licensing eliminated",
            "employers": ["Acme"],
        },
        {
            "id": "acme.proof",
            "tokens": ["$18K"],
            "usage": "document",
            "measured": True,
            "sample": "one connector",
            "employers": ["Acme"],
        },
        {
            "id": "acme.anecdote",
            "tokens": ["12-26"],
            "usage": "interview_only",
            "measured": False,
            "sample": "UNRECORDED",
            "why_not_document": "case count never recorded",
            "employers": ["Acme"],
        },
        {
            "id": "acme.reach",
            "tokens": ["310"],
            "usage": "document",
            "measured": True,
            "sample": "the department",
            "employers": ["Acme"],
        },
        {
            "id": "acme.seats",
            "tokens": ["85"],
            "usage": "document",
            "measured": True,
            "sample": "funded seats",
            "employers": ["Acme"],
        },
        # Deliberately shares the '100+' token with the entry below: one number
        # can legitimately mean different things at two employers.
        {
            "id": "acme.hours",
            "tokens": ["640+"],
            "usage": "document",
            "measured": True,
            "sample": "hours/month",
            "employers": ["Acme"],
        },
        {
            "id": "beta.users",
            "tokens": ["640+"],
            "usage": "document",
            "measured": True,
            "sample": "report recipients",
            "employers": ["Beta"],
        },
        {
            "id": "career.years",
            "tokens": ["7+"],
            "usage": "document",
            "measured": True,
            "sample": "whole career",
        },
    ],
}


def spec(bullet, company="Acme", **extra):
    s = {
        "name": "A Candidate",
        "contact": "Anytown, ZZ | 555.0100",
        "summary": "A summary.",
        "experience": [
            {
                "company": company,
                "title": "Director",
                "location_dates": "City, ST | 2020 – 2024",
                "bullets": [["Lead", bullet]],
            }
        ],
    }
    s.update(extra)
    return s


class RegistryTest(unittest.TestCase):
    def warns(self, s):
        return metric_registry.warnings(s, REGISTRY)

    def test_registered_figure_at_its_own_employer_is_silent(self):
        self.assertEqual(self.warns(spec(" cut spend by $775K a year.")), [])

    def test_unregistered_number_is_flagged(self):
        w = self.warns(spec(" served 4,200 users."))
        self.assertTrue(any("UNREGISTERED" in x and "4,200" in x for x in w), w)

    def test_interview_only_figure_is_blocked(self):
        w = self.warns(spec(" compressed 12-26 hours of work."))
        self.assertTrue(any("INTERVIEW-ONLY" in x for x in w), w)
        self.assertTrue(any("case count never recorded" in x for x in w), w)

    def test_figure_drifting_to_the_wrong_employer_is_flagged(self):
        w = self.warns(spec(" cut spend by $775K.", company="Beta"))
        self.assertTrue(any("WRONG EMPLOYER" in x for x in w), w)

    def test_a_token_shared_by_two_employers_is_silent_at_each(self):
        # The bug this guards: collapsing tokens to one metric made the guard
        # accuse correct bullets of drifting between employers.
        self.assertEqual(self.warns(spec(" saved 640+ hours a month.")), [])
        self.assertEqual(self.warns(spec(" reached 640+ recipients.", company="Beta")), [])

    def test_employer_alias_resolves_to_one_employer(self):
        s = spec(" reached 7+ years.", company="Contract Services")
        self.assertEqual([w for w in self.warns(s) if "WRONG EMPLOYER" in w], [])

    def test_hard_adjacency_rule_fires_on_cooccurrence(self):
        w = self.warns(spec(" rolled out to 310 people with 85 seats."))
        self.assertTrue(any("NEVER-TOGETHER" in x for x in w), w)

    def test_advisory_pair_is_only_a_note_when_sequenced(self):
        w = self.warns(spec(" proved it with the $18K connector, then cancelled $775K."))
        self.assertTrue(any(x.startswith("NOTE:") for x in w), w)
        self.assertFalse(any("NEVER-TOGETHER" in x for x in w), w)

    def test_advisory_pair_escalates_when_summed(self):
        w = self.warns(spec(" the $18K connector plus $775K of licensing."))
        self.assertTrue(any("NEVER-TOGETHER" in x for x in w), w)

    def test_idioms_and_versions_are_not_claims(self):
        self.assertEqual(self.warns(spec(" inside Fortune 500 insurers.")), [])
        self.assertEqual(self.warns(spec(" published under AGPL-3.0.")), [])

    def test_years_and_contact_details_are_not_claims(self):
        # A date is a calendar, and a phone number is an address.
        self.assertEqual(self.warns(spec(" from 2019 to 2022.")), [])

    def test_summary_prose_is_checked_too(self):
        s = spec(" ordinary text.")
        s["summary"] = "Leader who saved 4,200 hours."
        self.assertTrue(any("UNREGISTERED" in x for x in self.warns(s)), self.warns(s))

    def test_missing_registry_is_not_an_error(self):
        self.assertEqual(metric_registry.warnings(spec(" saved $775K."), {}), [])


if __name__ == "__main__":
    unittest.main()

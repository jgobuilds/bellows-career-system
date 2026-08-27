#!/usr/bin/env python3
"""Tests for the library's generation and re-validation modes.

The case that matters most asserts that a phrasing failing TODAY'S rules is never
offered. Approval is a snapshot: a bullet checked in July stays "verified" forever,
including after the claim inside it is corrected in August. Four phrasings using a
forbidden growth verb sat approved while the registry had banned exactly that
pairing in prose the whole time, and one was offered as a top-three suggestion for
a live application.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine")
)

import bullet_library as bl


def _entry(lead, rest, fp, revoked=None):
    e = {"fp": fp, "lead": lead, "rest": rest, "tokens": [], "approved": "2026-07-01"}
    if revoked:
        e["revoked"] = revoked
    return e


class TestSuggest(unittest.TestCase):
    def setUp(self):
        self.DATA = {
            "employers": {
                "Acme": [
                    _entry(
                        "Built data pipelines on dbt and Airflow", " across three domains.", "a1"
                    ),
                    _entry(
                        "Automated broker compensation reporting", " and quarterly close.", "a2"
                    ),
                ]
            }
        }

    def test_it_ranks_by_fit_to_the_posting(self):
        jd = "We need someone to run data pipelines with dbt and Airflow."
        got = bl.suggest(jd, top=5, data=self.DATA)
        self.assertTrue(got["Acme"])
        self.assertIn("dbt", got["Acme"][0]["text"])

    def test_a_phrasing_with_no_overlap_is_not_offered(self):
        jd = "We need someone to run data pipelines with dbt and Airflow."
        texts = [r["text"] for r in bl.suggest(jd, top=5, data=self.DATA)["Acme"]]
        self.assertFalse(any("broker compensation" in t for t in texts))

    def test_a_revoked_phrasing_is_never_offered(self):
        data = {
            "employers": {
                "Acme": [
                    _entry(
                        "Built data pipelines on dbt and Airflow",
                        " across three domains.",
                        "a1",
                        revoked={"on": "2026-08-24", "why": "test"},
                    )
                ]
            }
        }
        self.assertEqual(bl.suggest("dbt and Airflow pipelines", data=data)["Acme"], [])

    def test_an_empty_library_is_safe(self):
        self.assertEqual(bl.suggest("anything at all", data={"employers": {}}), {})


class TestRevocation(unittest.TestCase):
    def setUp(self):
        # save() writes on every revoke; point it somewhere harmless. os.devnull
        # cannot be used — its dirname is "" and makedirs then fails.
        fd, self.path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        self.addCleanup(os.unlink, self.path)

    def test_revoke_marks_rather_than_deletes(self):
        """The entry is the evidence that this wording was once approved, which is
        what makes the failure legible next time someone asks how a false claim
        reached four documents."""
        data = {"employers": {"Acme": [_entry("A claim", " with detail.", "x1")]}}
        n = bl.revoke({"x1"}, "because", data=data, path=self.path)
        self.assertEqual(n, 1)
        entry = data["employers"]["Acme"][0]
        self.assertIn("revoked", entry)
        self.assertEqual(entry["revoked"]["why"], "because")
        self.assertEqual(entry["lead"], "A claim")  # still on record

    def test_revoking_twice_is_a_no_op(self):
        data = {"employers": {"Acme": [_entry("A claim", " with detail.", "x1")]}}
        bl.revoke({"x1"}, "first", data=data, path=self.path)
        self.assertEqual(bl.revoke({"x1"}, "second", data=data, path=self.path), 0)
        self.assertEqual(data["employers"]["Acme"][0]["revoked"]["why"], "first")

    def test_an_unknown_fingerprint_revokes_nothing(self):
        data = {"employers": {"Acme": [_entry("A claim", " with detail.", "x1")]}}
        self.assertEqual(bl.revoke({"nope"}, "r", data=data, path=self.path), 0)


class TestHardVersusAdvisory(unittest.TestCase):
    """Revoking on an advisory would be over-reach: "these two figures share a
    passage, check it reads right" is a prompt to look, not a verdict."""

    def test_a_note_is_advisory(self):
        self.assertFalse(bl._is_hard("NOTE: '$250K' and '$50K' share one passage"))

    def test_everything_else_is_hard(self):
        for w in (
            "FORBIDDEN PAIRING: 'grew' appears with hartford.org.headcount",
            "INTERVIEW-ONLY figure '40 to 80' is on a document",
            "WRONG EMPLOYER: '2' appears under 'Acme'",
            "NEVER-TOGETHER: '200' and '50'",
        ):
            self.assertTrue(bl._is_hard(w), w)


if __name__ == "__main__":
    unittest.main()


class TestForbiddenClaimsAreEmployerScoped(unittest.TestCase):
    """A forbidden claim is its own rule shape, not a metric.

    `never_words` hangs off a metric, so it only fires where a registered FIGURE
    is present. That works for "never say GREW beside the 25-person headcount" and
    is useless for "he never held a budget at this employer" — the false claim
    carries no number to key on, and neither does the honest version. Anchoring it
    to a fake metric was tried and silently did not fire.
    """

    def _spec(self, text, company):
        return {
            "experience": [
                {
                    "company": company,
                    "title": "Head of Data",
                    "location_dates": "City, ST | June 2022 – September 2023",
                    "bullets": [["Built the function", text]],
                }
            ]
        }

    def setUp(self):
        import metric_registry

        self.mr = metric_registry
        # The rule is supplied here rather than read from the user's registry.
        # CI scaffolds a BLANK template config, so a test leaning on real personal
        # data passes locally and fails there — which is the entire reason
        # ci_local.py exists, and it caught exactly that on this test.
        self.data = {
            "metrics": [],
            "not_a_claim": [],
            "never_together": [],
            "forbidden_claims": [
                {
                    "id": "upright.budget_ownership",
                    "employers": ["Upright"],
                    "words": ["budget", "p&l"],
                    "why": "no budget ownership at this employer",
                }
            ],
        }

    def test_the_forbidden_word_fires_for_the_named_employer(self):
        w = self.mr.warnings(
            self._spec(" owning architecture, roadmap, and budget.", "Upright"), data=self.data
        )
        self.assertTrue(any("FORBIDDEN CLAIM" in x for x in w))

    def test_the_honest_version_is_silent(self):
        w = self.mr.warnings(
            self._spec(
                " owning architecture and roadmap, and negotiating purchases"
                " directly with the CEO.",
                "Upright",
            ),
            data=self.data,
        )
        self.assertFalse(any("FORBIDDEN CLAIM" in x for x in w))

    def test_a_DIFFERENT_employer_may_carry_the_same_word(self):
        """Budget ownership is real at The Hartford. A rule that fired everywhere
        would be wrong about a true claim, and would get switched off."""
        w = self.mr.warnings(
            self._spec(
                " across three teams on a $10M+ annual budget.",
                "The Hartford Financial Services Group",
            ),
            data=self.data,
        )
        self.assertFalse(any("FORBIDDEN CLAIM" in x for x in w))

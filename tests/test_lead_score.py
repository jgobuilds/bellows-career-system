"""Tests for the geo half of the lead scorer.

These are regression tests for two bugs that shipped together and stayed hidden
because this module had no tests at all:

  1. "hybrid" sat in GEO_OK, so "Hybrid-San Francisco Office" scored as
     commutable no matter where the user lived.
  2. "remote" sat in GEO_GOOD, so "Remote - India" scored 2/2 "CT-local" —
     the exact same geo score as a job in the user's home town.

Both came from the same root cause: a work model is not a place.

Written to pass under BOTH the shipped template config (what CI scaffolds) and a
real filled-in user config, so in-range terms are derived from whatever config is
loaded rather than hard-coded.
"""

import os
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "engine"))
sys.path.insert(0, _ROOT)

import config as CFG
import lead_score

# A strong in-lane, at-level title, so geo is the only thing under test.
TITLE = "Director of Data Governance"


def _geo_reason(location):
    """Score a fixed strong title against a location; return the reasons string."""
    return lead_score.score_row(TITLE, location)[2]


def _in_range_place():
    """A real place term from whatever config is loaded (never a work model)."""
    places = lead_score._places(CFG.GEO_GOOD)
    return places[0] if places else None


class TestWorkModelIsNotAPlace(unittest.TestCase):
    def test_places_helper_strips_work_model_words(self):
        got = lead_score._places(["hybrid", "remote", "hartford", "onsite", "boston"])
        self.assertEqual(got, ["hartford", "boston"])

    def test_hybrid_alone_confers_no_geo_credit(self):
        # regression: "hybrid" in GEO_OK scored any hybrid role as commutable
        self.assertIn("off-geo", _geo_reason("Hybrid-San Francisco Office"))

    def test_compiled_place_lists_contain_no_work_model_words(self):
        for word in ("hybrid", "onsite", "remote"):
            self.assertIsNone(
                lead_score.GEO_GOOD.search(word),
                f"GEO_GOOD should not match the work-model word {word!r}",
            )
            self.assertIsNone(
                lead_score.GEO_OK.search(word),
                f"GEO_OK should not match the work-model word {word!r}",
            )


class TestExclusionBeatsRemote(unittest.TestCase):
    def test_offshore_remote_is_not_home_range(self):
        # regression: "Remote - India" used to score 2/2 as "CT-local"
        reason = _geo_reason("Remote - India")
        self.assertIn("off-geo", reason)
        self.assertNotIn("home range", reason)

    def test_plain_remote_still_scores_as_home_range(self):
        self.assertIn("remote", _geo_reason("Remote"))

    def test_offshore_remote_cannot_be_a_keep(self):
        _, bucket, _ = lead_score.score_row(TITLE, "Remote - India")
        self.assertNotEqual(bucket, "Keep")

    def test_local_beats_offshore_for_the_same_title(self):
        place = _in_range_place()
        if not place:
            self.skipTest("config defines no in-range places")
        local = lead_score.score_row(TITLE, place)[0]
        offshore = lead_score.score_row(TITLE, "Remote - India")[0]
        self.assertGreater(local, offshore)


class TestMultiLocationPostings(unittest.TestCase):
    def test_in_range_option_survives_an_excluded_sibling(self):
        # "Hartford, CT or Bangalore, India" is worth a look, but isn't a clean 2
        place = _in_range_place()
        if not place:
            self.skipTest("config defines no in-range places")
        reason = _geo_reason(f"{place} or Mumbai, India")
        self.assertIn("multi-location", reason)
        self.assertNotIn("off-geo", reason)

    def test_in_range_alone_is_home_range(self):
        place = _in_range_place()
        if not place:
            self.skipTest("config defines no in-range places")
        self.assertIn("home range", _geo_reason(place))


class TestBackwardCompatibility(unittest.TestCase):
    def test_missing_geo_exclude_is_harmless(self):
        # configs predating GEO_EXCLUDE must keep working — the regex matches nothing
        empty = CFG.terms_to_regex([])
        self.assertIsNone(empty.search("anywhere at all"))


class TestWorkAuthCarryThrough(unittest.TestCase):
    """score_file builds an explicit dict, so anything not named here is silently
    dropped. That is exactly how the work-auth columns got lost between the sweep
    and the dashboard the first time."""

    def _run(self, extra):
        import csv
        import tempfile

        row = {
            "title": "Director of Data Governance",
            "company": "Acme",
            "location": "Remote",
            "date_posted": "2026-07-01",
            "job_url": "https://example.com/1",
        }
        row.update(extra)
        with tempfile.TemporaryDirectory() as d:
            src = os.path.join(d, "in.csv")
            dst = os.path.join(d, "out.csv")
            with open(src, "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=list(row))
                w.writeheader()
                w.writerow(row)
            lead_score.score_file(src, dst, os.path.join(d, "nonexistent-pipeline.md"))
            with open(dst, encoding="utf-8") as fh:
                return list(csv.DictReader(fh))

    def test_verdict_and_evidence_survive_scoring(self):
        out = self._run(
            {
                "work_auth": "no_sponsorship",
                "work_auth_concern": "posting states it does not sponsor",
                "work_auth_evidence": "we are unable to offer visa sponsorship",
            }
        )
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["work_auth"], "no_sponsorship")
        self.assertIn("does not sponsor", out[0]["work_auth_concern"])
        self.assertIn("unable to offer", out[0]["work_auth_evidence"])

    def test_missing_columns_default_to_unstated(self):
        # rows swept before the feature existed must not blow up or imply permission
        out = self._run({})
        self.assertEqual(out[0]["work_auth"], "unstated")
        self.assertEqual(out[0]["work_auth_concern"], "")


if __name__ == "__main__":
    unittest.main()

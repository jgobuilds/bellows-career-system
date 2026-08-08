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


def _excluded_place():
    """A place the loaded config says you will not go.

    Derived, not hard-coded. Naming a real city here works against a filled-in
    config and silently fails against the template CI scaffolds, which is exactly
    how the country-token tests broke the build.
    """
    excluded = list(getattr(CFG, "GEO_EXCLUDE", []) or [])
    return excluded[0] if excluded else None


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

    def test_a_country_token_is_not_an_in_range_option(self):
        """Regression, caught on real swept data.

        "Seattle, Washington, United States" matched GEO_OK on the COUNTRY, so it
        looked like a multi-location posting and escaped the exclusion — scoring
        Keep/8 for someone who will not relocate. "Seattle, WA, US" was handled
        correctly, so the bug needed a specific spelling to appear.

        The place is derived from the loaded config: naming Seattle here passes
        against a filled-in config and fails against the template, which is how the
        first version of this test broke CI.
        """
        excluded = _excluded_place()
        if not excluded:
            self.skipTest("config defines no excluded places")
        reason = _geo_reason(f"Somewhereville, {excluded.title()}, United States")
        self.assertIn("off-geo", reason)
        self.assertNotIn("multi-location", reason)

    def test_an_excluded_city_cannot_be_a_keep(self):
        excluded = _excluded_place()
        if not excluded:
            self.skipTest("config defines no excluded places")
        for loc in (f"Somewhereville, {excluded.title()}, United States", f"{excluded.title()}"):
            _, bucket, _ = lead_score.score_row("Director of Data Governance", loc)
            self.assertNotEqual(bucket, "Keep", loc)

    def test_a_genuine_multi_location_still_qualifies(self):
        # the branch must keep working for real cases: a SPECIFIC in-range place
        # alongside an excluded one
        place, excluded = _in_range_place(), _excluded_place()
        if not place or not excluded:
            self.skipTest("config needs both an in-range and an excluded place")
        self.assertIn("multi-location", _geo_reason(f"{excluded.title()} | {place}"))

    def test_country_only_still_scores(self):
        # a US-wide posting is plausible on its own; it just isn't EVIDENCE of an
        # in-range option when an excluded city is also present
        self.assertNotIn("off-geo", _geo_reason("United States"))

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
                "work_auth_evidence": "we are unable to offer visa sponsorship",
            }
        )
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["work_auth"], "no_sponsorship")
        self.assertIn("unable to offer", out[0]["work_auth_evidence"])

    def test_missing_columns_default_to_unstated(self):
        # rows swept before the feature existed must not blow up or imply permission
        out = self._run({})
        self.assertEqual(out[0]["work_auth"], "unstated")

    def test_the_user_vs_posting_comparison_is_never_persisted(self):
        # It is derived from a setting that changes. Storing it would leave every
        # existing row stale the moment the user updates their status, and would
        # make the dashboard's live switching impossible.
        out = self._run({"work_auth": "no_sponsorship", "work_auth_evidence": "cannot sponsor"})
        self.assertNotIn("work_auth_concern", out[0])
        self.assertNotIn("work_auth_concern", lead_score.__dict__.get("_", {}))


if __name__ == "__main__":
    unittest.main()


class TestLaneAnchorRule(unittest.TestCase):
    """A lane keyword only counts when the title shows it means DATA work.

    WHY: across two sweeps, 9 of 17 postings this scorer put at 7+ scored below 6
    on a proper read, and they all failed the same way. A lane list widens over
    time — correctly, it buys recall — and widening produces BARE words.
    "governance" and "enablement" alone are the worst offenders because they are
    common outside data entirely, so a physician's "Medical Director, DI
    Underwriting Governance" and a sales job's "Revenue Enablement Director" both
    took the full lane score.

    These assert the MECHANISM rather than end-to-end totals, because the totals
    depend on which config is loaded and this repo ships two.
    """

    def test_a_bare_lane_word_in_a_non_data_title_is_not_anchored(self):
        self.assertFalse(
            lead_score.lane_is_anchored(
                "Medical Director, DI Underwriting Governance", "governance"
            )
        )
        self.assertFalse(lead_score.lane_is_anchored("Revenue Enablement Director", "enablement"))

    def test_a_self_anchored_term_carries_its_own_proof(self):
        self.assertTrue(lead_score.lane_is_anchored("Director, Data Governance", "data governance"))
        self.assertTrue(lead_score.lane_is_anchored("Head of MDM", "mdm"))

    def test_a_bare_term_is_anchored_by_a_data_word_elsewhere_in_the_title(self):
        # The bare word is fine when the title proves the subject some other way.
        self.assertTrue(
            lead_score.lane_is_anchored(
                "Quantitative Analytics Manager, Model Governance", "governance"
            )
        )

    def test_the_two_worst_real_titles_never_reach_keep_under_any_config(self):
        # Holds under both shipped configs: the template has no bare lane words to
        # match at all, and this rule demotes them where a config does.
        for title in (
            "Medical Director, DI Underwriting Governance",
            "Revenue Enablement Director",
        ):
            score, bucket, _ = lead_score.score_row(title, "Remote")
            self.assertNotEqual(bucket, "Keep", f"{title!r} scored {score} / {bucket}")


class TestScoreCeilings(unittest.TestCase):
    """Lane fit and level bound the total, so geography and domain cannot carry an
    off-lane role to Keep on "remote" plus "insurance" alone. Pure arithmetic,
    tested directly — it is the same under every config."""

    def test_a_weak_lane_caps_the_total(self):
        # raw 8 with a lane of 2 is exactly the failure shape: right words, wrong job.
        self.assertEqual(lead_score.cap_total(8, lane=2, lvl=3), 5)
        self.assertEqual(lead_score.cap_total(8, lane=1, lvl=3), 3)

    def test_a_strong_lane_is_not_capped(self):
        self.assertEqual(lead_score.cap_total(9, lane=4, lvl=3), 9)

    def test_below_target_level_caps_below_keep(self):
        self.assertEqual(lead_score.cap_total(9, lane=4, lvl=1), lead_score.BELOW_LEVEL_CAP)
        self.assertLess(lead_score.BELOW_LEVEL_CAP, 7, "a below-level role must not reach Keep")

    def test_a_title_with_no_level_word_is_kept_out_of_keep(self):
        self.assertEqual(lead_score.cap_total(9, lane=4, lvl=0), lead_score.NO_LEVEL_CAP)
        self.assertLess(lead_score.NO_LEVEL_CAP, 7)

    def test_ceilings_never_raise_a_score(self):
        for lane in range(5):
            for lvl in (0, 1, 3):
                for raw in range(11):
                    self.assertLessEqual(lead_score.cap_total(raw, lane, lvl), raw)


class SoftAnchorTest(unittest.TestCase):
    """Anchors that another discipline also uses.

    Reporting, information and insight mean data work in the right company and
    something else entirely in the wrong one. A tax role reached the top bucket on
    "reporting" plus "Director": "Senior Director, Transaction Advisory Services //
    Tax Reporting and Restructuring".

    Two things were wrong. The word one place to the left decides the meaning and
    was not being read, and a soft word was allowed to certify the very lane match
    it had caused - circular, so it could never be wrong.

    Mechanism, not totals: the totals depend on which config is loaded.
    """

    def test_the_discipline_in_front_of_the_word_disqualifies_it(self):
        for title, term in (
            ("Senior Director, Transaction Advisory Services // Tax Reporting", "reporting"),
            ("Director of Financial Reporting", "reporting"),
            ("Director, Statutory Reporting", "reporting"),
            ("VP, Regulatory Reporting", "reporting"),
        ):
            self.assertFalse(lead_score.lane_is_anchored(title.lower(), term), title)

    def test_the_discipline_after_the_word_disqualifies_it_too(self):
        # Checking only leftward let Chief Information Security Officer through.
        for title in ("Chief Information Security Officer", "Director of Information Technology"):
            self.assertFalse(lead_score.lane_is_anchored(title.lower(), "information"), title)

    def test_a_soft_word_cannot_certify_the_match_it_caused(self):
        # The circular case: "reporting" matched the lane, so letting "reporting"
        # also anchor it means the check can never fail.
        self.assertFalse(lead_score.lane_is_anchored("head of tax reporting", "reporting"))

    def test_genuine_reporting_and_insight_roles_still_anchor(self):
        for title, term in (
            ("Director of Reporting and Analytics", "reporting"),
            ("Head of Reporting", "reporting"),
            ("Director, Regulatory Reporting and Data Governance", "reporting"),
            ("VP, Insights and Analytics", "insights"),
            ("Head of Data and Insights", "insights"),
        ):
            self.assertTrue(lead_score.lane_is_anchored(title.lower(), term), title)


class AiAnchorsTheLaneTest(unittest.TestCase):
    """AI is a data anchor.

    Its absence was a silent recall hole rather than a visible bug. "AVP, AI COE
    Leader", "Senior Director - AI Operations & Enablement" and "Director, AI
    Governance & Portfolio" were all demoted to the floor for having "no data
    anchor" - and all three are exactly the roles this search exists to surface.

    A false Keep costs a minute of reading. A lead that never appears is never
    known about, so the two errors are not symmetric.
    """

    def test_ai_anchors_a_bare_lane_word(self):
        for title, term in (
            ("AVP, AI COE Leader", "ai coe"),
            ("Senior Director - AI Operations & Enablement", "enablement"),
            ("Director, AI Governance & Portfolio", "ai governance"),
        ):
            self.assertTrue(lead_score.lane_is_anchored(title.lower(), term), title)

    def test_spelled_out_artificial_intelligence_anchors_too(self):
        self.assertTrue(
            lead_score.lane_is_anchored(
                "director of artificial intelligence enablement", "enablement"
            )
        )


class RemoteFirstSignalTest(unittest.TestCase):
    """The remote-first bonus (added 2026-08-06).

    'Remote' describes one posting; 'remote-first' describes whether the policy
    survives a change of CEO. The bonus exists to separate them, and it is
    deliberately weak: gated on the role ALREADY being remote, folded into the
    raw total so the lane cap still bounds it, and never a gate of its own.

    Config-derived rather than hard-coded, because CI scaffolds the template
    config (empty company list) and a real user config has a filled-in one.
    """

    def _text_term(self):
        terms = getattr(CFG, "REMOTE_FIRST_TEXT", None) or []
        return terms[0] if terms else None

    def test_remote_first_text_adds_the_bonus(self):
        term = self._text_term()
        if not term:
            self.skipTest("no REMOTE_FIRST_TEXT configured")
        plain = lead_score.score_row(TITLE, "Remote")[0]
        first = lead_score.score_row(TITLE, f"Remote ({term})")[0]
        self.assertGreaterEqual(first, plain, "remote-first must never score BELOW plain remote")
        if plain < 10:  # only observable when the lane cap has not already bound it
            self.assertGreater(first, plain, "remote-first should beat plain remote")

    def test_onsite_at_a_remote_first_company_gets_nothing(self):
        """The bonus rewards the ROLE being remote, not the employer's brand."""
        cos = getattr(CFG, "REMOTE_FIRST_COMPANIES", None) or []
        if not cos:
            self.skipTest("no REMOTE_FIRST_COMPANIES configured")
        _, _, why = lead_score.score_row(TITLE, "San Francisco, CA", cos[0])
        self.assertNotIn("remote-first", why)

    def test_offshore_still_excluded_at_a_remote_first_company(self):
        """GEO_EXCLUDE outranks the bonus — 'remote' is only as good as its country."""
        cos = getattr(CFG, "REMOTE_FIRST_COMPANIES", None) or []
        excluded = _excluded_place()
        if not cos or not excluded:
            self.skipTest("needs both a remote-first company and an excluded place")
        _, _, why = lead_score.score_row(TITLE, f"Remote - {excluded}", cos[0])
        self.assertNotIn("remote-first", why)

    def test_company_argument_is_optional(self):
        """score_row(title, location) must keep working — ats_sweep calls it that way."""
        two = lead_score.score_row(TITLE, "Remote")
        three = lead_score.score_row(TITLE, "Remote", None)
        self.assertEqual(two, three)

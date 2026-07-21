"""Tests for the approximate career ladder.

The motivating case, restated: this repo ships two configs that put "principal" and
"lead" on OPPOSITE sides of the target line, and both are correct. A flat word list
cannot be right in general, only relative to a target. These tests pin the ordering
that makes that relativity work, plus the two parsing rules that silently destroy it
when they regress.

Config-free (imports only career_ladder). Stdlib unittest.
"""

import os
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine")
)
import career_ladder as cl


class TestLongestMatchWins(unittest.TestCase):
    """Compound titles must resolve to the compound rung, not a fragment of it."""

    def test_senior_director_is_not_senior_and_is_not_director(self):
        rung = cl.rung_of("Senior Director of Data")
        self.assertEqual(rung.key, "senior_director")
        self.assertNotEqual(rung.rank, cl.BY_KEY["senior"].rank)
        self.assertNotEqual(rung.rank, cl.BY_KEY["director"].rank)

    def test_associate_vice_president_is_avp_not_junior(self):
        self.assertEqual(cl.rung_of("Associate Vice President, Analytics").key, "avp")

    def test_senior_manager_is_not_plain_senior(self):
        self.assertEqual(cl.rung_of("Senior Manager, Analytics").key, "senior_manager")


class TestPunctuationDoesNotHideTheLevel(unittest.TestCase):
    """Regression: matching on ' term ' without normalising punctuation missed the
    most common real title formats, reporting no level at all — which silently
    zeroes the level score rather than failing loudly."""

    def test_comma_after_the_level_word(self):
        self.assertEqual(cl.rung_of("Director, Data Governance").key, "director")

    def test_comma_and_ampersand(self):
        self.assertEqual(cl.rung_of("VP, Data & Analytics").key, "vp")

    def test_abbreviation_with_a_period(self):
        self.assertEqual(cl.rung_of("Sr. Director, Platform").key, "senior_director")

    def test_hyphenated(self):
        self.assertEqual(cl.rung_of("Head-of-Data").key, "senior_director")


class TestRelativeOrdering(unittest.TestCase):
    """The whole point: the same word sits on different sides of different targets."""

    def test_principal_is_above_senior_and_below_director(self):
        self.assertGreater(cl.BY_KEY["principal"].rank, cl.BY_KEY["senior"].rank)
        self.assertLess(cl.BY_KEY["principal"].rank, cl.BY_KEY["director"].rank)

    def test_principal_flips_sides_with_the_target(self):
        self.assertIn("principal", cl.terms_below("director"))
        self.assertIn("principal", cl.terms_at_or_above("senior"))

    def test_lead_flips_sides_with_the_target(self):
        self.assertIn("lead", cl.terms_below("director"))
        self.assertIn("lead", cl.terms_at_or_above("senior"))

    def test_above_and_below_never_overlap(self):
        for level in ("senior", "manager", "director", "vp"):
            above = set(cl.terms_at_or_above(level))
            below = set(cl.terms_below(level))
            self.assertEqual(above & below, set(), f"{level}: a term is on both sides")


class TestReachCap(unittest.TestCase):
    def test_uncapped_reaches_the_top(self):
        self.assertIn("chief", cl.terms_at_or_above("senior"))

    def test_cap_limits_the_reach(self):
        capped = cl.terms_at_or_above("senior", 2)
        self.assertIn("senior", capped)
        self.assertIn("principal", capped)  # 2 rungs up
        self.assertNotIn("chief", capped)  # 8 rungs up
        self.assertNotIn("director", capped)

    def test_cap_of_zero_is_target_rung_only(self):
        self.assertEqual(
            set(cl.terms_at_or_above("director", 0)), {"director", "distinguished", "fellow"}
        )


class TestParsingNonLevels(unittest.TestCase):
    def test_titles_without_a_level_marker(self):
        # None is the correct answer, not a failure — plenty of real titles state
        # no level at all, and the scorer treats that as "no leadership level".
        for title in ("Data Analyst", "Business Analyst", "", None):
            self.assertIsNone(cl.rung_of(title), f"{title!r} should carry no level marker")

    def test_ic_titles_ending_in_manager_are_flagged_as_ambiguous(self):
        # "Product Marketing Manager" resolves to the manager rung, which is right
        # by the words and wrong by the job — those roles usually have no reports.
        # The ladder cannot resolve this from a title, so it must warn instead of
        # pretending. Johnny in userconfig.example.py is exactly this case.
        self.assertEqual(cl.rung_of("Product Marketing Manager").key, "manager")
        self.assertIn("manager", cl.caveats(["manager"]))
        self.assertIn("IC title", cl.AMBIGUOUS["manager"])

    def test_rank_of_mirrors_rung_of(self):
        self.assertEqual(cl.rank_of("Director, Data"), cl.BY_KEY["director"].rank)
        self.assertIsNone(cl.rank_of("Data Analyst"))


class TestLadderIsWellFormed(unittest.TestCase):
    def test_both_tracks_are_represented(self):
        tracks = {r.track for r in cl.LADDER}
        self.assertEqual(tracks, {"ic", "management"})

    def test_ranks_are_positive_and_ordered(self):
        ranks = [r.rank for r in cl.LADDER]
        self.assertEqual(ranks, sorted(ranks), "LADDER must be declared in rank order")
        self.assertTrue(all(r > 0 for r in ranks))

    def test_no_duplicate_terms_across_rungs(self):
        seen = {}
        for rung in cl.LADDER:
            for term in rung.terms:
                self.assertNotIn(term, seen, f"{term!r} appears on {seen.get(term)} and {rung.key}")
                seen[term] = rung.key

    def test_unknown_level_raises(self):
        with self.assertRaises(KeyError):
            cl.terms_at_or_above("supreme overlord")


class TestCaveatsTravelWithTheTerms(unittest.TestCase):
    def test_generated_director_list_warns_about_vp(self):
        notes = cl.caveats(cl.terms_at_or_above("director"))
        self.assertIn("vp", notes)
        self.assertIn("banking", notes["vp"].lower())

    def test_caveats_only_covers_terms_present(self):
        self.assertEqual(cl.caveats(["director"]).keys() - {"director"}, set())
        self.assertEqual(cl.caveats([]), {})


class TestMatchesHandCuratedLists(unittest.TestCase):
    """Sanity: the generated director list should contain what a human targeting
    Director actually wrote by hand."""

    def test_director_search_covers_the_hand_written_terms(self):
        generated = set(cl.terms_at_or_above("director"))
        for term in ("director", "head of", "vice president", "vp", "avp", "chief"):
            self.assertIn(term, generated)

    def test_director_search_demotes_the_hand_written_below_terms(self):
        below = set(cl.terms_below("director"))
        for term in ("senior manager", "sr manager", "principal", "lead"):
            self.assertIn(term, below)


if __name__ == "__main__":
    unittest.main()

"""Tests for the work-authorization classifier.

Most of these are adversarial by design. The failure mode that matters is not
"missed a posting" - it is telling someone they can apply to a role they legally
cannot hold, or burying a role they could. Both come from ordering mistakes, so the
ordering is what gets hammered here.

Config-free (imports only work_auth). Stdlib unittest.
"""

import os
import sys
import unittest
from typing import ClassVar

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine")
)
import work_auth


class TestNegationBeatsPositive(unittest.TestCase):
    """The bare word "sponsorship" carries no polarity. Negatives must win."""

    def test_unable_to_sponsor_is_not_a_sponsor(self):
        f = work_auth.classify("We are unable to offer visa sponsorship for this role.")
        self.assertEqual(f.verdict, "no_sponsorship")

    def test_does_not_provide_sponsorship(self):
        f = work_auth.classify("The company does not provide sponsorship at this time.")
        self.assertEqual(f.verdict, "no_sponsorship")

    def test_will_not_sponsor(self):
        self.assertEqual(
            work_auth.classify("We will not sponsor applicants for work visas.").verdict,
            "no_sponsorship",
        )

    def test_without_sponsorship_now_or_in_the_future(self):
        text = (
            "Applicants must be authorized to work in the U.S. without sponsorship "
            "now or in the future."
        )
        self.assertEqual(work_auth.classify(text).verdict, "no_sponsorship")

    def test_explicit_no_sponsorship(self):
        self.assertEqual(
            work_auth.classify("No visa sponsorship is offered.").verdict, "no_sponsorship"
        )

    def test_without_company_sponsorship(self):
        """Regression from a real posting (The Hartford, AVP Applied AI).

        The pattern spelled out "visa" and "employer" as the only qualifiers, so
        "without COMPANY sponsorship" — one of the commonest phrasings there is —
        classified as unstated and the flag never fired.
        """
        f = work_auth.classify("Must be eligible to work in the US without company sponsorship.")
        self.assertEqual(f.verdict, "no_sponsorship")
        self.assertIn("sponsor", f.evidence.lower())

    def test_eligible_to_work_reads_like_authorized_to_work(self):
        text = "Applicants must be legally able to work without visa sponsorship."
        self.assertEqual(work_auth.classify(text).verdict, "no_sponsorship")

    def test_without_alone_does_not_fire(self):
        # the broadened "without ... sponsorship" must still need the sponsorship word
        self.assertEqual(
            work_auth.classify("This role requires collaboration without silos.").verdict,
            "unstated",
        )

    def test_positive_sponsorship_still_reads_as_positive(self):
        self.assertEqual(
            work_auth.classify("Visa sponsorship is available for this position.").verdict,
            "sponsors",
        )

    def test_open_to_sponsorship(self):
        self.assertEqual(
            work_auth.classify("We are open to sponsoring the right candidate.").verdict,
            "sponsors",
        )

    def test_bare_no_in_an_unrelated_clause_is_not_a_refusal(self):
        # regression: a bare "no" in the negation list matched across the clause and
        # turned an employer that DOES sponsor into one that doesn't
        text = "We have no offices in Europe, and we offer visa sponsorship."
        self.assertEqual(work_auth.classify(text).verdict, "sponsors")


class TestPermanentResidentIsNotExcluded(unittest.TestCase):
    """ "Citizen OR permanent resident" must not collapse into "citizens only"."""

    def test_citizen_or_green_card_is_not_citizens_only(self):
        f = work_auth.classify("Open to U.S. Citizens or Green Card holders.")
        self.assertEqual(f.verdict, "no_sponsorship")

    def test_citizen_or_permanent_resident_is_not_citizens_only(self):
        f = work_auth.classify("Must be a U.S. citizen or lawful permanent resident.")
        self.assertEqual(f.verdict, "no_sponsorship")

    def test_us_person_includes_permanent_residents(self):
        self.assertEqual(
            work_auth.classify("Applicants must be U.S. persons.").verdict, "no_sponsorship"
        )

    def test_plain_citizen_requirement_is_citizens_only(self):
        self.assertEqual(work_auth.classify("Must be a U.S. citizen.").verdict, "citizens_only")

    def test_citizens_only_phrasing(self):
        self.assertEqual(
            work_auth.classify("This role is open to US citizens only.").verdict,
            "citizens_only",
        )

    def test_citizenship_required_phrasing(self):
        self.assertEqual(
            work_auth.classify("U.S. citizenship is required.").verdict, "citizens_only"
        )


class TestClearanceImpliesCitizenship(unittest.TestCase):
    def test_active_clearance(self):
        self.assertEqual(
            work_auth.classify("Requires an active security clearance.").verdict,
            "citizens_only",
        )

    def test_ts_sci(self):
        self.assertEqual(
            work_auth.classify("TS/SCI with polygraph required.").verdict, "citizens_only"
        )


class TestUnstatedIsTheDefault(unittest.TestCase):
    def test_ordinary_posting_says_nothing(self):
        text = (
            "We are looking for a Director of Data Governance to lead our data "
            "quality program. You will partner with business stakeholders and "
            "manage a team of five analysts."
        )
        self.assertEqual(work_auth.classify(text).verdict, "unstated")

    def test_empty_and_none(self):
        for value in ("", "   ", None):
            self.assertEqual(work_auth.classify(value).verdict, "unstated")

    def test_open_to_the_public_is_not_permission(self):
        # the USAJOBS trap: sounds inclusive, still carries a citizenship rule
        f = work_auth.classify("This job is open to the public.")
        self.assertEqual(f.verdict, "unstated")
        self.assertNotEqual(f.verdict, "sponsors")

    def test_unstated_carries_no_evidence(self):
        self.assertEqual(work_auth.classify("Nothing relevant here.").evidence, "")

    def test_is_stated_flag(self):
        self.assertFalse(work_auth.classify("nothing").is_stated)
        self.assertTrue(work_auth.classify("Must be a U.S. citizen.").is_stated)


class TestEvidenceIsAuditable(unittest.TestCase):
    def test_every_stated_verdict_quotes_the_posting(self):
        samples = [
            "We are unable to offer visa sponsorship.",
            "Must be a U.S. citizen.",
            "Visa sponsorship is available.",
            "Requires an active security clearance.",
        ]
        for text in samples:
            f = work_auth.classify(text)
            self.assertTrue(f.is_stated, text)
            self.assertTrue(f.evidence.strip(), f"no evidence captured for: {text}")

    def test_evidence_is_drawn_from_the_source_text(self):
        f = work_auth.classify("Some preamble. We are unable to sponsor visas. More text.")
        self.assertIn("sponsor", f.evidence.lower())


class TestConcernReconciliation(unittest.TestCase):
    CITIZEN: ClassVar[dict[str, object]] = {"needs_sponsorship": False, "citizenship": "citizen"}
    LPR: ClassVar[dict[str, object]] = {
        "needs_sponsorship": False,
        "citizenship": "permanent_resident",
    }
    NEEDS_SPONSOR: ClassVar[dict[str, object]] = {
        "needs_sponsorship": True,
        "citizenship": "other",
    }

    def test_feature_is_opt_in(self):
        f = work_auth.classify("Must be a U.S. citizen.")
        self.assertIsNone(work_auth.concern(f, None))
        self.assertIsNone(work_auth.concern(f, {}))

    def test_citizens_only_flags_a_permanent_resident(self):
        f = work_auth.classify("Must be a U.S. citizen.")
        self.assertIsNotNone(work_auth.concern(f, self.LPR))

    def test_citizens_only_is_silent_for_a_citizen(self):
        f = work_auth.classify("Must be a U.S. citizen.")
        self.assertIsNone(work_auth.concern(f, self.CITIZEN))

    def test_no_sponsorship_flags_someone_who_needs_it(self):
        f = work_auth.classify("We are unable to offer visa sponsorship.")
        self.assertIsNotNone(work_auth.concern(f, self.NEEDS_SPONSOR))

    def test_no_sponsorship_is_silent_for_someone_who_doesnt(self):
        f = work_auth.classify("We are unable to offer visa sponsorship.")
        self.assertIsNone(work_auth.concern(f, self.CITIZEN))

    def test_unstated_never_raises_a_concern(self):
        f = work_auth.classify("An ordinary posting.")
        for profile in (self.CITIZEN, self.LPR, self.NEEDS_SPONSOR):
            self.assertIsNone(work_auth.concern(f, profile))


class TestLabels(unittest.TestCase):
    def test_every_verdict_has_a_label(self):
        for verdict in ("citizens_only", "no_sponsorship", "sponsors", "unstated"):
            self.assertTrue(work_auth.label(verdict))


if __name__ == "__main__":
    unittest.main()


class TestUserStatus(unittest.TestCase):
    """The user's own status is a NAMED key, so the dashboard dropdown,
    userconfig.py, and concern() cannot drift apart."""

    def test_every_status_maps_back_to_its_key(self):
        for key, value in work_auth.STATUSES.items():
            self.assertEqual(work_auth.status_key(value), key)

    def test_unset_and_empty_are_unset(self):
        self.assertEqual(work_auth.status_key(None), "unset")
        self.assertEqual(work_auth.status_key({}), "unset")

    def test_hand_edited_dict_still_classifies(self):
        # someone edits userconfig.py by hand into a shape matching no preset
        odd = {"authorized_us": True, "needs_sponsorship": True, "citizenship": "citizen"}
        self.assertEqual(work_auth.status_key(odd), "needs_sponsorship")

    def test_every_status_has_a_label(self):
        self.assertEqual(set(work_auth.STATUS_LABELS), set(work_auth.STATUSES))


class TestConfigRewrite(unittest.TestCase):
    """Pure, because a botched rewrite would break the one file the whole system
    reads. Two real bugs were caught here: the round-trip stripped the inline
    comments, and the writer flipped every line in the file to CRLF."""

    SRC = (
        "NAME = 'x'\n\n"
        "WORK_AUTH = {\n"
        '    "authorized_us": True,       # legally authorized to work in the US?\n'
        '    "needs_sponsorship": False,  # will you need sponsorship now or in the future?\n'
        '    "citizenship": "citizen",    # "citizen" | "permanent_resident" | "other"\n'
        "}\n\n"
        "LANE_STRONG = ['a']\n"
    )

    def test_round_trip_is_byte_identical(self):
        out = work_auth.rewrite_config(self.SRC, "needs_sponsorship")
        out = work_auth.rewrite_config(out, "citizen")
        self.assertEqual(out, self.SRC)

    def test_inline_comments_survive(self):
        out = work_auth.rewrite_config(self.SRC, "needs_sponsorship")
        self.assertIn("# legally authorized to work in the US?", out)
        self.assertIn('# "citizen" | "permanent_resident" | "other"', out)

    def test_only_the_assignment_changes(self):
        out = work_auth.rewrite_config(self.SRC, "permanent_resident")
        self.assertTrue(out.startswith("NAME = 'x'\n\n"))
        self.assertTrue(out.endswith("LANE_STRONG = ['a']\n"))
        self.assertIn('"citizenship": "permanent_resident"', out)

    def test_none_and_back(self):
        off = work_auth.rewrite_config(self.SRC, "unset")
        self.assertIn("WORK_AUTH = None", off)
        self.assertNotIn('"citizenship"', off)
        back = work_auth.rewrite_config(off, "citizen")
        self.assertEqual(back, self.SRC)

    def test_appends_when_absent(self):
        out = work_auth.rewrite_config("NAME = 'x'\n", "citizen")
        self.assertIn("WORK_AUTH = {", out)
        self.assertTrue(out.startswith("NAME = 'x'\n"))

    def test_no_carriage_returns_introduced(self):
        self.assertNotIn("\r", work_auth.rewrite_config(self.SRC, "needs_sponsorship"))

    def test_unknown_status_raises(self):
        with self.assertRaises(ValueError):
            work_auth.rewrite_config(self.SRC, "resident alien of mars")

    def test_written_block_is_valid_python(self):
        import ast

        for status in work_auth.STATUSES:
            ast.parse(work_auth.render_config_block(status))

"""Tests for the commit-message career-detail guard.

Two of these encode bugs the first version actually had, because both were silent
false negatives — the check reported "clean" and the leak went through:

  * the trailer filter matched any "word:" prefix, which is this repo's own
    "component: summary" subject convention, so no subject line was ever scanned;
  * employer extraction required a line-ending right after the name, so a heading
    reading a "THE <COMPANY> ..." heading yielded only the stopword "THE".

A guard that fails open is worse than no guard, since it is trusted.

Fictional employers throughout. Config-free. Stdlib unittest.
"""

import os
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools")
)
import check_commit_msg as c

EMPLOYERS = ["acme", "globex", "initech"]


def flagged(msg):
    return c.findings(msg, employers=EMPLOYERS)


class BlocksLeaks(unittest.TestCase):
    def test_employer_named_in_the_body(self):
        self.assertTrue(flagged("fix: parser\n\nFound on a real posting at Globex."))

    def test_employer_named_in_the_SUBJECT_line(self):
        """The subject used to be skipped entirely: 'test: ...' looked like a trailer."""
        self.assertTrue(flagged("test: Acme bullet said the wrong thing"))

    def test_quoted_document_text_in_a_career_context(self):
        msg = 'fix: builder\n\nA resume bullet claimed "Alpha Cloud, Beta Cloud, and Gamma warehousing".'
        self.assertTrue(flagged(msg))

    def test_stack_tool_in_a_career_context(self):
        self.assertTrue(flagged("fix: a resume bullet credited Snowflake to the wrong employer"))

    def test_money_figure(self):
        self.assertTrue(flagged("docs: note the $250K licensing saving"))

    def test_scale_figure(self):
        self.assertTrue(flagged("docs: mention consolidating 4,000 reports"))


class AllowsOrdinaryCommits(unittest.TestCase):
    def test_the_generic_replacement_wording_passes(self):
        self.assertEqual(
            flagged(
                "builder: add employer/tool check\n\nDeveloper caught an "
                "incorrect bullet; additional checks added."
            ),
            [],
        )

    def test_ats_vendor_names_are_a_legitimate_code_topic(self):
        msg = (
            "ats_sweep: throttle per registrable domain\n\n"
            "Greenhouse and Workday share a domain, so hold the lock across the sleep. "
            "Raised throughput 30% and cut the longest same-ATS run from 10 to 2."
        )
        self.assertEqual(flagged(msg), [])

    def test_stack_tool_outside_a_career_context_is_fine(self):
        """'add BigQuery to the skills vocabulary' is about code, not the record."""
        self.assertEqual(flagged("ats_match: add BigQuery to the skills vocabulary"), [])

    def test_a_possessive_apostrophe_does_not_look_like_a_quote(self):
        """Treating ' as a delimiter made "this repo's own" close a quote opened
        earlier in the sentence, blocking a legitimate commit."""
        msg = (
            'fix: builder\n\nThe employer filter matched any "word:" prefix, '
            "which is this repo's own convention."
        )
        self.assertEqual(flagged(msg), [])

    def test_co_authored_by_trailer_is_not_scanned(self):
        self.assertEqual(flagged("hub: tidy\n\nCo-Authored-By: Someone Name <x@y.z>"), [])


class EmployerExtraction(unittest.TestCase):
    def test_reads_every_distinctive_word_past_a_leading_stopword(self):
        profile = (
            "### THE GLOBEX LIFE INSURANCE COMPANY OF AMERICA — Senior Analyst\n"
            "### ACME (FORMERLY INITECH)\n"
            "### THE\n"
        )
        import tempfile

        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
            fh.write(profile)
            path = fh.name
        try:
            got = c.employers_from_profile(path)
        finally:
            os.unlink(path)
        self.assertIn("globex", got)
        self.assertIn("acme", got)  # a parenthetical must not stop the match
        self.assertNotIn("the", got)  # stopword
        self.assertNotIn("life", got)  # corporate filler

    def test_missing_profile_is_not_an_error(self):
        self.assertEqual(c.employers_from_profile("/nonexistent/profile.md"), [])


if __name__ == "__main__":
    unittest.main()

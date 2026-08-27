#!/usr/bin/env python3
"""Tests for resume_coverage — the check that asks whether a resume selected the
RIGHT accomplishments, not whether the ones it has are good.

Several cases assert SILENCE. An advisory tool that breaks prints nothing, which
is indistinguishable from "all clear" and which nobody investigates — so the
negative cases matter more here than the positive ones.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine")
)

import resume_coverage


class TestTokens(unittest.TestCase):
    def test_stopwords_and_short_words_are_dropped(self):
        self.assertEqual(resume_coverage.tokens("the and of a to"), set())

    def test_plurals_fold_to_the_singular(self):
        self.assertEqual(resume_coverage.tokens("pipelines"), resume_coverage.tokens("pipeline"))

    def test_a_double_s_word_is_not_stemmed(self):
        # "access" must not become "acces"
        self.assertIn("access", resume_coverage.tokens("access controls"))

    def test_tool_names_with_punctuation_survive(self):
        got = resume_coverage.tokens("dbt / dbt Cloud, CI/CD and BigQuery")
        self.assertIn("bigquery", got)
        self.assertTrue(any(t.startswith("dbt") for t in got))

    def test_empty_input_is_safe(self):
        self.assertEqual(resume_coverage.tokens(""), set())
        self.assertEqual(resume_coverage.tokens(None), set())


class TestProfileParsing(unittest.TestCase):
    PROFILE = """# Profile

### OPTIMUM — Director

Some framing prose that is not an accomplishment and has no themes.

Accomplishments:
- Built a quality framework on dbt | Result: issues down 72% | Themes: quality, dbt
- Led a migration to BigQuery | Result: qualitative | Themes: platform, gcp `[a note]`
- A line with no themes tag at all

### UPRIGHT — Head of Data
- Consolidated reports into data products | Result: 4000 to 20 | Themes: consolidation
"""

    def setUp(self):
        fd, self.p = tempfile.mkstemp(suffix=".md")
        os.close(fd)
        open(self.p, "w", encoding="utf-8").write(self.PROFILE)
        self.addCleanup(os.unlink, self.p)

    def test_only_lines_carrying_a_themes_tag_are_accomplishments(self):
        accs = resume_coverage.parse_profile(self.p)
        self.assertEqual(len(accs), 3)
        self.assertNotIn("A line with no themes tag at all", [a["claim"] for a in accs])

    def test_prose_and_headings_are_not_accomplishments(self):
        claims = " ".join(a["claim"] for a in resume_coverage.parse_profile(self.p))
        self.assertNotIn("framing prose", claims)

    def test_the_section_heading_is_attached(self):
        accs = resume_coverage.parse_profile(self.p)
        self.assertEqual(accs[0]["section"], "OPTIMUM")
        self.assertEqual(accs[-1]["section"], "UPRIGHT")

    def test_result_and_themes_are_split_out(self):
        a = resume_coverage.parse_profile(self.p)[0]
        self.assertEqual(a["claim"], "Built a quality framework on dbt")
        self.assertEqual(a["result"], "issues down 72%")
        self.assertEqual(a["themes"], ["quality", "dbt"])

    def test_agent_note_brackets_are_stripped(self):
        a = resume_coverage.parse_profile(self.p)[1]
        self.assertNotIn("a note", a["themes"])
        self.assertNotIn("`[", a["result"])


class TestScoring(unittest.TestCase):
    def test_theme_tokens_count_double(self):
        jd = {"governance"}
        plain = resume_coverage.score({"governance"}, jd)
        tagged = resume_coverage.score({"governance"}, jd, {"governance"})
        self.assertEqual(tagged, plain * 2)

    def test_no_overlap_scores_zero(self):
        self.assertEqual(resume_coverage.score({"actuarial"}, {"kafka"}), 0)


class TestOnResumeMatching(unittest.TestCase):
    """A bullet is a REPHRASING of a profile line, never a copy, so representation
    is judged by overlap. Both directions matter: missing a real match floods the
    'left on the table' list with things already on the page, and matching too
    loosely hides a genuine gap."""

    def _acc(self, text):
        return {"tokens": resume_coverage.tokens(text)}

    def _bullets(self, *texts):
        return [{"tokens": resume_coverage.tokens(t)} for t in texts]

    def test_a_rephrasing_counts_as_represented(self):
        acc = self._acc("Consolidated 4,000 legacy reports into 20 governed data products")
        b = self._bullets(
            "Consolidated 4,000+ scattered legacy reports into 20 governed data products with one owner"
        )
        self.assertTrue(resume_coverage._on_resume(acc, b))

    def test_an_unrelated_bullet_does_not_count(self):
        acc = self._acc("Built entity resolution mastering party data across source systems")
        b = self._bullets("Automated broker compensation reporting and quarterly financial close")
        self.assertFalse(resume_coverage._on_resume(acc, b))

    def test_a_couple_of_shared_words_is_not_a_match(self):
        acc = self._acc("Established role-based access control mapped to business area and schema")
        b = self._bullets("Led a data team across three business domains")
        self.assertFalse(resume_coverage._on_resume(acc, b))

    def test_no_bullets_means_nothing_is_represented(self):
        self.assertFalse(resume_coverage._on_resume(self._acc("anything at all here"), []))


class TestSpecBullets(unittest.TestCase):
    def test_stacked_sub_roles_advisory_and_earlier_are_all_collected(self):
        spec = {
            "experience": [
                {
                    "company": "Acme",
                    "roles": [
                        {"title": "Director", "bullets": [["A", " one."]]},
                        {"title": "Engineer", "bullets": [["B", " two."]]},
                    ],
                },
                {"company": "Beta", "title": "Head", "bullets": [["C", " three."]]},
            ],
            "advisory": [{"company": "Self", "title": "Fractional", "bullets": [["D", " four."]]}],
            "earlier": [{"company": "Oldco", "bullet": "E five."}],
        }
        got = [b["text"] for b in resume_coverage.spec_bullets(spec)]
        self.assertEqual(len(got), 5)
        self.assertIn("A one.", got)
        self.assertIn("D four.", got)
        self.assertIn("E five.", got)

    def test_an_earlier_entry_with_no_bullet_is_skipped(self):
        spec = {"earlier": [{"company": "Oldco"}]}
        self.assertEqual(resume_coverage.spec_bullets(spec), [])

    def test_an_empty_spec_is_safe(self):
        self.assertEqual(resume_coverage.spec_bullets({}), [])


if __name__ == "__main__":
    unittest.main()


class TestConceptFolding(unittest.TestCase):
    """Without this, "managing and scaling teams" reads as unanswered next to
    "Led a 25-person organization" — same claim, different words. The number was
    then wrong in the direction that does damage: it invents gaps, which invites
    padding a resume to close them."""

    def test_lead_and_manage_are_the_same_claim(self):
        self.assertEqual(resume_coverage.concepts({"led"}), resume_coverage.concepts({"managing"}))

    def test_develop_and_coach_are_the_same_claim(self):
        self.assertEqual(
            resume_coverage.concepts({"developed"}), resume_coverage.concepts({"mentored"})
        )

    def test_an_unmapped_word_survives_unchanged(self):
        self.assertEqual(resume_coverage.concepts({"actuarial"}), {"actuarial"})

    def test_a_tool_name_is_NOT_folded(self):
        # exact-match is the whole game for a named technology
        self.assertEqual(resume_coverage.concepts({"bigquery"}), {"bigquery"})
        self.assertNotEqual(
            resume_coverage.concepts({"bigquery"}), resume_coverage.concepts({"snowflake"})
        )

    def test_unrelated_verbs_do_not_collide(self):
        self.assertNotEqual(
            resume_coverage.concepts({"led"}), resume_coverage.concepts({"collaborate"})
        )


class TestBestMatch(unittest.TestCase):
    def _bullets(self, *texts):
        return [{"text": t, "tokens": resume_coverage.tokens(t)} for t in texts]

    def test_it_matches_across_synonyms(self):
        req = resume_coverage.tokens("managing and scaling data engineering teams")
        b = self._bullets("Led a 25-person data engineering organization across three teams")
        best, hits = resume_coverage.best_match(req, b)
        self.assertIsNotNone(best)
        self.assertGreaterEqual(hits, 2)

    def test_an_unrelated_bullet_scores_low(self):
        req = resume_coverage.tokens("managing and scaling data engineering teams")
        b = self._bullets("Automated broker compensation reporting and quarterly close")
        _, hits = resume_coverage.best_match(req, b)
        self.assertLess(hits, 2)

    def test_no_bullets_is_safe(self):
        self.assertEqual(resume_coverage.best_match({"anything"}, []), (None, 0))

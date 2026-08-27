#!/usr/bin/env python3
"""Tests for jd_requirements — reading a posting as discrete asks.

The dispositional split carries the most weight here. Counting "care deeply about
what you do" as a requirement a resume can answer corrupts the coverage figure in
both directions at once: as a denominator it invents a gap no document could ever
close, and as a numerator it claims credit no bullet earned.
"""

import os
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine")
)

import jd_requirements as jr

POSTING = """About the role
We are looking for someone to join the team.

What You'll Do
* Lead a team of Data Engineers across multiple domains
* Champion technical excellence across our stack: BigQuery, dbt, Airflow, Kafka
* x

What We're Looking For
* Proven experience in managing and scaling Data Engineering teams
* Strong command of modern data stack technologies
* Experience with large-scale data architecture and data governance

About you
* Care deeply about what you do
* Keep up with an unrelenting pace
* Work digital-first for your daily work
* You thrive in fast-paced environments while maintaining focus on data quality
"""


class TestRequirementExtraction(unittest.TestCase):
    def setUp(self):
        self.reqs = jr.requirements(POSTING)

    def test_bulleted_asks_are_found(self):
        texts = [r["text"] for r in self.reqs]
        self.assertIn("Lead a team of Data Engineers across multiple domains", texts)

    def test_prose_is_not_a_requirement(self):
        self.assertNotIn(
            "We are looking for someone to join the team.", [r["text"] for r in self.reqs]
        )

    def test_a_fragment_is_skipped(self):
        self.assertNotIn("x", [r["text"] for r in self.reqs])

    def test_looking_for_outweighs_responsibilities(self):
        want = next(r for r in self.reqs if r["text"].startswith("Proven experience"))
        do = next(r for r in self.reqs if r["text"].startswith("Lead a team"))
        self.assertGreater(want["weight"], do["weight"])

    def test_headings_set_the_section(self):
        do = next(r for r in self.reqs if r["text"].startswith("Lead a team"))
        self.assertEqual(do["section"], "responsibilities")


class TestDispositionSplit(unittest.TestCase):
    def setUp(self):
        self.reqs = jr.requirements(POSTING)

    def kind_of(self, prefix):
        return next(r for r in self.reqs if r["text"].startswith(prefix))["kind"]

    def test_pure_temperament_is_a_disposition(self):
        self.assertEqual(self.kind_of("Care deeply"), "disposition")
        self.assertEqual(self.kind_of("Keep up with an unrelenting"), "disposition")
        self.assertEqual(self.kind_of("Work digital-first"), "disposition")

    def test_a_skill_is_demonstrable(self):
        self.assertEqual(self.kind_of("Proven experience"), "demonstrable")
        self.assertEqual(self.kind_of("Lead a team"), "demonstrable")

    def test_a_MIXED_line_stays_demonstrable(self):
        """ "You thrive in fast-paced environments while maintaining focus on data
        quality" opens on temperament and ends on a checkable skill. Discarding it
        would lose a real requirement, so the evidence half wins."""
        self.assertEqual(self.kind_of("You thrive"), "demonstrable")

    def test_an_ai_ask_opening_on_a_disposition_verb_is_demonstrable(self):
        """ "Embrace AI and LLMs to accelerate repetitive tasks" is entirely
        checkable — a tooling rollout and shipped agents evidence it. It was
        misfiled as temperament until AI terms were added to the evidence set,
        which dropped the strongest match on the posting out of the denominator."""
        reqs = jr.requirements("* Embrace AI and LLMs to accelerate repetitive tasks\n")
        self.assertEqual(reqs[0]["kind"], "demonstrable")


class TestTechnologies(unittest.TestCase):
    def test_named_tools_are_found_in_order(self):
        got = jr.technologies(POSTING)
        for t in ("bigquery", "dbt", "airflow", "kafka"):
            self.assertIn(t, got)

    def test_a_substring_is_not_a_match(self):
        # "goal" must not match the language "go"
        self.assertNotIn("go", jr.technologies("We have goals and gopher problems."))

    def test_nothing_named_is_safe(self):
        self.assertEqual(jr.technologies("A posting with no tools named at all."), [])

    def test_empty_input_is_safe(self):
        self.assertEqual(jr.technologies(""), [])
        self.assertEqual(jr.requirements(""), [])


class TestDedupe(unittest.TestCase):
    def test_a_repeated_ask_is_folded_and_weighted_up(self):
        text = (
            "What You'll Do\n"
            "* Champion data governance and dimensional modeling across pipelines\n"
            "What We're Looking For\n"
            "* Champion data governance and dimensional modeling across pipelines\n"
        )
        reqs = jr.requirements(text)
        self.assertEqual(len(reqs), 1)
        self.assertGreaterEqual(reqs[0]["weight"], 3)

    def test_distinct_asks_are_not_folded(self):
        text = (
            "What We're Looking For\n"
            "* Experience with data governance and stewardship models\n"
            "* Experience hiring and developing senior engineers\n"
        )
        self.assertEqual(len(jr.requirements(text)), 2)


if __name__ == "__main__":
    unittest.main()

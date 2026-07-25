"""Tests for the verified-fact ledger.

The design went through two rejected shapes before this one, and the tests encode
why, because the failure mode of a verification gate is NOISE, not permissiveness:

  * fingerprinting the exact wording flagged 15+ bullets per application, since a
    tailored résumé re-words nearly every line;
  * fingerprinting the fact-set PER BULLET still flagged 12-14, because tailoring
    also recombines — the same facts split and merged across different bullets.

Both would have been approved unread within a week, which is the same as having
no gate. Verification is therefore per-TOKEN: reword and recombine freely, and
surface only a fact this employer has not been verified to support.

Fictional employers throughout. Stdlib unittest.
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine")
)
import bullet_library as bl


def spec(company, bullets):
    return {"experience": [{"company": company, "bullets": bullets}]}


class TokenExtraction(unittest.TestCase):
    def test_pulls_figures_tools_and_claims(self):
        toks = bl.material_tokens("Ran the warehouse on Snowflake, hiring 4 engineers, up 30%")
        self.assertIn("tool:snowflake", toks)
        self.assertIn("claim:hiring", toks)
        self.assertTrue(any("30" in t for t in toks))

    def test_prose_alone_yields_nothing_to_verify(self):
        self.assertEqual(bl.material_tokens("Led the team and set the technical direction"), set())


class Verification(unittest.TestCase):
    def setUp(self):
        self.data = {"employers": {}}
        fd, self.path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        self.addCleanup(lambda: os.path.exists(self.path) and os.unlink(self.path))

    def approve(self, s):
        bl.approve(s, data=self.data, path=self.path)

    def test_rewording_a_verified_fact_is_silent(self):
        """The whole point: tailoring must not cost a review."""
        self.approve(
            spec("Globex", [["Ran the platform", " on Snowflake, raising throughput 30%."]])
        )
        reworded = spec(
            "Globex", [["Owned the platform", " built on Snowflake; throughput up 30%."]]
        )
        self.assertEqual(bl.unverified(reworded, self.data), [])

    def test_recombining_facts_across_bullets_is_silent(self):
        self.approve(spec("Globex", [["Ran the platform", " on Snowflake, throughput up 30%."]]))
        split = spec(
            "Globex",
            [["Ran the platform", " on Snowflake."], ["Raised throughput", " 30% year over year."]],
        )
        self.assertEqual(bl.unverified(split, self.data), [])

    def test_a_new_tool_surfaces(self):
        self.approve(spec("Globex", [["Ran the platform", " on Snowflake."]]))
        rows = bl.unverified(spec("Globex", [["Ran the platform", " on Databricks."]]), self.data)
        self.assertEqual([r["new_tokens"] for r in rows], [["tool:databricks"]])

    def test_a_new_activity_claim_surfaces(self):
        self.approve(spec("Globex", [["Led the org", " of 19 people."]]))
        rows = bl.unverified(
            spec("Globex", [["Led the org", " of 19 people, hiring into it."]]), self.data
        )
        self.assertEqual([r["new_tokens"] for r in rows], [["claim:hiring"]])

    def test_verification_is_scoped_to_the_employer(self):
        """A tool true at one employer is not evidence for another — the exact
        shape of the defect that prompted this."""
        self.approve(spec("Globex", [["Built the warehouse", " on Snowflake."]]))
        rows = bl.unverified(
            spec("Initech", [["Built the warehouse", " on Snowflake."]]), self.data
        )
        self.assertEqual([r["new_tokens"] for r in rows], [["tool:snowflake"]])

    def test_approving_twice_does_not_duplicate(self):
        s = spec("Globex", [["Ran the platform", " on Snowflake."]])
        self.approve(s)
        before = len(self.data["employers"]["Globex"])
        self.approve(s)
        self.assertEqual(len(self.data["employers"]["Globex"]), before)


if __name__ == "__main__":
    unittest.main()

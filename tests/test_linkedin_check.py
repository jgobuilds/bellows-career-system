"""LinkedIn as a gate: it must catch real drift and stay quiet about formatting.

WHY IT IS A GATE. LinkedIn does two jobs and both fail silently. It generates the inbound
- a profile that does not say what you now do is invisible to the recruiters searching
for exactly that, and nothing ever tells you about the leads you did not get. And it is
where the résumé gets verified: a recruiter with the document open will pull up the
profile, and any disagreement on employer, title or dates reads as a discrepancy rather
than a stale page.

WHY HALF THESE TESTS ARE ABOUT STAYING QUIET. The first version fired five warnings on a
real résumé and four were formatting: "The Hartford Financial Services Group" against
"The Hartford", and a title whose comma-versus-"and" form this repo mandates itself. A
gate that cries wolf gets ignored, and then the one real warning goes with it. Precision
here is not politeness, it is the difference between a control and noise.
"""

import datetime
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))

import linkedin_check as lc


def spec(company, title, dates=""):
    return {"experience": [{"company": company, "title": title, "location_dates": dates}]}


class StalenessTest(unittest.TestCase):
    def test_no_snapshot_at_all_is_the_loudest_case(self):
        _, warn = lc.staleness(None)
        self.assertIn("No LinkedIn snapshot", warn)

    def test_a_recent_snapshot_is_silent(self):
        today = datetime.date(2026, 8, 4)
        days, warn = lc.staleness({"as_of": "2026-07-19"}, today=today)
        self.assertEqual(days, 16)
        self.assertIsNone(warn)

    def test_a_stale_snapshot_warns_with_its_age(self):
        today = datetime.date(2026, 8, 4)
        days, warn = lc.staleness({"as_of": "2026-01-01"}, today=today)
        self.assertGreater(days, lc.STALE_DAYS)
        self.assertIn("days old", warn)

    def test_an_unparseable_date_is_reported_not_swallowed(self):
        _, warn = lc.staleness({"as_of": "sometime in July"})
        self.assertIn("no usable as_of", warn)


class QuietOnFormattingTest(unittest.TestCase):
    """Every case here MUST produce zero warnings."""

    def state(self, company, title, dates="April 2024 - Present"):
        return {
            "as_of": datetime.date.today().isoformat(),
            "experience": [{"company": company, "title": title, "dates": dates}],
        }

    def test_the_legal_name_matches_the_short_name(self):
        # REGRESSION: this fired three times on one résumé.
        s = self.state("The Hartford", "Director of Data Engineering", "May 2019 - June 2022")
        got = lc.compare(
            spec(
                "The Hartford Financial Services Group",
                "Director of Data Engineering",
                "Hartford, CT | May 2019 – June 2022",
            ),
            s,
        )
        self.assertEqual(got, [], got)

    def test_a_comma_is_not_a_discrepancy(self):
        # REGRESSION: the résumé style rules MANDATE the "and" form because an ATS
        # truncated the comma one. A check that cannot see past it fires on a rule the
        # system itself imposed.
        s = self.state("Optimum", "Director of Data Governance, Platform & Apps")
        got = lc.compare(
            spec(
                "Optimum",
                "Director of Data Governance and Platform & Apps",
                "Long Island City, NY | April 2024 – Present",
            ),
            s,
        )
        self.assertEqual(got, [], got)

    def test_an_en_dash_in_dates_matches_a_hyphen(self):
        s = self.state("Optimum", "Director", "April 2024 - Present")
        got = lc.compare(spec("Optimum", "Director", "NY | April 2024 – Present"), s)
        self.assertEqual(got, [], got)

    def test_a_declared_alias_is_not_drift(self):
        # The résumé says "Self-Employed" where the profile names the LLC. That is a
        # documented choice, so it is declared rather than warned about every build.
        s = self.state("Brightside Data LLC", "Fractional Head of Data", "Sept 2023 - April 2026")
        s["aliases"] = {"Self-Employed": "Brightside Data LLC"}
        got = lc.compare(
            {
                "advisory": [
                    {
                        "company": "Self-Employed",
                        "title": "Fractional Head of Data",
                        "location_dates": "CT | September 2023 – April 2026",
                    }
                ]
            },
            s,
        )
        self.assertEqual(got, [], got)


class CatchesRealDriftTest(unittest.TestCase):
    def state(self, roles):
        return {
            "as_of": datetime.date.today().isoformat(),
            "experience": [{"company": c, "title": t, "dates": d} for c, t, d in roles],
        }

    def test_a_title_that_genuinely_differs_is_flagged(self):
        s = self.state([("Acme", "Director of Data Engineering", "2019 - 2022")])
        got = lc.compare(spec("Acme", "Vice President of Data", "2019 - 2022"), s)
        self.assertEqual(len(got), 1, got)
        self.assertIn("title mismatch", got[0])

    def test_an_employer_missing_from_the_profile_is_flagged(self):
        s = self.state([("Acme", "Director", "2019 - 2022")])
        got = lc.compare(spec("Globex", "Director", "2019 - 2022"), s)
        self.assertEqual(len(got), 1, got)
        self.assertIn("not on the recorded profile", got[0])

    def test_dates_that_disagree_are_flagged(self):
        s = self.state([("Acme", "Director", "March 2020 - June 2022")])
        got = lc.compare(spec("Acme", "Director", "CT | May 2019 – June 2022"), s)
        self.assertTrue(any("dates differ" in w for w in got), got)

    def test_multi_role_company_blocks_are_all_checked(self):
        # Nested roles under one employer are the shape most likely to drift, because
        # each promotion is a separate LinkedIn entry someone forgets to add.
        s = self.state([("Acme", "Senior Engineer", "2016 - 2019")])
        got = lc.compare(
            {
                "experience": [
                    {
                        "company": "Acme",
                        "roles": [
                            {"title": "Senior Engineer", "location_dates": "2016 - 2019"},
                            {"title": "Director of Data", "location_dates": "2019 - 2022"},
                        ],
                    }
                ]
            },
            s,
        )
        self.assertTrue(any("Director of Data" in w for w in got), got)


class EndToEndTest(unittest.TestCase):
    def test_check_reads_a_file_and_returns_clean_when_it_agrees(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "profile-state.json")
            with open(p, "w", encoding="utf-8") as fh:
                json.dump(
                    {
                        "as_of": datetime.date.today().isoformat(),
                        "experience": [
                            {"company": "Acme", "title": "Director", "dates": "2019 - 2022"}
                        ],
                    },
                    fh,
                )
            self.assertEqual(lc.check(spec("Acme", "Director", "2019 - 2022"), path=p), [])

    def test_a_missing_file_still_warns_rather_than_passing_silently(self):
        with tempfile.TemporaryDirectory() as tmp:
            got = lc.check(spec("Acme", "Director"), path=os.path.join(tmp, "nope.json"))
        self.assertTrue(got)
        self.assertIn("No LinkedIn snapshot", got[0])


if __name__ == "__main__":
    unittest.main()

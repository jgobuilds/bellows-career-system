"""Tests for the doc-builder pure logic (F2/F5) — placeholder scanning and the
resume ATS-rule validator. Config-free (needs python-docx only). Stdlib unittest.
"""

import os
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine")
)
import docx_common
import resume_builder


class TestScanPlaceholders(unittest.TestCase):
    def test_finds_stubs_in_nested_content(self):
        spec = {"a": "clean", "b": ["[NEED METRIC]", {"c": "see <TODO>"}], "d": "CONFIRM this"}
        found = docx_common.scan_placeholders(spec)
        self.assertIn("[NEED METRIC]", found)
        self.assertIn("<TODO>", found)
        self.assertIn("CONFIRM", found)

    def test_clean_content_has_no_stubs(self):
        self.assertEqual(docx_common.scan_placeholders({"a": "all clean here"}), set())

    def test_structural_braces_are_not_stubs(self):
        # only string leaves are scanned — the JSON's own {}/[] are not placeholders
        self.assertEqual(docx_common.scan_placeholders({"x": [1, 2, {"y": "ok"}]}), set())


class TestResumeValidate(unittest.TestCase):
    def _spec(self, title, loc):
        return {
            "experience": [
                {"company": "Acme", "title": title, "location_dates": loc, "bullets": []}
            ]
        }

    def test_clean_spec_has_no_warnings(self):
        w = resume_builder.validate(
            self._spec("Director of Data Governance", "City, ST | 2020 - 2024")
        )
        self.assertEqual(w, [])

    def test_comma_in_title_warns_about_truncation(self):
        w = resume_builder.validate(
            self._spec("Director, Data Governance", "City, ST | 2020 - 2024")
        )
        self.assertTrue(any("truncate" in x for x in w), w)

    def test_malformed_location_line_warns(self):
        w = resume_builder.validate(self._spec("Director of Data Governance", "Remote"))
        self.assertTrue(any("location/date" in x for x in w), w)

    def test_leftover_placeholder_warns(self):
        spec = self._spec("Director of Data Governance", "City, ST | 2020 - 2024")
        spec["summary"] = "Led [NEED METRIC] teams."
        w = resume_builder.validate(spec)
        self.assertTrue(any("placeholder" in x for x in w), w)


class TestSectionOrderByLevel(unittest.TestCase):
    def test_executive_puts_experience_before_tools(self):
        # the record is the pitch at Director/VP; the tool list supports it
        self.assertEqual(
            resume_builder.SECTION_ORDERS["executive"],
            ("competencies", "experience", "skills"),
        )

    def test_ic_leads_with_tools(self):
        # at IC level the exact-tool match IS the screen
        self.assertEqual(resume_builder.SECTION_ORDERS["ic"][0], "skills")

    def test_competency_grid_stays_above_experience_at_every_level(self):
        # the compact keyword grid is ATS-indexed and orients a human in ~10s
        for level, order in resume_builder.SECTION_ORDERS.items():
            self.assertLess(
                order.index("competencies"),
                order.index("experience"),
                f"{level}: competencies must precede experience",
            )

    def test_default_level_is_executive(self):
        self.assertEqual(resume_builder.DEFAULT_LEVEL, "executive")
        self.assertIn(resume_builder.DEFAULT_LEVEL, resume_builder.SECTION_ORDERS)

    def test_unknown_level_warns(self):
        spec = {
            "level": "principal",  # not a valid key
            "experience": [
                {
                    "company": "Acme",
                    "title": "Director of Data",
                    "location_dates": "City, ST | 2020 - 2024",
                    "bullets": [],
                }
            ],
        }
        self.assertTrue(any("unknown level" in w for w in resume_builder.validate(spec)))

    def test_valid_level_is_silent(self):
        spec = {
            "level": "executive",
            "experience": [
                {
                    "company": "Acme",
                    "title": "Director of Data",
                    "location_dates": "City, ST | 2020 - 2024",
                    "bullets": [],
                }
            ],
        }
        self.assertEqual([w for w in resume_builder.validate(spec) if "level" in w], [])


class TestReverseChronology(unittest.TestCase):
    def _job(self, company, dates):
        return {
            "company": company,
            "title": "Director of Data",
            "location_dates": dates,
            "bullets": [],
        }

    def test_correct_order_is_clean(self):
        spec = {
            "experience": [
                self._job("Optimum", "City, ST | April 2024 – Present"),
                self._job("Consulting", "City, ST | September 2023 – April 2026"),
                self._job("Upright", "City, ST | June 2022 – September 2023"),
                self._job("Hartford", "City, ST | May 2019 – June 2022"),
            ]
        }
        self.assertEqual([w for w in resume_builder.validate(spec) if "chronological" in w], [])

    def test_out_of_order_entry_warns(self):
        # Hartford (2022) placed above Consulting (2026) — the exact bug we hit
        spec = {
            "experience": [
                self._job("Optimum", "City, ST | April 2024 – Present"),
                self._job("Hartford", "City, ST | May 2019 – June 2022"),
                self._job("Consulting", "City, ST | September 2023 – April 2026"),
            ]
        }
        w = [x for x in resume_builder.validate(spec) if "reverse-chronological" in x]
        self.assertTrue(w, "expected an out-of-order warning")
        self.assertIn("Consulting", w[0])

    def test_present_sorts_as_most_recent(self):
        # a 'Present' role listed AFTER an ended one is out of order
        spec = {
            "experience": [
                self._job("Old", "City, ST | May 2019 – June 2022"),
                self._job("Current", "City, ST | April 2024 – Present"),
            ]
        }
        self.assertTrue(any("reverse-chronological" in x for x in resume_builder.validate(spec)))

    def test_stacked_subroles_must_descend(self):
        spec = {
            "experience": [
                {
                    "company": "BigCo",
                    "roles": [
                        {
                            "title": "Analyst",
                            "location_dates": "City, ST | 2016 – 2019",
                            "bullets": [],
                        },
                        {
                            "title": "Director",
                            "location_dates": "City, ST | 2019 – 2022",
                            "bullets": [],
                        },
                    ],
                }
            ]
        }
        self.assertTrue(any("stacked roles" in x for x in resume_builder.validate(spec)))

    def test_end_key_parses_formats(self):
        self.assertEqual(resume_builder._end_key("City, ST | May 2019 – June 2022"), (2022, 6))
        self.assertEqual(resume_builder._end_key("City, ST | 2024 – Present"), (9999, 99))
        self.assertEqual(resume_builder._end_key("City, ST | 2020 - 2024"), (2024, 0))


if __name__ == "__main__":
    unittest.main()

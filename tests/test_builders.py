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


if __name__ == "__main__":
    unittest.main()

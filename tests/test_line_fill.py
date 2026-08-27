#!/usr/bin/env python3
"""Tests for line_fill — measuring which bullets waste a line.

The case that matters most asserts it REFUSES TO GUESS. Without the real font
metrics this module returns nothing rather than falling back to an average
character width, because a fabricated measurement presented as a measurement is
the failure it exists to prevent: "trim this by two words" is useless advice if
the number underneath it was invented.
"""

import os
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine")
)

import line_fill

HAVE_FONTS = line_fill._fonts() is not None


def _spec(lead, rest):
    return {
        "experience": [
            {
                "company": "Acme",
                "title": "Director",
                "location_dates": "City, ST | May 2019 – Present",
                "bullets": [[lead, rest]],
            }
        ]
    }


class TestRefusesToGuess(unittest.TestCase):
    def test_analyse_returns_nothing_without_real_metrics(self):
        real = line_fill._fonts
        line_fill._fonts = lambda: None
        self.addCleanup(setattr, line_fill, "_fonts", real)
        self.assertEqual(line_fill.analyse(_spec("A", " b."), 30, 25), [])


@unittest.skipUnless(HAVE_FONTS, "Calibri metrics unavailable on this machine")
class TestWrapping(unittest.TestCase):
    def setUp(self):
        self.fonts = line_fill._fonts()
        self.usable = line_fill.PAGE_USABLE_IN - line_fill.BULLET_INDENT_IN

    def test_a_short_bullet_is_one_line(self):
        self.assertEqual(len(line_fill.wrap("Led a team", " of six.", self.fonts, self.usable)), 1)

    def test_a_long_bullet_wraps(self):
        widths = line_fill.wrap(
            "Led a team", " of six. " + ("word " * 120), self.fonts, self.usable
        )
        self.assertGreater(len(widths), 1)

    def test_no_line_exceeds_the_usable_width(self):
        widths = line_fill.wrap(
            "Delivered a platform transformation",
            " " + ("engineering " * 60),
            self.fonts,
            self.usable,
        )
        for w in widths:
            self.assertLessEqual(round(w, 3), round(self.usable, 3))

    def test_bold_is_measured_wider_than_regular(self):
        """The lead-in renders bold, and bold Calibri is meaningfully wider —
        enough to move a borderline line on its own. Measuring it in the regular
        face would under-count exactly the run that starts every bullet."""
        s = "Delivered a cloud platform transformation"
        self.assertGreater(
            line_fill.width_in(s, self.fonts, bold=True),
            line_fill.width_in(s, self.fonts, bold=False),
        )

    def test_character_shape_matters_not_just_count(self):
        """The reason a character-count approximation was refused: same length,
        very different widths."""
        wide = line_fill.width_in("WWWWWWWWWW", self.fonts)
        thin = line_fill.width_in("iiiiiiiiii", self.fonts)
        self.assertGreater(wide, thin * 2)


@unittest.skipUnless(HAVE_FONTS, "Calibri metrics unavailable on this machine")
class TestClassification(unittest.TestCase):
    def test_a_single_line_bullet_is_never_flagged(self):
        # It has no orphan and no measurable tail — nothing to advise.
        self.assertEqual(line_fill.analyse(_spec("Led a team", " of six."), 30, 25), [])

    def test_a_short_tail_after_a_full_line_is_an_ORPHAN(self):
        """Constructed rather than guessed at.

        The first version of this test asserted `any(ORPHAN) or rows == []`, which
        is an escape hatch, not an assertion — it would have passed on a module
        that classified nothing at all. The case is now BUILT: pack words until
        the line is nearly full, then add one short word so the tail is tiny.
        """
        fonts = line_fill._fonts()
        usable = line_fill.PAGE_USABLE_IN - line_fill.BULLET_INDENT_IN
        words, rest = [], ""
        while line_fill.width_in(rest + " engineering", fonts) < usable * 0.95:
            words.append("engineering")
            rest = " " + " ".join(words)
        rest += " tail"
        rows = line_fill.analyse(_spec("Led", rest), 30, 25)
        self.assertTrue(rows, "a wrapped bullet with a tiny tail should be flagged")
        self.assertEqual(rows[0]["kind"], "ORPHAN")
        self.assertLessEqual(rows[0]["fill"], 0.30)

    def test_every_flagged_row_carries_its_measurements(self):
        rows = line_fill.analyse(_spec("Led", " " + ("engineering " * 20)), 30, 25)
        for r in rows:
            self.assertIn(r["kind"], ("ORPHAN", "ROOM"))
            self.assertGreaterEqual(r["lines"], 2)
            self.assertGreater(r["spare_in"], 0)

    def test_thresholds_are_honoured(self):
        # Nothing can be an orphan at 0%, and everything multi-line has room at 0%.
        spec = _spec("Led", " " + ("engineering " * 20))
        self.assertEqual([r for r in line_fill.analyse(spec, 0, 100) if r["kind"] == "ORPHAN"], [])


if __name__ == "__main__":
    unittest.main()

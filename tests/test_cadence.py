"""Tests for posting-cadence inference.

The design claim under test is that cadence needs NO sweep history: every fetcher
already pulls a company's whole open board with real dates, so one request is a
time series. These tests assert that a single board is enough — and, just as
importantly, that a board which cannot support a claim gets refused rather than
guessed at.

The refusals matter more than the successes here. A confidently wrong "posts on
Mondays" would send someone sweeping on the wrong day forever and look right
because it never contradicts itself.

Config-free. Stdlib unittest.
"""

import datetime
import os
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine")
)
import cadence

TODAY = datetime.date(2026, 7, 22)


def board(dates, start=0):
    """What a fetcher returns before the lane filter runs."""
    return [
        {"date_posted": d, "job_url": f"u{start + i}", "title": "t", "location": "l"}
        for i, d in enumerate(dates)
    ]


def every(days, n, end=TODAY):
    return [(end - datetime.timedelta(days=days * i)).isoformat() for i in range(n)]


class TestSingleSweepIsEnough(unittest.TestCase):
    def test_weekly_board_is_read_from_one_fetch(self):
        c = cadence.analyse("gh:weekly", "greenhouse", board(every(7, 12)), TODAY)
        self.assertEqual(c.median_gap_days, 7.0)
        self.assertEqual(c.confidence, "high")
        self.assertIsNotNone(c.next_expected)

    def test_weekday_concentration_is_named(self):
        mondays = [
            (datetime.date(2026, 4, 6) + datetime.timedelta(days=7 * i)).isoformat()
            for i in range(12)
        ]
        c = cadence.analyse("gh:mon", "greenhouse", board(mondays), TODAY)
        self.assertIsNotNone(c.weekday_bias)
        self.assertIn("Monday", c.weekday_bias)

    def test_day_of_month_concentration_is_named_with_a_real_ordinal(self):
        firsts = [datetime.date(2026, m, 1).isoformat() for m in (3, 4, 5, 6, 7)]
        c = cadence.analyse("lv:first", "lever", board(firsts), TODAY)
        self.assertIsNotNone(c.monthday_bias)
        self.assertIn("1st", c.monthday_bias)  # not "1th"

    def test_ordinals(self):
        got = [cadence._ordinal(n) for n in (1, 2, 3, 4, 11, 12, 13, 21, 22, 23, 31)]
        self.assertEqual(
            got,
            ["1st", "2nd", "3rd", "4th", "11th", "12th", "13th", "21st", "22nd", "23rd", "31st"],
        )


class TestItRefusesToGuess(unittest.TestCase):
    """A wrong rhythm is worse than no rhythm — it is self-consistent and invisible."""

    def test_sparse_board_makes_no_claim(self):
        c = cadence.analyse("ab:sparse", "ashby", board(["2026-07-01", "2026-06-02"]), TODAY)
        self.assertIsNone(c.median_gap_days)
        self.assertEqual(c.confidence, "none")
        self.assertTrue(c.notes)

    def test_undated_board_makes_no_claim(self):
        rows = [{"title": "t", "location": "l", "job_url": "u1"}]
        c = cadence.analyse("gh:undated", "greenhouse", rows, TODAY)
        self.assertEqual(c.dated, 0)
        self.assertEqual(c.confidence, "none")

    def test_scattered_dates_get_no_weekday_claim(self):
        # one of each weekday: no concentration to report
        spread = [(TODAY - datetime.timedelta(days=i)).isoformat() for i in range(14)]
        c = cadence.analyse("gh:spread", "greenhouse", board(spread), TODAY)
        self.assertIsNone(c.weekday_bias)

    def test_ancient_postings_do_not_count_as_recent(self):
        old = [(TODAY - datetime.timedelta(days=400 + 7 * i)).isoformat() for i in range(10)]
        c = cadence.analyse("gh:old", "greenhouse", board(old), TODAY)
        self.assertEqual(c.confidence, "none")


class TestWorkdayApproximation(unittest.TestCase):
    """Workday's list endpoint gives relative text only, so its dates are derived
    and saturate at '30+ days'. Those must not be treated as real gaps."""

    def test_relative_ages_become_dates_and_are_flagged(self):
        rows = [
            {"age_days": a, "job_url": f"w{a}", "title": "t", "location": "l"}
            for a in (1, 5, 9, 13, 17)
        ]
        c = cadence.analyse("wd:acme", "workday", rows, TODAY)
        self.assertEqual(c.quality, "approx")
        self.assertEqual(c.median_gap_days, 4.0)
        self.assertTrue(any("approximate" in n for n in c.notes))

    def test_saturated_ages_are_discarded_not_stacked(self):
        # ten postings all reported as "30+ days" are not ten postings on one day
        rows = [
            {"age_days": 30, "job_url": f"w{i}", "title": "t", "location": "l"} for i in range(10)
        ]
        c = cadence.analyse("wd:vague", "workday", rows, TODAY)
        self.assertEqual(c.dated, 0)
        self.assertIsNone(c.median_gap_days)


class TestRecordingAndArrivals(unittest.TestCase):
    def test_observe_is_compact_and_pure(self):
        obs = cadence.observe("greenhouse", board(every(7, 5)))
        self.assertEqual(obs["open_count"], 5)
        self.assertEqual(len(obs["ids"]), 5)
        self.assertNotIn("rows", obs)

    def test_first_sweep_records_no_arrivals(self):
        # everything is "new" on sweep one; counting it would invent a spike
        data = {}
        fresh = cadence.record(data, "gh:a", cadence.observe("greenhouse", board(every(7, 5))))
        self.assertEqual(len(fresh), 5)
        self.assertEqual(data["companies"]["gh:a"].get("arrivals", []), [])

    def test_second_sweep_records_only_genuinely_new_postings(self):
        data = {}
        first = board(every(7, 5))
        cadence.record(data, "gh:a", cadence.observe("greenhouse", first))
        second = first + board(["2026-07-22"], start=99)
        cadence.record(data, "gh:a", cadence.observe("greenhouse", second))
        self.assertEqual(len(data["companies"]["gh:a"]["arrivals"]), 1)

    def test_closed_postings_are_dropped_so_the_file_cannot_grow_forever(self):
        data = {}
        cadence.record(data, "gh:a", cadence.observe("greenhouse", board(every(7, 10))))
        cadence.record(data, "gh:a", cadence.observe("greenhouse", board(every(7, 3))))
        self.assertEqual(len(data["companies"]["gh:a"]["seen_ids"]), 3)

    def test_round_trip_through_storage_preserves_the_analysis(self):
        data = {}
        rows = board(every(7, 12))
        cadence.record(data, "gh:a", cadence.observe("greenhouse", rows))
        live = cadence.analyse("gh:a", "greenhouse", rows, TODAY)
        stored = cadence.from_entry("gh:a", data["companies"]["gh:a"], TODAY)
        self.assertEqual(stored.median_gap_days, live.median_gap_days)
        self.assertEqual(stored.confidence, live.confidence)


class TestRecommendation(unittest.TestCase):
    def test_no_readable_board_falls_back_to_weekly(self):
        rec = cadence.recommend([], TODAY)
        self.assertEqual(rec["days"], 7)
        self.assertIn("default", rec["basis"])

    def test_interval_tracks_the_faster_boards(self):
        fast = cadence.analyse("a", "greenhouse", board(every(3, 12)), TODAY)
        slow = cadence.analyse("b", "greenhouse", board(every(30, 12)), TODAY)
        rec = cadence.recommend([fast, slow], TODAY)
        self.assertLessEqual(
            rec["days"], 7, "sweeping at the slow board's pace misses the fast one"
        )

    def test_interval_is_bounded(self):
        crawl = cadence.analyse("c", "greenhouse", board(every(90, 12)), TODAY)
        self.assertLessEqual(cadence.recommend([crawl], TODAY)["days"], 21)
        blitz = cadence.analyse("d", "greenhouse", board(every(1, 12)), TODAY)
        self.assertGreaterEqual(cadence.recommend([blitz], TODAY)["days"], 2)


if __name__ == "__main__":
    unittest.main()

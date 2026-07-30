"""Tests for the Hub's sweep-freshness read-out (server.sweep_cadence).

The claim under test is the one the UI makes: "you last swept N days ago, and the
next sweep is worth running on DATE." cadence.recommend() only answers how many
days should elapse BETWEEN sweeps; anchoring that interval to the last sweep
rather than to today is this function's whole job, and getting it wrong would
show a permanently-not-due chip no matter how stale the data got.

Config-free apart from server's own import chain. Stdlib unittest.
"""

import datetime
import os
import sys
import unittest
from typing import ClassVar

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine")
)
import cadence
import server


def _board(last_swept: str, dates: list[str], ats: str = "greenhouse") -> dict:
    return {
        "ats": ats,
        "last_swept": last_swept + "T09:00:00+00:00",
        "open_count": len(dates),
        "posting_dates": dates,
        "date_quality": "exact",
    }


# A board posting every ~3 days: enough dated postings to carry a rhythm.
STEADY = [f"2026-07-{d:02d}" for d in (1, 4, 7, 10, 13, 16, 19, 22)]


class SweepCadenceTest(unittest.TestCase):
    def setUp(self):
        self._real_load = cadence.load
        self.addCleanup(lambda: setattr(cadence, "load", self._real_load))

    def _with(self, companies):
        cadence.load = lambda _path: {"companies": companies}

    def test_no_history_reports_never_swept(self):
        self._with({})
        out = server.sweep_cadence(datetime.date(2026, 7, 24))
        self.assertFalse(out["swept"])
        self.assertIn("reason", out)

    def test_due_date_is_anchored_to_last_sweep_not_today(self):
        """The bug this guards: computing the due date from today would make the
        chip say 'not due' forever, however long ago the last sweep actually ran."""
        self._with({"greenhouse:acme": _board("2026-07-22", STEADY)})
        out = server.sweep_cadence(datetime.date(2026, 7, 24))
        self.assertEqual(out["last_swept"], "2026-07-22")
        self.assertEqual(out["days_since"], 2)
        due = datetime.date.fromisoformat(out["due_on"])
        self.assertEqual(due, datetime.date(2026, 7, 22) + datetime.timedelta(out["interval_days"]))

    def test_becomes_due_once_the_interval_has_elapsed(self):
        self._with({"greenhouse:acme": _board("2026-07-10", STEADY)})
        out = server.sweep_cadence(datetime.date(2026, 7, 24))
        self.assertTrue(out["due"])
        self.assertGreater(out["overdue_by"], 0)

    def test_not_due_immediately_after_a_sweep(self):
        self._with({"greenhouse:acme": _board("2026-07-24", STEADY)})
        out = server.sweep_cadence(datetime.date(2026, 7, 24))
        self.assertFalse(out["due"])
        self.assertLess(out["overdue_by"], 0)
        self.assertEqual(out["days_since"], 0)

    def test_last_swept_is_the_most_recent_across_boards(self):
        self._with(
            {
                "greenhouse:old": _board("2026-07-01", STEADY),
                "greenhouse:new": _board("2026-07-20", STEADY),
            }
        )
        out = server.sweep_cadence(datetime.date(2026, 7, 24))
        self.assertEqual(out["last_swept"], "2026-07-20")
        self.assertEqual(out["boards"], 2)

    def test_active_list_is_fastest_first_and_carries_a_numeric_gap(self):
        self._with(
            {
                "greenhouse:slow": _board("2026-07-22", [f"2026-0{m}-01" for m in (3, 4, 5, 6, 7)]),
                "greenhouse:fast": _board("2026-07-22", STEADY),
            }
        )
        out = server.sweep_cadence(datetime.date(2026, 7, 24))
        gaps = [a["gap"] for a in out["active"]]
        self.assertEqual(gaps, sorted(gaps))
        for a in out["active"]:
            self.assertIsInstance(a["gap"], float)

    def test_a_board_with_no_readable_rhythm_is_excluded_not_guessed(self):
        self._with({"greenhouse:thin": _board("2026-07-22", ["2026-07-01"])})
        out = server.sweep_cadence(datetime.date(2026, 7, 24))
        self.assertEqual(out["active"], [])
        self.assertEqual(out["companies_used"], 0)
        # Still reports freshness — not knowing the rhythm is not the same as
        # not knowing when you last looked.
        self.assertTrue(out["swept"])
        self.assertEqual(out["days_since"], 2)


if __name__ == "__main__":
    unittest.main()


class SweepStatusTest(unittest.TestCase):
    """The Hub's one-line verdict: what the boards want, crossed with what the
    machine will actually do. See server.sweep_status for why "a task exists" is
    not on its own enough to report the job as handled."""

    CAD: ClassVar[dict] = {
        "swept": True,
        "interval_days": 2,
        "days_since": 2,
        "overdue_by": 0,
        "due": True,
    }

    def test_never_swept_short_circuits(self):
        st = server.sweep_status({"swept": False}, {"installed": True, "days": 2})
        self.assertEqual(st["state"], "never")
        self.assertFalse(st["warn"])

    def test_due_and_unscheduled_still_says_due(self):
        st = server.sweep_status(self.CAD, {"installed": False})
        self.assertEqual(st["state"], "due")
        self.assertEqual(st["label"], "due now")
        self.assertTrue(st["warn"])

    def test_overdue_and_unscheduled_counts_the_days(self):
        cad = dict(self.CAD, overdue_by=3, days_since=5)
        self.assertEqual(server.sweep_status(cad, None)["label"], "due 3d ago")

    def test_not_due_and_unscheduled_counts_forward(self):
        cad = dict(self.CAD, due=False, overdue_by=-2, days_since=0)
        st = server.sweep_status(cad, {})
        self.assertEqual(st["state"], "upcoming")
        self.assertEqual(st["label"], "next in 2d")

    def test_due_but_scheduled_and_keeping_up_reports_scheduled(self):
        # The point of the change: do not tell someone to do what the machine will.
        st = server.sweep_status(self.CAD, {"installed": True, "days": 2, "next_run": "Sat 01 Aug"})
        self.assertEqual(st["state"], "scheduled")
        self.assertFalse(st["warn"])
        self.assertIn("Sat 01 Aug", st["label"])

    def test_a_schedule_slower_than_the_recommendation_still_warns(self):
        st = server.sweep_status(self.CAD, {"installed": True, "days": 7})
        self.assertEqual(st["state"], "slow")
        self.assertTrue(st["warn"])
        self.assertIn("slower", st["label"])

    def test_a_schedule_that_is_not_landing_warns_rather_than_reassures(self):
        # The expensive failure: a registered task that quietly never runs would be
        # reported as handled by any "installed => scheduled" rule.
        cad = dict(self.CAD, days_since=9, overdue_by=7)
        st = server.sweep_status(cad, {"installed": True, "days": 2})
        self.assertEqual(st["state"], "stale")
        self.assertTrue(st["warn"])
        self.assertIn("9d", st["label"])

    def test_one_day_of_grace_before_calling_a_schedule_stale(self):
        # Same-day timing and a sleeping machine are not faults.
        cad = dict(self.CAD, days_since=3, overdue_by=1)
        self.assertEqual(
            server.sweep_status(cad, {"installed": True, "days": 2})["state"], "scheduled"
        )

    def test_installed_without_an_interval_falls_back_to_the_due_reading(self):
        st = server.sweep_status(self.CAD, {"installed": True, "days": None})
        self.assertEqual(st["state"], "due")

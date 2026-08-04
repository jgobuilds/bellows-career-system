"""The sweep's output has to reach a human, and the carry-forward that keeps it whole.

TWO DEFECTS, ONE STORY. The sweep ran on a schedule and wrote a scored CSV that nothing
in the UI read, so the only way to learn it had found something was to ask in chat.
Meanwhile a second sweep run shortly after a first would silently replace a full result
set with a nearly empty one, because the ATS leg is a delta and the file was written
from whatever that invocation happened to fetch.

Together those meant a qualifying lead could be found, destroyed, and never seen, with
nothing anywhere looking wrong. Automation whose output nobody sees is worse than none,
because it also creates the belief that the thing is handled.
"""

import csv
import datetime
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))

import jobspy_sweep
import server


class LeadsPayloadTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.csv = os.path.join(self._tmp.name, "leads_scored.csv")

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, rows):
        cols = ["score", "bucket", "title", "company", "location", "date_posted", "why", "job_url"]
        with open(self.csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            for r in rows:
                w.writerow({c: r.get(c, "") for c in cols})

    def payload(self, jobs=None):
        with (
            mock.patch.object(server.config, "LEADS_SCORED", self.csv),
            mock.patch.object(server, "load_jobs", lambda: {"jobs": jobs or []}),
        ):
            return server.leads_payload()

    def test_a_missing_file_is_empty_rather_than_an_error(self):
        missing = os.path.join(self._tmp.name, "nope.csv")
        with mock.patch.object(server.config, "LEADS_SCORED", missing):
            out = server.leads_payload()
        self.assertEqual(out["leads"], [])
        self.assertIsNone(out["swept"])

    def test_keeps_and_watches_surface_and_drops_do_not(self):
        self.write(
            [
                {"score": "9", "bucket": "Keep", "title": "Head of Data", "company": "Acme"},
                {"score": "5", "bucket": "Watch", "title": "Director, Data", "company": "Beta"},
                {"score": "1", "bucket": "Drop", "title": "Chef", "company": "Gamma"},
            ]
        )
        out = self.payload()
        self.assertEqual([lead["company"] for lead in out["leads"]], ["Acme", "Beta"])
        self.assertEqual(out["counts"]["Drop"], 1)

    def test_rows_already_on_the_board_are_filtered_out(self):
        # A list that re-proposes decided roles teaches people to stop reading it.
        self.write([{"score": "9", "bucket": "Keep", "title": "Head of Data", "company": "Acme"}])
        jobs = [{"id": 1, "role": "Head of Data", "co": "Acme"}]
        self.assertEqual(self.payload(jobs)["leads"], [])

    def test_highest_score_first(self):
        self.write(
            [
                {"score": "4", "bucket": "Watch", "title": "A", "company": "A Co"},
                {"score": "9", "bucket": "Keep", "title": "B", "company": "B Co"},
            ]
        )
        self.assertEqual([lead["score"] for lead in self.payload()["leads"]], [9, 4])

    def test_counts_cover_every_row_including_the_hidden_ones(self):
        # The panel distinguishes "nothing new" from "nothing in lane" using these,
        # and the two mean different things to someone judging whether it still works.
        self.write(
            [
                {"score": "9", "bucket": "Keep", "title": "X", "company": "X Co"},
                {"score": "1", "bucket": "Drop", "title": "Y", "company": "Y Co"},
                {"score": "1", "bucket": "Drop", "title": "Z", "company": "Z Co"},
            ]
        )
        self.assertEqual(self.payload()["counts"], {"Keep": 1, "Watch": 0, "Drop": 2})


class CarryForwardTest(unittest.TestCase):
    """A delta re-run must not destroy what the previous run found."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self._tmp.name, "leads_raw.csv")

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, rows):
        with open(self.path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=jobspy_sweep.CSV_COLS)
            w.writeheader()
            for r in rows:
                w.writerow({c: r.get(c, "") for c in jobspy_sweep.CSV_COLS})

    @staticmethod
    def days_ago(n):
        return (datetime.date.today() - datetime.timedelta(days=n)).isoformat()

    def test_recent_rows_are_carried_forward(self):
        self.write([{"company": "Acme", "title": "Head of Data", "date_posted": self.days_ago(1)}])
        self.assertEqual(
            [r["company"] for r in jobspy_sweep.carry_forward(self.path, 30)], ["Acme"]
        )

    def test_rows_past_the_window_age_out(self):
        self.write(
            [{"company": "Stale", "title": "Head of Data", "date_posted": self.days_ago(90)}]
        )
        self.assertEqual(jobspy_sweep.carry_forward(self.path, 30), [])

    def test_an_undated_row_is_kept_rather_than_silently_dropped(self):
        # It cannot be aged out, and dropping it loses a real lead. The dedupe on the
        # write path collapses it the moment the row is fetched again.
        self.write([{"company": "NoDate", "title": "VP Data", "date_posted": ""}])
        self.assertEqual(
            [r["company"] for r in jobspy_sweep.carry_forward(self.path, 30)], ["NoDate"]
        )

    def test_an_unparseable_date_is_kept_not_discarded(self):
        self.write([{"company": "Odd", "title": "VP Data", "date_posted": "last Tuesday"}])
        self.assertEqual([r["company"] for r in jobspy_sweep.carry_forward(self.path, 30)], ["Odd"])

    def test_a_missing_previous_file_is_not_an_error(self):
        self.assertEqual(jobspy_sweep.carry_forward(os.path.join(self._tmp.name, "x.csv"), 30), [])

    def test_the_carry_window_is_bounded_regardless_of_the_look_back(self):
        # REGRESSION: this reused MAX_AGE_DAYS (60), so leads_raw stopped being
        # "recent leads" and became a rolling two-month archive that re-proposed the
        # same ageing postings every run - one sweep carried 160 rows aged 15-60 days.
        # Carry-forward only bridges the gap BETWEEN sweeps.
        self.write(
            [
                {"company": "Fresh", "title": "Head of Data", "date_posted": self.days_ago(3)},
                {"company": "Ageing", "title": "VP Data", "date_posted": self.days_ago(30)},
            ]
        )
        got = [r["company"] for r in jobspy_sweep.carry_forward(self.path, 60)]
        self.assertEqual(got, ["Fresh"], "a 60-day look-back must not widen the carry window")

    def test_a_shorter_look_back_still_wins(self):
        # The bound is a ceiling, not an override: asking for 2 days means 2 days.
        self.write([{"company": "Week", "title": "Head of Data", "date_posted": self.days_ago(7)}])
        self.assertEqual(jobspy_sweep.carry_forward(self.path, 2), [])
        self.assertEqual(
            [r["company"] for r in jobspy_sweep.carry_forward(self.path, 14)], ["Week"]
        )

    def test_the_window_is_never_less_than_a_day(self):
        # max_age_days of 0 or None must not silently discard everything.
        self.write([{"company": "Today", "title": "Head of Data", "date_posted": self.days_ago(0)}])
        for bad in (0, None):
            self.assertEqual(
                [r["company"] for r in jobspy_sweep.carry_forward(self.path, bad)],
                ["Today"],
                f"max_age_days={bad!r}",
            )


if __name__ == "__main__":
    unittest.main()

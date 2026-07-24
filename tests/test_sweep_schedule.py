"""Tests for registering the lead sweep with the OS task scheduler.

These are all pure: nothing here shells out to schtasks. What is worth testing is
the parsing and the guardrails, because those are where a wrong answer is silent.
A mis-parsed task definition reports "never scheduled" for a task that exists, and
an unbounded interval would happily register a sweep every 12 hours against the
same ATS endpoints the throttling work exists to protect.

Config-free apart from the module's own import chain. Stdlib unittest.
"""

import datetime
import os
import subprocess
import sys
import unittest

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine")
)
import sweep_schedule

TASK_XML = """<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2026-07-25T07:30:00</StartBoundary>
      <ScheduleByDay><DaysInterval>3</DaysInterval></ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Settings><Enabled>true</Enabled></Settings>
</Task>"""


class ParseTest(unittest.TestCase):
    def test_reads_interval_and_time_from_the_definition(self):
        out = sweep_schedule._parse_xml(TASK_XML)
        self.assertEqual(out["days"], 3)
        self.assertEqual(out["at"], "07:30")
        self.assertTrue(out["enabled"])

    def test_unparseable_output_yields_nothing_rather_than_a_wrong_answer(self):
        self.assertEqual(sweep_schedule._parse_xml("ERROR: task not found"), {})

    def test_a_disabled_task_is_reported_as_disabled(self):
        out = sweep_schedule._parse_xml(TASK_XML.replace(">true<", ">false<"))
        self.assertFalse(out["enabled"])


class NextOccurrenceTest(unittest.TestCase):
    """Computed rather than scraped, so it must be right on its own."""

    B = datetime.datetime(2026, 7, 24, 7, 30)

    def test_today_still_counts_when_the_time_has_not_arrived(self):
        now = datetime.datetime(2026, 7, 24, 7, 19)
        self.assertEqual(sweep_schedule.next_occurrence(self.B, 3, now), self.B)

    def test_steps_a_whole_interval_once_the_time_has_passed(self):
        now = datetime.datetime(2026, 7, 24, 11, 0)
        self.assertEqual(
            sweep_schedule.next_occurrence(self.B, 3, now), datetime.datetime(2026, 7, 27, 7, 30)
        )

    def test_a_long_dormant_task_lands_on_a_future_slot_not_a_past_one(self):
        now = datetime.datetime(2026, 7, 24, 11, 0)
        got = sweep_schedule.next_occurrence(datetime.datetime(2026, 7, 14, 7, 30), 3, now)
        self.assertGreater(got, now)
        self.assertEqual(got, datetime.datetime(2026, 7, 26, 7, 30))

    def test_daily_rolls_to_tomorrow(self):
        now = datetime.datetime(2026, 7, 24, 11, 0)
        self.assertEqual(
            sweep_schedule.next_occurrence(self.B, 1, now), datetime.datetime(2026, 7, 25, 7, 30)
        )


class ValidateTest(unittest.TestCase):
    def test_accepts_a_sane_request(self):
        self.assertEqual(sweep_schedule.validate(3, "07:30"), (3, "07:30"))

    def test_accepts_the_string_a_form_post_actually_sends(self):
        self.assertEqual(sweep_schedule.validate("7", "23:05"), (7, "23:05"))

    def test_rejects_intervals_outside_the_bounds(self):
        for bad in (0, -1, 31, 999):
            with self.assertRaises(ValueError):
                sweep_schedule.validate(bad, "07:30")

    def test_rejects_junk_intervals(self):
        for bad in (None, "soon", [3], True):
            with self.assertRaises(ValueError):
                sweep_schedule.validate(bad, "07:30")

    def test_rejects_times_that_are_not_a_24h_clock(self):
        for bad in ("7:30", "24:00", "07:60", "7.30", "", None, "0730"):
            with self.assertRaises(ValueError):
                sweep_schedule.validate(3, bad)


class CronTest(unittest.TestCase):
    def test_daily_uses_a_plain_star_not_a_step(self):
        self.assertTrue(sweep_schedule.cron_line(1, "07:30").startswith("30 7 * * *"))

    def test_multi_day_uses_a_step(self):
        self.assertTrue(sweep_schedule.cron_line(3, "07:05").startswith("5 7 */3 * *"))


ALL_TASKS_XML = """<?xml version="1.0" encoding="UTF-16"?>
<Tasks>
  <Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
    <RegistrationInfo><URI>\\BellowsLeadSweep</URI></RegistrationInfo>
    <Actions Context="Author"><Exec>
      <Command>"C:\\data\\scheduled-sweep.cmd"</Command>
    </Exec></Actions>
  </Task>
  <Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
    <RegistrationInfo><URI>\\MyOwnSweep</URI></RegistrationInfo>
    <Actions Context="Author"><Exec>
      <Command>C:\\py\\python.exe</Command>
      <Arguments>D:\\repo\\engine\\jobspy_sweep.py --out leads.csv</Arguments>
    </Exec></Actions>
  </Task>
  <Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
    <RegistrationInfo><URI>\\Unrelated\\Backup</URI></RegistrationInfo>
    <Actions Context="Author"><Exec><Command>C:\\backup\\run.exe</Command></Exec></Actions>
  </Task>
</Tasks>"""


class ConflictTest(unittest.TestCase):
    """A second task running the same sweep is the duplicate that can actually
    happen — /F already makes re-registering our own name idempotent."""

    def setUp(self):
        self._run = sweep_schedule._run
        self._win = sweep_schedule.is_windows
        sweep_schedule.is_windows = lambda: True
        self.addCleanup(lambda: setattr(sweep_schedule, "_run", self._run))
        self.addCleanup(lambda: setattr(sweep_schedule, "is_windows", self._win))

    def _stub(self, stdout, rc=0):
        sweep_schedule._run = lambda _args: subprocess.CompletedProcess([], rc, stdout, "")

    def test_finds_a_differently_named_task_running_the_same_sweep(self):
        self._stub(ALL_TASKS_XML)
        names = [c["name"] for c in sweep_schedule.find_conflicts()]
        self.assertEqual(names, ["\\MyOwnSweep"])

    def test_does_not_report_our_own_task_as_its_own_duplicate(self):
        self._stub(ALL_TASKS_XML)
        self.assertNotIn(
            "\\" + sweep_schedule.TASK_NAME, [c["name"] for c in sweep_schedule.find_conflicts()]
        )

    def test_leaves_unrelated_tasks_alone(self):
        self._stub(ALL_TASKS_XML)
        self.assertNotIn(
            "\\Unrelated\\Backup", [c["name"] for c in sweep_schedule.find_conflicts()]
        )

    def test_our_task_in_a_folder_is_flagged_because_it_would_stack(self):
        """Re-registered under a folder its URI differs, so a query by name misses
        it and it runs alongside ours. That is precisely a duplicate."""
        self._stub(ALL_TASKS_XML.replace("\\BellowsLeadSweep", "\\Bellows\\BellowsLeadSweep"))
        self.assertIn(
            "\\Bellows\\BellowsLeadSweep", [c["name"] for c in sweep_schedule.find_conflicts()]
        )

    def test_unreadable_output_reports_nothing_rather_than_a_false_alarm(self):
        self._stub("ERROR: access denied", rc=1)
        self.assertEqual(sweep_schedule.find_conflicts(), [])
        self._stub("not xml at all")
        self.assertEqual(sweep_schedule.find_conflicts(), [])


class UnsupportedTest(unittest.TestCase):
    def setUp(self):
        self._real = sweep_schedule.is_windows
        sweep_schedule.is_windows = lambda: False
        self.addCleanup(lambda: setattr(sweep_schedule, "is_windows", self._real))

    def test_offers_the_cron_equivalent_instead_of_just_refusing(self):
        state = sweep_schedule.describe()
        self.assertFalse(state["supported"])
        self.assertFalse(state["installed"])
        self.assertIn("cron", state)
        self.assertIn("jobspy_sweep.py", state["cron"])

    def test_install_refuses_rather_than_pretending_it_worked(self):
        with self.assertRaises(RuntimeError):
            sweep_schedule.install(3, "07:30")


if __name__ == "__main__":
    unittest.main()

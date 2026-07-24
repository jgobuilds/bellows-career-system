#!/usr/bin/env python3
"""sweep_schedule.py — register the lead sweep with the OS task scheduler.

WHY THE OS AND NOT A TIMER IN THE APP:
  The whole point of a scheduled sweep is that it runs when the Hub is closed. An
  in-process scheduler (APScheduler and friends) only fires while something of ours
  is alive, which is exactly when you did not need it. Windows Task Scheduler already
  solves this, ships with the OS, survives reboots, and the user can inspect and
  cancel it without us. So we drive `schtasks.exe` rather than reimplement it.

WHY A .cmd WRAPPER:
  schtasks' /TR quoting is famously fragile once paths contain spaces (and this repo
  lives under a path that does). Writing a tiny batch file and pointing the task at
  it sidesteps quoting entirely, and has the side benefit that the user can open the
  file and see exactly what the scheduled run will do.

SAFETY:
  Creates a normal user-scope task. No elevation, no SYSTEM account, no stored
  password. It runs the same local sweep the "Run sweep now" button runs, and like
  that button it never applies to anything.
"""

import os
import platform
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

import _paths  # noqa: F401  (side-effect: adds repo root to sys.path for `import config`)
import config

TASK_NAME = "BellowsLeadSweep"
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
WRAPPER = os.path.join(config.DATA_DIR, "scheduled-sweep.cmd")

# Bounds on the interval. A sub-daily sweep hammers the same ATS endpoints for no
# gain (postings do not appear that fast), and beyond a month the leads are stale
# enough that the feature is not doing its job.
MIN_DAYS, MAX_DAYS = 1, 30
_TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def is_windows() -> bool:
    return platform.system() == "Windows"


def _schtasks() -> str | None:
    return shutil.which("schtasks")


def supported() -> tuple[bool, str]:
    """Can we actually schedule on this machine, and if not, why not."""
    if not is_windows():
        return False, (
            "Automatic scheduling is Windows-only for now. On macOS or Linux, add a cron "
            "entry instead - the command is shown below."
        )
    if not _schtasks():
        return False, "schtasks.exe was not found on PATH, so the task scheduler can't be driven."
    return True, ""


def _python() -> str:
    """Prefer pythonw so a scheduled run does not flash a console window."""
    pyw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    return pyw if os.path.exists(pyw) else sys.executable


def sweep_command() -> list[str]:
    """The same sweep the Hub button runs. Kept in one place deliberately."""
    return [_python(), os.path.join(HERE, "jobspy_sweep.py"), "--out", config.LEADS_RAW]


def cron_line(days: int, at: str) -> str:
    """The equivalent crontab entry, for the platforms we can't register on."""
    hh, mm = at.split(":")
    cmd = " ".join(f'"{p}"' if " " in p else p for p in sweep_command())
    when = f"{int(mm)} {int(hh)} * * *" if days == 1 else f"{int(mm)} {int(hh)} */{days} * *"
    return f"{when} cd {ROOT} && {cmd}"


def _write_wrapper() -> str:
    os.makedirs(os.path.dirname(WRAPPER), exist_ok=True)
    cmd = " ".join(f'"{p}"' for p in sweep_command())
    body = (
        "@echo off\r\n"
        "rem Written by Bellows (engine/sweep_schedule.py). Safe to delete once the\r\n"
        "rem scheduled sweep is turned off in the Hub.\r\n"
        f'cd /d "{ROOT}"\r\n'
        f"{cmd}\r\n"
    )
    with open(WRAPPER, "w", encoding="utf-8", newline="") as fh:
        fh.write(body)
    return WRAPPER


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, timeout=25)


def _parse_xml(xml_text: str) -> dict:
    """Read interval + start time from the task definition.

    Deliberately parsed from XML rather than `/FO LIST`: the list output is
    localized, so on a non-English Windows the field labels do not match and a
    regex over them silently reports "never scheduled" for a task that exists.
    """
    out: dict = {}
    try:
        # Not untrusted input: this is schtasks' own output for a task we created,
        # read over a pipe from the local OS. No network, no user-supplied document.
        root = ET.fromstring(xml_text.lstrip("﻿"))  # noqa: S314
    except ET.ParseError:
        return out
    ns = {"t": "http://schemas.microsoft.com/windows/2004/02/mit/task"}
    start = root.find(".//t:CalendarTrigger/t:StartBoundary", ns)
    if start is not None and start.text:
        try:
            boundary = datetime.fromisoformat(start.text)
        except ValueError:
            boundary = None
        if boundary:
            out["at"] = boundary.strftime("%H:%M")
            out["start_boundary"] = boundary.isoformat()
    every = root.find(".//t:ScheduleByDay/t:DaysInterval", ns)
    if every is not None and every.text and every.text.isdigit():
        out["days"] = int(every.text)
    enabled = root.find(".//t:Settings/t:Enabled", ns)
    if enabled is not None and enabled.text:
        out["enabled"] = enabled.text.strip().lower() != "false"
    return out


def _local(tag: str) -> str:
    """Element name without its namespace. Every <Task> in the combined dump
    redeclares the Microsoft namespace, so a plain find() by name misses."""
    return tag.rsplit("}", 1)[-1]


def _markers() -> tuple[str, ...]:
    """Strings that identify a task as 'this is a Bellows sweep'."""
    return ("jobspy_sweep", "ats_sweep", os.path.basename(WRAPPER).lower())


def find_conflicts() -> list[dict]:
    """Other scheduled tasks that also run a Bellows sweep.

    /F already makes OUR task idempotent - creating it twice replaces it rather
    than stacking - so the duplicate that can actually bite is a SECOND task under
    a different name: one the user made by hand, one left by an older version, or
    ours re-registered inside a Task Scheduler folder (which changes its URI and
    makes it invisible to a query by name). Two tasks means two sweeps hitting the
    same ATS endpoints, which is exactly what the throttling work exists to avoid.
    """
    ok, _why = supported()
    if not ok:
        return []
    proc = _run([_schtasks() or "schtasks", "/Query", "/XML", "ONE"])
    if proc.returncode != 0 or not proc.stdout.strip():
        return []
    try:
        root = ET.fromstring(proc.stdout.strip().lstrip("﻿"))  # noqa: S314  (local OS output)
    except ET.ParseError:
        return []

    marks, out = _markers(), []
    for task in root.iter():
        if _local(task.tag) != "Task":
            continue
        uri = ""
        parts = []
        for el in task.iter():
            name = _local(el.tag)
            if name == "URI" and el.text:
                uri = el.text.strip()
            elif name in ("Command", "Arguments") and el.text:
                parts.append(el.text.strip())
        blob = " ".join(parts).lower()
        if not any(m in blob for m in marks):
            continue
        if uri.lstrip("\\").lower() == TASK_NAME.lower():
            continue  # our own task, found where we expect it
        out.append({"name": uri or "(unnamed task)", "command": " ".join(parts)})
    return out


def next_occurrence(boundary: datetime, days: int, now: datetime | None = None) -> datetime:
    """The next time this task will actually fire.

    Computed rather than scraped from `schtasks /FO LIST`, for two reasons. Right
    after creation schtasks reports the start boundary itself even when that moment
    has already passed - schedule at 11:00 for 07:30 and it claims a next run of
    07:30 today, which reads as "about to run" when the truth is three days out
    (a past start is skipped: StartWhenAvailable is off). And the list output is
    localized, so the label regex silently fails on a non-English Windows.
    """
    now = now or datetime.now()
    if boundary > now:
        return boundary
    # Whole intervals elapsed, then step to the next one.
    return boundary + timedelta(days=((now - boundary).days // days + 1) * days)


def describe() -> dict:
    """Current state of the scheduled sweep, for the Hub to render."""
    ok, why = supported()
    state: dict = {
        "supported": ok,
        "reason": why,
        "task_name": TASK_NAME,
        "installed": False,
        "min_days": MIN_DAYS,
        "max_days": MAX_DAYS,
        "command": " ".join(sweep_command()),
    }
    if not ok:
        # Nothing to register, so hand over the equivalent the user CAN run.
        state["cron"] = cron_line(7, "07:30")
        return state
    # Scanned whether or not ours is registered: a stray duplicate is worth showing
    # BEFORE the user adds a second one, not only after.
    state["conflicts"] = find_conflicts()
    proc = _run([_schtasks() or "schtasks", "/Query", "/TN", TASK_NAME, "/XML", "ONE"])
    if proc.returncode != 0:
        return state  # not registered — the normal "off" case, not an error
    state["installed"] = True
    state.update(_parse_xml(proc.stdout))
    boundary, days = state.get("start_boundary"), state.get("days")
    if boundary and days:
        nxt = next_occurrence(datetime.fromisoformat(boundary), int(days))
        state["next_run"] = nxt.strftime("%a %d %b, %H:%M")
    state["wrapper"] = WRAPPER if os.path.exists(WRAPPER) else None
    return state


def validate(days: object, at: object) -> tuple[int, str]:
    """Coerce and bound the request. Raises ValueError with a message for the UI."""
    if isinstance(days, bool) or not isinstance(days, int | float | str):
        raise ValueError("Interval must be a whole number of days.")
    try:
        n = int(days)
    except ValueError:
        raise ValueError("Interval must be a whole number of days.") from None
    if not MIN_DAYS <= n <= MAX_DAYS:
        raise ValueError(f"Interval must be between {MIN_DAYS} and {MAX_DAYS} days.")
    t = str(at or "").strip()
    if not _TIME_RE.match(t):
        raise ValueError("Time must look like HH:MM on a 24-hour clock, e.g. 07:30.")
    return n, t


def install(days: object, at: object) -> dict:
    """Create or replace the scheduled sweep. Returns the resulting state.

    Asking for a schedule that is already in place is a no-op, not a rewrite: it
    keeps the existing start boundary, so re-opening the modal and clicking through
    does not quietly push the next run out by an interval.
    """
    ok, why = supported()
    if not ok:
        raise RuntimeError(why)
    n, t = validate(days, at)
    current = describe()
    if (
        current.get("installed")
        and current.get("days") == n
        and current.get("at") == t
        and current.get("wrapper")
    ):
        current["changed"] = False
        return current
    _write_wrapper()
    proc = _run(
        [
            _schtasks() or "schtasks",
            "/Create",
            "/TN",
            TASK_NAME,
            "/TR",
            f'"{WRAPPER}"',
            "/SC",
            "DAILY",
            "/MO",
            str(n),
            "/ST",
            t,
            "/F",  # replace an existing definition rather than erroring
        ]
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "schtasks failed").strip())
    state = describe()
    state["changed"] = True
    return state


def remove() -> dict:
    """Turn the scheduled sweep off. Removing something that isn't there is fine."""
    ok, why = supported()
    if not ok:
        raise RuntimeError(why)
    proc = _run([_schtasks() or "schtasks", "/Delete", "/TN", TASK_NAME, "/F"])
    if proc.returncode != 0 and "cannot find" not in (proc.stderr + proc.stdout).lower():
        raise RuntimeError((proc.stderr or proc.stdout or "schtasks failed").strip())
    try:
        if os.path.exists(WRAPPER):
            os.remove(WRAPPER)
    except OSError:
        pass  # a leftover wrapper is harmless; the task is what mattered
    return describe()


def main() -> None:
    import json

    args = sys.argv[1:]
    if args and args[0] == "install":
        print(json.dumps(install(args[1], args[2] if len(args) > 2 else "07:30"), indent=1))
    elif args and args[0] == "remove":
        print(json.dumps(remove(), indent=1))
    else:
        print(json.dumps(describe(), indent=1))


if __name__ == "__main__":
    main()

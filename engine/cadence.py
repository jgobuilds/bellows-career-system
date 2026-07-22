"""Posting cadence: when a company actually posts, and when to sweep next.

The key realisation is that this needs NO history. Every ATS fetcher already pulls
a company's ENTIRE open board and the sweep then throws away everything out of
lane. But that discarded board is a dated time series: one Greenhouse request
returns dozens of postings spanning months. Cadence is available from sweep one;
it was simply being deleted.

Two signals are recorded, and they are different things:

  posting_dates  What the EMPLOYER says. Exact for Greenhouse / Lever / Ashby /
                 SmartRecruiters (first_published, createdAt, publishedDate,
                 releasedDate). Derived for Workday, whose list endpoint only
                 gives relative text ("Posted 3 Days Ago"), so its dates are
                 sweep-date minus age and go vague past "30+ days".

  arrivals       When WE first saw a posting. Accumulates across sweeps and is
                 immune to how a board reports dates. Worth less on day one and
                 more every sweep after.

WHAT THIS CANNOT SEE, and it matters: only OPEN postings exist in a board. Roles
already filled are gone. So the visible history thins out the further back you
look, and an interval estimated over a long window is biased FAST (the gaps you
can see are the survivors). Estimates are therefore weighted to the recent window
and every claim carries a confidence, rather than pretending the older data is as
good as the new.
"""

from __future__ import annotations

import json
import os
import statistics
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from itertools import pairwise

# A board with fewer than this many dated postings cannot support a cadence claim.
MIN_FOR_CADENCE = 4
# Only look this far back: beyond it, filled roles have thinned the record enough
# that the surviving gaps overstate how often the company posts.
RECENT_WINDOW_DAYS = 120
# Workday's relative text saturates here, so anything at or beyond is a floor.
WORKDAY_VAGUE_AT = 30


@dataclass
class Cadence:
    """What one company's open board implies about its posting rhythm."""

    key: str
    ats: str
    open_count: int = 0
    dated: int = 0
    quality: str = "exact"  # "exact" | "approx" (Workday-derived)
    median_gap_days: float | None = None
    last_post: str | None = None
    next_expected: str | None = None
    weekday_bias: str | None = None
    monthday_bias: str | None = None
    confidence: str = "none"  # none | low | medium | high
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return dict(self.__dict__)


def _parse(value: object) -> date | None:
    if not value:
        return None
    text = str(value).strip()
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        pass
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def board_dates(rows: Sequence[dict], today: date | None = None) -> tuple[list[date], str]:
    """Every dated posting on a board, plus how trustworthy those dates are.

    Falls back to age_days (Workday) when no absolute date is present, which is
    why the quality flag exists — a derived date is fine at 3 days old and
    meaningless at "30+".
    """
    today = today or datetime.now(timezone.utc).date()
    dates: list[date] = []
    approx = False
    for r in rows:
        d = _parse(r.get("date_posted"))
        if d is None:
            age = r.get("age_days")
            if age is None:
                continue
            try:
                age_i = int(age)
            except (TypeError, ValueError):
                continue
            d = today - timedelta(days=age_i)
            approx = True
            if age_i >= WORKDAY_VAGUE_AT:
                continue  # a floor, not a date — it would flatten every gap
        dates.append(d)
    return sorted(dates), ("approx" if approx else "exact")


def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:  # 11th, 12th, 13th
        return f"{n}th"
    return f"{n}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th') }"


def _bias(values: list[int], labels: dict[int, str], min_share: float) -> str | None:
    """Name a concentration only when it is well clear of uniform chance."""
    if len(values) < MIN_FOR_CADENCE:
        return None
    counts = Counter(values)
    top, n = counts.most_common(1)[0]
    share = n / len(values)
    return f"{labels.get(top, top)} ({n}/{len(values)})" if share >= min_share else None


def analyse(key: str, ats: str, rows: Sequence[dict], today: date | None = None) -> Cadence:
    """Infer one company's posting rhythm from a single board fetch."""
    today = today or datetime.now(timezone.utc).date()
    dates, quality = board_dates(rows, today)
    return _analyse_dates(key, ats, dates, quality, len(rows), today)


def from_entry(key: str, entry: dict, today: date | None = None) -> Cadence:
    """Same analysis, replayed from what a previous sweep stored."""
    today = today or datetime.now(timezone.utc).date()
    dates = sorted(d for d in (_parse(x) for x in entry.get("posting_dates") or []) if d)
    return _analyse_dates(
        key,
        entry.get("ats", "?"),
        dates,
        entry.get("date_quality", "exact"),
        entry.get("open_count", len(dates)),
        today,
    )


def _analyse_dates(
    key: str,
    ats: str,
    dates: list[date],
    quality: str,
    open_count: int,
    today: date,
) -> Cadence:
    c = Cadence(key=key, ats=ats, open_count=open_count, dated=len(dates), quality=quality)

    if not dates:
        c.notes.append("no usable posting dates on this board")
        return c

    c.last_post = dates[-1].isoformat()
    recent = [d for d in dates if (today - d).days <= RECENT_WINDOW_DAYS]
    if len(recent) < MIN_FOR_CADENCE:
        c.notes.append(
            f"only {len(recent)} posting(s) in the last {RECENT_WINDOW_DAYS} days — "
            "too few to claim a rhythm"
        )
        return c

    gaps = [(b - a).days for a, b in pairwise(recent)]
    gaps = [g for g in gaps if g >= 0]
    if gaps:
        c.median_gap_days = round(statistics.median(gaps), 1)
        c.next_expected = (dates[-1] + timedelta(days=max(1, round(c.median_gap_days)))).isoformat()

    # Weekday needs a clear majority; day-of-month ("the 1st and 15th") is a
    # weaker claim, so it needs a higher bar before it is worth stating at all.
    c.weekday_bias = _bias(
        [d.weekday() for d in recent],
        {0: "Mondays", 1: "Tuesdays", 2: "Wednesdays", 3: "Thursdays", 4: "Fridays"},
        0.45,
    )
    c.monthday_bias = _bias(
        [d.day for d in recent], {i: f"the {_ordinal(i)}" for i in range(1, 32)}, 0.30
    )

    if len(recent) >= 12 and quality == "exact":
        c.confidence = "high"
    elif len(recent) >= 6:
        c.confidence = "medium"
    else:
        c.confidence = "low"
    if quality == "approx":
        c.notes.append("dates derived from relative text (Workday); treat gaps as approximate")
    return c


# ---------------------------------------------------------------------------
# Persistence. Kept small on purpose: an id is dropped as soon as its posting
# leaves the board, so the file tracks roughly the current open count rather than
# growing without bound. The ARRIVAL it produced is kept, since that is the part
# that accumulates into a better estimate over time.
# ---------------------------------------------------------------------------
def load(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {"companies": {}}


def save(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        json.dump(data, fh, indent=1, ensure_ascii=False)


def _posting_id(row: dict) -> str:
    return str(row.get("job_url") or "") or f"{row.get('title', '')}|{row.get('location', '')}"


def observe(ats: str, rows: Sequence[dict], now: datetime | None = None) -> dict:
    """Compact, immutable summary of one board fetch.

    Pure and allocation-light on purpose: sweep workers run in parallel, so they
    build one of these and the main thread does all the merging. No locks, and the
    full board is not held in memory until the end.
    """
    now = now or datetime.now(timezone.utc)
    dates, quality = board_dates(rows, now.date())
    return {
        "ats": ats,
        "open_count": len(rows),
        "dates": [d.isoformat() for d in dates],
        "quality": quality,
        "ids": sorted({_posting_id(r) for r in rows if _posting_id(r)}),
    }


def record(data: dict, key: str, obs: dict, now: datetime | None = None) -> list[str]:
    """Fold one observation in. Returns the ids seen for the first time."""
    now = now or datetime.now(timezone.utc)
    stamp = now.isoformat(timespec="seconds")
    entry = data.setdefault("companies", {}).setdefault(key, {})
    entry["ats"] = obs["ats"]
    entry["last_swept"] = stamp
    entry["open_count"] = obs["open_count"]
    entry["posting_dates"] = obs["dates"]
    entry["date_quality"] = obs["quality"]

    known = entry.get("seen_ids") or {}
    current = set(obs["ids"])
    fresh = [i for i in current if i not in known]

    # First sweep establishes a baseline; calling all of it "new" would invent a
    # spike that never happened.
    if known:
        arrivals = entry.setdefault("arrivals", [])
        arrivals.extend([now.date().isoformat()] * len(fresh))
    entry["seen_ids"] = {i: known.get(i, stamp) for i in current}  # drop closed postings
    return fresh


def recommend(
    cadences: list[Cadence], today: date | None = None, floor_days: int = 2, ceiling_days: int = 21
) -> dict:
    """When to sweep next, from what the boards themselves imply.

    Driven by the companies that actually post, not the median across a list that
    is mostly dormant — a sweep is worth running when the ACTIVE boards have had
    time to produce something, and the quiet ones cost nothing by riding along.
    """
    today = today or datetime.now(timezone.utc).date()
    usable = [c for c in cadences if c.median_gap_days and c.confidence != "none"]
    if not usable:
        return {
            "next_sweep": (today + timedelta(days=7)).isoformat(),
            "days": 7,
            "basis": "no board had enough dated postings to infer a rhythm; weekly default",
            "companies_used": 0,
        }
    gaps = sorted(c.median_gap_days for c in usable if c.median_gap_days)
    # The quartile, not the median: sweeping at the median means missing half the
    # active boards' next posting on any given cycle.
    q1 = gaps[max(0, len(gaps) // 4 - 1)]
    days = int(min(max(round(q1), floor_days), ceiling_days))
    return {
        "next_sweep": (today + timedelta(days=days)).isoformat(),
        "days": days,
        "basis": (
            f"lower-quartile posting gap across {len(usable)} board(s) with a readable "
            f"rhythm is {q1:.1f} days"
        ),
        "companies_used": len(usable),
    }


def report(path: str, today: date | None = None) -> str:
    """Human-readable cadence summary + a sweep recommendation."""
    today = today or datetime.now(timezone.utc).date()
    data = load(path)
    companies = data.get("companies") or {}
    if not companies:
        return "No cadence data yet — run a sweep first (python engine/ats_sweep.py)."

    stats = [from_entry(k, v, today) for k, v in sorted(companies.items())]
    readable = [c for c in stats if c.median_gap_days]
    readable.sort(key=lambda c: c.median_gap_days or 999)

    out = [
        f"Posting cadence across {len(stats)} board(s) — {len(readable)} with a readable rhythm.",
        "",
    ]
    for c in readable[:20]:
        bits = [f"every ~{c.median_gap_days:g}d", f"{c.dated} dated/{c.open_count} open"]
        if c.weekday_bias:
            bits.append(f"mostly {c.weekday_bias}")
        if c.monthday_bias:
            bits.append(f"often {c.monthday_bias}")
        out.append(
            f"  {c.key:34} {', '.join(bits)}{'  [' + c.confidence + ']' if c.confidence else ''}"
        )
        if c.next_expected:
            out.append(f"  {'':34} last {c.last_post}, next ~{c.next_expected}")
    quiet = [c for c in stats if not c.median_gap_days]
    if quiet:
        out += ["", f"  {len(quiet)} board(s) too sparse to read:"]
        for c in quiet[:8]:
            out.append(
                f"    {c.key:32} {c.dated} dated posting(s) — {c.notes[0] if c.notes else ''}"
            )

    rec = recommend(stats, today)
    out += [
        "",
        f"Recommended next sweep: {rec['next_sweep']}  (in {rec['days']} day(s))",
        f"  basis: {rec['basis']}",
    ]
    total_arrivals = sum(len(v.get("arrivals") or []) for v in companies.values())
    out.append(
        f"  arrivals recorded so far: {total_arrivals} "
        "(accumulates each sweep; sharpens this estimate over time)"
    )
    return "\n".join(out)


def main() -> None:
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import config as CFG

    print(report(os.path.join(CFG.DATA_DIR, "posting_cadence.json")))


if __name__ == "__main__":
    main()

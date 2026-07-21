"""An approximate career ladder, so level terms stop being hand-typed guesses.

The problem this solves: a job title word carries no level information on its own.
"Principal" and "Lead" are BELOW target in a director-level search and ABOVE target
in an individual-contributor search. Both of the configs shipped in this repo place
those two words on opposite sides, and both are correct. So a flat word list can
never be right in general - it is only ever right relative to a target.

This module places titles on one approximate scale (1-11) spanning both the
individual-contributor and management tracks, so "at or above my target" becomes
arithmetic instead of vocabulary.

    IC track                        Management track
    ---------------------------------------------------------
     1  junior / entry
     2  mid (no title marker)
     3  senior                       supervisor / team lead
     4  staff / lead                 manager
     5  principal                    senior manager
     6  distinguished / fellow       director
     7                               senior director / head of
     8                               AVP
     9                               VP / managing director
    10                               SVP / EVP
    11                               C-level

APPROXIMATE is the operative word. Title inflation and industry convention make any
universal ladder wrong somewhere, so the genuinely misleading cases are recorded in
AMBIGUOUS below rather than pretended away. A banking VP is not an executive.

Nothing here overrides an explicit LEVEL_AT_OR_ABOVE / LEVEL_BELOW in a user's
config. This only generates a starting point when those are absent.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

Track = str  # "ic" | "management"


@dataclass(frozen=True)
class Rung:
    key: str
    rank: int
    track: Track
    terms: tuple[str, ...] = field(default_factory=tuple)


# Ordered by rank. Terms are plain words; the scorer compiles them with word
# boundaries, so "vp" will not match inside another word.
LADDER: tuple[Rung, ...] = (
    Rung("junior", 1, "ic", ("junior", "jr", "entry level", "intern", "trainee")),
    Rung("mid", 2, "ic", ()),  # mid-level roles carry no marker at all
    Rung("senior", 3, "ic", ("senior", "sr")),
    Rung("supervisor", 3, "management", ("supervisor", "team lead")),
    Rung("staff", 4, "ic", ("staff", "lead", "tech lead")),
    Rung("manager", 4, "management", ("manager",)),
    Rung("principal", 5, "ic", ("principal",)),
    Rung("senior_manager", 5, "management", ("senior manager", "sr manager")),
    Rung("associate_director", 5, "management", ("associate director",)),
    Rung("fellow", 6, "ic", ("distinguished", "fellow")),
    Rung("director", 6, "management", ("director",)),
    Rung("senior_director", 7, "management", ("senior director", "sr director", "head of")),
    Rung("avp", 8, "management", ("avp", "assistant vice president", "associate vice president")),
    Rung("vp", 9, "management", ("vice president", "vp", "managing director")),
    Rung(
        "svp", 10, "management", ("svp", "evp", "senior vice president", "executive vice president")
    ),
    Rung(
        "c_level",
        11,
        "management",
        ("chief", "cdo", "cto", "cio", "ciso", "chief data officer", "chief analytics officer"),
    ),
)

BY_KEY: dict[str, Rung] = {r.key: r for r in LADDER}

# Where the ladder is genuinely unreliable. These are the cases that cost someone a
# real application, so they are stated rather than smoothed over.
AMBIGUOUS: dict[str, str] = {
    "vp": (
        "In investment and commercial banking, VP is roughly a senior IC or manager - "
        "not an executive. Check team size and reporting line before treating it as one."
    ),
    "principal": (
        "In consulting, Principal is near-partner and sits well above Director. On a "
        "tech IC ladder it sits just above Staff. Same word, four rungs apart."
    ),
    "head of": (
        "Scope tracks org size, not the title. 'Head of Data' is the top job at a "
        "40-person startup and a mid-level director inside a bank."
    ),
    "lead": "Can be an IC tech lead or a people-managing team lead. The JD decides, not the title.",
    "manager": (
        "Two traps. In product and marketing, 'Manager' is usually an IC title with no "
        "reports — Product Manager, Product Marketing Manager, Account Manager. And in "
        "Big-4 and consulting, Manager sits materially higher than a corporate Manager. "
        "Read the JD for team size before trusting the rung."
    ),
    "director": "In the UK and much of the EU, Director can imply statutory board membership.",
    "associate": (
        "Junior on its own, but 'Associate Director' and 'Associate Vice President' are "
        "senior. Always match the longest phrase first."
    ),
}

# Longest phrase first, so "senior director" wins over "senior", and "associate vice
# president" over "associate". Getting this backwards silently mis-ranks every
# compound title.
_SEARCH_ORDER: tuple[tuple[str, Rung], ...] = tuple(
    sorted(
        ((term, rung) for rung in LADDER for term in rung.terms),
        key=lambda pair: len(pair[0]),
        reverse=True,
    )
)


def rung_of(title: str | None) -> Rung | None:
    """The ladder rung a title sits on, or None if it carries no level marker.

    None is normal: plenty of real titles ("Data Analyst") state no level at all.
    """
    if not title:
        return None
    # Punctuation must become whitespace, not vanish. Real titles are written
    # "Director, Data Governance" and "VP, Data & Analytics"; matching on " term "
    # without this misses both and silently reports no level at all.
    low = " " + " ".join(re.sub(r"[^a-z0-9]+", " ", title.lower()).split()) + " "
    for term, rung in _SEARCH_ORDER:
        if f" {term} " in low:
            return rung
    return None


def rank_of(title: str | None) -> int | None:
    rung = rung_of(title)
    return rung.rank if rung else None


def _resolve(level: str) -> Rung:
    key = level.strip().lower().replace(" ", "_").replace("-", "_")
    if key in BY_KEY:
        return BY_KEY[key]
    rung = rung_of(level)
    if rung:
        return rung
    raise KeyError(f"unknown ladder level {level!r}; known keys: {sorted(BY_KEY)}")


def terms_at_or_above(level: str, max_above: int | None = None) -> list[str]:
    """Level words for roles at or above `level`.

    `max_above` caps how far up to reach. IC searches usually want a cap: a
    mid-career IC matching everything up to C-level is not a useful signal.
    """
    base = _resolve(level).rank
    ceiling = base + max_above if max_above is not None else 99
    return [t for r in LADDER if base <= r.rank <= ceiling for t in r.terms]


def terms_below(level: str) -> list[str]:
    """Level words for roles below `level` - a step down, not a disqualification."""
    base = _resolve(level).rank
    return [t for r in LADDER if r.rank < base for t in r.terms]


def caveats(terms: list[str]) -> dict[str, str]:
    """Ambiguity notes for any generated list, so the traps travel with the terms."""
    return {t: AMBIGUOUS[t] for t in terms if t in AMBIGUOUS}


def describe(level: str) -> str:
    """A short human summary — used by the suggest CLI below."""
    rung = _resolve(level)
    peers = [r.key for r in LADDER if r.rank == rung.rank and r.key != rung.key]
    peer = f" (roughly parallel to {', '.join(peers)})" if peers else ""
    return f"{rung.key} — rank {rung.rank} on the {rung.track} track{peer}"


def main() -> None:
    """python engine/career_ladder.py director  ->  paste-ready config lines."""
    import sys

    level = sys.argv[1] if len(sys.argv) > 1 else "director"
    cap = int(sys.argv[2]) if len(sys.argv) > 2 else None
    above = terms_at_or_above(level, cap)
    below = terms_below(level)
    print(f"# target: {describe(level)}")
    print(f"LEVEL_AT_OR_ABOVE = {above!r}")
    print(f"LEVEL_BELOW = {below!r}")
    notes = caveats(above + below)
    if notes:
        print("\n# Ambiguous in your generated lists — check these against real postings:")
        for term, note in notes.items():
            print(f"#   {term}: {note}")


if __name__ == "__main__":
    main()

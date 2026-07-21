"""Read a job posting's stated work-authorization terms.

This module reports what a posting SAYS. It never decides whether a given person is
eligible, because that is a legal question about an individual's status and getting
it wrong costs someone hours of effort and a piece of their hope. A wrong
"you're eligible" is worse than no signal at all, so `unstated` (the majority case)
is never upgraded to a yes.

Four states, and every finding carries the snippet that produced it so a human can
check the call:

    citizens_only   "must be a U.S. citizen"; active-clearance terms as a proxy
    no_sponsorship  "unable to sponsor", and "citizen or permanent resident"
    sponsors        "visa sponsorship available"
    unstated        the default

Order matters more than the patterns do. The bare word "sponsorship" carries no
information at all - it appears in "we offer visa sponsorship" and "we are unable to
offer visa sponsorship" alike - so negatives are tested before positives, and the
narrower "citizen OR permanent resident" is tested before the broader "citizen",
which would otherwise swallow it and wrongly report citizens-only.

Config-free by design: callers pass the user's stored answers in, so this stays
unit-testable without scaffolding a userconfig.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

Verdict = Literal["citizens_only", "no_sponsorship", "sponsors", "unstated"]

# Ordered most-specific-first. The first pattern to match wins, so DO NOT reorder
# without re-reading the note above and running tests/test_work_auth.py.
_RULES: list[tuple[Verdict, str]] = [
    # 1. Citizen OR permanent resident. Must precede the citizens-only rules, or
    #    "U.S. Citizens or Green Card holders" reads as citizens-only and wrongly
    #    tells a permanent resident to skip a role they can actually hold.
    (
        "no_sponsorship",
        r"(?:u\.?s\.?|united states)?\s*citizens?(?:hip)?\s*(?:,|or|and/or)\s*"
        r"(?:lawful\s+)?(?:permanent\s+residen\w*|green[\s\-]?card\w*)",
    ),
    ("no_sponsorship", r"\bu\.?s\.?\s+persons?\b"),
    # 2. Citizens only, with no permanent-resident escape hatch nearby.
    (
        "citizens_only",
        r"must\s+be\s+(?:a\s+)?(?:u\.?s\.?|united states)\s+citizens?"
        r"(?!\s*(?:,|or|and/or)\s*(?:lawful\s+)?(?:permanent|green))",
    ),
    (
        "citizens_only",
        r"(?:u\.?s\.?|united states)\s+citizenship\s+(?:is\s+)?(?:required|mandatory)",
    ),
    (
        "citizens_only",
        r"(?:restricted\s+to|open\s+only\s+to)\s+(?:u\.?s\.?|united states)\s+citizens?",
    ),
    (
        "citizens_only",
        r"(?:u\.?s\.?|united states)\s+citizens?\s+only"
        r"(?!\s*(?:,|or|and/or)\s*(?:lawful\s+)?(?:permanent|green))",
    ),
    # 3. Security clearance. A DoD clearance requires U.S. citizenship, so this is a
    #    real signal rather than a guess - but the evidence snippet makes clear it
    #    was inferred from clearance language, not from an explicit statement.
    ("citizens_only", r"\b(?:ts/sci|top\s+secret|secret\s+clearance)\b"),
    ("citizens_only", r"active\s+(?:security\s+)?clearance"),
    # 4. Sponsorship, NEGATIVE. Before the positives: "we do not offer visa
    #    sponsorship" contains "visa sponsorship" as a substring.
    # Bare "no" is deliberately NOT in this alternation. It would match across an
    # unrelated clause - "we have no offices in Europe and offer visa sponsorship"
    # reads as a refusal to sponsor. Explicit "no sponsorship" is handled below.
    (
        "no_sponsorship",
        r"(?:not|unable|cannot|can\s*not|won'?t|do(?:es)?\s+not|will\s+not)\b[^.]{0,40}?"
        r"\bsponsor\w*",
    ),
    ("no_sponsorship", r"\bno\s+(?:visa\s+|employer\s+|immigration\s+)?sponsor\w*"),
    ("no_sponsorship", r"sponsorship\s+is\s+not\s+(?:available|offered|provided)"),
    ("no_sponsorship", r"without\s+(?:the\s+need\s+for\s+)?(?:visa\s+|employer\s+)?sponsorship"),
    (
        "no_sponsorship",
        r"authoriz\w*\s+to\s+work[^.]{0,60}?without[^.]{0,20}?sponsor\w*",
    ),
    # 5. Sponsorship, POSITIVE.
    ("sponsors", r"(?:visa\s+)?sponsorship\s+(?:is\s+)?(?:available|offered|provided)"),
    ("sponsors", r"(?:will|do|can|happy\s+to|open\s+to)\s+(?:consider\s+)?sponsor\w*"),
    # "offer/provide sponsorship" is only safe to treat as positive because the
    # negative rules above run first and already claim "does not offer sponsorship".
    ("sponsors", r"(?:offer|provide|support)s?\s+(?:visa\s+|immigration\s+)?sponsor\w*"),
    ("sponsors", r"\bwe\s+sponsor\b"),
    ("sponsors", r"h-?1b\s+transfer"),
]

_COMPILED: list[tuple[Verdict, re.Pattern[str]]] = [
    (verdict, re.compile(pattern, re.I)) for verdict, pattern in _RULES
]

_EVIDENCE_PAD = 70


@dataclass(frozen=True)
class Finding:
    """What a posting states, plus the text that says so."""

    verdict: Verdict
    evidence: str

    @property
    def is_stated(self) -> bool:
        return self.verdict != "unstated"


def _snippet(text: str, start: int, end: int) -> str:
    """Widen a match to readable context so a human can audit the verdict."""
    left = max(0, start - _EVIDENCE_PAD)
    right = min(len(text), end + _EVIDENCE_PAD)
    out = " ".join(text[left:right].split())
    if left > 0:
        out = "..." + out
    if right < len(text):
        out = out + "..."
    return out


def classify(text: str | None) -> Finding:
    """Report the work-authorization terms a posting states.

    Returns `unstated` when nothing is said, which is the common case and must never
    be presented as permission to apply.
    """
    if not text or not text.strip():
        return Finding("unstated", "")
    for verdict, rx in _COMPILED:
        m = rx.search(text)
        if m:
            return Finding(verdict, _snippet(text, m.start(), m.end()))
    return Finding("unstated", "")


def concern(finding: Finding, work_auth: dict[str, object] | None) -> str | None:
    """Reconcile a posting against the user's stored answers.

    Returns a short human-readable warning, or None when there is nothing to flag.
    Callers should DEMOTE and show this, never silently drop the lead: a wrong
    reading here would bury a good role invisibly.
    """
    if not work_auth:
        return None  # feature is opt-in; nothing captured means nothing to say

    needs_sponsorship = bool(work_auth.get("needs_sponsorship"))
    citizenship = str(work_auth.get("citizenship") or "").lower()

    if finding.verdict == "citizens_only" and citizenship != "citizen":
        return "posting states U.S. citizenship is required"
    if finding.verdict == "no_sponsorship" and needs_sponsorship:
        return "posting states it does not sponsor, and you indicated you need sponsorship"
    return None


def label(verdict: Verdict) -> str:
    """Short display text for a chip or a CSV column."""
    return {
        "citizens_only": "US citizens only",
        "no_sponsorship": "No sponsorship",
        "sponsors": "Sponsors visas",
        "unstated": "Not stated",
    }[verdict]

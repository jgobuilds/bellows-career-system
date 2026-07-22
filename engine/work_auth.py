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


# ---------------------------------------------------------------------------
# The user's own status.
#
# Stored as ONE named status rather than three loose booleans, so the dashboard
# dropdown, userconfig.py, and concern() cannot drift apart. The posting's verdict
# is a durable fact and is persisted per job; the user's status is NOT baked into
# job records, because it changes and would leave every stored row stale. The
# comparison happens at display time.
# ---------------------------------------------------------------------------
STATUSES: dict[str, dict[str, object] | None] = {
    "citizen": {"authorized_us": True, "needs_sponsorship": False, "citizenship": "citizen"},
    "permanent_resident": {
        "authorized_us": True,
        "needs_sponsorship": False,
        "citizenship": "permanent_resident",
    },
    "authorized": {"authorized_us": True, "needs_sponsorship": False, "citizenship": "other"},
    "needs_sponsorship": {
        "authorized_us": True,
        "needs_sponsorship": True,
        "citizenship": "other",
    },
    "unset": None,
}

STATUS_LABELS: dict[str, str] = {
    "unset": "Not set",
    "citizen": "US citizen",
    "permanent_resident": "Green Card / permanent resident",
    "authorized": "Authorized, no sponsorship needed",
    "needs_sponsorship": "Will need sponsorship",
}


def status_key(work_auth: dict[str, object] | None) -> str:
    """Which named status a stored WORK_AUTH dict corresponds to."""
    if not work_auth:
        return "unset"
    for key, value in STATUSES.items():
        if value == work_auth:
            return key
    # A hand-edited dict that matches no preset: classify it by what actually
    # drives concern(), so the dropdown still shows something truthful.
    if work_auth.get("needs_sponsorship"):
        return "needs_sponsorship"
    return "citizen" if work_auth.get("citizenship") == "citizen" else "authorized"


def render_config_block(status: str) -> str:
    """The exact WORK_AUTH assignment to write into userconfig.py."""
    value = STATUSES[status]
    if value is None:
        return "WORK_AUTH = None"
    # The inline comments are reproduced, not dropped. Someone who opens
    # userconfig.py after changing this in the dashboard should find the same
    # annotated block they started with, not a stripped one.
    rows = [
        (
            f'    "authorized_us": {value["authorized_us"]},',
            "# legally authorized to work in the US?",
        ),
        (
            f'    "needs_sponsorship": {value["needs_sponsorship"]},',
            "# will you need sponsorship now or in the future?",
        ),
        (
            f'    "citizenship": "{value["citizenship"]}",',
            '# "citizen" | "permanent_resident" | "other"',
        ),
    ]
    width = max(len(code) for code, _ in rows) + 2
    body = "\n".join(f"{code.ljust(width)}{comment}" for code, comment in rows)
    return "WORK_AUTH = {\n" + body + "\n}"


_ASSIGNMENT = re.compile(
    r"^WORK_AUTH\s*=\s*(?:None|\{.*?^\})",
    re.M | re.S,
)


def rewrite_config(text: str, status: str) -> str:
    """Replace the WORK_AUTH assignment in userconfig.py source.

    Pure so it can be tested without touching a real config — a botched rewrite
    here would break the one file the whole system reads.
    """
    if status not in STATUSES:
        raise ValueError(f"unknown work-auth status {status!r}")
    block = render_config_block(status)
    new, n = _ASSIGNMENT.subn(lambda _: block, text, count=1)
    if n:
        return new
    return text.rstrip() + "\n\n" + block + "\n"


def label(verdict: Verdict) -> str:
    """Short display text for a chip or a CSV column."""
    return {
        "citizens_only": "US citizens only",
        "no_sponsorship": "No sponsorship",
        "sponsors": "Sponsors visas",
        "unstated": "Not stated",
    }[verdict]

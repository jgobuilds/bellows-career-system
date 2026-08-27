#!/usr/bin/env python3
"""metric_registry.py — every number that may appear on a document, and its terms.

    python engine/metric_registry.py --check <spec.json>   # validate one spec
    python engine/metric_registry.py --audit               # every spec at once
    python engine/metric_registry.py --stats

WHY THIS EXISTS: the guards that came before this one are all DENYLISTS. The
bullet ledger asks "has a human looked at this token for this employer?", the
claim guard asks "does the profile put this tool at this employer?", and the
banned-phrase check asks "is this string on the list?" Each was added after an
error escaped, and each catches only the shape of error that created it.

A number got through all three while being TRUE: a per-case saving whose SAMPLE
SIZE was never recorded. It was real, and it was hedged exactly as the profile
then instructed, and it was still wrong to print. Set beside a population figure,
a reader infers a rate nobody measured. The missing thing was not honesty and not a hedge. It was a FIELD:
what is this number a sample of?

So this inverts the logic. Instead of a denylist of phrasings, an ALLOWLIST of
numbers, each carrying the metadata that decides whether it can be stated at all:

    measured   did anyone measure it, or is it an estimate or an anecdote
    sample     what it is a sample OF - required, and the field that was missing
    usage      "document" or "interview_only"
    employers  which employers may carry it, so a figure cannot drift sideways
    never      the specific misreadings this number invites

Registering a figure forces the sample question ONCE, at registration, instead of
once per application - and a figure whose sample is unrecorded cannot be given
usage "document" without someone writing that down and meaning it.

The registry lives under `personal/` (gitignored) because the figures are career
content. Like the bullet ledger it is a cache of human judgement, not a source of
truth: `career-profile.md` remains the authority, and deleting this file costs a
re-registration, not a fact.
"""

import argparse
import glob
import json
import os
import re
from collections.abc import Iterator

import _paths  # noqa: F401  (side-effect: repo root on sys.path for `import config`)
import config

REGISTRY = os.path.join(os.path.dirname(config.PROFILE_MD), "data", "metrics.json")

# Fields that are not prose: contact lines, dates, and the folder-derived title
# block. Numbers here are addresses and calendars, not claims.
SKIP_FIELDS = {"contact", "name", "location_dates", "subject", "signoff"}

NUM = re.compile(r"\$?\d[\d,.]*\s?(?:%|k|K|M|\+|x)?")

# SPELLED-OUT figures. The digit scanner above is blind to them, so "twenty-five
# million contacts" and "two hundred centres" sailed through a cover letter while
# "25 million" would have been caught. A guard with a hole that size is worse than
# an obvious absence, because it reads as coverage.
#
# Prose is where the softest claims live — a writer reaching for words instead of
# digits is often reaching for a figure they cannot source — so this is exactly the
# wrong place to be blind. Deliberately bounded: number words plus their scale and
# units, not an English parser. Anything it cannot resolve to a value is still
# reported, because "there is a spelled-out quantity here" is the finding.
_ONES = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
}
_TENS = {
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}
_SCALE = {"hundred": 100, "thousand": 1_000, "million": 1_000_000, "billion": 1_000_000_000}
_WORDS = set(_ONES) | set(_TENS) | set(_SCALE)


def _alt(words: set[str]) -> str:
    """Longest-first alternation, so "seventeen" wins over "seven"."""
    return "|".join(sorted(words, key=len, reverse=True))


# Built with an explicit format string rather than concatenated raw fragments.
# An earlier version did the latter, a word-boundary escape became a literal
# backspace, and the pattern matched nothing while looking entirely correct. It
# read as coverage and delivered none, which is worse than an obvious gap. The
# tests exist because of that, and they assert on VALUES, not on the pattern.
WORD_NUM = re.compile(
    r"\b(?:{first})(?:[\s-]+(?:{rest}))*\b".format(first=_alt(_WORDS), rest=_alt(_WORDS | {"and"})),
    re.I,
)


def spelled_value(phrase: str) -> int | None:
    """The numeric value of a spelled-out phrase, or None if it will not resolve.

    None is not a failure — an unresolvable phrase is still reported as a
    spelled-out quantity. Refusing to guess is the point.
    """
    total = current = 0
    seen = False
    for word in re.split(r"[\s-]+", phrase.lower()):
        if word == "and":
            continue
        if word in _ONES:
            current += _ONES[word]
            seen = True
        elif word in _TENS:
            current += _TENS[word]
            seen = True
        elif word in _SCALE:
            mult = _SCALE[word]
            if mult >= 1000:
                total += (current or 1) * mult
                current = 0
            else:
                current = (current or 1) * mult
            seen = True
        else:
            return None
    return (total + current) if seen else None


def load(path: str = REGISTRY) -> dict:
    if not os.path.exists(path):
        return {"metrics": [], "not_a_claim": [], "never_together": []}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _numbers(text: str) -> list[tuple[str, int, str]]:
    """Every number-like token in a string, with its offset.

    Returns (value, offset, surface). The offset lets the caller skip numbers
    already covered by a longer registered phrase - a hyphenated range must be
    judged as one figure, not two adjacent ones. The SURFACE is what the text
    actually said: for a spelled figure the value and the surface differ, and the
    not-a-claim check has to read the surface or it can never excuse an idiom.
    """
    out = []
    for m in NUM.finditer(text):
        t = m.group(0).strip().rstrip(".,")
        if not any(c.isdigit() for c in t) or len(t) < 2:
            continue
        if re.fullmatch(r"(19|20)\d\d", t):  # a year is a date, not a claim
            continue
        out.append((t, m.start(), t))

    # Spelled-out figures, normalised to the digit form the registry stores, so a
    # metric registered as "200" matches "two hundred" without a second entry.
    #
    # Bounded to figures that can actually mislead: >= 10, or any quantity followed
    # by a time unit. Small structural counts ("four analysts", "three sprints") are
    # the least valuable thing to gate and the most likely to collide - "two data
    # engineers" produced a "2" that clashed with a registered "two hours" at
    # another employer and accused a correct bullet of drifting.
    for m in WORD_NUM.finditer(text):
        phrase = m.group(0)
        if phrase.lower() in ("one", "and"):
            continue  # "one source of truth" is an article, not a quantity
        val = spelled_value(phrase)
        if val is None:
            continue
        tail = text[m.end() : m.end() + 14].lower()
        is_duration = bool(re.match(r"[\s-]*(year|month|week|day|hour|minute|sprint)", tail))
        if val < 10 and not is_duration:
            continue
        out.append((str(val), m.start(), phrase))
    return out


def _strings(obj: object, field: str = "") -> "Iterator[tuple[str, str]]":
    """Every renderable string in a spec, paired with the employer it sits under."""
    if isinstance(obj, str):
        yield field, obj
    elif isinstance(obj, list):
        for x in obj:
            yield from _strings(x, field)
    elif isinstance(obj, dict):
        company = obj.get("company")
        for k, v in obj.items():
            if k in SKIP_FIELDS:
                continue
            yield from _strings(v, company or field)


def _index(data: dict) -> dict[str, list[dict]]:
    """token -> every metric that uses it.

    A LIST, not a single metric. The same number legitimately means different
    things at different employers: one employer's hours-saved is another's
    recipient count, and one dollar figure can be a budget in one role and an
    annual value in another. Collapsing those to one entry
    made the guard accuse correct bullets of drifting between employers, which is
    how a check earns the reputation that gets it ignored.
    """
    idx: dict[str, list[dict]] = {}
    for m in data.get("metrics", []):
        for tok in m.get("tokens", []):
            idx.setdefault(tok, []).append(m)
    return idx


def _canon(company: str, data: dict) -> str:
    """One employer, one name. A résumé label can change across applications for
    ATS-parsing reasons while the employer does not, and older specs keep the
    old label. The profile declares those aliases so they resolve to one."""
    for canon, aliases in (data.get("employer_aliases") or {}).items():
        if company == canon or company in aliases:
            return canon
    return company


def _is_noise(surface: str, text: str, data: dict) -> bool:
    """Known non-claims: version strings, requisition ids, idioms, scale ranges."""
    for pat in data.get("not_a_claim", []):
        if re.search(pat, text):
            # only excuse the token if the noise pattern actually contains it
            for m in re.finditer(pat, text):
                if surface.lower() in m.group(0).lower():
                    return True
    return False


def warnings(spec: dict, data: dict | None = None) -> list[str]:
    """Every registry violation in one spec.

    Four checks, in the order they catch things:
      1. UNREGISTERED  a number nobody has vetted (the allowlist, option B)
      2. INTERVIEW-ONLY a registered number the registry forbids on documents
      3. WRONG EMPLOYER a figure drifting to an employer it does not belong to
      4. NEVER-TOGETHER two figures a reader will wrongly combine (option C)
    """
    data = load() if data is None else data
    if not data.get("metrics"):
        # An empty allowlist means "not configured yet", not "nothing is allowed".
        # Without this a fresh install would flag every number on every document.
        return []
    idx = _index(data)
    out: list[str] = []

    # 0: PHRASE tokens first — any registered token that is not a single number
    # (a hyphenated range, a spelled-out quantity, a percentage range). The bare
    # number scanner splits those into their parts, so a registered range arrived
    # as two unrelated numbers and the interview-only entry never matched. That is
    # the exact shape this registry exists to stop, so it failed at its founding
    # purpose until a test said so.
    # Phrase spans are recorded and the number scanner skips inside them.
    def phrase_hits(text: str) -> tuple[list[tuple[str, dict]], list[tuple[int, int]]]:
        hits, spans = [], []
        for tok, metrics in idx.items():
            if re.fullmatch(r"\$?[\d,.]+\s?[%kKM+x]?", tok):
                continue  # a plain number; the scanner below handles it
            for m in re.finditer(re.escape(tok), text, re.I):
                hits.append((tok, metrics[0]))
                spans.append(m.span())
        return hits, spans

    for company, text in _strings(spec):
        company = _canon(company, data)
        hits, spans = phrase_hits(text)
        for tok, metric in hits:
            if metric.get("usage") != "document":
                out.append(
                    f"INTERVIEW-ONLY figure {tok!r} ({metric['id']}) is on a document — "
                    f"{metric.get('why_not_document', 'registry marks it interview-only')}"
                )

    # 1-3: per-string checks.
    for company, text in _strings(spec):
        company = _canon(company, data)
        _, spans = phrase_hits(text)
        covered = {i for a, b in spans for i in range(a, b)}
        for tok, at, surface in _numbers(text):
            if at in covered:
                continue  # already judged as part of a registered phrase
            cands = idx.get(tok)
            if not cands:
                if _is_noise(surface, text, data):
                    continue
                out.append(
                    f"UNREGISTERED number {tok!r} in: …{text.strip()[:70]}… — "
                    f"register it in metrics.json (state its sample) or it does not ship"
                )
                continue
            # Employer first: it narrows an ambiguous token to the metric that
            # actually applies here, which is what the usage verdict depends on.
            fits = [
                m
                for m in cands
                if not m.get("employers")
                or not company
                or company in [_canon(e, data) for e in m["employers"]]
            ]
            if not fits:
                where = ", ".join(sorted({e for m in cands for e in m.get("employers", [])}))
                out.append(
                    f"WRONG EMPLOYER: {tok!r} ({cands[0]['id']}) appears under {company!r}, "
                    f"but the registry places it at {where}"
                )
                continue
            # Only a problem if EVERY reading of this token is interview-only.
            if all(m.get("usage") != "document" for m in fits):
                m = fits[0]
                out.append(
                    f"INTERVIEW-ONLY figure {tok!r} ({m['id']}) is on a document — "
                    f"{m.get('why_not_document', 'registry marks it interview-only')}"
                )

    # 4: adjacency. Scoped to ONE rendered string, because that is the unit a
    # reader combines within — a bullet, a summary, a cover paragraph.
    #
    # Two severities, learned the hard way on the first audit: co-occurrence is
    # not the defect. A smaller figure legitimately sits beside the larger one it
    # is part of, when the passage SEQUENCES them ("proved it with X, then
    # delivered Y"). What is never allowed is the SUM. So the hard rule
    # fires on summing language, and bare co-occurrence is an advisory NOTE.
    SUMMING = re.compile(
        r"\b(total(?:ling|ing|s)?|combined|altogether|in all|together worth|plus)\b", re.I
    )
    for company, text in _strings(spec):
        toks = {t for t, _, _ in _numbers(text)}
        for rule in data.get("never_together", []):
            if rule["a"] in toks and rule["b"] in toks:
                out.append(f"NEVER-TOGETHER: {rule['a']!r} and {rule['b']!r} — {rule['why']}")
        for rule in data.get("check_together", []):
            if rule["a"] in toks and rule["b"] in toks:
                sev = "NEVER-TOGETHER" if SUMMING.search(text) else "NOTE"
                out.append(
                    f"{sev}: {rule['a']!r} and {rule['b']!r} share one passage — {rule['why']}"
                )

    # 5: words a metric must never appear beside.
    #
    # Every metric already carries a `never` list, and it was PROSE — read by
    # people, enforced by nothing. The 25-person figure has said "any growth verb
    # — grew / built from / scaled from / from a single unit" since the registry
    # was written, and four phrasings using exactly those verbs were nonetheless
    # approved into the bullet library and offered back as suggestions. A rule
    # that is written down and unenforced is indistinguishable from no rule; it is
    # worse, because everyone believes it is being kept.
    #
    # `never_words` is the machine-checkable half. It sits beside the prose rather
    # than replacing it: the prose says WHY, which a warning has to quote to be
    # actionable, and the list says WHAT to match.
    for company, text in _strings(spec):
        low = text.lower()
        toks = {t for t, _, _ in _numbers(text)}
        for m in data.get("metrics", []):
            words = m.get("never_words") or []
            if not words or not (set(m.get("tokens", [])) & toks):
                continue
            if m.get("employers") and company and company not in m["employers"]:
                continue
            for w in words:
                if re.search(rf"\b{re.escape(w.lower())}\b", low):
                    why = (m.get("never") or ["registry forbids this pairing"])[0]
                    out.append(f"FORBIDDEN PAIRING: {w!r} appears with {m['id']} — {why}")
                    break

    return sorted(set(out))


def main() -> int:
    ap = argparse.ArgumentParser(description="Allowlist of documentable figures.")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", metavar="SPEC")
    g.add_argument("--audit", action="store_true", help="every spec under applications/")
    g.add_argument("--stats", action="store_true")
    a = ap.parse_args()

    data = load()
    if a.stats:
        ms = data.get("metrics", [])
        doc = [m for m in ms if m.get("usage") == "document"]
        print(
            f"  {len(ms)} registered figures — {len(doc)} documentable, {len(ms) - len(doc)} interview-only"
        )
        print(f"  {len(data.get('never_together', []))} adjacency rule(s)")
        for m in ms:
            if m.get("usage") != "document":
                print(f"    ⛔ {m['id']}: {m.get('why_not_document', '')[:78]}")
        return 0

    if a.check:
        specs = [a.check]
    else:
        base = os.path.join(os.path.dirname(config.PROFILE_MD), "applications")
        specs = sorted(glob.glob(os.path.join(base, "*", "resume.json"))) + sorted(
            glob.glob(os.path.join(base, "*", "cover.json"))
        )

    bad = 0
    for path in specs:
        with open(path, encoding="utf-8") as fh:
            spec = json.load(fh)
        warns = warnings(spec, data)
        if warns:
            bad += 1
            label = os.path.join(os.path.basename(os.path.dirname(path)), os.path.basename(path))
            print(f"\n  {label}")
            for w in warns:
                print(f"      {w}")
    if not bad:
        print(f"  {len(specs)} spec(s) clean — every figure registered and documentable.")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())

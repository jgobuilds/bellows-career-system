#!/usr/bin/env python3
"""resume_score.py — a standalone résumé health score (0-100), honest and rule-based.

WHAT IT IS: a fast pre-flight grade for a resume.json spec across three checkable
dimensions -- ATS-safety (structural rules that survive a real import, reused from
resume_builder.validate), quantified impact (the share of bullets carrying a real
number), and tight-and-complete structure. It names the specific weak bullets to fix,
so the number is actionable rather than a vanity score.

WHAT IT IS NOT: a benchmark against "real applicants" or a market-data oracle -- there
is no hidden corpus and no invented percentile. Every point traces to a rule you can
read below. It grades the spec you feed it; it does not tailor to a specific job (that
is ats_match.py) or write content for you.

    python engine/resume_score.py personal/applications/acme/resume.json
"""

import json
import re
import sys

import resume_builder

_METRIC = re.compile(r"\d")  # any digit == a number, %, $, year, multiple, or count
_LONG_BULLET = 320  # chars; longer reads as a paragraph, not a bullet

# The three dimensions, weighted to 100.
W_ATS = 40
W_QUANT = 40
W_TIGHT = 20


def _bullet_texts(spec: dict) -> list[str]:
    """Every impact bullet flattened to one string (lead + rest joined). Earlier
    one-line roles are excluded -- they're intentionally terse, not weak bullets."""
    out: list[str] = []
    for entry in spec.get("experience", []):
        roles = entry["roles"] if entry.get("roles") else [entry]
        for role in roles:
            for pair in role.get("bullets", []):
                out.append("".join(str(p) for p in pair))
    return out


def _grade(score: int) -> str:
    for cut, letter in ((90, "A"), (75, "B"), (60, "C"), (45, "D")):
        if score >= cut:
            return letter
    return "F"


def score_spec(spec: dict) -> dict:
    """Grade a resume.json spec 0-100. Pure: no I/O, no config. Returns the score, a
    letter grade, per-dimension points, and the specific issues to fix."""
    warnings = list(resume_builder.validate(spec))
    bullets = _bullet_texts(spec)
    total = len(bullets)

    # 1. ATS-safety -- each structural warning costs points (floor 0).
    ats = max(0, W_ATS - 8 * len(warnings))

    # 2. Quantified impact -- share of bullets carrying a real number.
    weak = [b for b in bullets if not _METRIC.search(b)]
    quantified = total - len(weak)
    quant = round(W_QUANT * quantified / total) if total else 0

    # 3. Tight & complete -- concision and the basics being present.
    tight = W_TIGHT
    reasons: list[str] = []
    if not str(spec.get("summary") or "").strip():
        tight -= 5
        reasons.append("no summary paragraph")
    if total < 3:
        tight -= 5
        reasons.append(f"only {total} impact bullets (aim for a few per recent role)")
    if any(len(b) > _LONG_BULLET for b in bullets):
        tight -= 5
        reasons.append("a bullet runs long enough to read as a paragraph")
    if not spec.get("contact"):
        tight -= 5
        reasons.append("no contact line")
    tight = max(0, tight)

    score = ats + quant + tight
    return {
        "score": score,
        "grade": _grade(score),
        "dimensions": {"ats_safe": ats, "quantified": quant, "tight_complete": tight},
        "stats": {"bullets": total, "quantified": quantified},
        "weak_bullets": weak[:8],
        "warnings": warnings,
        "tight_reasons": reasons,
    }


def report(result: dict) -> str:
    """One-screen human-readable report."""
    d = result["dimensions"]
    st = result["stats"]
    lines = [
        f"Résumé health: {result['score']}/100  (grade {result['grade']})",
        f"  ATS-safe           {d['ats_safe']:>2}/{W_ATS}",
        f"  Quantified impact  {d['quantified']:>2}/{W_QUANT}   "
        f"({st['quantified']}/{st['bullets']} bullets carry a number)",
        f"  Tight & complete   {d['tight_complete']:>2}/{W_TIGHT}",
    ]
    if result["warnings"]:
        lines.append("\nATS warnings (fix first -- these can break the import):")
        lines += [f"  - {w}" for w in result["warnings"]]
    if result["tight_reasons"]:
        lines.append("\nStructure:")
        lines += [f"  - {r}" for r in result["tight_reasons"]]
    if result["weak_bullets"]:
        lines.append("\nBullets with no number (quantify or cut):")
        lines += [f"  - {b[:100]}" for b in result["weak_bullets"]]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: python engine/resume_score.py <resume.json>", file=sys.stderr)
        return 2
    path = argv[0]
    try:
        with open(path, encoding="utf-8") as fh:
            spec = json.load(fh)
    except FileNotFoundError:
        print(f"no such file: {path}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        print(f"not valid JSON ({path}): {e}", file=sys.stderr)
        return 2
    print(report(score_spec(spec)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""line_fill.py — which bullets waste a line, and which have room to say more.

    python engine/line_fill.py <spec.json>
    python engine/line_fill.py <spec.json> --orphan 30 --room 25

A bullet that wraps to a final line holding three words has spent a whole line on
three words. Tightened by a dozen characters it costs one line less, and that line
is the scarcest thing on a two-page résumé — it is what pays for the accomplishment
currently sitting in the profile unused.

The reverse case is worth as much and is invisible without measuring: a bullet
whose last line ends near the left margin has room for real detail at ZERO cost in
lines. Adding a metric or a named tool there is free.

MEASURED, NOT ESTIMATED. Widths come from the actual Calibri metrics at the actual
10.5pt, with the bold lead-in measured in the bold face, because a character-count
approximation is wrong exactly where it matters: "WWW" and "iii" differ by a factor
of four, and the advice "tighten this by two words" is useless if the underlying
number is a guess. Bold runs ~4% wider than regular, which is enough to move a
borderline line on its own.

IT PROPOSES AND NEVER EDITS. Where to spend a recovered line, and whether a bullet
has anything worth adding, are judgement calls — and the honesty rule means any
added detail has to come from career-profile.md rather than be invented to fill
space. Filling a line with padding is worse than leaving it short.
"""

import argparse
import json
import os
import sys

import _paths  # noqa: F401  (side-effect: repo root on sys.path)
from docx_common import BODY_FONT

# resume_builder's page geometry, plus the bullet's own indent: the glyph "•  "
# and a 0.18" hanging indent mean a bullet's text is narrower than the page.
PAGE_USABLE_IN = 7.3
BULLET_INDENT_IN = 0.18
BODY_PT = 10.5
DPI = 96.0

# CALIBRATION, measured against Word's actual output rather than reasoned about.
#
# Raw advance widths put slightly more on a line than Word does, and the gap only
# shows at the boundary — which is precisely where this tool's advice lives. The
# first version called a real 4-line bullet "3 lines, last line 99% full", so it
# reported a full line where the page showed four characters stranded alone. A
# tool that is right in the easy cases and wrong at the margin is worse than no
# tool, because the margin is the only place anyone consults it.
#
# Derived from four bullets whose rendered line counts were read off the page,
# then checked that no shorter margin reproduces all four. 0.10in is the smallest
# that does; 0.12 also fits, so this sits at the conservative end of the range
# rather than tuned to a single case.
#
# ⚠️ Re-derive this if the body font, point size or margins change. It is a
# correction for one specific rendering, not a universal constant.
WORD_MARGIN_IN = 0.10


def _fonts() -> dict | None:
    """The real faces, or None if they cannot be loaded.

    Returning None rather than falling back to an average character width is
    deliberate: a fabricated measurement presented as a measurement is the failure
    this module exists to avoid.
    """
    try:
        from PIL import ImageFont
    except ImportError:
        return None
    root = os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts")
    faces = {"regular": "calibri.ttf", "bold": "calibrib.ttf"}
    if BODY_FONT.lower() != "calibri":
        return None
    out = {}
    for key, fn in faces.items():
        path = os.path.join(root, fn)
        if not os.path.exists(path):
            return None
        out[key] = ImageFont.truetype(path, round(BODY_PT * DPI / 72.0))
    return out


def width_in(text: str, fonts: dict, bold: bool = False) -> float:
    """Rendered width of a string, in inches."""
    face = fonts["bold" if bold else "regular"]
    return face.getlength(text) / DPI


def wrap(lead: str, rest: str, fonts: dict, usable: float) -> list[float]:
    """Greedy line-break the bullet the way Word will, returning each line's width.

    Word breaks on whitespace and the lead-in is bold, so the two runs are measured
    in their own faces. Greedy wrapping is what Word does for a plain paragraph
    with no justification, which is how these are rendered.
    """
    lines: list[float] = []
    cur = 0.0
    first = True
    tokens = [(w, True) for w in lead.split()] + [(w, False) for w in rest.split()]
    for i, (word, is_bold) in enumerate(tokens):
        w = width_in(word, fonts, is_bold)
        space = 0.0 if cur == 0.0 else width_in(" ", fonts, is_bold)
        bullet = width_in("•  ", fonts) if (first and cur == 0.0) else 0.0
        if cur + space + w + bullet <= usable or cur == 0.0:
            cur += space + w + bullet
        else:
            lines.append(cur)
            first = False
            cur = w
        if i == len(tokens) - 1:
            lines.append(cur)
    return lines


def analyse(spec: dict, orphan_pct: float, room_pct: float) -> list[dict]:
    fonts = _fonts()
    if fonts is None:
        return []
    usable = PAGE_USABLE_IN - BULLET_INDENT_IN - WORD_MARGIN_IN
    out = []
    for entry in spec.get("experience", []) + spec.get("advisory", []):
        for role in entry.get("roles") or [entry]:
            for lead, rest in role.get("bullets") or []:
                widths = wrap(lead, rest, fonts, usable)
                if len(widths) < 2:
                    continue  # a single-line bullet has no orphan and no tail
                fill = widths[-1] / usable
                kind = (
                    "ORPHAN"
                    if fill <= orphan_pct / 100.0
                    else ("ROOM" if fill <= (100 - room_pct) / 100.0 else None)
                )
                if not kind:
                    continue
                out.append(
                    {
                        "company": entry.get("company", "?"),
                        "lead": lead,
                        "rest": rest,
                        "lines": len(widths),
                        "fill": fill,
                        "spare_in": usable - widths[-1],
                        "kind": kind,
                    }
                )
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Bullets that waste a line, or have room to say more.")
    ap.add_argument("spec")
    ap.add_argument(
        "--orphan",
        type=float,
        default=30.0,
        help="last line at or below this %% of width is an orphan (default 30)",
    )
    ap.add_argument(
        "--room",
        type=float,
        default=25.0,
        help="at least this %% of the last line free counts as room (default 25)",
    )
    a = ap.parse_args()

    with open(a.spec, encoding="utf-8") as fh:
        spec = json.load(fh)
    if _fonts() is None:
        print("  Cannot measure: Pillow or the Calibri faces are unavailable.")
        print("  Refusing to estimate — a guessed width would make the advice worse than none.")
        return 1

    rows = analyse(spec, a.orphan, a.room)
    orphans = [r for r in rows if r["kind"] == "ORPHAN"]
    room = [r for r in rows if r["kind"] == "ROOM"]

    print(
        f"  measured in {BODY_FONT} {BODY_PT}pt across "
        f"{PAGE_USABLE_IN - BULLET_INDENT_IN:.2f}in of bullet width\n"
    )

    print(f"ORPHAN — last line ≤{a.orphan:.0f}% of the width; tightening saves a whole line")
    if not orphans:
        print("   none\n")
    for r in orphans:
        print(f"   [{r['lines']} lines, last {r['fill']:.0%}]  {r['company'][:22]}")
        print(f"      {r['lead']}{r['rest'][:70]}")
        print(
            f"      → trim ~{r['fill'] * (PAGE_USABLE_IN - BULLET_INDENT_IN - WORD_MARGIN_IN) * 14:.0f} "
            f"characters to pull it back"
        )
    print()

    print(f"ROOM — ≥{a.room:.0f}% of the last line free; detail here costs NO extra line")
    if not room:
        print("   none")
    for r in room:
        print(
            f"   [{r['lines']} lines, last {r['fill']:.0%}, {r['spare_in']:.2f}in free]  "
            f"{r['company'][:22]}"
        )
        print(f"      {r['lead']}{r['rest'][:70]}")
        print(f"      → room for ~{r['spare_in'] * 14:.0f} more characters, free")
    print("\n  Proposes only. Anything added must come from career-profile.md —")
    print("  padding a line to fill it is worse than leaving it short.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

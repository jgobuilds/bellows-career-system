#!/usr/bin/env python3
"""docx_common.py — rendering utilities shared by resume_builder + cover_builder.

The placeholder scan, the brand constants, and the run() primitive were duplicated
byte-for-byte in both builders. They live here once now. Each builder still owns
its own page layout (margins, sections, spacing) — only the genuinely shared bits
are here.
"""

import re
from collections.abc import Iterator
from typing import Any

from docx.shared import Pt, RGBColor

BRAND_BLUE = RGBColor(0x00, 0x72, 0xB2)  # primary brand blue #0072B2 (swap for your own)
BODY_FONT = "Calibri"

# Leftover template stubs: [brackets], {braces}, <angles>, and the two sentinel words.
_PLACEHOLDER = re.compile(r"\[[^\]]*\]|\{[^}]*\}|<[^>]+>|NEED METRIC|CONFIRM")


def iter_strings(obj: object) -> Iterator[str]:
    """Yield every string leaf in a nested dict/list/tuple — so a placeholder scan
    reads CONTENT, not the JSON structure (whose own {} and [] are not stubs)."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from iter_strings(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from iter_strings(v)


def scan_placeholders(spec: object) -> set[str]:
    """Unique leftover template stubs across all content strings in the spec."""
    found = set()
    for s in iter_strings(spec):
        found.update(_PLACEHOLDER.findall(s))
    return found


def run(
    p: Any,
    text: str,
    bold: bool = False,
    italic: bool = False,
    size: float = 10.5,
    color: Any = None,
    font: str = BODY_FONT,
) -> Any:
    """Add a styled run to paragraph `p` and return it."""
    r = p.add_run(text)
    r.bold, r.italic = bold, italic
    r.font.size = Pt(size)
    r.font.name = font
    if color:
        r.font.color.rgb = color
    return r

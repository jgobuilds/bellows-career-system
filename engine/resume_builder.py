#!/usr/bin/env python3
"""
resume_builder.py — render an ATS-clean resume .docx from a JSON spec.

The FORMAT rules (the ones learned the hard way from real ATS imports — see
resume-style-rules.md) live here, once. Each application supplies only its
CONTENT as a JSON spec; this builder guarantees the parse-safe layout every time:
no tables, single column, "City, ST | dates" location lines, punctuation-free job
titles, bold sentence-case bullet lead-ins, plain competency lines.

USAGE
  python engine/resume_builder.py <spec.json> <out.docx>
  # or:  from engine.resume_builder import build_resume; build_resume(spec, out)

Then run docx_finalize.py on the output to scrub metadata, and render a PDF.
build_application.py does the whole chain (build -> finalize -> PDF) in one call.

SPEC SHAPE (see personal/applications/<company>/resume.json for a live example):
  {
    "name": "Firstname Lastname, M.S.",
    "contact": "City, ST  |  email  |  phone  |  linkedin",
    "level": "executive",            # executive | manager | ic | entry — drives layout
    "summary": "one paragraph",
    "competencies": ["A | B | C", "D | E | F"],          # plain lines, never a table
    "skills": [["Cloud & Warehouse:  ", "Snowflake, ..."]],
    "experience": [
      {"company": "...", "title": "...",                 # title: NO comma/slash/hyphen
       "location_dates": "City, ST | Month Year - Month Year",
       "bullets": [["bold lead-in", " rest of the bullet."]]}
    ],
    "earlier": [{"company": "...", "title": "...", "location_dates": "..."}],
    "education": [["Master of Science, Business Analytics", " - State University University (2018)"]],
    "certs": "Prior Certifications: ..."
  }

The builder VALIDATES the spec against the import rules and prints warnings for
anything that would parse badly (punctuation in a title, a malformed location
line, a leftover placeholder). Warnings do not block the build — they surface the
risk so you fix the spec, not the generated file.
"""

import json
import re
import sys
from itertools import pairwise

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

from docx_common import BODY_FONT, BRAND_BLUE, scan_placeholders
from docx_common import run as _run

PAGE_USABLE_IN = 7.3  # 8.5" Letter minus 0.6" left + 0.6" right margins

# ---- layout by target level (resume-style-rules.md §3a) --------------------------
# Executive-resume practice puts a compact Core Competencies keyword grid right under
# the summary: it is ATS-indexed and orients a human in ~10 seconds. ATS guidance
# counters that skills are validated against work history and that senior candidates
# should lead with the track record. Both are satisfied by keeping the SHORT competency
# grid high and moving the LONG tool list relative to experience by level.
#
# Early career inverts the whole thing: with a thin work history the degree is the
# strongest credential, so education leads and the page target drops to one.
#
# Each level sets the section order plus the format defaults that travel with it.
LEVELS = {
    # Director / Head-of / VP / C-suite: the record is the pitch; tools support it.
    "executive": {
        "order": ("competencies", "experience", "skills", "education"),
        "pages": 2,
        "competency_columns": 2,
    },
    # Manager / lead / player-coach: tools matter to the screen but don't outrank scope.
    "manager": {
        "order": ("competencies", "skills", "experience", "education"),
        "pages": 2,
        "competency_columns": 2,
    },
    # Senior IC / staff / hands-on: the exact-tool match IS the screen.
    "ic": {
        "order": ("skills", "competencies", "experience", "education"),
        "pages": 2,
        "competency_columns": 3,
    },
    # Early career (roughly 0-3 years): education leads because it is the strongest
    # credential, skills next, experience after. One page. A "Core Competencies"
    # leadership grid is usually inappropriate here — omit `competencies` entirely
    # and the section simply doesn't render.
    "entry": {
        "order": ("education", "skills", "competencies", "experience"),
        "pages": 1,
        "competency_columns": 3,
    },
}
DEFAULT_LEVEL = "executive"

# Back-compat alias: the order tuples on their own.
SECTION_ORDERS = {k: v["order"] for k, v in LEVELS.items()}


def level_config(spec):
    """The layout settings for a spec's level, falling back to the default."""
    return LEVELS.get(spec.get("level", DEFAULT_LEVEL), LEVELS[DEFAULT_LEVEL])


# ---- validation against the ATS import rules (resume-style-rules.md §9) ----
_TITLE_BAD = re.compile(r"[,/]| - ")  # comma, slash, or spaced hyphen truncates titles
_LOC_OK = re.compile(r"^.+,\s*[A-Z]{2}\s*\|\s*.+$")  # "City, ST | dates"

_MONTHS = {
    m: i
    for i, m in enumerate(
        (
            "january february march april may june july august september october november december"
        ).split(),
        start=1,
    )
}


def _end_key(location_dates):
    """A sortable (year, month) key for the END of a role's date range, or None if
    unparseable. 'Present' sorts as most-recent. Reads the text after the last '|'
    and the right side of the en-dash: 'City, ST | May 2019 – June 2022' -> (2022, 6)."""
    seg = str(location_dates or "").split("|")[-1]
    end = re.split(r"\s[–—-]\s", seg)[-1].strip()  # right of the date-range dash
    if not end:
        return None
    if "present" in end.lower():
        return (9999, 99)  # current role — most recent
    m = re.search(r"([A-Za-z]+)\s+(\d{4})", end)  # "June 2022"
    if m:
        return (int(m.group(2)), _MONTHS.get(m.group(1).lower(), 0))
    y = re.search(r"\b(\d{4})\b", end)  # bare year fallback
    return (int(y.group(1)), 0) if y else None


def _entry_end(entry):
    """The most-recent end date across an experience entry's role(s)."""
    roles = entry.get("roles") or [entry]
    keys = [k for k in (_end_key(r.get("location_dates")) for r in roles) if k]
    return max(keys) if keys else None


def _all_roles(spec):
    """Flatten experience entries — including stacked sub-roles under one employer —
    plus earlier roles, for validation."""
    roles: list[dict] = []
    for e in spec.get("experience", []):
        roles.extend(e["roles"] if e.get("roles") else [e])
    roles.extend(spec.get("advisory", []))
    roles.extend(spec.get("earlier", []))
    return roles


def validate(spec):
    warns = []
    for role in _all_roles(spec):
        t = role.get("title", "")
        if _TITLE_BAD.search(t):
            warns.append(
                f"title has punctuation that can truncate on import: {t!r} "
                f"(join with 'and', drop the comma/slash/hyphen)"
            )
        ld = role.get("location_dates", "")
        if not _LOC_OK.match(ld):
            warns.append(f"location/date line is not 'City, ST | dates': {ld!r}")
    for m in sorted(scan_placeholders(spec)):
        warns.append(f"unresolved placeholder in spec text: {m!r}")

    lvl = spec.get("level", DEFAULT_LEVEL)
    if lvl not in LEVELS:
        warns.append(
            f"unknown level {lvl!r} — layout fell back to {DEFAULT_LEVEL!r}; "
            f"use one of {sorted(LEVELS)}"
        )
    elif lvl == "entry" and spec.get("competencies"):
        warns.append(
            "level 'entry' with a Core Competencies grid — that block is an executive "
            "device and reads as padding on an early-career résumé; consider dropping it"
        )

    # Reverse-chronological order: each experience entry must be at least as recent
    # as the one after it, and stacked sub-roles must descend within an employer.
    experience = spec.get("experience", [])
    prev_co, prev_end = None, None
    for e in experience:
        end = _entry_end(e)
        co = e.get("company", "?")
        if prev_end is not None and end is not None and end > prev_end:
            warns.append(
                f"experience is out of reverse-chronological order: {co!r} is more "
                f"recent than {prev_co!r} but is listed after it"
            )
        prev_co, prev_end = co, end
    for e in experience:
        roles = e.get("roles")
        if roles:
            keys = [_end_key(r.get("location_dates")) for r in roles]
            for a, b in pairwise(keys):
                if a is not None and b is not None and b > a:
                    warns.append(
                        f"stacked roles under {e.get('company', '?')!r} are out of "
                        f"reverse-chronological order"
                    )
                    break
    return warns


# ---- rendering helpers ----------------------------------------------------------
def _setup(d):
    for s in d.sections:
        s.top_margin = s.bottom_margin = Inches(0.5)
        s.left_margin = s.right_margin = Inches(0.6)
    st = d.styles["Normal"]
    st.font.name = BODY_FONT
    st.font.size = Pt(10.5)
    st.paragraph_format.space_after = Pt(0)
    st.paragraph_format.space_before = Pt(0)
    st.paragraph_format.line_spacing = 1.0


def _para(d, before=0, after=0, align=None):
    p = d.add_paragraph()
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    if align:
        p.alignment = align
    return p


def _section(d, text):
    p = _para(d, before=9, after=2)
    _run(p, text, bold=True, size=12, color=BRAND_BLUE)
    pPr = p._p.get_or_add_pPr()
    pbdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    for k, v in (("w:val", "single"), ("w:sz", "6"), ("w:space", "1"), ("w:color", "0072B2")):
        bottom.set(qn(k), v)
    pbdr.append(bottom)
    pPr.append(pbdr)


def _bullet(d, lead, rest):
    p = _para(d, before=1, after=1)
    p.paragraph_format.left_indent = Inches(0.18)
    p.paragraph_format.first_line_indent = Inches(-0.18)
    _run(p, "•  ")
    _run(p, lead, bold=True)
    _run(p, rest)


def _competencies(d, comp_lines, columns=2):
    """Render competencies as tab-stop-aligned columns so they line up cleanly.

    Accepts either a flat list of items or the older `"A | B | C"` line format —
    any '|' is split out — so items always align regardless of how the spec is
    written. Tabs are plain whitespace in the text stream, so this stays ATS-safe
    (unlike a real table, which is why we don't use one)."""
    items: list[str] = []
    for line in comp_lines:
        items.extend(x.strip() for x in line.split("|") if x.strip())
    colw = PAGE_USABLE_IN / columns
    for i in range(0, len(items), columns):
        row = items[i : i + columns]
        p = _para(d, before=2)
        stops = p.paragraph_format.tab_stops
        for c in range(1, columns):
            stops.add_tab_stop(Inches(round(colw * c, 3)), WD_TAB_ALIGNMENT.LEFT)
        _run(p, "\t".join(row))


def build_resume(spec, out_path):
    """Render the spec to out_path. Returns the list of validation warnings."""
    warns = validate(spec)
    d = docx.Document()
    _setup(d)

    # Header
    p = _para(d, after=1, align=WD_ALIGN_PARAGRAPH.CENTER)
    _run(p, spec["name"], bold=True, size=19, color=BRAND_BLUE)
    p = _para(d, after=2, align=WD_ALIGN_PARAGRAPH.CENTER)
    _run(p, spec["contact"], size=10)

    # Summary
    _section(d, "Professional Summary")
    p = _para(d, before=2)
    _run(p, spec["summary"])

    cfg = level_config(spec)

    def _emit_competencies():
        """Core Competencies (tab-aligned columns — NOT a table). Omit the key
        entirely at entry level; a leadership grid reads wrong on a new-grad résumé."""
        if spec.get("competencies"):
            _section(d, "Core Competencies")
            cols = spec.get("competency_columns", cfg["competency_columns"])
            _competencies(d, spec["competencies"], cols)

    def _emit_skills():
        if spec.get("skills"):
            _section(d, "Technical Skills")
            for label, rest in spec["skills"]:
                p = _para(d, before=1)
                _run(p, label, bold=True)
                _run(p, rest)

    def _emit_experience():
        """An entry is either a single role {company, title, location_dates, bullets}
        or one employer with stacked sub-roles {company, roles: [...]} — the latter
        shows promotion history under one company header."""
        _section(d, "Professional Experience")

        def _role_block(title, location_dates, bullets, before):
            _run(_para(d, before=before), title, bold=True)
            _run(_para(d, after=1), location_dates)
            for lead, rest in bullets:
                _bullet(d, lead, rest)

        for entry in spec["experience"]:
            _run(_para(d, before=6), entry["company"], bold=True, size=11)
            if entry.get("roles"):
                for i, r in enumerate(entry["roles"]):
                    _role_block(r["title"], r["location_dates"], r["bullets"], before=3 if i else 0)
            else:
                _role_block(entry["title"], entry["location_dates"], entry["bullets"], before=0)

        # Older roles live in the SAME section now, not a separate "Earlier
        # Experience" block (changed 2026-07-22). They are the oldest entries, so
        # reverse-chron puts them last, and folding them in drops one of the three
        # experience-like sections a résumé parser has to segment — one suspect in
        # the Workday import dropping the current role entirely. Same block format
        # as any other entry; a bullet is optional and usually absent for old roles.
        for role in spec.get("earlier", []):
            _run(_para(d, before=6), role["company"], bold=True, size=11)
            bullets = [["", role["bullet"]]] if role.get("bullet") else []
            _role_block(role["title"], role["location_dates"], bullets, before=0)

    def _emit_education():
        if spec.get("education") or spec.get("certs"):
            _section(d, "Education & Certifications")
            for i, (bold_part, rest) in enumerate(spec.get("education", [])):
                p = _para(d, before=2 if i == 0 else 0)
                _run(p, bold_part, bold=True)
                _run(p, rest)
            if spec.get("certs"):
                label, _, rest = spec["certs"].partition(":")
                p = _para(d)
                _run(p, label + ":", bold=True)
                _run(p, rest)

    # Section order is level-dependent (resume-style-rules.md §3a). The competency
    # keyword grid sits above experience at every level — compact, ATS-indexed, orients
    # a reader in ten seconds. What MOVES is the tool list and education: at executive
    # level the track record is the pitch so tools follow experience; for hands-on roles
    # the exact-tool match is the screen; and early-career inverts the whole thing,
    # leading with the degree because it is the strongest credential on a thin history.
    emit = {
        "competencies": _emit_competencies,
        "skills": _emit_skills,
        "experience": _emit_experience,
        "education": _emit_education,
    }
    for part in cfg["order"]:
        emit[part]()
        if part == "experience" and spec.get("advisory"):
            # Concurrent fractional / advisory work lives in its OWN section, out of
            # the main reverse-chron timeline. Two reasons, one craft and one
            # mechanical: it is the conventional way to show work that overlaps a
            # primary role, and it keeps an entry whose dates sit inside the current
            # job's window from being folded into that job by a résumé parser
            # (observed on Workday, 2026-07-22 — the merge that a relabel could not
            # fix, because the trigger was the date overlap, not the company name).
            _section(d, "Advisory & Consulting")
            for entry in spec["advisory"]:
                _run(_para(d, before=6), entry["company"], bold=True, size=11)
                _run(_para(d), entry["title"], bold=True)
                _run(_para(d, after=1), entry["location_dates"])
                for lead, rest in entry.get("bullets", []):
                    _bullet(d, lead, rest)
    d.save(out_path)
    return warns


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: python resume_builder.py <spec.json> <out.docx>")
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    warns = build_resume(spec, sys.argv[2])
    print(f"built {sys.argv[2]}  (tables: 0)")
    if warns:
        print("\n  ⚠ spec warnings (fix the spec, not the docx):")
        for w in warns:
            print("   -", w)
    else:
        print("  ✓ spec passes ATS import checks")


if __name__ == "__main__":
    main()

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
import os
import re
import sys
from itertools import pairwise

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

import _paths  # noqa: F401  (side-effect: repo root on sys.path)
import config
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
TRACKED_TOOLS = (
    # Distinctive, employer-identifying tools. A generic word like "sql" or "python"
    # is everywhere and would only produce noise, so the list stays deliberately short.
    "snowflake",
    "bigquery",
    "redshift",
    "databricks",
    "synapse",
    "azure",
    "quantexa",
    "sigma",
    "metabase",
    "looker",
    "power bi",
    "thoughtspot",
    "fivetran",
    "airflow",
    "astronomer",
    "talend",
    "informatica",
    "elementary",
    "atlan",
    "dataiku",
    "dremio",
    "stripe",
    "cursor",
    "copilot",
    "rovo",
)

_TITLE_BAD = re.compile(r"[,/]| - ")  # comma, slash, or spaced hyphen truncates titles
_LOC_OK = re.compile(r"^.+,\s*[A-Z]{2}\s*\|\s*.+$")  # "City, ST | dates"
# A bullet continuation that opens with a colon, semicolon or dash. Space and comma
# are the house shape and are deliberately absent from this class.
_BULLET_SEP = re.compile(r"^\s*([:;]|[-–—]\s)")

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
    plus earlier roles, for validation.

    Stacked sub-roles carry no `company` of their own; it lives on the parent. So
    sub-roles are returned as shallow COPIES with the employer filled in, which is
    what lets a warning name the company instead of reporting '?'. Copies, not
    mutation: these are validation views, and writing a synthetic key back into the
    spec would risk it reaching the rendered document.

    Read-only by contract. Callers must not mutate what they get back.
    """
    roles: list[dict] = []
    for e in spec.get("experience", []):
        if e.get("roles"):
            roles.extend(
                {**r, "company": r.get("company") or e.get("company", "?")} for r in e["roles"]
            )
        else:
            roles.append(e)
    roles.extend(spec.get("advisory", []))
    roles.extend(spec.get("earlier", []))
    return roles


# Activity claims that are employer-SPECIFIC and material enough to be checked.
# Each entry is a synonym group: if a bullet uses any word in the group, the
# profile's section for that employer must evidence at least one word from it.
# Kept short and material on purpose — policing ordinary verbs would produce
# noise, and a gate with false positives gets switched off.
TRACKED_CLAIMS = {
    "hiring": ("hire", "hired", "hiring", "recruit", "recruited", "backfill", "staffed up"),
    "budget ownership": ("budget", "p&l", "spend under management"),
    "managing managers": ("managing managers", "manage managers", "through team leads"),
    "on-call / production duty": ("on-call", "on call", "pager"),
    "patents / publications": ("patent", "published paper", "peer-reviewed"),
    # Added after an access-governance claim entered a document unflagged: none of
    # its words were tracked, so the ledger had nothing to verify. A capability that
    # is true at one employer and not another is exactly what this list is for.
    "access governance": (
        "role-based access",
        "rbac",
        "least privilege",
        "access review",
        "need-to-know",
        "entitlement",
    ),
    "audit / compliance attestation": (
        "soc 2",
        "soc2",
        "iso 27001",
        "internal audit",
        "compliance audit",
    ),
}


def employer_claim_warnings(spec, profile_text=None):
    """Flag a tool named in one employer's bullets that the profile does not put there.

    WHY THIS EXISTS: a bullet once named a warehouse product under an employer whose
    profile tool line does not list it. The claim was also gratuitous — the product is
    genuinely on the record at OTHER employers — so nothing was gained by borrowing it
    into the wrong one. Misattributing a tool to a SPECIFIC employer
    is the kind of error a reference check or one pointed interview question exposes,
    and it is invisible to every other check we run: the résumé still parses, still
    scores, and the tool is real *somewhere* on the record.

    The profile is the authority, never a hardcoded list, so this stays correct as the
    record grows. A tool the profile does not associate with ANY employer is left alone
    — that is the no-fabrication rule's job, not this one.
    """
    if profile_text is None:
        path = getattr(config, "PROFILE_MD", None)
        if not path or not os.path.exists(path):
            return []  # no profile to check against; silence beats a false alarm
        with open(path, encoding="utf-8") as fh:
            profile_text = fh.read()

    # Per-employer tool truth: the profile's "Skills/tools:" line under each employer
    # heading, which is where the record states what was used where.
    sections: dict[str, list[str]] = {}
    current = None
    for line in profile_text.splitlines():
        head = re.match(r"^#{2,4}\s+([A-Z][^—\-\n]{2,60})", line)
        if head:
            current = head.group(1).strip().rstrip(" —-").lower()
            sections.setdefault(current, [])
        elif current is not None:
            sections[current].append(line)

    def tools_for(company):
        """The profile's tool vocabulary for one employer, if it names one."""
        key = next((k for k in sections if company.lower().split()[0] in k), None)
        if key is None:
            return None
        body = "\n".join(sections[key]).lower()
        return body if "skills/tools:" in body else None

    warns = []
    for entry in spec.get("experience", []) + spec.get("advisory", []):
        company = entry.get("company") or ""
        body = tools_for(company)
        if not body:
            continue  # employer not found in the profile, or no tool line to check
        roles = entry.get("roles") or [entry]
        for role in roles:
            for bullet in role.get("bullets", []):
                text = " ".join(bullet).lower()
                for tool in TRACKED_TOOLS:
                    if tool in text and tool not in body:
                        warns.append(
                            f"{company}: bullet names {tool!r}, which the profile does not "
                            f"list under that employer — verify before sending"
                        )
                # Same test, applied to activity claims rather than tool names.
                # A tool check alone missed a bullet claiming hiring at an employer
                # whose teams the profile describes as standing and largely
                # offshore: the wrong CLAIM, not the wrong tool.
                for label, synonyms in TRACKED_CLAIMS.items():
                    if any(s in text for s in synonyms) and not any(s in body for s in synonyms):
                        warns.append(
                            f"{company}: bullet claims {label}, which the profile does not "
                            f"evidence under that employer — verify before sending"
                        )
    return sorted(set(warns))


def document_banned_warnings(spec, profile_text=None):
    """Flag wording the profile marks as true-but-not-for-a-document.

    WHY THIS EXISTS: some facts are real and still wrong to print. The first one
    was a per-case saving whose SAMPLE SIZE was never recorded. Set beside a department headcount it reads as the return on the
    whole rollout, which nobody measured. It reached finished documents twice.
    The prose guidance in the profile said to hedge it ("documented cases of"),
    and hedging is exactly what failed — a qualifier does not repair a number
    whose denominator is unknown, it just lengthens the sentence while the reader
    goes on inferring scale.

    So the profile gets to ban a phrase outright, in a line the machine reads:

        ⛔ DOCUMENT-BANNED: <phrase> | <variant> | <spelled-out variant>

    Everything after the colon is a pipe-separated list of substrings, matched
    case-insensitively against every rendered string in the spec. The profile
    stays the authority — banning something new is one line there, not a code
    change — which is the same principle employer_claim_warnings runs on.
    """
    if profile_text is None:
        path = getattr(config, "PROFILE_MD", None)
        if not path or not os.path.exists(path):
            return []  # no profile to check against; silence beats a false alarm
        with open(path, encoding="utf-8") as fh:
            profile_text = fh.read()

    banned: list[str] = []
    for line in profile_text.splitlines():
        m = re.search(r"DOCUMENT-BANNED:(.+)$", line)
        if m:
            banned += [p.strip().lower() for p in m.group(1).split("|") if p.strip()]
    if not banned:
        return []

    def strings(obj):
        if isinstance(obj, str):
            yield obj
        elif isinstance(obj, list):
            for x in obj:
                yield from strings(x)
        elif isinstance(obj, dict):
            for v in obj.values():
                yield from strings(v)

    warns = []
    for text in strings(spec):
        low = text.lower()
        for phrase in banned:
            if phrase in low:
                warns.append(
                    f"DOCUMENT-BANNED phrase {phrase!r} appears in the spec — the profile "
                    f"marks this as interview-only; remove it"
                )
    return sorted(set(warns))


def validate(spec):
    warns = []
    warns.extend(employer_claim_warnings(spec))
    warns.extend(document_banned_warnings(spec))
    # The figure allowlist. Imported lazily for the same reason as the ledger
    # below: it reads the gitignored profile directory, which CI does not have.
    try:
        import metric_registry

        warns.extend(metric_registry.warnings(spec))
    except Exception:  # noqa: S110 — a missing registry must not block a build
        pass
    # The ledger of facts already verified per employer. Imported lazily: it reads
    # the gitignored profile directory, and validate() must still work in CI where
    # that does not exist.
    try:
        import bullet_library

        for row in bullet_library.unverified(spec):
            warns.append(
                f"{row['company']}: bullet asserts {', '.join(row['new_tokens'])}, "
                f"not yet verified for that employer — check career-profile.md, then "
                f"`python engine/bullet_library.py --approve <spec>`"
            )
    except Exception as exc:
        # A ledger problem must never block a document build. The ledger is a
        # convenience layer over the profile, not the source of truth, and it is
        # absent by design in CI, where personal/ does not exist. Reported, not
        # raised: silence here would look like "nothing to verify".
        warns.append(f"bullet ledger unavailable ({type(exc).__name__}) — phrasings unchecked")
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
        # The bold lead-in and the rest are ONE SENTENCE, so the continuation starts
        # with a space or a comma. A colon, semicolon or dash turns the lead-in into a
        # label with an explanation hanging off it, and mixing the two shapes inside one
        # document is visible to a reader before they have read a word of the content.
        #
        # Measured before being enforced rather than asserted: across a real portfolio the
        # sentence shape was already overwhelmingly dominant, so the outliers were drift
        # rather than a competing house style. This pins what was already true.
        #
        # WARNS RATHER THAN REWRITING, for the same reason as the missing-line rule:
        # deleting a colon leaves ungrammatical text ("...how it moves a stewardship
        # model..."), so the fix is to rewrite the sentence, which is authorial work.
        for lead, rest in role.get("bullets", []) or []:
            sep = _BULLET_SEP.match(str(rest))
            if sep:
                warns.append(
                    f"bullet continuation starts with {sep.group(1)!r} — the lead-in and the "
                    f"rest are one sentence, so it should read on with a space or a comma. "
                    f"Rewrite rather than deleting the punctuation: {str(lead)[:44]!r}"
                )
        # Every role should carry at least one line. A bare title-and-dates entry
        # reads as filler to a human and gives an ATS nothing to match on, so the
        # tenure it was added to prove is the only thing it contributes.
        #
        # WARNS RATHER THAN FILLING THE GAP. The line has to come from
        # career-profile.md, and a builder that invented one would be fabricating —
        # the one thing this system must never do. Both honest remedies are named
        # in the message, and "fold it upward" is often the right one for an early
        # role that exists only to close a date gap.
        #
        # `earlier` entries carry a singular `bullet` string while experience and
        # advisory carry a `bullets` list; both count.
        if not (role.get("bullets") or str(role.get("bullet") or "").strip()):
            warns.append(
                f"role has no content line: {role.get('company', '?')} — {t!r}. "
                f"Add one from career-profile.md, or fold the dates into the role "
                f"above it so the entry is not carrying only a title."
            )
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


def _keep_with_next(p):
    """Bind a paragraph to the one after it so Word will not break between them.

    A company name stranded at the foot of one page with its title, dates and
    bullets on the next reads as two different employers, and the reader has to
    turn back to work out whose job they are looking at. Chaining company ->
    title -> dates means the header always arrives with at least its first
    bullet, and Word pushes the whole block over instead.
    """
    p.paragraph_format.keep_with_next = True
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
    _section(d, spec.get("summary_heading", "Professional Summary"))
    p = _para(d, before=2)
    _run(p, spec["summary"])

    cfg = level_config(spec)

    def _emit_competencies():
        """Core Competencies (tab-aligned columns — NOT a table). Omit the key
        entirely at entry level; a leadership grid reads wrong on a new-grad résumé."""
        if spec.get("competencies"):
            _section(d, spec.get("competencies_heading", "Core Competencies"))
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
            _run(_keep_with_next(_para(d, before=before)), title, bold=True)
            _run(_keep_with_next(_para(d, after=1)), location_dates)
            for lead, rest in bullets:
                _bullet(d, lead, rest)

        for entry in spec["experience"]:
            _run(_keep_with_next(_para(d, before=6)), entry["company"], bold=True, size=11)
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
            _run(_keep_with_next(_para(d, before=6)), role["company"], bold=True, size=11)
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
                _run(_keep_with_next(_para(d, before=6)), entry["company"], bold=True, size=11)
                _run(_keep_with_next(_para(d)), entry["title"], bold=True)
                _run(_keep_with_next(_para(d, after=1)), entry["location_dates"])
                for lead, rest in entry.get("bullets", []):
                    _bullet(d, lead, rest)
        if part == "experience" and spec.get("projects"):
            # Selected work that is not employment: open source, a public artifact
            # someone can actually open. Rendered as short prose rather than
            # bullets, because a project earns attention by what it IS, and a
            # reader skimming bullets cannot tell a weekend script from a system
            # with users.
            #
            # A URL is printed as plain visible text, never a hyperlink field:
            # parsers routinely keep the field and drop its display text, and
            # visible characters survive a .docx, a PDF, and a pasted plain-text
            # box alike.
            _section(d, spec.get("projects_heading", "Selected Projects & Open Source"))
            for proj in spec["projects"]:
                para = _para(d, before=6, after=0)
                _run(para, proj["name"], bold=True, size=11)
                if proj.get("meta"):
                    _run(para, "   " + proj["meta"], size=9.5)
                if proj.get("url"):
                    _run(_para(d, after=1), proj["url"], size=9.5)
                _run(_para(d, after=2), proj["summary"])
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

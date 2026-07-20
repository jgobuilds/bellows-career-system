#!/usr/bin/env python3
"""
build_application.py — build a full application (resume + cover letter) for one
company from JSON specs, in a single command.

Replaces the per-application throwaway scripts. Put the CONTENT in the folder:
  personal/applications/<company>/resume.json    (resume_builder.py spec)
  personal/applications/<company>/cover.json     (cover_builder.py spec, optional)
then run:
  python engine/build_application.py personal/applications/<company>

It does the whole chain that used to be hand-typed each time:
  1. build the raw .docx from each spec (resume_builder / cover_builder)
  2. scrub metadata (docx_finalize) into the human filename
  3. render a text-selectable .pdf via Word and report the page count
  4. run the pre-send placeholder scan and surface any spec warnings

Output lands as "<Name> - Resume.docx/.pdf" and "<Name> - Cover Letter.docx/.pdf"
in the same folder (company lives in the folder, never the filename — §6).
"""

import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
import json

import _paths  # noqa: F401  (adds repo root to sys.path)
import config
import cover_builder
import docx_finalize
import resume_builder

AUTHOR = config.LEGAL_NAME  # document metadata author (from personal/userconfig.py)


def _render_pdf(docx_path, pdf_path):
    """Render docx -> pdf via Word and return the page count (or None on failure).

    Prefers in-process win32com (fast, no shell); falls back to a PowerShell +
    Word invocation where pywin32 isn't installed. Word needs absolute paths.
    """
    docx_path = os.path.abspath(docx_path)
    pdf_path = os.path.abspath(pdf_path)

    try:
        import win32com.client  # pywin32
    except ImportError:
        return _render_pdf_powershell(docx_path, pdf_path)

    WD_PDF, WD_STAT_PAGES = 17, 2
    word = None
    try:
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        doc = word.Documents.Open(docx_path, False, True)  # (path, ConfirmConversions, ReadOnly)
        doc.SaveAs2(pdf_path, WD_PDF)
        pages = int(doc.ComputeStatistics(WD_STAT_PAGES))
        doc.Close(False)
        return pages
    except Exception as e:
        print(f"   ! PDF render failed ({e}); is the file open in Word?")
        return None
    finally:
        if word is not None:
            word.Quit()


def _render_pdf_powershell(docx_path, pdf_path):
    # Escape single quotes for PowerShell single-quoted strings ('' == one ') so a
    # path with an apostrophe (e.g. O'Brien) can't break — or inject into — the command.
    dq = docx_path.replace("'", "''")
    pq = pdf_path.replace("'", "''")
    ps = (
        f"$w = New-Object -ComObject Word.Application; $w.Visible=$false; "
        f"try {{ $d = $w.Documents.Open('{dq}', $false, $true); "
        f"$d.SaveAs2('{pq}', 17); Write-Output $d.ComputeStatistics(2); "
        f"$d.Close($false) }} finally {{ $w.Quit() }}"
    )
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True,
            text=True,
            timeout=180,
        )
        digits = [ln.strip() for ln in out.stdout.splitlines() if ln.strip().isdigit()]
        return int(digits[-1]) if digits else None
    except Exception as e:
        print(f"   ! PDF render failed ({e}); is the file open in Word?")
        return None


def _build_one(spec_path, out_docx, builder):
    spec = json.load(open(spec_path, encoding="utf-8"))
    raw = out_docx + ".raw.docx"
    warns = builder(spec, raw)
    try:
        docx_finalize.finalize(raw, out_docx, author=AUTHOR)
    except PermissionError:
        os.replace(raw, out_docx + ".NEW")
        print(
            f"   ! {os.path.basename(out_docx)} is open in Word — wrote {os.path.basename(out_docx)}.NEW instead; "
            f"close Word and rename it."
        )
        return warns, None
    if os.path.exists(raw):
        os.remove(raw)
    pdf = os.path.splitext(out_docx)[0] + ".pdf"
    pages = _render_pdf(out_docx, pdf)
    return warns, pages


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python build_application.py <application-folder> [Name]")
    folder = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else config.NAME
    if not os.path.isdir(folder):  # accept a repo-root-relative folder too
        cand = os.path.join(os.path.dirname(_HERE), folder)
        if os.path.isdir(cand):
            folder = cand
        else:
            sys.exit(f"not a folder: {folder}")

    jobs = [
        ("resume.json", f"{name} - Resume.docx", resume_builder.build_resume),
        ("cover.json", f"{name} - Cover Letter.docx", cover_builder.build_cover),
    ]
    any_built = False
    for spec_name, out_name, builder in jobs:
        spec_path = os.path.join(folder, spec_name)
        if not os.path.exists(spec_path):
            continue
        any_built = True
        out_docx = os.path.join(folder, out_name)
        warns, pages = _build_one(spec_path, out_docx, builder)
        tag = f"{pages} pages" if pages else "PDF not rendered"
        print(f"✓ {out_name}  ({tag})")
        for w in warns:
            print("   ⚠", w)
    if not any_built:
        sys.exit(f"no resume.json or cover.json found in {folder}")
    print("\nDone. Review both files, then submit yourself — nothing is auto-submitted.")


if __name__ == "__main__":
    main()

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
        # FALL BACK RATHER THAN GIVE UP. In-process COM is the fast path, not the only
        # one, and it fails for reasons that have nothing to do with the document: a
        # wedged Word server answers "Call was rejected by callee", and a half-resolved
        # type library answers "Open.SaveAs2" - both while a fresh out-of-process Word
        # renders the same file without complaint.
        #
        # This fallback already existed and was reachable ONLY on ImportError, so it
        # could not help in the one situation it was written for. An optimisation that
        # fails should degrade to the working path, not to no PDF at all.
        print(f"   ! in-process render failed ({e}); retrying via a fresh Word process")
        pages = _render_pdf_powershell(docx_path, pdf_path)
        if pages is None:
            print("   ! PDF still not rendered; is the file open in Word?")
        return pages
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

    # LinkedIn is checked HERE, at the moment a résumé exists and before anyone sends it.
    # It does two jobs that both fail silently: it generates the inbound (a profile that
    # does not say what you now do is invisible to the recruiters searching for it, and
    # nothing tells you about the leads you did not get), and it is where this document
    # gets verified. A recruiter reading the résumé will open the profile, and any
    # disagreement on employer, title or dates reads as a discrepancy rather than a stale
    # page. So the résumé is not finished until the profile it will be checked against
    # agrees with it.
    try:
        import linkedin_check

        resume_spec = None
        rj = os.path.join(folder, "resume.json")
        if os.path.exists(rj):
            with open(rj, encoding="utf-8") as fh:
                resume_spec = json.load(fh)
        li = linkedin_check.check(resume_spec)
        if li:
            print("\n⚠ LinkedIn — fix before you apply:")
            for w in li:
                print("   ⚠", w)
            print("   Run `python engine/linkedin_check.py` for the detail.")
    except Exception as e:  # never block a build over the profile check
        print(f"\n(LinkedIn check skipped: {e})")

    # SELECTION, not quality. Every other check here asks whether what is on the page
    # is good; this one asks whether it is the right thing. They are different failures:
    # a bullet can be true, verified in the bullet library, inside the metric registry
    # and score well, and still be the wrong accomplishment for the posting. That is not
    # hypothetical — a vendor-negotiation bullet survived onto a data-engineering résumé
    # through four rounds while a medallion build on the posting's own stack sat unused.
    # Runs only when a jd.txt was saved, which is itself the nudge to save one: without
    # the posting the selection cannot be re-checked later, or by anyone else.
    rj = os.path.join(folder, "resume.json")
    jd = os.path.join(folder, "jd.txt")
    if os.path.exists(rj):
        if os.path.exists(jd):
            try:
                import resume_coverage

                with open(jd, encoding="utf-8") as fh:
                    print("\n— selection check —")
                    resume_coverage.report(rj, fh.read(), top=4)
            except Exception as e:  # advisory: never block a build over relevance
                print(f"\n(selection check skipped: {e})")
        else:
            print("\n○ No jd.txt in this folder — selection was not checked.")
            print("   Save the posting text there to see what the profile still has unused.")

    print("\nDone. Review both files, then submit yourself — nothing is auto-submitted.")


if __name__ == "__main__":
    main()

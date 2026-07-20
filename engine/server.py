#!/usr/bin/env python3
"""
server.py — the local app server for the Career Hub and pipeline board.

WHY THIS EXISTS:
  A page opened as a file:// can't launch a program on your computer or save
  changes (browsers sandbox that). This tiny local helper can. Run it once and it
  (a) serves the Career Hub (hub.html) over
  http://localhost so the buttons work same-origin, (b) runs jobspy_sweep.py when
  "Run lead sweep" is clicked, and (c) exposes the /api endpoints the pages use
  (jobs, status, set-status, set-voice, run). It reads personal/data/jobs.json.

RUN:
  python server.py
  # it prints a URL and opens it. Click "Run lead sweep" -> "Run sweep now".
  # Ctrl+C to stop.

SAFETY:
  Binds to 127.0.0.1 only — nothing is exposed to your network. It only runs the
  local jobspy_sweep.py; it never applies to anything. Requires: python-jobspy
  (pip install -U python-jobspy) for the sweep itself. Stdlib-only otherwise.
"""

import csv
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import quote

import _paths  # noqa: F401  (side-effect: adds repo root to sys.path for `import config`)
import config  # file paths (all under personal/) + the shared dashboard shell in engine/

PORT = int(os.environ.get("SWEEP_PORT", "8765"))


def _resolve_cli(name):
    """Find a CLI even when it isn't on PATH. For 'claude', fall back to the
    version-pinned binary that Claude Desktop bundles (newest install wins), so
    the Hub's 'Run here' works without the user editing their PATH."""
    p = shutil.which(name)
    if p:
        return p
    if name == "claude":
        import glob

        base = os.path.join(
            os.environ.get("LOCALAPPDATA", ""),
            "Packages",
            "Claude_pzs8sxrjxfjjc",
            "LocalCache",
            "Roaming",
            "Claude",
            "claude-code",
        )
        cands = glob.glob(os.path.join(base, "*", "claude.exe"))
        if cands:
            cands.sort(key=lambda c: os.path.getmtime(c), reverse=True)  # newest install
            return cands[0]
    return None


CLAUDE_BIN = _resolve_cli("claude")
GEMINI_BIN = _resolve_cli("gemini")

BANNER = r"""
    ____       ____
   / __ )___  / / /___ _      _______
  / __  / _ \/ / / __ \ | /| / / ___/
 / /_/ /  __/ / / /_/ / |/ |/ (__  )
/_____/\___/_/_/\____/|__/|__/____/
"""
TAGLINE = "It doesn't make the fire. It makes yours hotter."


def _enable_ansi():
    """Best-effort: turn on ANSI/VT color in the terminal. True if color is safe."""
    if not sys.stdout.isatty():
        return False
    if os.name != "nt":
        return True
    try:  # Windows 10+: flip ENABLE_VIRTUAL_TERMINAL_PROCESSING on the console
        import ctypes

        # windll is Windows-only (guarded by os.name above); getattr avoids the
        # attr-defined error Linux mypy raises for `ctypes.windll`. B009 wants direct
        # access, but that's exactly what breaks cross-platform mypy here.
        k = getattr(ctypes, "windll").kernel32  # noqa: B009
        mode = ctypes.c_uint()
        h = k.GetStdHandle(-11)
        if not k.GetConsoleMode(h, ctypes.byref(mode)):
            return False
        k.SetConsoleMode(h, mode.value | 0x0004)
        return True
    except Exception:
        return False


def paint_banner():
    """The wordmark in the brand orange - one word, one colour, matching the Hub
    and the SVG - or plain text if the terminal can't do colour (degrades cleanly,
    never prints escape garbage)."""
    if not _enable_ansi():
        return BANNER + "  " + TAGLINE + "\n"
    r, g, b = 230, 159, 0  # #E69F00 - the brand orange (a bellows feeds the fire)
    out = []
    for line in BANNER.strip("\n").split("\n"):
        s = "".join(ch if ch == " " else f"\x1b[1;38;2;{r};{g};{b}m{ch}" for ch in line)
        out.append(s + "\x1b[0m")
    tag = "\x1b[3;38;2;230;159;0m  " + TAGLINE + "\x1b[0m"
    return "\n" + "\n".join(out) + "\n" + tag + "\n"


HERE = os.path.dirname(os.path.abspath(__file__))  # where the tool scripts live
# repo root = parent when we live in engine/, else HERE (tolerates a flat layout too)
ROOT = os.path.dirname(HERE) if os.path.basename(HERE) == "engine" else HERE
RUN_LOCK = threading.Lock()


def count_rows(path):
    if not os.path.exists(path):
        return 0
    with open(path, encoding="utf-8", errors="ignore") as fh:
        return max(0, sum(1 for _ in csv.reader(fh)) - 1)


# ---------------------------------------------------------------------------
# Status write-back: pipeline.md is the SOURCE OF TRUTH, the dashboard is its
# view. So a status change writes BOTH - the pipeline row, and the dashboard's
# embedded JOBS entry so the change survives a reload.
# ---------------------------------------------------------------------------
PIPELINE = config.PIPELINE_MD
VALID_STATUS = {
    "to review",
    "tailored",
    "applied",
    "interviewing",
    "offer",
    "accepted",
    "rejected",
    "no response",
    "not applying",
    "declined",
    "response",
    "closed",
    "jd pending",
    "parked",
}
# jobs.json + pipeline.md I/O go through the repository (pipeline_store) — the one
# place that owns the datastore. SUBMITTED ("counts as applied") lives there too,
# so the dashboard's Applied stat and the pipeline.md recount can't disagree.
import pipeline_store as store
from pipeline_store import SUBMITTED, load_jobs, save_jobs
from pipeline_store import find_job as _find_job

JOBS_JSON = store.JOBS_JSON


# ---- Career Hub: progress status + voice ---------------------------------
PERSONAL_DIR = os.path.dirname(config.PROFILE_MD)  # personal/ (gitignored)
VOICES = ("supportive", "tough-love", "zen", "humorous", "analytical")
STATUS_ARTIFACTS = {
    "profile": "career-profile.md",
    "self_assessment": "self-assessment.md",
    "positioning": "positioning.md",
    "roadmap": "career-roadmap.md",
    "accountability": "accountability.md",
    "story_bank": os.path.join("interview-prep", "story-bank.md"),
    "references": "references.md",
    "writing_style": "writing-style.md",
    "reconnect": "reconnect-list.md",
    "infointerview": "informational-interviews.md",
}

# ---- Tailored documents: server-authoritative links -----------------------
# The dashboard is client-side and can't see the filesystem, so it used to link
# all three doc types unconditionally (404ing when a file was never generated)
# and built the URL itself (which broke on messy `doc` values). Instead the
# server resolves which files actually exist and hands back correctly-encoded
# hrefs, so the Hub renders ONLY links that resolve.
APPS_DIR = os.path.join(PERSONAL_DIR, "applications")
DOC_SPECS = [
    ("Résumé (PDF)", "Resume.pdf"),
    ("Résumé (DOCX)", "Resume.docx"),
    ("Cover letter", "Cover Letter.pdf"),
]


def _doc_slug(doc):
    """The folder name under personal/applications/ for a job's `doc`, tolerant of
    stray paths/slashes (e.g. 'applications/burq/' -> 'burq')."""
    if not doc:
        return ""
    return os.path.basename(str(doc).replace("\\", "/").rstrip("/"))


def job_docs(doc, prefix):
    """[{label, href}] for the tailored files that exist on disk, hrefs URL-encoded."""
    slug = _doc_slug(doc)
    if not slug:
        return []
    folder = os.path.join(APPS_DIR, slug)
    out = []
    for label, fname in DOC_SPECS:
        full = (prefix or "") + fname
        if os.path.exists(os.path.join(folder, full)):
            out.append(
                {
                    "label": label,
                    "href": "/personal/applications/" + quote(slug) + "/" + quote(full),
                }
            )
    return out


def jobs_payload():
    """load_jobs() enriched with a per-job `docs` list the dashboard renders as-is.
    Reads a fresh copy each call, so this never mutates jobs.json on disk."""
    d = load_jobs()
    prefix = d.get("resumePrefix") or ""
    for j in d.get("jobs", []):
        j["docs"] = job_docs(j.get("doc"), prefix)
    return d


def hub_status():
    import time

    arts, dates = {}, {}
    for k, rel in STATUS_ARTIFACTS.items():
        p = os.path.join(PERSONAL_DIR, rel)
        arts[k] = os.path.exists(p)
        if arts[k]:
            try:
                dates[k] = time.strftime("%Y-%m-%d", time.localtime(os.path.getmtime(p)))
            except OSError:
                pass
    jobs = load_jobs().get("jobs", [])
    return {
        "artifacts": arts,
        "artifact_dates": dates,  # {key: "YYYY-MM-DD"} last-modified, for nudges + timestamps
        "pipeline": {
            "total": len(jobs),
            "applied": sum(1 for j in jobs if (j.get("status") or "") in SUBMITTED),
            "interviewing": sum(1 for j in jobs if (j.get("status") or "") == "interviewing"),
        },
        "voice": getattr(config, "COACH_VOICE", "supportive"),
        "cli": {"claude": bool(CLAUDE_BIN), "gemini": bool(GEMINI_BIN)},
        "profile": profile_summary(),
    }


def profile_summary():
    """Small identity + targets card for the Hub banner, read from userconfig."""
    titles = getattr(config, "TARGET_TITLES", None) or []
    return {
        "name": getattr(config, "NAME", "") or "",
        "current_role": getattr(config, "CURRENT_ROLE", "") or "",
        "target_title": titles[0] if titles else "",
        "target_comp": _fmt_comp(getattr(config, "COMP_TARGET", None) or []),
        "metro": getattr(config, "HOME_METRO", "") or "",
    }


def _fmt_comp(rng):
    """[low, high] annual base -> '$250K–$265K' (skips zero/placeholder values)."""
    try:
        lo, hi = int(rng[0]), int(rng[1])
    except (TypeError, ValueError, IndexError):
        return ""

    def k(n):
        return f"${n // 1000}K" if n >= 1000 else f"${n}"

    if lo and hi:
        return f"{k(lo)}–{k(hi)}"
    return k(hi) if hi else (k(lo) if lo else "")


def set_voice(voice):
    voice = (voice or "").strip()
    if voice not in VOICES:
        raise ValueError("unknown voice '%s'" % voice)
    uc = os.path.join(PERSONAL_DIR, "userconfig.py")
    txt = open(uc, encoding="utf-8").read()
    new = re.sub(r'COACH_VOICE\s*=\s*"[^"]*"', 'COACH_VOICE = "%s"' % voice, txt)
    if new == txt:  # no existing setting — append one
        new = txt.rstrip() + '\n\nCOACH_VOICE = "%s"\n' % voice
    open(uc, "w", encoding="utf-8").write(new)
    config.COACH_VOICE = voice  # reflect in the running process
    return voice


def set_status(job_id, status):
    """Write a status change to pipeline.md + data/jobs.json."""
    status = (status or "").strip().lower()
    if status not in VALID_STATUS:
        raise ValueError(f"invalid status '{status}'")
    job_id = int(job_id)
    changed: dict[str, object] = {
        "pipeline": False,
        "dashboard": False,
        "role": None,
        "company": None,
    }

    # 1) pipeline.md - the table row for this ID (Status is the 8th cell)
    lines = store.read_pipeline()
    for i, line in enumerate(lines):
        if not line.startswith("|"):
            continue
        cells = line.rstrip("\n").split("|")
        # cells[0] is '' (leading pipe); the ID is cells[1]
        if len(cells) < 10 or cells[1].strip() != str(job_id):
            continue
        changed["role"] = cells[2].strip()
        changed["company"] = cells[3].strip()
        cells[8] = f" {status} "  # Status column
        lines[i] = "|".join(cells) + "\n"
        changed["pipeline"] = True
        break
    if changed["pipeline"]:
        # refresh the Applied count in the summary line (any submitted stage counts)
        applied = sum(
            1
            for line in lines
            if line.startswith("|")
            and len(line.split("|")) > 9
            and line.split("|")[8].strip() in SUBMITTED
        )
        for i, line in enumerate(lines):
            if line.startswith("- Added:") and "Applied:" in line:
                lines[i] = re.sub(r"Applied: \d+", f"Applied: {applied}", line)
                break
        store.write_pipeline(lines)

    # 2) jobs.json - the canonical data the dashboard reads
    d = load_jobs()
    j = _find_job(d, job_id)
    if j is not None:
        j["status"] = status
        j["applied"] = status in SUBMITTED
        if status in SUBMITTED and not j.get("applied_on"):
            j["applied_on"] = datetime.date.today().isoformat()
            changed["applied_on"] = j["applied_on"]
        save_jobs(d)
        changed["dashboard"] = True

    return changed


TRACK_FIELDS = {"recruiter", "followup", "applied_on", "ats"}


def set_field(job_id, field, value):
    """Persist a tracking field (recruiter / followup / applied_on / ats) to the
    dashboard JOBS entry. These live in the dashboard block (the live tracker)."""
    job_id = int(job_id)
    field = (field or "").strip()
    if field not in TRACK_FIELDS:
        raise ValueError(f"unknown field '{field}'")
    d = load_jobs()
    j = _find_job(d, job_id)
    if j is None:
        return {"dashboard": False, "field": field}
    j[field] = value
    save_jobs(d)
    return {"dashboard": True, "field": field}


def set_notes(job_id, notes):
    """Save a free-text note/gap for a job to pipeline.md (detail block) + the
    dashboard JOBS entry, so it persists and shows in the drawer."""
    job_id = int(job_id)
    notes = (notes or "").strip()
    safe = notes.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("|", "/")
    changed = {"pipeline": False, "dashboard": False}

    # 1) pipeline.md - a "- **Notes:**" line inside the "### Job N —" detail block
    lines = store.read_pipeline()
    hdr = None
    for i, line in enumerate(lines):
        if re.match(r"^### Job %d\b" % job_id, line) or line.startswith(f"### Job {job_id} —"):
            hdr = i
            break
    if hdr is not None:
        # find an existing Notes line within this block (stop at the next "### ")
        note_i = None
        for j in range(hdr + 1, len(lines)):
            if lines[j].startswith("### "):
                break
            if lines[j].startswith("- **Notes:**"):
                note_i = j
        newline = f"- **Notes:** {safe}\n"  # sanitized: no raw newline/pipe can break the block
        if note_i is not None:
            lines[note_i] = newline
        else:
            lines.insert(hdr + 1, newline)
        store.write_pipeline(lines)
        changed["pipeline"] = True

    # 2) jobs.json - the canonical data the dashboard reads
    d = load_jobs()
    job = _find_job(d, job_id)  # not `j` — that's the block-scan loop index above
    if job is not None:
        job["notes"] = notes
        save_jobs(d)
        changed["dashboard"] = True
    return changed


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self._cors()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path.rstrip("/") == "/api/ping":
            return self._json(200, {"ok": True, "service": "sweep-helper"})
        if self.path.rstrip("/") == "/api/config":
            # user-specific display config for the dashboard (commute chip, etc.)
            return self._json(
                200,
                {
                    "home_metro": getattr(config, "HOME_METRO", ""),
                    "commute_tiers": getattr(config, "COMMUTE_TIERS", []),
                },
            )
        if self.path.rstrip("/") == "/api/status":
            return self._json(200, hub_status())
        if self.path.rstrip("/") == "/api/jobs":
            return self._json(200, jobs_payload())
        if self.path.rstrip("/") == "/api/sweep-status":
            return self._json(
                200,
                {
                    "running": SWEEP_STATE["running"],
                    "done": SWEEP_STATE["done"],
                    "log": "\n".join(SWEEP_STATE["log"])[-9000:],
                    "result": SWEEP_STATE["result"],
                },
            )
        # the standalone pipeline board is retired — it lives inside the Hub now.
        if self.path.split("?", 1)[0].rstrip("/") == "/engine/dashboard.html":
            self.send_response(301)
            self.send_header("Location", "/engine/hub.html#search")
            self.end_headers()
            return
        return super().do_GET()

    def do_POST(self):
        path = self.path.rstrip("/")

        if path == "/api/set-status":
            length = int(self.headers.get("Content-Length") or 0)
            try:
                body = json.loads(self.rfile.read(length) or b"{}")
                res = set_status(body.get("id"), body.get("status"))
            except Exception as e:
                return self._json(400, {"ok": False, "error": str(e)})
            if not res["pipeline"]:
                return self._json(
                    404, {"ok": False, "error": f"job id {body.get('id')} not found in pipeline.md"}
                )
            return self._json(200, {"ok": True, **res})

        if path == "/api/set-notes":
            length = int(self.headers.get("Content-Length") or 0)
            try:
                body = json.loads(self.rfile.read(length) or b"{}")
                res = set_notes(body.get("id"), body.get("notes"))
            except Exception as e:
                return self._json(400, {"ok": False, "error": str(e)})
            if not res["pipeline"] and not res["dashboard"]:
                return self._json(404, {"ok": False, "error": f"job id {body.get('id')} not found"})
            return self._json(200, {"ok": True, **res})

        if path == "/api/set-field":
            length = int(self.headers.get("Content-Length") or 0)
            try:
                body = json.loads(self.rfile.read(length) or b"{}")
                res = set_field(body.get("id"), body.get("field"), body.get("value"))
            except Exception as e:
                return self._json(400, {"ok": False, "error": str(e)})
            return self._json(200, {"ok": True, **res})

        if path == "/api/set-voice":
            length = int(self.headers.get("Content-Length") or 0)
            try:
                body = json.loads(self.rfile.read(length) or b"{}")
                return self._json(200, {"ok": True, "voice": set_voice(body.get("voice"))})
            except Exception as e:
                return self._json(400, {"ok": False, "error": str(e)})

        if path == "/api/run":
            # one-shot: hand the prompt to a local claude/gemini CLI (uses the user's
            # subscription). Interactive skills are better run in the AI app directly.
            length = int(self.headers.get("Content-Length") or 0)
            try:
                body = json.loads(self.rfile.read(length) or b"{}")
                prompt = (body.get("prompt") or "").strip()
                if not prompt:
                    return self._json(400, {"ok": False, "error": "no prompt"})
                cli = CLAUDE_BIN or GEMINI_BIN
                if not cli:
                    return self._json(400, {"ok": False, "error": "no claude or gemini CLI found"})
                cmd = (
                    [cli, "-p", prompt]
                    if "claude" in os.path.basename(cli).lower()
                    else [cli, prompt]
                )
                out = subprocess.run(cmd, capture_output=True, text=True, timeout=180, cwd=ROOT)
                return self._json(
                    200, {"ok": True, "output": (out.stdout or out.stderr or "").strip()}
                )
            except subprocess.TimeoutExpired:
                return self._json(
                    200,
                    {
                        "ok": False,
                        "error": "timed out — interactive skills work better in your AI app",
                    },
                )
            except Exception as e:
                return self._json(400, {"ok": False, "error": str(e)})

        if path != "/api/run-sweep":
            return self._json(404, {"ok": False, "error": "unknown endpoint"})

        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            args = json.loads(raw or b"{}")
        except Exception:
            args = {}

        # Start the sweep in the background; the dashboard streams its live
        # progress via GET /api/sweep-status (same activity as the command line).
        if SWEEP_STATE["running"]:
            return self._json(409, {"ok": False, "error": "a sweep is already running"})
        threading.Thread(target=run_sweep_bg, args=(args.get("hours"),), daemon=True).start()
        return self._json(200, {"ok": True, "started": True})

    def log_message(self, *a):  # keep the console quiet
        pass


# ---------------------------------------------------------------------------
# Background sweep runner — streams live progress into SWEEP_STATE["log"] so the
# dashboard's /api/sweep-status shows the same activity you'd see on the CLI.
# ---------------------------------------------------------------------------
SWEEP_STATE: dict[str, Any] = {"running": False, "log": [], "done": False, "result": None}


def run_sweep_bg(hours):
    SWEEP_STATE.update(running=True, done=False, result=None)
    SWEEP_STATE["log"] = []
    log = SWEEP_STATE["log"]
    try:
        cmd = [sys.executable, os.path.join(HERE, "jobspy_sweep.py"), "--out", config.LEADS_RAW]
        if hours:
            cmd += ["--hours", str(int(hours))]
        log.append("$ python jobspy_sweep.py" + (" --hours " + str(int(hours)) if hours else ""))
        proc = subprocess.Popen(
            cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
        )
        assert proc.stdout is not None  # noqa: S101  (stdout=PIPE guarantees a stream)
        for line in proc.stdout:  # stream each progress line as it prints
            log.append(line.rstrip("\n"))
        proc.wait()
        scored = []
        try:
            import lead_score

            scored = lead_score.score_file()  # defaults resolve to <repo>/data now
        except Exception as e:
            log.append("(triage read skipped: %s)" % e)
        SWEEP_STATE["result"] = {
            "total": count_rows(config.LEADS_RAW),
            "inlane": len(scored),
            "keep": sum(1 for x in scored if x["bucket"] == "Keep"),
            "watch": sum(1 for x in scored if x["bucket"] == "Watch"),
            "returncode": proc.returncode,
        }
    except Exception as e:
        log.append("ERROR: " + str(e))
        SWEEP_STATE["result"] = {"error": str(e)}
    finally:
        SWEEP_STATE["running"] = False
        SWEEP_STATE["done"] = True


def main():
    os.chdir(ROOT)
    httpd = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    url = f"http://localhost:{PORT}/engine/hub.html"
    print(paint_banner())
    print(f"  Bellows Hub  ->  {url}")
    print("  click 'Run lead sweep' -> 'Run sweep now'.  Ctrl+C to stop.")
    if os.environ.get("BELLOWS_NO_BROWSER") != "1":
        try:
            webbrowser.open(url)
        except Exception:  # noqa: S110
            pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")


if __name__ == "__main__":
    main()

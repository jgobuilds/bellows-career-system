#!/usr/bin/env python3
"""test_links.py — validate that every link the Career Hub renders actually resolves.

The Hub is client-side, so a wrong document path or a never-generated file shows
up only as a 404 in the browser. This test catches that class of bug before you
see it: it boots the Hub server on a throwaway port and HTTP-GETs

  - the core routes (hub.html, /api/status, /api/jobs, /api/config),
  - the retired-board redirect (/engine/dashboard.html must 301 -> hub, not 404),
  - and EVERY tailored-document link the dashboard would render, straight from
    /api/jobs `docs` (the same list the Hub renders), so the check and the UI can
    never drift.

Run it after any change to the Hub, jobs.json, the document links, or the
applications/ folder:

    python engine/test_links.py        # exits 0 if all links resolve, 1 otherwise
"""

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Off the default 8765 so this never collides with a Hub you already have open.
PORT = int(os.environ.get("TEST_LINKS_PORT", "8799"))
BASE = f"http://127.0.0.1:{PORT}"


def _get(path):
    """(status, body_bytes). status is None on a connection error (body = reason).
    Retries once on a transient connection error so rapid sequential requests to
    the threaded dev server don't flake the result."""
    last = (None, b"")
    for attempt in range(2):
        try:
            with urllib.request.urlopen(BASE + path, timeout=10) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, b""  # a real HTTP status (e.g. 404) — don't retry
        except Exception as e:
            last = (None, str(e).encode())
            time.sleep(0.2)
    return last


def main():
    env = dict(os.environ, SWEEP_PORT=str(PORT), BELLOWS_NO_BROWSER="1")
    proc = subprocess.Popen(
        [sys.executable, os.path.join(_ROOT, "engine", "server.py")],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(50):  # up to ~5s for the server to answer
            if _get("/api/ping")[0] == 200:
                break
            time.sleep(0.1)
        else:
            print(f"FAIL: server did not start on port {PORT}")
            return 1

        failures = []

        # 1) core routes + the retired-board redirect (urlopen follows 301 -> 200)
        routes = [
            ("/engine/hub.html", 200),
            ("/api/status", 200),
            ("/api/jobs", 200),
            ("/api/config", 200),
            ("/engine/dashboard.html", 200),
        ]
        for path, want in routes:
            code = _get(path)[0]
            if code != want:
                failures.append(f"route {path} -> {code} (expected {want})")

        # 2) every document link the dashboard renders
        code, body = _get("/api/jobs")
        data = json.loads(body) if code == 200 else {"jobs": []}
        jobs = data.get("jobs", [])
        doclinks = 0
        for j in jobs:
            for d in j.get("docs") or []:
                doclinks += 1
                code = _get(d["href"])[0]  # fetch once, report that same status
                if code != 200:
                    failures.append(f"doc  {j.get('co')}: {d['label']} -> {code}  {d['href']}")

        print(f"checked {len(routes)} routes + {doclinks} document links across {len(jobs)} jobs")
        if failures:
            print(f"\nBROKEN LINKS ({len(failures)}):")
            for f in failures:
                print("  x", f)
            return 1
        print("all links OK")
        return 0
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())

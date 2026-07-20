#!/usr/bin/env python3
"""build_demo.py — generate a self-contained, server-free demo of the Career Hub.

Reads engine/hub.html and writes starter/hub-demo.example.html: the exact same UI,
but with fictional example data (Johnny Fakeuser) baked in and a fetch() shim so every
/api/* call is answered locally. No server, no network, no personal data — open the
file straight from disk and the kanban, drawer, filters, and drag-to-status all work.

Regenerate whenever hub.html changes:
    python engine/build_demo.py
"""

import json
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(_ROOT, "engine", "hub.html")
OUT = os.path.join(_ROOT, "starter", "hub-demo.example.html")

# --- Fictional demo data (matches starter/pipeline.example.md — Johnny Fakeuser) ---
JOBS = [
    {
        "id": 1,
        "co": "Sentinel Security",
        "role": "Product Marketing Manager",
        "score": 8,
        "tier": "mid",
        "warm": True,
        "warmContact": "Lena Placeholder",
        "fit": "core",
        "ats": 88,
        "status": "tailored",
        "url": "#",
        "tags": ["PMM", "B2B Security", "Positioning & Content", "Remote", "$120–145K"],
        "notes": "Lena introduced me to the hiring manager — call Thursday.",
        "why": (
            "Near one-for-one: technical/security buyer, positioning and launch content named a "
            "top-three priority (their landing-page rewrite that lifted signups 31%->45% lands), "
            "competitive one-pagers, remote, and a clean step up in scope. Gap: they want someone "
            "who's owned an analyst-briefing cadence; they've supported briefings, not run them — own "
            "that plainly."
        ),
    },
    {
        "id": 2,
        "co": "Loop Data",
        "role": "Product Marketing Manager (first PMM)",
        "score": 6,
        "tier": "mid",
        "warm": False,
        "fit": "stretch",
        "ats": 72,
        "status": "to review",
        "url": "#",
        "tags": ["PMM", "Dev Tools", "0→1", "Remote", "$115–140K"],
        "why": (
            "Real 0->1 build as a dev-tools company's first PMM, remote, and their Northwind launch "
            "story fits. Gap: it's a solo role with no team and the JD leans ~40% demand gen — a lane "
            "they explicitly don't have; worth it only if they'd take the demand-gen half."
        ),
    },
    {
        "id": 3,
        "co": "Wander (DTC)",
        "role": "Brand & Growth Marketing Manager",
        "score": 4,
        "tier": "mid",
        "warm": False,
        "fit": "stretch",
        "ats": 40,
        "status": "to review",
        "url": "#",
        "tags": ["Brand & Growth", "Consumer DTC", "Paid Media", "Remote", "$110–135K"],
        "why": (
            "Honest recommendation: skip. Title, level, comp, and 'remote' all look right, so keyword "
            "triage liked it. Gap: the core is consumer DTC brand + paid-media buying, a stated hard gate "
            "in their profile — no framing bridges it. Don't apply."
        ),
    },
    {
        "id": 4,
        "co": "Northwind Analytics",
        "role": "Senior Product Marketing Manager",
        "score": 7,
        "tier": "mid",
        "warm": False,
        "fit": "core",
        "ats": 81,
        "status": "applied",
        "url": "#",
        "tags": ["Senior PMM", "Analytics", "Positioning", "Remote", "$130–160K"],
        "why": (
            "Strong positioning and messaging mandate at an analytics company, remote, and a genuine "
            "step up to Senior PMM. Gap: they want a couple more years and one product launch they "
            "led end-to-end — a stretch on seniority, so lead with the launch they owned."
        ),
    },
    {
        "id": 5,
        "co": "Ravel",
        "role": "Product Marketing Manager",
        "score": 7,
        "tier": "mid",
        "warm": False,
        "fit": "core",
        "ats": 79,
        "status": "interviewing",
        "url": "#",
        "tags": ["PMM", "Series B", "Platform", "Remote", "$120–145K + equity"],
        "notes": "2nd round with the CMO on Tuesday.",
        "why": (
            "Series B platform hiring its first PMM — their 0->1 strength, remote, real equity. "
            "Gap: early-stage scope and runway are unproven; press on ownership and budget in the "
            "interview."
        ),
    },
    {
        "id": 6,
        "co": "Brightpath Cloud",
        "role": "Senior Product Marketing Manager",
        "score": 6,
        "tier": "mid",
        "warm": False,
        "fit": "stretch",
        "ats": 70,
        "status": "applied",
        "url": "#",
        "tags": ["Senior PMM", "Cloud Infra", "Hybrid", "New York, NY", "$140–170K"],
        "why": (
            "A real level-up to Senior PMM with a cloud-infra platform and strong comp. Gap: NYC "
            "hybrid (3 days) is a stretch against their remote preference, and the role folds in some "
            "field marketing beyond their core — verify the mandate."
        ),
    },
    {
        "id": 7,
        "co": "Cascade Labs",
        "role": "Product Marketing Manager, Platform",
        "score": 8,
        "tier": "mid",
        "warm": True,
        "warmContact": "referral — ex-Northwind colleague",
        "fit": "core",
        "ats": 90,
        "status": "offer",
        "url": "#",
        "tags": ["PMM", "Platform", "Remote", "$125–150K + equity"],
        "notes": "Verbal offer — negotiating title + equity.",
        "why": (
            "Platform PMM at a company they'd love, remote, top-of-range comp, and a warm referral "
            "carried it in. Gap: the leveling reads a touch junior for the scope — negotiate the "
            "title alongside the equity."
        ),
    },
]
for j in JOBS:
    j["docs"] = []  # no tailored files in the demo; drawer shows the "build" prompt

DEMO = {
    "jobs": {
        "jobs": JOBS,
        "resumePrefix": "Johnny Fakeuser - ",
        "glassdoor": {
            "Sentinel Security": {"rating": 4.2},
            "Loop Data": {"rating": 3.6},
            "Wander (DTC)": {"rating": 3.0},
            "Northwind Analytics": {"rating": 4.5},
            "Ravel": {"rating": 4.1},
            "Brightpath Cloud": {"rating": 3.4},
            "Cascade Labs": {"rating": 4.6},
        },
    },
    "status": {
        "artifacts": {
            "profile": True,
            "self_assessment": True,
            "positioning": True,
            "roadmap": False,
            "writing_style": True,
            "reconnect": True,
            "references": False,
            "story_bank": False,
            "accountability": False,
            "infointerview": False,
        },
        "artifact_dates": {},
        "pipeline": {"total": len(JOBS), "applied": 4, "interviewing": 1},
        "voice": "supportive",
        "cli": {"claude": False, "gemini": False},
        "profile": {
            "name": "Johnny Fakeuser",
            "current_role": "Product Marketing Manager",
            "target_title": "Senior Product Marketing Manager",
            "target_comp": "$120K–$150K",
            "metro": "Remote · New York, NY",
        },
    },
    "config": {
        "home_metro": "New York, NY",
        "commute_tiers": [{"match": "new york|nyc|brooklyn", "label": "NYC ~45m", "tier": "warn"}],
    },
    "sweepStatus": {
        "running": False,
        "done": True,
        "log": "Demo mode — the live sweep runs in your own Bellows install.",
        "result": {},
    },
}

SHIM = """
<script>
/* ---- Bellows DEMO shim: answer every /api/* call locally, no server ---- */
window.__DEMO__ = %s;
(function(){
  var D = window.__DEMO__;
  function res(data){ return { ok:true, status:200, json:function(){return Promise.resolve(data);},
                               text:function(){return Promise.resolve(JSON.stringify(data));} }; }
  var real = window.fetch ? window.fetch.bind(window) : null;
  window.fetch = function(url, opts){
    try{
      var u = (typeof url === 'string') ? url : (url && url.url) || '';
      if(u.indexOf('/api/') !== -1){
        if(u.indexOf('/api/status') !== -1)       return Promise.resolve(res(D.status));
        if(u.indexOf('/api/jobs') !== -1)         return Promise.resolve(res(D.jobs));
        if(u.indexOf('/api/config') !== -1)       return Promise.resolve(res(D.config));
        if(u.indexOf('/api/sweep-status') !== -1) return Promise.resolve(res(D.sweepStatus));
        if(u.indexOf('/api/run-sweep') !== -1)    return Promise.resolve(res({ok:true}));
        if(u.indexOf('/api/set-status') !== -1){
          try{ var b=JSON.parse((opts&&opts.body)||'{}');
               (D.jobs.jobs||[]).forEach(function(j){ if(j.id===b.id) j.status=b.status; }); }catch(e){}
          return Promise.resolve(res({ok:true, pipeline:true, dashboard:true}));
        }
        if(u.indexOf('/api/set-notes') !== -1)  return Promise.resolve(res({ok:true, pipeline:true, dashboard:true}));
        if(u.indexOf('/api/set-field') !== -1)  return Promise.resolve(res({ok:true}));
        if(u.indexOf('/api/set-voice') !== -1)  return Promise.resolve(res({ok:true}));
        if(u.indexOf('/api/run') !== -1)        return Promise.resolve(res({ok:false, error:'This is the static demo — run steps in your own Bellows install.'}));
        return Promise.resolve(res({ok:true}));
      }
    }catch(e){}
    return real ? real(url, opts) : Promise.reject(new Error('demo: fetch unavailable'));
  };
  document.addEventListener('DOMContentLoaded', function(){
    var bar = document.createElement('div');
    bar.style.cssText = 'background:linear-gradient(90deg,#0072B2,#E69F00);color:#fff;font:600 12.5px Inter,system-ui,sans-serif;'
      + 'padding:7px 14px;text-align:center;letter-spacing:.2px;';
    bar.innerHTML = 'Interactive demo &middot; fictional data (Johnny Fakeuser) &middot; nothing is saved. '
      + 'Get the real thing at <b>github.com/&hellip;/bellows-career-system</b>';
    var w = document.querySelector('.wrap');
    (w ? w.parentNode.insertBefore(bar, w) : document.body.insertBefore(bar, document.body.firstChild));
  });
})();
</script>
""" % json.dumps(DEMO, ensure_ascii=False)


def main() -> None:
    html = open(SRC, encoding="utf-8").read()
    # 1) drop external Google Fonts links (self-contained; fall back to system fonts)
    html = re.sub(r"\s*<link[^>]*fonts\.g[^>]*>", "", html)
    # 2) inject the demo shim just before </head> so it overrides fetch before load() runs
    assert "</head>" in html, "no </head> in hub.html"  # noqa: S101
    html = html.replace("</head>", SHIM + "</head>", 1)
    # 3) title makes it obvious in a tab
    html = html.replace("<title>Bellows</title>", "<title>Bellows — Demo</title>", 1)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(html)
    print(f"wrote {os.path.relpath(OUT, _ROOT)}  ({len(JOBS)} demo jobs, {len(html)} bytes)")


if __name__ == "__main__":
    main()

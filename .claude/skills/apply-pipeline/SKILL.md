---
name: apply-pipeline
description: The find-and-triage engine of the search — discover reliable job leads, then score the ones worth pursuing. Never auto-submits. Discovery polls company ATS feeds directly (Greenhouse, Lever, Ashby, SmartRecruiters, Workday) plus aggregators (hiring.cafe, Built In), validates freshness to kill ghost/stale jobs, filters to the user's lane and level from career-profile.md, and writes qualified leads to personal/data/leads.md. Triage scores a specific job 1-10, gives an honest go/no-go with reasoning, drafts the tailoring approach, routes warm-intro-first at senior level, and writes a tracked row to personal/data/pipeline.md. Triggers: "run a sweep", "find new roles", "check for openings", "any new jobs", "score this job", "is this worth applying to", "what should I emphasize", "handle this application". Reads career-profile.md; hands the document build to resume-tailor; checks warm paths via network. Never applies or submits.
---

# Apply Pipeline (Triage Spoke)


> **Where files live (READ THIS):** every user-specific file lives in the gitignored `personal/` folder — read from it and write to it, never anywhere else in the repo. The profile is `personal/career-profile.md`; tailored résumés, cover letters, and job specs go in `personal/applications/<company>/`; the pipeline board is `personal/data/pipeline.md` + `personal/data/jobs.json`; other user files are `personal/reconnect-list.md`, `personal/application-answers.md`, `personal/writing-style.md`. Settings live in `personal/userconfig.py`. **Anything you create for the user goes under `personal/`** — nothing user-specific is ever written into the tracked repo.

> **Coach voice:** adopt the tone set by `userconfig.COACH_VOICE` (see `coach-voice.md`) — supportive / tough-love / zen / humorous / analytical. It changes **delivery only**; the honest substance, the real gaps, and the no-fabrication rule never change.
The human-in-the-loop answer to autonomous mass-apply tools. It runs the search's front half end to end: **discover** real, fresh leads from reliable sources, then **triage** the ones worth it — score honestly against the real profile, go/no-go, draft the tailoring approach, and route it (warm intro first if a path exists, cold application if not). It stops at the submit button, always.

Part of the career system:
- **career-profile** (hub) → the profile this reads for the lane/level filter and scoring.
- **network** → the warm-contact list this checks against for routing; hands off the message.
- **resume-tailor** → builds the actual tailored resume file once you decide to apply.
- **career-coach** → its "jobs to watch" reshapes what discovery targets.
- **apply-pipeline** (this) → finds leads, decides IF/HOW to apply, drafts the approach, tracks it.

## The three hard boundaries (never cross, even if asked)
1. **No auto-submit, ever.** This skill drafts and prepares. The user opens the posting and submits. Not a default — a rule. It exists because unsupervised submission attaches the user's name to applications they never read, trips bot-detection, and auto-answers screening/EEO/work-authorization questions that carry legal and reputational weight (acute at defense/regulated employers).
2. **The quality bar is not bypassed for volume.** Every tailoring draft runs the fabrication check from resume-tailor's de-ai-checklist: metrics must trace to personal/career-profile.md, no scale overreach, no inflated scope. A lighter *review surface* for volume roles is fine; skipping the *check* is not.
3. **Senior roles hit the warm-channel gate first.** Before a senior role becomes a cold application, check the profile's reconnect contacts and `personal/reconnect-list.md` (the network skill's tracker). If a warm path exists, route there first — a referral beats a cold submit at senior level, every time (the whole career system is built on this lesson).

## Workflow

### 0 — Discovery (the sweep — run when the user wants fresh leads, not for a single pasted job)
Find reliable, fresh openings from sources more accurate than LinkedIn, and write qualified leads to `personal/data/leads.md`. **Full procedure, source catalog, and the anti-ghost-job rules are in `references/discovery.md`** — follow it. In brief:
- **Source hierarchy, top-down:** (1) **ATS-direct** company JSON feeds — Greenhouse, Lever, Ashby, SmartRecruiters, Workday (real dates, near-zero ghost jobs, most reliable); (2) **ATS-sourced aggregators** — hiring.cafe, Built In (wide recall, still validate); (3) general boards (discovery only, confirm at source); (4) LinkedIn (warm-path layer, not a freshness source).
- **Lane-first, not company-first:** the job *title* is the signal, not the employer. A "Director / Head / AVP / VP of Data {Platform | Governance | Strategy | Enablement | Analytics}" role is a Keep at *any* company once its ATS confirms it; industry is a tiebreaker, never a gate. Run the title-first recall pass across all industries first — that's where the best hand-found leads came from.
- **Never trust a date or "open" status** until confirmed on the company's own ATS. Validate freshness, dedupe against `personal/data/pipeline.md`, and qualify each Keep/Watch/Drop with an honest fit note. See `references/target-companies.md` (compounding company cache + ATS-resolution recipe) and `references/lead-row.md` (output format).
- **Discovery only — never apply.** Surface the top Keeps and offer to score them (Stage 1+ below). Never fabricate a posting, date, or company; label below-level/off-lane honestly instead of padding the list.

### 1 — Intake (triage a specific job)
User pastes a job description or URL. If a URL, fetch it. Extract: title, company, seniority, must-haves vs. nice-to-haves, the company's terminology, and any knockout gates (work authorization, clearance, location, hard years floor).

### 2 — Score (1–10) against personal/career-profile.md
Load the profile. Score honestly on genuine fit, not keyword overlap:
- **9–10** — strong match on the role's core thesis; few gaps; apply with confidence.
- **7–8** — good match, some stretch; worth a tailored application.
- **5–6** — moderate; real gaps; apply only if something specific makes it worth it (warm path, dream company).
- **1–4** — skip; the gap is structural.
Show the score WITH its reasoning: what matches, what's the gap, and the honest read on whether the gap is bridgeable. Never inflate the score to be encouraging — a false 8 wastes the user's effort. A well-argued 6 that says "skip unless you have an in" is more useful than a flattering 8.

### 3 — Route (warm vs. cold)
- **Senior role + warm path exists** (contact at the company in `personal/reconnect-list.md`) → route to warm intro FIRST. Output: "reach [contact] before applying," hand to the network skill for the message. Do not frame the cold application as the primary path.
- **Senior role, no warm path** → cold application, but flag that a warm path would materially help and suggest checking whether any reconnect contact could bridge in.
- **Volume/mid role** → cold application is fine; warm-first is not required (the referral math changes at mid-level).

### 4 — Draft the tailoring approach (not the full resume)
Using the profile and the target analysis, specify: which bullets to lead with, which to drop, what terminology to mirror, the role's thesis (build/scale/turnaround/governance), and any honest gaps to be ready for in interview. This is the *plan* resume-tailor will execute — don't build the file here unless the user says apply; hand off to resume-tailor for the document.

### 5 — Run the integrity check (always, surface it)
Before presenting, check the drafted approach against the fabrication guards:
- Every metric traces to personal/career-profile.md.
- No scale/scope overreach for this role (esp. "global"/"enterprise" claims the profile doesn't support).
- Knockout gates named honestly (don't route the user toward a role a clearance requirement disqualifies them from).
Surface the check results to the user — it's a feature, not a hidden step. The user seeing "✓ metrics trace / ⚠ don't imply global org here" is the thing that keeps the volume path honest.

### 6 — Persist the scored job (immediately, not at session end)
Emit a compact tracker row (format in `references/tracker-row.md`), then **persist it** the drift-proof way. The board reads **`personal/data/jobs.json`** (through the local server's `/api/jobs`); **`personal/data/pipeline.md`** is the human-readable record. Both must stay in sync — the `add_job.py` tool writes both from one input and recomputes the summary counts so they can't drift.

- **Folder mode (Claude Code / Cowork — the career folder is mounted):**
  1. Build a small `job.json`: a `record` (the full jobs.json object — id, role, co, score, tier, warm, fit, tags, why, checks, diff, cover, status, applied, posted, doc) plus a `pipeline` block (why_short, flags, date_added, detail_block). Shape + a live example: `references/tracker-row.md` and any `personal/applications/<company>/job.json`.
  2. Run **`python engine/add_job.py <path/to/job.json>`** — it appends to `personal/data/jobs.json`, inserts the row + detail block into `personal/data/pipeline.md`, and recomputes the counts. One job scored = one `add_job.py` run. Never batch persistence to session end.
  3. **Never hand-edit `dashboard.html`.** It is the PII-free shell — it holds no data and renders entirely from `/api/jobs → jobs.json`. Writing job data into it would re-introduce PII into the tracked repo. To see the new row, just refresh the browser (or restart `dashboard.bat` / the server).
- **Chat mode (no file access):** emit the tracker row and the `record` JSON and ask the user to run `add_job.py` or paste them into their `personal/data/` files. Never score into the void and lose it.
- **Status changes** ("mark Acme applied"): edit that job's `status` in `jobs.json` and the matching row in `pipeline.md` — never duplicate the row. The board's Applied button does this for you via the server's `/api/set-status`.

## Persistence model (one line)
**`jobs.json` is the database, `pipeline.md` is the human record, the dashboard is a read-only rendered view.** `add_job.py` writes the first two atomically; the local server renders them. The PII-free `dashboard.html` never contains data — never edit its HTML to add a job.
# Discovery — the reliable-source sweep (apply-pipeline Stage 0)
_Operational procedure for finding and qualifying leads. The SKILL.md summarizes; this is the full playbook._


> **Where files live (READ THIS):** every user-specific file lives in the gitignored `personal/` folder — read from it and write to it, never anywhere else in the repo. The profile is `personal/career-profile.md`; tailored résumés, cover letters, and job specs go in `personal/applications/<company>/`; the pipeline board is `personal/data/pipeline.md` + `personal/data/jobs.json`; other user files are `personal/reconnect-list.md`, `personal/application-answers.md`, `personal/writing-style.md`. Settings live in `personal/userconfig.py`. **Anything you create for the user goes under `personal/`** — nothing user-specific is ever written into the tracked repo.
The reliable-source answer to the LinkedIn sweep. Instead of trusting a noisy aggregator's "posted this week" feed, this goes to where jobs actually live — company ATS systems — pulls exactly what's open, confirms it's real and fresh, filters to the user's lane, and writes qualified leads to `personal/data/leads.md`. It stops at discovery; scoring and applying happen downstream.

Part of the career system:
- **career-profile** (hub) → the profile this reads to know the user's lane, level, domain, geography, and comp floor.
- **apply-pipeline** (this) → finds & qualifies leads from reliable sources, writes `personal/data/leads.md`.
- **apply-pipeline** → scores one lead 1–10 and promotes it to `personal/data/pipeline.md`.
- **network** → the warm-path layer.


## Why not just search LinkedIn (the thing this fixes)
- **Ghost jobs:** ~18–22% of postings on major platforms are live with no active hiring intent (Greenhouse data, late 2025). LinkedIn/Indeed can't be trusted on whether a role is real.
- **Reposts & hidden employers:** a large share of "past week" hits are recruiter/aggregator reposts (hackajob, Swooped, Jobgether, Peaple) where the true employer is hidden and the date is the repost date.
- **Geo folding:** LinkedIn folds all US-remote roles into any location search, so a "Hartford" search is mostly not local.
- **The fix:** rank sources by distance from the ATS, and never trust a date or an "open" status until it's confirmed on the company's own ATS.

## The source hierarchy (always work top-down)
1. **ATS-direct** — the company's own public JSON feed. Real posting date, real open status, near-zero ghost jobs. Greenhouse, Lever, Ashby, SmartRecruiters, Workday. **Most reliable.**
2. **ATS-sourced aggregators** — hiring.cafe (scrapes ~46 ATS platforms, deduped, refreshed multiple times/day) and Built In (server-rendered, real recency filter). Wide recall; still validate the best hits.
3. **General boards** — Indeed / Google for Jobs. Discovery only; every hit gets confirmed against the company ATS.
4. **LinkedIn** — network/warm-path layer only. Not a freshness source.

## Lane-first, not company-first (2026-07-11 upgrade)
The precision pass (a curated company list weighted to insurance + big SaaS) is high-trust but **misses in-lane roles at companies not on the list**. Every strong lead Jon has found by hand — Director of Data Platforms & Governance (AssetWatch, manufacturing/IoT), Director of Data Strategy & Services (Momentive, nonprofit/association software), Head of Data Enablement (Zekelman, steel), plus healthcare, consumer-tech, and devtools roles — was **in his lane but outside the curated domains**, so a company-first sweep never polled them.
The fix: **run discovery lane-first.** The job title is the signal, not the employer. A "Director / Head / AVP / VP of Data {Platform | Governance | Strategy | Enablement | Analytics}" role is a Keep at *any* company once its ATS confirms it — manufacturing, nonprofit software, consumer media, healthcare, retail, devtools, EdTech all count. Industry is a tiebreaker (insurance/fintech still raises confidence), never a gate. The recall layer now **leads with a title-first pass across all industries**, and the target list is a compounding cache, not the boundary of the search.

## The three boundaries (never cross)
1. **Discovery only — never apply or submit.** This skill finds and qualifies. Applying is the user's decision, routed through apply-pipeline and done by hand. Same no-auto-submit ethos as the rest of the system.
2. **Never fabricate a posting, a date, or a company.** If a role can't be validated on a real source, it's flagged "unconfirmed" or dropped — never written to personal/data/leads.md as if it were verified. A made-up lead is worse than no lead.
3. **Honesty over volume.** Below-level, off-lane, or step-down roles are labeled as such, not padded into the list to look productive. A short list of real fits beats a long list of noise.
4. **No mass-apply / auto-submit, borrowed or otherwise.** Discovery tooling may be borrowed (e.g. JobSpy for breadth), but this skill never adopts the auto-apply / bulk-submit behavior of mass-application agents. Applying stays human-in-the-loop through apply-pipeline. (This is the whole reason the career system exists.)

## Workflow

### 1 — Load context
Read `personal/career-profile.md` for the qualification filter: lane (data leadership — governance/enablement/platform/analytics/reliability), level (Director/AVP/VP/Head), domain bonus (insurance/fintech), geography (Hartford hybrid + US remote), comp floor. Read `personal/data/pipeline.md` and `personal/data/leads.md` so you can dedupe against what's already tracked. If in Cowork/folder mode these are live files; in chat mode ask the user to upload them.

### 2 — Precision pass: poll the target list (ATS-direct)
Open `references/target-companies.md`. For each company with a validated ATS slug/tenant, hit its endpoint (exact patterns in `references/sources.md`):
- Greenhouse, Lever, Ashby, SmartRecruiters → keyless GET, returns JSON with real posting dates.
- Workday → keyless POST to the CXS `/jobs` endpoint with a `searchText` like "data".
Pull the **lightweight list first** (title, location, date, url). For Greenhouse specifically, do NOT use `?content=true` on the list call — it returns full descriptions and overflows fetch limits after ~6 jobs; fetch full detail per-job only for candidates that pass the filter.
Keep anything whose title/level is in-lane. Every ATS-direct hit is self-validated (the date is real).

### 2.5 — Role-first (title) recall — the highest-yield net, run it FIRST
Company-first polling only finds what's on the list. This pass finds in-lane roles **anywhere**, which is where Jon's best hand-found leads came from. Search by TITLE across all industries, Remote (US) + Hartford-commutable, restricted to recent postings:
- **hiring.cafe (best net):** query each target title pattern (below), filter Remote + recency. Every hit originates from a company ATS, so resolve each promising one to Tier 1 and confirm.
- **Built In** (`daysSinceUpdated=1|7`) and **Google for Jobs** for the same titles — server-rendered breadth.
- **Target title patterns** (Director / AVP / VP / Head / Sr Director; strong Manager roles at modern-tech also in scope): `Data Platform(s)`, `Data Governance`, `Data Strategy`, `Data Enablement`, `Data Management`, `Data Analytics` (data-*function*, not product-analytics/DS-lead), `Data Center of Excellence`, `Head of Data`, `Data Platform Lead`, and market synonyms ("Data Strategy & Services", "Data Platforms & Governance").
- **Watch for slug/title mismatches:** Momentive's posting *slug* said "Data Center of Excellence" but the real title was "Director, Data Strategy & Services." Always read the real title from the ATS JSON, not the URL.
- For any promising company NOT on the target list: resolve its ATS (recipe in target-companies.md), **add it to the list**, and validate directly. This is how the precision list compounds.
Then run Step 3 for the curated domains.

### 3 — Recall pass: sweep the ATS-sourced aggregators
Run hiring.cafe and Built In (methods in `references/sources.md`) for the user's role terms + geography, restricted to recent postings. Optionally seed breadth with the JobSpy engine (multi-board, MIT-licensed; see `references/sources.md`) — but treat every JobSpy/aggregator hit as a pointer to confirm at source, never as proof. For any promising hit at a company NOT already on the target list: resolve its ATS (recipe in `references/target-companies.md`), **add it to the target list**, and validate the role directly. The precision layer compounds over time this way.

### 4 — Validate freshness (the anti-ghost-job rule)
- ATS-direct hits → already validated; record the real posting date.
- Aggregator/board hits → confirm on the company's own ATS before trusting. If the role isn't on the company ATS, mark it "unconfirmed / possibly stale" and do not promote it. Never carry an aggregator's date forward as if it were the posting date.

### 5 — Dedupe
- Same company + same/near title already in `personal/data/pipeline.md` → mark "already tracked", do not re-add.
- Same role from multiple sources → one lead, preferring the ATS-direct URL over any aggregator URL.
- Same company + title within the freshness window → collapse to one.

### 6 — Qualify (against personal/career-profile.md, not keywords)
For each surviving lead assign:
- **Keep / Watch / Drop** — Keep = in-lane and at-level; Watch = adjacent or caveated; Drop = off-lane or below-level (note briefly why).
- **Confidence** high/med/low = source reliability × lane match. ATS-direct + strong lane = high; aggregator + hidden employer = low.
- **Fit note** — one honest line: the match and the gap. Insurance/fintech domain raises confidence; flag comp materially below band as a step-down.

**Lane-first qualification (2026-07-11):** a role whose title matches a target pattern and whose ATS confirms it is a **Keep at any company/industry** — do not Drop or down-rank it merely because the employer isn't a known insurer or big-name SaaS. Industry adjusts *confidence* (insurance/fintech/regulated raises it; an unfamiliar domain is neutral, not negative); comp below floor is still flagged. Reserve Drop for genuine lane/level misses (product-management-track, data-science/experimentation-lead, below-Director IC, pure HR/People analytics). The point of this upgrade is to stop losing in-lane roles that sit in unexpected industries.

### 7 — Write personal/data/leads.md and hand off
Append a dated sweep section to `personal/data/leads.md` (format in `references/lead-row.md`): a "Worth scoring" group (Keep, high/med confidence), a "Worth a look" group (Watch, with caveats), a "Below level / off-lane" note, and an "Already tracked" note. Update the `_Last sweep_` line. Then surface the top 3–4 "Keep" leads and offer to run **apply-pipeline** on them to score into `personal/data/pipeline.md`. Do not score here — that's apply-pipeline's job.

## Modes
- **Folder mode (Cowork / Claude Code — career folder mounted):** personal/career-profile.md, personal/data/leads.md, personal/data/pipeline.md are live. Read them, write personal/data/leads.md the moment the sweep completes. Don't ask for uploads.
- **Chat mode (no file access):** ask the user to upload personal/career-profile.md and personal/data/leads.md; return the updated personal/data/leads.md to save back.

## Tooling notes
- ATS JSON endpoints are public and keyless — fetch with the standard web fetch tool. They are legitimate published feeds, not scraping around a block.
- hiring.cafe, Built In job pages, Google for Jobs, and LinkedIn are JS-rendered — use the Chrome extension (browser tools) to read them, not a raw fetch.
- Built In supports a real recency filter (`daysSinceUpdated=1`) and is server-rendered, so it works without the browser when you need last-24h.
- Respect each site's terms; this is personal, human-in-the-loop discovery at low volume, not bulk scraping.

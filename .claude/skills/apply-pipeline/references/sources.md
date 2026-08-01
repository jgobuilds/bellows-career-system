# Source Catalog — exact endpoints and methods
_Ranked by reliability (distance from the ATS). Top-down is the order to work them._


## Contents

- [Tier 1 - ATS-direct](#tier-1--ats-direct-public-keyless-json-most-reliable) - Greenhouse, Lever, Ashby, SmartRecruiters, Workday
- [Tier 1.5 - resolvable non-standard ATS](#tier-15--resolvable-non-standard-ats-icims-phenom--added-2026-07-11)
- [Tier 2 - ATS-sourced aggregators](#tier-2--ats-sourced-aggregators-wide-recall-validate-best-hits-at-source)
- [Tier 2.5 - community and thread sources](#tier-25--community--thread-sources-secondary-verify-at-source)
- [Tier 3 - general boards](#tier-3--general-boards-discovery-only-always-verify-at-source)
- [Tier 4 - LinkedIn](#tier-4--linkedin-network-layer-not-a-freshness-source)
- [Optional discovery engines](#optional-discovery-engines-run-in-the-users-own-environment)
- [The one rule that ties it together](#the-one-rule-that-ties-it-together)

**Two things worth knowing before you fetch anything** (learned the hard way, 2026-08-01):

- **Workday LIST needs a POST; DETAIL is a plain GET.** Trying to GET the search endpoint
  returns 400, which reads as a broken endpoint rather than the wrong verb. The detail
  endpoint below works fine over GET and returns the full description.
- **An aggregator's link is not the employer's link.** Aggregators re-title and mislocate
  roles, and their pages often cannot be fetched to check. Prefer `job_url_direct` where the
  scraper supplies it; a UK role was once assessed as a phantom because only the aggregator's
  rewrite was on hand.

## Tier 1 — ATS-direct (public, keyless JSON; most reliable)
These return exactly what's open at a company right now, with a real posting date. If a role isn't here, it isn't really open. Fetch with the standard web fetch tool.

### Greenhouse  — VALIDATED live 2026-07-04 (gitlab board)
- List (lightweight): `GET https://boards-api.greenhouse.io/v1/boards/{company}/jobs`
- Full content (heavy — avoid on list calls): add `?content=true`. Returns full HTML per job and overflows fetch limits after ~6 jobs. Use only on a single job.
- Single job detail: `GET https://boards-api.greenhouse.io/v1/boards/{company}/jobs/{id}`
- Departments (to map jobId→department): `GET https://boards-api.greenhouse.io/v1/boards/{company}/departments`
- Key fields: `title`, `location.name`, `absolute_url`, `updated_at`, `first_published`, `requisition_id`, `internal_job_id`.
- Freshness: use `first_published` (real post date) and `updated_at`.

### Lever
- List: `GET https://api.lever.co/v0/postings/{company}?mode=json`
- Source-side filters supported: `team`, `department`, `location`, `commitment`, `level`, plus `skip` / `limit`.
- Key fields: `text` (title), `categories.location`, `categories.team`, `hostedUrl`, `createdAt` (ms epoch — divide by 1000 for a real date).

### Ashby — cleanest compensation data
- List: `GET https://api.ashbyhq.com/posting-api/job-board/{company}?includeCompensation=true`
- No source-side filtering — pull all, filter locally.
- Key fields: title, location, job URL, published date, and (with the flag) compensation range.

### SmartRecruiters
- Search: `GET https://api.smartrecruiters.com/v1/companies/{company}/postings?q={query}&limit={n}&offset={n}&country={c}&region={r}&city={city}`
- Detail: `GET https://api.smartrecruiters.com/v1/companies/{company}/postings/{postingId}`
- Key fields: name (title), location, `releasedDate`, ref to detail.

### Workday — used by most large insurers; POST, per-tenant
- List: `POST https://{tenant}.wd{N}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs`
  - JSON body: `{"appliedFacets":{},"limit":20,"offset":0,"searchText":"data"}` (all fields required even if empty; page with `offset`).
  - Returns `jobPostings[]` with `title`, `locationsText`, `postedOn` (e.g. "Posted 3 Days Ago"), `externalPath`, and a `total` count.
- Detail (precise date + full description): `GET https://{tenant}.wd{N}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/job/{externalPath}` → includes `startDate` / precise `postedOn`.
- The `wd{N}` data center (wd1, wd3, wd5…) and `{site}` differ per company — read them off the company's real careers URL; never assume. See target-companies.md for the resolution recipe.
- VALIDATED patterns in use: `archgroup.wd1` (Arch), `thehartford.wd5` site `Careers_External`, `pluralsight.wd1`.

## Tier 1.5 — resolvable non-standard ATS (iCIMS, Phenom) — added 2026-07-11
Previously written off as "no-api / browser only," these two cover a large slice of employers (GitHub, Travelers, Liberty Mutual, Selective, Asurion). They lack the clean keyless JSON of Tier 1, but each is resolvable — stop treating them as blind spots.

### iCIMS (e.g. github.careers)
- Career fronts look like `{company}.careers` or `careers-{company}.icims.com`. Job pages are JS-rendered.
- Reliable path: load the careers-home search with the Chrome extension, read the result list, open each job — iCIMS job pages embed a **JSON-LD `JobPosting`** block (see enrichment cascade below) with `title`, `datePosted`, and full `description`. Validate freshness from `datePosted`.
- Some tenants also expose a JSON search widget under `api-*.icims.com`; inspect the network tab once and record it. Log resolved iCIMS hosts in target-companies.md as you find them (e.g. `github.careers`).

### Phenom (e.g. careers.travelers.com, Liberty Mutual, Asurion)
- Phenom sites (`careers.{company}.com`, often `/us/en/search-results`) expose a JSON search endpoint — commonly `POST {host}/api/apply/v2/jobs` or `GET {host}/api/jobs?keyword={terms}&limit={n}` (path varies per tenant; inspect once via the Chrome extension network tab, then record it per company).
- Job-detail pages also carry a **JSON-LD `JobPosting`** block for full text + `datePosted`. Confirm freshness there.
- Record resolved Phenom endpoints per company in target-companies.md as discovered.

## Tier 2 — ATS-sourced aggregators (wide recall; validate best hits at source)
JS-rendered — read with the Chrome extension.

### hiring.cafe  ★ best general net
- Scrapes ~46 ATS platforms (Greenhouse, Lever, Workable, Workday, BambooHR, company career pages), deduped, refreshed multiple times/day → far lower scam/ghost rate than LinkedIn.
- Use the site's filters (title terms, location incl. Remote, recency).
- **Run it title-first:** query Jon's target title patterns (SKILL.md Step 2.5) across ALL industries + Remote, not just companies on the target list — this is the pass that surfaces in-lane roles at employers you'd never think to poll (AssetWatch, Momentive, etc.). Because listings originate from company sites, a hit here almost always maps cleanly to a Tier-1 ATS — resolve it and add the company to the target list.
- Caveats: new postings can lag; may miss smaller/local employers.

### Built In  — good for last-24h, works without the browser
- Server-rendered; supports `daysSinceUpdated=1` (last 24h) / `=7` (week) as a real recency filter.
- Good for CT/remote tech + data roles. Confirm the employer's ATS for anything worth keeping.

## Tier 2.5 — community & thread sources (secondary; verify at source)
Lower volume, but self-posted by real hiring teams and often remote. Skews startup / senior-IC / eng-manager, so expect a handful of leadership-flavored hits, not a stream of Director/VP roles.

### Hacker News "Who is hiring?" (monthly, API-accessible)
- Posted the 1st of each month by the `whoishiring` bot; each top-level comment is one company's post. No recruiters. Remote-heavy.
- Programmatic: use the public Algolia API (no key). `hn_sweep.py` (in the career folder) finds the latest thread and writes in-lane remote pointers to `leads_hn.csv`; run it like jobspy_sweep.py, then hand the CSV to apply-pipeline.
- Human-searchable mirrors: hnjobs.emilburzo.com, nthesis.ai/public/hn-who-is-hiring, nchelluri.github.io/hnjobs (filter for "Head of Data / Director / Data Lead / Remote").

### analyticsengineeringjobs.com  — curated, on-stack niche board
- Curated analytics-engineering / dbt board; low noise, roles are on your exact stack (dbt, Snowflake, SQL). Has a `/landing-pages/dbt/#recent-jobs` view and links straight to each employer's own ATS (Greenhouse/Lever/Ashby), so a hit resolves cleanly to Tier 1.
- Skews IC/senior-IC and eng-manager; scan for Head of Data / Director / Analytics-Engineering-Manager titles and remote. Good complement to hiring.cafe for the modern-data-stack lane. Confirm each at source.

### Data-leadership community #jobs channels (cannot be scraped — join + set alerts)
This is where senior data roles actually circulate. Join and set a keyword alert (data lead, head of data, director, governance):
- Locally Optimistic (the data-leadership community) — #jobs
- dbt Community Slack — #jobs (analytics-engineering / data-platform roles, on-stack)
- MeasureSlack, Data Angels, Operational Analytics Club
These are manual channels: apply-pipeline can't poll them, but they are the highest-yield non-obvious source for this level, so check them on the same cadence as the sweep.

## Tier 3 — general boards (discovery only; always verify at source)
- **Google for Jobs:** search `https://www.google.com/search?q={terms}&ibp=htl;jobs` (Chrome extension; client-rendered). Aggregates broadly, links to source.
- **Indeed:** high volume, high ghost/repost rate; only as a pointer, never as proof a role is live.
- **Wellfound (AngelList Talent, wellfound.com):** startup / venture-backed roles (the pool that includes Cursor-type companies). Client-rendered — read with the Chrome extension; requires a free login to see most listings. High volume and noise, startup-heavy, often equity-forward comp. Use it to *find companies* in the modern-tech lane, then resolve each opening on the company's own ATS (Tier 1) before writing it to leads.

## Tier 4 — LinkedIn (network layer, NOT a freshness source)
- Use only to work warm paths on leads that already survived Tiers 1–3: who works at the company, who's hiring, who can refer. Its date and employer fields are unreliable for discovery (geo-folds remote, surfaces reposts). Hand warm paths to network.

## Optional discovery engines (run in the user's own environment)
These broaden the net but do NOT replace the validate-at-source rule below.

### JobSpy (`python-jobspy`) — MIT-licensed, free
One library that scrapes Indeed, LinkedIn, Glassdoor, Google Jobs, and ZipRecruiter concurrently and returns a pandas DataFrame with dates. `pip install -U python-jobspy`; call `scrape_jobs(site_name=[...], search_term=..., location=..., results_wanted=..., hours_old=...)`.
- **Why use it:** multi-board breadth in one call, with a real `hours_old`/date field, runnable from a script (no browser allowlist needed) — a fast first-pass recall tool.
- **Guardrails (important):** LinkedIn is JobSpy's most aggressive blocker and usually needs a proxy; Indeed/LinkedIn results still carry the ghost-job and repost noise this skill exists to filter, so **every JobSpy hit is a pointer, not proof** — confirm it on the company's own ATS (Tier 1) before writing it to personal/data/leads.md. Respect each board's ToS; run at low, personal volume.
- **Best value:** Google Jobs breadth + a quick cross-board sweep to find companies to add to the target list; then validate at source.

### Full-JD enrichment cascade (technique, for pulling a complete description)
When a board only shows a summary (e.g. Built In) or a JD won't fetch, resolve the full text in three tiers, cheapest first:
1. **JSON-LD** — most career/job pages embed a `<script type="application/ld+json">` `JobPosting` object with the full `description`, `datePosted`, `hiringOrganization`, `jobLocation`. Fetch the page and parse it — no rendering needed.
2. **Known CSS selectors** — per-ATS description containers (Greenhouse `#content`, Workday job-detail JSON, Lever `.section-wrapper`).
3. **Rendered read** — only if 1–2 fail, load via the Chrome extension and read the description.

## The one rule that ties it together
A lead is "validated" only when its posting date and open status are confirmed on the company's own ATS (Tier 1). Everything below Tier 1 is a pointer to be confirmed, not evidence on its own.

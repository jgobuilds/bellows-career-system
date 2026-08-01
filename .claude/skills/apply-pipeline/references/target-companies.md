# Target Companies — the curated precision list
_Poll these ATS endpoints directly each sweep. Seeded 2026-07-04; schema upgraded to the queryable Workday format (tenant / wd# / site_id / base_url) so each row can be hit directly via the CXS endpoint. Extend the list every time the recall pass turns up a new fitting company._

## Queryable schema (Workday)
Store four fields so a sweep can POST straight to the feed (see `sources.md`):
`tenant` · `wd#` (data center) · `site_id` (careers site path) · `base_url` = `https://{tenant}.wd{N}.myworkdayjobs.com`
CXS list endpoint = `{base_url}/wday/cxs/{tenant}/{site_id}/jobs` (POST, body `{"appliedFacets":{},"limit":20,"offset":0,"searchText":"data"}`).

## How to resolve a company's ATS (do once per company, then record it)
1. Open the careers page and read the URL / "View source":
   - `boards.greenhouse.io/{slug}` / `job-boards.greenhouse.io/{slug}` → **Greenhouse**.
   - `jobs.lever.co/{slug}` → **Lever** · `jobs.ashbyhq.com/{slug}` → **Ashby** · `careers.smartrecruiters.com/{slug}` → **SmartRecruiters**.
   - `{tenant}.wd{N}.myworkdayjobs.com/{site_id}` → **Workday**; record all four fields above.
   - `searchjobs.*` / Phenom / iCIMS / Taleo → no clean public feed; browser/aggregator only.
2. Test the endpoint from `sources.md`. JSON back → mark **validated**; confirmed-from-URL but not yet queried → **resolved**.

## Harvested Workday-tenant source (ApplyPilot registry)
The open-source ApplyPilot repo ships a `config/employers.yaml` with ~48 Workday tenants in exactly this tenant/site_id/base_url shape — a handy lookup for resolving a company's Workday site. Note: it skews **Canadian banks/pensions + global tech** (TD, RBC, BMO, Manulife, Sun Life, Intact, CPPIB, OMERS…), so most of it isn't Jon's US-insurer market. Genuinely reusable US/data-adjacent tenants below are lifted from it and flagged `verify` (re-confirm before trusting — tenants change). ApplyPilot is AGPL-3.0; we reuse only the factual tenant list (re-verified), not its code.

## Status legend
`validated` = feed returned JSON · `resolved` = tenant/site confirmed from careers URL, not yet queried (Workday is POST-only) · `verify` = not yet confirmed · `no-api` = no clean public feed.

## Insurance / financial services (Jon's core domain)
| Company | ATS | tenant · wd# · site_id | Status | Notes |
|---|---|---|---|---|
| Arch Insurance | Workday | archgroup · wd1 · Careers | resolved | AVP Reporting & Data in pipeline. |
| The Hartford | Workday | thehartford · wd5 · Careers_External | resolved | Alumni network = warm paths. |
| Travelers | Phenom (careers.travelers.com) | — | no-api | AVP D&A Architecture in pipeline; browser/aggregator only. |
| Cigna (The Cigna Group) | Workday | cigna · wd5 · cignacareers | resolved | Bloomfield CT — commutable. |
| CVS Health / Aetna | Workday | cvshealth · wd1 · CVS_Health_Careers | resolved | Aetna HQ Hartford. |
| MassMutual | Workday | massmutual · wd1 · MMAscendCareers | resolved | Also MMINDCareersite / MMExperiencedCareers. |
| Voya Financial | Workday | godirect · wd5 · voya_jobs | resolved | Hartford-area. |
| Synchrony | Workday | synchronyfinancial · wd5 · careers | resolved | Stamford CT / remote-friendly. |
| Liberty Mutual | Phenom | — | no-api | Data Strategy/Governance roles, often below Director. |
| Mastercard | Workday | mastercard · wd1 · CorporateCareers | verify | From ApplyPilot registry; data/analytics leadership does appear. |
| PayPal | Workday | paypal · wd1 · jobs | verify | From ApplyPilot registry; fintech data roles. |
| FIS Global | Workday | fis · wd5 · SearchJobs | verify | From ApplyPilot registry; fintech. |
| CNA Insurance | verify | — | verify | Director Strategy/Execution/Analytics seen 2026-07-04. |
| Prudential | verify | — | verify | |
| Guardian Life | verify | — | verify | Jon worked there (2012–13). |
| Ledgebrook | verify | — | verify | Insurtech; AVP Data Quality seen (remote). |
| Asurion | verify (Phenom likely) | — | verify | Director PM Data Platform — scored 5 (PM lane). |
| _(Canada, if remote/relocation ever in scope)_ | Workday | manulife·wd3·MFCJH_Jobs · sunlife·wd3·Experienced-Jobs · intactfc·wd3·intactfc | verify | Canadian insurers from ApplyPilot registry — only if Jon opens to Canada. |

## Data / analytics platform & enterprise (Jon's stack lane)
| Company | ATS | slug / tenant | Status | Notes |
|---|---|---|---|---|
| GitLab | Greenhouse | gitlab | validated | VP Data & Insights in pipeline. |
| Pluralsight | Workday | pluralsight · wd1 | resolved | Director Enterprise Data Mgmt & Governance (Tier-1); re-validated fresh 2026-07-04. |
| Databricks | Greenhouse | databricks | validated | Leadership roles are data-infra/field — off Jon's lane. Low yield. |
| ServiceNow | Workday | servicenow · wd1 · ServiceNowCareers | verify | From ApplyPilot registry; large internal data org. |
| Salesforce | Workday | salesforce · wd12 · External_Career_Site | verify | From ApplyPilot registry. |
| Thomson Reuters | Workday | thomsonreuters · wd5 · External_Career_Site | verify | From ApplyPilot registry; data/analytics heavy. |
| dbt Labs (merged w/ Fivetran) | verify | — | verify | Jon's core tool. Resolve post-merger ATS. |
| Snowflake / Sigma / Atlan / Zekelman | verify | — | verify | Resolve on next recall pass. |

## Modern tech / AI-native (stretch lane — manager-level OK, added 2026-07-07)
Jon asked to pursue modern tech companies even at manager level. These hire **product/analytics-engineering managers and data-platform leaders** on his exact stack (dbt/Snowflake/SQL/Python). Reality check: the bar is very high, comp is high, and most are hybrid in SF/NYC/SEA — so filter for remote or NYC-commutable, and lean on warm paths. Titles here run "Manager / Head of" more than "Director/VP," which is fine given the openness to manager roles.
| Company | ATS | slug / tenant | Status | Notes |
|---|---|---|---|---|
| Anthropic | Greenhouse | anthropic | validated | Analytics Data Engineering Manager, Product in pipeline (Job 14). Board also had "Data Science Manager, Supply" (DS lane). SF/NYC/SEA hybrid 25%. Sweep `boards-api.greenhouse.io/v1/boards/anthropic/jobs`. |
| Shopify | own site (shopify.com/careers) | — | no-api | Client-rendered; read with Chrome extension. Custom careers site, not a standard ATS — catch it via the lane-first recall pass plus any warm path you have. |
| Cursor (Anysphere) | verify (Ashby likely) | anysphere / cursor | verify | Small, elite bar; data/analytics-eng roles appear rarely. Resolve ATS at cursor.com/careers (check `jobs.ashbyhq.com/anysphere`). |
| Meta | own site (metacareers.com) | — | no-api | Data Engineering Manager / Analytics roles exist but no clean feed and a very high bar; browser/referral only. |
| _Also worth a periodic look_ | Greenhouse/Ashby | openai · ramp · notion · databricks | verify | AI-native / modern-stack peers that post analytics-engineering-manager and data-platform roles; resolve each ATS when a real opening appears. |

## Lane note (2026-07-04)
Data-platform **vendors** mostly hire data-**infrastructure/field** leaders, not internal data-function leaders — low yield for Jon's governance/enablement lane. **Enterprises with a large internal data org** (insurers, large SaaS like GitLab/Pluralsight/ServiceNow, healthcare, retail) are where his lane lives.  Weight the precision list toward those.

**Update (2026-07-11) — lane-first:** keep that weighting for the *precision* pass, but run the *recall* pass **title-first across all industries** (SKILL.md Step 2.5). In-lane roles at non-insurance / non-SaaS employers (manufacturing/IoT, nonprofit software, consumer tech, healthcare, devtools, EdTech, retail) are real fits — Jon has found several by hand — and must not be filtered out for being off-domain. Domain is a confidence tiebreaker, not a gate.

## In-lane companies outside the core domains — added 2026-07-11 (from Jon's own finds)
The lane lives in **any org with a real internal or client-facing data function**, not just insurers and big SaaS. Roles Jon found by hand prove the spread; poll these directly now, and treat their industries as in-scope for the title-first recall pass.
| Company | ATS | slug / tenant · wd# · site_id | Status | Notes |
|---|---|---|---|---|
| AssetWatch | Greenhouse | assetwatch | validated | Director of Data Platforms & Governance (pipeline Job 23). Manufacturing / predictive-maintenance IoT startup. Sweep `boards-api.greenhouse.io/v1/boards/assetwatch/jobs`. |
| Momentive Software (Community Brands) | Workday | communitybrands · wd1 · Momentive_External_Careers | validated | Director, Data Strategy & Services (pipeline Job 24). Nonprofit / association software. CXS `communitybrands.wd1/wday/cxs/communitybrands/Momentive_External_Careers/jobs`. |
| Yahoo | Workday | ouryahoo · wd5 · careers | resolved | Sr Director, Analytics (pipeline Job 20). Consumer media/tech; product-analytics/DS-heavy — watch for data-function (not DS-lead) roles. |
| GitHub | iCIMS | github.careers (iCIMS) | no-api → see sources.md iCIMS recipe | People/HR-analytics role was off-lane (Job 21), but GitHub's board carries data-platform/analytics-engineering roles worth watching. |
| Elios | staffing network (own site) | eliosai.com | no-api | Forward-deployed / staffing network, JS-rendered; confirm the end employer + permanence before trusting (Job 22). |

**Industries now explicitly in-scope** (no longer "low yield"): industrial / manufacturing / IoT, nonprofit & association software, consumer tech & media, healthcare & health-tech, devtools / modern-data-stack, EdTech, retail — anywhere with a sizable data org.

## Maintenance
- After each recall pass, promote newly-found fitting companies here with resolved ATS fields.
- Periodically re-test `validated`/`verify` endpoints; Workday tenants and site_ids change.

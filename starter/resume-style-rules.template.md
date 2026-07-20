# Resume & Application Text — Style Rules
_Personal preferences applied to every generated resume, cover letter, and outreach message, on top of resume-tailor's `de-ai-checklist.md`. This file is the source of truth — edit it to change the rules._
_Last updated: 2026-07-16_

## 0. Rule precedence (when two rules collide, higher wins)
_Adopted 2026-07-16 (pattern borrowed from the "annie" plugin's Section-A precedence block). Every other rule in this file, in the profile framing notes, and in `de-ai-checklist.md` sits under this order:_
1. **Honesty** — every claim traces to `career-profile.md`; no invented metrics, scope, or tools. Never overridden, by anything.
2. **ATS parseability** — the document must import cleanly (the §9 layout rules). A parse-safe document beats a prettier one that drops a role.
3. **Style & voice** — this file's formatting, capitalization, and `my-writing-style` voice.
4. **Tailoring preference** — keyword coverage, emphasis choices for a specific posting.

If clearing an ATS keyword target (4) would require a claim you can't defend (1), honesty wins and the score sits lower. If a voice choice (3) would make a title un-parseable (2), parseability wins. Apply the order the same way every time.

## 1. Work authorization: implicit, never explicit
- Do **not** add a "U.S. Citizen" or work-authorization line to the resume header or summary. 18+ years of continuous U.S. employment conveys it implicitly.
- Add an explicit citizenship/authorization statement **only** when a specific posting makes it a hard knockout (an active-clearance or ITAR-gated role that screens on it) — and confirm with the candidate before adding it, rather than defaulting it on. Cover letters and interviews are the place to raise it if needed, not the resume banner.

## 2. No em-dashes — and fix the cadence, not just the dash
- No em-dashes (—) in prose. Rewrite with a comma, colon, semicolon, parentheses, or split into two sentences. Swapping the dash for a comma is not enough; the sentence must not read as an interrupted AI aside.
- Numeric ranges are spelled out: "40 to 80 hours," not "40–80." Date ranges keep the conventional en-dash ("May 2019 – Jun 2022").
- Also remove the other AI tells from `de-ai-checklist.md`: rule-of-three cadence, uniform sentence length (vary it hard), hollow phrases ("leverage," "proven track record," "spearheaded," "seamless," "robust," "passionate"), and any brand tagline/voice. Prefer concrete specifics and real numbers.

## 3. Core competencies: short and scannable; tools live separately
- Each core competency is a **2–4 word phrase**. No long tool parentheticals inside a competency.
  - Bad: `AI & Automation Enablement (Cursor, GitHub Copilot, Atlassian Rovo, MCP, core agents)`
  - Good: `AI & Automation Enablement`
- Put specific tools and platforms in a separate compact **Technical Skills** block, grouped by capability. Keeps the competencies block scannable and the tools keyword-matchable for the ATS.
- **Technical Skills = 3 to 5 BROAD capability categories, never a per-tool taxonomy (senior-level best practice, adopted 2026-07-17).** At Director / Head-of level a long granular tool list reads junior and eats space better spent on leadership narrative; hiring managers want capability breadth plus a few flagship platforms, and the Core Competencies grid already carries the positioning. Consolidate to **four reusable buckets** and tailor by reordering items inside them (the full granular taxonomy lives in `career-profile.md` as the master to draw from):
  1. **Data Platform & Cloud** — warehouse, cloud, pipelines/transformation, languages (Snowflake, BigQuery/GCP, AWS, dbt, Fivetran, Airflow, Python, SQL, CI/CD)
  2. **Architecture & Modeling** — Medallion / Lakehouse, Data Mesh, Semantic Layer, Data Contracts, data modeling
  3. **Governance, Quality & Reliability** — governance, quality, observability, metadata & lineage, catalog, entity resolution, access controls, FinOps
  4. **BI, AI & ML Enablement** — Tableau / Power BI / Sigma; MLOps enablement, model-ready data, LLM tooling, AI-driven stewardship
  Agile / SAFe and other delivery methodology go in Core Competencies or the summary, NOT the Technical Skills block (and the SAFe cert already appears under Education). Keep four category headers stable across roles; tailoring = reorder the items, not rename the buckets.
- **Tailor the skills STRUCTURE to the target role's seniority (standard practice, adopted 2026-07-17):** the number and granularity of Technical Skills categories scales with the level being targeted.
  - **Executive / senior leadership (CDO, VP, Head-of, Director):** 3-4 broad categories (the four buckets above), 2-column competencies. Lead with capability breadth and flagship platforms; the leadership narrative carries the detail. **This is the default and the master resume's form — the default senior lane.**
  - **Manager / lead:** 4-5 categories — split a broad bucket where the role is more hands-on (e.g., separate BI from AI/ML, or Platform from Pipelines), 2-3 column competencies.
  - **Senior IC / staff / hands-on:** 5-6 granular, tool-forward categories with specific tools named per lane and a dedicated Languages/Tools line — at IC level the exact-tool match IS the screen.
  Down-level from the executive default ONLY when a specific posting is genuinely more hands-on (e.g., the "player-coach, build it yourself" roles). Expand granularity by drawing from the full pool in `career-profile.md`'s cross-role skills index; never invent tools to fill a more-granular structure.

## 4. Capitalization: match the register, and be consistent
- **Proper names stay capitalized** everywhere: products and platforms (Snowflake, dbt, GitHub Copilot, Vertex AI, Tableau, Power BI), named frameworks/patterns (Data Mesh, Medallion Architecture, SAFe, FinOps), and specific org/program/domain names (BI Enablement, Data Governance & Quality, Data Champion program, Enterprise Data Warehouse, Analytics & Data Science Enablement).
- **Generic concepts stay lowercase in running prose:** data and analytics, self-service adoption, data governance, data observability, change management, operational reliability, incident management, reference-data management. Capitalizing these mid-sentence reads as marketing/AI filler and is grammatically off.
- **Labels and headers are Title Case** because they are labels, not prose: the section headers, the core-competency phrases (Self-Service Analytics & Democratization), and job titles (Head of Data and Analytics). So "Data and analytics leader" (prose, lowercase) and "Head of Data and Analytics" (title, Title Case) are both correct — the register differs, the rule is consistent.
- The test: is the word a name/label, or a concept in a sentence? Name/label → capitalize. Concept in prose → lowercase. Apply it the same way every time.

- **In the Technical Skills and Core Competencies lists (a label context), named data concepts and disciplines take Title Case:** Data Contracts, Reference & Master Data, Metadata & Lineage, Master Data Management, Data Quality, Data Mesh, Medallion Architecture, Access Controls, Entity / Identity Resolution, Semantic Layer, AI-Driven Stewardship. They are labels in a list, not concepts in running prose, so they are capitalized here even though the same terms stay lowercase inside sentence bullets.

## 5. Honesty (unchanged)
- Every metric, title, and claim traces to `career-profile.md`. No invented numbers, no scale overreach, no skills you haven't claimed.

## 6. File output: no machine-generation tells
The document's metadata should be honest and free of the generator's fingerprints — **corrected, not disguised.** Two things to fix on every generated file:
- **Filenames stay human and simple.** Use `Firstname Lastname - Resume.docx` and `Firstname Lastname - Cover Letter.docx`. The company/role lives in the `applications/<company>/` folder, **not** baked into the filename. Role-encoded slugs like `Firstname_Lastname_Resume_BigCo_Data_Lead.docx` read as rote batch generation — drop them.
- **Normalize the document metadata (honestly).** Programmatic `.docx` generation misattributes the file (creator = "python-docx", a "generated by python-docx" description, a stale 2013 timestamp inherited from the library's template). Run `docx_finalize.py` after generating any `.docx` so: creator and last-modified-by = the candidate's name (they authored the content; the tool only rendered it); description and Company blank; created/modified = the real generation time; revision = 1 (first save); Application blank (assert nothing). It **corrects** the misattribution and drops the generator advert — it does **not** backdate the file, inflate the revision, or claim it was made in Word. The honesty rule applies to metadata too. Touches **only metadata**, never content.

- **Output both `.docx` and a text-selectable `.pdf`.** Render the finished .docx to PDF (never a scanned/image PDF). The .docx is safest for ATS parsing; the PDF is for human-facing sends (email, referrer) and applications that ask for PDF.
- **Where files live.** Tailored resumes and cover letters go in `applications/<company>/`. The generic / master resume goes at the **root of the `applications/` folder** (`applications/Firstname Lastname - Resume.docx` + `.pdf`), not the repo root.

Command: `python docx_finalize.py "in.docx" "Firstname Lastname - Resume.docx" --author "Firstname Lastname"`

## 7. Length: two full pages, filled by prioritized selection
- Target **two full pages** for these senior resumes. Not one, not a sparse second page with a few lines, not a spillover onto a third.
- Use **achievement selection as the lever**. The profile holds far more accomplishments than fit, so pick the ones most relevant to the target role first, then add the next-most-relevant until page two is full. If content spills onto a third page, cut the least-relevant bullets or tighten wording. Never shrink fonts or margins or pad with filler to hit the length.
- Prioritize by relevance to the role's thesis, then quantified impact, then recency. Lead each role with its strongest, most on-target bullet.
- **Verify by rendering.** After building, render to PDF and confirm it lands on two full pages; add or trim a bullet if it does not.

## 8. Name: show legal and preferred — Title Case, never all-caps
- Header name renders as **Firstname Lastname, M.S.** in Title Case. Do **NOT** use all-caps ("FIRSTNAME LASTNAME"): all-caps names parse worse on ATS import (some parsers mis-split or drop the name) and read as a template. Legal first name plus the preferred name in parentheses, so a background check matches the legal name while recruiters see the name he goes by.
- Apply the same Title-Case treatment to section headers AND company/employer lines — Title Case, never all-caps, anywhere in the document (adopted as the standard 2026-07-16; the master resume now complies).
- Document metadata author = **Firstname Lastname** (legal). Cover-letter signatures may use the preferred "Firstname Lastname."

## Scope
Applies to all generated application text: resumes, cover letters, and LinkedIn/warm outreach. When generating any of these, read this file and apply it alongside the resume-tailor skill.

## 9. Layout: NO standalone company-descriptor line; bold lead-ins OK (updated 2026-07-16)
- **Do NOT add a one-line italic company-descriptor line under the employer header.** It breaks ATS import: some parsers read that italic line as the *position* and drop the rest of that role's experience. (Adopted 2026-07-09 from an executive format; removed now for parseability — it was costing whole roles on import.)
- If a lesser-known employer needs context, weave a few words of scale into the role's **first bullet** instead, never as a separate line. Example: "Owned data platform and governance at Acme, a broadband business serving millions of subscribers, ..."
- **Employer block: one datum per line, in this exact order, no fields combined** (parsers mis-map combined lines — a real ATS import proved it):
  1. **Company name only** — e.g., `Acme Data LLC`. NEVER combine company with a role, alias, or employment type on one line: no `Company / Independent Consultant`, no `Company — Title`, no slashes. The parser reads the second half as the job title and shoves everything else into the description.
  2. **Job title only** — e.g., `Fractional Head of Data`. NEVER append the location to the title line — `Fractional Head of Data   Remote` gets parsed as one string and dumped into the description.
  3. **Location and dates together on their own line, pipe-separated, NOTHING but `City, ST | dates`** — e.g., `City, ST | May 2019 – June 2022`. Use `|` between location and dates, not `·` (the middot is nonstandard as a field separator). **Remote roles use the home city plain: `City, ST | September 2023 – Present`.** Two Workday import tests (Pfizer, 2026-07-16) proved the boundaries: a bare `Remote` leaves the location field blank, and `City, ST (Remote)` ALSO fails — the parser can't match the parenthetical as a location, so the whole string leaks into the role description. Only the exact `City, ST | Month Year – Month Year` shape imported cleanly. If remote-ness matters for a role, say it inside a bullet, never on the location line.
  Then the bullets. If an employment type like "Independent Consultant" matters, it is NOT a company and NOT glued to the title — make it the job title itself, or leave it out (it's implied by the entity name). Pick ONE title per role.
- **Earlier / Prior Experience uses the SAME per-role block format.** Never a run-in paragraph that lists several old roles together (`Old Employer (2008–2012). ...`) and never a "years supporting X" summary sentence *inside* the experience section — parsers grab one title/company and dump the rest into a role's description. Each prior role gets its own three lines (Company / Title / Location · Dates); a single bullet is optional, none is fine for old roles. Any "roughly N years doing X" framing belongs in the **Professional Summary**, not the experience blocks. Also keep multi-word company names intact (e.g., "The Former Employer Life Insurance Company of America") so runs don't merge into "Companyof".
- **Bold sentence-case lead-in on every experience bullet** stays — bold the opening outcome/action phrase (first clause), stop before a comma, colon, opening parenthesis, or conjunction, never end on a filler word (and/to/of/the/for), target a clean 3 to 8 word phrase. NEVER all-caps.
- **No punctuation of any kind inside a job title** (Pfizer/Workday imports, 2026-07-16): `Director of Data Governance, Platform & Apps` truncated at the comma, and the retest with ` - ` truncated at the hyphen at the same spot. Join with words instead: `Director of Data Governance and Platform & Apps`. Know the limit: Workday also rewrote `Fractional Head of Data` to `Head of Data`, which looks like normalization against a known-titles dictionary — so a nonstandard title may never import verbatim no matter the formatting. The imported field is editable; hand-correct it in the application form and keep the true full title on the document, which is what humans read.
- **No tables anywhere in the document** (same import): the Core Competencies grid was a real Word table and is a known parser hazard — some ATS abort or mis-segment at tables. Render competencies as plain paragraphs, one row per line with ` | ` between items. Nothing else in the resume may be a table, text box, or multi-column section.
- **Know when the document is no longer the problem** (third Pfizer/Workday test, 2026-07-16): with every line format-uniform and verified clean at the XML level, Workday still (a) left the location blank on the second consecutive "Present" role and leaked the text into its description, and (b) dropped the Former Startup title ("Head of Data and Analytics" — likely colliding with the adjacent normalized "Head of Data"). Identically formatted lines elsewhere in the same resume imported fine. These are parser quirks, not formatting defects — fix them by editing the fields in the application form (they are all editable) during the required human review, and do not keep mutating the document chasing them.

## 9b. ATS keyword check (run before you submit)
Before submitting any tailored resume, run the coverage check against that job's description:

```
python ats_match.py "applications/<company>/Firstname Lastname - Resume.docx" <jd.txt> --min 85
```

- **Aim for 85%+.** It prints what's missing, highest-value first.
- **Raise the score only with TRUE terms.** The tool splits gaps into skills you likely have (add them if
  they're in `career-profile.md` and you just didn't name them on THIS resume) versus terms you can't back up
  (e.g. a platform you've never used). Never add a keyword you can't defend in an interview to clear a number -
  that violates the honesty rule and gets caught in the screen. If the only way to 85 is a lie, let it sit lower.
- It's a keyword-coverage heuristic, not a literal ATS score. Treat 85 as a useful bar, not gospel.

## 10. Application short-answers (screening questions)
When a posting asks free-text screening questions (Why [company]? Why looking? experience prompts, etc.), answer in the candidate's voice per `my-writing-style` and save them next to the resume as `applications/<company>/application-questions.md` (one file, `## Question` headers, answer below each).
- **Voice:** direct and concrete, spaced hyphen ( - ) never an em-dash, real numbers and named tools, no AI-isms. Short is fine; a punchy honest opener ("Put simply -", "I'll be straight -") reads like the candidate.
- **Honesty first (the differentiator):** claim genuine strengths hard, and be candid about gaps rather than bluffing - e.g., "I haven't run Databricks hands-on, but the patterns carry," or "I have not acquired third-party consumer-data assets - that would be new." Candor consistently reads better than a stretch and pre-empts the screener's probe. Every claim still traces to `career-profile.md`.
- **Refuse-and-ask beats guessing (adopted 2026-07-16 from the "annie" plugin).** If any part of an answer can't be verified from `career-profile.md`, the answer bank, or something the candidate said in the conversation, do NOT improvise it. Write the verifiable part, mark the gap `[not stated — need from the candidate: <the specific question>]`, and ask him. A skipped sentence with a sharp question beats a confident fabrication every time — and it's the honesty rule (0.1) applied to answers, not a separate courtesy.
- **Portability test for any "Why [company]?" hook (adopted 2026-07-16 from "annie").** Before an answer or cover-letter opener ships, apply the test: _if this exact sentence could be sent to a different company unchanged, rewrite it._ The first sentence must name something true and specific about THIS company (a product, a stated value, a technical choice, a market position) that wouldn't be true of its competitor. A generic "I'm drawn to your mission and culture" fails the test.
- **Factual fields** (mailing address, how-heard, prior-employment): never invent. Use `[bracketed]` fill-ins for anything not in the profile (street address, ZIP) and flag them.
- **CHECK THE ANSWER BANK FIRST.** `application-answers.md` (repo root) holds canonical answers by question type - "Why [company]?", why looking, AI experience, Customer 360, cloud platforms, PII/compliance, leadership style, plus pre-written HONEST answers for the recurring gaps (Databricks, hands-on/IC, production MLOps, product analytics, third-party data, consumer/D2C, new industry). Start there, swap in the company-specific hook, and never send one unedited - the first sentence must name something true about *that* company. When a NEW question type comes in, answer it and then add it to the bank.
- **Reuse anchors:** keep a short list of your strongest reusable achievement anchors — the two or three stories that answer the most common prompts (a signature platform or identity build, a growth/adoption number, a quality or cost win, an executive-trust moment). Pick the ones the question calls for, and add new ones to the answer bank as they come up.

## 11. Cover-letter drafting order: approve the hook before the letter (adopted 2026-07-16 from "annie")
Don't draft a whole cover letter and present it for one all-or-nothing review. Gate it, so a wrong angle costs one sentence of rework instead of a page:
1. **Read the role** — pull the company name, exact title, and the two or three requirements the letter must answer. Map them to specific `career-profile.md` evidence first.
2. **Approval gate 1 — the "why this company" hook.** Draft ONLY the 1-to-2-sentence opener (the thing the portability test in §10 governs) and get the candidate's explicit yes before writing anything else. This is the sentence most likely to be wrong and most expensive to rewrite late.
3. **Approval gate 2 — the "where I add value" body.** Draft the body paragraph(s) mapping his record to the role, get the yes, then assemble the full letter. Every claim traces to the profile (rule 0.1); metrics stay exact, never rounded up to sound better.

The gates are hard stops, not suggestions — the whole system exists so a human approves every word before it goes out under the candidate's name.

## 12. Pre-send check: no unresolved placeholders in any deliverable (adopted 2026-07-16 from "annie")
Before ANY generated file or answer is handed over as final, scan it and confirm ZERO unresolved fill-ins survive: no `[bracketed]` prompts, no `{{tokens}}`, no `[NEED METRIC]`, no `[CONFIRM]`, no `<placeholder>` left in the text. A leftover bracket in a submitted résumé or answer is exactly the failure this system exists to prevent (it reads as careless and can leak the internal scaffolding). If a placeholder can't be resolved from the profile, it's a refuse-and-ask (§10), not something to ship with the bracket still in it. State "placeholder scan: clean" when presenting a finished document.

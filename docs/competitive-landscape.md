# Bellows — Competitive Landscape (mid-2026)

_Research snapshot of the AI career/job-search market, mapped against what Bellows does. Two uses: (1) an **enhancement backlog** (what the market has that we don't), and (2) **positioning** for the user guide (why choose Bellows). Pricing/features are from public sources as of mid-2026 — verify before quoting externally._

## Name collision — RESOLVED by rename (2026-07-20)
This project was formerly called **CareerForge**. **[careerforgeai.com](https://www.careerforgeai.com/)** is a live commercial product that already used that name in this exact space — a coaching/analysis funnel aimed at **professionals 40–60 facing AI-driven displacement** (hook: *"You're 47, 53, 58 — and AI just made your job a line item to cut."*), priced $9 one-time → $149/mo with "2,500+ success stories." They had market priority.

**Resolution: renamed to Bellows before any public release**, so the collision never reached a published artifact. Roughly 36 candidates were vetted for in-category collision across six naming strategies (craft, aspirational/journey, growth, other languages, coined, climbing).

The finding worth keeping, because it will recur for anyone naming in this market: **every name that directly expresses "coaching," "growth," "excellence," or "the path" is already taken — usually by career-coaching firms specifically.** Arete returned six coaching companies, Trellis two (one doing literal résumé/job coaching), Lodestar three, Aletheia six. Sisu was blocked by both SISU Careers and a class-9 software registration. Names survive by being **oblique** (a forge tool, a trail marker) or **invented**. "Bellows" was the only candidate with zero software-sector collision, and it takes a searchable descriptor ("Bellows Career System") without conflict.

**Features borrowed from their toolkit (shipped 2026-07-19), done our way:**
- **Résumé health score (0–100).** Their headline "Resume Analyzer." Ours is `engine/resume_score.py` — rule-based and local (ATS-safety + quantified-impact + concision), names the weak bullets, and makes *no* "benchmarked against real applicants" claim it can't back.
- **AI-displacement lens.** Their emotional hook, converted to honest coaching: a new **automation-exposure** step in `career-coach` that splits a role into automatable vs. durable work and steers skills + target roles toward the durable edge. Fires on "am I going to be replaced by AI."
- **Age-proofing.** Their "age-related language detection," done ethically: `resume-tailor/references/age-proofing.md` strips age *signals* (grad years, dated phrasing, the full backlog) without altering one real date or fact.

**Where we differ (lean in):** local-first/privacy (they're SaaS you upload your comp to), the whole-arc system vs. an assess-and-upsell funnel, no-fabrication traceability, runs on your existing Claude sub vs. a $9–149 ladder, and a real job pipeline + tracker (which they lack).

## The market, in five categories
Almost every competitor is a **point tool** — it does one job well and stops. Bellows spans the whole arc, on your own machine.

| Category | Representative tools (paid) | What they do | Typical price |
|---|---|---|---|
| **Auto-apply agents** | LazyApply, JobCopilot, Sonara, Jobright, AIApply, Sorce, Simplify (autofill) | Mass-submit applications for you; volume over fit | $24–249/mo |
| **Résumé builders / ATS optimizers** | Jobscan, Rezi, Teal, Enhancv, Resume Worded, Kickresume | Keyword-match a résumé to a JD, ATS scoring, templates | $9–50/mo |
| **Job trackers / CRM** | Huntr, Teal, Careerflow, Simplify | Kanban pipeline, contacts, doc storage, job clipper | $10–40/mo |
| **Interview prep** | Yoodli, Final Round AI, Big Interview, interviewing.io | Mock interviews, delivery coaching (filler words, pace) | $8–90/mo (human $179/session) |
| **Negotiation / coaching** | Mostly ChatGPT/Claude prompts + GPTs (no dominant dedicated tool) | Scripts, market data, roleplay | free–$20/mo |

**Open source** worth knowing:
- **JobSpy** (~3.3k★, MIT) — multi-board job scraper. *Bellows already uses it.*
- **Resume-Matcher** (~26.9k★, Apache) — résumé↔JD keyword/gap matcher, runs local Ollama or API.
- **AIHawk / Auto_Jobs_Applier** (feder-cr) — mass auto-apply agent (ToS/velocity risk).
- **ApplyPilot** (~33★, MIT) — self-hosted job-search companion (role analysis, fit scoring, company research, résumé rewrite, cover letters, dashboard, mock interviews, Chrome extension). **The closest all-in-one OSS comp** — but it auto-applies via extension and has no career-coaching depth.
- **Reactive Resume / JSON Resume / RenderCV** — OSS résumé builders.

## Feature comparison (Bellows vs. the field)

| Capability | Bellows | Auto-appliers | Résumé/ATS tools | Trackers | Interview tools |
|---|---|---|---|---|---|
| Reliable job discovery (ATS-direct, anti–ghost-job) | ✅ (JobSpy + ATS feeds, freshness-validated) | ~ (board reposts) | ❌ | ~ (clipper) | ❌ |
| Honest 1–10 fit scoring, gaps named, no fabrication | ✅ | ❌ (apply to everything) | ~ (ATS % only) | ❌ | ❌ |
| Résumé/cover tailoring from one source of truth | ✅ (ATS-safe, traces to profile) | ~ | ✅ (keyword-optimized) | ~ (Pro) | ❌ |
| Pipeline kanban + per-job detail + notes | ✅ (in-Hub) | ~ | ✅ | ✅ | ❌ |
| Warm-channel first (referrals, reconnect list) | ✅ | ❌ | ❌ | ~ (contacts) | ❌ |
| Interview prep (STAR bank, per-role Qs, mock) | ✅ | ❌ | ❌ | ~ | ✅ |
| **Career coaching** (self-assessment, 3–10yr roadmap) | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Negotiation** anchored to *your* comp targets | ✅ | ❌ | ❌ | ❌ | ~ |
| **First-90-days** ramp plan | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Local-first / data never leaves your machine** | ✅ | ❌ (SaaS) | ❌ (SaaS) | ❌ (SaaS) | ❌ (SaaS) |
| **Never auto-submits** (human-in-the-loop) | ✅ by design | ❌ (the whole model) | n/a | n/a | n/a |
| Cost | free (runs on your Claude sub) | $24–249/mo | $9–50/mo | $10–40/mo | $8–90/mo |

## Why Bellows (for the user guide)
Six things the market can't match — grounded in the research above:

1. **The whole journey, one system.** Competitors are point tools — a résumé builder *or* a tracker *or* an interview coach *or* an auto-applier. Bellows is the only thing that runs **self-assessment → positioning → roadmap → sweep → score → tailor → track → network → interview → negotiate → first-90-days**. The nearest all-in-one (OSS ApplyPilot, ~33★) has no coaching layer; Teal is the nearest paid one and stops at "get the interview."

2. **Your data never leaves your machine.** Every paid tool above stores your résumé, full history, and comp on their servers. Salary-negotiation privacy is a *documented* concern (researchers warn LLM salary advice can carry bias; employers report people over-relying on unverified data). Bellows keeps everything in a gitignored `personal/` folder on your computer — nothing is uploaded.

3. **It never auto-applies — and that's the point.** Auto-appliers are hitting a wall: LinkedIn's 2026 detection flags "human-impossible velocity" (100+ apps/hour), billing complaints are the top review theme, and mass-applied generic résumés damage your reputation. Bellows does the opposite — honest fit scoring, tailored applications, warm-intro-first — and **stops at the submit button** so you never risk your accounts or your name.

4. **Honesty over keyword-stuffing.** ATS tools optimize a résumé to "pass the scanner," which can drift into overclaiming. Bellows ties every bullet, metric, and claim to your real profile, flags `[NEED METRIC]` gaps instead of inventing numbers, and tells you to *skip* a role when the fit is a 4.

5. **Coaching, not just applications.** Most tools help you *apply*. Bellows coaches the *career*: what you actually want (values/HBDI self-assessment), a 3-to-10-year roadmap with honest gaps, a negotiation anchored to your own comp floor/target, and a first-90-days plan so the move sticks.

6. **Open, forkable, no subscription stack.** Replacing this stack with SaaS would run $60–200+/month across four or five tools. Bellows runs on the Claude subscription you already have, is fully forkable, and has no vendor lock-in.

## Enhancement backlog (what the market has that we could add)

**Shipped 2026-07-19** (from the CareerForge AI review): standalone résumé-health score (`engine/resume_score.py`), automation-exposure coaching lens (`career-coach`), and résumé age-proofing (`resume-tailor`). Next: surface the résumé-health score and the automation-exposure read **in the Hub** (currently CLI + skill only) so the value is visible without the terminal.

Ranked by value / fit with our principles:

1. **Human-in-the-loop autofill.** Simplify's killer feature is form-autofill on Workday/Greenhouse/Lever/Ashby (~85–90% accuracy). We refuse to *auto-submit* — but a browser helper that **fills the form and lets you review + press send** saves the tedium without crossing our line. High value, on-brand.
2. **Deeper ATS keyword scoring.** Rezi/Jobscan do section-by-section keyword density + hard/soft-skill coverage. We have `ats_match.py` (basic, now surfaced as the ATS % chip) — deepen it into a per-section coverage report in the tailoring step.
3. **Interview *delivery* coaching.** Yoodli scores filler words, pace, and conciseness on spoken answers. Our interview-prep does STAR + text mock drills — adding voice/delivery feedback would close the gap with the dedicated interview tools.
4. **Insider-connection discovery.** Jobright surfaces alumni/employees at target companies. We have warm-path via the reconnect list + LinkedIn import — extend it to *find* connections at pipeline companies automatically.
5. **Verified salary data in negotiation.** Experts warn against unverified AI salary numbers. Wire a real market-data source (Levels.fyi / BLS-style) into the negotiation skill instead of relying on the model's recall.
6. **Outcomes analytics.** Response rate, funnel conversion, time-in-stage — a small analytics panel on the Hub (the old board had an outcomes row) to show what's working.
7. **LinkedIn profile score.** Careerflow markets a profile "score + views uplift." Our linkedin-optimizer rewrites the profile; adding a before/after score would make the value legible.

_Deliberately **not** copying:_ mass auto-apply (the whole reason Bellows exists), visually-rich non-ATS résumé templates (ATS-safe is the point), and a hosted SaaS version (breaks local-first privacy).

## Sources
- [Sorce — Top AI job-search tools compared](https://www.sorce.jobs/blog/top-ai-job-search-tools-compared-review) · [JobHire — best auto-apply tools](https://jobhire.ai/blog/best-ai-auto-apply-tools) · [LoopCV — 20 best AI job tools](https://blog.loopcv.pro/20-best-ai-job-application-tools-bots-to-apply-faster/) · [LazyApply](https://lazyapply.com/) · [Jobright](https://jobright.ai/)
- [Rezi — best AI résumé builders](https://www.rezi.ai/posts/best-ai-resume-builders) · [Jobscan — best AI résumé builders](https://www.jobscan.co/blog/best-ai-resume-builders/) · [Teal](https://www.tealhq.com/) · [ResuFit pricing comparison](https://resufit.com/blog/best-ai-resume-builders-2026-pricing-features-ats-comparison/)
- [Huntr job tracker](https://huntr.co/product/job-tracker) · [Huntr pricing](https://huntr.co/pricing.html) · [ApplyArc — Huntr alternatives](https://applyarc.com/blog/huntr-alternatives)
- [Yoodli interview prep](https://yoodli.ai/use-cases/interview-preparation) · [FinalRound — best interview practice tools](https://www.finalroundai.com/blog/best-ai-interview-practice-tools) · [AceRound — Google Interview Warmup shutdown](https://www.aceround.app/blog/google-interview-warmup-review/)
- [Harvard PON — negotiating salary with AI](https://www.pon.harvard.edu/daily/salary-negotiations/how-to-negotiate-a-pay-raise-or-starting-salary-using-ai/) · [CNBC — don't make this AI negotiation mistake](https://www.cnbc.com/2025/10/08/dont-make-this-ai-mistake-in-salary-negotiations-says-hr-expert.html) · [PMC — bias in LLM salary advice](https://pmc.ncbi.nlm.nih.gov/articles/PMC11805401/)
- OSS: [JobSpy](https://github.com/speedyapply/JobSpy) · [Resume-Matcher](https://github.com/srbhr/Resume-Matcher) · [Auto_Jobs_Applier_AIHawk](https://github.com/feder-cr/jobs_applier_ai_agent_aihawk) · [ApplyPilot](https://github.com/Pickle-Pixel/ApplyPilot) · [builtwithjon — AI job-search repos](https://builtwithjon.com/articles/ai-job-search-tools-workflows-2026/)

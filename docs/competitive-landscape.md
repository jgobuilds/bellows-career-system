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

## Closest analog — SearchSteward (reviewed 2026-07-20)
**[searchsteward.com](https://searchsteward.com/)** — *"A job radar for the companies you actually want."* $19/mo (free tier: 25 companies, 50 scored matches, 10 AI evals). Built by a laid-off fintech professional using Claude, same as this project; [written up on r/ClaudeAI](https://www.reddit.com/r/ClaudeAI/comments/1uyky9u/). Hosted SaaS (React/TS + FastAPI + Postgres), US-only.

**The convergence is the headline.** Two people, independently, arrived at the same architecture — which is strong validation that these choices are right, not idiosyncratic:
- **Refuses to auto-apply**, explicitly ("We will never auto-apply for you"), for the same reason: auto-applied volume gets auto-rejected.
- **Deterministic scoring, not an LLM ranker.** Two-stage: hard gates (location/work-type, title exclusions, clearance, staleness) then weighted scoring (title match, required/preferred keywords, exact-title bonus, negative-keyword penalties, seniority multiplier). Their stated reason — *"I didn't want a black box deciding what you never see"* — is our "Why it scored" drawer in different words.
- **ATS-direct, avoids aggregators.** 40+ ATS platforms; they skip LinkedIn entirely to dodge the noise.
- Nice refinement worth copying: **sparse job descriptions drag the *confidence*, not the verdict** (~15%), so a title-only stub can't masquerade as a confident match.

**Their public benchmark: 104 applications → 23 screens (22%) → 13 interviews.** That is the number to beat, and it was achieved with *manual* applications off ATS-direct sourcing — i.e. this method demonstrably works.

**What they have that we don't (ranked by value):**
1. **Outcomes analytics** — response rate by score band, résumé-version performance, referral effectiveness, whether applying within 48 hours matters, and which JD keywords correlate with reaching a screen. This closes the loop from "we scored it" to "the score predicted reality." Our biggest gap.
2. **Gmail + Calendar sync** — the pipeline updates itself instead of requiring manual status changes.
3. **Ghost-job / scam detector** (free tool) — we validate freshness but don't name-and-shame ghost postings.
4. **Zero setup, multi-device** — hosted beats our ~1-hour local setup for non-technical users. Structural, and we accept it.

**Where we differ (lean in):**
- **They have no coaching layer at all** — no self-assessment, positioning, roadmap, interview prep, or first-90-days. They confirm interview prep is absent. They are a *search-and-track* system; we're a *career* system. This is the widest gap in our favour.
- **Local-first.** Their résumé lives on their servers (they promise never to sell it; still a server). Ours never leaves the machine.
- **No-fabrication traceability.** Their tailoring is "ATS-optimized" prompting, which the founder candidly says "works, but could be better." We trace every claim to the profile and flag `[NEED METRIC]` rather than inventing.
- **Warm-path routing.** They *measure* referral effectiveness; we *route* senior roles through referrals first.
- Free and AGPL vs $19/mo closed source.

_Also noted in that thread: **[career-ops](https://github.com/santifer/career-ops)** (OSS, CLI, AI-heavy — closer to us in spirit, but token-hungry and command-line only), plus bypass.uno and jobs.myrlin.io (auto-apply, waitlisted)._

## Closest architectural twin — suraj-davariya/ai-job-search (reviewed 2026-07-20)
**[github.com/suraj-davariya/ai-job-search](https://github.com/suraj-davariya/ai-job-search)** — MIT, ~14★, 128 commits, actively developed. And, with some irony, **it is also named "CareerForge"** — a third independent claimant on the name we just left. That retroactively confirms the rename was right, not over-cautious.

This is a nearer relative than SearchSteward: where SearchSteward is a hosted SaaS, this is a **local-first toolkit that runs inside Claude Code** — the same shape as our folder mode. Slash commands (`/setup`, `/search`, `/apply`, `/upskill`, `/expand`, `/reset`), a profile built by interviewing you, tailored CV + cover letter per role, and a **loopback-only local dashboard** (Next.js on `127.0.0.1:4480`) reading a flat CSV as the single source of truth. Ours is `hub.html` + `server.py` over `pipeline.md`. Same idea, different file format.

**Three independent implementations now share our core principles**, which is about as much design validation as this space offers: local-first with nothing uploaded, never auto-submits, no fabricated skills, and a profile-as-single-source-of-truth.

**Worth stealing (ranked):**
1. **Adversarial reviewer pass.** After drafting the CV and cover letter they spawn a *second* agent to critique it, apply revisions, and independently verify claims made about the company. We have the de-AI checklist and integrity flags, but nothing adversarial. This fits our honesty rule better than it fits theirs.
2. **`/expand` — competency discovery with source attribution.** Mines your own documents, GitHub repos, and the web for skills you never wrote down, and adds only approved items *with the source recorded*. That is the no-fabrication rule pointed in the opposite direction: not "don't invent," but "go find the evidence you forgot." It would directly attack our `[NEED METRIC]` backlog.
3. **`/upskill` — gap analysis → researched learning plan** against the roles actually in your tracker. Our `career-coach` names the skills to acquire; it doesn't build the study sequence.
4. Cover letters written in the *posting's* language, plus 12-language localisation. Not a priority for a US search, but a real capability we lack.

**Where we're stronger:**
- **Coaching arc.** Their own docs say it "does not provide active coaching." They have interview prep and upskill; no self-assessment, positioning, 3–10yr roadmap, weekly accountability loop, negotiation, or first-90-days.
- **Sourcing quality.** They search job portals via **web search**; we poll ATS endpoints directly (Greenhouse/Lever/Ashby/Workday). Direct polling is the thing both we and SearchSteward independently concluded beats aggregator noise.
- **`.docx` over LaTeX PDF.** They compile beautiful two-page LaTeX CVs. Ours are `python-docx`, and deliberately so: our format rules were learned from real ATS import failures (Workday truncating titles at commas, blank-title imports). A LaTeX PDF is prettier and parses worse. This is a genuine advantage, not a gap.
- **Warm-path routing** (reconnect list, referral-first for senior roles) and **negotiation anchored to your own comp floor** — neither exists there.

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

Ranked by value / fit with our principles. **#1 was promoted to the top after the SearchSteward review (2026-07-20)** — it's the one gap a direct competitor has already proven valuable, and without it the scoring rubric can never be validated against reality:

0. **Outcomes analytics — the feedback loop.** Right now a score of 8 is an *assertion*; with this it becomes a *prediction that can be checked*, and the weights get tuned from evidence instead of intuition. Both close competitors have this and we don't. Concrete spec, informed by seeing both:

   **The one view neither of them fully builds — build this first:** a **score band × outcome cross-tab.** SearchSteward claims "response rate by score band"; [ai-job-search's dashboard](https://suraj-davariya.github.io/ai-job-search/dashboard/) shows a fit-distribution histogram but not distribution *against outcome*. A histogram tells you how you scored things; the cross-tab tells you whether the scoring **works**. If 8s and 5s convert identically, the rubric is decoration.

   **Supporting views (their visual vocabulary is good, borrow it):** a 4-KPI header — total applied, velocity with a 7d/30d toggle, average score, and **response/interview rate**; applications-per-week bars; a status-mix funnel; and a **contribution-graph activity calendar**. That last one isn't a vanity metric for us: `career-coach`'s weekly loop is explicitly "manage inputs, not outcomes," and it currently makes the user read `pipeline.md` by hand to count reps. An activity graph *is* that loop, rendered.

   **Data we still need:** a response/outcome field and its date (we have `status` but no dated transitions), and which résumé version went out. Everything else — dates, scores, `warm` flag, company — is already in `pipeline.md`.

   **Benchmarks to measure against:** SearchSteward reports 104 applications → 23 screens (22%); ai-job-search's demo shows a 21% interview rate. Two independent implementations landing near ~20% gives us a target instead of a guess.

   _Design note: their dashboard answers "how am I doing"; our Hub answers "what do I do next" (Next-step banner, launchers, kanban). These are complements, not substitutes — add the retrospective view without burying the action view._

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

---
name: resume-tailor
description: Generate a tailored resume and cover letter for a specific target job by reading the user's stored personal/career-profile.md, selecting the most relevant real accomplishments, and matching the job description's terminology so the resume parses cleanly and scores well in modern ATS platforms (Workday, Greenhouse, Lever, iCIMS, Taleo) without deception. Use whenever the user wants to tailor, optimize, or generate a resume/cover letter for a specific role, make a resume "ATS-friendly" or "get past the ATS," align a resume to a job description, or make a resume "not look AI-generated." This is a spoke of the career system — it reads the profile that the career-profile skill builds. If no personal/career-profile.md exists yet, direct the user to build one there first. Produces unique output per job by re-selecting and re-aligning against each specific job description.
---

# Resume Tailor (Spoke)


> **Where files live (READ THIS):** every user-specific file lives in the gitignored `personal/` folder — read from it and write to it, never anywhere else in the repo. The profile is `personal/career-profile.md`; tailored résumés, cover letters, and job specs go in `personal/applications/<company>/`; the pipeline board is `personal/data/pipeline.md` + `personal/data/jobs.json`; other user files are `personal/reconnect-list.md`, `personal/application-answers.md`, `personal/writing-style.md`. Settings live in `personal/userconfig.py`. **Anything you create for the user goes under `personal/`** — nothing user-specific is ever written into the tracked repo.
Reads the user's stored `personal/career-profile.md` and a target job description, then generates a resume + cover letter tuned to that one job. Part of the career system:
- **career-profile** (hub) builds the profile → run it first if none exists.
- **resume-tailor** (this) → resume + cover letter for a job.
- **network** → warm-intro / LinkedIn messages.

## Start here
1. **Load the profile.** If the career folder is mounted (Cowork / Claude Code), read `personal/career-profile.md` from it directly — don't ask for an upload. Otherwise, ask the user to upload `personal/career-profile.md`. If they don't have one, send them to the **career-profile** skill to build it — don't collect a full history from scratch here; that's the hub's job. (If the user only has loose resumes and won't build a profile, you can proceed in a degraded mode by treating the pasted resumes as the inventory, but recommend building the profile for reuse.)
2. **Get the target job description** — full text or paste.

## The one rule
**Only use what's in the profile.** Every bullet, metric, title, and skill must trace to `personal/career-profile.md`. Never invent numbers or add skills the user hasn't claimed. If a bullet the profile marks `NEED METRIC` is a strong fit, use it without the fake number and ask the user if they can supply one. Fabrication is both dishonest and the #1 AI tell — and it collapses in the first real conversation.

## What "get past the ATS" actually means
ATS platforms are parsers + databases + an LLM summary layer that reads the *already-parsed text*. They are not secret AI rejecters. The real failure modes: (1) parse failure from two-column layouts, tables, text boxes, headers/footers, images; (2) genuinely missing keywords; (3) knockout questions (authorization, years, location) that no resume trick touches. So the goal is **parseability + genuine keyword match + fast human readability** — never hidden text, white-on-white stuffing, or invisible layers, which are detected as manipulative in 2026 and backfire. If the user asks for tricks, explain why they hurt and redirect. Do not produce them.

## Workflow

### 1 — Analyze the target profile
From the JD, extract must-haves vs. nice-to-haves, the company's exact terminology, the seniority signal, the role's thesis (build / scale / turnaround / governance), and knockout risks. Build a keyword list with acronym/full-form pairs. Full method in `references/target-analysis.md`. Name knockout flags to the user directly — they're pass/fail.

### 2 — Select and align (the core move, and the source of per-job uniqueness)
For each role in the profile, **select** the 2-5 accomplishments whose Themes best match the target thesis and must-haves; drop the rest. Then align the *language* of selected bullets to the JD's terminology without lying — if the user did the thing under a different name, use the JD's word (or both). Method + synonym maps in `references/keyword-synonyms.md`. This re-selection against each specific JD is what makes every generated resume unique — the profile is constant; the selection and phrasing are computed fresh each time.
- Lead each role with its highest-impact, most-relevant bullet.
- Put the strongest quantified outcomes near the top of the resume.
- Matching vocabulary ≠ adding a keyword for work the user didn't do. Honest gaps stay gaps.

**Get the ratio right (2026 reality).** Keyword alignment is table-stakes, not the differentiator — and over-indexing on it actively backfires now. Semantic ATS matching already bridges most synonyms, and recruiters/hiring managers report that AI-mirrored, keyword-stuffed resumes read as hollow boilerplate at the human stage, where the real decision happens. So do the keyword match cleanly, then stop optimizing it. Spend the real effort on the **leadership narrative**: each senior bullet should read as a micro-story — what you did, how, and the "so what" (the business outcome). "Consolidated 3 vendor contracts, cutting spend $2M/yr" beats a keyword-dense duty line every time, for both the parser AND the human. If a resume is winning on keyword density but losing on narrative clarity, it's optimized for the wrong reader.

**Lead with the skill-stack.** In the summary/leadership snapshot, position the profile's skill-stack — the unique *combination* of technical + strategic + interpersonal strengths — as one fused value proposition, not three separate skill lists. This is the executive differentiator; few candidates can claim the same pairing. Pull it from `personal/career-profile.md`.

**Surface AI fluency where real.** If the profile has genuine AI/automation leadership and the target role values it (most data-leadership roles in 2026 do), surface it with context — what you led, why, the outcome. If the profile flags AI fluency as a gap, don't invent it; note to the user it's a likely gap for this role and let them decide how to address it (honestly) elsewhere.

### 3 — Assemble the resume
Use the ATS-safe structure in `references/ats-format-rules.md`: single column, standard headers, contact in the body, consistent `Month YYYY` dates, no tables/graphics/text boxes, selectable text. Lead with a short leadership snapshot + core-competencies keyword block for leadership roles. Deliver clean `.docx` by default (most universally parsed). **Finalize the file:** give it a human filename (`Firstname Lastname - Resume.docx`, company in the folder not the filename) and scrub the metadata so it doesn't read as machine-generated (author = the candidate, no library fingerprint, plausible recent timestamps). See `ats-format-rules.md` → File naming & metadata. **Target two full pages** and verify by rendering to PDF, using achievement selection (add or trim) to fill page two without spilling to a third.

**Quick health check.** After writing the spec, run `python engine/resume_score.py personal/applications/<company>/resume.json` for a fast 0-100 read across ATS-safety, quantified impact, and concision. It names the weak (unquantified) bullets and any structural warnings to fix *before* you build the `.docx` — a rule-based sanity check, not a benchmark. Aim to clear the ATS warnings and quantify what the profile can honestly support.

**One bullet, one claim.** The bold lead-in states what a bullet is about, and everything
after it has to serve that claim. A trailing *"I also led X"* is a second, unrelated claim
riding on the first, and it costs twice: the lead-in stops describing the bullet, so a reader
scanning lead-ins is misled about what the line holds, and the appended claim gets a
subordinate clause where it needed its own line — reading as an afterthought because it was
appended as one. The fix is a decision rather than a rewrite: the claim earns its own bullet,
merges into the neighbouring bullet that already covers that topic, or does not belong on this
document. `resume_builder.validate()` warns on the explicit `I also` / `Also,` join and on
nothing inferred, because "these two sentences feel unrelated" is a judgement and a gate that
makes judgements gets suppressed.

**"I" vs "we" vs neither is decided by the CLAIM, not by tone.** Swapping globally in either
direction costs the candidate, so decide per clause. A **judgment or decision** takes **I** —
the decision itself is the evidence, and "we chose" hands away the thing being assessed.
**Execution or delivery** takes **we** — nobody believes a director personally ran every
pipeline, and "I ran" invites a hands-on question a leadership candidate does not want. A
**leadership action** takes **neither**: `Led a 25-person organization` reads strongest with an
implied subject, and that is where most bullets belong. The question only arises in a bullet's
second clause, since a lead-in verb has already settled it. Note the failure modes differ by
artifact and do not conflict: a résumé fails by being **ambiguous** about attribution, an
interview answer fails by being **evasive** about what the candidate personally did.

**People are never the obstacle, and a team is never an "it".** Two phrasings pass every other
check and still say the wrong thing about how someone leads. **Change-leadership bullets that
name colleagues as what was defeated** — "overcoming years of institutional *resistance*",
"winning over the skeptics", "fighting for buy-in" — cast the people who were brought along as
adversaries, in the very sentence meant to prove the candidate brings people along. Name what
was *entrenched* rather than who was in the way ("institutional habit", "a decade of established
practice"); the difficulty stays, the adversary goes. And **a team is people, so it takes
"they", not "it"** — a bullet about developing engineers that reads "giving *it* a roadmap …
*it* began experimenting" undercuts its own claim. Avoid `headcount`, `FTEs`, `resources` and
`bodies` for people too. Check both before the de-AI pass; neither is a grammar error, so
nothing else will catch them.

### 4 — Cover letter
Short, specific, built on genuine profile↔target overlap. Structure and rules in `references/cover-letter.md`. No boilerplate openers/closers.

### 5 — De-AI pass
Run the whole output through `references/de-ai-checklist.md`: kill em-dash-and-tricolon cadence, cut hollow phrases, vary sentence length, prefer real specifics. If the honesty rule held, the writing is already mostly human.

**Age-proofing (when relevant).** For a candidate with ~20+ years, or one worried about age bias, also run `references/age-proofing.md`: strip the *signals* (graduation years, dated language, the full backlog) without touching a single real date or fact. It's signal-removal, not deception — the same honesty rule applies, and anything that would misrepresent when or where they worked gets surfaced to the user, not changed.

**Apply the user's standing style overrides.** If a `resume-style-rules.md` sits in the career folder (alongside personal/career-profile.md), read it and enforce it here too — it captures per-user preferences (e.g., implicit citizenship, no em-dashes, concise competencies) that override defaults. These are cheap to miss and expensive to re-do.

### 6 — Persist and sync the pipeline (folder mode)
If the career folder is mounted (Cowork / Claude Code): save the resume and cover letter under `personal/applications/<company>/` inside that folder, then — in the same turn, not at session end — update the job's row in `personal/data/pipeline.md` (status → `tailored`, document paths recorded in its detail block) and refresh the `JOBS DATA` block in `dashboard.html`. The apply-pipeline skill owns the row format and the dashboard-refresh procedure; keep one source of truth. In chat mode, deliver the files and remind the user to update their personal/data/pipeline.md.

## Interaction principles
- Discuss, don't just comply — correct framings that will hurt the user.
- Batch metric questions rather than inventing figures.
- Surface tradeoffs (dropped bullets, title/seniority mismatches) and let the user decide.
- For leadership roles, remember the resume is often not the bottleneck — referrals and recruiters matter more. If the user is cold-applying only, it's worth naming that, and pointing them to **network** for the warm-network angle.

## Brand
If the user has brand standards, apply a **calibrated** brand to the resume, not full brand and not zero: name and section headers (and header rules) in the brand's primary color; ALL body text stays black; fonts stay universally-installed (Calibri/Arial), never brand display fonts — font substitution on the reader's machine is a real parse/render risk. No fill
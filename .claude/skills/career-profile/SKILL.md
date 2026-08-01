---
name: career-profile
description: Collect, structure, and store a person's complete career history into one durable, reusable master profile file (personal/career-profile.md) that the resume-tailor and network skills both read from. Use whenever the user wants to build, update, or maintain their career profile; consolidate multiple resumes/CVs into one source of truth; capture a new role, project, or accomplishment; or set up the shared foundation before tailoring resumes or writing outreach. This is the FIRST skill to run in the career system — the hub. Always build or load the profile here before generating any resume, cover letter, or outreach message. Triggers include "build my career profile," "here are my resumes," "add this project to my profile," "update my career history," or starting any job-search workflow.
---

# Career Profile (Hub)


> **Where files live (READ THIS):** every user-specific file lives in the gitignored `personal/` folder — read from it and write to it, never anywhere else in the repo. The profile is `personal/career-profile.md`; tailored résumés, cover letters, and job specs go in `personal/applications/<company>/`; the pipeline board is `personal/data/pipeline.md` + `personal/data/jobs.json`; other user files are `personal/reconnect-list.md`, `personal/application-answers.md`, `personal/writing-style.md`. Settings live in `personal/userconfig.py`. **Anything you create for the user goes under `personal/`** — nothing user-specific is ever written into the tracked repo.
This is the hub of a three-skill career system. It owns one durable artifact — `personal/career-profile.md` — a complete, deduplicated, structured record of everything the user has ever legitimately done professionally. Two spoke skills read from it:

- **resume-tailor** → generates a tailored resume + cover letter for a specific job.
- **network** → generates warm-intro / LinkedIn / referral messages.

The profile is the leverage: built once (well), then reused for every application and every outreach message, so the user never re-explains their career.

## The one rule that governs the whole system

**Only capture what's real.** Every role, bullet, metric, date, title, and skill in the profile must trace to something the user actually provided. Never invent numbers, inflate scope, or add skills the user hasn't claimed. Fabricated specifics are both dishonest and the #1 tell that downstream output was AI-generated — and they collapse the moment the user reaches a real conversation. When a real accomplishment lacks a metric, capture it with a `[NEED METRIC: ...]` flag rather than inventing one, and ask the user to fill it.

## How storage works (be honest with the user about this)

The profile lives in `personal/career-profile.md` — human-readable Markdown the user can eyeball and edit directly. How it persists depends on the environment:

**Folder mode (Cowork / Claude Code — the career folder is mounted):** read and write `personal/career-profile.md` in the folder directly. Updates are saved the moment they're made — no re-uploading, no end-of-session save step. When the user mentions a new role, project, metric, or correction mid-conversation, write it into the file then and there.

**Chat mode (claude.ai, no file access):** skills have no persistent memory between sessions. "Stored for reuse" means **a file the user keeps and re-uploads**, not an automatic database. Don't oversell this as seamless memory. Tell them plainly: "Save this file. Re-upload it whenever you want to tailor a resume or write outreach, and bring it back here whenever you want to add something new."

## Workflow

### Phase 1 — Collect
Ask the user for:
- **Every existing resume / CV** they have (all versions — more raw material means better selection downstream).
- **LinkedIn** content (About, experience, recommendations) if available.
- Anything else: performance-review highlights, brag docs, project retros, promo packets. These often hold the best metrics.

If a `personal/career-profile.md` already exists, load it first and treat this as an *update*, not a rebuild — merge new material in, don't overwrite.

### Phase 2 — Structure
Read everything and compile the master profile using the exact schema in `references/profile-schema.md`. Core moves:
- One entry per role, with every distinct accomplishment as its own bullet (the union across all source resumes — never merge two accomplishments into one inflated bullet).
- Tag each bullet with **themes** (e.g., team-building, ML, cost-reduction, governance, 0→1 build, turnaround) so the spokes can select fast.
- Capture skills/tools per role AND in a cross-role index.
- Record scope: team size, budget, reporting line, seniority progression.
- Capture the **skill-stack** — the unique *combination* of technical + strategic + interpersonal strengths that differentiates this person (not a longer skills list; the fusion few others pair). This is the executive differentiator in 2026 and every spoke uses it. See the schema.
- Capture **AI fluency** — genuine instances of using or leading AI/automation, with context. Increasingly a baseline leadership competency for data roles. If there are none, record that honestly as a gap to discuss — never manufacture AI experience.
- Flag every bullet lacking a hard result as `[NEED METRIC]`.
- Flag inconsistencies across resume versions (dates, titles, metrics that grew between versions) and ask the user which is correct — don't silently pick.

### Phase 3 — Fill the gaps
Batch all `[NEED METRIC]` flags and any inconsistency questions and ask the user together — not one at a time. Fill in their real answers. Leave flags that stay unanswered visibly marked so they never ship by accident.

### Phase 4 — Store and hand off
Save `personal/career-profile.md` and give it to the user with clear instructions to keep it. Tell them what's next:
- To tailor a resume for a job → use **resume-tailor** (upload this profile + the job description).
- To write warm-network / LinkedIn outreach → use **network** (upload this profile + who they're contacting).

## Onboarding essentials — capture targets + comp (route to `personal/userconfig.py`)
The profile is the WHO. Two more things drive the rest of the system, and onboarding is
where to nail them down. As part of the first profile build, **explicitly ask for and
confirm these, then offer to write them into `personal/userconfig.py`:**

1. **Current role** — exact title. → the profile snapshot AND `userconfig.CURRENT_ROLE`.
2. **Target roles + target industry** — the titles they'd accept and the industries they're
   strongest in or aiming for. → `userconfig.TARGET_TITLES`, `LANE_STRONG`, and `DOMAIN_BONUS`.
   **These drive the sweep** — get them right and apply-pipeline surfaces the right roles for their
   target role and industry.
3. **Compensation** — current base, established-company floor, target base range, and the hard
   walk-away. → `userconfig.CURRENT_COMP`, `COMP_FLOOR`, `COMP_TARGET`, `COMP_HARD_FLOOR`.
   **The negotiation skill reads these**, and apply-pipeline uses them to flag step-downs.
4. **Target companies** — seed the sweep's precision layer, don't leave it empty. **Actively
   research** a starter set of companies that fit the user's lane, level, domain, and role
   shapes — include any they name, any where they have a warm contact, and companies matching
   their stack/philosophy — then **resolve each one's ATS** (Greenhouse / Lever / Ashby /
   SmartRecruiters / Workday; recipe in apply-pipeline's `references/target-companies.md`) and
   add them to `userconfig.COMPANIES`. This is the **highest-signal sweep source and it
   compounds** — apply-pipeline adds more as it discovers them, but seeding a real starter set at
   onboarding means the first sweeps aren't empty. Never guess an ATS slug; resolve it against the
   live endpoint or mark the entry `"status": "verify"`. (Also confirm **location/remote** and any
   **dealbreakers** → `LOCATIONS` / `GEO_*` / `HARD_GATES`, and pull the "why" from
   `personal/self-assessment.md` if it exists.)

Don't skip comp because it feels awkward — a search with no floor wastes time on roles that
can't clear it, and negotiation with no target flies blind. If the user is unsure, capture a
range and mark it to refine later.

## Optional: intake UI
If the user wants a reusable front door for collection, build the interactive intake artifact in `references/intake-app.md` (branded if they have brand standards). It gathers resumes + fills metric gaps in one place and exports the structured profile. The artifact organizes input; the structuring judgment still happens here in the workflow.

## Interaction principles
- **Discuss, don't just comply.** If the user's framing will hurt them, say so and offer the version that works.
- **Ask for metr
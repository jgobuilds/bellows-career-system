---
name: linkedin-optimizer
description: Rewrite and optimize the user's LinkedIn from career-profile.md, aligned to their target roles and in their own voice. Produces a keyword-rich positioning headline; a first-person About that tells the story and states the value proposition; experience entries consistent with the résumé but LinkedIn-appropriate; a Skills section that pins modern, target-relevant skills above legacy ones; and a strategy for Featured, recommendations, "Open to Work", and the custom URL. LinkedIn is top-of-funnel — how recruiters find you and how warm intros vet you — so it optimizes for search + credibility, not just résumé copy. Triggers: "improve my LinkedIn", "rewrite my headline / About", "optimize my profile", "make me findable to recruiters", "LinkedIn audit", "what skills should I list", "personal brand". Reads career-profile.md, userconfig target titles/lane, and voice-profile. Writes personal/linkedin/.
---

# LinkedIn Optimizer (Branding Spoke)

Your résumé is read once, by one person, after they're already interested. Your LinkedIn
is searched by recruiters who've never heard of you and vetted by everyone a warm intro
sends your way. This skill makes it work as **discovery + credibility**, not a résumé paste.

> **Where files live (READ THIS):** every user-specific file lives in the gitignored `personal/` folder. Source is `personal/career-profile.md`; targets are `personal/userconfig.py` (TARGET_TITLES / LANE_* / DOMAIN); voice is `personal/writing-style.md`; output goes in `personal/linkedin/`. Read from and write to `personal/`.

## What makes LinkedIn different from the résumé (calibrate for it)
- **Public + networked + searched.** Recruiters find you by keywords; write for search AND for a human skimming in 5 seconds.
- **First person, a little warmer.** "I build…" not "Built…". It's your voice (use `personal/writing-style.md`), not résumé shorthand.
- **Consistency is verification.** Titles, dates, and employers must match the résumé and a background check. A LinkedIn/résumé mismatch is a red flag — pick one title per role and use it both places.
- **Same honesty rule.** Every claim traces to `personal/career-profile.md`. No inflated scope, no invented metrics.

## Workflow — section by section (details in `references/guide.md`)

### 1 — Headline (the single highest-leverage field)
Not just your job title. Combine **searchable keywords** (the target titles/lane from
`userconfig`) with a **positioning line** (what you're known for). ~3 segments separated by
`|`. It shows in every search result, comment, and connection request — earn the click.

### 2 — About (the story + the value proposition)
First person, in the user's voice. Structure: a hook (the through-line), what you do and for
whom, a couple of proof points (real numbers from the profile), the positioning/"why", and a
soft call to connect. This is where the force-multiplier / signature framing lives — warmer
than the résumé summary, same substance.

### 3 — Experience
Mirror the résumé's substance (consistent titles/dates/employers) but LinkedIn-appropriate:
a short role framing + the strongest outcomes. Slightly more narrative than résumé bullets is
fine. Keep it aligned so a recruiter reading both sees one coherent story.

### 4 — Skills (pin the right ones; demote the dated)
Recruiters and LinkedIn's search weight the top skills. **Pin the modern, target-role skills**
(the lane from `userconfig`) at the top; **demote or drop legacy/dated skills** that age you or
pull off-target. Then a plan to solicit endorsements on the pinned ones.

### 5 — The rest (quick wins)
Featured (a portfolio piece / post / the résumé), a recommendations ask strategy (who + what to
prompt them for), "Open to Work" (recruiters-only vs. public green banner — advise the trade-off),
a clean custom URL, and location/industry set to the target. See `references/guide.md`.

## Output
Write `personal/linkedin/` — one file per section (`headline.md`, `about.md`, `experience.md`,
`skills.md`) or a single `linkedin-profile.md` the user can paste in section by section. Note
which fields to change in Settings vs. paste into the profile body.

## Guardrails
- **Traces to the profile.** No claim on LinkedIn that isn't true and in `career-profile.md`.
- **Consistent with the résumé.** One title per role, matching dates/employers. Mismatch = red flag.
- **Their voice.** Use `personal/writing-style.md`; avoid LinkedIn-cliché mush ("results-driven thought leader passionate about synergy").
- **Keyword-honest.** Use the exact target terms the user actually owns — for search, not stuffing. Never list a skill they can't back up.

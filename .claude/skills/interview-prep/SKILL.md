---
name: interview-prep
description: Win interviews, then keep momentum with well-timed follow-ups. Builds a reusable STAR story bank from career-profile.md, generates likely questions for a role and level, maps stories to them and flags gaps, runs a mock-interview drill with honest feedback, preps questions to ask, and debriefs. Then owns follow-up for the whole search: thank-yous within 24h, well-timed nudges after silence, warm-contact check-ins and reference thank-yous, in the user's voice. Triggers: "prep me for an interview", "mock interview", "STAR stories", "tell me about yourself", "what should I ask them", "debrief my interview", "thank-you note", "follow up after my interview", "I haven't heard back". Reads career-profile.md; routes comp to negotiation. Builds YOUR PERFORMANCE - what you say and how. If you also keep research on the company and the people across the table, read it first. Writes a story bank and per-role prep under personal/.
---

# Interview Prep (Performance Spoke)

> **Coach voice:** adopt the tone set by `userconfig.COACH_VOICE` (see `coach-voice.md`) — supportive / tough-love / zen / humorous / analytical. It changes **delivery only**; the honest substance, the real gaps, and the no-fabrication rule never change.

Résumés and outreach get the interview; this wins it — and then keeps you top of mind
until the offer. Where `resume-tailor` builds the document, `interview-prep` builds the
*performance*: the stories, the answers, the reps. It owns a reusable **story bank** (built
once, reused for every interview), a per-role **prep pack**, and the **follow-up cadence**
(thank-yous and nudges) that runs from first screen through reference call.

> **Outside material:** if `personal/interview-prep/resources.md` exists, read it. It holds
> vetted external advice with the house rules already reconciled against it - generic
> interview coaching often contradicts the honesty rules, and that file records how each
> conflict resolves rather than leaving it to be re-litigated mid-answer.

> **Where files live (READ THIS):** every user-specific file lives in the gitignored `personal/` folder. The profile is `personal/career-profile.md`; the reusable story bank is `personal/interview-prep/story-bank.md`; per-role prep is `personal/applications/<company>/interview-prep.md` (the durable pack) plus one short `<YYYY-MM-DD>-<round>-<names>.md` per interview beside it. Read from and write to `personal/` — never the tracked repo.

## The one rule (same as the whole system)
**Every story traces to something real in `personal/career-profile.md`.** No invented
achievements, no borrowed war stories, no inflated scope. A fabricated story collapses
under one follow-up question ("what was your exact role in that?") and it's the fastest
way to lose an offer. Coach delivery, structure, and framing — never facts.

## Workflow

### 1 — Build or refresh the STAR story bank (do this once, reuse forever)
Read `personal/career-profile.md` and mine **8–12 signature stories** — the moments that
best demonstrate the competencies interviewers probe. Structure each as **STAR**
(Situation, Task, Action, Result) and **tag it by the competencies it proves** so it can
be pulled for many questions. See `references/story-bank.md` for the structure and the
competency checklist (leadership, conflict, failure/mistake, influence-without-authority,
ambiguity, delivery-under-pressure, disagreement, biggest-impact, etc.). Save to
`personal/interview-prep/story-bank.md`. This is durable — refresh it as the career grows,
don't rebuild per interview.
- Lead each story with the **Result** in the user's head (that's the "so what"), but
  deliver S-T-A-R in order.
- Flag competencies with **no strong story** — those are prep gaps to fill or answer honestly.

### 2 — Analyze the target interview

**First: look for research that already exists on this company and these people.** If you keep
a company/people research store, read it BEFORE writing anything — the profile, any interview
brief, and the record for each named interviewer. Look even when you are confident there is
nothing there; the lookup is one command and skipping it is how prep gets built twice, worse
the second time.

When research does exist, the prep pack is a **delta on it**, not a parallel document: point
at the brief, add only what is new or newer, and push anything you learn back into the store so
the durable copy stays current. Two documents covering the same ground will disagree, and the
reader cannot tell which is current.

Two things the research answers that a JD never will, and both change the whole conversation:
**who the interviewer actually is** — a prospective direct report is a completely different
interview from a recruiter screen — and **whether the company is somewhere worth landing.**

Then read the JD (or role/level) and infer what it will probe: behavioral areas,
role-specific/technical topics, leadership/scope questions, domain knowledge, and the classics
every interview asks. Note the interview *type* and stakes (recruiter screen vs.
hiring-manager vs. panel vs. exec). Method in `references/mock-drill.md`.

### 3 — Build the prep pack: ONE durable file, plus ONE SHORT FILE PER ROUND

**Two kinds of file, and the split is the point.**

`personal/applications/<company>/interview-prep.md` is the **durable pack** — comp, the story
map, logistics, the honest gaps, and the reasoning behind each call. It survives the whole
loop and is where a fact is recorded once.

`personal/applications/<company>/<YYYY-MM-DD>-<round>-<names>.md` is a **short page per
interview**, carrying only what is live for that day and **linking back to the durable pack**
rather than restating it. Name it date-first so rounds sort chronologically and say who was in
them: `2026-08-10-panel-narla-kaminsky.md`.

Keep an index table at the top of the durable pack listing every round and its file.

**Why this is a rule.** A single growing file is corrected in place as the picture changes —
an interviewer turns out to be a skip-level rather than a peer, two separate conversations turn
out to be one panel — and the corrections land at the BOTTOM while the stale version stays at
the top. It then reads plausibly from the first line and describes an interview that is not
happening. That is worse than no prep, because it is confidently wrong in exactly the places
the research already corrected. This is not hypothetical - it happens whenever a loop runs long
enough for the facts to move, and the stale version is the one at the top.

Two habits that keep it honest:
- **Mark superseded sections where they sit**, with a pointer to what replaced them. Do not
  delete the reasoning; date it and say what overtook it.
- **Never duplicate a fact across the two.** If it is in the durable pack, the round page links
  to it. Two copies disagree the moment one is updated.

Each round page should be a three-minute read: who is in the room and what they actually own,
the one structural idea for that conversation, the probe most likely to decide it, two or three
stories in priority order, questions to ask, and the hard landmines.

**The durable pack contains:**
- **Likely questions** for this role (behavioral + role-specific + classics).
- **Story map** — which story-bank entry answers each question (reuse; don't rewrite).
- **Gaps** — questions with no strong story; prep an honest answer or a candid "haven't done X, here's the closest / how I'd approach it."
- **"Tell me about yourself"** — a crafted 60–90s pitch + one-line positioning (the same honest hook `resume-tailor`/`network` use).
- **Why this role / why now / why leaving** — honest, specific to THIS company (passes the portability test: it can't be sent to a different company unchanged).
- **Weakness / failure** — a real one, with what you learned; never a humblebrag ("I work too hard").
- **Comp question** — do NOT wing this; hand off to the `negotiation` skill for the range and the deflection script.
- **Questions to ask them** — sharp, level-appropriate; signals seriousness and screens the role.

### 4 — Mock-drill loop (reps are the point)
Run a live mock: ask ONE question, let the user answer, then give **honest, specific
feedback** against the rubric in `references/mock-drill.md` — STAR completeness, specificity
and real numbers, length (rambling vs. thin), filler, and whether the "so what" landed.
Iterate on the weak ones. Escalate difficulty (follow-ups, pushback, "walk me through the
numbers") as they improve. Feedback is candid but kind — the point is a better answer, not
a grade.

### 5 — Post-interview debrief (the learning loop)
After a real interview, capture what was actually asked, what landed, what didn't, and any
follow-up owed (thank-you, materials promised). Feed new question types back into the bank
and the next prep pack. This is how prep compounds across a search instead of starting cold
each time.

### 6 — Follow-ups & thank-yous (the cadence — own it for the whole search, not just interviews)
The cheapest edge in a search: a specific thank-you within a day, a well-timed nudge, a report-back to someone who helped. Most candidates skip them or do them generically. Own the **cadence** — when to send what, and when to let go — and draft each in the user's voice (`personal/writing-style.md`). Pull owed touches from `personal/data/pipeline.md`: who just interviewed (thank-you owed), who's gone quiet past their timeline (nudge due), who referred you (report-back owed). Drafts go in `personal/applications/<company>/` or straight to the user.
- **After an interview → within 24h.** Specific: reference something real from the conversation, reinforce one reason you fit, thank them. Each interviewer if you have addresses, else via the recruiter. Never generic.
- **After an informational interview → within 24h.** Thank them, reference a specific insight, and **report back** if they referred you onward (that's what builds the relationship).
- **After applying via a warm contact → a short heads-up.** "Just applied to X — thank you for the context; anything I should know?" Keeps them able to advocate.
- **Silence past the expected decision → nudge at the right interval.** Wait for the timeline they gave (or ~1 week if none), then one brief, warm check-in reaffirming interest and asking next steps. **One nudge, maybe two spaced out — then let it rest.**
- **After a reference call → thank the reference** and tell them how it went (the network skill keeps them warm).
- **Rejection → a gracious note.** Surprisingly high-ROI; "thank you for the chance; I'd welcome staying in touch." Doors reopen.

Rules: **brief** (3–5 sentences), **specific** (one real detail beats any enthusiasm), **add a little value or warmth** (never a bare "any update?"), **well-timed** (eager reads as anxious — don't nudge early), and **know when to stop** (~2 follow-ups into silence, then it's their move). For anything longer than a note, hand to the **network** skill. Never mass-template — be the specific one.

## How it plugs into the system
- **career-profile** → the source of every story. Stories that surface a `[NEED METRIC]` gap flag it back to the profile.
- **resume-tailor** → same source of truth; the résumé bullets and the spoken stories should agree.
- **negotiation** → owns the comp question; interview-prep just routes there.
- **network / career-coach** → the pitch and the "why" are shared raw material.

## Guardrails
- **Truth over polish.** Real stories, real numbers, honest weaknesses. Never coach a candidate to mislead.
- **Reps over theory.** A drilled answer beats a perfect written one; push the mock loop.
- **Their voice, not a script.** Prep bullets and structure, not memorized paragraphs that sound canned.
- **Level-appropriate.** An exec panel and a first recruiter screen need different prep — calibrate.

---
name: network
description: The people side of the search — WHO to reach out to, the MESSAGE to send, and your REFERENCES, in one skill. Surfaces and prioritizes contacts from career-profile.md (ranked by warmth x usefulness, status tracked in reconnect-list.md); writes genuine, specific outreach for a named person and context (cold connection notes, InMails, referral and intro asks, reconnects, recruiter replies, hiring-manager direct) — never spam; and builds, preps, and manages job references (choose per role, ask early, prep them before the call, keep them warm). Triggers: "who should I reach out to", "reconnect list", "prioritize my network", "message this recruiter", "referral ask", "warm intro", "reconnect with", "who should I use as a reference", "prep my references", "they asked for references". Reads career-profile.md; feeds warm paths to apply-pipeline. Writes personal/reconnect-list.md and personal/references.md.
---

# Network (Relationships Spoke)

> **Coach voice:** adopt the tone set by `userconfig.COACH_VOICE` (see `coach-voice.md`) — supportive / tough-love / zen / humorous / analytical. It changes **delivery only**; the honest substance, the real gaps, and the no-fabrication rule never change.

Owns the whole warm channel: the **who** (a prioritized, tracked contact list), the **what** (the actual outreach message, matched to the real relationship), and the **references** (chosen, prepped, and kept warm for the offer stage). For mid-to-senior and leadership roles the warm channel usually beats the front-door application — referrals and warm intros move more offers than cold portal submissions. If the user is cold-applying and stalling, this is often the higher-leverage move; name that.

> **Where files live (READ THIS):** every user-specific file lives in the gitignored `personal/` folder. Reads `personal/career-profile.md`; writes the contact tracker to `personal/reconnect-list.md` and the reference roster to `personal/references.md`; other user files are `personal/writing-style.md`, `personal/application-answers.md`. Read from and write to `personal/` — never the tracked repo.

## The two rules (system-wide)
1. **Only what's real.** Every credential, metric, and connection traces to `personal/career-profile.md` and to the actual relationship. Warmth ratings must reflect the real tie — miscalling a cold contact "warm" produces a message that reads false and burns the contact. When unsure how warm a tie is, ask.
2. **Genuine, not spam.** These go to real people the user wants a lasting relationship with. A good message could only have been sent to that one person. If asked for a spray-and-pray template to blast 200 people, push back — it damages reputation and barely works; offer a reusable *framework* they personalize per person.

---

## Part A — WHO: build and maintain the reconnect list

### 1 — Gather candidates
Pull from every source: `personal/career-profile.md` (every company → its managers, peers, reports, vendors), the user's memory, and any existing `personal/reconnect-list.md` (update, don't rebuild). Prompt **by category** — recall works far better than "who do you know?":
- Former managers and skip-levels (strongest vouchers)
- Former peers who've moved elsewhere (referral routes in)
- People the user hired, managed, or mentored (loyal, responsive)
- Vendors, consultants, agency contacts (hear about openings early)
- People from earlier roles / school lost touch with

### 2 — Rate on two axes
- **Warmth** (strength/recency of the real relationship): warm / lukewarm / cold — this drives the message tone.
- **Usefulness** (how well-placed to help): high / medium / low — a function of where they sit now and how connected they are.

Prioritize: **warm + useful first** (fast, high-yield), **warm + less useful** next (easy reconnects that surface more names), **cold + useful** later (needs a warmer bridge or an intro — route through a mutual). Skip cold + low-usefulness. Full rubric and edge cases in `references/prioritization.md`.

### 3 — Produce the tracked list
Output to `personal/reconnect-list.md` in the schema in `references/list-schema.md`: name, where they are now, warmth, usefulness, priority tier, the angle (why reach out / what you share), status (not contacted / contacted / replied / conversation had / cold), last-touch date. Living artifact.

### 4 — Maintain
Each session: update statuses, add names surfaced by earlier conversations (every reconnect yields "who else should I talk to?" — those loop back into step 1), re-prioritize, flag anyone due a follow-up. A tracker full of "contacted" with no "replied" is a signal the *messages* need work (Part B), not that the user should contact more people.

---

## Part B — WHAT: write the outreach message

### Get the context first (batched)
- **Who** — name, role, company, seniority.
- **Relationship** — cold, second-degree (shared connection), former colleague, met once at X, alum? Determines everything.
- **The ask** — referral, intro to a third person, informational chat, "is your team hiring", reply to a recruiter, reconnect with no ask yet.
- **The target** — specific role/company, or exploratory.
- **Channel** — LinkedIn connection note (300-char hard limit!), InMail/message, or email. Length and tone differ.

### Pick the message type and follow its pattern (`references/message-patterns.md`)
Cold connection note (≤300 chars) · warm reconnect · referral ask · intro request · informational-interview request · recruiter reply · hiring-manager direct.

### Core craft (all types)
- **Lead with the recipient**, not the user — why *them*, why now.
- **Concrete and short**, one clear ask that's easy to say yes to.
- **Small, specific ask** — "20 minutes on how you think about X" beats "pick your brain."
- **Give an easy out** — low-pressure closes get more replies.
- **Match the temperature** — cold ≠ warm; don't fake closeness.
- **One real proof point, max** — the single most relevant thing from the profile, not a resume dump.

### De-AI + de-cringe pass (`references/de-ai-checklist.md`)
Cut the tells: "I hope this finds you well," "I came across your profile," "I was impressed by your work at," "pick your brain," "explore synergies." It should sound like the user on a good day, not a sales sequence.

### Output
Offer 2–3 strategic variants when high-stakes or ambiguous (labeled by approach + tradeoff, not tone swaps); one good message for simple cases. Use a message-composition tool if available; otherwise clean copy. Draft in the user's voice (`personal/writing-style.md`).

---

## Part C — REFERENCES: choose, prep, manage

The final gate most people wing. A reference surprised by the call, or speaking to the wrong things, can cost an offer at the one-yard line. Make references a managed asset. Writes `personal/references.md`.

### 1 — Choose (per role)
Mix that covers what the role probes: a **recent manager** (work + how they're led), a **peer/cross-functional partner** (collaboration), and where relevant a **skip-level, report, or client** (leadership, or delivery from the other side). Cross-check `career-profile.md` — each reference should speak firsthand to a specific win. Leadership role → scope/people; craft role → someone who saw the work.

### 2 — Ask well (and early)
Ask *before* you need them, with an out ("would you be comfortable being a **strong** reference?"). A hesitant yes is a no. Confirm best contact method.

### 3 — Prep them (the step that wins offers)
Before the call, send the **role/JD**, a one-line **why you want it**, and **2–3 specific things to emphasize** mapped to what this employer cares about (from `career-profile.md`). Remind them of the wins they witnessed. A prepped reference tells a specific, aligned story instead of generic praise.

### 4 — Manage logistics
References come **late** (final stages / after a verbal), **never on the résumé**. Give a tight curated list (usually 3), matched to the role. **Thank them after** and tell them how it went (see interview-prep's follow-up cadence). Keep them warm for next time.

The file (`personal/references.md`):
```markdown
## {name} — {title, company} · {relationship, when}
- **Contact:** {method} · **Asked/confirmed:** {date}
- **Can speak to:** {the specific wins/competencies they witnessed}
- **Best for:** {which kinds of roles}
- **Prepped:** {date + what you sent for the last call}
```

---

## How it plugs into the system
- **career-profile** (hub) → the profile this reads. Run it first if none exists.
- **apply-pipeline** → when a senior role has a warm path, it routes here for the message.
- **informational-interview** → owns the coffee-chat strategy; this drafts the actual request.
- **interview-prep** → owns the follow-up/thank-you cadence, including reference thank-yous.

## Guardrails
- **Real and firsthand.** Only genuine relationships; never invent closeness or coach a reference to embellish.
- **Prioritize honestly.** Warm+useful first; don't pad a thin list with cold low-value names.
- **Protect the relationship.** Ask early, deploy sparingly, thank always, keep warm.
- **Their voice, not a template.** Specific to the one person; no mass-blast.

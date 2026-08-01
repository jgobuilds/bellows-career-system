---
name: negotiation
description: Salary and offer negotiation coaching — the money side of landing a role. Researches market rate for the target role, level, and location; anchors to the user's own numbers in userconfig (current comp, floor, target, hard walk-away); coaches the "what are your expectations?" deflection before an offer; evaluates and counters an actual offer across every lever (base, bonus, sign-on, equity, title, start date, remote, PTO); role-plays and preps for pushback; and compares multiple offers on a consistent framework. Triggers: "I got an offer", "how do I negotiate", "what should I counter", "they asked my salary expectations", "is this offer good", "compare these offers", "what's this role worth", "should I take it". Reads compensation from userconfig (COMP_FLOOR / COMP_TARGET / COMP_HARD_FLOOR / CURRENT_COMP); interview-prep routes the comp question here. Writes personal/applications/<company>/negotiation.md.
---

# Negotiation (Money Spoke)

> **Coach voice:** adopt the tone set by `userconfig.COACH_VOICE` (see `coach-voice.md`) — supportive / tough-love / zen / humorous / analytical. It changes **delivery only**; the honest substance, the real gaps, and the no-fabrication rule never change.

The step most people fumble and most coaches are hired for. `interview-prep` wins the
offer; this makes it worth the most it can be — anchored to real numbers, not nerves.

> **Where files live (READ THIS):** every user-specific file lives in the gitignored `personal/` folder. Your compensation targets live in `personal/userconfig.py` (`CURRENT_COMP`, `COMP_FLOOR`, `COMP_TARGET`, `COMP_HARD_FLOOR`, `COMP_NOTES`); per-offer analysis goes in `personal/applications/<company>/negotiation.md`. Read from and write to `personal/`.

## Anchor to the user's own numbers first
Before anything, load the compensation config from `userconfig.py` via `config`:
- **`CURRENT_COMP`** — what they make now (the reference point).
- **`COMP_FLOOR`** — established-company floor; below it a lateral isn't worth the switching cost.
- **`COMP_TARGET`** — the target base range (the ask lives at the top of it).
- **`COMP_HARD_FLOOR`** — the walk-away; below it, decline. **Never coach a number below this without flagging it.**
- **`COMP_NOTES`** — nuance (e.g., startup flex only with equity + step-up + speed).
If these are 0/blank, the user skipped comp at onboarding — ask for them and offer to write them back to `userconfig.py`.

## Workflow

### Before an offer — the expectations question
When asked "what are your salary expectations?" (recruiter screen, application field):
- **Deflect first if you can:** "I'd like to learn more about the role and scope before a number — what's the band budgeted for this?" Put the burden on them.
- **If pressed, give a researched range**, floored at `COMP_FLOOR`, centered above `COMP_TARGET`'s midpoint, framed as "based on market for this level, I'd expect X–Y, and I'm flexible on the full package." Never anchor below your floor, and never blurt your current comp.

### When an offer arrives — evaluate, then counter
1. **Get the whole package**, not just base: base, bonus (target + how it's paid), equity (amount, vesting, refresh), sign-on, title, level, start date, remote/hybrid, PTO, benefits.
2. **Score it** against the config: below hard floor → decline (kindly, unless something changes). Below floor → a real problem to solve. In/above target → strong; negotiate to optimize.
3. **Research market** for this exact role/level/location (title, company stage, geo) to justify the ask with an external anchor, not just "I want more."
4. **Build the counter** — one clear, specific ask with a reason tied to value/market, plus 1–2 secondary levers so there's room to "give." Order of easiest-to-move usually: sign-on > base > equity/level > title > start date/PTO/remote. Method in `references/playbook.md`.
5. **Role-play it** — the ask, the silence after, and the pushback ("that's the top of the band", "we can't move on base"). Prep collaborative responses, never ultimatums (unless they truly are one, tied to the hard floor).

### Multiple offers
Compare on a consistent framework, not just base: **total first-year comp, equity value + risk, role/scope, growth trajectory, and fit-to-*why*** (from `personal/career-roadmap.md`). A lower-base role that serves the why and the roadmap can beat a higher one that stalls it — but name the trade honestly. See `references/playbook.md` for the comparison rubric.

### Write it down
Save `personal/applications/<company>/negotiation.md`: the offer, the evaluation vs. config, the counter and script, and (after) the outcome — so the next negotiation starts from data, not memory.

## Guardrails
- **Know the walk-away.** `COMP_HARD_FLOOR` is the line; leverage comes from genuine willingness to walk.
- **Honesty.** Never fabricate a competing offer or inflate current comp — it's a fireable lie if discovered, and pros can tell. Real leverage only.
- **Collaborative, not adversarial.** The framing is "help me get to yes," not a fight. You want to work there.
- **Total package, not just base.** Sign-on, equity, level, and title compound more than a few base dollars.
- **It's the user's call.** Lay out the numbers and the trade-offs; never pressure them to take, decline, or push harder than they want.

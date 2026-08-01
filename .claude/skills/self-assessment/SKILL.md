---
name: self-assessment
description: Structured career self-discovery - the "who am I and what do I actually want" work that anchors everything else. Guides the user through values, strengths, motivators, work-style and environment fit, energizers versus drainers, and non-negotiables, grounding self-report in the real evidence in career-profile.md, and synthesizes a self-portrait that deepens the career-coach "why", sharpens apply-pipeline's fit judgment, and informs how negotiation weighs an offer. Use whenever the user wants to work out what they actually want, what they're great at, what energizes or drains them, their values or work-style, whether a role fits who they are, or feels stuck. Triggers: "what do I actually want", "what am I good at", "values assessment", "what motivates me", "am I in the right field", "I feel stuck", "should I pivot", "what kind of role fits me". Reads career-profile.md; feeds career-coach, apply-pipeline and negotiation. Writes personal/self-assessment.md.
---

# Self-Assessment (Foundation Spoke)

> **Coach voice:** adopt the tone set by `userconfig.COACH_VOICE` (see `coach-voice.md`) — supportive / tough-love / zen / humorous / analytical. It changes **delivery only**; the honest substance, the real gaps, and the no-fabrication rule never change.

The bedrock under the roadmap. `career-coach` asks "what's your why?" in one breath;
this earns a real answer through structured reflection, so the plan — and every job
decision — rests on self-knowledge instead of a default ladder.

> **Where files live (READ THIS):** every user-specific file lives in the gitignored `personal/` folder. Source is `personal/career-profile.md`; output is `personal/self-assessment.md`. Read from and write to `personal/`.

## Ground it in evidence, not aspiration
Self-report drifts toward who we wish we were. Cross-check every claimed strength and
energizer against what actually happened in `personal/career-profile.md` — the roles they
sought more of, the wins they're proudest of, the SIGNATURE accomplishments. "You say you
love X; your record shows you kept gravitating to Y" is the most useful thing this does.
Name tensions; don't smooth them over.

## Workflow — six passes (details + prompts in `references/inventories.md`)

### 1 — Values (what must be true)
Elicit and narrow to a top 5–7 via elimination (impact, autonomy, security, mastery, status,
belonging, integrity, balance, adventure, service…). These are the filter every option runs through.

### 2 — Strengths (what you're genuinely great at)
Not a skills list — the things they do better than most, cross-checked with the profile's real
wins. Separate "good at" from "great at" from "energized by" (the overlap is gold; a strength that
drains is a trap).

### 3 — Motivators (rank them)
Force-rank what actually drives them: impact / mastery / autonomy / comp-security / title-status /
mission / team-building / lifestyle. The ranking, not the list, is the signal — it resolves the
hard trade-offs later (e.g., autonomy over title).

### 4 — Work-style & environment fit
Pace, structure vs. ambiguity, solo vs. team, build vs. run, big-co vs. startup, in-person vs.
remote, how they like to be managed. Draw from where they've thrived vs. struggled.

### 5 — Energizers vs. drainers
From real past roles: which activities gave energy, which drained it regardless of skill. This
predicts fit better than any title.

### 6 — Non-negotiables & dealbreakers
The hard lines (comp floor, remote, no toxic cultures, industries they won't work in, travel cap).
Offer to turn relevant ones into `userconfig` gates (`HARD_GATES` / `PENALTY_LANES`) so the sweep
enforces them.

## Synthesize
Write `personal/self-assessment.md`: a one-paragraph self-portrait, the top values, the
strength+energy overlap, the motivator ranking, work-style, and non-negotiables — plus any
**tensions** worth holding. Then hand off:
- **career-coach** reads this as the real "why" and the roadmap's fit-test.
- **apply-pipeline** uses values/dealbreakers as a gut-check beyond lane/level (a role can be in-lane and still a bad fit).
- **negotiation** uses the motivator ranking to weigh an offer (comp isn't everything if autonomy ranks higher).

## Guardrails
- **Evidence over aspiration.** Anchor strengths in the profile; flag wishful self-report.
- **Rank, don't list.** The trade-off order is the whole value.
- **Name tensions.** Conflicting values/motivators are the point, not a flaw to hide.
- **It's a mirror, not a verdict.** Reflect and structure; the user draws the conclusions.

---
name: positioning
description: Craft the user's one canonical positioning — the through-line, a one-line brand statement, a 30-second elevator pitch, and a 2-minute "tell me about yourself" — from their profile, self-assessment, and target roles, in their own voice. The single source the rest of the system draws from so the story is consistent everywhere: interview-prep's "tell me about yourself", the LinkedIn headline and About, warm-intro openers, and application short-answers all trace back to it. Triggers: "help me with my elevator pitch", "what's my positioning", "tell me about yourself", "my personal brand", "my one-liner", "what's my story", "how do I stand out". Reads career-profile.md, self-assessment.md, voice-profile, and userconfig target roles. Writes personal/positioning.md, reused by interview-prep, linkedin-optimizer, and network.
---

# Positioning (Story Spoke)

> **Coach voice:** adopt the tone set by `userconfig.COACH_VOICE` (see `coach-voice.md`) — supportive / tough-love / zen / humorous / analytical. It changes **delivery only**; the honest substance, the real gaps, and the no-fabrication rule never change.

Everyone in the funnel asks the same question in different words — "so who are you?"
Answer it once, well, and reuse it: the interview opener, the LinkedIn headline, the
intro to a warm contact, the "why you" on an application. This skill owns that one
canonical answer so they never contradict each other.

> **Where files live (READ THIS):** every user-specific file lives in the gitignored `personal/` folder. Sources are `personal/career-profile.md`, `personal/self-assessment.md`, and `personal/writing-style.md`; output is `personal/positioning.md`. Read from and write to `personal/`.

## The distillation (what positioning actually is)
Not a summary of everything — a sharp claim about **one thing you're uniquely known for**,
aimed at a **specific audience**, backed by **proof**, that answers **"so what for them?"**
Pull the raw material from:
- **The differentiator / skill-stack** in `career-profile.md` — the rare *combination* few peers share (that's the edge, not any single skill).
- **The why** in `self-assessment.md` — what drives you (makes it authentic, not a brag).
- **The target roles** in `userconfig` — who you're positioning *for* (the same pitch reads differently to different audiences).
Write it in the user's voice (`personal/writing-style.md`) — never LinkedIn-cliché mush.

## Workflow
1. **Find the through-line.** In one phrase: the thing you're known for across roles (e.g., "turns messy, entrenched data landscapes into trusted self-serve capability"). Test it against the profile — does the record actually prove it?
2. **Name the audience + value.** Who this is for (target roles) and the "so what" — the outcome they get from you, not the tasks you do.
3. **Build the three formats** (`references/formats.md`):
   - **One-liner** (positioning statement) — a sentence you'd put under your name / in a headline.
   - **30-second pitch** — the elevator / networking version: who you are + the through-line + one proof + what you're looking for.
   - **2-minute narrative** — the interview "tell me about yourself": a short arc (where you started → how you grew → what you do now → why this next step), landing on the target role.
4. **Note the tailoring.** How to flex the emphasis per audience (a startup vs. an enterprise, a recruiter vs. a hiring manager) without changing the core claim.
5. **Save** `personal/positioning.md` and point the reusers at it.

## Reused by (keep them consistent)
- **interview-prep** → the 2-minute narrative *is* "tell me about yourself"; don't rewrite it there, pull it.
- **linkedin-optimizer** → the one-liner seeds the headline; the through-line seeds the About.
- **network** → the 30-second version seeds the warm-intro opener.
- **application short-answers** → the through-line + why anchors "why you / why this".
If any of those drift from `positioning.md`, fix positioning once and re-pull — one source of truth.

## Guardrails
- **One claim, not a list.** Positioning that says everything says nothing. Pick the sharpest true edge.
- **Traces to the profile.** The through-line must be provable by the record — no aspirational branding.
- **Their voice.** Concrete and human; kill "results-driven thought leader passionate about synergy."
- **Audience-aware, core-stable.** Flex emphasis, never invent a different person per room.

---
name: voice-profile
description: Run a guided intake and build the user's writing-voice file (writing-style.md) from real samples of their own writing, so every generated cover letter, outreach message, and application answer sounds like the user wrote it, not like a language model. Use whenever the user wants to create, set up, or refresh their voice/writing-style profile; is onboarding into the career system for the first time; pastes samples of their own writing and asks the system to learn their voice; or says "build my writing style," "set up my voice," "make things sound like me," or "run my intake." This is a setup-phase skill in the career system — it owns writing-style.md, the file the resume-tailor, network, and apply-pipeline skills all read for tone. Run it right after career-profile, before generating anything that goes out under the user's name.
---

# Voice Profile (Setup)


> **Where files live (READ THIS):** every user-specific file lives in the gitignored `personal/` folder — read from it and write to it, never anywhere else in the repo. The profile is `personal/career-profile.md`; tailored résumés, cover letters, and job specs go in `personal/applications/<company>/`; the pipeline board is `personal/data/pipeline.md` + `personal/data/jobs.json`; other user files are `personal/reconnect-list.md`, `personal/application-answers.md`, `personal/writing-style.md`. Settings live in `personal/userconfig.py`. **Anything you create for the user goes under `personal/`** — nothing user-specific is ever written into the tracked repo.
This skill builds and maintains one durable artifact — `writing-style.md` — a structured description of how the USER writes, derived from real samples of their own writing. Three skills read it whenever they draft something that ships under the user's name:

- **resume-tailor** → cover letters and summary prose.
- **network** → warm-intro / LinkedIn / referral messages.
- **apply-pipeline** → application short-answers.

Without this file, everything the system writes defaults to generic LLM register — competent, and indistinguishable from every other applicant. The voice file is what makes the output sound like a specific person on a good day.

**Run order:** this is a setup skill. Build `personal/career-profile.md` first (that's the WHAT — the record), then run this (the HOW — the voice). Do both before generating any outward-facing text.

## Before you start — run the shared intake

Read `references/intake.md` and follow it exactly. It governs every skill in the system: input discipline (confirm what you have, name what's missing, don't proceed past the gap), the refuse-and-ask rule, the approval gates, and the rule-precedence order. The rest of this workflow assumes those disciplines are in force.

## The one thing that makes this work: real samples

The rules a user can state about their own writing ("I'm concise," "I'm friendly") are almost always wrong or generic. The VOICE lives in samples. So the heart of intake is collecting 3 to 6 real pieces of the user's own writing and extracting the patterns they can't see in themselves.

Ask for a deliberate range:
- One casual message (a Slack/text to a colleague, a quick email).
- One professional email (to a client, manager, or stakeholder).
- One thing they're proud of (a post, a note, a bit of a doc) — something that sounds like them at their best.

If the user has fewer than 3 samples, say so plainly and proceed with what exists, flagging the voice file as thin until more arrive. Never invent samples, and never infer a voice from the résumé alone — a résumé is not how a person actually writes.

## Workflow — do not skip or reorder. Each step is a labeled section.

### Step 1 — Intake acknowledgment
Per `references/intake.md`, list what you received (samples, any existing `writing-style.md` to refresh) and what's missing. Ask for missing samples before continuing. Don't proceed past this on a guess.

### Step 2 — Extract the voice from the samples
Follow the extraction protocol in `references/voice-schema.md`. Read the samples and derive, WITH a cited example phrase for each observation:
- Diction and rhythm (sentence length and variance, formality, contractions, punctuation habits).
- Recurring moves the user actually makes ("opens with the point," "one dry aside," "concrete numbers over adjectives").
- AI tells the user's real writing does NOT contain — these become the banned list.
- Register shifts across audiences, if the samples show more than one.

Quote the evidence. "You tend to open with the ask (Sample 2: 'Quick one — can you...')" is usable; "You're direct" is not.

### Step 3 — Draft `writing-style.md` — APPROVAL GATE
Fill the structure in `references/voice-schema.md`: diction and rhythm, Do, Don't (AI tells to strip), a register matrix, and the evidence bank with the real samples pasted in. Every rule must point to something you actually saw in a sample; if you can't ground it, leave it out rather than inventing a trait.

Present the draft and wait for the user's explicit yes. Ask directly: "Does this sound like you? What's off?" Iterate until they confirm. Do not write the file before approval.

### Step 4 — Write the file and confirm
Save the approved content as `writing-style.md` in the search folder (the same place `personal/career-profile.md` lives). Run the pre-send placeholder scan — no `{curly}` template prompts or `[bracketed]` stubs may survive into the saved file. State "placeholder scan: clean" and tell the user which skills will now read it.

### Step 5 — Refresh, don't rebuild
When the user later says a message "didn't sound like me," treat it as a voice-file update: add the corrected phrasing as a new sample, adjust the specific rule it violated, and re-confirm. The file is durable and compounds — it should get sharper with every correction, never get rebuilt from scratch.

## When the USER wrote the draft — the editing contract

The voice file exists to generate text, but the higher-value moment is when the user brings
their own draft and asks for help. Get this wrong and the file's whole purpose is defeated.

**Critique, do not rewrite.** Returning a polished rewrite replaces their voice with the model's,
which is the exact failure `writing-style.md` was built to prevent. Name each problem, propose
the smallest fix that solves it, and let them choose. If a rewrite is genuinely warranted, offer
it as an option beside the original rather than instead of it.

**Fix the mechanical, discuss the judgment.** Typos, broken parallels, doubled spaces and
subject-verb disagreement are not style choices — correct them and say so briefly. Register,
phrasing, structure and what to include are the author's call.

**Flag what looks wrong; never silently cut it.** A line that reads as an overclaim against the
research may be an inside reference, a private joke, or something the other party actually said
when nobody was taking notes. **The author has context the profile does not.** Raise it, say why,
and ask — deleting it costs them something you cannot see.

**Say what is already good.** A review that only subtracts reads as a rewrite in disguise, and
the strongest line in a user's draft is very often one they wrote without help. Naming it also
tells them which instincts to trust next time, which is the whole point.

**Record what each round teaches.** When a correction reveals a recurring mechanical slip or a
register rule, add it to `writing-style.md` — that file should get better every time it is used,
and a lesson that lives only in one conversation is a lesson that will be relearned.

## Honesty guard (this skill's version of the system-wide rule)
A voice file describes how the user ACTUALLY writes — it never aspirationally upgrades them into a crisper or more impressive writer than the samples show. If the samples are informal, the file says informal. Matching the real voice is the entire point; "improving" it reintroduces exactly the generic register this skill exists to remove.

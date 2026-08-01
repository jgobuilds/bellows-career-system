# Voice File — target structure and extraction protocol

The output of the voice-profile skill. `writing-style.md` is read by resume-tailor, network, and apply-pipeline whenever they draft anything outward-facing.

## Extraction protocol — how to derive the voice from samples

Read the 3 to 6 real samples the user pasted. For each dimension below, make an observation ONLY if a sample supports it, and cite the phrase that shows it. If no sample supports a dimension, leave it blank and note it as unobserved — do not fill it from a generic idea of "good writing."

- **Sentence length and variance** — are sentences uniformly short, uniformly long, or deliberately varied? (Uniformity is itself an AI tell; note whether the user's real writing varies.)
- **Formality** — conversational, neutral, or formal? Look at greetings, sign-offs, and word choice.
- **Contractions** — does the user use them? (Most real writing does; LLM default drifts formal.)
- **Punctuation habits** — dashes, semicolons, ellipses, exclamation frequency. Note the actual habit (e.g. "spaced hyphen, never em-dash").
- **Recurring moves** — the two or three things this person reliably does: opens with the ask, adds one dry aside, leads with a number, closes with a concrete next step.
- **AI tells ABSENT from their real writing** — words and tics the samples never contain. These become the banned list, and it's strongest when it's drawn from the contrast between the samples and generic LLM prose ("delve," "leverage," "I'm thrilled to," hollow tricolons).
- **Register shifts** — if a casual sample and a professional sample differ, capture both registers in the matrix rather than averaging them into one bland middle.

## File structure to produce

```markdown
# My Writing Style — {name}
_Used whenever the system drafts anything that goes out under your name._
_Goal: it should sound like you wrote it on a good day, not like a model wrote it about you._

## Diction & rhythm
- Sentence length: {observed pattern, with a cited sample}
- Formality default: {observed}
- Contractions: {yes/no, from samples}
- Punctuation habits: {observed habit}

## Do
- {a real recurring move, with the sample phrase that shows it}
- {another}

## Don't (AI tells to strip)
- Banned words: {drawn from the contrast between the samples and LLM default}
- {structural tells the user's writing avoids — e.g. no tricolons, no hollow openers}

## Register matrix
| Audience | Register |
|---|---|
| Close colleague | {from the casual sample} |
| Recruiter / hiring manager | {from the professional sample} |
| Executive | {tight, lead with the point} |
| Public post | {from the "proud of" sample} |

## Evidence bank
_The real samples. This section matters more than every rule above — it's what the
system actually matches against. Keep it; add to it whenever a correction teaches
the voice something new._

### Sample 1 — {context}
> {the real pasted text}

### Sample 2 — {context}
> {...}
```

## Guardrails
- **Evidence bank is mandatory.** A voice file with rules but no pasted samples is a voice file that will drift back to generic. The samples are the ground truth; the rules are just the index to them.
- **No aspirational upgrade.** Describe how the user writes, not how they "should." Matching the real voice is the point.
- **User-entered only.** Every sample is the user's own real writing. Never synthesize a sample to fill the bank.

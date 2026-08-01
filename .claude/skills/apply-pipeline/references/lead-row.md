# personal/data/leads.md Write Format
_How apply-pipeline appends a sweep to personal/data/leads.md. personal/data/leads.md is the discovery scratchpad; apply-pipeline promotes a lead into personal/data/pipeline.md._

## Update the header
Set the top `_Last sweep_` line to the run date, sources used, and geography, e.g.:
`_Last sweep: 2026-07-04 (ATS-direct target list + hiring.cafe/Built In recall, Hartford hybrid + US remote)_`

## Append a dated sweep section (newest at top)
```
## Sweep — YYYY-MM-DD (method in one phrase)
_One-line honest read of the run: what was strong, what was noise._

### Worth scoring   (Keep — high/med confidence)
- **{Company} — {Role}** · {location / remote} · {source: ATS-direct | hiring.cafe | Built In} · posted {validated date} · confidence {high|med}. {One honest line: the match and the gap.} {apply URL}

### Worth a look   (Watch — caveats)
- **{Company} — {Role}** · {…} · confidence {med|low}. Caveat: {why it's a watch, not a keep}. {URL}

### Below level / off-lane   (noted, not surfaced as real leads)
- {Company} — {Role} ({one-line reason: below Director / DS-science lane / comp step-down}).

### Unconfirmed   (could not validate on a source ATS — treat as possibly stale)
- {Company} — {Role} ({where seen}; not found on company ATS this run).

### Already tracked   (in personal/data/pipeline.md — no action)
- {Company} — {Role}.
```

## Field rules
- **source** names the most reliable source the lead was validated on (prefer ATS-direct).
- **posted date** is the real ATS date, never an aggregator's "posted X ago".
- **confidence** = source reliability × lane match. ATS-direct + strong lane = high; hidden-employer aggregator = low.
- **fit line** is honest and specific — the match AND the gap. Never "great fit!". Insurance/fintech domain raises it; below-band comp is called out.
- Anything that can't be validated goes under **Unconfirmed** or is dropped — never written as if confirmed.

## Handoff
After writing, surface the top 3–4 "Worth scoring" leads and offer to run **apply-pipeline** on them (that skill does the 1–10 score and the personal/data/pipeline.md promotion). apply-pipeline does not score.

# Tracker Row Format

The bridge between this skill (scores/drafts) and the dashboard (tracks). After scoring a job, emit a row in BOTH forms below so the user can (a) read it in chat and (b) paste structured JSON into the dashboard's "Add job" input.

## Human-readable (show in chat)
```
[SCORE/10] Role — Company  ·  tier: senior|volume  ·  warm: yes(<contact>)|no
Why: <one honest line — the match and the gap>
Route: <warm intro first via X | cold application | skip unless Y>
Integrity: ✓ <passed checks>  ⚠ <flags to watch>
Lead with: <top 2–3 bullets/themes to emphasize>
Status: to review
```

## Machine-readable (paste into dashboard)
A single JSON object matching the dashboard's schema:
```json
{
  "role": "Director, Data & AI Enablement",
  "co": "Company Name",
  "score": 8,
  "tier": "senior",
  "warm": true,
  "warmContact": "Firstname Lastname",
  "tags": ["Enablement", "Governance", "AI"],
  "why": "Title matches your throughline; reliability + AI map. Gap: global scale, carried by warm intro.",
  "checks": [["ok","Metrics trace to profile"],["warn","Don't imply global org — match your real span"]],
  "diff": "Lead with Data & AI Enablement summary; surface reliability metrics high.",
  "cover": "First line of the cover-letter angle…",
  "url": "https://…",
  "status": "to review"
}
```

## Rules
- `score` is the honest 1–10, never inflated. `checks` always includes at least the metrics-trace result.
- `warm` true only if a real contact exists in personal/career-profile.md reconnect contacts or reconnect-list — never guessed.
- `tier`: senior = director+/VP where warm-channel dominates; volume = mid-senior where cold apply is reasonable.
- `status` values: "to review" → "tailored" → "applied" → "response" → "closed". The user advances it in the dashboard.
- Keep `why` honest and specific. A row that says "great fit!" helps no one; "8, but the scale gap needs your warm intro" does.

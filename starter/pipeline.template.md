# Application Pipeline — {YOUR NAME}
_Source of truth for job applications. The dashboard is a rendered VIEW of this file — this file is the database._
_Last updated: {date}_

## How this works
- Paste a job URL into Claude → the `apply-pipeline` skill scores it 1-10 against `career-profile.md` and appends a row here.
- Status flow: `to review` → `tailored` → `applied` → `response` → `closed`.
- To change a status, say "mark {company} as applied" — the row is edited here, never duplicated.
- Tailored documents live in `applications/<company>/`.
- **Never let history live in both the dashboard and this file.** This file wins; the dashboard is regenerated from it.

## Pipeline

| ID | Role | Company | Score | Tier | Warm? | Contact | Status | Why (short) | Integrity flags | Date added |
|----|------|---------|-------|------|-------|---------|--------|-------------|-----------------|------------|
| | | | | | | | | | | |

## Row detail (tailoring notes)
_One block per job — the richer content the dashboard's drawer shows._

### Job 1 — {Company}, {Role}
- **Tags:** {level, discipline, comp, remote}
- **Job ID / source:** {req id, ATS, location, posting date}
- **Thesis:** {what the role actually is, in the company's own language}
- **Why {score} (honest):** {what genuinely matches, and what genuinely doesn't. A well-argued 6 that says
  "skip unless you have an in" is worth more than a flattering 8.}
- **Lead with:** {which accomplishments to foreground}
- **Honest gaps to prep:** {what you'd be asked about that you can't fully answer}
- **Integrity check:** {✓ metrics trace · ⚠ don't claim X}
- **Route:** {warm intro first? cold apply? park?}
- **Documents:** {applications/<company>/}
- **URL:** {posting url}

## Summary counts
- Added: 0 · Worth a look (≥7): 0 · Warm path: 0 · Tailored: 0 · Applied: 0

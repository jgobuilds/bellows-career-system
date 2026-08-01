# personal/career-profile.md Schema

This is the shared contract. resume-tailor and network both parse this file, so keep the structure stable. Save it as `personal/career-profile.md`.

```markdown
# Career Profile — [Full Name]
_Last updated: [Month YYYY]_

## Snapshot
- Current/most recent title & level:
- Domain & specialty: (e.g., data leadership — analytics + platform)
- Total years / years in leadership:
- Scope headline: (largest team led, largest budget owned, biggest outcome)
- Location & work authorization:
- Links: LinkedIn / portfolio / GitHub

## Positioning themes
_The 3-5 recurring throughlines of this career. Spokes use these to lead._
- [e.g., Built data functions from 0→1 at two startups]
- [e.g., Turned analytics into board-level decision input]

## Skill-stack (the executive differentiator)
_The UNIQUE COMBINATION that sets this person apart — not a longer skills list, but the fusion of technical + strategic + interpersonal that few others pair. One or two sentences. This is a positioning asset all three spokes draw on (resume summary, LinkedIn headline, outreach framing)._
- [e.g., "Rare pairing of hands-on data-platform depth (Snowflake/dbt) with board-level communication and a track record of standing up data functions from scratch."]

## AI fluency
_How this person has used or led AI/automation, with real context. Increasingly a baseline leadership competency for data roles in 2026 — capture the genuine instances, not aspirational claims. If there are none yet, note that honestly; don't manufacture them._
- [e.g., "Led evaluation and rollout of an LLM-based internal analytics assistant; NEED METRIC on adoption."]
- [If none: "No direct AI leadership yet — nearest adjacent: [x]." Flag as a genuine gap to discuss, not paper over.]

---

## Roles

### [Company] — [Title]
- Dates: Month YYYY – Month YYYY  |  Location  |  Reporting to: [role]
- Scope: team size [N], budget [$X], remit [what you owned]
- Context: [one line — what the company/team was, why it mattered]

Accomplishments:
- [Verbatim/cleaned bullet] | Result: [number or NEED METRIC] | Themes: [tags]
- ...

Skills/tools in this role: [list]

_(repeat per role, most recent first)_

---

## Cross-role skills index
- Technical: [SQL, Python, Snowflake, dbt, Airflow, ...]
- Platforms/methods: [ETL/ELT, ML, experimentation, governance, ...]
- Leadership: [hiring, mentoring, org design, exec comms, ...]
_(Include acronym + full form where relevant: Machine Learning (ML), etc.)_

## Education & certifications
- [Degree, institution, year] / [Cert, year]

## Metric gaps (open)
_Every NEED METRIC flag still unanswered. Ask the user to fill these._
- [Role] — [bullet]: needs [what number]

## Inconsistencies to resolve
_Conflicts found across source resumes; user must confirm._
- [e.g., "Acme title: 'Analytics Lead' in v1 vs 'Head of Analytics' in v2 — which is correct?"]
```

## Parsing rules for the spokes
- Roles are `### ` headings under `## Roles`.
- Each accomplishment line carries `Result:` and `Themes:` — spokes select on Themes, verify on Result.
- `Positioning themes` and `Cross-role skills index` are the fast-match surfaces.
- Anything tagged `NEED METRIC` must NOT be shipped with an invented number — either the user fills it or the bullet is used without the fake figure.

## Update discipline
When updating an existing profile: load it, merge new roles/bullets, refresh `Last updated`, re-run gap and inconsistency checks. Never silently drop existing content on update.

## Schema additions (v2 — learned from real use)
A real profile grew three sections beyond the original schema. Spokes should expect and use them:

```markdown
## Validated reputation themes (for COVER LETTER + INTERVIEW use — NOT resume bullets)
_What recommenders/references independently say. Opinion signal, not accomplishments.
Rules: (1) themes multiple people name independently are safe to assert in the user's
OWN voice in cover letters; (2) never quote praise as resume bullets — self-selected
praise weakens a resume; (3) separate OPINION (what they call the person) from
CORROBORATED FACT (specific claims a recommender independently confirms — those
facts may inform resume bullets, in the user's words).

## Reference roster
- [Name] — [current role]; [relationship]. Strongest on: [theme].
_(Which reference to point at for which strength, for the references stage.)_

## Reconnect contacts (seed for network)
- [Name] — [company, role]. [How known]. Warmth: [honest rating]. [PRIMARY/SECONDARY + why.]
```

Maintenance rule: when a session adds a section to the real personal/career-profile.md, update THIS schema in the same session. Schema drift breaks the spokes' contract silently.

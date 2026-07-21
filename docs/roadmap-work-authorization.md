# Roadmap: work authorization, sponsorship, and government jobs

_Status: Phases 1 and 2 shipped 2026-07-21. Phases 3-4 not started._

This exists because of a feature request worth quoting:

> Would it be possible to include state and federal government jobs, including
> non-technical opportunities, with filters showing which roles are open to U.S.
> citizens, Green Card holders, or other work-authorized applicants?
>
> As an immigrant, I don't always know where to find these opportunities or which
> ones I'm eligible for.

## The finding that reframes the request

The assumption is that the hard part is *finding* government jobs. It isn't. Federal
postings are one free API away.

The hard part is that the honest answer is mostly "no," and a filter that gets it
wrong is actively harmful.

Under [Executive Order 11935](https://help.usajobs.gov/working-in-government/non-citizens),
only U.S. citizens and nationals may be appointed to **competitive service**
positions. Permanent residents are eligible only for **excepted service** or SES
roles, and only where the annual appropriations act, immigration law, and the
agency's own policy all permit it. Congress routinely restricts even those.

The trap: USAJOBS labels many postings **"Open to the public,"** which sounds
inclusive but still carries a citizens-only requirement. A filter reading that label
naively would tell someone they are eligible for roles they legally cannot hold.

**A wrong "eligible" is worse than no filter at all.** It costs the user hours of
application effort and, worse, hope. That principle drives every design decision
below.

## The reframe: this is one feature, not two

Government eligibility and private-sector visa sponsorship answer the same question:
*can this person actually hold this job?* They are two data sources feeding one
vocabulary. And "must be a U.S. citizen" is not government-only, since defense
contractors and cleared roles carry it too.

So: one module, one set of states, applied everywhere.

## The vocabulary

Four states, deliberately conservative:

| State | Meaning |
|---|---|
| `sponsors` | Explicit. "visa sponsorship available", "open to sponsorship" |
| `no_sponsorship` | Explicit. "unable to sponsor", "without sponsorship now or in the future" |
| `citizens_only` | "U.S. citizenship required"; active-clearance terms as a strong proxy |
| `unstated` | **The default, and the majority of postings** |

`unstated` is never rendered as "you're eligible." The tool reports what a posting
says and links to the source. It does not tell anyone whether they are eligible,
because that is a legal question about a specific person's status.

## Why negation is the whole engineering problem

The bare word "sponsorship" carries no information. It appears in both:

- "We are happy to offer **visa sponsorship**."
- "We are unable to offer **visa sponsorship**."

So negative patterns must be tested **before** positive ones, because
*"we do not offer visa sponsorship"* contains *"visa sponsorship"* as a substring.
Matching must be word-boundary anchored and ordered most-specific-first.

This repo has been burned by naive substring matching before (a bare
`"her " -> "their "` replacement corrupted "other" into "ottheir" across two
repos). The adversarial cases are unit-tested for exactly that reason.

## Phases

### Phase 1 - sponsorship signal everywhere (SHIPPED 2026-07-21)

`engine/work_auth.py`. Applies to every board already swept, so it needed no new
data source, API key, or terms review. Sequenced first for that reason.

- `classify(text)` returns a verdict plus the **evidence snippet** that produced it
- `WORK_AUTH` captured at onboarding, shipping as `None` so it is strictly opt-in
- Verdict computed in `ats_sweep` where the JD body exists, then carried as a
  compact field rather than dragging full description text downstream

### Phase 2 - non-technical lanes (SHIPPED 2026-07-21)

Confirmed architecturally supported: `lead_score` reads every scoring term from
config, so nothing is hardcoded to technical roles. No engine change was needed.

But the claim was untrue in practice. The shipped template's sample values describe
a data-leadership search, and two of its lists **drop roles silently**. Scored
against the shipped defaults, every non-technical title tested was discarded, three
of them by `NOISE`/`OFF_CONTEXT` rather than by simply failing to match a lane:

    DROP (NOISE)        Senior Recruiter
    DROP (NOISE)        Nurse Manager
    DROP (NOISE)        Director of Payroll Operations
    DROP (OFF_CONTEXT)  Proposal Manager (RFP)

A recruiter searching for recruiting roles lost them to the word "recruiter". So
Phase 2 shipped `starter/userconfig.example.py`, a complete non-technical worked
config (product marketing, matching the existing `career-profile.example.md`
persona), plus warnings on the two dangerous lists and a README note.

`tests/test_starter_configs.py` pins two invariants: the example must define every
setting the template does (so it cannot silently drift), and no config's own
`NOISE`/`OFF_CONTEXT` may match its own target titles or core lane terms.

### Phase 3 - federal ingestion via USAJOBS

Free API key, two headers, and the data is a U.S. Government work so it is public
domain. Emits into the Phase 1 vocabulary.

Key on **`HiringPath`, not `WhoMayApply`**. This is evidence-based: USAJOBS
[confirmed `WhoMayApply` is buggy and unpopulated on some postings](https://github.com/fecgov/fec-cms/issues/1839)
and stated it will be replaced by `HiringPath`. Building on the deprecated field
would mean a rewrite.

### Phase 4 - state jobs (gated on terms review)

Fragmented across 50 states. Best aggregate source is
[CareerOneStop List Jobs V2](https://www.careeronestop.org/Developers/WebAPI/Jobs/list-jobs-v2.aspx)
(U.S. DOL) over the National Labor Exchange, which includes state job bank
postings. [NEOGOV](https://www.neogov.com/products/gjobs) holds roughly 40% of
state and local postings but its API serves hiring agencies, not job seekers.

Requires an API token request and a redistribution-terms review before any code.
Coverage will be partial, and the docs must say so rather than implying completeness.

## Non-negotiables

**Flag and demote, never silently drop.** A false negative would kill a good lead
invisibly. Postings are demoted with a visible reason and a quoted snippet, so the
call can be checked by a human.

**Immigration status is sensitive personal data.** It lives only in gitignored
`personal/`, never in a tracked file, never in the demo persona or screenshots.

**Never auto-insert status into a resume or cover letter.** Standard guidance is not
to volunteer it unprompted, because it invites filtering before a human reads the
record. Surface the stored answers when an application form *asks*. Leave the
documents alone. See rule 1 in `resume-style-rules`.

## Sources

- [USAJOBS: employment of non-citizens](https://help.usajobs.gov/working-in-government/non-citizens)
- [OPM: do I have to be a U.S. citizen to apply?](https://www.opm.gov/faq/employment/Do-I-have-to-be-a-US-citizen-to-apply.ashx)
- [USAJOBS Search API](https://developer.usajobs.gov/API-Reference/GET-api-Search)
- [USAJOBS HiringPath code list](https://developer.usajobs.gov/api-reference/get-codelist-hiringpaths)
- [CareerOneStop List Jobs V2 (U.S. DOL)](https://www.careeronestop.org/Developers/WebAPI/Jobs/list-jobs-v2.aspx)

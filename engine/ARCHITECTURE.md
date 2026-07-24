# engine/ — the map

Twenty-two modules in one flat directory looks like a lot. It isn't tangled: the
imports form a clean one-directional DAG (no cycles), and the files group into five
families along a single pipeline. This is the map; read it before assuming complexity.

```
        sweep  ─────►  score  ─────►  triage  ─────►  store  ─────►  serve
     (discovery)    (rank/gate)     (dedupe)      (jobs.json +      (dashboard)
                                                   pipeline.md)
```

## The five families

**discovery** — find postings and rank them
- `ats_sweep` — polls company ATS feeds directly (Greenhouse/Lever/Ashby/SmartRecruiters/Workday), throttled per domain, parallel by ATS
- `jobspy_sweep` — the sweep entrypoint: runs `ats_sweep` and adds optional `python-jobspy` board recall. **Not a duplicate of ats_sweep — it wraps it.**
- `lead_score` — the transparent 0–10 triage scorer (lane / level / geo / domain)
- `cadence` — infers each company's posting rhythm and the next sweep date from one board
- `triage_leads` — keeps new in-lane leads, drops dupes, writes a triage worksheet
- `ats_url` — resolves a company to its live ATS careers URL
- `jobkey` — the one canonical job-identity/dedupe key

**documents** — build the tailored deliverables
- `resume_builder` / `cover_builder` — spec (JSON) → .docx, ATS-safe layout rules
- `build_application` — orchestrates: build both, scrub metadata, render PDF via Word
- `docx_common` / `docx_finalize` — shared docx helpers + metadata scrub
- `resume_score` — standalone 0–100 résumé health check
- `ats_match` — résumé-vs-JD keyword coverage

**datastore** — the one place that owns the record (Repository pattern)
- `pipeline_store` — reads/writes the `jobs.json` + `pipeline.md` pair in lockstep
- `add_job` / `add_jobs_batch` — write leads into the store

**scoring helpers** — pure profile logic, no I/O
- `work_auth` — classify a posting's sponsorship/citizenship terms vs the user's status
- `career_ladder` — map titles to a rung, generate level terms from a target

**serving** — the local app
- `server` — the Hub app server (`bellows.bat`/`bellows.sh` run this); serves `hub.html`, saves status changes, runs the sweep button, reports sweep freshness (`/api/sweep-cadence`) and owns the schedule endpoints
- `sweep_schedule` — registers/queries/removes the recurring sweep in Windows Task Scheduler via `schtasks`, and detects other tasks already running a sweep so two don't stack
- `hub.html` — the single-page dashboard (not a module)

**infra**
- `_paths` — puts the repo root on `sys.path` so `import config` resolves when a
  script is run directly. `config` (repo root) reads gitignored `personal/userconfig.py`.

## Which of these do you actually run?

Most files have a `__main__`, but only a handful are user-facing commands:

| Run this | Does |
|---|---|
| `bellows.bat` / `bellows.sh` | starts `server` — the Hub, the normal entry |
| `python engine/jobspy_sweep.py` | a sweep (calls `ats_sweep` + board recall) |
| `python engine/build_application.py <dir>` | build a tailored résumé + cover |
| `python engine/cadence.py` | posting-rhythm report + next-sweep recommendation |
| `python engine/sweep_schedule.py [install N HH:MM \| remove]` | inspect or change the scheduled sweep (the Hub drives this for you) |

The rest (`docx_finalize`, `add_jobs_batch`, `triage_leads`, `pipeline_store`, …) are
internal steps the above call, or helpers imported by other modules.

## Dev tooling lives in `tools/`, not here

`tools/build_demo.py` (regenerates the demo screenshot HTML) and `tools/test_links.py`
(dashboard-link smoke test) are developer utilities, not the product. `tools/ci_local.py`
runs the CI gate in CI's own environment. They are one directory up on purpose.

## Design constraints worth knowing before you refactor

- **Flat run-as-script is deliberate.** Every module runs directly (`python engine/x.py`)
  via `import _paths`; there is no build step, and the repo *is* the product. Grouping
  files into subpackages would break `import config` everywhere, every invocation string,
  the CI scaffold, and the test `sys.path` inserts — large blast radius for organization
  a README already provides. The coupling is low; directories would decouple nothing.
- **`config` reads `personal/` (gitignored).** Tests and CI scaffold the blank
  `starter/userconfig.template.py` as `personal/userconfig.py`. A test that depends on a
  *filled-in* config passes locally and fails in CI — run `python tools/ci_local.py`
  before pushing (it reproduces CI's environment), or rely on the installed pre-push hook.

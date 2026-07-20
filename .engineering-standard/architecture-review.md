# Bellows — Architecture & Maturity Review

_A tech-lead audit of the engine + server + view, judged against Pragmatic Programmer
principles (DRY, orthogonality, functional-core/imperative-shell, crash-early) and design-pattern
maturity. Living document — the roadmap at the bottom tracks what's been addressed._

_First written 2026-07-19._

## Architecture snapshot

A layered pipeline:

```
config.py (single source of truth)
   → engine/ tools:  discover → score → build → persist
       jobspy_sweep / ats_sweep  →  leads_raw.csv
       lead_score                →  leads_scored.csv
       triage_leads              →  triage_worksheet.json   (dedupe + scaffold)
       (human judgment)          →  scores + why
       add_jobs_batch / add_job  →  jobs.json + pipeline.md  (the datastore)
       resume/cover/build_application + docx_finalize → tailored docs
   → server.py (thin HTTP + /api)
   → engine/hub.html (single-page view)
skills/  = the AI layer (markdown skill packages)
```

`jobs.json` is the machine datastore the (PII-free) dashboard reads; `pipeline.md` is the
human-readable record. Both are gitignored under `personal/`.

## What's already strong

- **Config as single source of truth** — `terms_to_regex()` compiles plain-word settings into
  scoring rules (a clean Factory). Retargeting to another person/field needs no code changes.
- **ATS provider registry** — `ats_sweep.FETCHERS` is a Strategy/registry: a new board is one
  function + one dict entry (open/closed).
- **Module docstrings** — every file has a "what it is / what it is NOT" header.
- **Honest domain modeling** — triage score vs. authoritative score; never auto-submit;
  server-authoritative doc links.
- **Network hygiene** — timeouts, User-Agent, per-call pauses, incremental `sweep_state.json`.
- **Idempotent pipeline tools** — `triage_leads` + `add_jobs_batch` validate up front and never
  half-write.

## Findings

| # | Sev | Finding | Where | Recommendation |
|---|-----|---------|-------|----------------|
| F1 | 🔴 High | **Four divergent "same job?" implementations** with different rules; they disagree ("owner" vs "Owner.com"). | `jobspy_sweep:207`, `ats_sweep:95`, `lead_score:139`, `add_job` | One canonical `engine/jobkey.py` (`norm_co`/`norm_title`/`is_duplicate`/`job_key`); all four call it. |
| F2 | 🟠 Med | **Duplicated doc-builder utilities** (`_iter_strings`, `_PLACEHOLDER`, brand constants, para/run primitives byte-identical). | `resume_builder`, `cover_builder` | Extract `engine/docx_common.py`. |
| F3 | 🟠 Med | **`engine/` isn't a package**; the sys.path bootstrap block is copy-pasted into ~8 files. | all engine scripts | `engine/_paths.py` shim + `__init__.py`; one-line `import _paths`. Keep run-as-script. |
| F4 | 🟠 Med | **Three writers of the datastore**, each with its own read/write logic, no repository. | `add_job`, `add_jobs_batch`, `server` | `engine/pipeline_store.py` (Repository) owns every jobs.json/pipeline.md read/write + the recount invariant. |
| F5 | 🟠 Med | **No unit tests; no dependency manifest.** Purest logic (scoring, dedupe, validate) untested; deps implicit. | repo | `requirements.txt` + a `pytest`/stdlib suite for the deterministic core. |
| F6 | 🟠 Med | **Config-drivenness inconsistent** — `ats_match` hardcodes `SKILL_LEXICON`/`STOP`; `score()` couples compute with printing. | `ats_match` | Move lexicon to config; split functional core from CLI shell. |
| F7 | 🟡 Low | PowerShell PDF fallback interpolates paths into a single-quoted command; breaks on `O'Brien`. | `build_application:70` | Escape / pass via args. |
| F8 | 🟡 Low | 28 broad `except Exception`, several silent. | engine-wide | Narrow, or log-and-count instead of `pass`. |
| F9 | 🟡 Low | `bold_part is spec["education"][0][0]` identity check to find row 0. | `resume_builder:253` | Use `enumerate`. |
| F10 | 🟡 Low | Stray `"man,"` token in the stopword set. | `ats_match:60` | Fix typo. |
| F11 | ⚖️ Values | **`docx_finalize` fabricates provenance** (created −3d, revision=3, App=Word) to defeat "auto-generated" detection — in tension with the "never fabricate" brand. | `docx_finalize:38-41` | Neutralize the python-docx fingerprint (blank creator/description) without inventing a fake human edit history — or make it a documented, deliberate choice. |

## Roadmap

- [x] **1. Unify job identity/dedup** (F1) — `engine/jobkey.py`; sweep/scorer/triage/writer all call it. 10 tests. _Done._
- [x] **2. Pipeline repository** (F4) — `engine/pipeline_store.py` owns jobs.json + pipeline.md; `server.load_jobs is store.load_jobs`. 6 tests. _Done._
- [x] **3. `docx_common` + package-ify `engine/`** (F2, F3) — shared builder utils; `engine/_paths.py` + `__init__.py` replace 9 bootstraps. 4 tests. _Done._
- [x] **4. `requirements.txt` + test suite** (F5) — pinned deps; `tests/` (20 stdlib-unittest tests, `python -m unittest discover -s tests`). _Done._
- [x] **5. `docx_finalize` integrity** (F11) — normalizes metadata honestly: corrects authorship + drops the generator advert, but no backdating, no revision inflation, no false "made in Word". `resume-style-rules.md` + the resume-tailor skill updated to match. _Done._
- [x] **6. Sweep-up** — F7 (PowerShell single-quote escaping), F9 (`enumerate`), F10 (stopword typo), F6 (`ats_match` split into pure `evaluate()` + `report()`; lexicon config-overridable via `ATS_SKILL_LEXICON`, 3 tests), **SUBMITTED unified** into `pipeline_store` (server's was narrower — undercounted Applied), **`_dash_set_field` removed** (dead code). F8: the sweep's network failures were already counted + printed per-company (more mature than the audit implied); narrowed the pure state/date-parse excepts so a real bug surfaces instead of being swallowed. _Done._

**All findings F1–F11 + both bonus items are addressed.** The broad `except` clauses that
remain are deliberate network resilience in the sweeps (already visible via the error count).
Every refactor was behavior-preserving, landed behind **26 unit tests** + the batch/triage/link
integration checks.

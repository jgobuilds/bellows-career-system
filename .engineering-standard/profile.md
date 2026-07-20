# Engineering profile — Bellows

_The per-repo memory for the `engineering-standard` skill. Committed, so it grows with
every review and travels with the team. Human sections are preserved across re-runs;
`audit.py --emit-profile` refreshes only the auto blocks (currently blocked on a Windows
bug in that script — see findings memory)._

## Stack & shape
- **Language:** Python (27 files, ~3,400 LOC) + one single-page HTML/JS view (`engine/hub.html`).
- **Entry points:** `engine/server.py` (local HTTP app), the CLI tools (`jobspy_sweep`, `ats_sweep`, `lead_score`, `triage_leads`, `add_jobs_batch`, `build_application`), `setup.py`.
- **Architecture:** layered — `config.py` (single source) → engine tools (discover → score → build → persist) → `pipeline_store` (Repository over jobs.json + pipeline.md) → `server.py` → `hub.html`. Patterns: Repository, Strategy/registry (`ats_sweep.FETCHERS`), Factory (`terms_to_regex`), one identity module (`jobkey`).
- **Datastore:** `personal/data/jobs.json` (machine) + `personal/data/pipeline.md` (human). `personal/` is gitignored (all PII).
- **Tests:** `tests/` — 26 stdlib-`unittest` tests over the pure core. Run: `python -m unittest discover -s tests`.
- **Deps:** `requirements.txt` (python-docx, python-jobspy; pywin32 optional). Linters: ruff/mypy/bandit (installed 2026-07-19).

## Conventions worth knowing
- Run engine scripts directly (`python engine/foo.py`); `import _paths` puts the repo root on `sys.path` (see review H2 — this blinds mypy).
- No em-dashes in generated user-facing prose (spaced hyphens); commit co-author `Claude Opus 4.8`.
- The honesty rule is load-bearing (no fabricated metrics; `docx_finalize` corrects metadata but never fakes provenance).

## Maturity scorecard (finalized 2026-07-19)
| Capability | Current | Target |
|---|---|---|
| Architecture & Modularity | 4/5 | 4/5 |
| Testing | 3/5 | 4/5 |
| Error Handling & Resilience | 3/5 | 4/5 |
| Observability | 2/5 | 3/5 |
| Security | 3/5 | 3/5 |
| CI/CD & Automation | 3/5 | 4/5 |
| Dependency & Supply-Chain | 2/5 | 3/5 |
| Documentation & Onboarding | 4/5 | 4/5 |

**Overall: 3/5** — well-architected and documented; the gap is automation (nothing runs on push).

## Findings memory (headlines)
- **2026-07-19 (ratchet complete):** the full quality gate is on and green — lint (`E/W/F/B/C4/UP/RUF`), isort (`I`), bandit (`S`), `ruff format`, and `mypy`. mypy is gated per module: typed core (jobkey, docx_common, pipeline_store) enforces `disallow_untyped_defs`; the rest is exempted in `[[tool.mypy.overrides]]` (the typing backlog). By-design ignores documented in `pyproject.toml` (E402 `_paths`; S603/S310 local-tool subprocess/urlopen). CI runs check+format+mypy+tests; verified in clean-checkout sim. **Only remaining action is the user's: mark the `quality` check required in GitHub branch protection.**
- **2026-07-19 (H2 resolved):** mypy is green + **gating in CI** — not by repackaging, but by teaching it the flat run-as-script layout (`mypy_path=["engine",".","personal"]`, drop the vestigial `engine/__init__.py`, `[[overrides]]` ignore the user's `userconfig`). Fixed the 12 real type issues it then found, incl. a genuine `proc.stdout` None-guard (server.py) and `SWEEP_STATE` typing. CI-simulated green with the template config. Still queued: isort, strict mypy (needs hints), bandit, ruff format.
- **2026-07-19 (post-review fixes):** M1 fixed (`set_notes` now uses `safe`). Mode B gates installed — `pyproject.toml` ruff config (green), `.pre-commit-config.yaml`, CI `quality.yml` (ruff + tests, CI-simulated green). Nits cleaned: E731 lambdas→def, E741 `l`→`line` (×12→0), C408, B904. CI/CD 1→3.
- **2026-07-19 (review):** No CI (H1) is the top gap. `_paths` sys.path shim blinds mypy — 33 import-not-found (H2); fix by packaging `engine/`. Latent bug: `set_notes` computes `safe` but writes raw `notes` to pipeline.md (M1). Testing not automated + no integration tests (M2). print-only observability (M3). Nits: `l`→`line` (E741×12), lambda-assign (E731×4). Full report: `.engineering-standard/review-2026-07-19.md`.
- **Known tooling bug:** the skill's `audit.py --emit-profile` crashes on Windows (`re.PatternError: bad escape \s` — backslash paths fed into a regex replacement unescaped), so this profile is hand-maintained for now.

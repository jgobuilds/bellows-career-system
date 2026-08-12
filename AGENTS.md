# Bellows Career System

An AI career coach and job-search copilot: honest role scoring, ATS-safe résumé
tailoring, interview prep, salary negotiation — all from one profile. Python
(stdlib HTTP server + CLI tools) plus one single-page HTML view.

**Public repo, AGPL-3.0-or-later.** Copyright © 2026 Brightside Data LLC.
Bellows, by JGOBuilds.

## Non-negotiables

These are the rules an agent gets wrong most expensively. The full list lives in
[`CONTRIBUTING.md`](CONTRIBUTING.md) under **House rules** — read it before your
first change; it is the authority and this section is a pointer, not a copy.

1. **Never auto-submit an application.** The system stops at the submit button,
   by design. Adding an auto-applier is explicitly out of scope, not a backlog
   item.
2. **No fabrication.** Every résumé claim traces to `career-profile.md`. Document
   metadata is corrected, never faked.
3. **`personal/` is gitignored and holds all PII.** Never commit anything under
   it, and never copy its contents into tracked files, tests, or fixtures.
4. **Keep career details out of commit messages.** The gitignore protects the
   *files*, not prose about them. A commit message is permanent and public.
   Describe the defect class and the fix — never the user's history.

## Before you push

```bash
python tools/ci_local.py
```

This reproduces CI exactly: ruff, format, tests, and mypy against a scaffolded
**template** config in a temp copy of the tracked tree. It exists because a test
that depends on a filled-in `personal/` passes locally and fails in CI. Install
it as a pre-push hook per `CONTRIBUTING.md` and it runs itself.

Everyday commands, dev setup, and the commit-msg gate are all in
[`CONTRIBUTING.md`](CONTRIBUTING.md).

## Layout

| Path | What |
|---|---|
| `engine/` | The Python system — scoring, tailoring, sweeps |
| `.claude/skills/` | **Source** for the 13 agent skills (resume-tailor, apply-pipeline, career-profile, …). Edit here. |
| `skills/` | **Generated** `.skill` packages — the install path in the README, and why they exist is in [`skills/README.md`](skills/README.md). `python tools/build_skills.py` rebuilds them; `--check` gates drift in CI. Never hand-edit an archive. |
| `starter/` | Templates `setup.py` scaffolds into `personal/` |
| `personal/` | **Gitignored.** The user's real profile and documents. Gitignored means unpublished, not backed up — `python engine/backup_personal.py` writes a dated, verified archive to `BACKUP_DIR`. |
| `tools/` | `ci_local.py`, `check_commit_msg.py`, link smoke tests |
| `tests/` | stdlib `unittest` |

## Working here

- **The profile is the product; the sweep is optional.** `career-profile.md` is what makes
  every downstream artifact honest, and it is the reason to use this at all. Lead discovery
  is a convenience layer over a finite list of company boards — it cannot see companies the
  user has not added, ATSes with no public feed, or roles filled before posting. Most strong
  leads still arrive by hand. Never imply the sweep is the point, and never let a proposal
  make it a prerequisite for anything.
- **Quality over volume** is the product thesis, not a preference. A generic
  application to a role the user scores 5 for is worse than none — it costs them
  the company. Proposals that trade honesty or selectivity for throughput are
  off-strategy regardless of how well they work.
- Read [`docs/competitive-landscape.md`](docs/competitive-landscape.md) before
  proposing a feature; the market comparison and enhancement backlog live there.
- Optional house engineering lenses live in `../ai-standards`, but this repo
  deliberately carries **no `overlay:`** — it is public, and a contributor cannot
  be assumed to have a private sibling on disk. Everything needed to contribute
  is in this repo.

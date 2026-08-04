# Contributing / Dev setup

Bellows is a small Python system (an HTTP server + CLI tools) plus one
single-page HTML view. This is the developer loop; end-user setup is in the
[README](README.md#first-time-setup).

## Get set up

```bash
git clone https://github.com/YOUR-USERNAME/bellows-career-system.git
cd bellows-career-system
python setup.py                                   # scaffolds gitignored personal/ from the templates
pip install -r requirements.txt -r requirements-dev.txt
pre-commit install                                # lint + hygiene gate before each commit
```

### The gates are installed for you

`setup.py` installs the **pre-push** and **commit-msg** hooks, because `.git/hooks/` is
never tracked by git — a fresh clone has no gates at all, and an instruction people have
to copy by hand is one they skip. It never overwrites a hook you already have; it reports
what it left alone.

- **pre-push** runs `tools/ci_local.py`, which reproduces CI's *environment* rather than
  yours. Deliberately a plain script, not `pre-commit install --hook-type pre-push` —
  that wrapper ran commit-stage hooks at push time and hung on Windows (see
  `.pre-commit-config.yaml`).
- **commit-msg** runs `tools/check_commit_msg.py`, keeping career details (employer
  names, figures, quoted document text) out of permanent public commit messages — see
  House rules below.

To install them without a full setup run, or to check what you already have:

```bash
python -c "import setup; print(setup.install_hooks())"   # -> (installed, left_alone, note)
ls -l .git/hooks/pre-push .git/hooks/commit-msg          # both must be executable
```

**A green local run is not a green build.** `ci_local.py` reproduces CI's config *and*
its OS — including a mypy pass with `--platform linux`, because typeshed gates
Windows-only modules behind `sys.platform` and a Windows type check will happily accept
a module CI rejects. That gap shipped two red builds. When in doubt after a push,
`gh run list --limit 3` is the actual answer.

`tools/ci_local.py` runs the full gate (ruff, format, tests, mypy) against a
scaffolded **template** config in a temp copy of the tracked tree — i.e. what CI
sees, not your filled-in `personal/`. A test that depends on your config passes
locally and fails in CI; this catches that before the push.

## The everyday commands

```bash
python -m unittest discover -s tests   # run the tests (stdlib unittest; pytest also works)
ruff check .                           # lint against pyproject.toml [tool.ruff]
ruff check . --fix                     # auto-fix what's safe
python tools/test_links.py            # integration smoke: every dashboard link resolves
```

`bellows.bat` / `./bellows.sh` launches the Career Hub for manual testing.

## Code standards (automated, so they don't rot)

Quality gates run automatically — you don't have to remember them:

- **pre-commit** (`.pre-commit-config.yaml`) runs `ruff` (lint + `ruff-format`) + hygiene hooks on every commit.
- **CI** (`.github/workflows/quality.yml`) runs `ruff check` + `ruff format --check` + **`mypy engine`**
  + the unit tests on every push/PR. Make these **required** in branch protection so red can't merge.

The full ratchet is now **on**: lint (`E/W/F/B/C4/UP/RUF`), import order (`I`/isort), security
(`S`/bandit), formatting (`ruff format`), and `mypy`. Two calibrations remain deliberate (in
`pyproject.toml`, with a comment each): style the formatter settles + by-design patterns are
`ignore`d (e.g. `E402` for the `import _paths` bootstrap; `S603`/`S310` for local-tool
subprocess/urlopen), and **strict mypy is gated per module** — the typed core (`jobkey`,
`docx_common`, `pipeline_store`) enforces `disallow_untyped_defs`; every other module is exempted
in `[[tool.mypy.overrides]]` and gets typed one at a time (remove it from the list as you annotate
it, and fix what mypy then flags). When you touch a file, keep it green.

## House rules

- **Never auto-submit** an application; the system stops at the submit button.
- **No fabrication** — every résumé claim traces to `career-profile.md`; even document metadata
  is corrected, never faked (`docx_finalize`).
- `personal/` is gitignored and holds all PII — never commit anything under it.
- **Keep career details out of commit messages.** `personal/` being gitignored protects the
  *files*, not the *prose you write about them*. A commit message is permanent, public, and
  outside every check that guards the working tree — and bugs here are usually found by
  hitting a real résumé, so the temptation to explain the defect in specifics is constant.
  Describe the **defect class and the fix**, never the user's history.

  | Don't | Do |
  |---|---|
  | name an employer, job title, or company applied to | "an employer entry", "a posting" |
  | quote a real résumé bullet, metric, or salary | "a bullet", "a figure" |
  | tie a specific tool to a specific employer | "a tool credited to the wrong employer" |

  A commit that opened by quoting a real bullet and naming the employer's warehouse should
  have read: **"Developer caught an incorrect bullet; additional checks added."** That is
  enough for anyone reading the history to understand the change. The reproduction detail
  belongs in a test, where it is fictional, or in gitignored notes.

  Enforced by `tools/check_commit_msg.py`, installed as a `commit-msg` hook (see setup
  above). It reads employer names from the gitignored profile rather than hardcoding them,
  and applies a stricter net — quoted document text, warehouse/BI tool names — only when the
  message is already discussing a résumé, a posting, or an employer.
- Tests for pure logic are cheap and expected — if you touch `jobkey`, `pipeline_store`,
  `ats_match`, or a builder, add/extend a test in `tests/`.

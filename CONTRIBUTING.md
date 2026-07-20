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
pre-commit install                                # runs the lint gate before each commit
```

## The everyday commands

```bash
python -m unittest discover -s tests   # run the tests (stdlib unittest; pytest also works)
ruff check .                           # lint against pyproject.toml [tool.ruff]
ruff check . --fix                     # auto-fix what's safe
python engine/test_links.py            # integration smoke: every dashboard link resolves
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
- Tests for pure logic are cheap and expected — if you touch `jobkey`, `pipeline_store`,
  `ats_match`, or a builder, add/extend a test in `tests/`.

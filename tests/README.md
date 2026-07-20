# Tests

Stdlib `unittest` — no pytest required. From the repo root:

```
python -m unittest discover -s tests
```

(`pytest tests/` also works if you have it.)

| File | Covers |
|---|---|
| `test_jobkey.py` | Canonical job identity (F1): company-suffix + title-noise dedupe. Config-free. |
| `test_builders.py` | Doc-builder pure logic (F2): placeholder scan + resume ATS-rule validator. Needs `python-docx`. |
| `test_pipeline_store.py` | Datastore repository table logic (F4): row insert + recount, in-memory. Needs a configured `personal/` (run `setup.py` first). |

These cover the deterministic core. Scoring functions (`lead_score.score_row`,
`ats_match`) are config-coupled — pinning them needs a rubric-injection refactor
(tracked as F6 in `.engineering-standard/architecture-review.md`).

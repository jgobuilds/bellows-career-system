#!/usr/bin/env python3
"""resume_coverage.py — did this resume SELECT the right accomplishments?

    python engine/resume_coverage.py <spec.json>              # reads jd.txt beside it
    python engine/resume_coverage.py <spec.json> --jd JD.txt
    python engine/resume_coverage.py <spec.json> --top 8

WHY THIS EXISTS: every other check asks whether what is on the page is GOOD.
None of them asks whether it is the RIGHT THING. The distinction is not academic
-- an advisory bullet about restructuring a vendor contract survived onto a data
engineering resume through four rounds of review. It was true, it was verified in
the bullet library, its number was in the metric registry, and it scored fine. It
was simply the wrong accomplishment, while a medallion build on the exact stack
the posting named sat unused in the profile.

THE FAILURE MODE IS INHERITANCE, NOT FABRICATION. Resumes get built by copying
the last one and editing the top against the new posting. Anything not obviously
wrong survives untouched, so a bullet propagates by never being noticed. Nothing
forces a re-read of the profile per application, and the profile is a SELECTION
POOL holding far more than any two pages can carry.

So this reports three things, and proposes nothing that is not already in the
profile -- it cannot invent a claim, only make a non-selection visible:

  LEFT ON THE TABLE   profile accomplishments that score well against this
                      posting and are not on the resume
  EARNING ITS PLACE?  bullets on the resume that answer little in the posting
  INHERITED           bullets appearing verbatim in other applications, which
                      is the signature of a copy-forward rather than a choice

IT PRINTS AND NEVER FAILS. Relevance is a judgement, a gate that makes judgements
produces false positives, false positives get suppressed, and a suppressed gate is
worse than none because it is trusted. Same call as the crossref scanner in the
sibling repo, for the same reason: it proposes, a human disposes.

The scoring is deliberately crude -- token overlap, with the profile's own
`Themes:` tags weighted double. A cleverer relevance model would be tuned against
nothing and trusted more than it earned. The useful output is the ordering, not
the number.
"""

import argparse
import json
import os
import re
import sys

import _paths  # noqa: F401  (side-effect: repo root on sys.path for `import config`)
import config

# Words that carry no signal about WHICH accomplishment fits a posting. Kept short
# on purpose: an aggressive stoplist quietly removes the domain words that matter.
STOP = frozenset(
    """
a an the and or but if then than that this these those with without within into onto
of to for from by on at in as is are was were be been being have has had do does did
will would can could should may might must our your their its it we you they he she
i me my us them who whom which what when where how why all any both each few more most
other some such no nor not only own same so too very s t just don now here there
work working works role roles team teams new using use used across other including
strong stellar proven track record experience ability able help helps helping
""".split()
)

_WORD = re.compile(r"[a-z0-9][a-z0-9+#./-]*")

# Recruiting vocabulary where two words mean one thing. Without this, "managing and
# scaling Data Engineering teams" reads as UNANSWERED next to "Led a 25-person data
# engineering organization" — the words differ, the claim does not, and the coverage
# number is then wrong in the direction that causes real damage: it invents gaps,
# which invites padding the resume to close them.
#
# Deliberately small and hand-written. Every group is a synonym in THIS domain, not
# a loose association — "lead" and "manage" are the same claim, "lead" and "inspire"
# are not. A bigger map would match more and mean less, and the failure would be
# silent because an inflated score looks like good news.
CONCEPTS = {
    "LEAD": (
        "lead",
        "led",
        "leading",
        "manage",
        "managing",
        "managed",
        "management",
        "run",
        "ran",
        "running",
        "direct",
        "directed",
        "head",
        "headed",
        "oversee",
        "oversaw",
        "own",
        "owns",
        "owned",
        "owning",
        "supervise",
    ),
    "SCALE": (
        "scale",
        "scaling",
        "scaled",
        "grow",
        "grew",
        "growing",
        "growth",
        "expand",
        "expanded",
        "expansion",
        "hypergrowth",
    ),
    "DEVELOP": (
        "develop",
        "developed",
        "developing",
        "coach",
        "coached",
        "coaching",
        "mentor",
        "mentored",
        "upskill",
        "upskilling",
        "train",
        "training",
        "enable",
        "enablement",
        "cultivate",
        "empower",
        "empowered",
    ),
    "BUILD": (
        "build",
        "built",
        "building",
        "establish",
        "established",
        "create",
        "created",
        "stood",
        "found",
        "founded",
        "architect",
        "architected",
        "designed",
    ),
    "PARTNER": (
        "collaborate",
        "collaboration",
        "partner",
        "partnered",
        "partnering",
        "partnership",
        "stakeholder",
        "cross-functional",
        "influence",
        "align",
        "alignment",
        "communicate",
        "communication",
    ),
    "DELIVER": (
        "deliver",
        "delivered",
        "delivery",
        "ship",
        "shipped",
        "launch",
        "launched",
        "execute",
        "execution",
        "outcome",
        "outcomes",
        "on-time",
        "benchmark",
    ),
    "QUALITY": (
        "quality",
        "reliability",
        "reliable",
        "trust",
        "trusted",
        "trustworthy",
        "observability",
        "accuracy",
        "sla",
        "slas",
        "incident",
        "uptime",
    ),
    "GOVERN": (
        "governance",
        "governed",
        "steward",
        "stewardship",
        "policy",
        "compliance",
        "classification",
        "lineage",
        "catalog",
        "metadata",
        "contract",
        "contracts",
    ),
    "PIPELINE": (
        "pipeline",
        "pipelines",
        "etl",
        "elt",
        "ingestion",
        "ingest",
        "transform",
        "transformation",
        "orchestration",
        "warehouse",
        "lakehouse",
        "infrastructure",
    ),
    "MODEL": (
        "model",
        "modeling",
        "models",
        "modelling",
        "dimensional",
        "schema",
        "semantic",
        "canonical",
        "domain-driven",
        "mesh",
        "medallion",
    ),
    "IMPACT": (
        "impact",
        "business",
        "value",
        "roi",
        "revenue",
        "cost",
        "savings",
        "trade-offs",
        "tradeoffs",
        "strategic",
        "prioritization",
        "prioritize",
    ),
    "PRODUCT": ("product", "products", "ownership", "owner", "owners"),
    "CRAFT": (
        "craft",
        "excellence",
        "standards",
        "best",
        "practices",
        "knowledge",
        "sharing",
        "improvement",
        "rigor",
        "review",
    ),
    "AI": (
        "ai",
        "llm",
        "llms",
        "agent",
        "agents",
        "genai",
        "copilot",
        "automation",
        "automate",
        "automated",
    ),
}
_CONCEPT_OF = {w: c for c, words in CONCEPTS.items() for w in words}


def concepts(toks: set[str]) -> set[str]:
    """Fold a token set into concept ids, keeping any token that maps to none.

    Returned alongside the raw tokens rather than replacing them: an exact tool
    name must still match exactly, and collapsing "bigquery" into a concept would
    lose the one comparison where only the literal string counts.
    """
    return {_CONCEPT_OF.get(t, t) for t in toks}


# A profile accomplishment line: "- <text> | Result: <r> | Themes: <t1, t2> `[notes]`"
_ACC = re.compile(r"^\s*-\s+(?P<body>.+?)\s*$")


def tokens(text: str) -> set[str]:
    """Lowercase content words, with the trailing plural dropped so "pipelines"
    and "pipeline" are the same signal. Crude stemming beats none and is honest
    about being crude."""
    out = set()
    for w in _WORD.findall((text or "").lower()):
        if w in STOP or len(w) < 3:
            continue
        out.add(w[:-1] if len(w) > 4 and w.endswith("s") and not w.endswith("ss") else w)
    return out


def parse_profile(path: str) -> list[dict]:
    """Accomplishment lines from career-profile.md.

    A line qualifies when it carries a `| Themes:` tag, which is the profile's own
    marker for a claimable accomplishment. Prose, framing notes and decision logs
    have no themes and are skipped -- so this reads the pool WITHOUT needing the
    profile to be restructured for it.
    """
    accs, section = [], "?"
    with open(path, encoding="utf-8") as fh:
        lines = fh.readlines()
    for raw in lines:
        if raw.startswith("###"):
            section = raw.lstrip("#").strip().split("—")[0].strip()
        m = _ACC.match(raw)
        if not m or "| Themes:" not in raw:
            continue
        body = m.group("body")
        body = re.sub(r"`\[.*?\]`", "", body, flags=re.S)  # drop the agent-note brackets
        head, _, rest = body.partition("| Themes:")
        themes = [t.strip() for t in rest.split("`")[0].split(",") if t.strip()]
        claim, _, result = head.partition("| Result:")
        accs.append(
            {
                "section": section,
                "claim": claim.strip(),
                "result": result.strip(),
                "themes": themes,
                "tokens": tokens(claim) | tokens(result) | {t for th in themes for t in tokens(th)},
                "theme_tokens": {t for th in themes for t in tokens(th)},
            }
        )
    return accs


def spec_bullets(spec: dict) -> list[dict]:
    out = []
    for entry in spec.get("experience", []) + spec.get("advisory", []):
        for role in entry.get("roles") or [entry]:
            company = entry.get("company", "?")
            for lead, rest in role.get("bullets") or []:
                text = f"{lead}{rest}".strip()
                out.append({"company": company, "text": text, "tokens": tokens(text)})
    for e in spec.get("earlier", []):
        if e.get("bullet"):
            out.append(
                {
                    "company": e.get("company", "?"),
                    "text": e["bullet"],
                    "tokens": tokens(e["bullet"]),
                }
            )
    return out


def score(item_tokens: set[str], jd: set[str], theme_tokens: set[str] | None = None) -> int:
    """Overlap with the posting. The profile's own theme tags count double: a
    hand-written tag is a stronger statement of what an accomplishment IS than
    any word that happens to appear in its prose."""
    return len(item_tokens & jd) + len((theme_tokens or set()) & jd)


def _on_resume(acc: dict, bullets: list[dict]) -> bool:
    """Is this accomplishment already represented? Judged by token overlap with a
    bullet rather than string match, because a bullet is a REPHRASING of the
    profile line, never a copy of it."""
    for b in bullets:
        shared = acc["tokens"] & b["tokens"]
        if len(shared) >= 4 and len(shared) >= 0.4 * min(len(acc["tokens"]), len(b["tokens"])):
            return True
    return False


def inherited(spec_path: str, bullets: list[dict]) -> dict[str, int]:
    """How many OTHER applications carry each bullet verbatim.

    Not a defect on its own -- a strong bullet belongs on many resumes. It is a
    provenance signal: a bullet in five other documents was almost certainly
    copied forward rather than chosen for this posting, and deserves a second
    look that a freshly written one does not.
    """
    here = os.path.abspath(spec_path)
    root = os.path.dirname(os.path.dirname(here))
    counts = {b["text"]: 0 for b in bullets}
    if not os.path.isdir(root):
        return counts
    for folder in sorted(os.listdir(root)):
        other = os.path.join(root, folder, "resume.json")
        if not os.path.isfile(other) or os.path.abspath(other) == here:
            continue
        try:
            with open(other, encoding="utf-8") as fh:
                texts = {b["text"] for b in spec_bullets(json.load(fh))}
        except (OSError, ValueError):
            continue
        for t in counts:
            if t in texts:
                counts[t] += 1
    return counts


# A requirement counts as answered when a bullet hits a PROPORTION of what it asks
# for, not a fixed number of words. A flat threshold cannot work because
# requirements are not the same length: "Embrace AI and LLMs to accelerate
# repetitive tasks" carries about four ideas and a bullet answering two of them has
# answered it, while a long compound requirement needs more before the match is
# real. A flat 3 marked the AI requirement uncovered on a resume whose bullet is
# about shipping agents.
#
# Two conditions, both cheap to state and neither tuned to make the number look
# better: at least two ideas in common, and at least a third of what was asked.
COVER_MIN_HITS = 2
COVER_MIN_RATIO = 0.30

# Published guidance to candidates is roughly this: meet most of what is asked and
# leave room to grow. A resume claiming EVERYTHING is not a stronger application,
# it is a less believable one — and it usually means bullets were stretched to
# reach. So the target is a band with a ceiling, not a maximum.
TARGET_LOW, TARGET_HIGH = 0.70, 0.90


def best_match(req_tokens: set[str], bullets: list[dict]) -> tuple[dict | None, int]:
    """The resume bullet that best answers a requirement, and by how much.

    Matched on CONCEPTS, not raw words, so a requirement to "manage and scale"
    is answered by a bullet that says "led" and "25-person".
    """
    req = concepts(req_tokens)
    best, best_n = None, 0
    for b in bullets:
        n = len(req & concepts(b["tokens"]))
        if n > best_n:
            best, best_n = b, n
    return best, best_n


def report(spec_path: str, jd_text: str, top: int = 6) -> int:
    import jd_requirements

    with open(spec_path, encoding="utf-8") as fh:
        spec = json.load(fh)
    jd = tokens(jd_text)
    bullets = spec_bullets(spec)
    accs = parse_profile(config.PROFILE_MD)
    if not accs:
        print(f"  no accomplishment lines found in {config.PROFILE_MD}")
        return 1

    reqs = [r for r in jd_requirements.requirements(jd_text) if r["kind"] == "demonstrable"]
    disp = [r for r in jd_requirements.requirements(jd_text) if r["kind"] == "disposition"]
    techs = jd_requirements.technologies(jd_text)
    spec_text = tokens(json.dumps(spec))

    for r in reqs:
        r["tokens"] = tokens(r["text"])
        r["concepts"] = concepts(r["tokens"])
        r["bullet"], r["hits"] = best_match(r["tokens"], bullets)
        need = max(1, len(r["concepts"]))
        r["covered"] = r["hits"] >= COVER_MIN_HITS and r["hits"] / need >= COVER_MIN_RATIO

    got = sum(r["weight"] for r in reqs if r["covered"])
    want = sum(r["weight"] for r in reqs) or 1
    pct = got / want
    gaps = [r for r in reqs if not r["covered"]]

    print(f"  profile pool: {len(accs)} accomplishments   ·   resume: {len(bullets)} bullets")
    print(f"  posting: {len(reqs)} demonstrable requirement(s), {len(disp)} dispositional\n")

    band = (
        "on target"
        if TARGET_LOW <= pct <= TARGET_HIGH
        else (
            "below target — close the closable gaps below"
            if pct < TARGET_LOW
            else "above target — check nothing was stretched to reach"
        )
    )
    print(f"REQUIREMENT COVERAGE   {pct:.0%}  (weighted)   → {band}")
    print(f"   target band {TARGET_LOW:.0%}–{TARGET_HIGH:.0%}. Gaps are normal and fine to show;")
    print("   a document answering everything reads as stretched, not as strong.\n")

    # Technologies are the one place an exact match is the whole game.
    missing_tech = [
        t
        for t in techs
        if t.replace(" ", "") not in "".join(sorted(spec_text))
        and not any(t in b["text"].lower() for b in bullets)
        and t not in " ".join(spec_text)
    ]
    have = [t for t in techs if t not in missing_tech]
    if techs:
        print(f"NAMED TECHNOLOGIES   {len(have)}/{len(techs)}")
        print(f"   on the resume : {', '.join(have) if have else '(none)'}")
        print(f"   NOT on it     : {', '.join(missing_tech) if missing_tech else '(none)'}")
        if missing_tech:
            print("   ⛔ A named tool you have not used is a REAL gap. Never reach for a")
            print("      near-neighbour to cover one — that trade costs more than the keyword.")
        print()

    if gaps:
        print(f"GAPS — {len(gaps)} requirement(s) with nothing answering them")
        for r in sorted(gaps, key=lambda x: -x["weight"]):
            rc = concepts(r["tokens"])
            closable = sorted(
                (a for a in accs if not _on_resume(a, bullets)),
                key=lambda a: -len(concepts(a["tokens"]) & rc),
            )
            best = closable[0] if closable else None
            n = len(concepts(best["tokens"]) & rc) if best else 0
            print(f"   [w{r['weight']}] {r['text'][:82]}")
            if best and n >= COVER_MIN_HITS and n / max(1, len(rc)) >= COVER_MIN_RATIO:
                print(f"         ↳ CLOSABLE from the profile: {best['claim'][:66]}")
            else:
                print("         ↳ no profile evidence — a real gap, and fine to have")
        print()

    missing = sorted(
        (a for a in accs if not _on_resume(a, bullets)),
        key=lambda a: -score(a["tokens"], jd, a["theme_tokens"]),
    )
    print("LEFT ON THE TABLE — scores well here, not on the resume")
    shown = [a for a in missing if score(a["tokens"], jd, a["theme_tokens"]) > 0][:top]
    if not shown:
        print("   nothing above zero — the pool is well covered\n")
    for a in shown:
        s = score(a["tokens"], jd, a["theme_tokens"])
        print(f"   [{s:3}] {a['section'][:26]:26} {a['claim'][:78]}")
        if a["result"]:
            print(f"         → {a['result'][:78]}")
    print()

    print("EARNING ITS PLACE? — on the resume, answers little in the posting")
    weak = sorted(bullets, key=lambda b: score(b["tokens"], jd))[:top]
    floor = max(
        3, int(0.25 * (sum(score(b["tokens"], jd) for b in bullets) / max(1, len(bullets))))
    )
    flagged = [b for b in weak if score(b["tokens"], jd) < floor]
    if not flagged:
        print(f"   none below the bar ({floor})\n")
    for b in flagged:
        print(f"   [{score(b['tokens'], jd):3}] {b['company'][:20]:20} {b['text'][:74]}")
    print()

    counts = inherited(spec_path, bullets)
    carried = sorted(((n, b) for b, n in counts.items() if n), reverse=True, key=lambda x: x[0])
    print("INHERITED — appears verbatim in other applications")
    if not carried:
        print("   none — every bullet is unique to this application")
    for n, text in carried[:top]:
        print(f"   in {n:2} other(s)  {text[:74]}")
    print("\n  Advisory only. Relevance is a judgement — this proposes, you dispose.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Did this resume select the right accomplishments?")
    ap.add_argument("spec")
    ap.add_argument("--jd", help="job-description text file (default: jd.txt beside the spec)")
    ap.add_argument("--top", type=int, default=6)
    a = ap.parse_args()

    jd_path = a.jd or os.path.join(os.path.dirname(os.path.abspath(a.spec)), "jd.txt")
    if not os.path.isfile(jd_path):
        print(f"  no job description at {jd_path}")
        print("  Save the posting text as jd.txt in the application folder, or pass --jd.")
        print("  Storing it is the point: without it the selection cannot be re-checked later.")
        return 1
    with open(jd_path, encoding="utf-8") as fh:
        return report(a.spec, fh.read(), a.top)


if __name__ == "__main__":
    sys.exit(main())

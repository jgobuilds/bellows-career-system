#!/usr/bin/env python3
"""jd_requirements.py — read a job posting as a list of REQUIREMENTS, not a bag of words.

    python engine/jd_requirements.py <jd.txt>

WHY: token overlap against a whole posting answers "is this bullet vaguely on
topic". It cannot answer the question that actually decides a resume — "which of
the things they asked for does this document demonstrate, and which does it
leave unanswered". Those need the posting split into the discrete asks it is
already written as.

Postings are structured, so this reads the structure rather than guessing at it:
bulleted lines under the responsibilities and qualifications headings are the
requirements, and each one is a single ask.

WEIGHTING. A requirement stated under "what we're looking for" is a filter; one
under "what you'll do" describes the job. Both matter, the first slightly more,
because that is the list a screener reads with a pen. Anything repeated across
sections is weighted up again — a posting that says a thing twice means it.

NAMED TECHNOLOGIES are extracted separately and are the one place an exact match
is the whole game. "Strong command of BigQuery, dbt, Airflow, Kafka, Spark,
Flink, or similar" is six checks, not one, and reporting it as a single satisfied
requirement would hide that two thirds of the list is missing.
"""

import argparse
import re
import sys

# Headings that introduce a run of requirement bullets. Matched loosely because
# every company words them differently and the shape is what matters.
_WANT = re.compile(
    r"what we.?re looking for|qualifications|requirements|you (?:should )?have|"
    r"about you|who you are|skills|experience (?:you|we)",
    re.I,
)
_DO = re.compile(
    r"what you.?ll do|responsibilities|the role|your (?:mission|impact)|day to day|"
    r"in this role|about the role",
    re.I,
)
_BULLET = re.compile(r"^\s*[*\-•‣▪●]\s+(?P<text>.+?)\s*$")

# Asks about TEMPERAMENT rather than evidence. "Care deeply", "thrive on change",
# "work digital-first" are real requirements and a resume cannot answer any of
# them — no bullet evidences a disposition. They are counted separately so the
# coverage figure stays honest: folding them into the denominator invents a gap
# the document could never close, and folding them into the numerator claims
# credit no bullet earned. They belong to the interview.
_DISPOSITION = re.compile(
    r"^(care|thrive|excel|embrace|be resilient|bring critical|keep up|work digital|"
    r"comfortable|enjoy|love|passion|curious|humble|bias for|self-start|own your|"
    r"you are|willing|eager|hungry)",
    re.I,
)
_DISPOSITION_ANY = re.compile(
    r"\b(fast-paced|unrelenting pace|hypergrowth|get shit done|culture fit|"
    r"team player|can-do|roll up your sleeves)\b",
    re.I,
)
# Words that make a line checkable no matter what else it says.
_EVIDENCE = re.compile(
    r"\b(data|pipeline|governance|model|modeling|architect|architecture|engineer|"
    r"sql|cloud|quality|lineage|team|deliver|stakeholder|budget|platform|"
    # AI terms belong here: "Embrace AI and LLMs to accelerate repetitive tasks"
    # opens on a disposition verb and is entirely checkable — a tooling rollout
    # and shipped agents evidence it. Classifying it as temperament dropped the
    # single strongest match on the posting out of the coverage denominator.
    r"ai|llm|agent|automation|automate|tooling|ml|analytics|reporting|metric)\b",
    re.I,
)


def _kind(text: str) -> str:
    """`demonstrable` if a bullet could evidence it, `disposition` otherwise.

    A line can name a real skill AND a temperament — "thrive in fast-paced
    environments while maintaining focus on data quality, governance and lineage".
    Those stay demonstrable: the skill half is checkable, and discarding the line
    would lose a genuine requirement.
    """
    body = text.strip()
    if _DISPOSITION.match(body) and not _EVIDENCE.search(body):
        return "disposition"
    if _DISPOSITION_ANY.search(body) and not _EVIDENCE.search(body):
        return "disposition"
    return "demonstrable"


# Tools worth checking by exact name. A posting naming one is making a specific,
# checkable claim about the stack, and a near-miss is not a match: "we run Kafka"
# is not answered by "we ran micro-batch", and pretending otherwise is the exact
# credibility trade this whole system exists to refuse.
TECHNOLOGIES = (
    "bigquery",
    "snowflake",
    "redshift",
    "databricks",
    "synapse",
    "postgres",
    "postgresql",
    "mysql",
    "oracle",
    "dbt",
    "airflow",
    "dagster",
    "prefect",
    "composer",
    "kafka",
    "spark",
    "flink",
    "beam",
    "kinesis",
    "pubsub",
    "fivetran",
    "stitch",
    "airbyte",
    "informatica",
    "talend",
    "looker",
    "tableau",
    "power bi",
    "sigma",
    "metabase",
    "mode",
    "superset",
    "python",
    "sql",
    "scala",
    "java",
    "go",
    "terraform",
    "kubernetes",
    "docker",
    "aws",
    "gcp",
    "azure",
    "s3",
    "lambda",
    "glue",
    "emr",
    "athena",
    "elementary",
    "monte carlo",
    "great expectations",
    "atlan",
    "collibra",
    "alation",
    "datahub",
    "hightouch",
    "census",
    "ci/cd",
    "git",
    "github",
    "gitlab",
    "mcp",
    "llm",
    "langchain",
)


def _lines(text: str) -> list[str]:
    return [ln.rstrip() for ln in (text or "").splitlines()]


def requirements(text: str) -> list[dict]:
    """The posting's discrete asks, each with a weight and the section it came from.

    A bullet outside any recognised heading still counts, at base weight — plenty
    of postings never use a heading this recognises, and dropping those silently
    would report a suspiciously clean coverage score on a posting we simply failed
    to read.
    """
    out: list[dict] = []
    section = "other"
    for ln in _lines(text):
        stripped = ln.strip()
        if stripped and not _BULLET.match(ln):
            if _WANT.search(stripped) and len(stripped) < 90:
                section = "looking-for"
                continue
            if _DO.search(stripped) and len(stripped) < 90:
                section = "responsibilities"
                continue
        m = _BULLET.match(ln)
        if not m:
            continue
        body = m.group("text").strip(" *")
        if len(body) < 12:  # a fragment, not an ask
            continue
        out.append(
            {
                "text": body,
                "section": section,
                "kind": _kind(body),
                "weight": {"looking-for": 3, "responsibilities": 2}.get(section, 1),
            }
        )
    return _dedupe(out)


def _dedupe(reqs: list[dict]) -> list[dict]:
    """Fold near-identical asks and weight the survivor up. A posting that states a
    requirement in two sections means it, and counting it twice would let one
    strongly-covered theme inflate the coverage score."""
    kept: list[dict] = []
    for r in reqs:
        key = frozenset(w for w in re.findall(r"[a-z]{4,}", r["text"].lower()))
        for k in kept:
            if key and len(key & k["_key"]) >= 0.7 * min(len(key), len(k["_key"])):
                k["weight"] += 1
                break
        else:
            kept.append({**r, "_key": key})
    for k in kept:
        k.pop("_key", None)
    return kept


def technologies(text: str) -> list[str]:
    """Named tools, in the order the posting introduces them."""
    low = (text or "").lower()
    seen, out = set(), []
    for tech in TECHNOLOGIES:
        pat = re.escape(tech).replace(r"\ ", r"\s+")
        if re.search(rf"(?<![a-z0-9]){pat}(?![a-z0-9])", low) and tech not in seen:
            seen.add(tech)
            out.append(tech)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Read a posting as requirements.")
    ap.add_argument("jd")
    a = ap.parse_args()
    with open(a.jd, encoding="utf-8") as fh:
        text = fh.read()
    reqs = requirements(text)
    techs = technologies(text)
    dem = [r for r in reqs if r["kind"] == "demonstrable"]
    dis = [r for r in reqs if r["kind"] == "disposition"]
    print(
        f"  {len(dem)} demonstrable, {len(dis)} dispositional, {len(techs)} named technolog(ies)\n"
    )
    for r in dem:
        print(f"   [w{r['weight']}] {r['section']:<16} {r['text'][:86]}")
    if dis:
        print("\n  DISPOSITION — no bullet can evidence these; they are the interview:")
        for r in dis:
            print(f"        {r['text'][:86]}")
    print(f"\n  technologies: {', '.join(techs) if techs else '(none named)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

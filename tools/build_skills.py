#!/usr/bin/env python3
"""build_skills.py — rebuild the shippable .skill packages from their sources.

    python tools/build_skills.py            # rebuild all
    python tools/build_skills.py --check    # report drift, change nothing
    python tools/build_skills.py <name> ... # rebuild only these

TWO COPIES, ONE DIRECTION. `.claude/skills/<name>/` is the SOURCE: editable,
reviewable in a diff, and what Claude Code actually loads while you work in this
repo. `skills/<name>.skill` is the GENERATED distributable, and it is the install
path the README hands to users. The arrow only ever points source -> bundle.

Editing an archive by hand is the failure this exists to prevent, because a stale
zip looks fine from the outside. Nothing about it reads as wrong until someone
installs it and gets a version of the skill that no longer exists in the repo.

Deterministic on purpose: entries are written in sorted order with a fixed
timestamp, so rebuilding unchanged sources produces an identical file and does not
show up as a spurious diff.
"""

import argparse
import hashlib
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SOURCES = REPO / ".claude" / "skills"
BUNDLES = REPO / "skills"

# Fixed so a rebuild of unchanged sources is byte-identical rather than a new diff.
EPOCH = (1980, 1, 1, 0, 0, 0)


def files_of(src):
    return sorted(p for p in src.rglob("*") if p.is_file())


CRLF, LF = bytes([13, 10]), bytes([10])


def _norm(data):
    """Line endings are not content.

    A checkout that hands back CRLF must not make every bundle look stale.
    `.gitattributes` pins these sources to LF; this survives a contributor whose
    git is configured otherwise. Written with byte values rather than escapes
    because an escaped one silently became a literal here once already.
    """
    return data.replace(CRLF, LF)


def digest_dir(src):
    return {
        str(p.relative_to(src)).replace("\\", "/"): hashlib.sha256(
            _norm(p.read_bytes())
        ).hexdigest()
        for p in files_of(src)
    }


def digest_bundle(path):
    if not path.is_file():
        return None
    with zipfile.ZipFile(path) as z:
        return {
            n.split("/", 1)[1]: hashlib.sha256(_norm(z.read(n))).hexdigest()
            for n in z.namelist()
            if not n.endswith("/")
        }


def build(src, target):
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in files_of(src):
            rel = str(p.relative_to(src)).replace("\\", "/")
            info = zipfile.ZipInfo(f"{src.name}/{rel}", date_time=EPOCH)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, p.read_bytes())


def main():
    ap = argparse.ArgumentParser(description="Rebuild .skill packages from sources.")
    ap.add_argument("names", nargs="*", help="skill names; default is all")
    ap.add_argument("--check", action="store_true", help="report drift without writing")
    a = ap.parse_args()

    if not SOURCES.is_dir():
        print(f"  no sources at {SOURCES}")
        return 1

    wanted = set(a.names)
    drifted, rebuilt = [], []
    for src in sorted(d for d in SOURCES.iterdir() if d.is_dir()):
        if wanted and src.name not in wanted:
            continue
        target = BUNDLES / f"{src.name}.skill"
        if digest_dir(src) == digest_bundle(target):
            continue
        drifted.append(src.name)
        if not a.check:
            BUNDLES.mkdir(parents=True, exist_ok=True)
            build(src, target)
            rebuilt.append(src.name)

    if a.check:
        if drifted:
            print(f"  {len(drifted)} bundle(s) out of date: {', '.join(drifted)}")
            print("  Run `python tools/build_skills.py` to regenerate them.")
            return 1
        print("  every bundle matches its source.")
        return 0

    if rebuilt:
        for n in rebuilt:
            print(f"  rebuilt  {n}.skill")
        print(f"\n  {len(rebuilt)} bundle(s) regenerated from source.")
    else:
        print("  nothing to do — every bundle already matches its source.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

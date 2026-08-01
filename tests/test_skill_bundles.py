"""The `.skill` bundles must match the sources they are built from.

WHY THIS EXISTS: `.claude/skills/<name>/` is the SOURCE — editable, reviewable in a
diff, and what Claude Code actually loads. `skills/<name>.skill` is a GENERATED
distributable, and it is the documented install path for users ("Install the
`*.skill` packages in `skills/`" — README step 2). Two copies of the same content
means they can disagree, and a zip disagrees silently: nothing about a stale
archive looks wrong until someone installs it and gets last month's skill.

Before the sources existed, the bundles were the only copy and nothing validated
them at all. Four descriptions drifted to within a few characters of the hard
limit, and one past it, with no warning — because a checker that reads directories
found nothing to read.

Compares CONTENT, not archive bytes: zip files differ on timestamps and compression
without differing on anything that matters.
"""

import hashlib
import unittest
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SOURCES = REPO / ".claude" / "skills"
BUNDLES = REPO / "skills"


CRLF, LF = bytes([13, 10]), bytes([10])


def _norm(data):
    """Compare content, not line endings.

    A checkout with core.autocrlf=true hands back CRLF while git stores LF, so a
    byte comparison would report every bundle as drifted on a clone that changed
    nothing. This was not hypothetical: the sources were first committed from a
    CRLF working tree with bundles built to match, which made the drift check fail
    for anyone cloning fresh. `.gitattributes` now pins the sources to LF, and this
    keeps the check honest for a contributor whose git is configured otherwise.

    Written with byte values rather than escapes because an escaped one silently
    became a literal newline here once already.
    """
    return data.replace(CRLF, LF)


def digest_dir(path):
    return {
        str(p.relative_to(path)).replace("\\", "/"): hashlib.sha256(
            _norm(p.read_bytes())
        ).hexdigest()
        for p in sorted(path.rglob("*"))
        if p.is_file()
    }


def digest_bundle(path):
    with zipfile.ZipFile(path) as z:
        return {
            n.split("/", 1)[1]: hashlib.sha256(_norm(z.read(n))).hexdigest()
            for n in sorted(z.namelist())
            if not n.endswith("/")
        }


class SkillBundleTest(unittest.TestCase):
    def test_every_bundle_has_a_source(self):
        missing = [
            b.stem for b in sorted(BUNDLES.glob("*.skill")) if not (SOURCES / b.stem).is_dir()
        ]
        self.assertEqual(missing, [], f"bundles with no source directory: {missing}")

    def test_every_source_has_a_bundle(self):
        # A source with no bundle ships to nobody: the install docs point at
        # `skills/`, so a skill that never gets packaged is invisible downstream.
        missing = [
            d.name
            for d in sorted(SOURCES.iterdir())
            if d.is_dir() and not (BUNDLES / f"{d.name}.skill").is_file()
        ]
        self.assertEqual(missing, [], f"sources never packaged: {missing}")

    def test_no_bundle_has_drifted_from_its_source(self):
        drifted = []
        for b in sorted(BUNDLES.glob("*.skill")):
            src = SOURCES / b.stem
            if not src.is_dir():
                continue
            if digest_dir(src) != digest_bundle(b):
                drifted.append(b.stem)
        self.assertEqual(
            drifted,
            [],
            "these bundles no longer match their sources — rebuild them rather than "
            f"editing the archive: {drifted}",
        )

    def test_each_source_has_a_skill_md(self):
        for d in sorted(SOURCES.iterdir()):
            if d.is_dir():
                self.assertTrue((d / "SKILL.md").is_file(), f"{d.name} has no SKILL.md")


if __name__ == "__main__":
    unittest.main()

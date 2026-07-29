"""The vendored scope gate must not silently drift from the copy that runs.

WHY THIS EXISTS. `scripts/staged_scope_check.py` is VENDORED — a copy of a script
that lives upstream in the house standards repo. It is vendored deliberately:
this repo is public and carries no overlay, so a contributor cannot be assumed to
have the private sibling on disk, and a gate they cannot run is not a gate.

The failure mode that follows is specific and it already happened. The developer's
own pre-commit hook points at the UPSTREAM copy, not this one. So the vendored
copy is the only file in the repo that nobody executes: it fell 42 lines behind,
including a real fix to the ignored-file detector, and nothing noticed for days.

This test compares the two when the upstream repo is present and SKIPS when it is
not, so it does the work on the machine where drift originates and stays silent in
CI, where the sibling does not exist and never will. A skipped test in CI is the
correct outcome here, not a gap — CI cannot answer this question.
"""

import os
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
VENDORED = os.path.join(os.path.dirname(HERE), "scripts", "staged_scope_check.py")

# Sibling layout per the workspace standard: repos are peers under one parent.
UPSTREAM = os.path.normpath(
    os.path.join(os.path.dirname(HERE), "..", "ai-standards", "scripts", "staged_scope_check.py")
)


class VendoredScopeGateTest(unittest.TestCase):
    def test_vendored_copy_matches_upstream(self):
        if not os.path.isfile(UPSTREAM):
            self.skipTest("upstream ai-standards not on disk — nothing to compare against")
        self.assertTrue(os.path.isfile(VENDORED), "the vendored scope gate is missing")
        with open(UPSTREAM, encoding="utf-8") as fh:
            up = fh.read()
        with open(VENDORED, encoding="utf-8") as fh:
            ven = fh.read()
        self.assertEqual(
            ven,
            up,
            "scripts/staged_scope_check.py has drifted from the upstream copy that actually "
            "runs in the pre-commit hook. Re-vendor it:\n"
            f"  cp {UPSTREAM} {VENDORED}\n"
            "Contributors run the vendored copy; drift means they run a different gate.",
        )

    def test_vendored_copy_is_syntactically_valid(self):
        # Cheap, and it runs in CI where the comparison above cannot.
        with open(VENDORED, encoding="utf-8") as fh:
            compile(fh.read(), VENDORED, "exec")


if __name__ == "__main__":
    unittest.main()

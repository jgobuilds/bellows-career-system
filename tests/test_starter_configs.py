"""Tests for the shipped starter configs.

Two things are checked:

1. The worked example stays in step with the template. When a new setting is added
   to one and not the other, a new user copying the example silently loses a
   feature. WORK_AUTH was added to the template and would have drifted this way.

2. No config's own DROP lists eat its own targets. NOISE and OFF_CONTEXT discard
   roles silently, so a term that also appears in a target title or a core lane is
   a self-inflicted blind spot - the search would throw away exactly the jobs it
   was set up to find. This is the trap a non-technical user falls into by copying
   a data searcher's noise list unedited.
"""

import importlib.util
import os
import sys
import unittest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

import config as CFG

STARTER = os.path.join(_ROOT, "starter")
CONFIGS = {
    "template": os.path.join(STARTER, "userconfig.template.py"),
    "example": os.path.join(STARTER, "userconfig.example.py"),
}


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _settings(mod):
    return {k for k in vars(mod) if k.isupper() and not k.startswith("_")}


class TestStarterConfigsLoad(unittest.TestCase):
    def test_both_are_importable(self):
        for name, path in CONFIGS.items():
            self.assertTrue(os.path.exists(path), f"{name} missing at {path}")
            self.assertTrue(_settings(_load(path, f"cfg_{name}")), f"{name} defines no settings")


class TestExampleTracksTemplate(unittest.TestCase):
    def test_example_defines_every_template_setting(self):
        tmpl = _settings(_load(CONFIGS["template"], "cfg_t"))
        example = _settings(_load(CONFIGS["example"], "cfg_e"))
        missing = sorted(tmpl - example)
        self.assertEqual(
            missing,
            [],
            "starter/userconfig.example.py is missing settings the template has: "
            f"{missing}. A user copying the example would silently lose them.",
        )

    def test_example_introduces_no_unknown_settings(self):
        tmpl = _settings(_load(CONFIGS["template"], "cfg_t2"))
        example = _settings(_load(CONFIGS["example"], "cfg_e2"))
        self.assertEqual(sorted(example - tmpl), [])


class TestDropListsDoNotEatTargets(unittest.TestCase):
    """NOISE / OFF_CONTEXT drop silently. They must not match the config's own
    target titles or core lane terms."""

    def _check(self, name):
        mod = _load(CONFIGS[name], f"cfg_drop_{name}")
        targets = list(getattr(mod, "TARGET_TITLES", [])) + list(getattr(mod, "LANE_STRONG", []))
        for list_name in ("NOISE", "OFF_CONTEXT"):
            terms = getattr(mod, list_name, []) or []
            if not terms:
                continue
            rx = CFG.terms_to_regex(terms)
            for target in targets:
                hit = rx.search(target)
                self.assertIsNone(
                    hit,
                    f"{name}: {list_name} term {hit.group() if hit else ''!r} matches the "
                    f"target {target!r} — this search would silently discard its own results.",
                )

    def test_template_is_self_consistent(self):
        self._check("template")

    def test_example_is_self_consistent(self):
        self._check("example")


class TestExampleIsGenuinelyNonTechnical(unittest.TestCase):
    """The example exists to prove the engine is not data-specific. If it drifts
    back toward a data search it stops proving anything."""

    def test_lane_is_not_a_data_lane(self):
        mod = _load(CONFIGS["example"], "cfg_lane")
        lane = " ".join(mod.LANE_STRONG).lower()
        for data_term in ("data governance", "data platform", "analytics engineering"):
            self.assertNotIn(data_term, lane)

    def test_lane_is_populated(self):
        mod = _load(CONFIGS["example"], "cfg_lane2")
        self.assertGreaterEqual(len(mod.LANE_STRONG), 3)
        self.assertGreaterEqual(len(mod.TARGET_TITLES), 3)


if __name__ == "__main__":
    unittest.main()

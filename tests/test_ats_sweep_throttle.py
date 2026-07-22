"""Tests for the sweep's rate-limit defences.

The failure these guard against is silent and remote: you don't find out the
throttle is wrong from a stack trace, you find out when a board starts refusing
you. So the properties are pinned here rather than trusted.

The subtle one is _domain(). Keying the budget on the full hostname would give
every Workday tenant its own bucket, which looks implemented and does nothing —
tenants share Workday's infrastructure, and the burst is exactly what we're
trying to stop.
"""

import os
import sys
import unittest
from itertools import pairwise
from unittest.mock import patch

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "engine")
)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ats_sweep


class FrozenClock:
    """monotonic never advances, so a throttle decision is deterministic and we
    measure the worst case rather than a race."""

    def __init__(self):
        self.slept = []

    def monotonic(self):
        return 1000.0

    def sleep(self, n):
        self.slept.append(n)

    @property
    def total(self):
        return sum(self.slept)


class TestDomainKeying(unittest.TestCase):
    def test_workday_tenants_share_one_budget(self):
        a = ats_sweep._domain("https://acme.wd5.myworkdayjobs.com/wday/cxs/acme/Careers/jobs")
        b = ats_sweep._domain("https://beta.wd1.myworkdayjobs.com/wday/cxs/beta/External/jobs")
        self.assertEqual(a, b)
        self.assertEqual(a, "myworkdayjobs.com")

    def test_every_greenhouse_company_shares_one_budget(self):
        # they all resolve to boards-api.greenhouse.io, so per-company spacing was
        # never the same thing as per-host spacing
        self.assertEqual(
            ats_sweep._domain("https://boards-api.greenhouse.io/v1/boards/a/jobs"),
            ats_sweep._domain("https://boards-api.greenhouse.io/v1/boards/b/jobs"),
        )

    def test_different_ats_do_not_share(self):
        seen = {
            ats_sweep._domain(u)
            for u in (
                "https://boards-api.greenhouse.io/x",
                "https://api.lever.co/x",
                "https://api.ashbyhq.com/x",
                "https://api.smartrecruiters.com/x",
                "https://a.wd5.myworkdayjobs.com/x",
            )
        }
        self.assertEqual(len(seen), 5)

    def test_malformed_url_does_not_explode(self):
        for u in ("", "not a url", "https://"):
            self.assertIsInstance(ats_sweep._domain(u), str)


class TestThrottleSpacing(unittest.TestCase):
    def _run(self, urls):
        clock = FrozenClock()
        with (
            patch.object(ats_sweep, "time", clock),
            patch.object(ats_sweep.random, "uniform", lambda a, b: 0.1),
        ):
            ats_sweep._LAST_HIT.clear()
            for u in urls:
                ats_sweep._throttle(u)
            ats_sweep._LAST_HIT.clear()
        return clock

    def test_second_call_to_the_same_domain_waits(self):
        clock = self._run(
            ["https://boards-api.greenhouse.io/a", "https://boards-api.greenhouse.io/b"]
        )
        self.assertGreaterEqual(clock.total, ats_sweep.PER_CALL_PAUSE)

    def test_a_different_domain_does_not_wait(self):
        clock = self._run(["https://boards-api.greenhouse.io/a", "https://api.lever.co/b"])
        self.assertLess(clock.total, ats_sweep.PER_CALL_PAUSE)

    def test_enrichment_burst_is_throttled(self):
        # the original bug: _enrich_desc ran inside the row loop with no sleep, so a
        # Workday company with N in-lane roles fired N back-to-back requests
        clock = self._run(["https://acme.wd5.myworkdayjobs.com/job/%d" % i for i in range(5)])
        self.assertGreaterEqual(clock.total, ats_sweep.PER_CALL_PAUSE * 4)

    def test_jitter_is_applied(self):
        clock = self._run(["https://api.lever.co/only-one"])
        self.assertGreater(clock.total, 0, "a flat interval is a machine signature")


class TestInterleave(unittest.TestCase):
    def _companies(self):
        return (
            [{"ats": "greenhouse", "slug": f"g{i}"} for i in range(31)]
            + [{"ats": "workday", "tenant": f"w{i}"} for i in range(22)]
            + [{"ats": "ashby", "slug": f"a{i}"} for i in range(8)]
            + [{"ats": "lever", "slug": "l0"}]
        )

    def test_no_company_is_lost_or_duplicated(self):
        src = self._companies()
        out = ats_sweep._interleave(src)
        self.assertEqual(len(out), len(src))
        self.assertEqual(
            sorted(str(sorted(c.items())) for c in out),
            sorted(str(sorted(c.items())) for c in src),
        )

    def test_clustering_is_broken_up(self):
        order = [c["ats"] for c in ats_sweep._interleave(self._companies())]
        longest = cur = 1
        for prev, nxt in pairwise(order):
            cur = cur + 1 if nxt == prev else 1
            longest = max(longest, cur)
        # config order gives a run of 10; naive round-robin still leaves a tail of 9
        self.assertLessEqual(longest, 3, f"still clustering: longest run {longest}")

    def test_within_an_ats_the_original_order_is_kept(self):
        out = ats_sweep._interleave(self._companies())
        gh = [c["slug"] for c in out if c["ats"] == "greenhouse"]
        self.assertEqual(gh, [f"g{i}" for i in range(31)])

    def test_empty_and_single(self):
        self.assertEqual(ats_sweep._interleave([]), [])
        one = [{"ats": "lever", "slug": "x"}]
        self.assertEqual(ats_sweep._interleave(one), one)


class TestRateLimitIsNotAnError(unittest.TestCase):
    """A 429 means the feed is ALIVE. Reporting it as 'unreachable' invites
    pruning a good company from the config."""

    def test_rate_limited_is_its_own_exception(self):
        self.assertTrue(issubclass(ats_sweep.RateLimited, Exception))
        e = ats_sweep.RateLimited("greenhouse.io", 429)
        self.assertEqual(e.domain, "greenhouse.io")
        self.assertEqual(e.code, 429)
        self.assertIn("429", str(e))

    def test_retry_statuses_are_the_slow_down_signals(self):
        self.assertIn(429, ats_sweep.RETRY_STATUS)
        self.assertIn(503, ats_sweep.RETRY_STATUS)
        self.assertNotIn(404, ats_sweep.RETRY_STATUS)  # a dead slug must NOT retry


if __name__ == "__main__":
    unittest.main()

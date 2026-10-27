"""reconcile.stale: the logic that decides whether a lost bump is resubmitted."""

from __future__ import annotations

import unittest
from unittest import mock

import reconcile


def build(state, version):
    return {"state": state, "source_package": {"version": version}}


class StaleTest(unittest.TestCase):
    def run_stale(self, builds, nvr="2.0-1", **kw):
        with mock.patch.object(reconcile, "spec_nvr", return_value=nvr):
            return reconcile.stale(["p"], builds, **kw)

    def test_published_is_not_stale(self):
        b = build("succeeded", "2.0-1")
        self.assertEqual(self.run_stale({"p": {"latest": b, "latest_succeeded": b}}), ([], []))

    def test_bump_never_built(self):
        b = build("succeeded", "1.0-1")
        self.assertEqual(self.run_stale({"p": {"latest": b, "latest_succeeded": b}}), (["p"], []))

    def test_never_built_at_all(self):
        self.assertEqual(self.run_stale({}), (["p"], []))

    def test_failed_build_is_stale_and_reported(self):
        old, bad = build("succeeded", "1.0-1"), build("failed", "2.0-1")
        # the failed build is for an OLDER nvr than the spec: a fresh attempt
        bad = build("failed", "1.5-1")
        self.assertEqual(self.run_stale({"p": {"latest": bad, "latest_succeeded": old}}), (["p"], ["p"]))

    def test_same_nvr_failure_is_reported_not_retried(self):
        old, bad = build("succeeded", "1.0-1"), build("failed", "2.0-1")
        b = {"p": {"latest": bad, "latest_succeeded": old}}
        self.assertEqual(self.run_stale(b), ([], ["p"]))
        self.assertEqual(self.run_stale(b, retry_failed=True), (["p"], ["p"]))

    def test_in_flight_is_skipped(self):
        old, run = build("succeeded", "1.0-1"), build("running", "2.0-1")
        self.assertEqual(self.run_stale({"p": {"latest": run, "latest_succeeded": old}}), ([], []))


if __name__ == "__main__":
    unittest.main()

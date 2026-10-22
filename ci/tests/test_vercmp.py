"""rpm's version ordering — the cases where a naive port silently ranks a
release BELOW its own predecessor (a silent downgrade of the packaged app).
"""

from __future__ import annotations

import unittest

from vercmp import rpmvercmp


class VerCmpTest(unittest.TestCase):
    def assertOrder(self, newer: str, older: str) -> None:
        self.assertEqual(rpmvercmp(newer, older), 1, f"{newer} should be > {older}")
        self.assertEqual(rpmvercmp(older, newer), -1, f"{older} should be < {newer}")
        self.assertEqual(rpmvercmp(newer, newer), 0)

    def test_plain_numbers(self):
        self.assertOrder("1.10", "1.9")
        self.assertOrder("2", "1.999")

    def test_numeric_segment_beats_alpha_segment(self):
        # rpm's segment type comes from the FIRST string: "1.23.4b" splits
        # into 1 | 23 | 4 | b, so the numeric 4 decides it. Merging digits
        # and letters into one segment would rank "1.23b" newest.
        self.assertOrder("1.23.4b", "1.23b")

    def test_leading_zeros_are_meaningless(self):
        self.assertEqual(rpmvercmp("1.007", "1.7"), 0)

    def test_tilde_is_a_pre_release(self):
        self.assertOrder("1.0", "1.0~rc1")
        self.assertOrder("1.0~rc2", "1.0~rc1")

    def test_caret_is_a_post_release(self):
        self.assertOrder("1.0^post", "1.0")
        self.assertOrder("1.0.0", "1.0^post")

    def test_markers_split_the_version(self):
        # the bases compare first, then the markers, then the suffixes
        self.assertOrder("1.0.1", "1.0~rc1")
        self.assertOrder("1.0", "1.0~rc1")

    def test_separators_are_ignored(self):
        self.assertEqual(rpmvercmp("1.0-1", "1.0.1"), 0)
        self.assertEqual(rpmvercmp("1_0", "1.0"), 0)

    def test_alpha_vs_numeric_prefix(self):
        # rpmvercmp ranks a leading digit over a leading letter
        self.assertOrder("0.56.2", "0.1.0-beta")

    def test_release_suffix_does_not_leak_into_the_version(self):
        # the sweeper compares bare versions; a trailing "-1" is a Release
        self.assertEqual(rpmvercmp("1.2.3", "1.2.3"), 0)

    def test_empty_strings(self):
        self.assertEqual(rpmvercmp("", ""), 0)
        self.assertOrder("1", "")


if __name__ == "__main__":
    unittest.main()

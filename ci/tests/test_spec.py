"""The sweeper's spec editing.

The dangerous half of this module is what it must NOT touch: a `Version:`
or `Release:` line that only appears in the %changelog is not the tag, and a
sweep that rewrites it corrupts the changelog instead of the package.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from spec import SpecError, SpecFile, preamble_end

BASE_SPEC = """\
%global             upstream_version 1.0.0
%global             digest abc123

Name:               demo
Version:            1.0.0
Release:            1%{?dist}
Summary:            A demo
License:            MIT
URL:                https://example.com
Source0:            https://example.com/demo-%{version}.tar.gz

%description
A demo package.

%prep
%autosetup -p1

%install
%make_install

%files
%{_bindir}/demo

%changelog
* Mon Jan 01 2024 halcyon-autoupdate - 1.0.0-1
- initial package
* Sun Dec 31 2023 halcyon-autoupdate - 0.9.0-1
- Version: 0.9.0
- Release: 1%{?dist}
"""


class SpecFileTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "demo.spec"
        self.path.write_text(BASE_SPEC)
        self.addCleanup(self.tmp.cleanup)

    def spec(self) -> SpecFile:
        return SpecFile(self.path)

    def test_preamble_ends_at_the_first_section(self):
        text = BASE_SPEC
        end = preamble_end(text)
        self.assertTrue(text[:end].rstrip().endswith("Source0:            https://example.com/demo-%{version}.tar.gz"))
        self.assertIn("%description", text[end:])

    def test_preamble_ignores_global_lines(self):
        # %global/%define are preamble directives, not sections
        text = "%global x 1\nName: a\n%define y 2\n%description\nd\n"
        self.assertEqual(preamble_end(text), text.index("%description"))

    def test_get_version_reads_the_tag(self):
        self.assertEqual(self.spec().get_version(), "1.0.0")

    def test_get_version_ignores_the_changelog(self):
        # the changelog mentions "Version: 0.9.0" — that is not the tag
        self.assertEqual(self.spec().get_version(), "1.0.0")

    def test_set_version_rewrites_the_tag_only(self):
        spec = self.spec()
        self.assertTrue(spec.set_version("2.0.0"))
        self.assertIn("Version:            2.0.0", spec.text)
        self.assertIn("- Version: 0.9.0", spec.text)  # the changelog is intact
        self.assertNotIn("Version:            1.0.0", spec.text)

    def test_set_version_resets_the_release(self):
        spec = self.spec()
        spec.text = spec.text.replace("Release:            1%{?dist}",
                                      "Release:            7%{?dist}")
        spec.set_version("2.0.0")
        self.assertIn("Release:            1%{?dist}", spec.text)

    def test_set_version_keeps_the_release_when_the_version_is_unchanged(self):
        spec = self.spec()
        spec.text = spec.text.replace("Release:            1%{?dist}",
                                      "Release:            7%{?dist}")
        self.assertFalse(spec.set_version("1.0.0"))
        self.assertIn("Release:            7%{?dist}", spec.text)

    def test_set_version_keeps_upstream_version_in_sync(self):
        spec = self.spec()
        spec.set_version("2.0.0")
        self.assertIn("%global             upstream_version 2.0.0", spec.text)

    def test_set_version_sanitizes_a_dash_to_a_tilde(self):
        spec = self.spec()
        spec.set_version("2026.9.1-beta.1")
        self.assertIn("Version:            2026.9.1~beta.1", spec.text)
        # the raw upstream string still reaches the Source URLs
        self.assertIn("%global             upstream_version 2026.9.1-beta.1",
                      spec.text)

    def test_set_version_strips_a_leading_v(self):
        spec = self.spec()
        spec.set_version("v3.1.4")
        self.assertIn("Version:            3.1.4", spec.text)

    def test_set_version_rejects_an_empty_version(self):
        with self.assertRaises(SpecError):
            self.spec().set_version("")

    def test_set_version_rejects_an_illegal_version(self):
        for bad in ("1.0 2", "1.0/2", "1.0:2"):
            with self.assertRaises(SpecError):
                self.spec().set_version(bad)

    def test_bump_release_keeps_the_dist_suffix(self):
        spec = self.spec()
        spec.text = spec.text.replace("Release:            1%{?dist}",
                                      "Release:            4%{?dist}")
        self.assertTrue(spec.bump_release())
        self.assertIn("Release:            5%{?dist}", spec.text)

    def test_bump_release_does_not_touch_the_changelog(self):
        spec = self.spec()
        spec.bump_release()
        self.assertIn("- Release: 1%{?dist}", spec.text)

    def test_bump_release_without_a_release_line_fails_loudly(self):
        spec = self.spec()
        spec.text = spec.text.replace("Release:            1%{?dist}", "")
        with self.assertRaises(SpecError):
            spec.bump_release()

    def test_save_writes_only_on_a_change(self):
        spec = self.spec()
        self.assertFalse(spec.save())
        spec.set_version("2.0.0")
        self.assertTrue(spec.save())
        self.assertIn("Version:            2.0.0", self.path.read_text())

    def test_get_global_reads_the_value(self):
        self.assertEqual(self.spec().get_global("digest"), "abc123")
        self.assertIsNone(self.spec().get_global("nosuch"))

    def test_set_global_rewrites_in_place(self):
        spec = self.spec()
        self.assertTrue(spec.set_global("digest", "def456"))
        self.assertIn("%global             digest def456", spec.text)

    def test_set_global_of_a_missing_macro_fails_loudly(self):
        with self.assertRaises(SpecError):
            self.spec().set_global("nosuch", "x")


if __name__ == "__main__":
    unittest.main()

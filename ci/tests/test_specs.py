"""The spec convention checker.

The comment rule is the interesting one: rpm expands `%{...}` and `%name`
inside comments too, so a `%global` in a comment is a hard parse error and
a `%{buildroot}` silently rewrites the comment into an absolute build path.
The checker has to know the difference between a macro and a directive.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import specs

GOOD_SPEC = """\
%global             debug_package %{nil}

Name:               demo
Version:            1.0.0
Release:            1%{?dist}
Summary:            A demo
License:            MIT
URL:                https://example.com
Source0:            https://example.com/demo-%{version}.tar.gz
Source1:            demo.desktop

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
"""


def violations_of(text: str, extra_files: tuple[str, ...] = ()) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        pkg = Path(tmp) / "demo"
        pkg.mkdir()
        (pkg / "demo.spec").write_text(text)
        for name in extra_files:
            (pkg / name).write_text("x\n")
        return specs.check_spec(pkg / "demo.spec")


class CommentRuleTest(unittest.TestCase):
    def flagged(self, comment: str) -> bool:
        return bool(specs.comment_macro_violations(f"# {comment}\n"))

    def test_an_escaped_macro_is_fine(self):
        self.assertFalse(self.flagged("write %%{buildroot} in a comment"))
        self.assertFalse(self.flagged("the %%prep section"))

    def test_a_macro_body_is_flagged(self):
        self.assertTrue(self.flagged("copy to %{buildroot}"))

    def test_a_defined_macro_is_flagged(self):
        self.assertTrue(self.flagged("%global debug_package %{nil}"))
        self.assertTrue(self.flagged("%define x 1"))
        self.assertTrue(self.flagged("%undefine x"))
        self.assertTrue(self.flagged("%autosetup -p1"))
        self.assertTrue(self.flagged("%configure"))

    def test_directives_are_fine(self):
        for directive in ("%prep", "%build", "%install", "%check", "%files",
                          "%changelog", "%description", "%setup"):
            self.assertFalse(self.flagged(f"the {directive} section"),
                             f"{directive} should be allowed in a comment")

    def test_a_bare_percent_is_fine(self):
        self.assertFalse(self.flagged("100% done"))
        self.assertFalse(self.flagged("50%% off"))

    def test_a_comment_is_reported_once(self):
        found = specs.comment_macro_violations(
            "# %{buildroot} and %{name} and %{_libdir}\n")
        self.assertEqual(len(found), 1)

    def test_a_code_line_is_not_a_comment(self):
        self.assertEqual(specs.comment_macro_violations("Source0: %{url}/x\n"), [])


class CheckSpecTest(unittest.TestCase):
    def test_a_good_spec_has_no_violations(self):
        self.assertEqual(violations_of(GOOD_SPEC, ("demo.desktop",)), [])

    def test_a_missing_release_is_flagged(self):
        text = GOOD_SPEC.replace("Release:            1%{?dist}\n", "")
        self.assertTrue(any("Release" in e for e in violations_of(text)))

    def test_a_release_without_the_dist_suffix_is_flagged(self):
        text = GOOD_SPEC.replace("Release:            1%{?dist}", "Release:            1")
        self.assertTrue(any("Release" in e for e in violations_of(text)))

    def test_a_missing_changelog_is_flagged(self):
        text = GOOD_SPEC.split("%changelog")[0]
        self.assertTrue(any("changelog" in e for e in violations_of(text)))

    def test_a_missing_debug_package_disable_is_flagged(self):
        text = GOOD_SPEC.replace("%global             debug_package %{nil}\n", "")
        self.assertTrue(any("debug_package" in e for e in violations_of(text)))

    def test_a_debuginfo_subpackage_is_flagged(self):
        text = GOOD_SPEC.replace(
            "%description", "%package -debuginfo\n%description -debuginfo\n\n%description")
        self.assertTrue(any("debug subpackage" in e for e in violations_of(text)))

    def test_a_local_source_must_exist(self):
        found = violations_of(GOOD_SPEC)  # demo.desktop is missing
        self.assertTrue(any("neither a URL" in e for e in found))

    def test_a_download_in_prep_is_flagged(self):
        text = GOOD_SPEC.replace(
            "%autosetup -p1", "curl -O https://example.com/x.tar.gz")
        self.assertTrue(any("%prep downloads" in e for e in violations_of(text)))

    def test_forgeautosetup_is_flagged(self):
        text = GOOD_SPEC.replace("%autosetup -p1", "%forgeautosetup")
        self.assertTrue(any("%forgeautosetup" in e for e in violations_of(text)))

    def test_an_illegal_version_is_flagged(self):
        text = GOOD_SPEC.replace("Version:            1.0.0", "Version:            1.0-1")
        self.assertTrue(any("illegal Version" in e for e in violations_of(text)))

    def test_autorelease_is_flagged(self):
        text = GOOD_SPEC.replace("Release:            1%{?dist}", "%autorelease")
        self.assertTrue(any("autorelease" in e for e in violations_of(text)))

    def test_a_mentioned_autorelease_in_a_comment_is_not(self):
        # the templates explain the rule in a comment — that is not a use
        text = GOOD_SPEC.replace(
            "%description", "# no rpmautospec here\n%description")
        self.assertFalse(any("autorelease" in e for e in violations_of(text)))


class MacroGlobalsTest(unittest.TestCase):
    def test_globals_are_collected(self):
        text = "%global full_name obsidian\n%define other 1\nName: x\n%description\n"
        globals_ = specs._macro_globals(text)
        self.assertEqual(globals_["full_name"], "obsidian")
        self.assertEqual(globals_["other"], "1")

    def test_a_local_source_resolves_through_a_global(self):
        text = GOOD_SPEC.replace("Source1:            demo.desktop",
                                  "Source1:            %{full_name}.desktop")
        text = text.replace("%global             debug_package %{nil}",
                            "%global             debug_package %{nil}\n"
                            "%global             full_name demo")
        found = violations_of(text, ("demo.desktop",))
        self.assertFalse(any("neither a URL" in e for e in found), found)


if __name__ == "__main__":
    unittest.main()

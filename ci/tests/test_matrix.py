"""The build-plan selection: the dependency graph that decides what a push
rebuilds, and the BuildRequires parsing it is built on.

A missed dependency here does not fail loudly — it ships a package built
against a stale dependency, which is exactly the failure the batch/wave
model exists to prevent.
"""

from __future__ import annotations

import contextlib
import io
import subprocess
import tempfile
import unittest
from pathlib import Path

import matrix


@contextlib.contextmanager
def quiet():
    """matrix.py narrates its decisions on stdout — the tests do not care."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        yield buf


class BrTokensTest(unittest.TestCase):
    def tokens(self, spec_text: str) -> tuple[list[str], bool]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.spec"
            path.write_text(spec_text)
            return matrix._br_tokens(path)

    def test_a_single_requirement(self):
        self.assertEqual(self.tokens("BuildRequires:  gcc\n"), (["gcc"], False))

    def test_every_name_on_the_line_is_collected(self):
        # the second name is a requirement too — dropping it would drop its
        # dependents from every rebuild
        tokens, conservative = self.tokens("BuildRequires:  foo-devel bar-devel\n")
        self.assertEqual(tokens, ["foo-devel", "bar-devel"])
        self.assertFalse(conservative)

    def test_a_version_constraint_stops_the_name_run(self):
        tokens, _ = self.tokens("BuildRequires:  foo >= 1.2\n")
        self.assertEqual(tokens, ["foo"])

    def test_a_constraint_between_two_names(self):
        tokens, _ = self.tokens("BuildRequires:  foo >= 1.2 bar-devel\n")
        self.assertEqual(tokens, ["foo", "bar-devel"])

    def test_the_isa_suffix_is_stripped(self):
        tokens, _ = self.tokens("BuildRequires:  qt6-qtbase-devel%{?_isa}\n")
        self.assertEqual(tokens, ["qt6-qtbase-devel"])

    def test_a_macro_wrapped_name_makes_the_spec_conservative(self):
        tokens, conservative = self.tokens("BuildRequires:  %{?foo}\n")
        self.assertEqual(tokens, [])
        self.assertTrue(conservative)

    def test_requirements_in_a_subpackage_section_are_seen_too(self):
        # a subpackage's BuildRequires is still a build input
        tokens, _ = self.tokens(
            "%package kitten\nBuildRequires:  foo-devel\n"
        )
        self.assertEqual(tokens, ["foo-devel"])

    def test_requires_lines_are_not_buildrequires(self):
        tokens, _ = self.tokens("Requires:  foo\n")
        self.assertEqual(tokens, [])


class ResolveTokenTest(unittest.TestCase):
    def test_plain_name(self):
        registry = {"kitty": "kitty"}
        self.assertEqual(matrix._resolve_token("kitty", registry), "kitty")

    def test_pkgconfig_wrapper(self):
        registry = {"hyprland": "hyprland"}
        self.assertEqual(matrix._resolve_token("pkgconfig(hyprland)", registry),
                         "hyprland")

    def test_cmake_wrapper(self):
        registry = {"hyprland": "hyprland"}
        self.assertEqual(matrix._resolve_token("cmake(hyprland)", registry),
                         "hyprland")

    def test_devel_suffix(self):
        registry = {"hyprland": "hyprland"}
        self.assertEqual(matrix._resolve_token("hyprland-devel", registry),
                         "hyprland")

    def test_unknown_token(self):
        self.assertIsNone(matrix._resolve_token("glibc", {"kitty": "kitty"}))


class ClosureTest(unittest.TestCase):
    def packages(self):
        return {
            "a": {"batch": 0, "brs": [], "conservative": False},
            "b": {"batch": 1, "brs": ["a"], "conservative": False},
            "c": {"batch": 2, "brs": ["b"], "conservative": False},
            "d": {"batch": 0, "brs": [], "conservative": False},
        }

    def test_dependents_follow_the_chain(self):
        pkgs = self.packages()
        self.assertEqual(matrix.dependents_closure(pkgs, {"a"}), {"a", "b", "c"})

    def test_a_leaf_change_does_not_pull_in_the_others(self):
        pkgs = self.packages()
        self.assertEqual(matrix.dependents_closure(pkgs, {"c"}), {"c"})

    def test_a_conservative_spec_is_seeded_on_a_lower_batch_change(self):
        pkgs = self.packages()
        pkgs["c"]["conservative"] = True
        # changing "a" (batch 0) seeds the conservative "c" (batch 2)
        self.assertEqual(matrix.dependents_closure(pkgs, {"a"}), {"a", "b", "c"})

    def test_a_conservative_spec_is_not_seeded_by_a_higher_batch_change(self):
        pkgs = self.packages()
        pkgs["c"]["conservative"] = True
        # changing "c" itself must not pull in anything else
        self.assertEqual(matrix.dependents_closure(pkgs, {"c"}), {"c"})


class SelectSinceTest(unittest.TestCase):
    """select_since reads the git history — a throwaway repository stands in
    for the real one."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        (self.repo / "ci").mkdir()
        (self.repo / "pkgs" / "a").mkdir(parents=True)
        (self.repo / "pkgs" / "b").mkdir(parents=True)
        (self.repo / "ci" / "packages.toml").write_text(
            '[a]\nbatch = 0\n\n[a.updates]\nfeed = "custom"\ncustom = "a"\n\n'
            '[b]\nbatch = 1\n\n[b.updates]\nfeed = "custom"\ncustom = "b"\n'
        )
        (self.repo / "pkgs" / "a" / "a.spec").write_text(
            "Name: a\nVersion: 1\nRelease: 1%{?dist}\n"
        )
        (self.repo / "pkgs" / "b" / "b.spec").write_text(
            "Name: b\nVersion: 1\nRelease: 1%{?dist}\nBuildRequires: a\n"
        )
        self.git("init", "-q")
        self.git("add", "-A")
        self.git("commit", "-qm", "initial")
        self.base = self.git("rev-parse", "HEAD").stdout.strip()
        self._orig_root = matrix.REPO_ROOT
        self._orig_file = matrix.PACKAGES_FILE
        matrix.REPO_ROOT = self.repo
        matrix.PACKAGES_FILE = self.repo / "ci" / "packages.toml"
        self.addCleanup(self._restore)

    def _restore(self):
        matrix.REPO_ROOT = self._orig_root
        matrix.PACKAGES_FILE = self._orig_file

    def git(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(self.repo),
             "-c", "user.name=halcyon-tests",
             "-c", "user.email=tests@example.com",
             "-c", "commit.gpgsign=false",
             "-c", "init.defaultBranch=main",
             *args],
            check=True, capture_output=True, text=True,
        )

    def commit(self, path: str, text: str, message: str = "change") -> None:
        (self.repo / path).write_text(text)
        self.git("add", "-A")
        self.git("commit", "-qm", message)

    def test_a_package_change_selects_its_dependents(self):
        self.commit("pkgs/a/a.spec", "Name: a\nVersion: 2\nRelease: 1%{?dist}\n")
        pkgs = matrix.load_packages()
        with quiet():
            self.assertEqual(matrix.select_since(pkgs, self.base), {"a", "b"})

    def test_an_infrastructure_change_selects_everything(self):
        self.commit("ci/matrix.py", "# changed\n")
        pkgs = matrix.load_packages()
        with quiet():
            self.assertEqual(matrix.select_since(pkgs, self.base), {"a", "b"})

    def test_a_docs_change_selects_nothing(self):
        # a README commit is not a build input — rebuilding the whole
        # registry for it would burn build-farm time for no new bits
        self.commit("README.md", "docs\n")
        pkgs = matrix.load_packages()
        with quiet():
            self.assertEqual(matrix.select_since(pkgs, self.base), set())

    def test_no_change_selects_nothing(self):
        pkgs = matrix.load_packages()
        with quiet():
            self.assertEqual(matrix.select_since(pkgs, self.base), set())

    def test_an_unknown_revision_is_an_error(self):
        pkgs = matrix.load_packages()
        with quiet(), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                matrix.select_since(pkgs, "nosuchrev")


class BatchValidationTest(unittest.TestCase):
    def test_a_batch_violation_is_rejected(self):
        pkgs = {
            "a": {"batch": 0, "brs": [], "conservative": False},
            "b": {"batch": 0, "brs": ["a"], "conservative": False},
        }
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                matrix._validate_batches(pkgs)

    def test_a_valid_batch_order_passes(self):
        pkgs = {
            "a": {"batch": 0, "brs": [], "conservative": False},
            "b": {"batch": 1, "brs": ["a"], "conservative": False},
        }
        matrix._validate_batches(pkgs)


if __name__ == "__main__":
    unittest.main()

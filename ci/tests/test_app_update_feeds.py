from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from feeds import FeedError
from custom import (
    custom_antigravity_cli,
    custom_antigravity_desktop,
    custom_antigravity_ide,
    custom_openwork,
    custom_podman_desktop,
    custom_windscribe,
    custom_zcode,
)
from spec import SpecFile


SPEC_TEXT = """\
%global digest none
%global build_id none
%global cli_build none
Name:           example
Version:        0.0.0
Release:        1%{?dist}
Summary:        Example
License:        MIT
URL:            https://example.com
Source0:        https://example.com/%{version}
%description
Example.
"""


class AppUpdateFeedsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "example.spec"
        self.path.write_text(SPEC_TEXT)

    def spec(self) -> SpecFile:
        return SpecFile(self.path)

    def test_antigravity_desktop_tracks_only_the_official_x64_archive(self):
        page = """
        x64: https://storage.googleapis.com/antigravity-public/antigravity-hub/2.35.2-4585983447007232/linux-x64/Antigravity.tar.gz
        arm: https://storage.googleapis.com/antigravity-public/antigravity-hub/2.35.2-4585983447007232/linux-arm/Antigravity.tar.gz
        CLI: https://storage.googleapis.com/antigravity-public/antigravity-cli/1.5.13-5999302598852608/linux-x64/cli_linux_x64.tar.gz
        """
        spec = self.spec()
        with patch("custom.feeds.fetch_text", return_value=page):
            custom_antigravity_desktop(spec, Path(self.tmp.name))
        self.assertEqual(spec.get_version(), "2.35.2")
        self.assertEqual(spec.get_global("build_id"), "4585983447007232")

    def test_antigravity_desktop_rejects_missing_or_ambiguous_x64_archive(self):
        spec = self.spec()
        original = spec.text
        with patch("custom.feeds.fetch_text", return_value="no x64 release"):
            with self.assertRaisesRegex(FeedError, "expected one official x64 archive"):
                custom_antigravity_desktop(spec, Path(self.tmp.name))
        self.assertEqual(spec.text, original)

        archive = (
            "https://storage.googleapis.com/antigravity-public/antigravity-hub/"
            "2.35.2-4585983447007232/linux-x64/Antigravity.tar.gz"
        )
        with patch("custom.feeds.fetch_text", return_value=f"{archive}\n{archive}"):
            with self.assertRaisesRegex(FeedError, "expected one official x64 archive"):
                custom_antigravity_desktop(spec, Path(self.tmp.name))
        self.assertEqual(spec.text, original)

    def test_antigravity_cli_tracks_aur_version_and_build_id(self):
        spec = self.spec()
        with patch("custom.feeds.fetch_json", return_value={
            "results": [{"Version": "1.5.17_4823843970351104-1"}],
        }):
            custom_antigravity_cli(spec, Path(self.tmp.name))
        self.assertEqual(spec.get_version(), "1.5.17")
        self.assertEqual(spec.get_global("cli_build"), "4823843970351104")

    def test_antigravity_cli_rejects_unexpected_aur_version_without_mutation(self):
        spec = self.spec()
        original = spec.text
        with patch("custom.feeds.fetch_json", return_value={
            "results": [{"Version": "1.5.17"}],
        }):
            with self.assertRaisesRegex(FeedError, "unexpected AUR pkgver"):
                custom_antigravity_cli(spec, Path(self.tmp.name))
        self.assertEqual(spec.text, original)

    def test_antigravity_ide_deduplicates_links_and_selects_x64(self):
        url = ("https://edgedl.me.gvt1.com/edgedl/release2/j0qc3/antigravity/stable/"
               "2.9.0-4671306730438656/linux-x64/Antigravity%20IDE.tar.gz")
        spec = self.spec()
        page = "\n".join([url, url, url.replace("linux-x64", "linux-arm"),
                          url.replace("Antigravity%20IDE", "Antigravity")])
        with patch("custom.feeds.fetch_text", return_value=page):
            custom_antigravity_ide(spec, Path(self.tmp.name))
        self.assertEqual(spec.get_version(), "2.9.0")
        self.assertEqual(spec.get_global("build_id"), "4671306730438656")

    def test_antigravity_ide_rejects_missing_conflicting_and_stale_links(self):
        url = ("https://dl.google.com/release2/j0qc3/antigravity/stable/"
               "2.9.0-4671306730438656/linux-x64/Antigravity%20IDE.tar.gz")
        for page in ("missing", url + "\n" + url.replace("2.9.0-", "2.10.0-"),
                     url.replace("2.9.0-", "2.8.0-")):
            with self.subTest(page=page):
                spec = self.spec()
                spec.set_version("2.9.0")
                original = spec.text
                with patch("custom.feeds.fetch_text", return_value=page):
                    with self.assertRaises(FeedError):
                        custom_antigravity_ide(spec, Path(self.tmp.name))
                self.assertEqual(spec.text, original)

    def test_antigravity_ide_build_id_change_bumps_release(self):
        from sweep import prepare_spec

        spec = self.spec()
        spec.set_version("2.9.0")
        self.path.write_text(spec.text)
        spec = self.spec()
        url = ("https://dl.google.com/release2/j0qc3/antigravity/stable/"
               "2.9.0-4671306730438656/linux-x64/Antigravity%20IDE.tar.gz")
        with patch("custom.feeds.fetch_text", return_value=url):
            prepare_spec("antigravity-ide", {"feed": "custom", "custom": "antigravity_ide"},
                         spec, Path(self.tmp.name))
        self.assertIn("Release:        2%{?dist}", spec.text)
        self.assertEqual(spec.get_global("build_id"), "4671306730438656")

    def test_openwork_tracks_stable_x64_archive_and_digest(self):
        release = {
            "tag_name": "v0.18.65",
            "draft": False,
            "prerelease": False,
            "assets": [{
                "name": "openwork-linux-x64-0.18.65.tar.gz",
                "digest": "sha256:" + "a" * 64,
            }],
        }
        spec = self.spec()
        with patch("custom.feeds.fetch_json", return_value=[release]):
            custom_openwork(spec, Path(self.tmp.name))
        self.assertEqual(spec.get_version(), "0.18.65")
        self.assertEqual(spec.get_global("digest"), "a" * 64)

    def test_podman_desktop_tracks_stable_x64_archive_and_digest(self):
        release = {
            "tag_name": "v1.30.5",
            "draft": False,
            "prerelease": False,
            "assets": [{
                "name": "podman-desktop-1.30.5-x64.tar.gz",
                "digest": "sha256:" + "b" * 64,
            }],
        }
        spec = self.spec()
        with patch("custom.feeds.fetch_json", return_value=[release]):
            custom_podman_desktop(spec, Path(self.tmp.name))
        self.assertEqual(spec.get_version(), "1.30.5")
        self.assertEqual(spec.get_global("digest"), "b" * 64)

    def test_zcode_requires_published_official_rpm(self):
        with patch("custom.feeds.github_release_tag", return_value="v3.17.2"), \
                patch("custom.feeds.head_probe", return_value=True) as probe:
            spec = self.spec()
            custom_zcode(spec, Path(self.tmp.name))
        self.assertEqual(spec.get_version(), "3.17.2")
        probe.assert_called_once_with(
            "https://cdn-zcode.z.ai/zcode/electron/releases/3.17.2/"
            "linux-x64/ZCode-3.17.2-linux-x64.rpm"
        )

    def test_windscribe_tracks_latest_stable_fedora_gui_rpm_and_digest(self):
        releases = [
            {
                "tag_name": "v2.25.7",
                "draft": False,
                "prerelease": True,
                "assets": [{
                    "name": "windscribe_2.25.7_beta_amd64_fedora.rpm",
                    "digest": "sha256:" + "b" * 64,
                }],
            },
            {
                "tag_name": "v2.24.13",
                "draft": False,
                "prerelease": False,
                "assets": [{
                    "name": "windscribe_2.24.13_amd64_fedora.rpm",
                    "digest": "sha256:" + "c" * 64,
                }],
            },
        ]
        spec = self.spec()
        with patch("custom.feeds.fetch_json", return_value=releases):
            custom_windscribe(spec, Path(self.tmp.name))
        self.assertEqual(spec.get_version(), "2.24.13")
        self.assertEqual(spec.get_global("digest"), "c" * 64)

if __name__ == "__main__":
    unittest.main()

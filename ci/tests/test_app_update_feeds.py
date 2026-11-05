from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from custom import (
    custom_openwork,
    custom_podman_desktop,
    custom_windscribe,
    custom_zcode,
)
from spec import SpecFile


SPEC_TEXT = """\
%global digest none
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

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sweep
from feeds import FeedError


SPEC = "%global upstream_sha256 " + "a" * 64 + "\nName: demo\nVersion: 1.0.0\nRelease: 1%{?dist}\n%description\ndemo\n"


class GhosttyPairTest(unittest.TestCase):
    def test_no_op_sweep_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = {name: root / f"{name}.spec" for name in ("zig017", "ghostty")}
            for path in paths.values():
                path.write_text(SPEC)
            swept = {name: ({"feed": "custom", "custom": name}, path, root) for name, path in paths.items()}
            with patch.object(sweep.custom_feeds, "custom_zig017", lambda spec, base: None), \
                    patch.object(sweep.custom_feeds, "custom_ghostty", lambda spec, base: None):
                results = sweep.sweep_ghostty_pair(swept)
            self.assertFalse(any(wrote for _, wrote, _, _ in results))

    def test_checksum_only_change_bumps_release(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "zig017.spec"
            path.write_text(SPEC)
            def update(spec, base):
                spec.set_global("upstream_sha256", "b" * 64)
            with patch.object(sweep.custom_feeds, "custom_zig017", update):
                wrote, old, new = sweep.sweep_one("zig017", {"feed": "custom", "custom": "zig017"}, path, Path(tmp))
            self.assertTrue(wrote)
            self.assertEqual((old, new), ("1.0.0", "1.0.0"))
            self.assertIn("Release: 2%{?dist}", path.read_text())

    def test_feed_failure_does_not_write_either_spec(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = {name: root / f"{name}.spec" for name in ("zig017", "ghostty")}
            for path in paths.values():
                path.write_text(SPEC)
            swept = {
                name: ({"feed": "custom", "custom": name}, path, root)
                for name, path in paths.items()
            }

            def update_ghostty(spec, base):
                spec.set_version("1.1.0")
                raise FeedError("missing matching Zig archive")

            with patch.object(sweep.custom_feeds, "custom_zig017", lambda spec, base: spec.set_version("1.1.0")), \
                    patch.object(sweep.custom_feeds, "custom_ghostty", update_ghostty):
                with self.assertRaises(FeedError):
                    sweep.sweep_ghostty_pair(swept)
            for path in paths.values():
                self.assertEqual(path.read_text(), SPEC)


if __name__ == "__main__":
    unittest.main()

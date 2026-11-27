from __future__ import annotations

import json
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXTRACTOR = ROOT / "pkgs/antigravity/extract-icon.py"
PNG = b"\x89PNG\r\n\x1a\nicon data"


def make_asar(icon: bytes) -> bytes:
    manifest = json.dumps({
        "files": {"icon.png": {"size": len(icon), "offset": "0"}}
    }).encode()
    padded_manifest = manifest + b"\0" * (-len(manifest) % 4)
    pickle_size = 4 + len(padded_manifest)
    header_size = 4 + pickle_size
    return (struct.pack("<IIII", 4, header_size, pickle_size, len(manifest))
            + padded_manifest + icon)


class AntigravityIconTest(unittest.TestCase):
    def test_extracts_icon_from_asar(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "app.asar"
            output = Path(tmp) / "antigravity.png"
            archive.write_bytes(make_asar(PNG))
            subprocess.run(
                [sys.executable, str(EXTRACTOR), str(archive), str(output)],
                check=True,
            )
            self.assertEqual(output.read_bytes(), PNG)

    def test_rejects_missing_icon(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "app.asar"
            output = Path(tmp) / "antigravity.png"
            manifest = json.dumps({"files": {}}).encode()
            padded = manifest + b"\0" * (-len(manifest) % 4)
            pickle_size = 4 + len(padded)
            archive.write_bytes(
                struct.pack("<IIII", 4, 4 + pickle_size, pickle_size, len(manifest)) + padded
            )
            result = subprocess.run(
                [sys.executable, str(EXTRACTOR), str(archive), str(output)],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("icon.png not found", result.stderr)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()

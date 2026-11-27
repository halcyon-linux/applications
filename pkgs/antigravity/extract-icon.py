#!/usr/bin/python3
"""Extract the Hub app's icon.png from Electron's app.asar archive."""

import json
import struct
import sys
from pathlib import Path


def extract_icon(archive: Path, output: Path) -> None:
    with archive.open("rb") as source:
        source.seek(4)
        header_size_raw = source.read(4)
        source.seek(12)
        json_size_raw = source.read(4)
        if len(header_size_raw) != 4 or len(json_size_raw) != 4:
            raise ValueError("truncated ASAR header")
        header_size = struct.unpack("<I", header_size_raw)[0]
        json_size = struct.unpack("<I", json_size_raw)[0]
        if json_size > header_size - 8:
            raise ValueError("invalid ASAR header size")
        header_raw = source.read(json_size)
        if len(header_raw) != json_size:
            raise ValueError("truncated ASAR manifest")
        header = json.loads(header_raw)
        entry = header.get("files", {}).get("icon.png")
        if not isinstance(entry, dict):
            raise ValueError("icon.png not found in app.asar")
        offset, size = int(entry["offset"]), int(entry["size"])
        if offset < 0 or size <= 0:
            raise ValueError("invalid icon.png entry in app.asar")
        payload_start = 8 + header_size
        source.seek(0, 2)
        if payload_start + offset + size > source.tell():
            raise ValueError("icon.png entry extends past the end of app.asar")
        source.seek(payload_start + offset)
        icon = source.read(size)
        if len(icon) != size or not icon.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("icon.png payload is missing or is not a PNG")
    output.write_bytes(icon)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(f"usage: {sys.argv[0]} APP_ASAR OUTPUT_PNG")
    try:
        extract_icon(Path(sys.argv[1]), Path(sys.argv[2]))
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"icon extraction failed: {exc}") from exc

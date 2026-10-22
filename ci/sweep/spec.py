"""Spec text editing for the version sweeper — the Python port of andax's
`rpm.version()` / `rpm.global()` with byte-identical output semantics
(verified against `anda update` on the real specs, 2026-09-25):

- line whitespace before the value is preserved on every rewrite;
- rpm.version() resets Release to `1%{?dist}` ONLY when the version actually
  changes (a no-op sweep never touches a hand-bumped Release);
- %changelog is never touched;
- the file is written only when the content actually changed.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

_VALUE = r"[^\s]+"  # spec preamble values are single tokens (no spaces)


class SpecError(Exception):
    pass


class SpecFile:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.text = self.path.read_text()
        self._original = self.text

    def save(self) -> bool:
        """Write back only when the content actually changed (anda's rule)."""
        if self.text == self._original:
            return False
        self.path.write_text(self.text)
        return True

    # ---- Version / Release -------------------------------------------------

    def get_version(self) -> str:
        m = re.search(rf"(?m)^Version:[ \t]*({_VALUE})", self.text)
        if not m:
            raise SpecError(f"{self.path}: no Version: line")
        val = m.group(1)
        if val.startswith("%"):
            try:
                proc = subprocess.run(
                    ["rpmspec", "-D", "fedora 44", "-q", "--qf", "%{version}\\n", str(self.path)],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                first_line = proc.stdout.strip().splitlines()
                if first_line:
                    return first_line[0].strip()
            except Exception:
                pass
        return val

    def is_changed(self) -> bool:
        """True when the in-memory text differs from the file on disk."""
        return self.text != self._original

    def bump_release(self) -> bool:
        """Increment the Release number, keeping the dist suffix.

        rpm's version() resets Release to 1 when the Version changes; a
        sweep that changes anything ELSE (a pinned upstream build id, a
        checksum) without changing the Version must still move the Release.
        Otherwise the rebuilt RPM carries the NVR of the one already
        published and `dnf upgrade` skips it — the update is silently lost.
        """
        m = re.search(r"(?m)^(Release:[ \t]*)([0-9]+)(\S*)$", self.text)
        if not m:
            raise SpecError(f"{self.path}: no Release: line to bump")
        bumped = f"{m.group(1)}{int(m.group(2)) + 1}{m.group(3)}"
        self.text = re.sub(
            r"(?m)^Release:[ \t]*\S+$", lambda _: bumped, self.text, count=1
        )
        return True

    def set_version(self, version: str, reset_release: bool = True) -> bool:
        """rpm.version() port: strip a leading `v`, rewrite the Version value,
        reset Release to 1%{?dist} — only when the version really changes.
        Returns whether anything was rewritten.

        RPM Version forbids '-' (the Version/Release separator); upstream
        pre-release tags (bitwarden's 2026.9.1-beta.1) are sanitized to tilde
        form, which vercmp orders as pre-release. A spec that defines an
        %global upstream_version opts in to carrying the RAW upstream string
        (Source URLs usually need it) — it is kept in sync here."""
        version = version.removeprefix("v")
        if not version:
            raise SpecError(f"{self.path}: refusing to set an empty Version")
        if self.get_global("upstream_version") is not None:
            self.set_global("upstream_version", version)
        version = version.replace("-", "~")
        if version == self.get_version():
            return False
        text = re.sub(
            rf"(?m)^(Version:[ \t]*){_VALUE}",
            lambda m: m.group(1) + version,
            self.text,
            count=1,
        )
        if reset_release:
            text = re.sub(
                rf"(?m)^(Release:[ \t]*){_VALUE}",
                lambda m: m.group(1) + "1%{?dist}",
                text,
                count=1,
            )
        self.text = text
        return True

    # ---- %global macros ----------------------------------------------------

    def get_global(self, name: str) -> str | None:
        m = re.search(
            rf"(?m)^%global[ \t]+{re.escape(name)}[ \t]+([^\n]+)$", self.text
        )
        return m.group(1).strip() if m else None

    def set_global(self, name: str, value: str) -> bool:
        """rpm.global() port: rewrite the `%global <name> <value>` line in
        place, preserving the whitespace columns. Returns whether the value
        actually changed."""
        pattern = rf"(?m)^%global([ \t]+){re.escape(name)}([ \t]+)[^\n]*$"
        if not re.search(pattern, self.text):
            raise SpecError(f"{self.path}: no %%global {name} line to rewrite")
        new_text = re.sub(
            pattern,
            lambda m: f"%global{m.group(1)}{name}{m.group(2)}{value}",
            self.text,
            count=1,
        )
        changed = new_text != self.text
        self.text = new_text
        return changed

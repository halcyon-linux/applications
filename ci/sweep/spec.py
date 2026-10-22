"""Spec text editing for the version sweeper — the Python port of andax's
`rpm.version()` / `rpm.global()` with byte-identical output semantics
(verified against `anda update` on the real specs, 2026-09-25):

- line whitespace before the value is preserved on every rewrite;
- rpm.version() resets Release to `1%{?dist}` ONLY when the version actually
  changes (a no-op sweep never touches a hand-bumped Release);
- %changelog is never touched;
- the file is written only when the content actually changed.

Every rewrite is scoped to the SPEC PREAMBLE (the tag block before the first
section directive). rpm expands `%{...}` and `%name` inside comments too, so a
`Version:`/`Release:` line that only ever appears in a %changelog entry must
not be picked up by the sweeper — the preamble scope makes that impossible
rather than merely unlikely.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

_VALUE = r"[^\s]+"  # spec preamble values are single tokens (no spaces)

# The preamble ends at the first section directive. %global/%define/%undefine
# are preamble directives, not sections, so they do not end it.
_SECTION_RE = re.compile(
    r"(?m)^%(description|prep|build|install|check|clean|files|changelog|"
    r"package|pre|post|preun|postun|pretrans|posttrans|sepolicy|triggerin|"
    r"triggerpostun|triggerpreun|defattr|attr|include|generate_buildrequires)\b"
)

# A legal RPM Version: alphanumerics and the separators rpm accepts. The '-'
# is forbidden — it separates Version from Release — and whitespace would
# silently truncate the value. Shared with ci/specs.py, which enforces the
# same rule on the specs as they are written.
VERSION_RE = re.compile(r"^[A-Za-z0-9._+~^]+$")


class SpecError(Exception):
    pass


def preamble_end(text: str) -> int:
    """Offset of the first section directive — the end of the preamble.

    Everything the sweeper rewrites (Version, Release, %global) lives before
    it; everything after it is a section body or the changelog, which the
    sweeper must never touch.
    """
    m = _SECTION_RE.search(text)
    return m.start() if m else len(text)


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
        m = re.search(rf"(?m)^Version:[ \t]*({_VALUE})", self._preamble())
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

    def _release_match(self) -> re.Match:
        """The preamble's Release: line.

        Scoped to the preamble so a `Release:` inside a %changelog entry is
        never the one that gets bumped, and matched with ONE pattern so the
        value that is read is exactly the value that is rewritten.
        """
        m = re.search(r"(?m)^(Release:[ \t]*)([0-9]+)(\S*)$", self._preamble())
        if not m:
            raise SpecError(f"{self.path}: no Release: line")
        return m

    def _set_release(self, value: str) -> None:
        """Rewrite the preamble's Release: line, keeping the column layout.

        The rewrite is confined to the preamble span, so a `Release:` inside
        a %changelog entry can never be the line that changes — the same
        rule the match in _release_match() follows."""
        m = self._release_match()
        bumped = f"{m.group(1)}{value}{m.group(3)}"
        end = preamble_end(self.text)
        head, tail = self.text[:end], self.text[end:]
        head = re.sub(
            r"(?m)^(Release:[ \t]*)\S+$", lambda _: bumped, head, count=1
        )
        self.text = head + tail

    def bump_release(self) -> bool:
        """Increment the Release number, keeping the dist suffix.

        rpm's version() resets Release to 1 when the Version changes; a
        sweep that changes anything ELSE (a pinned upstream build id, a
        checksum) without changing the Version must still move the Release.
        Otherwise the rebuilt RPM carries the NVR of the one already
        published and `dnf upgrade` skips it — the update is silently lost.
        """
        m = self._release_match()
        self._set_release(str(int(m.group(2)) + 1))
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
        # '-' is illegal in an RPM Version but common in an upstream tag
        # (bitwarden's 2026.9.1-beta.1): it becomes '~', which vercmp
        # orders as a pre-release. The validation runs on the SANITIZED
        # value, so a raw tag with a dash is accepted.
        sanitized = version.replace("-", "~")
        if not VERSION_RE.match(sanitized):
            raise SpecError(
                f"{self.path}: refusing to set an illegal Version {version!r} "
                f"(rpm versions allow letters, digits and . _ + ~ ^ only)"
            )
        if self.get_global("upstream_version") is not None:
            self.set_global("upstream_version", version)
        if sanitized == self.get_version():
            return False
        end = preamble_end(self.text)
        head, tail = self.text[:end], self.text[end:]
        head = re.sub(
            rf"(?m)^(Version:[ \t]*){_VALUE}",
            lambda m: m.group(1) + sanitized,
            head,
            count=1,
        )
        text = head + tail
        if reset_release:
            end = preamble_end(text)
            head, tail = text[:end], text[end:]
            head = re.sub(
                r"(?m)^(Release:[ \t]*)\S+$",
                lambda m: m.group(1) + "1%{?dist}",
                head,
                count=1,
            )
            text = head + tail
        self.text = text
        return True

    # ---- %global macros ----------------------------------------------------

    def _preamble(self) -> str:
        """The spec preamble: the tag block before the first section."""
        return self.text[: preamble_end(self.text)]

    def get_global(self, name: str) -> str | None:
        m = re.search(
            rf"(?m)^%global[ \t]+{re.escape(name)}[ \t]+([^\n]+)$", self._preamble()
        )
        return m.group(1).strip() if m else None

    def set_global(self, name: str, value: str) -> bool:
        """rpm.global() port: rewrite the `%global <name> <value>` line in
        place, preserving the whitespace columns. Returns whether the value
        actually changed."""
        pattern = rf"(?m)^%global([ \t]+){re.escape(name)}([ \t]+)[^\n]*$"
        if not re.search(pattern, self._preamble()):
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

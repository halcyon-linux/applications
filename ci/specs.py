#!/usr/bin/env python3
"""ci/specs.py - the spec convention checker.

Every rule here mirrors a convention written down in AGENTS.md. The point of
the checker is to make those conventions MECHANICAL: a spec that breaks one
fails the validate job (seconds) instead of the Copr build (minutes, on the
shared build farm) — or, worse, a consumer's `dnf upgrade`.

    ci/specs.py [--check] [PKG...]

`--check` is the offline mode the validate job runs; with no arguments it
checks every registered package. Without --check the violations are printed
the same way, so the script is usable as a plain linter.

The rules:

  preamble     Name/Version/Release/Summary/License/URL are present, the
               Release is an explicit `N%{?dist}`, no %autorelease, and the
               spec carries a written %changelog.
  version      the Version is a legal rpm version (no whitespace, no '-',
               which separates Version from Release).
  debug        the debug package is disabled (`debug_package %{nil}`) and no
               debuginfo/debugsource subpackage is declared — nothing in the
               halcyon image consumes debug packages.
  comments     no macro text in comments. rpm expands `%{...}` and `%name`
               inside comments too: a `%global`/`%define` there is a HARD
               parse error, `%autosetup`/`%configure` are hard parse errors
               as well, and anything else silently rewrites the comment (the
               packaged spec then carries an expanded build path). `%%` is
               the escape.
  sources      every Source*/Patch* is a full URL (the submit job's
               `spectool -g` fetches it) or a file that exists in the
               package directory.
  prep         %prep does not download anything (the sources are fetched at
               SRPM-build time).
  files        the spec has a %files section.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGES_FILE = REPO_ROOT / "ci" / "packages.toml"
TEMPLATE_DIR = REPO_ROOT / "templates"

sys.path.insert(0, os.path.join(str(REPO_ROOT), "ci", "sweep"))

from spec import VERSION_RE, preamble_end  # noqa: E402

# rpm directives that are never expanded as macros — mentioning them in a
# comment is harmless ("keep the downloads out of %prep"). Every OTHER
# `%name` form is a macro rpm expands (or rejects).
SAFE_DIRECTIVES = frozenset({
    "attr", "brp", "build", "cargo", "changelog", "check", "cmake", "clean",
    "cmake_install", "description", "doc", "files", "glib2_post", "icon_theme_cache",
    "install", "ldconfig", "meson", "meson_build", "meson_install",
    "package", "patch", "post", "posttrans", "pre", "prep", "pretrans", "preun",
    "postun", "pyproject_buildrequires", "pyproject_files", "pyproject_install",
    "pyproject_save_files", "pyproject_wheel", "sepolicy", "setup", "systemd_post",
    "systemd_postun", "systemd_postun_with_restart", "systemd_preun",
    "triggerin", "triggerpostun", "triggerpreun",
})

# The preamble tags rpm (and this repo) require.
REQUIRED_TAGS = ("Name", "Version", "Release", "Summary", "License", "URL")

# Anything that reaches out to the network from inside %prep.
_NETWORK = re.compile(
    r"(?m)^\s*(curl|wget|git\s+clone|git\s+fetch|svn\s+checkout|aria2c)\b"
)


def die(msg: str) -> None:
    print(f"specs.py: error: {msg}", file=sys.stderr)
    raise SystemExit(1)


def registered_packages() -> list[str]:
    with open(PACKAGES_FILE, "rb") as fh:
        data = tomllib.load(fh)
    return sorted(data)


def spec_path_for(name: str) -> Path:
    return REPO_ROOT / "pkgs" / name / f"{name}.spec"


def _macro_globals(spec_text: str) -> dict[str, str]:
    """The spec's own %global/%define values — enough to resolve the
    `%{full_name}.sh` shape a local Source entry uses."""
    values: dict[str, str] = {}
    head = spec_text[: preamble_end(spec_text)]
    for m in re.finditer(
        r"(?m)^%(?:global|define)[ \t]+([A-Za-z_][A-Za-z0-9_]*)[ \t]+([^\n]*)$", head
    ):
        values.setdefault(m.group(1), m.group(2).strip())
    return values


def _expand_local(value: str, globals_: dict[str, str]) -> str:
    """Resolve `%{name}` from the spec's own globals (one pass)."""
    def repl(m: re.Match) -> str:
        return globals_.get(m.group(1), m.group(0))

    return re.sub(r"%\{([A-Za-z_][A-Za-z0-9_]*)\}", repl, value)


def _is_placeholder(value: str) -> bool:
    """Template placeholders (`<pkg>`) are not real values."""
    return value.startswith("<") and value.endswith(">")


def comment_macro_violations(spec_text: str) -> list[tuple[int, str]]:
    """Comments whose macro text rpm would expand (or reject).

    rpm expands `%{...}` and `%name` inside comments. `%global`, `%define`
    and `%undefine` are a hard parse error there; `%autosetup`/`%configure`
    expand to shell fragments that the parser then rejects; everything else
    silently rewrites the comment. `%%` is the escape and stays literal.

    A comment is reported once, however many macro references it holds.
    """
    violations: list[tuple[int, str]] = []
    for num, line in enumerate(spec_text.splitlines(), start=1):
        stripped = line.lstrip()
        if not stripped.startswith("#"):
            continue
        i = 0
        bad = False
        while i < len(stripped):
            if stripped[i] != "%":
                i += 1
                continue
            if stripped[i + 1 : i + 2] == "%":
                i += 2          # %% is the escape — rpm renders it as a literal %
                continue
            nxt = stripped[i + 1 : i + 2]
            if nxt == "" or nxt in " \t":
                i += 1          # a bare '%' (100% done) is literal
                continue
            if nxt == "{":
                bad = True
                break
            if nxt.isalpha() or nxt == "_":
                m = re.match(r"[A-Za-z_][A-Za-z0-9_]*", stripped[i + 1 :])
                name = m.group(0) if m else ""
                if name not in SAFE_DIRECTIVES:
                    bad = True
                    break
                i += 1 + len(name)
                continue
            # %(...), %-x, %!x — rpm treats these as macro references too
            bad = True
            break
        if bad:
            violations.append((num, stripped))
    return violations


def _code_text(spec_text: str) -> str:
    """The spec with its comment lines removed — the directives that matter
    (an %autorelease, a rpmautospec BuildRequires) never live in a comment."""
    return "\n".join(
        line for line in spec_text.splitlines()
        if not line.lstrip().startswith("#")
    )


def check_spec(path: Path) -> list[str]:
    """The convention violations of one spec file."""
    errors: list[str] = []
    text = path.read_text()
    head = text[: preamble_end(text)]

    # ---- preamble tags ---------------------------------------------------
    for tag in REQUIRED_TAGS:
        if not re.search(rf"(?m)^{tag}:[ \t]*\S", head):
            errors.append(f"missing {tag}: line in the preamble")
    if re.search(r"(?m)^Version:[ \t]*\S", head):
        version = re.search(r"(?m)^Version:[ \t]*([^\s]+)", head).group(1)
        if not VERSION_RE.match(version):
            errors.append(
                f"illegal Version {version!r} (rpm versions allow letters, "
                f"digits and . _ + ~ ^ only)"
            )
    if re.search(r"(?m)^Release:[ \t]*(\S+)", head):
        release = re.search(r"(?m)^Release:[ \t]*(\S+)", head).group(1)
        if not re.match(r"^[0-9]+%\{\?dist\}$", release):
            errors.append(
                f"Release {release!r} is not an explicit `N%{{?dist}}` "
                f"(no rpmautospec/%autorelease in this repo)"
            )
    if re.search(r"%autorelease|rpmautospec", _code_text(text)):
        errors.append("%autorelease/rpmautospec is not used in this repo")
    if not re.search(r"(?m)^%changelog\b", text):
        errors.append("no %changelog section (this repo requires a written one)")
    elif not re.search(r"(?m)^\*[ \t]+\S", text[text.index("%changelog"):]):
        errors.append("%changelog section is empty")

    # ---- debug packages --------------------------------------------------
    if not re.search(r"(?m)^%(?:global|define)[ \t]+debug_package[ \t]+%\{nil\}", text):
        errors.append(
            "debug_package is not disabled (`%global debug_package %{nil}`) — "
            "no debug packages are built in this repo"
        )
    for m in re.finditer(r"(?m)^%package[ \t]+-?(debuginfo|debugsource)\b", text):
        errors.append(f"debug subpackage %package -{m.group(1)} is declared")

    # ---- macros in comments ----------------------------------------------
    for num, line in comment_macro_violations(text):
        errors.append(
            f"line {num}: macro text in a comment — rpm expands macros inside "
            f"comments too (write %% instead): {line.strip()[:70]}"
        )

    # ---- sources ---------------------------------------------------------
    globals_ = _macro_globals(text)
    pkg_dir = path.parent
    for m in re.finditer(r"(?m)^(Source|Patch)(\d*):[ \t]*(\S+)", head):
        kind, index, value = m.group(1), m.group(2), m.group(3)
        if _is_placeholder(value):
            continue
        if value.startswith(("http://", "https://", "%{url}")):
            continue
        local = _expand_local(value, globals_)
        if not (pkg_dir / local).is_file():
            errors.append(
                f"{kind}{index}: {value!r} is neither a URL nor a file in "
                f"{pkg_dir.name}/ (the submit job's spectool only fetches URLs)"
            )

    # ---- %prep must not download -----------------------------------------
    prep = re.search(r"(?ms)^%prep\b(.*?)(?=^%[a-z])", text)
    if prep and _NETWORK.search(prep.group(1)):
        errors.append(
            "%prep downloads something — the sources are fetched at "
            "SRPM-build time (spectool), not in %prep"
        )

    # ---- forgeautosetup --------------------------------------------------
    if re.search(r"%forge(?:autosetup|meta)", text):
        errors.append(
            "%forgeautosetup/%forgemeta without a forgemeta state derives the "
            "wrong archive dir — use plain `%autosetup -n <archive-dir>`"
        )

    # ---- %files ----------------------------------------------------------
    if not re.search(r"(?m)^%files\b", text):
        errors.append("no %files section")

    return errors


def check_template(path: Path) -> list[str]:
    """Templates are checked for the rules that make sense on a skeleton
    (comments, no autorelease); the placeholder values are skipped."""
    errors: list[str] = []
    text = path.read_text()
    for num, line in comment_macro_violations(text):
        errors.append(
            f"line {num}: macro text in a comment — rpm expands macros inside "
            f"comments too (write %% instead): {line.strip()[:70]}"
        )
    if re.search(r"%autorelease|rpmautospec", _code_text(text)):
        errors.append("%autorelease/rpmautospec is not used in this repo")
    return errors


def main() -> None:
    ap = argparse.ArgumentParser(description="halcyon-applications spec conventions")
    ap.add_argument("packages", nargs="*", help="packages to check (default: all)")
    ap.add_argument("--check", action="store_true",
                    help="check every registered package (and the templates)")
    args = ap.parse_args()

    names = args.packages or registered_packages()
    unknown = [n for n in names if n not in registered_packages()]
    if unknown:
        die(f"not in {PACKAGES_FILE}: {', '.join(unknown)}")

    failed = False
    for name in names:
        path = spec_path_for(name)
        if not path.is_file():
            print(f"{name}: {path} does not exist", file=sys.stderr)
            failed = True
            continue
        errors = check_spec(path)
        if errors:
            failed = True
            for err in errors:
                print(f"{name}: {err}", file=sys.stderr)

    if args.check or not args.packages:
        for tmpl in sorted(TEMPLATE_DIR.glob("*.spec.tmpl")):
            errors = check_template(tmpl)
            if errors:
                failed = True
                for err in errors:
                    print(f"templates/{tmpl.name}: {err}", file=sys.stderr)

    if failed:
        print("specs.py: convention violations found", file=sys.stderr)
        raise SystemExit(1)
    print(f"spec conventions ok: {len(names)} package(s)")


if __name__ == "__main__":
    main()

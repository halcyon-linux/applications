#!/usr/bin/env python3
"""ci/sweep — the applications upstream version sweeper (specs live under
pkgs/<name>/).

Reads each registered package's [pkg.updates] table from ci/packages.toml,
asks the configured feed for the latest upstream version, edits the spec in
place (ci/sweep/spec.py has the exact anda semantics) and reports what
changed. The update workflow commits the result — straight to main (default)
or onto a bump branch — and the push makes copr-build.yml rebuild the changed
packages plus every higher batch.

Feed types:
  github-release  latest GitHub release tag of `repo` (leading v stripped)
  github-tag      newest git tag of `repo` (releases or not)
  custom          custom.custom_<name>() — the upstream-specific feeds
Every registry package must carry an [updates] table; `--check` enforces that,
validates each feed and rejects unreferenced custom_* functions.

Usage:
  ci/sweep/sweep.py [--pkg NAME ...] [--list] [--check]

`--check` is offline and is what copr-build.yml's validate job runs.

Exits 1 when any feed failed (the workflow surfaces it); a feed error never
blocks the other packages.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import custom as custom_feeds  # noqa: E402
import feeds  # noqa: E402
from spec import SpecError, SpecFile  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGES_FILE = REPO_ROOT / "ci" / "packages.toml"


def die(msg: str) -> None:
    print(f"sweep.py: error: {msg}", file=sys.stderr)
    raise SystemExit(1)


def load_registry() -> dict:
    with open(PACKAGES_FILE, "rb") as fh:
        return tomllib.load(fh)


def load_swept() -> dict[str, tuple[dict, Path, Path]]:
    """Registry name -> (updates table, spec path, package dir) for every
    package. A package without an [updates] table is an error: an unswept
    package would silently stop receiving upstream updates."""
    swept: dict[str, tuple[dict, Path, Path]] = {}
    for name, entry in load_registry().items():
        updates = entry.get("updates")
        if not updates:
            die(f"[{name}]: no [updates] table in {PACKAGES_FILE}")
        base = REPO_ROOT / "pkgs" / name
        spec_path = base / f"{name}.spec"
        if not spec_path.is_file():
            die(f"[{name}]: {spec_path} does not exist")
        swept[name] = (updates, spec_path, base)
    return swept


def custom_feed_name(updates: dict) -> str:
    return "custom_" + updates["custom"].replace("-", "_")


def check_registry() -> None:
    """Offline coverage check: every registry package carries a valid feed,
    every custom feed exists, no custom_* function is unreferenced, and no
    pkgs/ directory is unregistered (dead code)."""
    data = load_registry()
    errors: list[str] = []
    referenced: set[str] = set()

    for name, entry in data.items():
        updates = entry.get("updates")
        if not updates:
            errors.append(f"[{name}]: no [updates] table (never swept)")
            continue
        spec_path = REPO_ROOT / "pkgs" / name / f"{name}.spec"
        if not spec_path.is_file():
            errors.append(f"[{name}]: {spec_path} does not exist")
        feed = updates.get("feed")
        if feed in ("github-release", "github-tag"):
            if not updates.get("repo"):
                errors.append(f"[{name}]: feed {feed!r} needs a repo")
        elif feed == "custom":
            if not updates.get("custom"):
                errors.append(f"[{name}]: feed 'custom' needs a custom name")
                continue
            fn_name = custom_feed_name(updates)
            referenced.add(fn_name)
            if not callable(getattr(custom_feeds, fn_name, None)):
                errors.append(f"[{name}]: no {fn_name}() in ci/sweep/custom.py")
        else:
            errors.append(f"[{name}]: unknown feed {feed!r}")

    defined = {
        name for name, obj in vars(custom_feeds).items()
        if name.startswith("custom_") and callable(obj)
    }
    for fn_name in sorted(defined - referenced):
        errors.append(
            f"ci/sweep/custom.py: {fn_name}() is not referenced by {PACKAGES_FILE}"
        )

    for pkg_dir in sorted((REPO_ROOT / "pkgs").iterdir()):
        if (pkg_dir.is_dir() and not pkg_dir.name.startswith(".")
                and pkg_dir.name not in data):
            errors.append(
                f"pkgs/{pkg_dir.name}: not in {PACKAGES_FILE} (never built)"
            )

    if errors:
        for err in errors:
            print(f"check: {err}", file=sys.stderr)
        raise SystemExit(1)
    print(f"registry ok: {len(data)} packages, {len(referenced)} custom feeds")


def sweep_one(name: str, updates: dict, spec_path: Path, base: Path) -> tuple[bool, str, str]:
    """Sweep one package. Returns (wrote, old_version, new_version)."""
    spec = SpecFile(spec_path)
    old_version = spec.get_version()
    feed = updates.get("feed")
    if feed == "github-release":
        spec.set_version(feeds.github_release_tag(updates["repo"]))
    elif feed == "github-tag":
        tag = feeds.github_latest_tag(updates["repo"])
        if not tag:
            raise feeds.FeedError(f"{name}: no tags on {updates['repo']}")
        spec.set_version(tag)
    elif feed == "custom":
        fn_name = custom_feed_name(updates)
        fn = getattr(custom_feeds, fn_name, None)
        if fn is None:
            raise feeds.FeedError(f"no custom feed {fn_name} in ci/sweep/custom.py")
        fn(spec, base)
    else:
        raise feeds.FeedError(f"unknown feed type {feed!r}")
    wrote = spec.save()
    return wrote, old_version, spec.get_version()


def main() -> None:
    ap = argparse.ArgumentParser(description="halcyon-applications version sweep")
    ap.add_argument("--pkg", nargs="+", help="sweep only these packages (default: all)")
    ap.add_argument("--list", action="store_true", help="print the swept packages and exit")
    ap.add_argument("--check", action="store_true",
                    help="validate registry/feed coverage (offline) and exit")
    args = ap.parse_args()

    if args.check:
        check_registry()
        return

    swept = load_swept()
    if args.list:
        for name in sorted(swept):
            print(f"{swept[name][0].get('feed', '?'):>15}  {name}")
        return

    names = sorted(swept) if not args.pkg else args.pkg
    unknown = [n for n in names if n not in swept]
    if unknown:
        die(f"not swept (no [updates] table in {PACKAGES_FILE}): {', '.join(unknown)}")

    failed = False
    for name in names:
        updates, spec_path, base = swept[name]
        try:
            wrote, old_version, new_version = sweep_one(name, updates, spec_path, base)
        except (feeds.FeedError, SpecError, OSError, ValueError, KeyError,
                TypeError, IndexError, subprocess.SubprocessError) as exc:
            # OSError covers urllib errors, ValueError malformed JSON,
            # KeyError/TypeError a malformed API payload, SubprocessError a
            # failing date/rpmspec — one broken feed must not abort the
            # remaining packages
            failed = True
            print(f"error: {name}: {exc}", file=sys.stderr)
            continue
        if wrote:
            print(f"bumped: {name}: {old_version} -> {new_version}")
        else:
            print(f"unchanged: {name} ({new_version})")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()

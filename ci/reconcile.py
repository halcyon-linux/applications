#!/usr/bin/env python3
"""ci/reconcile.py - find packages whose spec NVR is not what Copr published.

The sweep only notices NEW upstream versions. A bump that was committed but
never built (dispatch lost, workflow cancelled) or whose Copr build failed is
invisible to the next sweep - it finds nothing new and the update stays lost.
This closes that gap by comparing each spec's Version-Release against the
latest *succeeded* Copr build.

stdout: space-separated packages to (re)submit - spec differs from the
        published build and no build for the package is in flight.
stderr: `failed: <pkg>` for each stale package whose latest build failed
        (update.yml turns these into an issue).

A package whose latest build already failed on the SAME NVR is only reported,
not resubmitted - same inputs fail again - unless --retry-failed is given
(the workflow passes it weekly, to ride out transient Copr/upstream errors).

Usage: ci/reconcile.py [--project OWNER/NAME] [--retry-failed]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "sweep"))

from spec import SpecFile  # noqa: E402
from sweep import REPO_ROOT, load_registry  # noqa: E402

API = "https://copr.fedorainfracloud.org/api_3/package/list"
IN_FLIGHT = {"pending", "starting", "running", "importing", "waiting", "forked"}


def spec_nvr(name: str) -> str:
    spec = SpecFile(REPO_ROOT / "pkgs" / name / f"{name}.spec")
    return f"{spec.get_version()}-{spec._release_match().group(2)}"


def copr_builds(owner: str, project: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    offset = 0
    while True:
        url = (f"{API}?ownername={owner}&projectname={project}&limit=100&offset={offset}"
               "&with_latest_build=true&with_latest_succeeded_build=true")
        with urllib.request.urlopen(url, timeout=60) as resp:
            items = json.load(resp)["items"]
        out.update({p["name"]: p["builds"] for p in items})
        if len(items) < 100:
            return out
        offset += 100


def stale(names, builds, retry_failed=False) -> tuple[list[str], list[str]]:
    """(packages to resubmit, subset whose latest build failed)."""
    todo, failed = [], []
    for name in names:
        b = builds.get(name, {})
        latest, ok = b.get("latest"), b.get("latest_succeeded")
        if latest and latest["state"] in IN_FLIGHT:
            continue
        published = ok and ok["source_package"]["version"]
        if published == spec_nvr(name):
            continue
        if latest and latest["state"] == "failed":
            failed.append(name)
            if latest["source_package"]["version"] == spec_nvr(name) and not retry_failed:
                continue
        todo.append(name)
    return todo, failed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default="aahsnr-work/applications")
    ap.add_argument("--retry-failed", action="store_true")
    args = ap.parse_args()
    owner, project = args.project.split("/")
    todo, failed = stale(sorted(load_registry()), copr_builds(owner, project), args.retry_failed)
    for name in failed:
        print(f"failed: {name}", file=sys.stderr)
    print(" ".join(todo))


if __name__ == "__main__":
    main()

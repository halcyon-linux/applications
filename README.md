# applications

halcyon GUI applications — Fedora 44 (+45) RPMs built on
[Copr](https://copr.fedorainfracloud.org/coprs/aahsnr-work/applications/).

```
dnf copr enable aahsnr-work/applications fedora-44
```

One of the six halcyon group repositories: base-pkgs · cli-tools ·
applications · fonts · texlive-packages · linux-p03.

## CI

- `copr-build.yml` — a push to `main` rebuilds changed packages plus every
  higher batch, wave-by-wave. Gated on the `CASCADE_ENABLED` repository
  variable (kill-switch; `workflow_dispatch` bypasses it). PRs validate
  only.
- `update.yml` — the upstream version sweep (`ci/sweep/sweep.py` over the
  registry's `[pkg.updates]` feeds), commits bumps straight to `main`.
- `builder-docker.yml` — builds this repo's own CI job image and pushes
  it to `ghcr.io/halcyon-linux/applications-builder:f44` (consumed by this
  repo's build and sweep jobs).
- `repoclosure.yml` — nightly (05:43 UTC) + post-cascade closure check of
  the published Copr repo against Fedora 44/45 (+ Terra and the
  lionheartp bootstrap repo).

## Running and cancelling workflows

### Run a workflow manually

In the GitHub UI: **Actions** → the workflow → **Run workflow** → branch `main` →
fill the inputs → **Run workflow**. From the CLI:

```bash
gh workflow run <file> -R halcyon-linux/applications --ref main -f <input>=<value>
```

Inputs (leave empty for the default):

- `copr-build.yml` — `only`: space-separated packages to build (empty = all), e.g. `-f only="<pkg> <pkg>"`. Bypasses the `CASCADE_ENABLED` gate.
- `update.yml` — `mode`: `commit` or `pr`; `pkg`: space-separated packages to sweep (empty = all).
- `repoclosure.yml`, `builder-docker.yml` — no inputs.

### Force-cancel a workflow run

1. Find the run ID: `gh run list -R halcyon-linux/applications --workflow <file>`.
2. Cancel it: `gh run cancel <run-id> -R halcyon-linux/applications`, or **Cancel workflow**
   on the run page.
3. If it stays in *Cancelling* because a job or runner is hung, use **Force cancel**
   on the run page, or:

   ```bash
   gh api -X POST repos/halcyon-linux/applications/actions/runs/<run-id>/force-cancel
   ```

A force cancel ends the run without waiting for its jobs. It does not stop Copr
builds that were already submitted; cancel those on the Copr project page.

**Caution:** if a `update.yml` run is cancelled after it has pushed a bump, that bump can be left without a `copr-build` run. Dispatch `copr-build.yml` with `only` set to the bumped packages.

## Layout

```
ci/packages.toml    the registry: build selection + sweep-feed config
ci/matrix.py        batch/wave build plan (validate job runs it)
ci/specs.py         the spec conventions, checked mechanically
ci/sweep/           the version sweeper + custom feeds
ci/tests/           unit tests for the CI helpers
pkgs/<pkg>/         spec + local sources
repo/               the applications.repo consumer drop-in
templates/          starting points for new specs
```

See [AGENTS.md](AGENTS.md) for the conventions before touching specs.

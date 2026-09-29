# AGENTS.md

RPM package repo for **halcyon GUI applications** — one of the six halcyon group
repositories (base-pkgs, cli-tools, applications, fonts, texlive-packages,
linux-p03; each has its own GitHub repo under
[halcyon-linux](https://github.com/orgs/halcyon-linux/repositories) and its
own Copr project under `aahsnr-work`). Built on Fedora Copr
([aahsnr-work/applications](https://copr.fedorainfracloud.org/coprs/aahsnr-work/applications/),
chroots fedora-44-x86_64 + fedora-45-x86_64) in CI. The repo carries only
specs, the registry, the version sweeper and the workflows; Copr owns the
build farm, the GPG signing and the repo hosting. Consumers:

```
dnf copr enable aahsnr-work/applications fedora-44
```

Fedora 44 is the target; the fc45 chroot exists so closure and build
breakage surfaces one release early.

**Markdown discipline**: do NOT read, use, or act on `TODO.md`, `notes/` or
any other markdown file unless the user explicitly instructs you to utilize
that particular markdown file for the task at hand. Code, the registry
(`ci/packages.toml`), and the workflows are the source of truth.

## Commands

There is no test suite; verification = the Copr build going green.

```bash
# registry consistency + build plan (what CI's validate job runs)
python3 ci/matrix.py --list
python3 ci/matrix.py --list --since <sha>   # what a push would rebuild

# submit ONE package to Copr (what copr-build.yml's submit jobs do;
# rpmbuild/spectool/cop-cli: run inside the CI image or a fedora:44 container)
spectool -g -C _srpms/<pkg> pkgs/<pkg>/<pkg>.spec
rpmbuild -bs --define "_sourcedir $PWD/_srpms/<pkg>" \
         --define "_srcrpmdir $PWD/_srpms" \
         --define "_specdir $PWD/pkgs/<pkg>" pkgs/<pkg>/<pkg>.spec
copr-cli build --nowait applications _srpms/<pkg>-*.src.rpm

# the version sweep (update.yml)
GITHUB_TOKEN=$(gh auth token) python3 ci/sweep/sweep.py [--pkg <name>]

# a mock buildroot identical to Copr's, for debugging a failed build locally
copr-cli mock-config aahsnr-work/applications fedora-44-x86_64 > /tmp/copr.cfg
mock -r /tmp/copr.cfg <srpm>
```

## Non-obvious rules

- **A package without a `ci/packages.toml` entry is never built** — the
  registry is the build selection AND the sweep-feed config. Adding a
  package = 2 files: `pkgs/<pkg>/<pkg>.spec` (start from
  `templates/*.spec.tmpl`) and the registry entry (`batch` +
  `[pkg.updates]` feed).
- **Batches are dependency levels**: a package's `batch` must be >= 1 + the
  highest batch of anything it BuildRequires. Packages within one batch
  submit in parallel and must never depend on each other. `copr-build.yml`
  submits wave-by-wave — each successful build is immediately visible to
  the project repo, which is how batch N+1 installs batch N's output as
  BuildRequires. `ci/matrix.py` enforces the invariant (the validate job
  runs it).
- **A push to `main` rebuilds changed packages plus every higher batch**
  (wave-submitted). Push cascades are additionally gated on the
  CASCADE_ENABLED repository variable (kill-switch — set it to `false` to
  stop automatic cascades; `workflow_dispatch` bypasses it). PRs run
  validation only.
- Touching `ci/**` or `.github/builder/**` makes `ci/matrix.py` rebuild
  _every_ package in this repo (`INFRA_PREFIXES`).
- **Version bumps are automatic** (`update.yml`, weekly Monday floor +
  chained after every cascade): `ci/sweep/sweep.py` reads each package's
  `[pkg.updates]` table (`feed = "github-release" | "github-tag" |
  "custom"` + `repo`) and edits specs in place (Release resets only on a
  real version change; file written only on content change). Custom feeds
  live in `ci/sweep/custom.py`. Default mode commits bumps straight to
  main (self-healing: a failed build leaves the published version
  untouched); set the `UPDATE_MODE` repo variable to `pr` for a review
  gate.
- **Spec conventions** (terra-style, differ from Fedora defaults):
  - full URLs in `Source*` entries — the submit job's `spectool -g`
    fetches them before `rpmbuild -bs`; keep downloads out of `%prep`.
  - explicit `Release: N%{?dist}` + a written `%changelog` — no
    rpmautospec/`%autorelease`.
  - **never mention macros textually in comments** — rpm expands macros
    inside comments too.
  - build-time repos outside Fedora/Terra go in the **Copr chroot's repo
    list** (`copr-cli edit-chroot aahsnr-work/applications/fedora-44-x86_64
    --repos …`), not the spec. Configured: Terra 44 and the
    `lionheartp/Hyprland` lowest-priority bootstrap.
  - _no debug packages_ — every spec carries the debug_package nil define;
    nothing in the halcyon image consumes debug packages.
  - **vendor rewraps** are only allowed when upstream itself ships an RPM
    or a self-contained release archive; anything else is a source build.
    A foreign binary tree needs the full nil set (debug_package nil,
    _build_id_links none, __os_install_post nil) — an empty debugsource
    file list fails the build, and Copr's brp hooks (shebang mangler,
    check-rpaths, /usr/lib/.build-id links) hard-fail what older
    buildroots let pass. Do not remove those defines.
  - never use forgeautosetup/forgemeta without defining the forgemeta
    state — the archive dir name derives wrong. Use plain
    `%autosetup -n <archive-dir>`.
  - validate a spec against the UPSTREAM tarball, not from memory:
    release layouts drift (completions dirs get renamed, changelogs
    dropped).
  - `install -t DIR SRC` keeps SRC's basename — `%files` must claim the
    name as installed. Prefer explicit
    `install -Dm644 SRC %{buildroot}%{dir}/NAME`.
- `repo/` carries the consumer drop-ins for **all six** group repos —
  repoclosure installs all of them and checks THIS repo's project against
  the union, exactly what a halcyon-image consumer sees. The
  *_mirror.repo alternative is never installed by CI.
- **CI authentication**: the `COPR_CLICONF` GitHub secret drives every
  copr-cli step. The Copr API token expires — a wave of 401s in
  copr-build.yml means: regenerate at
  <https://copr.fedorainfracloud.org/api/>, re-set the secret, re-run.


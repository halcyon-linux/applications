"""The custom version feeds for the applications registry.

Each function implements one upstream whose version discovery cannot be
expressed by the generic github-release/github-tag feeds. Only feeds
referenced by an [updates] table in ci/packages.toml belong here; `sweep.py
--check` rejects an unreferenced custom_* function.

The obsidian port fixes the old rhai script, which used `#` lines as comments
(a rhai syntax error) and therefore never parsed; the port implements the
documented intent.
"""

from __future__ import annotations

import re
from pathlib import Path

import feeds
from spec import SpecFile


def _aur_pkgver(pkg: str) -> str:
    """pkgver of an AUR package (pkgrel stripped) — for vendor apps whose
    only version tracker is the AUR maintainer."""
    data = feeds.fetch_json(
        "https://aur.archlinux.org/rpc/v5/info?arg%5B%5D=" + pkg)
    results = data.get("results") or []
    aur_version = results[0]["Version"] if results else ""
    if not aur_version:
        raise feeds.FeedError(f"{pkg}: the AUR RPC returned no version")
    return aur_version.rsplit("-", 1)[0]


def custom_antigravity_cli(spec: SpecFile, pkg_dir: Path) -> None:
    # the AUR pkgver carries the full "1.2.10_4751581200121856" pair; the
    # spec keeps the dotted version and pins the build id in the cli_build
    # global that the Source URL interpolates
    pkgver = _aur_pkgver("antigravity-cli")
    m = re.fullmatch(r"([0-9.]+)_(\d+)", pkgver)
    if not m:
        raise feeds.FeedError(f"antigravity-cli: unexpected AUR pkgver {pkgver!r}")
    spec.set_version(m.group(1))
    spec.set_global("cli_build", m.group(2))


def custom_bees(spec: SpecFile, pkg_dir: Path) -> None:
    # Zygo/bees publishes no GitHub releases and tags prereleases as
    # vX.Y.Z-rcN; rpmvercmp ranks a suffixed tag above its release
    # ("0.11-rc4" beats "0.11" — end-of-string loses to any leftover
    # segment) and the Version rewrite would then sanitize the hyphen,
    # breaking the archive Source URL. Take the newest tag with no suffix.
    from functools import cmp_to_key
    from vercmp import rpmvercmp
    tags = [t.removeprefix("v") for t in feeds.github_tag_names("Zygo/bees")]
    tags.sort(key=cmp_to_key(rpmvercmp), reverse=True)
    for version in tags:
        if re.fullmatch(r"[0-9][0-9.]*", version):
            spec.set_version(version)
            return
    raise feeds.FeedError("bees: no stable tag on Zygo/bees")


def custom_bitwarden(spec: SpecFile, pkg_dir: Path) -> None:
    # bitwarden/clients cuts other tags too, and pre-releases (betas) often
    # ship no Linux RPM at all (the 2026.9.1-beta.1 assets are Windows/macOS
    # only) — the first desktop-v tag is therefore not enough. Walk the
    # releases newest-first and take the first desktop-v release that
    # actually carries the x86_64 RPM asset Source0 needs.
    releases = feeds.fetch_json(
        "https://api.github.com/repos/bitwarden/clients/releases?per_page=30"
    )
    for release in releases:
        tag = release.get("tag_name", "")
        if not tag.startswith("desktop-v"):
            continue
        version = tag.removeprefix("desktop-v")
        assets = {a.get("name", "") for a in release.get("assets", [])}
        if f"Bitwarden-{version}-x86_64.rpm" in assets:
            spec.set_version(version)
            return
    raise feeds.FeedError(
        "bitwarden: no desktop-v release in the last 30 ships a Bitwarden-<ver>-x86_64.rpm"
    )


def custom_obsidian(spec: SpecFile, pkg_dir: Path) -> None:
    # the newest obsidianmd/obsidian-releases release that ships the desktop
    # linux tarball; the release's sha256 asset digest is pinned in %global
    # digest for the %prep checksum ('none' skips the check when upstream
    # publishes no digest).
    #
    # The asset list is parsed as JSON, not scraped with a regex: a regex
    # over the raw payload can pair one asset's name with the NEXT asset's
    # digest whenever upstream publishes an asset without one — and the
    # mismatch then only shows up as a sha256 failure in the build.
    releases = feeds.fetch_json(
        "https://api.github.com/repos/obsidianmd/obsidian-releases/releases?per_page=30"
    )
    for release in releases:
        version = None
        digest = "none"
        for asset in release.get("assets", []):
            name = asset.get("name", "")
            m = re.fullmatch(r"obsidian-([0-9.]+)\.tar\.gz", name)
            if not m:
                continue
            version = m.group(1)
            found = asset.get("digest") or ""
            if found.startswith("sha256:"):
                digest = found[len("sha256:"):]
            break
        if version is None:
            continue
        spec.set_version(version)
        spec.set_global("digest", digest)
        return
    raise feeds.FeedError(
        "obsidian: no release in the last 30 ships an obsidian-<ver>.tar.gz"
    )


def custom_opencode_desktop(spec: SpecFile, pkg_dir: Path) -> None:
    # the desktop app ships through opencode.ai's own stable download
    # endpoint, which 302s to the versioned RPM; the version is read off the
    # redirect target (no first-party release feed)
    import urllib.error
    import urllib.request

    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    req = urllib.request.Request(
        "https://opencode.ai/download/stable/linux-x64-rpm",
        headers={"User-Agent": "halcyon-packages-sweeper"},
    )
    feeds.validate_url(req.full_url)
    try:
        urllib.request.build_opener(_NoRedirect).open(req, timeout=60)
    except urllib.error.HTTPError as exc:
        location = exc.headers.get("Location", "")
    else:
        raise feeds.FeedError(
            "opencode-desktop: the stable endpoint did not redirect")
    spec.set_version(feeds.find_group(r"/files/bin/([0-9.]+)/", location))


def custom_ticktick(spec: SpecFile, pkg_dir: Path) -> None:
    # TickTick publishes no first-party version feed, but the AUR package
    # tracks it: the AUR maintainer bumps pkgver on every upstream release.
    # Version is pkgver-pkgrel — keep pkgver only.
    data = feeds.fetch_json("https://aur.archlinux.org/rpc/v5/info?arg%5B%5D=ticktick")
    results = data.get("results") or []
    aur_version = results[0]["Version"] if results else ""
    if not aur_version:
        raise feeds.FeedError("ticktick: the AUR RPC returned no version")
    spec.set_version(re.sub(r"-[^-]*$", "", aur_version))


def custom_zotero(spec: SpecFile, pkg_dir: Path) -> None:
    # zotero's git tags can outrun its release artifacts: the 10.0.4 tag has
    # no linux tarball on download.zotero.org (S3 answers 403 for the absent
    # key) and the 2026-09-27 batch-0 submit died in spectool on exactly
    # that. Version is the newest tag whose official linux tarball really
    # downloads — probe newest-first with HEAD, skipping 403/404 (yanked or
    # never-published) and erroring on anything else, so a dead network or a
    # moved host never silently downgrades the package.
    from functools import cmp_to_key

    from vercmp import rpmvercmp

    versions = sorted(
        {t.removeprefix("v") for t in feeds.github_tag_names("zotero/zotero")},
        key=cmp_to_key(rpmvercmp),
        reverse=True,
    )
    for version in versions:
        url = (
            "https://download.zotero.org/client/release/"
            + version
            + "/Zotero-"
            + version
            + "_linux-x86_64.tar.xz"
        )
        if feeds.head_probe(url):
            spec.set_version(version)
            return
    raise feeds.FeedError("zotero: no tag carries a published linux tarball")


def custom_emacs_pgtk(spec: SpecFile, pkg_dir: Path) -> None:
    # GNU Emacs publishes on ftp.gnu.org only; the emacs-mirror/emacs GitHub
    # mirror tags releases as emacs-<version> and pretests as
    # emacs-<version>.<90+> (pretest tarballs land on alpha.gnu.org, not
    # ftp.gnu.org). Rank the numeric tags newest-first and HEAD-probe the
    # ftp.gnu.org tarball zotero-style so a pretest tag never bumps the spec.
    from functools import cmp_to_key

    from vercmp import rpmvercmp

    versions = sorted(
        {
            v
            for v in (
                t.removeprefix("emacs-")
                for t in feeds.github_tag_names("emacs-mirror/emacs")
            )
            if re.fullmatch(r"[0-9][0-9.]*", v)
        },
        key=cmp_to_key(rpmvercmp),
        reverse=True,
    )
    for version in versions:
        url = f"https://ftp.gnu.org/gnu/emacs/emacs-{version}.tar.xz"
        if feeds.head_probe(url):
            spec.set_version(version)
            return
    raise feeds.FeedError("emacs-pgtk: no tag carries a published tarball")


def custom_private_internet_access(spec: SpecFile, pkg_dir: Path) -> None:
    # PIA publishes no version feed at all: no GitHub release assets and a 403
    # on the installers directory listing — the AUR piavpn-bin maintainer does
    # the discovery work, so mirror their pins: pkgver for the version, the
    # PKGBUILD's _pkgver for the URL version, and build_number for the
    # pia_build global the Source URL interpolates.
    pkgtxt = feeds.fetch_text(
        "https://aur.archlinux.org/cgit/aur.git/plain/PKGBUILD?h=piavpn-bin")
    spec.set_version(feeds.find_group(r"(?m)^pkgver=(\S+)", pkgtxt))
    spec.set_global("pia_url_version", feeds.find_group(r"(?m)^_pkgver=(\S+)", pkgtxt))
    spec.set_global("pia_build", feeds.find_group(r"(?m)^build_number=(\S+)", pkgtxt))


def custom_mullvad_vpn(spec: SpecFile, pkg_dir: Path) -> None:
    # mullvad.net's Linux download page is server-rendered and links the
    # current x86_64 RPM on their GitHub releases — the same page upstream's
    # own install instructions point at.
    html = feeds.fetch_text("https://mullvad.net/en/download/vpn/linux")
    spec.set_version(feeds.find_group(r"MullvadVPN-([0-9.]+)_x86_64\.rpm", html))


def _proton_rpm_version(ghrepo: str, rpm_name: str, srcarch: str, spec: SpecFile) -> None:
    # ProtonVPN/<ghrepo> tags newest-first, HEAD-probing the official
    # repo.protonvpn.com RPM URL so a tag whose RPM build has not landed yet
    # (Proton's RPM builds can lag their tags) never bumps the spec. The
    # official repo 403s the sweeper's default UA and answers the browser one.
    fc = spec.get_global("pv_fc") or "44"
    rel = spec.get_global("pv_rel") or "1"
    # /tags order is not newest-first (feeds.github_tag_names warns) — sort
    # with rpmvercmp so a tag-order hiccup can never bump the spec DOWN to an
    # older still-published RPM
    from functools import cmp_to_key

    from vercmp import rpmvercmp
    tags = [t.removeprefix("v") for t in feeds.github_tag_names(f"ProtonVPN/{ghrepo}")]
    tags.sort(key=cmp_to_key(rpmvercmp), reverse=True)
    for version in tags:
        if not re.fullmatch(r"[0-9][0-9.]*", version):
            continue
        url = (
            f"https://repo.protonvpn.com/fedora-{fc}-stable/"
            f"{rpm_name}/{rpm_name}-{version}-{rel}.fc{fc}.{srcarch}.rpm"
        )
        # the official repo 403s the sweeper's default UA and answers the
        # browser one
        if feeds.head_probe(url, user_agent="Mozilla/5.0"):
            spec.set_version(version)
            return
    raise feeds.FeedError(f"{rpm_name}: no tag carries a published RPM yet")


def custom_python3_proton_core(spec: SpecFile, pkg_dir: Path) -> None:
    _proton_rpm_version("python-proton-core", "python3-proton-core", "noarch", spec)


def custom_python3_proton_keyring_linux(spec: SpecFile, pkg_dir: Path) -> None:
    _proton_rpm_version("python-proton-keyring-linux",
                        "python3-proton-keyring-linux", "noarch", spec)


def custom_python3_proton_vpn_api_core(spec: SpecFile, pkg_dir: Path) -> None:
    _proton_rpm_version("python-proton-vpn-api-core",
                        "python3-proton-vpn-api-core", "x86_64", spec)


def custom_proton_vpn_daemon(spec: SpecFile, pkg_dir: Path) -> None:
    _proton_rpm_version("proton-vpn-daemon", "proton-vpn-daemon", "noarch", spec)


def custom_proton_vpn_gtk_app(spec: SpecFile, pkg_dir: Path) -> None:
    _proton_rpm_version("proton-vpn-gtk-app", "proton-vpn-gtk-app", "noarch", spec)


def _apt_stanzas(text: str):
    """Yield the field dicts of a Debian Packages index."""
    stanza: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip():
            if stanza:
                yield stanza
                stanza = {}
            continue
        if line[0] in " \t":
            continue          # continuation of the Description field
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        stanza[key.strip()] = value.strip()
    if stanza:
        yield stanza


def _apt_index_update(spec: SpecFile, index_url: str, package: str, arch: str,
                      filename_for) -> None:
    """Pin the newest version and its sha256 from a Debian Packages index."""
    from functools import cmp_to_key

    from vercmp import rpmvercmp

    candidates = []
    for fields in _apt_stanzas(feeds.fetch_text(index_url)):
        if fields.get("Package") != package or fields.get("Architecture") != arch:
            continue
        version = fields.get("Version", "")
        sha256 = fields.get("SHA256", "")
        filename = fields.get("Filename", "")
        if version and sha256 and filename:
            candidates.append((version, sha256, filename))
    if not candidates:
        raise feeds.FeedError(
            f"{package}: no {arch} stanza with Version/SHA256/Filename in {index_url}")
    version, sha256, filename = max(
        candidates, key=cmp_to_key(lambda a, b: rpmvercmp(a[0], b[0])))
    expected = filename_for(version)
    if filename != expected:
        raise feeds.FeedError(
            f"{package}: index filename {filename!r} does not match {expected!r}")
    if not re.fullmatch(r"[0-9a-f]{64}", sha256):
        raise feeds.FeedError(f"{package}: bad SHA256 {sha256!r} for {version}")
    spec.set_version(version)
    spec.set_global("digest", sha256)


def custom_claude_desktop(spec: SpecFile, pkg_dir: Path) -> None:
    # Anthropic's apt repo is the first-party source of both the version and
    # the .deb digest; the spec constructs the pool URL from the version.
    _apt_index_update(
        spec,
        "https://downloads.claude.ai/claude-desktop/apt/stable/"
        "dists/stable/main/binary-amd64/Packages",
        "claude-desktop",
        "amd64",
        lambda version: (
            f"pool/main/c/claude-desktop/claude-desktop_{version}_amd64.deb"),
    )


def custom_chatgpt(spec: SpecFile, pkg_dir: Path) -> None:
    # OpenAI serves the ChatGPT desktop RPMs from a real yum repository at
    # persistent.oaistatic.com/codex-app-prod/linux/rpm/x86_64 — the primary
    # metadata is the first-party source of the version, of the upstream
    # release number (part of the pool filename the spec's Source0
    # interpolates) and of the sha256 the spec pins in %global digest for
    # the %prep checksum. The .deb channel mirrors the same builds; the RPM
    # is the native artifact.
    import gzip
    import zlib
    import xml.etree.ElementTree as ET

    def _xml(payload, what: str):
        # a CDN hiccup can serve an HTML error page with HTTP 200, or a
        # truncated body: raise a FeedError, not a raw ParseError/EOFError —
        # sweep.py does not catch those and one of them would abort the
        # whole sweep run instead of failing this package
        try:
            return ET.fromstring(payload)
        except ET.ParseError as exc:
            raise feeds.FeedError(
                f"chatgpt: malformed {what}: {exc}") from exc

    repo = "https://persistent.oaistatic.com/codex-app-prod/linux/rpm/x86_64/"
    repomd = _xml(feeds.fetch_text(repo + "repodata/repomd.xml"), "repomd.xml")
    repo_ns = "{http://linux.duke.edu/metadata/repo}"
    primary_href = ""
    for data in repomd.iter(f"{repo_ns}data"):
        if data.get("type") == "primary":
            loc = data.find(f"{repo_ns}location")
            if loc is not None:
                primary_href = loc.get("href", "")
            break
    if not primary_href:
        raise feeds.FeedError("chatgpt: repodata carries no primary index")

    common_ns = "{http://linux.duke.edu/metadata/common}"
    try:
        primary = gzip.decompress(feeds.fetch_bytes(repo + primary_href))
    except (EOFError, OSError, zlib.error) as exc:
        raise feeds.FeedError(
            f"chatgpt: cannot decompress {primary_href}: {exc}") from exc
    candidates = []
    for pkg in _xml(primary, primary_href).iter(f"{common_ns}package"):
        if pkg.findtext(f"{common_ns}name") != "chatgpt":
            continue
        if pkg.findtext(f"{common_ns}arch") != "x86_64":
            continue
        ver = pkg.find(f"{common_ns}version")
        checksum = pkg.find(f"{common_ns}checksum")
        loc = pkg.find(f"{common_ns}location")
        if ver is None or checksum is None or loc is None:
            continue
        digest = checksum.text or ""
        # a stanza without a usable sha256 is skipped, like _apt_index_update
        # skips incomplete stanzas; if none survive, the error below names it
        if checksum.get("type") != "sha256" or not re.fullmatch(
                r"[0-9a-f]{64}", digest):
            continue
        candidates.append((ver.get("ver", ""), ver.get("rel", ""), digest,
                           loc.get("href", "")))
    if not candidates:
        raise feeds.FeedError(
            f"chatgpt: no x86_64 chatgpt stanza with a sha256 in "
            f"{repo}{primary_href}")

    from functools import cmp_to_key

    from vercmp import rpmvercmp

    def _newer(a, b):
        order = rpmvercmp(a[0], b[0])
        return order if order else rpmvercmp(a[1], b[1])

    version, rel, digest, href = max(candidates, key=cmp_to_key(_newer))
    expected = f"chatgpt-{version}-{rel}.x86_64.rpm"
    if href != expected:
        raise feeds.FeedError(
            f"chatgpt: pool filename {href!r} does not match {expected!r}")
    if not feeds.head_probe(repo + href):
        raise feeds.FeedError(f"chatgpt: RPM not published at {repo}{href}")
    spec.set_version(version)
    spec.set_global("upstream_rel", rel)
    spec.set_global("digest", digest)


def custom_claude_desktop_extra(spec: SpecFile, pkg_dir: Path) -> None:
    # Upstream re-releases the same base version with a new release number
    # (v3.6556.2-7); the tag and the x86_64 RPM asset carry both. The asset's
    # GitHub digest is pinned for the prep check.
    releases = feeds.fetch_json(
        "https://api.github.com/repos/patrickjaja/claude-desktop-extra/"
        "releases?per_page=30")
    for release in releases:
        if release.get("draft") or release.get("prerelease"):
            continue
        m = re.fullmatch(r"v([0-9][0-9.]*)-([1-9][0-9]*)",
                         release.get("tag_name", ""))
        if not m:
            continue
        version, rel = m.groups()
        asset_name = f"claude-desktop-extra-{version}-{rel}.x86_64.rpm"
        for asset in release.get("assets", []):
            if asset.get("name") != asset_name:
                continue
            digest = asset.get("digest") or ""
            if not digest.startswith("sha256:"):
                raise feeds.FeedError(
                    f"claude-desktop-extra: {asset_name} has no sha256 digest")
            spec.set_version(version)
            spec.set_global("extra_rel", rel)
            spec.set_global("digest", digest[len("sha256:"):])
            return
    raise feeds.FeedError(
        "claude-desktop-extra: no release in the last 30 ships "
        "claude-desktop-extra-<version>-<rel>.x86_64.rpm")


def custom_claude_science(spec: SpecFile, pkg_dir: Path) -> None:
    # Anthropic serves the latest build from a stable URL and publishes no
    # sha256. The version comes from the Content-Disposition filename and the
    # digest from x-goog-hash's MD5; then the versioned URL the spec pins is
    # probed, so a latest-only build never writes an unfetchable Source0.
    import base64

    latest = "https://downloads.claude.ai/claude-science/latest/linux-x64"
    headers = feeds.head_headers(latest)
    disposition = headers.get("Content-Disposition", "")
    m = re.search(r'filename="claude-science-([0-9][0-9.]*)-linux-x64"', disposition)
    if not m:
        raise feeds.FeedError(
            f"claude-science: no version in Content-Disposition {disposition!r}")
    version = m.group(1)

    md5 = ""
    for value in headers.get_all("x-goog-hash") or []:
        for part in value.split(","):
            part = part.strip()
            if part.startswith("md5="):
                md5 = base64.b64decode(part[len("md5="):]).hex()
    if not re.fullmatch(r"[0-9a-f]{32}", md5):
        raise feeds.FeedError("claude-science: download endpoint has no MD5 header")

    versioned = f"https://downloads.claude.ai/claude-science/{version}/linux-x64"
    if not feeds.head_probe(versioned):
        raise feeds.FeedError(
            f"claude-science: versioned URL not published: {versioned}")
    spec.set_version(version)
    spec.set_global("md5", md5)

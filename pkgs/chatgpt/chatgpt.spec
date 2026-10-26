# Vendor rewrap of OpenAI's official ChatGPT desktop RPM (x86_64 only).
# The upstream RPM is fetched at SRPM-build time (Source0) and unpacked
# in %%prep with rpm2cpio. No build step — the prebuilt binary is
# packaged as-is. The version sweep (ci/sweep/custom.py:custom_chatgpt)
# discovers the latest x86_64 RPM from OpenAI's persistent.oaistatic.com
# repository and pins the sha256 in %%global digest for the %%prep check.
#
# Prebuilt foreign binary: no build-id or debuginfo can be produced, so
# the debug package is disabled. The binary ships as-is from the release
# RPM; the full brp nil set keeps the payload byte-identical.
%global debug_package %{nil}
%global _build_id_links none
%global __os_install_post %{nil}

# NOTE: %%global debug_package %%{nil} is what makes the default ELF-rewriting
# brp hooks run, not what skips them — Fedora's %%__os_install_post gates
# brp-strip / brp-strip-comment-note on %%__debug_package being *undefined*.
# With them in place every ELF file in the bundle gets rewritten (measured:
# all, e.g. ChatGPT -528 bytes, libvulkan.so.1 -1685512, etc.), so the
# packaged payload stops being byte-identical to the upstream RPM.
# brp-strip-lto and brp-strip-static-archive are not gated at all. Empty all
# four so the payload matches the upstream blob bit for bit. Set them to
# %%{nil} rather than %%undefine'ing them: with rpm 6.0.2 %%undefine does not
# mask brp-strip / brp-strip-comment-note (the hooks still ran, while
# %%undefine on the lto one did take effect).
%global __brp_strip %{nil}
%global __brp_strip_comment_note %{nil}
%global __brp_strip_lto %{nil}
%global __brp_strip_static_archive %{nil}

# brp-mangle-shebangs is not an ELF hook but rewrites payload bytes just the
# same. The upstream bundle may contain shebangs; unset the hook to keep
# byte-identity.
%global __brp_mangle_shebangs %{nil}

# add-determinism's brp hook (add-det) would regenerate /usr/lib/.build-id
# links from the blob's ELF build-id notes and otherwise normalize the
# payload. The blob must ship byte-identical, so unset the hook.
%undefine __brp_add_determinism

# The bundled Electron/Chromium libs under /usr/lib/chatgpt carry SONAMEs,
# so the dependency generator would advertise them as system providers
# (e.g. libvulkan.so.1). They are private to the bundle (resolved via the
# $ORIGIN RPATH on the ChatGPT binary, not the system loader path), so
# suppress Provides from /usr/lib/chatgpt.
%global __provides_exclude_from ^/usr/lib/chatgpt/

# The ChatGPT binary links bundled libffmpeg.so, libvulkan.so.1, etc.
# Nothing in Fedora provides them, and the bundle satisfies them internally,
# so exclude them. The generated require strings carry the arch qualifier
# (libffmpeg.so()(64bit)), hence the prefix match without $.
%global __requires_exclude ^libffmpeg\.so|^libvulkan\.so\.1|^libEGL\.so|^libGLESv2\.so

# upstream version format: YY.MMDD.BUILD (e.g. 26.1021.22027)
# the sweep pins the sha256 of the x86_64 RPM in %%global digest
%global upstream_version 26.1021.22027
%global digest none

Name:           chatgpt
Version:        26.1021.22027
Release:        2%{?dist}
Summary:        ChatGPT by OpenAI — AI assistant with Codex integration
License:        Proprietary
URL:            https://chatgpt.com/download
ExclusiveArch:  x86_64

#!RemoteAsset
Source0:        https://persistent.oaistatic.com/codex-app-prod/linux/rpm/x86_64/chatgpt-%{upstream_version}-1.x86_64.rpm
# Curated AppStream metainfo (upstream ships com.openai.chatgpt.metainfo.xml
# in the RPM but it may be minimal; this repo provides a complete file).
Source1:        com.openai.chatgpt.metainfo.xml

BuildRequires:  desktop-file-utils
BuildRequires:  appstream
BuildRequires:  cpio
BuildRequires:  coreutils
BuildRequires:  sha256sum

# Runtime-only deps the ELF dependency generator cannot see. Everything
# linked (gtk3, nss, cups, alsa, at-spi2, dbus, ...) is auto-detected from
# DT_NEEDED and deliberately not duplicated here.
# - xdg-utils: the app shells out to xdg-open/xdg-settings.
# - libnotify, libXScrnSaver: loaded indirectly via Electron; not in any
#   DT_NEEDED, kept at parity so notifications and idle detection behave as
#   upstream ships them.
# - libXtst, libuuid: upstream-declared; Fedora satisfies via libXtst and libuuid.
# - libsecret: Electron uses it for keyring integration.
# - mesa-libgbm: required by the bundled Electron/Chromium for GPU acceleration.
Requires:       xdg-utils
Requires:       libnotify
Requires:       libXScrnSaver
Requires:       libXtst
Requires:       libuuid
Requires:       libsecret
Requires:       mesa-libgbm
Requires:       at-spi2-core
Requires:       dbus
Requires:       alsa-lib
Requires:       nss
Requires:       gtk3
Requires:       libX11
Requires:       libXfixes
Requires:       libXrandr
Requires:       libXrender
Requires:       libXi
Requires:       libXcomposite
Requires:       libXdamage
Requires:       libXcursor
Requires:       libdrm

# The Debian rewrap ships the same application files.
Conflicts:      chatgpt-desktop

%description
ChatGPT is an AI assistant from OpenAI that combines ChatGPT, ChatGPT Work,
and Codex in one native desktop application. This package rewraps the
upstream prebuilt Linux RPM for Fedora.

%prep
# Verify the vendored RPM against the digest the sweep pins in %%global digest.
# The expected digest is pinned by the sweep; 'auto' means the sweep will
# populate it. If the sweep cannot fetch a digest (upstream publishes none),
# it writes 'none' and the check is skipped.
if [ '%{digest}' != 'none' ] && [ '%{digest}' != 'auto' ]; then
    actual="$(sha256sum %{_sourcedir}/chatgpt-%{upstream_version}-1.x86_64.rpm | cut -d' ' -f1)"
    if [ "$actual" != '%{digest}' ]; then
        echo "chatgpt: sha256 mismatch (expected %{digest}, got $actual)" >&2
        exit 1
    fi
    echo "chatgpt: sha256 verified"
fi

# Unpack the upstream RPM
rpm2cpio %{SOURCE0} | cpio -idmu

# The upstream RPM includes LICENSE and LICENSES.chromium.html under
# /usr/lib/chatgpt/. Use the LICENSE file as the package license.
cp usr/lib/chatgpt/LICENSE LICENSE

%build
# Nothing to compile: the prebuilt upstream binary is unpacked in %%prep.
# The section exists so rpm's build hooks (e.g. macro-injected steps) run.

%install
cp -a usr %{buildroot}/
# upstream RPM may have etc/ (systemd units, etc.); copy if present
[ -d etc ] && cp -a etc %{buildroot}/ || :

# Install the curated AppStream metainfo (overwrites upstream's if present)
install -Dm0644 %{SOURCE1} %{buildroot}%{_metainfodir}/com.openai.chatgpt.metainfo.xml

# The upstream RPM installs /usr/bin/chatgpt as a wrapper script that execs
# /usr/lib/chatgpt/ChatGPT. It's already on PATH; no extra symlink needed.

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/chatgpt.desktop
appstreamcli validate --no-net %{buildroot}%{_metainfodir}/com.openai.chatgpt.metainfo.xml

%files
%license LICENSE
/usr/bin/chatgpt
/usr/lib/chatgpt/
/usr/share/applications/chatgpt.desktop
/usr/share/metainfo/com.openai.chatgpt.metainfo.xml
/usr/share/icons/hicolor/*/apps/chatgpt.png

%changelog
* Mon Oct 26 2026 halcyon-autoupdate <aahsnr041@proton.me> - 26.1021.22027-2
- Conflict with chatgpt-desktop (the Debian rewrap installs the same files)

* Sun Oct 25 2026 halcyon-autoupdate <aahsnr041@proton.me> - 26.1021.22027-1
- Initial packaging of OpenAI ChatGPT desktop app from upstream RPM
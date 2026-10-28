# Vendor rewrap of OpenAI's official ChatGPT desktop RPM (x86_64 only).
# The upstream RPM is fetched at SRPM-build time (Source0) and unpacked in
# %%prep with rpm2cpio; no build step. The version, the upstream release
# number and the RPM sha256 come from OpenAI's own yum repodata
# (ci/sweep/custom.py:custom_chatgpt).
#
# The upstream payload is packaged as shipped (launcher, desktop file,
# AppStream metadata). Not packaged: upstream's /etc machinery (AppArmor
# profile, GPG keys and the yum.repos.d drop-in of upstream's self-hosted
# repository) and its maintainer scripts, which only manage that repository.
# The one change to the payload is dropping the native prebuilds for other
# platforms (see %%install).
#
# Prebuilt foreign binary: no build-id or debuginfo can be produced, so the
# debug package is disabled and the brp hooks are emptied to keep the payload
# byte-identical to the upstream blob.
%global debug_package %{nil}
%global _build_id_links none
%global __os_install_post %{nil}

# NOTE: %%global debug_package %%{nil} is what makes the default ELF-rewriting
# brp hooks run, not what skips them — Fedora's %%__os_install_post gates
# brp-strip / brp-strip-comment-note on %%__debug_package being *undefined*.
# With them in place every ELF file in the bundle gets rewritten, so the
# packaged payload stops being byte-identical to the upstream blob.
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
# same; unset it to keep byte-identity.
%global __brp_mangle_shebangs %{nil}

# add-determinism's brp hook would regenerate build-id links and otherwise
# normalize the payload. The blob must ship byte-identical.
%undefine __brp_add_determinism

# Dependency generation for a private bundle. The Electron/Chromium libs under
# /usr/lib/chatgpt carry SONAMEs, so the generator would advertise them as
# system providers; with this repo at priority=1 that would shadow Fedora's
# real packages, so Provides from the bundle are suppressed. Requires follow
# suit: the bundled libs nothing in Fedora provides (Chromium's ffmpeg, vulkan
# loader, EGL/GLES and swiftshader, and sharp's libvips) are dropped, and so
# are the Requires of the optional Qt5/Qt6 platform-theme shims, which would
# otherwise pull the whole Qt stack onto every install. Brackets, not
# backslashes, escape the regex metacharacters: rpm consumes backslashes while
# expanding the macro, which leaves a silently-ignored or loose regex.
%global __provides_exclude_from ^/usr/lib/chatgpt/
%global __requires_exclude_from ^/usr/lib/chatgpt/libqt[56]_shim[.]so$
%global __requires_exclude ^libffmpeg[.]so|^libvulkan[.]so[.]1|^libEGL[.]so|^libGLESv2[.]so|^libvk_swiftshader[.]so|^libvips-cpp[.]so

# Pinned by the sweep from the upstream repodata; 'none' skips the check.
%global digest dfc857b549c68a90900ef7eebae93a1d89c09c7cb634dd260b2b17c0bd3ee562

# the upstream RPM's own release number, kept in sync by the sweep (it is
# part of the pool filename, not of our package NVR)
%global upstream_rel 1

Name:           chatgpt
Version:        26.1023.51421
Release:        1%{?dist}
Summary:        ChatGPT by OpenAI — official Linux desktop app
License:        LicenseRef-Proprietary
URL:            https://chatgpt.com/download
#!RemoteAsset
Source0:        https://persistent.oaistatic.com/codex-app-prod/linux/rpm/x86_64/chatgpt-%{version}-%{upstream_rel}.x86_64.rpm

ExclusiveArch:  x86_64

# This package replaces the earlier chatgpt-desktop rewrap.
Obsoletes:      chatgpt-desktop < 26.1021.22027-5

BuildRequires:  appstream
BuildRequires:  coreutils
BuildRequires:  cpio
BuildRequires:  desktop-file-utils
BuildRequires:  findutils

# Runtime-only deps the ELF generator cannot see; linked libraries are
# auto-detected from DT_NEEDED and deliberately not repeated.
# - xdg-utils: the app shells out to xdg-open/xdg-settings.
# - libsecret: Electron uses it for keyring integration.
# - libnotify, libXScrnSaver: loaded indirectly via Electron.
# - libusb1, tpm2-tss: the upstream RPM requires libusb-1.0 and libtss2-esys.
# - xz: the upstream RPM requires xz (the bundled Codex uses it).
# - glib2: provides /usr/bin/gio, used by the app's desktop integration.
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
Requires:       libusb1
Requires:       tpm2-tss
Requires:       xz
Requires:       glib2

Recommends:     git

%description
ChatGPT desktop application for Linux (ChatGPT, ChatGPT Work and Codex),
repackaged from OpenAI's official RPM.

%prep
# Verify the vendored RPM against the digest the sweep pins in %%global digest.
# 'none' skips the check.
if [ '%{digest}' != 'none' ]; then
    actual="$(sha256sum %{SOURCE0} | cut -d' ' -f1)"
    if [ "$actual" != '%{digest}' ]; then
        echo "chatgpt: sha256 mismatch (expected %{digest}, got $actual)" >&2
        exit 1
    fi
    echo "chatgpt: sha256 verified"
fi

# Unpack the upstream RPM
rpm2cpio %{SOURCE0} | cpio -idmu

# The upstream RPM ships the bundled Electron runtime's license in the app
# directory; it is the package's license file.
cp usr/lib/chatgpt/LICENSE LICENSE

%build
# Nothing to compile: the prebuilt upstream payload is unpacked in %%prep.

%install
# Only usr/ is copied, so upstream's /etc (see the header) is never packaged.
cp -a usr %{buildroot}/

# The Debian-style doc tree is a copy of the license kept above, and its
# unclaimed files would fail the unpackaged-files check.
rm -rf %{buildroot}%{_datadir}/doc/chatgpt

# The node-hid and serialport prebuild trees ship every platform's native
# module — macOS, Windows, Android, ARM, 32-bit and musl. Only the glibc
# x86_64 one can load here; the rest are dead weight whose ELF files would
# otherwise add 32-bit and foreign-libc Requires to the package.
find %{buildroot}/usr/lib/chatgpt/resources/app.asar.unpacked -type d -name prebuilds \
    -exec sh -c 'cd "$1" && for d in *; do case "$d" in HID-linux-x64|HID_hidraw-linux-x64|linux-x64) ;; *) rm -rf -- "$d" ;; esac; done' sh {} \;
find %{buildroot}/usr/lib/chatgpt/resources/app.asar.unpacked -name 'node.napi.musl.node' -delete

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/chatgpt.desktop
appstreamcli validate --no-net %{buildroot}%{_metainfodir}/com.openai.chatgpt.metainfo.xml

%files
%license LICENSE
/usr/bin/chatgpt
/usr/lib/chatgpt/
%{_datadir}/applications/chatgpt.desktop
%{_metainfodir}/com.openai.chatgpt.metainfo.xml
%{_datadir}/swcatalog/xml/com.openai.chatgpt.xml
%{_datadir}/pixmaps/chatgpt.png

%changelog
* Tue Oct 27 2026 halcyon-linux <aahsnr041@proton.me> - 26.1021.22027-1
- Rename chatgpt-desktop to chatgpt, the name OpenAI ships, and package the
  upstream payload as shipped (upstream launcher and AppStream metadata
  replace our flags-file launcher and curated metainfo); Obsoletes
  chatgpt-desktop
- Drop the native prebuilds of other platforms from the bundle; their 32-bit
  and foreign-libc ELF files made dnf pull glibc/libstdc++/libusb1/systemd-libs
  i686 into the transaction
- Exclude the optional Qt5/Qt6 shims from the dependency generator so the Qt
  stack is no longer pulled in, and replace the long soname blacklist with
  bundle-scoped exclusions

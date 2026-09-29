# Ported from github.com/anudeepd/bitwarden-fedora-copr-ci (specs/bitwarden.spec)
# on 2026-09-22 and adapted to this repo's pipeline: Source0/1 are
# fetched by mock at SRPM-build time, Source2 is a repo file, and nothing is
# downloaded in %prep. The release-NVR/force_build commentary of the upstream
# CI repo does not apply here (the sweep bumps Version and every publish
# carries a new NVR).
#
# Prebuilt foreign binary: no build-id or debuginfo can be produced, so the
# debug package is disabled. The binary ships as-is from the release RPM.
%global debug_package %{nil}
%global _build_id_links none

# NOTE (verified by local rpmbuild of 2026.8.0): %%global debug_package %%{nil}
# is what makes the default ELF-rewriting brp hooks run, not what skips them
# — Fedora's %%__os_install_post gates brp-strip / brp-strip-comment-note on
# %%__debug_package being *undefined*. With them in place every ELF file in
# the bundle gets rewritten (measured: all eleven, e.g. bitwarden-app -528
# bytes, desktop_proxy -252760, libprocess_isolation.so -206256,
# libvulkan.so.1 -1685512, desktop_napi.linux-x64-gnu.node -635776), so the
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
# same, and this repo — unlike equibop — ships a shell script under /opt: the
# /opt/Bitwarden/bitwarden launcher starts with #!/bin/sh, which the hook
# rewrites to #!/usr/bin/sh (+4 bytes), breaking byte-identity on its own (it
# is the only shebang in the payload). Unset it as well.
%global __brp_mangle_shebangs %{nil}

# add-determinism's brp hook (add-det) would regenerate /usr/lib/.build-id
# links from the blob's ELF build-id notes and otherwise normalize the
# payload. The blob must ship byte-identical, so unset the hook.
%undefine __brp_add_determinism

# The bundled Chromium libs under /opt/Bitwarden carry SONAMEs, so the
# dependency generator would advertise them as system providers
# (e.g. libvulkan.so.1). They are private to the bundle (resolved via the
# $ORIGIN RPATH on bitwarden-app, not the system loader path), so suppress
# Provides from /opt.
%global __provides_exclude_from ^/opt/Bitwarden/
# bitwarden-app links the bundled libffmpeg.so (found via its $ORIGIN
# RPATH). Nothing in Fedora provides it, and the bundle satisfies it
# internally, so exclude it. The generated require string carries the arch
# qualifier (libffmpeg.so()(64bit)), hence the prefix match without $.
# Every other DT_NEEDED entry is a system library and stays auto-detected.
%global __requires_exclude ^libffmpeg\.so

Name:           bitwarden
Version:	2026.9.0
Release:        1%{?dist}
Summary:        A secure and free password manager for all of your devices
License:        GPL-3.0-only
URL:            https://bitwarden.com
ExclusiveArch:  x86_64

#!RemoteAsset
Source0:        https://github.com/bitwarden/clients/releases/download/desktop-v%{version}/Bitwarden-%{version}-x86_64.rpm
# Upstream prebuilt RPM ships no GPL text (only Electron/Chromium notices
# under /opt). mock fetches LICENSE_GPL.txt (Source1, pinned to the release
# tag) at SRPM-build time, so the packaged license always matches the
# packaged version. The desktop sources default to GPL-3.0 per the repo's
# LICENSE.txt ("GPL-3.0 unless the header specifies another license";
# Bitwarden-licensed files live only in /bitwarden_license).
#!RemoteAsset
Source1:        https://raw.githubusercontent.com/bitwarden/clients/desktop-v%{version}/LICENSE_GPL.txt
# Upstream ships no AppStream metadata at all, so this repo ships a curated
# file under the RDNS id com.bitwarden.desktop (the id Bitwarden itself
# uses; it matches the Icon and StartupWMClass in bitwarden.desktop).
Source2:        com.bitwarden.desktop.metainfo.xml

BuildRequires:  desktop-file-utils
BuildRequires:  appstream
BuildRequires:  cpio

# Runtime-only deps the ELF dependency generator cannot see. Everything
# linked (gtk3, nss, cups, alsa, at-spi2, dbus, ...) is auto-detected from
# DT_NEEDED and deliberately not duplicated here:
# - xdg-utils: the app shells out to xdg-open/xdg-settings.
# - libnotify, libXScrnSaver: declared by the upstream RPM; not in any
#   DT_NEEDED (loaded indirectly), kept at parity so notifications and idle
#   detection behave as upstream ships them.
# - (libXtst or libXtst6), (libuuid or libuuid1): upstream-declared with
#   distro alternatives; Fedora satisfies them via libXtst and libuuid.
Requires:       xdg-utils
Requires:       libnotify
Requires:       libXScrnSaver
Requires:       (libXtst or libXtst6)
Requires:       (libuuid or libuuid1)

%description
Bitwarden is a secure and free password manager for all of your devices.
Store, share and sync logins, cards and identities with end-to-end
encryption. This package rewraps the upstream prebuilt Linux RPM for
Fedora.

%prep
rpm2cpio %{SOURCE0} | cpio -idmu
cp %{SOURCE1} LICENSE_GPL.txt

%build
# Nothing to compile: the prebuilt upstream binary is unpacked in %%prep.
# The section exists so rpm's build hooks (e.g. macro-injected steps) run.

%install
cp -a opt %{buildroot}/
cp -a usr %{buildroot}/
install -Dm0644 %{SOURCE2} %{buildroot}%{_metainfodir}/com.bitwarden.desktop.metainfo.xml
# Upstream ships no /usr/bin entry (Exec= points at /opt directly). Add one
# symlink so `bitwarden` is on PATH. Safe by upstream's own design: the
# /opt/Bitwarden/bitwarden wrapper resolves `readlink -f "$0"` ("might be
# behind symlink") and execs the Electron binary by absolute path, so
# launching via the symlink behaves identically. The blob itself is
# untouched; this symlink is the single documented delta.
install -d %{buildroot}%{_bindir}
ln -s /opt/Bitwarden/bitwarden %{buildroot}%{_bindir}/bitwarden

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/bitwarden.desktop
appstreamcli validate --no-net %{buildroot}%{_metainfodir}/com.bitwarden.desktop.metainfo.xml

%files
%license LICENSE_GPL.txt
%{_bindir}/bitwarden
/opt/Bitwarden/
%{_datadir}/applications/bitwarden.desktop
%{_datadir}/icons/hicolor/*/apps/bitwarden.png
%{_metainfodir}/com.bitwarden.desktop.metainfo.xml

%changelog
* Sat Sep 12 2026 Anudeep D <anudeepd2@gmail.com> - 2026.8.0-2
- Keep the packaged payload byte-identical: unset Fedora's ELF-rewriting brp
  hooks (brp-strip, brp-strip-comment-note, brp-strip-lto,
  brp-strip-static-archive) which drop .comment from every bundled binary
- Also unset brp-mangle-shebangs: it rewrote the bundle's
  /opt/Bitwarden/bitwarden launcher from #!/bin/sh to #!/usr/bin/sh
* Sun Sep 06 2026 Anudeep D <anudeepd2@gmail.com> - 2026.8.0-1
- Initial Fedora repackaging of upstream prebuilt RPM

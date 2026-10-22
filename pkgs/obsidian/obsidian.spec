# Ported from the Arch Linux obsidian package
# (gitlab.archlinux.org/archlinux/packaging/packages/obsidian) on 2026-09-22
# and adapted to Fedora + this repo's Copr pipeline:
#   * Arch runs the app with the SYSTEM electron (depends: electron43) and
#     installs only resources/ to the libdir. Fedora ships no Electron
#     package, so the official tarball's bundled Electron runtime ships too —
#     the full tarball goes into the package's private libdir and the
#     launcher execs the bundled binary; the launcher's user-flags mechanism
#     is Arch's.
#   * the launcher must not hardcode the runtime path: Arch's /usr/lib/obsidian
#     does not exist on Fedora, whose 64-bit libdir is /usr/lib64. The spec
#     substitutes the real libdir into the launcher at build time.
#   * sources are fetched at SRPM-build time (Source0/1/2 by mock); the
#     tarball's sha256 is verified in %prep against the digest upstream
#     publishes on the GitHub release (Arch's makepkg checksum equivalent) —
#     the expected digest is pinned in %%global digest by the sweep, empty
#     when upstream publishes none (also resolves the old deferred blocker).
#   * options=(!strip) -> debug_package/__os_install_post nil.
%global             full_name obsidian
%global             digest 1bc6547c889d7d02c3f2c5b55884cba14980bfac4ada32c0bdc6ec6db542aaf8
%global             debug_package %{nil}
%global _build_id_links none
%global             __os_install_post %{nil}

Name:               obsidian
Version:            1.14.5
Release:            1%{?dist}
Summary:            A powerful knowledge base that works on top of a local folder of plain text Markdown files
License:            LicenseRef-Obsidian
URL:                https://obsidian.md
#!RemoteAsset
Source0:            https://github.com/obsidianmd/obsidian-releases/releases/download/v%{version}/obsidian-%{version}.tar.gz
Source1:            %{full_name}.sh
Source2:            %{full_name}.desktop
Source3:            LICENSE-Obsidian

ExclusiveArch:      x86_64

# Electron runtime deps. The automatic ELF deps cover the linked sonames
# (gtk3, nss, atk, ...); these are the ones the binary only dlopen()s, plus
# the desktop bits — the same set the upstream .deb lists and the other
# electron rewraps in this repo declare.
Requires:           gtk3
Requires:           nss
Requires:           libXScrnSaver
Requires:           libXtst
Requires:           libuuid
Requires:           at-spi2-core
Requires:           libnotify
Requires:           libsecret
Requires:           xdg-utils

%description
Obsidian is a powerful knowledge base that works on top of a local folder of
plain text Markdown files. You can add custom permanent flags for Obsidian in
.config/obsidian/user-flags.conf (the Arch packager's launcher mechanism).

%prep
# the tarball's top directory is obsidian-<version> (the archive dir name
# derives from the upstream layout — re-check it when upstream re-releases)
%autosetup -n obsidian-%{version}

# verify the vendored tarball against the digest upstream publishes on the
# release (Arch makepkg checksum; the sweep pins %%global digest, 'none'
# when upstream publishes none).
if [ '%{digest}' != 'none' ]; then
    actual="$(sha256sum %{_sourcedir}/obsidian-%{version}.tar.gz | cut -d' ' -f1)"
    if [ "$actual" != '%{digest}' ]; then
        echo "obsidian: sha256 mismatch (expected %{digest}, got $actual)" >&2
        exit 1
    fi
    echo "obsidian: sha256 verified"
fi

%install
%__rm -rf %{buildroot}

# Arch installs only resources/ (system electron); the bundled runtime ships
# here, so the whole tarball lands in the package's private libdir
install -dm755 %{buildroot}%{_libdir}/obsidian
%__cp -a . %{buildroot}%{_libdir}/obsidian/

# the launcher execs the bundled runtime: that path is the package's private
# libdir, which is NOT the Arch one on Fedora — substitute it here
install -dm755 %{buildroot}%{_bindir}
sed -e 's|@OBSIDIAN_LIBDIR@|%{_libdir}/obsidian|g' %{SOURCE1} \
    > %{buildroot}%{_bindir}/obsidian
chmod 755 %{buildroot}%{_bindir}/obsidian

%__install -Dm644 %{SOURCE2} -t %{buildroot}%{_datadir}/applications

# Arch: install -Dm644 resources/icon.png -> hicolor 512x512
# (source of the icon is the buildroot copy made above; the system
# libdir never exists inside the mock sandbox)
%__install -Dm644 %{buildroot}%{_libdir}/obsidian/resources/icon.png \
    %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/%{full_name}.png

%__install -Dm644 %{SOURCE3} -t %{buildroot}%{_licensedir}/%{full_name}

%files
%{_bindir}/obsidian
%{_libdir}/obsidian/
%{_datadir}/applications/%{full_name}.desktop
%{_datadir}/icons/hicolor/512x512/apps/%{full_name}.png
%{_licensedir}/obsidian/LICENSE-Obsidian

%changelog
* Thu Oct 22 2026 halcyon-autoupdate <aahsnr041@proton.me> - 1.14.4-2
- fix the launcher: it execed the Arch path (/usr/lib/obsidian/obsidian),
  which does not exist on Fedora (the 64-bit libdir is /usr/lib64); the
  private libdir is now substituted into the launcher at build time
- unpack the tarball with autosetup -n instead of the double-nesting setup
- declare the Electron runtime deps the dlopen'ed sonames need
* Sat Sep 26 2026 halcyon-autoupdate <aahsnr041@proton.me> - 1.13.7-1
- changelog retro-added (the spec predates the written-changelog rule)

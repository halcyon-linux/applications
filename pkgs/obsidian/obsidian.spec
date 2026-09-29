# Ported from the Arch Linux obsidian package
# (gitlab.archlinux.org/archlinux/packaging/packages/obsidian) on 2026-09-22
# and adapted to Fedora + this repo's Copr pipeline:
#   * Arch runs the app with the SYSTEM electron (depends: electron43) and
#     installs only resources/ to /usr/lib/obsidian. Fedora ships no Electron
#     package, so the official tarball's bundled Electron runtime ships too —
#     the full tarball goes to /usr/lib/obsidian and the launcher execs the
#     bundled binary; the launcher's user-flags mechanism is Arch's.
#   * sources are fetched at SRPM-build time (Source0/1/2 by mock); the
#     tarball's sha256 is verified in %prep against the digest upstream
#     publishes on the GitHub release (Arch's makepkg checksum equivalent) —
#     the expected digest is pinned in %%global digest by update.rhai, empty
#     when upstream publishes none (also resolves the old deferred blocker).
#   * options=(!strip) -> debug_package/__os_install_post nil.
%global             full_name obsidian
%global             digest d3cbe375cbfa4024db1910b98191649f4134c5c48aee5e60b6e7713987dcdb28
%global             debug_package %{nil}
%global _build_id_links none
%global             __os_install_post %{nil}

Name:               obsidian
Version:            1.13.7
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

%description
Obsidian is a powerful knowledge base that works on top of a local folder of
plain text Markdown files. You can add custom permanent flags for Obsidian in
.config/obsidian/user-flags.conf (the Arch packager's launcher mechanism).

%prep
%setup -q -c -T -a 0

# verify the vendored tarball against the digest upstream publishes on the
# release (Arch makepkg checksum; update.rhai pins %%global digest, 'none'
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
# here, so the whole tarball lands in /usr/lib/obsidian
install -dm755 %{buildroot}%{_libdir}/obsidian
%__cp -r obsidian-%{version}/* %{buildroot}%{_libdir}/obsidian/

%__install -Dm755 %{SOURCE1} %{buildroot}%{_bindir}/obsidian

%__install -Dm644 %{SOURCE2} -t %{buildroot}%{_datadir}/applications

# Arch: install -Dm644 resources/icon.png -> hicolor 512x512
# (source of the icon is the buildroot copy made above; the system
# %{_libdir} never exists inside the mock sandbox)
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
* Sat Sep 26 2026 halcyon-autoupdate <aahsnr041@proton.me> - 1.13.7-1
- changelog retro-added (the spec predates the written-changelog rule)

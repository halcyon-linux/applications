# Vendor rewrap of AppFlowy's official RPM — upstream publishes a self-contained
# RPM at each GitHub release (the same Flutter bundle as their tarball, .deb and
# AppImage; the RPM additionally carries the desktop file, icon and metainfo, so
# one digest-pinned asset is everything). The release tag is the version
# (e.g. 0.14.11) and the RPM filename embeds it. The sweep's custom feed
# re-pins the RPM's sha256 on every bump.
#
# The bundle is built on Ubuntu 22.04: ~300 private libraries (ffmpeg, mpv,
# openssl, ...) sit in lib/ behind the binary's $ORIGIN/lib RPATH and only
# change when upstream cuts a release.
%global             debug_package %{nil}
%global _build_id_links none
%global             __os_install_post %{nil}

# The bundled libraries are private to the bundle, so they are not advertised
# as system Provides (priority=1 would let them shadow Fedora's packages) and
# the Requires they satisfy for each other are dropped as well. The latter is a
# lazy %%define, not %%global: the exclusion is built from the buildroot's lib/
# listing when rpm scans for Requires, so a release that adds or drops a bundled
# library needs no spec edit. Brackets, not backslashes, escape regex
# metacharacters: rpm consumes backslashes while expanding the macro.
%global __provides_exclude_from ^%{_libdir}/appflowy/
%define __requires_exclude ^(%(ls %{buildroot}%{_libdir}/appflowy/lib | grep '^lib' | sed -E 's/[.]so.*//; s/[.]/[.]/g' | sort -u | paste -sd'|'))[.]so

Name:           appflowy
Version:        0.14.11
Release:        1%{?dist}
Summary:        AppFlowy — open-source Notion alternative for notes and project management
License:        AGPL-3.0-only
URL:            https://www.appflowy.io/
# The RPM sha256 digest is pinned by the sweep (or 'none' when upstream
# publishes no digest). Verified in %%prep.
%global digest 9de50e579657620cc7e72d7fc8105789184971befd4c65a97ff879b0caad6418
Source0:        https://github.com/AppFlowy-IO/AppFlowy/releases/download/%{version}/AppFlowy-%{version}-linux-x86_64.rpm
Source1:        https://raw.githubusercontent.com/AppFlowy-IO/AppFlowy/%{version}/LICENSE

ExclusiveArch:  x86_64

%description
AppFlowy is an open-source alternative to Notion for notes, tasks, and project
management. This package rewraps the official RPM published by the AppFlowy
project at each GitHub release.

%prep
%setup -q -c -T
rpm2cpio %{SOURCE0} | cpio -idmu

# Verify the RPM against the digest upstream publishes on the release
# (skipped when upstream publishes none — %%global digest is 'none' then).
if [ '%{digest}' != 'none' ]; then
    actual="$(sha256sum %{SOURCE0} | cut -d' ' -f1)"
    if [ "$actual" != '%{digest}' ]; then
        echo "appflowy: sha256 mismatch (expected %{digest}, got $actual)" >&2
        exit 1
    fi
    echo "appflowy: sha256 verified"
fi

%install
%__rm -rf %{buildroot}

# The vendor RPM installs the Flutter bundle to /usr/lib/AppFlowy — move it to
# our private libdir (the binary finds data/ and lib/ relative to itself)
install -dm755 %{buildroot}%{_libdir}
mv usr/lib/AppFlowy %{buildroot}%{_libdir}/appflowy

# System launcher in /usr/bin
mkdir -p %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/appflowy <<'EOF'
#!/bin/sh
exec %{_libdir}/appflowy/AppFlowy "$@"
EOF
chmod 755 %{buildroot}%{_bindir}/appflowy

# Desktop file under the id the metainfo's <launchable> names, pointed at the
# launcher (the vendor one hardcodes /usr/lib/AppFlowy and an absolute icon path)
# and a registered category (it ships the invalid "Productivity")
sed -e 's|^Exec=.*|Exec=appflowy %U|' -e 's|^Icon=.*|Icon=appflowy|' \
    -e 's|^Categories=.*|Categories=Office;ProjectManagement;|' \
    usr/share/applications/AppFlowy.desktop > io.appflowy.AppFlowy.desktop
%__install -Dm644 io.appflowy.AppFlowy.desktop \
    %{buildroot}%{_datadir}/applications/io.appflowy.AppFlowy.desktop

%__install -Dm644 usr/share/icons/hicolor/scalable/apps/appflowy.svg \
    %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/appflowy.svg
%__install -Dm644 usr/share/metainfo/io.appflowy.AppFlowy.metainfo.xml \
    %{buildroot}%{_metainfodir}/io.appflowy.AppFlowy.metainfo.xml

# License
%__install -Dm644 %{SOURCE1} %{buildroot}%{_licensedir}/appflowy/LICENSE

%files
%{_bindir}/appflowy
%{_libdir}/appflowy/
%{_datadir}/applications/io.appflowy.AppFlowy.desktop
%{_datadir}/icons/hicolor/scalable/apps/appflowy.svg
%{_metainfodir}/io.appflowy.AppFlowy.metainfo.xml
%{_licensedir}/appflowy/LICENSE

%changelog
* Tue Oct 27 2026 halcyon-linux <aahsnr041@proton.me> - 0.14.11-1
- Initial package: vendor RPM rewrap of AppFlowy official RPM

# Vendor rewrap of AppFlowy's official RPM — upstream publishes a self-contained
# RPM at each GitHub release. The tag is the version (e.g. 0.14.11), and the
# RPM filename embeds it (AppFlowy-<version>-linux-x86_64.rpm). The sweep uses
# the standard github-release feed.
%global             debug_package %{nil}
%global _build_id_links none
%global             __os_install_post %{nil}

# The bundled libraries carry SONAMEs; exclude them from system Provides.
%global __provides_exclude_from ^%{_libdir}/appflowy/
# The Requires on the bundled Chromium libs nothing in Fedora provides are
# dropped as well. Brackets, not backslashes, escape regex metacharacters:
# rpm consumes backslashes while expanding the macro.
%global __requires_exclude ^libffmpeg[.]so|^libvulkan[.]so[.]1|^libEGL[.]so|^libGLESv2[.]so|^libvk_swiftshader[.]so

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

# Vendor RPM deps (Electron runtime)
Requires:       gtk3
Requires:       nss
Requires:       libXScrnSaver
Requires:       libXtst
Requires:       libuuid
Requires:       at-spi2-core
Requires:       libnotify
Requires:       libsecret
Requires:       xdg-utils

%description
AppFlowy is an open-source alternative to Notion for notes, tasks, and project
management. This package rewraps the official RPM published by the AppFlowy
project at each GitHub release.

%prep
%setup -q -c -T
rpm2cpio %{_sourcedir}/AppFlowy-%{version}-linux-x86_64.rpm | cpio -idmu

# Verify the RPM against the digest upstream publishes on the release
# (skipped when upstream publishes none — %%global digest is 'none' then).
if [ '%{digest}' != 'none' ]; then
    actual="$(sha256sum %{_sourcedir}/AppFlowy-%{version}-linux-x86_64.rpm | cut -d' ' -f1)"
    if [ "$actual" != '%{digest}' ]; then
        echo "appflowy: sha256 mismatch (expected %{digest}, got $actual)" >&2
        exit 1
    fi
    echo "appflowy: sha256 verified"
fi

%install
%__rm -rf %{buildroot}

# The vendor RPM installs to /opt/AppFlowy — move it to our private libdir
install -dm755 %{buildroot}%{_libdir}
mv opt/AppFlowy %{buildroot}%{_libdir}/appflowy

# System launcher in /usr/bin
mkdir -p %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/appflowy <<'EOF'
#!/bin/sh
exec %{_libdir}/appflowy/appflowy "$@"
EOF
chmod 755 %{buildroot}%{_bindir}/appflowy

# Desktop file (vendor provides one at /usr/share/applications/appflowy.desktop)
%__install -Dm644 usr/share/applications/appflowy.desktop \
    %{buildroot}%{_datadir}/applications/appflowy.desktop

# Icons (vendor provides hicolor icons)
cp -a usr/share/icons %{buildroot}%{_datadir}/icons

# License
%__install -Dm644 %{SOURCE1} %{buildroot}%{_licensedir}/appflowy/LICENSE

%files
%{_bindir}/appflowy
%{_libdir}/appflowy/
%{_datadir}/applications/appflowy.desktop
%{_datadir}/icons/hicolor/*/apps/appflowy.png
%{_licensedir}/appflowy/LICENSE

%changelog
* Tue Oct 27 2026 halcyon-linux <aahsnr041@proton.me> - 0.14.11-1
- Initial package: vendor RPM rewrap of AppFlowy official RPM
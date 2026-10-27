# Repackaged from the vendor RPM (Ferdium-linux-x86_64.rpm) on the ticktick
# pattern (2026-09-26). The vendor payload already carries the desktop file
# and the full hicolor icon set, so the rewrap is thin:
#   * /usr/bin/ferdium launcher added, vendor Exec line rewritten to it
#   * Electron/Chromium license texts move to /usr/share/licenses/ferdium,
#     the app's own Apache-2.0 text rides in as Source1
#   * chrome-sandbox gets the SUID bit Electron wants for the setuid
#     sandbox path
#   * the vendor (a or b) alternates mapped to Fedora package names
# Version is swept from the ferdium-app GitHub releases (tags 1:1 with
# releases).
# The bundled libraries under /opt/Ferdium carry SONAMEs, so the dependency
# generator would advertise them as system providers. This repo is consumed at
# priority=1, so those Provides would shadow Fedora's own packages in any
# dependency resolution; they are private to the bundle.
# The Requires on the bundled Chromium libs nothing in Fedora provides are
# dropped as well. Brackets, not backslashes, escape regex metacharacters:
# rpm consumes backslashes while expanding the macro.
%global __provides_exclude_from ^/opt/Ferdium/
%global __requires_exclude ^libffmpeg[.]so|^libvulkan[.]so[.]1|^libEGL[.]so|^libGLESv2[.]so|^libvk_swiftshader[.]so

Name:           ferdium
Version:        7.2.3
Release:        2%{?dist}
Summary:        Messaging app bringing all your services into one installable
License:        Apache-2.0
URL:            https://ferdium.org/
#!RemoteAsset
Source0:        https://github.com/ferdium/ferdium-app/releases/download/v%{version}/Ferdium-linux-%{version}-x86_64.rpm
Source1:        https://raw.githubusercontent.com/ferdium/ferdium-app/develop/LICENSE.md

ExclusiveArch:  x86_64

# the automatic check stage validates the packaged .desktop files
BuildRequires:  cpio
BuildRequires:  desktop-file-utils

# vendor Requires, alternates resolved to Fedora package names
Requires:       gtk3
Requires:       nss
Requires:       libXScrnSaver
Requires:       libXtst
Requires:       libuuid
Requires:       at-spi2-core
Requires:       libnotify
Requires:       xdg-utils

%define debug_package %{nil}
%global _build_id_links none
%global __os_install_post %{nil}
# the payload must stay byte-identical to the vendor blob
%global __brp_strip %{nil}
%global __brp_strip_comment_note %{nil}
%global __brp_mangle_shebangs %{nil}

%description
Ferdium is a messaging application that combines chat and messaging
services into one application (successor of Ferdi and Franz). Repackaged
from the vendor RPM with a system launcher in /usr/bin/ferdium and the
license texts consolidated under /usr/share/licenses/ferdium.

%prep
%setup -q -c -T
rpm2cpio %{_sourcedir}/Ferdium-linux-%{version}-x86_64.rpm | cpio -idmu

%install
install -dm755 %{buildroot}/opt %{buildroot}%{_bindir} \
    %{buildroot}%{_datadir}/applications %{buildroot}%{_licensedir}/%{name}
cp -a opt/Ferdium %{buildroot}/opt/
cp -a usr/share/icons %{buildroot}%{_datadir}/icons

# point the vendor desktop file at the system launcher
sed -i 's|^Exec=.*|Exec=/usr/bin/ferdium %U|' \
    usr/share/applications/ferdium.desktop
install -pm644 usr/share/applications/ferdium.desktop \
    %{buildroot}%{_datadir}/applications/ferdium.desktop

# system launcher
cat > %{buildroot}%{_bindir}/ferdium <<'EOF'
#!/bin/sh
exec /opt/Ferdium/ferdium "$@"
EOF
chmod 755 %{buildroot}%{_bindir}/ferdium

# vendor license files under /usr/share/licenses/ferdium
install -pm644 %{SOURCE1} %{buildroot}%{_licensedir}/%{name}/LICENSE
mv %{buildroot}/opt/Ferdium/LICENSE.electron.txt \
    %{buildroot}%{_licensedir}/%{name}/LICENSE.electron.txt
mv %{buildroot}/opt/Ferdium/LICENSES.chromium.html \
    %{buildroot}%{_licensedir}/%{name}/LICENSES.chromium.html

# SUID chrome-sandbox for the setuid sandbox path
chmod 4755 %{buildroot}/opt/Ferdium/chrome-sandbox

%files
/opt/Ferdium/
%{_bindir}/ferdium
%{_datadir}/applications/ferdium.desktop
%{_datadir}/icons/hicolor/*/apps/ferdium.png
%{_licensedir}/ferdium/

%changelog
* Tue Oct 27 2026 halcyon-linux <aahsnr041@proton.me> - 7.2.3-2
- Stop advertising the bundled libraries as system Provides (__provides_exclude_from): with the
  repo at priority=1 they shadowed Fedora's packages and were pulled into unrelated installs;
  drop the matching Requires on the bundled Chromium libs

* Sat Sep 26 2026 halcyon-autobuild - 7.2.3-1
- initial package: vendor RPM rewrap on the ticktick pattern
- /usr/bin/ferdium launcher, SUID chrome-sandbox, license consolidation

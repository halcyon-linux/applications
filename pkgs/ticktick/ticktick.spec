# Ported from the AUR PKGBUILD (aur.archlinux.org, h=ticktick) on 2026-09-22
# and adapted to RPM idioms:
#   * payload is the official vendor .deb (like the PKGBUILD — it carries the
#     desktop file and hicolor icons that the vendor's own RPM lacks),
#     unpacked with ar + tar instead of bsdtar
#   * the launcher script (ticktick.sh) lands in /usr/bin/ticktick, the
#     vendor Exec line is rewritten to it, the Electron/Chromium license
#     files move to /usr/share/licenses/ticktick, chrome-sandbox gets the
#     SUID bit the PKGBUILD sets
#   * Arch's depends= mapped to Fedora package names
#   * the vendor binaries ship as-is: no stripping, no debuginfo (the AUR
#     equivalent is options=(!strip))
# The version source is the AUR package itself (the AUR RPC API) — the AUR
# maintainer tracks upstream; there is still no first-party version feed.
Name:           ticktick
Version:        8.0.11
Release:        1%{?dist}
Summary:        Official desktop application for Linux
License:        LicenseRef-Proprietary
URL:            https://ticktick.com/download
#!RemoteAsset
Source0:        https://d2atcrkye2ik4e.cloudfront.net/download/linux/linux_deb_x64/ticktick-%{version}-amd64.deb
Source1:        ticktick.sh
Source2:        LICENSE

ExclusiveArch:  x86_64

# AUR depends= mapped to Fedora package names
Requires:       gtk3
Requires:       libnotify
Requires:       nss
Requires:       libXScrnSaver
Requires:       libXtst
Requires:       xdg-utils
Requires:       at-spi2-core
Requires:       libappindicator-gtk3
Requires:       libsecret

%define debug_package %{nil}
%global _build_id_links none
%global __os_install_post %{nil}
# the payload must stay byte-identical to the vendor blob
%global __brp_strip %{nil}
%global __brp_strip_comment_note %{nil}
%global __brp_mangle_shebangs %{nil}

%description
Official TickTick desktop client, repackaged from the vendor .deb exactly
like the AUR package: launcher script with per-user flags support in
/usr/bin/ticktick, vendor desktop file and hicolor icons, Electron and
Chromium license texts in /usr/share/licenses/ticktick.

%prep
%setup -q -c -T
# unpack the vendor .deb (ar + tar, the RPM-side equivalent of the PKGBUILD's
# makepkg deb extraction)
ar p %{_sourcedir}/ticktick-%{version}-amd64.deb data.tar.xz | tar -xJf -

%install
install -dm755 %{buildroot}/opt %{buildroot}%{_bindir} \
    %{buildroot}%{_datadir}/applications %{buildroot}%{_licensedir}/%{name}
cp -r opt/TickTick %{buildroot}/opt/

# PKGBUILD: point the vendor desktop file at the system launcher
sed -i 's|^Exec=.*|Exec=/usr/bin/ticktick --uri=%U|' \
    usr/share/applications/ticktick.desktop
install -pm644 usr/share/applications/ticktick.desktop \
    %{buildroot}%{_datadir}/applications/ticktick.desktop

# PKGBUILD: the vendor .deb ships hicolor icons; keep them
cp -r usr/share/icons %{buildroot}%{_datadir}/icons

# PKGBUILD: launch script allowing custom flags via
# ~/.config/ticktick/user-flags.conf
install -pm755 %{SOURCE1} %{buildroot}%{_bindir}/ticktick

# PKGBUILD: vendor license files under /usr/share/licenses/ticktick
install -pm644 %{SOURCE2} %{buildroot}%{_licensedir}/%{name}/LICENSE
mv %{buildroot}/opt/TickTick/LICENSE.electron.txt \
    %{buildroot}%{_licensedir}/%{name}/LICENSE.electron.txt
mv %{buildroot}/opt/TickTick/LICENSES.chromium.html \
    %{buildroot}%{_licensedir}/%{name}/LICENSES.chromium.html

# PKGBUILD: SUID chrome-sandbox for Electron 5+
chmod 4755 %{buildroot}/opt/TickTick/chrome-sandbox

%files
/opt/TickTick/
%{_bindir}/ticktick
%{_datadir}/applications/ticktick.desktop
%{_datadir}/icons/hicolor/*/apps/ticktick.png
%{_licensedir}/ticktick/

%changelog
* Tue Sep 22 2026 halcyon-autobuild - 8.0.11-1
- follow the AUR PKGBUILD: vendor .deb payload (desktop file + icons now
  included), /usr/bin/ticktick launcher with user-flags support, Electron/
  Chromium licenses relocated, SUID chrome-sandbox
- version is swept automatically from the AUR package via the AUR RPC API

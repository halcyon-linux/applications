# Google distributes the desktop app as a self-contained Linux x64 archive.
# Keep the vendor payload intact; the Arch package's depends list supplies
# the external runtime libraries while bundled-library requirements are private.
%global debug_package %{nil}
%global _build_id_links none
%global __os_install_post %{nil}
%global __provides_exclude_from ^%{_libdir}/antigravity/
# Avoid the bundled curl/OpenSSL ABI requirement seen in existing Antigravity RPM packaging.
%global __requires_exclude libcurl.*CURL_OPENSSL

Name:           antigravity
Version:        2.35.2
Release:        1%{?dist}
Summary:        Google's agentic desktop workspace
License:        LicenseRef-Proprietary
URL:            https://antigravity.google/product/antigravity-2
%global build_id 4585983447007232
#!RemoteAsset
Source0:        https://storage.googleapis.com/antigravity-public/antigravity-hub/%{version}-%{build_id}/linux-x64/Antigravity.tar.gz
Source1:        antigravity.desktop
Source2:        https://aur.archlinux.org/cgit/aur.git/plain/antigravity.png?h=antigravity&id=9c47441634aa1b7069cf1e9f22bde02a3d89f1a2

ExclusiveArch:  x86_64

BuildRequires:  desktop-file-utils

# Fedora equivalents of the upstream Antigravity package's runtime dependencies.
Requires:       alsa-lib
Requires:       at-spi2-core
Requires:       cairo
Requires:       cups-libs
Requires:       dbus-libs
Requires:       expat
Requires:       glib2
Requires:       glibc
Requires:       gtk3
Requires:       hicolor-icon-theme
Requires:       libgcc
Requires:       libX11
Requires:       libxcb
Requires:       libXcomposite
Requires:       libXdamage
Requires:       libXext
Requires:       libXfixes
Requires:       libxkbcommon
Requires:       libXrandr
Requires:       mesa-libgbm
Requires:       nspr
Requires:       nss
Requires:       pango
Requires:       systemd-libs

%description
Google Antigravity is an agentic development workspace with a Linux desktop
application. This package repackages Google's official x64 archive.

%prep
%setup -q -c -T
tar -xzf %{SOURCE0}

%install
install -dm755 %{buildroot}%{_libdir}/antigravity %{buildroot}%{_bindir}
cp -a Antigravity-*/. %{buildroot}%{_libdir}/antigravity/
ln -s %{_libdir}/antigravity/antigravity \
    %{buildroot}%{_bindir}/antigravity
install -Dm644 %{SOURCE1} \
    %{buildroot}%{_datadir}/applications/antigravity.desktop
install -Dm644 %{SOURCE2} \
    %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/antigravity.png
install -Dm644 %{buildroot}%{_libdir}/antigravity/LICENSE.electron.txt \
    %{buildroot}%{_licensedir}/antigravity/LICENSE.electron.txt
install -Dm644 %{buildroot}%{_libdir}/antigravity/LICENSES.chromium.html \
    %{buildroot}%{_licensedir}/antigravity/LICENSES.chromium.html

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/antigravity.desktop

%files
%{_bindir}/antigravity
%{_libdir}/antigravity/
%{_datadir}/applications/antigravity.desktop
%{_datadir}/icons/hicolor/512x512/apps/antigravity.png
%license %{_licensedir}/antigravity/LICENSE.electron.txt
%license %{_licensedir}/antigravity/LICENSES.chromium.html

%changelog
* Fri Nov 27 2026 halcyon-linux <aahsnr041@proton.me> - 2.35.2-1
- Initial package of Google's official Antigravity desktop app

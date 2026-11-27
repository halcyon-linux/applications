# Rewrap the official RPM and keep its resource-relative CLI layout intact.
%global digest 348a46a7bf8983ffe282f9de162fc58329594fb7944a470cdff07c098f14ca99
%global debug_package %{nil}
%global _build_id_links none
%global __os_install_post %{nil}
%global __provides_exclude_from ^/opt/Paseo/
%global __requires_exclude ^libffmpeg[.]so|^libvulkan[.]so[.]1|^libEGL[.]so|^libGLESv2[.]so|^libvk_swiftshader[.]so

Name:           paseo
Version:        0.18.1
Release:        1%{?dist}
Summary:        Desktop workspace for coding agents with remote access
License:        Apache-2.0
URL:            https://paseo.sh/
Source0:        https://github.com/getpaseo/paseo/releases/download/v%{version}/Paseo-%{version}-x86_64.rpm
Source1:        paseo.desktop
Source2:        https://raw.githubusercontent.com/getpaseo/paseo/v%{version}/LICENSE
ExclusiveArch:  x86_64
BuildRequires:  cpio
BuildRequires:  rpm
BuildRequires:  desktop-file-utils
Requires:       /bin/sh
Requires:       alsa-lib
Requires:       at-spi2-core
Requires:       gtk3
Requires:       nss
Requires:       libsecret
Requires:       libnotify
Requires:       libXScrnSaver
Requires:       libXtst
Requires:       mesa-libgbm
Requires:       xdg-utils
Requires:       hicolor-icon-theme
Requires:       git-core

%description
Paseo runs coding agents in a desktop workspace and provides access from
other machines and mobile devices. This package includes the official
desktop application and its bundled command-line launcher.

%prep
%setup -q -c -T
echo '%{digest}  %{SOURCE0}' | sha256sum -c -
rpm2cpio %{SOURCE0} > payload.cpio
cpio -idmu < payload.cpio
test -x opt/Paseo/Paseo
test -x opt/Paseo/resources/bin/paseo
test -f opt/Paseo/chrome-sandbox
test -f opt/Paseo/resources/app.asar.unpacked/dist/daemon/node-entrypoint-runner.js
# Remove the vendor update feed so package updates stay with RPM.
rm -f opt/Paseo/resources/app-update.yml

%install
install -dm755 %{buildroot}/opt %{buildroot}%{_bindir}
cp -a opt/Paseo %{buildroot}/opt/
# Record upstream's sandbox-helper mode in the RPM payload.
chmod 4755 %{buildroot}/opt/Paseo/chrome-sandbox
ln -s /opt/Paseo/Paseo %{buildroot}%{_bindir}/paseo-desktop
ln -s /opt/Paseo/resources/bin/paseo %{buildroot}%{_bindir}/paseo
install -Dm644 %{SOURCE1} %{buildroot}%{_datadir}/applications/Paseo.desktop
install -Dm644 opt/Paseo/resources/icon.png %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/paseo.png
install -Dm644 %{SOURCE2} %{buildroot}%{_licensedir}/%{name}/LICENSE

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/Paseo.desktop
test "$(stat -c '%%a' %{buildroot}/opt/Paseo/chrome-sandbox)" = 4755
test ! -e %{buildroot}/opt/Paseo/resources/app-update.yml

%files
%defattr(-,root,root,-)
/opt/Paseo/
%{_bindir}/paseo
%{_bindir}/paseo-desktop
%{_datadir}/applications/Paseo.desktop
%{_datadir}/icons/hicolor/512x512/apps/paseo.png
%license %{_licensedir}/%{name}/LICENSE

%changelog
* Sat Nov 28 2026 halcyon-linux <aahsnr041@proton.me> - 0.18.1-1
- Rewrap the official desktop RPM with bundled CLI and automatic stable updates

# Rewrap Z.ai's official Linux x64 RPM. Do not execute its scriptlets: they
# create global alternatives, change chrome-sandbox permissions, and manage
# AppArmor outside RPM ownership. The app payload remains under /opt/ZCode.
# Upstream's SHA256SUMS omits the Linux RPM, so its feed verifies publication
# before the HTTPS download but cannot pin a vendor-published digest.
%global             debug_package %{nil}
%global _build_id_links none
%global             __os_install_post %{nil}
%global __provides_exclude_from ^/opt/ZCode/
%global __requires_exclude ^libffmpeg[.]so|^libvulkan[.]so[.]1|^libvk_swiftshader[.]so

Name:           zcode
Version:        3.17.2
Release:        1%{?dist}
Summary:        Z.ai AI-assisted development environment
License:        LicenseRef-ZCode
URL:            https://zcode.z.ai/en
Source0:        https://cdn-zcode.z.ai/zcode/electron/releases/%{version}/linux-x64/ZCode-%{version}-linux-x64.rpm
Source1:        zcode.desktop

ExclusiveArch:  x86_64

BuildRequires:  cpio
BuildRequires:  desktop-file-utils

Requires:       alsa-lib
Requires:       at-spi2-core
Requires:       gtk3
Requires:       libXScrnSaver
Requires:       libXtst
Requires:       libuuid
Requires:       libnotify
Requires:       libsecret
Requires:       mesa-libgbm
Requires:       nss
Requires:       xdg-utils

%description
ZCode is Z.ai's desktop coding agent. This package rewraps the official
Linux x64 RPM without running its system-modifying scriptlets.

%prep
%setup -q -c -T
rpm2cpio %{SOURCE0} | cpio -idmu

%install
%__rm -rf %{buildroot}
install -dm755 %{buildroot}/opt %{buildroot}%{_bindir}
cp -a opt/ZCode %{buildroot}/opt/
rm -f %{buildroot}/opt/ZCode/resources/app-update.yml
ln -s /opt/ZCode/zcode %{buildroot}%{_bindir}/zcode
install -Dm644 %{SOURCE1} \
    %{buildroot}%{_datadir}/applications/zcode.desktop
install -Dm644 %{buildroot}/opt/ZCode/resources/icon_512x512.png \
    %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/zcode.png

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/zcode.desktop

%files
%{_bindir}/zcode
/opt/ZCode/
%{_datadir}/applications/zcode.desktop
%{_datadir}/icons/hicolor/512x512/apps/zcode.png

%changelog
* Fri Nov 06 2026 halcyon-linux <aahsnr041@proton.me> - 3.17.2-1
- Initial package: rewrap the official ZCode Linux x64 RPM

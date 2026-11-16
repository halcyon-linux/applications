# Rewrap the official PiChamber x86_64 RPM.
%global debug_package %{nil}
%global _build_id_links none
%global __os_install_post %{nil}
%global __provides_exclude_from ^/opt/PiChamber/
# Foreign architecture prebuilds are bundled by npm but unused on x86_64.
%global __requires_exclude_from ^/opt/PiChamber/.*(/prebuilds/linux-arm64/|/bun-pty/rust-pty/target/release/librust_pty_arm64[.]so$)
%global __requires_exclude ^libffmpeg[.]so|^libvulkan[.]so[.]1|^libEGL[.]so|^libGLESv2[.]so|^libvk_swiftshader[.]so|^libonnxruntime[.]so|^libsherpa-onnx-c-api[.]so

Name:           pichamber
Version:        1.0.7
Release:        2%{?dist}
Summary:        Desktop workspace for Pi Coding Agent
License:        MIT
URL:            https://github.com/RyderAsKing/PiChamber
Source0:        https://github.com/RyderAsKing/PiChamber/releases/download/v%{version}/PiChamber-%{version}-linux-x86_64.rpm
Source1:        https://raw.githubusercontent.com/RyderAsKing/PiChamber/v%{version}/LICENSE

ExclusiveArch:  x86_64
BuildRequires:  cpio
BuildRequires:  desktop-file-utils
Requires:       at-spi2-core
Requires:       gtk3
Requires:       libnotify
Requires:       libuuid
Requires:       libXScrnSaver
Requires:       libXtst
Requires:       nss
Requires:       xdg-utils

%description
PiChamber provides a desktop workspace for Pi Coding Agent sessions.
This package rewraps the official upstream Linux RPM.

%prep
%setup -q -c -T
rpm2cpio %{SOURCE0} | cpio -idmu

%build
# The application is supplied as a prebuilt RPM.

%install
cp -a opt %{buildroot}/
install -dm755 %{buildroot}%{_datadir}
cp -a usr/share/applications usr/share/icons %{buildroot}%{_datadir}/
rm -f %{buildroot}/opt/PiChamber/resources/app-update.yml
install -dm755 %{buildroot}%{_bindir}
ln -s /opt/PiChamber/pichamber %{buildroot}%{_bindir}/pichamber
# Support Chromium's sandbox when unprivileged user namespaces are unavailable.
chmod 4755 %{buildroot}/opt/PiChamber/chrome-sandbox
install -Dpm644 %{SOURCE1} %{buildroot}%{_licensedir}/%{name}/LICENSE

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/pichamber.desktop

%files
/opt/PiChamber/
%{_bindir}/pichamber
%{_datadir}/applications/pichamber.desktop
%{_datadir}/icons/hicolor/*/apps/pichamber.png
%license %{_licensedir}/%{name}/LICENSE

%changelog
* Mon Nov 16 2026 halcyon-linux <aahsnr041@proton.me> - 1.0.7-2
- Filter bundled ONNX libraries and unused ARM64 prebuild dependencies
- Install the command launcher and enable the Chromium sandbox helper

* Mon Nov 16 2026 halcyon-linux <aahsnr041@proton.me> - 1.0.7-1
- Initial package of the upstream x86_64 RPM

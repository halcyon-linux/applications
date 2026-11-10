# Vendor rewrap of pi-gui's official Linux x86_64 Debian package.
# Extract the data archive only; RPM owns desktop integration and package
# removal. The custom update feed pins the release asset's GitHub SHA256.
%global digest 4116a0a3bc73a3d0872cdb556f860be2ba2a640f4991cf327e7744e1d1f117b1

%global debug_package %{nil}
%global _build_id_links none
%global __os_install_post %{nil}

%global __provides_exclude_from ^/opt/pi-gui/
%global __requires_exclude ^libffmpeg[.]so|^libvulkan[.]so[.]1|^libEGL[.]so|^libGLESv2[.]so|^libvk_swiftshader[.]so

Name:           pi-gui
Version:        1.0.1
Release:        1%{?dist}
Summary:        Electron GUI for the pi coding agent
License:        MIT
URL:            https://github.com/minghinmatthewlam/pi-gui
Source0:        https://github.com/minghinmatthewlam/pi-gui/releases/download/v%{version}/pi-gui_%{version}_amd64.deb
Source1:        https://raw.githubusercontent.com/minghinmatthewlam/pi-gui/v%{version}/LICENSE

ExclusiveArch:  x86_64

BuildRequires:  binutils
BuildRequires:  desktop-file-utils
BuildRequires:  tar
BuildRequires:  xz

# Runtime dependencies declared by the Debian package, mapped to Fedora.
Requires:       at-spi2-core
Requires:       git
Requires:       gtk3
Requires:       libnotify
Requires:       libsecret
Requires:       libuuid
Requires:       libXScrnSaver
Requires:       libXtst
Requires:       mesa-libgbm
Requires:       nss
Requires:       xdg-utils

%description
pi-gui is an Electron desktop interface for the pi coding agent. This
package repackages the official upstream Linux x86_64 Debian payload.

%prep
%setup -q -c -T
actual="$(sha256sum %{SOURCE0} | cut -d' ' -f1)"
if [ "$actual" != '%{digest}' ]; then
    echo "pi-gui: sha256 mismatch (expected %{digest}, got $actual)" >&2
    exit 1
fi
ar p %{SOURCE0} data.tar.xz > data.tar.xz
tar -xJf data.tar.xz
cp %{SOURCE1} LICENSE

%build
# Nothing to compile; this RPM uses the upstream Electron application payload.

%install
install -dm755 %{buildroot}/opt %{buildroot}%{_bindir}
install -dm755 %{buildroot}%{_datadir}/applications
install -dm755 %{buildroot}%{_datadir}/icons/hicolor/512x512/apps
install -dm755 %{buildroot}%{_licensedir}/%{name}
cp -a opt/pi-gui %{buildroot}/opt/

# Keep RPM-managed updates authoritative. Move license texts into the license directory.
rm -f %{buildroot}/opt/pi-gui/resources/app-update.yml
mv %{buildroot}/opt/pi-gui/LICENSE.electron.txt \
    %{buildroot}%{_licensedir}/%{name}/LICENSE.electron.txt
mv %{buildroot}/opt/pi-gui/LICENSES.chromium.html \
    %{buildroot}%{_licensedir}/%{name}/LICENSES.chromium.html

# Set Chromium's setuid sandbox helper, matching Fedora Electron package practice.
chmod 4755 %{buildroot}/opt/pi-gui/chrome-sandbox

sed 's|^Exec=.*|Exec=/usr/bin/pi-gui %U|' \
    usr/share/applications/pi-gui.desktop \
    > %{buildroot}%{_datadir}/applications/pi-gui.desktop
install -pDm644 usr/share/icons/hicolor/512x512/apps/pi-gui.png \
    %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/pi-gui.png
install -pDm644 LICENSE %{buildroot}%{_licensedir}/%{name}/LICENSE

cat > %{buildroot}%{_bindir}/pi-gui <<'EOF'
#!/bin/sh
exec /opt/pi-gui/pi-gui "$@"
EOF
chmod 0755 %{buildroot}%{_bindir}/pi-gui

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/pi-gui.desktop

%files
/opt/pi-gui/
%{_bindir}/pi-gui
%{_datadir}/applications/pi-gui.desktop
%{_datadir}/icons/hicolor/512x512/apps/pi-gui.png
%license %{_licensedir}/%{name}/LICENSE
%license %{_licensedir}/%{name}/LICENSE.electron.txt
%license %{_licensedir}/%{name}/LICENSES.chromium.html

%changelog
* Tue Nov 10 2026 halcyon-linux <aahsnr041@proton.me> - 1.0.1-1
- Initial package: rewrap the official upstream Linux x86_64 Debian payload

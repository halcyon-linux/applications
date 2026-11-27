# Rewrap the official desktop AppImage with package-manager-owned updates.
%global digest dac1bbe9e93c1a5fb0942332befa998597f6a086232a87766ef5d8235a44f56d
%global debug_package %{nil}
%global _build_id_links none
%global __os_install_post %{nil}
%global __provides_exclude_from ^%{_libdir}/t3-code/
%global __requires_exclude ^libffmpeg[.]so|^libvulkan[.]so[.]1|^libEGL[.]so|^libGLESv2[.]so|^libvk_swiftshader[.]so

Name:           t3-code
Version:        0.1.13
Release:        1%{?dist}
Summary:        Desktop control plane for coding agents
License:        MIT
URL:            https://t3.codes/
Source0:        https://github.com/pingdotgg/t3code/releases/download/v%{version}/T3-Code-x86_64.AppImage
Source1:        t3-code.desktop
Source2:        https://raw.githubusercontent.com/pingdotgg/t3code/v%{version}/LICENSE
Source3:        https://raw.githubusercontent.com/pingdotgg/t3code/v%{version}/apps/desktop/resources/linux/com.t3tools.t3code.metainfo.xml
ExclusiveArch:  x86_64
BuildRequires:  desktop-file-utils
BuildRequires:  libappstream-glib
Requires:       alsa-lib
Requires:       at-spi2-core
Requires:       gtk3
Requires:       mesa-libgbm
Requires:       libnotify
Requires:       nss
Requires:       libsecret
Requires:       libuuid
Requires:       libXScrnSaver
Requires:       libXtst
Requires:       xdg-utils
Requires:       hicolor-icon-theme
Requires:       git-core

%description
T3 Code orchestrates coding agents in a desktop workspace. It connects to
the agent tools and subscriptions configured by the user. This package
installs the upstream desktop application with its bundled Electron runtime.

%prep
%setup -q -c -T
echo '%{digest}  %{SOURCE0}' | sha256sum -c -
cp %{SOURCE0} t3-code.AppImage
chmod 755 t3-code.AppImage
./t3-code.AppImage --appimage-extract > /dev/null
test -x squashfs-root/t3code
test -f squashfs-root/.DirIcon
# Remove Electron's updater manifest so RPM owns application updates.
rm -f squashfs-root/resources/app-update.yml

%install
install -dm755 %{buildroot}%{_libdir}/%{name} %{buildroot}%{_bindir}
cp -a squashfs-root/. %{buildroot}%{_libdir}/%{name}/
ln -s %{_libdir}/%{name}/t3code %{buildroot}%{_bindir}/t3code
install -Dm644 %{SOURCE1} %{buildroot}%{_datadir}/applications/t3code.desktop
install -Dm644 squashfs-root/.DirIcon %{buildroot}%{_datadir}/pixmaps/t3code.png
install -Dm644 %{SOURCE2} %{buildroot}%{_licensedir}/%{name}/LICENSE
install -Dm644 %{SOURCE3} %{buildroot}%{_metainfodir}/com.t3tools.t3code.metainfo.xml

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/t3code.desktop
appstream-util validate-relax --nonet %{buildroot}%{_metainfodir}/com.t3tools.t3code.metainfo.xml

%files
%{_bindir}/t3code
%{_libdir}/%{name}/
%{_datadir}/applications/t3code.desktop
%{_datadir}/pixmaps/t3code.png
%{_metainfodir}/com.t3tools.t3code.metainfo.xml
%license %{_licensedir}/%{name}/LICENSE

%changelog
* Sat Nov 28 2026 halcyon-linux <aahsnr041@proton.me> - 0.1.13-1
- Package the official desktop AppImage with automatic stable release updates

# Vendor rewrap of Podman Desktop's upstream Linux x64 release archive.
# The updater feed pins the release asset digest; disable the in-app updater
# so package updates remain owned by dnf.
%global             digest aa616a948a8b254132e903b751a95765eeae3454cbd5b7049146b5bdeb842d3d
%global             debug_package %{nil}
%global _build_id_links none
%global             __os_install_post %{nil}

%global __provides_exclude_from ^%{_libdir}/podman-desktop/
%global __requires_exclude ^libffmpeg[.]so|^libvulkan[.]so[.]1|^libEGL[.]so|^libGLESv2[.]so|^libvk_swiftshader[.]so

Name:           podman-desktop
Version:        1.30.5
Release:        1%{?dist}
Summary:        Graphical interface for containers and Kubernetes
License:        Apache-2.0
URL:            https://podman-desktop.io/
Source0:        https://github.com/podman-desktop/podman-desktop/releases/download/v%{version}/podman-desktop-%{version}-x64.tar.gz
Source1:        podman-desktop.desktop
Source2:        https://raw.githubusercontent.com/podman-desktop/podman-desktop/v%{version}/LICENSE
Source3:        https://raw.githubusercontent.com/podman-desktop/podman-desktop/v%{version}/buildResources/icon-512x512.png

ExclusiveArch:  x86_64

BuildRequires:  desktop-file-utils

Requires:       alsa-lib
Requires:       at-spi2-core
Requires:       gtk3
Requires:       libXScrnSaver
Requires:       libXtst
Requires:       libnotify
Requires:       libsecret
Requires:       libuuid
Requires:       nss
Requires:       podman
Requires:       xdg-utils

%description
Podman Desktop is a graphical interface for containers and Kubernetes.
This package rewraps the upstream Linux x64 release archive and uses the
system Podman engine.

%prep
%autosetup -n podman-desktop-%{version}-x64
actual="$(sha256sum %{SOURCE0} | cut -d' ' -f1)"
if [ "$actual" != '%{digest}' ]; then
    echo "podman-desktop: sha256 mismatch (expected %{digest}, got $actual)" >&2
    exit 1
fi
rm -f resources/app-update.yml

%install
%__rm -rf %{buildroot}
install -dm755 %{buildroot}%{_libdir}/podman-desktop %{buildroot}%{_bindir}
cp -a . %{buildroot}%{_libdir}/podman-desktop/
ln -s %{_libdir}/podman-desktop/podman-desktop \
    %{buildroot}%{_bindir}/podman-desktop
install -Dm644 %{SOURCE1} \
    %{buildroot}%{_datadir}/applications/podman-desktop.desktop
install -Dm644 %{SOURCE2} \
    %{buildroot}%{_licensedir}/podman-desktop/LICENSE
install -Dm644 %{SOURCE3} \
    %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/podman-desktop.png

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/podman-desktop.desktop

%files
%{_bindir}/podman-desktop
%{_libdir}/podman-desktop/
%{_datadir}/applications/podman-desktop.desktop
%{_datadir}/icons/hicolor/512x512/apps/podman-desktop.png
%license %{_licensedir}/podman-desktop/LICENSE

%changelog
* Fri Nov 06 2026 halcyon-linux <aahsnr041@proton.me> - 1.30.5-1
- Initial package: rewrap the Podman Desktop Linux x64 release

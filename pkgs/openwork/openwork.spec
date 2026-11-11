# Vendor rewrap of OpenWork's public Electron Linux x64 release archive.
# The updater feed pins the release asset digest; disable the in-app updater
# so package updates remain owned by dnf.
%global             digest c57a3a2b053b3c8caf7b8e18317e3266bdafdc763900ed930a4e0bd4cce244d4
%global             debug_package %{nil}
%global _build_id_links none
%global             __os_install_post %{nil}

%global __provides_exclude_from ^%{_libdir}/openwork/
%global __requires_exclude_from ^%{_libdir}/openwork/
%global __requires_exclude ^libffmpeg[.]so|^libvulkan[.]so[.]1|^libEGL[.]so|^libGLESv2[.]so|^libvk_swiftshader[.]so|^libc[.]musl|^ld-linux-aarch64

Name:           openwork
Version:        0.18.66
Release:        1%{?dist}
Summary:        Open-source AI agent desktop workspace
License:        MIT
URL:            https://openworklabs.com/
Source0:        https://github.com/different-ai/openwork/releases/download/v%{version}/openwork-linux-x64-%{version}.tar.gz
Source1:        openwork.desktop
Source2:        https://raw.githubusercontent.com/different-ai/openwork/v%{version}/LICENSE

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
Requires:       xdg-utils

%description
OpenWork is an open-source AI agent desktop workspace built on OpenCode.
This package rewraps the public upstream Linux x64 release archive.

%prep
%autosetup -n openwork-linux-x64-%{version}
actual="$(sha256sum %{SOURCE0} | cut -d' ' -f1)"
if [ "$actual" != '%{digest}' ]; then
    echo "openwork: sha256 mismatch (expected %{digest}, got $actual)" >&2
    exit 1
fi
rm -f resources/app-update.yml
find . -type f \( -name "*arm64*" -o -name "*aarch64*" \) -delete

%install
%__rm -rf %{buildroot}
install -dm755 %{buildroot}%{_libdir}/openwork %{buildroot}%{_bindir}
cp -a . %{buildroot}%{_libdir}/openwork/
ln -s %{_libdir}/openwork/openwork %{buildroot}%{_bindir}/openwork
install -Dm644 %{SOURCE1} \
    %{buildroot}%{_datadir}/applications/openwork.desktop
install -Dm644 %{SOURCE2} \
    %{buildroot}%{_licensedir}/openwork/LICENSE
install -Dm644 %{buildroot}%{_libdir}/openwork/resources/icons/linux/512x512.png \
    %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/openwork.png

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/openwork.desktop

%files
%{_bindir}/openwork
%{_libdir}/openwork/
%{_datadir}/applications/openwork.desktop
%{_datadir}/icons/hicolor/512x512/apps/openwork.png
%license %{_licensedir}/openwork/LICENSE

%changelog
* Sat Nov 07 2026 halcyon-linux <aahsnr041@proton.me> - 0.18.65-2
- Exclude private bundled requires and prune foreign arch binaries

* Fri Nov 06 2026 halcyon-linux <aahsnr041@proton.me> - 0.18.65-1
- Initial package: rewrap the public OpenWork Linux x64 release

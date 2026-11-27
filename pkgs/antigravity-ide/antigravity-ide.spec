%global debug_package %{nil}
%global _build_id_links none
%global __os_install_post %{nil}
%global __provides_exclude_from ^%{_libdir}/antigravity-ide/
# Electron loads its private FFmpeg library from the application directory.
%global __requires_exclude ^libffmpeg[.]so|^libcurl[.]so[.]4[(]CURL_OPENSSL_4[)][(]64bit[)]$
# The vendor's Debian curl symbol namespace is absent from Fedora's libcurl.
# Keep the unversioned libcurl requirement and the system library dependency.
%global build_id 4671306730438656
%global digest f0193df2558e35ff98fafe829a5c318a1ae0957942343597eb9f97098e276b23

Name:           antigravity-ide
Version:        2.9.0
Release:        2%{?dist}
Summary:        Google's agentic integrated development environment
License:        LicenseRef-Proprietary
URL:            https://antigravity.google/product/antigravity-ide
Source0:        https://edgedl.me.gvt1.com/edgedl/release2/j0qc3/antigravity/stable/%{version}-%{build_id}/linux-x64/Antigravity%%20IDE.tar.gz#/%{name}-%{version}.tar.gz
Source1:        antigravity-ide.desktop
Source2:        antigravity-ide-url-handler.desktop
Source3:        antigravity-ide-workspace.xml
ExclusiveArch:  x86_64
BuildRequires:  desktop-file-utils
BuildRequires:  shared-mime-info
Requires:       bash
Requires:       hicolor-icon-theme
Requires:       libsecret
Requires:       curl
Requires:       libcurl
Requires:       openssl-libs
Requires:       libsoup3
Requires:       webkit2gtk4.1

%description
Google Antigravity IDE combines a code editor with integrated agent panels
and an execution workspace. This package rewraps Google's official Linux
x64 release archive.

%prep
%setup -q -c -T
echo '%{digest}  %{SOURCE0}' | sha256sum -c -
tar -xzf %{SOURCE0}
test -x 'Antigravity IDE/bin/antigravity-ide'
test -f 'Antigravity IDE/libffmpeg.so'

%install
install -dm755 %{buildroot}%{_libdir}/%{name} %{buildroot}%{_bindir}
cp -a 'Antigravity IDE/.' %{buildroot}%{_libdir}/%{name}/
cat > %{buildroot}%{_bindir}/%{name} <<'EOF'
#!/bin/bash
exec %{_libdir}/%{name}/bin/antigravity-ide "$@"
EOF
chmod 755 %{buildroot}%{_bindir}/%{name}
install -Dm644 %{SOURCE1} %{buildroot}%{_datadir}/applications/%{name}.desktop
install -Dm644 %{SOURCE2} %{buildroot}%{_datadir}/applications/%{name}-url-handler.desktop
install -Dm644 %{SOURCE3} %{buildroot}%{_datadir}/mime/packages/%{name}-workspace.xml
install -Dm644 'Antigravity IDE/resources/app/resources/linux/code.png' \
    %{buildroot}%{_datadir}/pixmaps/%{name}.png
install -Dm644 'Antigravity IDE/resources/app/LICENSE.txt' \
    %{buildroot}%{_licensedir}/%{name}/LICENSE.txt
install -Dm644 'Antigravity IDE/LICENSES.chromium.html' \
    %{buildroot}%{_licensedir}/%{name}/LICENSES.chromium.html

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/%{name}.desktop
desktop-file-validate %{buildroot}%{_datadir}/applications/%{name}-url-handler.desktop
mkdir -p mime-check/packages
cp %{SOURCE3} mime-check/packages/
update-mime-database "$PWD/mime-check"

%files
%{_bindir}/%{name}
%{_libdir}/%{name}/
%{_datadir}/applications/%{name}.desktop
%{_datadir}/applications/%{name}-url-handler.desktop
%{_datadir}/mime/packages/%{name}-workspace.xml
%{_datadir}/pixmaps/%{name}.png
%license %{_licensedir}/%{name}/LICENSE.txt
%license %{_licensedir}/%{name}/LICENSES.chromium.html

%changelog
* Sat Nov 28 2026 halcyon-linux <aahsnr041@proton.me> - 2.9.0-2
- Use Google's update manifest and verify the archive SHA256
- Filter the Debian curl symbol namespace while retaining Fedora libcurl

* Sat Nov 28 2026 halcyon-linux <aahsnr041@proton.me> - 2.9.0-1
- Package Google's standalone IDE archive with automatic release tracking

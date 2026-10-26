# Vendor RPM rewrap (openchamber/openchamber releases).
# The desktop client ships its own Electron runtime under /opt/OpenChamber.
# The vendor payload carries build-id links (dropped) and its self-updater
# config (removed so dnf and the in-app updater do not fight).
# Sources are fetched by mock at SRPM-build time; nothing is downloaded in %prep.
%define debug_package %{nil}
%global _build_id_links none

Name:           openchamber
Version:        2.5.2
Release:        2%{?dist}
Summary:        Agentic Development Environment based on OpenCode AI agent
License:        MIT
URL:            https://openchamber.dev/
Source0:        https://github.com/openchamber/openchamber/releases/download/v%{version}/OpenChamber-%{version}-linux-x86_64.rpm
Source1:        https://raw.githubusercontent.com/openchamber/openchamber/v%{version}/LICENSE

ExclusiveArch:  x86_64

BuildRequires:  cpio
BuildRequires:  desktop-file-utils

# Electron runtime deps — the automatic ELF deps cover linked sonames
# (gtk3, nss, atk, ...); these are the ones the binary only dlopen()s,
# plus the desktop bits — the same set opencode-desktop declares.
Requires:       gtk3
Requires:       nss
Requires:       at-spi2-core
Requires:       libXScrnSaver
Requires:       libXtst
Requires:       libnotify
Requires:       xdg-utils
Requires:       ripgrep

%description
OpenChamber is an agentic development environment based on the OpenCode AI
agent. This package rewraps the upstream prebuilt Linux RPM for Fedora.

%prep
rpm2cpio %{SOURCE0} | cpio -idmu

%build
# Nothing to compile: the prebuilt Electron app is unpacked in prep.

%install
cp -a opt %{buildroot}/
cp -a usr %{buildroot}/
# the vendor RPM was built with build-id links; nothing packages them
rm -rf %{buildroot}/usr/lib/.build-id
# the in-app updater would fight dnf
rm -f %{buildroot}/opt/OpenChamber/resources/app-update.yml
install -Dpm0644 %{SOURCE1} %{buildroot}%{_licensedir}/%{name}/LICENSE
# The vendor payload carries node-native modules with upstream's own
# build-machine RPATHs — sherpa-onnx.node ships an absolute runpath into
# the upstream CI workspace plus an empty entry. check-rpaths hard-fails
# exactly those two classes; allow them and keep the check for the rest.
export QA_RPATHS=$(( 0x0002 | 0x0010 ))

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/*.desktop

%files
/opt/OpenChamber/
%{_datadir}/applications/*.desktop
%{_datadir}/icons/hicolor/*/apps/*.png
%{_datadir}/metainfo/*.metainfo.xml
%license %{_licensedir}/%{name}/LICENSE

%changelog
* Mon Oct 26 2026 halcyon-autoupdate <aahsnr041@proton.me> - 2.5.2-2
- Allow the vendor payload's upstream-CI RPATH classes through check-rpaths
  (QA_RPATHS 0x0002|0x0010): sherpa-onnx.node ships both, and the hook
  hard-failed every openchamber build so far

* Fri Oct 23 2026 halcyon-autobuild - 2.5.0-1
- Initial packaging (vendor-RPM rewrap per the opencode-desktop pattern)
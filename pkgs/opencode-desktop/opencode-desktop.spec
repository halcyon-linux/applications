# Rewrap of the vendor RPM (the desktop client ships its own Electron
# runtime under /opt/OpenCode — Arch's system-electron surgery is an
# unusual distribution-side pattern we do not mirror). The vendor payload
# also carries build-id links (dropped) and its self-updater config
# (removed so dnf and the in-app updater do not fight).
%define debug_package %{nil}
%global _build_id_links none

# The bundled libraries under /opt/OpenCode carry SONAMEs, so the dependency
# generator would advertise them as system providers. This repo is consumed at
# priority=1, so those Provides would shadow Fedora's own packages in any
# dependency resolution; they are private to the bundle.
# The Requires on the bundled Chromium libs nothing in Fedora provides are
# dropped as well. Brackets, not backslashes, escape regex metacharacters:
# rpm consumes backslashes while expanding the macro.
%global __provides_exclude_from ^/opt/OpenCode/
%global __requires_exclude ^libffmpeg[.]so|^libvulkan[.]so[.]1|^libEGL[.]so|^libGLESv2[.]so|^libvk_swiftshader[.]so

Name:           opencode-desktop
Version:        2.2.0
Release:        1%{?dist}
Summary:        OpenCode desktop client

License:        MIT
URL:            https://opencode.ai
Source0:        %{url}/files/bin/%{version}/opencode-desktop-linux-x86_64.rpm
Source1:        https://raw.githubusercontent.com/anomalyco/opencode/v%{version}/LICENSE
#!RemoteAsset
ExclusiveArch:  x86_64

# the automatic check stage validates the packaged .desktop files
BuildRequires:  cpio
BuildRequires:  desktop-file-utils

Requires:       gtk3
Requires:       nss
Requires:       at-spi2-core
Requires:       libXScrnSaver
Requires:       libXtst
Requires:       libnotify
Requires:       xdg-utils
Requires:       ripgrep

%description
The OpenCode desktop client: a visual companion to the opencode terminal
agent, packaging plans, diffs and agent runs in an Electron shell. The
bundled agent binary can delegate to the CLI.

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
rm -f %{buildroot}/opt/OpenCode/resources/app-update.yml
install -Dpm0644 %{SOURCE1} %{buildroot}%{_licensedir}/%{name}/LICENSE

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/*.desktop

%files
/opt/OpenCode/
%{_datadir}/applications/*.desktop
%{_datadir}/icons/hicolor/*/apps/*.png
%{_datadir}/metainfo/*.metainfo.xml
%license %{_licensedir}/%{name}/LICENSE

%changelog
* Tue Oct 27 2026 halcyon-linux <aahsnr041@proton.me> - 2.1.4-2
- Stop advertising the bundled libraries as system Provides (__provides_exclude_from): with the
  repo at priority=1 they shadowed Fedora's packages and were pulled into unrelated installs;
  drop the matching Requires on the bundled Chromium libs

* Sat Sep 26 2026 halcyon-autoupdate <aahsnr041@proton.me> - 2.0.18-1
- initial packaging (vendor-RPM rewrap per the opencode-desktop-bin AUR
  pattern, with the bundled Electron runtime)

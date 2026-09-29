# Vendor rewrap of Mullvad's official RPM (the same MullvadVPN-<ver>_x86_64.rpm
# Mullvad publishes both on their GitHub releases and in their own yum repo) —
# upstream ships the RPM, so a rewrap is the sanctioned path. The tree is
# reinstalled verbatim: the Electron GUI under "/opt/Mullvad VPN", the daemon
# and CLI wrappers in /usr/bin, the two systemd units, desktop entry and
# completions.
# Versioned by the custom sweep feed (ci/sweep/custom.py), which scrapes
# mullvad.net's server-rendered Linux download page — the same page upstream's
# own install instructions point at.
%global             debug_package %{nil}
%global _build_id_links none
%global             __os_install_post %{nil}

Name:               mullvad-vpn
Version:            2026.5
Release:            1%{?dist}
Summary:            Mullvad VPN client (official RPM rewrap)
License:            GPL-3.0-or-later
URL:                https://mullvad.net
#!RemoteAsset
Source0:            https://github.com/mullvad/mullvadvpn-app/releases/download/%{version}/MullvadVPN-%{version}_x86_64.rpm

ExclusiveArch:      x86_64

BuildRequires:      systemd-rpm-macros
Requires:           systemd
Requires:           dbus-libs
Requires:           libXScrnSaver
Requires:           libnotify

%description
Mullvad VPN desktop client and daemon, repacked from Mullvad's official
RPM. Ships the Electron GUI, the mullvad-daemon systemd service (with the
early-boot blocking unit), the mullvad CLI and shell completions.

%prep
# unpack the vendor RPM without installing it
mkdir -p extract
cd extract
rpm2cpio %{_sourcedir}/MullvadVPN-%{version}_x86_64.rpm | cpio -idm --quiet
test -d "opt/Mullvad VPN"

%install
%__rm -rf %{buildroot}
mkdir -p %{buildroot}/opt %{buildroot}%{_prefix}
cp -a extract/opt/. %{buildroot}/opt/
cp -a extract/usr/. %{buildroot}%{_prefix}/

%post
%systemd_post mullvad-daemon.service
%systemd_post mullvad-early-boot-blocking.service

%preun
%systemd_preun mullvad-daemon.service
%systemd_preun mullvad-early-boot-blocking.service

%postun
%systemd_postun mullvad-daemon.service
%systemd_postun mullvad-early-boot-blocking.service

%files
%{_unitdir}/mullvad-daemon.service
%{_unitdir}/mullvad-early-boot-blocking.service
%{_bindir}/mullvad
%{_bindir}/mullvad-daemon
%{_bindir}/mullvad-exclude
%{_bindir}/mullvad-problem-report
%{_datadir}/applications/mullvad-vpn.desktop
%{_datadir}/bash-completion/completions/mullvad
%{_datadir}/fish/vendor_completions.d/mullvad.fish
%{_datadir}/zsh/site-functions/_mullvad
%{_datadir}/icons/hicolor/*/apps/mullvad-vpn.png
"/opt/Mullvad VPN/"

%changelog
* Tue Sep 29 2026 halcyon-autoupdate <aahsnr041@proton.me> - 2026.5-1
- initial package: vendor rewrap of Mullvad's official MullvadVPN-2026.5
  RPM (GUI, daemon, early-boot blocking unit, CLI, completions)

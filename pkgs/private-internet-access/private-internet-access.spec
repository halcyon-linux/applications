# Vendor rewrap of Private Internet Access's official self-contained
# installer (pia.run, a makeself archive) — the installer is a
# self-contained release artifact, which is the sanctioned rewrap path in
# this repo. Layout follows the AUR piavpn-bin package: piafiles/ IS the
# app tree (/opt/piavpn), the installer's helper scripts ship into the
# app's bin, and the wireguard installer + uninstaller are installer-time
# artifacts that don't belong in an RPM.
#
# Versioning: the .run filename carries both the app version and a build
# number (pia-linux-<ver>-<build>.run); upstream publishes no assets on
# their GitHub releases and the download site has no listing, so the
# custom sweep feed (ci/sweep/custom.py, custom_private_internet_access)
# parses the AUR piavpn-bin PKGBUILD's pkgver/build_number and rewrites
# Version + the pia_build global here.
#
# Capabilities: the official installer and the AUR package both grant
# cap_net_bind_service on pia-unbound — done in %%post like upstream
# (a %%files %%caps entry would duplicate the /opt/piavpn dir glob).
# The pia iproute2 routing table is registered by the daemon itself at
# runtime (upstream's uninstaller merely cleans it up).
%global             pia_build 08420
%global             debug_package %{nil}
%global _build_id_links none
%global             __os_install_post %{nil}
# the bundle's ELFs were linked against a Qt built with the generic private
# symbol tag Qt_6_PRIVATE_API (Arch-style); Fedora's qt6-3d provides no
# provider for that tag and the bundle ships no 3D libs of its own — the
# public Qt_6 requires stay and resolve from Fedora's qt6-3d
%global             __requires_exclude ^libQt6.*Qt_6_PRIVATE_API.*$

Name:               private-internet-access
Version:            3.7.2
Release:            3%{?dist}
Summary:            Private Internet Access VPN client (official installer rewrap)
License:            LicenseRef-PIA
URL:                https://www.privateinternetaccess.com
#!RemoteAsset
Source0:            https://installers.privateinternetaccess.com/download/pia-linux-%{version}-%{pia_build}.run
# upstream's unit with the dead syslog.target dropped from After= (AUR)
Source1:            piavpn.service
# NetworkManager must not manage the app's wgpia* WireGuard devices (AUR)
Source2:            50-wgpia.conf
# log-volume limiter the AUR writes into /opt/piavpn/var
Source3:            debug.txt

ExclusiveArch:      x86_64

BuildRequires:      systemd-rpm-macros
Requires:           systemd
Requires:           iproute
Requires:           iptables
Requires:           libcap

%description
Private Internet Access VPN client, repacked from upstream's official
self-contained installer. Ships the Qt GUI, the root daemon
(piavpn.service) and piactl on PATH; the app lives under /opt/piavpn.

%prep
# makeself archive: extract the payload without running the installer.
# env -i keeps RPM's build environment out of the shell the archive's
# bootstrap sources (the AUR's makepkg trick).
mkdir -p extract
env -i /bin/sh %{_sourcedir}/pia-linux-%{version}-%{pia_build}.run \
    --noexec --target "$PWD/extract"
test -d extract/piafiles

%install
%__rm -rf %{buildroot}

# piafiles/* IS the app tree (bin/, lib/, plugins/, qml/, share/)
install -dm755 %{buildroot}/opt/piavpn
cp -a extract/piafiles/. %{buildroot}/opt/piavpn/

# installer helper scripts ship into the app's bin (AUR); the wireguard
# installer and uninstaller are installer-time artifacts — dropped
install -Dm755 extract/installfiles/error-notice.sh \
    %{buildroot}/opt/piavpn/bin/error-notice.sh
install -Dm755 extract/installfiles/run-in-terminal.sh \
    %{buildroot}/opt/piavpn/bin/run-in-terminal.sh

# log-volume limiter (AUR): /opt/piavpn/var/debug.txt
install -Dm644 %{SOURCE3} %{buildroot}/opt/piavpn/var/debug.txt

# systemd unit, desktop entry, icon, piactl on PATH
install -Dm644 %{SOURCE1} %{buildroot}%{_unitdir}/piavpn.service
install -Dm644 extract/installfiles/piavpn.desktop \
    %{buildroot}%{_datadir}/applications/piavpn.desktop
install -Dm644 extract/installfiles/app-icon.png \
    %{buildroot}%{_datadir}/pixmaps/piavpn.png
# BUILDROOT has no usr/bin yet — create it or the symlink fails
install -dm755 %{buildroot}%{_bindir}
ln -sr %{buildroot}/opt/piavpn/bin/piactl %{buildroot}%{_bindir}/piactl

# NetworkManager unmanaged-devices rule for the wgpia* interfaces
install -Dm644 %{SOURCE2} \
    %{buildroot}%{_sysconfdir}/NetworkManager/conf.d/50-wgpia.conf

# license from the app bundle's share/ tree
install -Dm644 extract/piafiles/share/LICENSE.txt \
    %{buildroot}%{_licensedir}/%{name}/LICENSE

%post
%systemd_post piavpn.service
# the installer's own step: pia-unbound binds low ports for DNS
setcap cap_net_bind_service=ep /opt/piavpn/bin/pia-unbound || :

%preun
%systemd_preun piavpn.service

%postun
%systemd_postun piavpn.service

%files
%license %{_licensedir}/%{name}/LICENSE
%{_unitdir}/piavpn.service
%{_bindir}/piactl
%{_datadir}/applications/piavpn.desktop
%{_datadir}/pixmaps/piavpn.png
%dir %{_sysconfdir}/NetworkManager/conf.d
%config(noreplace) %{_sysconfdir}/NetworkManager/conf.d/50-wgpia.conf
/opt/piavpn/

%changelog
* Wed Sep 30 2026 halcyon-autoupdate <aahsnr041@proton.me> - 3.7.2-3
- exclude the unresolvable Qt_6_PRIVATE_API auto-requires (upstream's Qt
  uses the generic private tag; Fedora's qt6-3d only satisfies the public ones)
* Wed Sep 30 2026 halcyon-autoupdate <aahsnr041@proton.me> - 3.7.2-2
- install fix: create bindir before linking piactl into it
* Tue Sep 29 2026 halcyon-autoupdate <aahsnr041@proton.me> - 3.7.2-1
- initial package: vendor rewrap of the official pia-linux-3.7.2-08420.run
  installer (AUR piavpn-bin layout)

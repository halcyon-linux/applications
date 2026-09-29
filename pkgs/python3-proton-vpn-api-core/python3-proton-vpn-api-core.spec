# Vendor rewrap of the RPM Proton AG publishes in their official Fedora
# repository (repo.protonvpn.com/fedora-44-stable) — upstream ships the RPM,
# so a rewrap is the sanctioned path. The payload is re-installed verbatim
# (rpm2cpio extract) EXCEPT the python trees, which are relocated onto the
# python3_sitelib/python3_sitearch macros: the upstream RPMs are built for
# Fedora 44's python3.14 and must land in the buildroot python's
# site-packages dir on every chroot we build (the .so in api-core is abi3,
# the pure-python trees are version-agnostic). Stale upstream __pycache__
# is stripped — brp is off for these (foreign payload) and the dist-info
# metadata drives the python(abi) deps from the relocated paths.
# Versioned by the custom sweep feed: ProtonVPN/python-proton-vpn-api-core tags, HEAD-probing
# the official repo RPM URL zotero-style so a tag whose RPM build has not
# landed yet never bumps the spec.
%global             pv_fc 44
%global             pv_rel 1
%global             debug_package %{nil}
%global _build_id_links none
%global             __os_install_post %{nil}
ExclusiveArch:      x86_64
Name:               python3-proton-vpn-api-core
Version:            5.8.3
Release:            2%{?dist}
Summary:            Proton VPN API facade with the integrated NetworkManager backend and Rust services
License:            GPL-3.0-or-later
URL:                https://github.com/ProtonVPN/python-proton-vpn-api-core
#!RemoteAsset
Source0:            https://repo.protonvpn.com/fedora-%{pv_fc}-stable/%{name}/%{name}-%{version}-%{pv_rel}.fc%{pv_fc}.x86_64.rpm
ExclusiveArch:      x86_64
BuildRequires:      systemd-rpm-macros
BuildRequires:      python3-devel
BuildRequires:      python-srpm-macros
Requires:           NetworkManager
Requires:           NetworkManager-openvpn
Requires:           NetworkManager-openvpn-gnome
Requires:           gobject-introspection
Requires:           python3-dbus-fast
Requires:           python3-distro
Requires:           python3-fido2
Requires:           python3-gobject
Requires:           python3-jinja2
Requires:           python3-packaging
Requires:           python3-proton-core >= 0.5.0
Requires:           python3-pynacl
Requires:           python3-sentry-sdk
Requires:           systemd
%description
The proton-vpn-api-core facade over the Proton VPN services, with the
integrated NetworkManager backend and the Rust nm-protun / kill-switch
helper services. Repacked from Proton's official Fedora repository.

%prep
mkdir -p extract
cd extract
rpm2cpio %{_sourcedir}/%{name}-%{version}-%{pv_rel}.fc%{pv_fc}.x86_64.rpm | cpio -idm --quiet
test -d usr/lib64/python3.14/site-packages/proton/vpn

%install
%__rm -rf %{buildroot}
mkdir -p %{buildroot}%{python3_sitearch} %{buildroot}%{_prefix} %{buildroot}%{_libexecdir}
cp -a extract/usr/lib64/python3.14/site-packages/proton %{buildroot}%{python3_sitearch}/
cp -a extract/usr/lib64/python3.14/site-packages/proton_vpn_api_core-*.dist-info %{buildroot}%{python3_sitearch}/
# copy the subtrees WHOLE: a trailing /. would flatten their contents one
# level (the libexec services would land in /usr, dbus-1 in /usr/dbus-1, …)
cp -a extract/usr/lib %{buildroot}%{_prefix}/
cp -a extract/usr/share %{buildroot}%{_prefix}/
cp -a extract/usr/libexec %{buildroot}%{_prefix}/
find %{buildroot} -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || :

%post
%systemd_post proton-vpn-kill-switch-boot.service

%preun
%systemd_preun proton-vpn-kill-switch-boot.service

%postun
%systemd_postun proton-vpn-kill-switch-boot.service

%files
%{python3_sitearch}/proton/
%{python3_sitearch}/proton_vpn_api_core-*/
%{_libexecdir}/nm-protun-service
%{_libexecdir}/proton-vpn-kill-switch-service
%{_prefix}/lib/NetworkManager/VPN/nm-protun.name
%{_unitdir}/proton-vpn-kill-switch-boot.service
%{_datadir}/dbus-1/system-services/me.proton.vpn.kill_switch.service
%{_datadir}/dbus-1/system.d/me.proton.vpn.kill_switch.conf
%{_datadir}/dbus-1/system.d/nm-protun-service.conf

%changelog
* Wed Sep 30 2026 halcyon-autoupdate <aahsnr041@proton.me> - 5.8.3-2
- install fix: copy the usr subtrees whole (the trailing /. flattened
  libexec, share and lib into /usr) and drop the stray unrelocated lib64 copy
* Wed Sep 30 2026 halcyon-autoupdate <aahsnr041@proton.me> - 5.8.3-1
- initial package: vendor rewrap of the official repo.protonvpn.com RPM

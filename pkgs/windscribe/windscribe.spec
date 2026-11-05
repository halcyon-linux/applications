# Vendor rewrap of Windscribe's official Fedora x86_64 GUI RPM. The custom
# update feed pins the stable GitHub release asset digest. Recreate package
# identity and service lifecycle locally instead of running upstream scriptlets,
# whose uninstall path deletes /etc/windscribe and /var/lib/windscribe.
%global             digest 7f37792789fea5299325f4b121cb3a347c088fa38d5311f4f13aaac3684c30f8
%global             debug_package %{nil}
%global _build_id_links none
%global             __os_install_post %{nil}
%global __provides_exclude_from ^/opt/windscribe/
%global __requires_exclude ^libcrypto[.]so[.]4|^libssl[.]so[.]4|^libwsnet[.]so

Name:               windscribe
Version:            2.24.13
Release:            1%{?dist}
Summary:            Windscribe VPN desktop client
License:            GPL-2.0-only
URL:                https://windscribe.com
Source0:            https://github.com/Windscribe/Desktop-App/releases/download/v%{version}/windscribe_%{version}_amd64_fedora.rpm

ExclusiveArch:      x86_64

BuildRequires:      cpio
BuildRequires:      systemd-rpm-macros
%{?sysusers_requires_compat}

Requires:           dbus-libs
Requires:           gnupg2
Requires:           iproute
Requires:           iputils
Requires:           iw
Requires:           nftables
Requires:           polkit
Requires:           procps-ng
Requires:           psmisc
Requires:           shadow-utils
Requires:           sudo
Requires:           systemd
Requires:           systemd-libs

%description
Windscribe's official Linux desktop VPN client, repackaged from its Fedora
x86_64 RPM. Includes the graphical client, helper service, and CLI.

%prep
actual=$(sha256sum %{SOURCE0} | cut -d ' ' -f 1)
if [ "$actual" != '%{digest}' ]; then
    echo "windscribe: sha256 mismatch (expected %{digest}, got $actual)" >&2
    exit 1
fi
mkdir -p extract
cd extract
rpm2cpio %{SOURCE0} | cpio -idm --quiet
test -x opt/windscribe/Windscribe
test -f usr/lib/systemd/system/windscribe-helper.service

%install
%__rm -rf %{buildroot}
install -dm755 %{buildroot}/opt/windscribe
cp -a extract/opt/windscribe/. %{buildroot}/opt/windscribe/

install -dm755 %{buildroot}%{_bindir}
ln -s /opt/windscribe/windscribe-cli %{buildroot}%{_bindir}/windscribe-cli
install -Dm644 extract/usr/lib/systemd/system/windscribe-helper.service \
    %{buildroot}%{_unitdir}/windscribe-helper.service
install -Dm644 extract/usr/lib/systemd/system-preset/69-windscribe-helper.preset \
    %{buildroot}%{_presetdir}/69-windscribe-helper.preset
install -Dm644 extract/usr/share/applications/windscribe.desktop \
    %{buildroot}%{_datadir}/applications/windscribe.desktop
cp -a extract/usr/share/icons %{buildroot}%{_datadir}/
install -Dm644 extract/etc/windscribe/autostart/windscribe.desktop \
    %{buildroot}%{_sysconfdir}/windscribe/autostart/windscribe.desktop
install -Dm644 /dev/stdin %{buildroot}%{_sysconfdir}/windscribe/platform <<'EOF'
linux_rpm_x64
EOF
install -Dm644 /dev/stdin %{buildroot}%{_sysusersdir}/windscribe.conf <<'EOF'
g windscribe -
u windscribe - "Windscribe service" - /sbin/nologin
EOF

%pre
%sysusers_create_compat %{_sysusersdir}/windscribe.conf

%post
%systemd_post windscribe-helper.service

%preun
%systemd_preun windscribe-helper.service

%postun
%systemd_postun windscribe-helper.service

%files
%{_unitdir}/windscribe-helper.service
%{_presetdir}/69-windscribe-helper.preset
%{_sysusersdir}/windscribe.conf
%{_bindir}/windscribe-cli
%{_datadir}/applications/windscribe.desktop
%{_datadir}/icons/hicolor/*/apps/Windscribe.png
%dir %{_sysconfdir}/windscribe
%dir %{_sysconfdir}/windscribe/autostart
%config(noreplace) %{_sysconfdir}/windscribe/platform
%{_sysconfdir}/windscribe/autostart/windscribe.desktop
%dir /opt/windscribe
%attr(2755,root,windscribe) /opt/windscribe/Windscribe
/opt/windscribe/helper
/opt/windscribe/lib/
/opt/windscribe/open_source_licenses.txt
/opt/windscribe/scripts/
/opt/windscribe/windscribe-cli
/opt/windscribe/windscribeamneziawg
/opt/windscribe/windscribectrld
/opt/windscribe/windscribeopenvpn
/opt/windscribe/windscribewstunnel

%changelog
* Fri Nov 06 2026 halcyon-linux <aahsnr041@proton.me> - 2.24.13-1
- Initial package: rewrap Windscribe's stable Fedora x86_64 GUI RPM

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
# Versioned by the custom sweep feed: ProtonVPN/python-proton-keyring-linux tags, HEAD-probing
# the official repo RPM URL zotero-style so a tag whose RPM build has not
# landed yet never bumps the spec.
%global             pv_fc 44
%global             pv_rel 1
%global             debug_package %{nil}
%global _build_id_links none
%global             __os_install_post %{nil}
Name:               python3-proton-keyring-linux
Version:            0.2.3
Release:            1%{?dist}
Summary:            Proton keyring component for Linux desktops
License:            GPL-3.0-or-later
URL:                https://github.com/ProtonVPN/python-proton-keyring-linux
BuildArch:          noarch
#!RemoteAsset
Source0:            https://repo.protonvpn.com/fedora-%{pv_fc}-stable/%{name}/%{name}-%{version}-%{pv_rel}.fc%{pv_fc}.noarch.rpm
BuildRequires:      python3-devel
BuildRequires:      python-srpm-macros
Requires:           gnome-keyring
Requires:           python3-keyring
Requires:           python3-proton-core
Requires:           python3-secretstorage
%description
The proton-keyring-linux component: credential storage through the
desktop keyring (libsecret / secret service). Repacked from Proton's
official Fedora repository.

%prep
mkdir -p extract
cd extract
rpm2cpio %{_sourcedir}/%{name}-%{version}-%{pv_rel}.fc%{pv_fc}.noarch.rpm | cpio -idm --quiet
test -d usr/lib/python3.14/site-packages/proton/keyring_linux

%install
%__rm -rf %{buildroot}
mkdir -p %{buildroot}%{python3_sitelib}
cp -a extract/usr/lib/python3.14/site-packages/proton %{buildroot}%{python3_sitelib}/
cp -a extract/usr/lib/python3.14/site-packages/proton_keyring_linux-*.dist-info %{buildroot}%{python3_sitelib}/
find %{buildroot} -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || :

%files
%{python3_sitelib}/proton/
%{python3_sitelib}/proton_keyring_linux-*/

%changelog
* Wed Sep 30 2026 halcyon-autoupdate <aahsnr041@proton.me> - 0.2.3-1
- initial package: vendor rewrap of the official repo.protonvpn.com RPM

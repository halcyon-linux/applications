# Repackaged from Google's prebuilt CLI tarball on the AUR antigravity-cli
# PKGBUILD pattern (2026-09-26): a single proprietary binary installed as
# /usr/bin/agy plus the packaging notice from the AUR tree. Proprietary
# payload, shipped as-is (no stripping, no debuginfo).
# There is no first-party version feed (the download URL embeds a
# non-derivable build id); the sweep reads pkgver off the AUR PKGBUILD.
Name:           antigravity-cli
Version:        1.2.12
Release:        1%{?dist}
Summary:        Google's agentic development platform (CLI companion)
License:        LicenseRef-Proprietary
URL:            https://antigravity.google/product/antigravity-cli
# Google's per-release build id in the download URL
%global cli_build 5784551402897408
#!RemoteAsset
Source0:        https://storage.googleapis.com/antigravity-public/antigravity-cli/%{version}-%{cli_build}/linux-x64/cli_linux_x64.tar.gz
Source1:        LICENSE

ExclusiveArch:  x86_64

Requires:       glibc
# the CLI authenticates and shares session state with the desktop app
Recommends:     antigravity-ide

%define debug_package %{nil}
%global _build_id_links none
%global __os_install_post %{nil}
# the payload must stay byte-identical to the vendor blob
%global __brp_strip %{nil}
%global __brp_strip_comment_note %{nil}
%global __brp_mangle_shebangs %{nil}

%description
The command-line companion of Google's Antigravity agentic development
platform, installed as /usr/bin/agy. Repackaged from the official
linux-x64 tarball.

%prep
%setup -q -c -T
tar -xzf %{SOURCE0}

%install
install -Dm755 antigravity %{buildroot}%{_bindir}/agy
install -Dm644 %{SOURCE1} %{buildroot}%{_licensedir}/%{name}/LICENSE

%files
%{_bindir}/agy
%license %{_licensedir}/%{name}/LICENSE

%changelog
* Sat Sep 26 2026 halcyon-autobuild - 1.2.10-1
- initial package: vendor linux-x64 binary rewrap on the AUR pattern
- version + build id swept from the AUR PKGBUILD

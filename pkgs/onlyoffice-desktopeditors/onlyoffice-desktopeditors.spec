# Rewrap of ONLYOFFICE's official vendor RPM (bitwarden pattern): upstream
# builds for el7 and publishes the prebuilt suite (bundled Qt5, CEF/Chromium
# and ICU under /opt/onlyoffice) with no source build feasible. The payload
# ships byte-identical; this spec only rehomes it for Fedora 44 and adds the
# AppStream metadata the vendor omits. Served from the aahsnr-work/halcyon
# Copr project like every other package (batch 4, the heavy wave).
#
# Prebuilt foreign binary: no build-id or debuginfo can be produced, so the
# debug package is disabled.
%global debug_package %{nil}

# Keep the payload byte-identical to the vendor blob: empty every ELF/bytes
# rewriting brp hook (verified against bitwarden's rewrap — rpm 6.0.2 needs
# them set to %%{nil}, not undefined, and the shebang mangler would rewrite
# the /usr/bin wrapper script).
%global __brp_strip %{nil}
%global __brp_strip_comment_note %{nil}
%global __brp_strip_lto %{nil}
%global __brp_strip_static_archive %{nil}
%global __brp_mangle_shebangs %{nil}
# the vendor payload carries hard-coded upstream rpaths (/opt/qt/5.9.9/...);
# check-rpaths hard-fails the build on them and the binaries are not ours to
# fix (Copr's brp set runs stricter than the previous buildroot, 2026-09-25)
%global __brp_check_rpaths %{nil}
# rpm writes /usr/lib/.build-id symlinks for every ELF in the payload (compat
# mode, with .1/.2/.3 dupes); with the debug package disabled nothing packages
# them and check-files fails — stop writing them (Copr, 2026-09-25)
%global _build_id_links none
%undefine __brp_add_determinism

# The bundle carries its own Qt5, CEF and ICU under /opt/onlyoffice
# (resolved via the app's RPATH, not the system loader). The dependency
# generator would otherwise advertise the bundled SONAMEs as provided by
# this package and satisfy DesktopEditors against Fedora's qt5 — exclude
# everything under /opt from both directions.
%global __provides_exclude_from ^/opt/onlyoffice/
%global __requires_exclude_from ^/opt/onlyoffice/

Name:           onlyoffice-desktopeditors
Version:        9.4.0
Release:        1%{?dist}
Summary:        Office productivity suite with text, spreadsheet and presentation editors

License:        AGPL-3.0-only
URL:            https://www.onlyoffice.com
ExclusiveArch:  x86_64

#!RemoteAsset
Source0:        https://github.com/ONLYOFFICE/DesktopEditors/releases/download/v%{version}/onlyoffice-desktopeditors.x86_64.rpm
# The vendor ships no AppStream metadata; this repo carries the Flathub
# project's curated metainfo (metadata_license CC0-1.0) under the app's own
# RDNS id, matching the Icon/StartupWMClass in the vendor desktop file.
Source1:        org.onlyoffice.desktopeditors.metainfo.xml

BuildRequires:  desktop-file-utils
BuildRequires:  appstream
BuildRequires:  cpio

# Runtime-only deps the ELF dependency generator cannot see, carried at
# parity with the vendor RPM's own declarations (fonts are required for
# correct document rendering; the rest are loaded indirectly or shelled out)
Requires:       dejavu-sans-fonts
Requires:       dejavu-sans-mono-fonts
Requires:       dejavu-serif-fonts
Requires:       liberation-mono-fonts
Requires:       liberation-narrow-fonts
Requires:       liberation-sans-fonts
Requires:       liberation-serif-fonts
Requires:       libnotify
Requires:       libXScrnSaver
Requires:       xdg-utils

%description
ONLYOFFICE Desktop Editors is an office suite with text, spreadsheet and
presentation editors with high OpenXML compatibility. This package rewraps
the upstream prebuilt Linux RPM for Fedora; the suite bundles its own Qt and
Chromium renderer under /opt/onlyoffice.

%prep
rpm2cpio %{SOURCE0} | cpio -idmu

%build
# Nothing to compile: the prebuilt upstream suite is unpacked in %%prep.

%install
cp -a opt %{buildroot}/
cp -a usr %{buildroot}/
# the vendor RPM was built with build-id links; nothing packages them
rm -rf %{buildroot}/usr/lib/.build-id
install -Dpm0644 %{SOURCE1} %{buildroot}%{_metainfodir}/org.onlyoffice.desktopeditors.metainfo.xml
# The vendor desktop file opens documents with the URL placeholder; editors expect
# file paths — switch to the file placeholder per the long-standing upstream bug every
# downstream repack patches
sed -i 's/%%U$/%%F/' %{buildroot}%{_datadir}/applications/onlyoffice-desktopeditors.desktop

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/onlyoffice-desktopeditors.desktop
appstreamcli validate --no-net %{buildroot}%{_metainfodir}/org.onlyoffice.desktopeditors.metainfo.xml

%files
%{_bindir}/onlyoffice-desktopeditors
%{_bindir}/desktopeditors
/opt/onlyoffice/
%{_datadir}/applications/onlyoffice-desktopeditors.desktop
%{_datadir}/icons/hicolor/*/apps/onlyoffice-desktopeditors.png
%{_metainfodir}/org.onlyoffice.desktopeditors.metainfo.xml
# the vendor payload ships its own docs and licenses — keep them
%{_datadir}/doc/onlyoffice-desktopeditors/
%license %{_datadir}/licenses/onlyoffice-desktopeditors/*

%changelog
* Fri Sep 25 2026 halcyon-autobump <aahsnr041@proton.me>
- initial import: rewrap of the vendor RPM; published on the R2 wave (the
  363 MB payload would take a third of the Pages budget)

# Ported from terrapkg/packages frawhide (anda/apps/zotero) on 2026-09-22 and
# adapted to this repo's Copr custom-source pipeline; the AUR zotero PKGBUILD
# is the reference for the runtime Requires, the symbolic icon and the
# launcher tweak. Deviations from upstream:
#   * Source0 is the OFFICIAL prebuilt Zotero tarball instead of building from
#     the git tag: upstream's prep (git_clone + npm install) and build
#     (npm run clean-build) fetch transient CI artifacts from
#     zotero-download.s3.amazonaws.com/ci/... which are gone (403) for the
#     current tags — the npm build cannot complete reliably for anyone, let
#     alone unattended. The official tarball is the output of the same
#     dir_build and carries zotero.desktop + the icons, so every install and
#     files line below is upstream's, just pointing at the unpacked tarball.
#   * the sweeper only ever lands on tags whose linux tarball is really
#     published on download.zotero.org (custom_zotero in ci/sweep/custom.py):
#     the 10.0.4 tag's tarball 403s upstream and killed the 2026-09-27
#     batch-0 submit in spectool, so the spec rides 10.0.3 until 10.0.4 is
#     republished or a fixed release lands.
#   * terra-appstream-helper / terra_appstream / desktop_file_install are
#     Terra-build-env macros — replaced with the plain Fedora equivalents
#     (marked inline). The hicolordir / appsdir helpers are defined below so the
#     upstream install and files lines stay untouched. desktop_file_install
#     also rewrote the desktop file's Exec and Icon to plain "zotero" — the
#     tarball file is written for the portable layout and both keys break in
#     a system install; the sed in install restores that rewrite.
#   * doc README.md / CONTRIBUTING.md and license COPYING dropped: the
#     official tarball ships neither.
%global debug_package %{nil}
%global _build_id_links none
%global appid org.zotero.Zotero
%global bundledir %{_libdir}/zotero
%global _hicolordir %{_datadir}/icons/hicolor
%global _appsdir %{_datadir}/applications

Name:           zotero
Version:        10.0.3
Release:        4%{?dist}
Summary:        Collect, organize, cite, and share your research sources
URL:            https://www.zotero.org/
License:        AGPL-3.0-or-later
ExclusiveArch:  x86_64

#!RemoteAsset
Source0:        https://download.zotero.org/client/release/%{version}/Zotero-%{version}_linux-x86_64.tar.xz
Source1:        %{appid}.metainfo.xml
Source2:        %{appid}.policies.json

BuildRequires:  desktop-file-utils
BuildRequires:  appstream

# dbus-glib and libXt are linked against from the system (not in the
# tarball's dependentlibs.list); nss mirrors the AUR package of the same
# prebuilt binary
Requires:       dbus-glib
Requires:       gtk3
Requires:       hicolor-icon-theme
Requires:       libXt
Requires:       nss
Requires:       xdg-utils

Packager:       Cypress Reed <cypress@fyralabs.com>

%description
Zotero is a free, easy-to-use tool to help you collect, organize, cite, and
share research sources.

%prep
%setup -q -c -T -a 0

%install
install -dm755 %{buildroot}%{bundledir}
# upstream: cp -a app/staging/Zotero_linux-*/* %{buildroot}%{bundledir}/
cp -a Zotero_linux-x86_64/* %{buildroot}%{bundledir}/

# AUR zotero PKGBUILD: prepend exec to the launcher's zotero-bin invocation
# so the wrapping shell exits on launch
sed -i 's|^"\$CALLDIR/zotero-bin"|exec "$CALLDIR/zotero-bin"|' \
    %{buildroot}%{bundledir}/zotero

install -dm755 %{buildroot}%{_bindir}
ln -sr %{buildroot}%{bundledir}/zotero %{buildroot}%{_bindir}/zotero

# RPM-managed installs must not self-update: disable the bundled updater via
# the Firefox-family enterprise policy path (the verify gates grep for it)
install -Dpm644 %{SOURCE2} %{buildroot}%{bundledir}/distribution/policies.json

# upstream:  desktop_file_install -k Exec,Icon -v zotero,zotero
# the tarball's desktop file is written for the portable layout — its Exec
# resolves against the .desktop file's own location (empty when launched
# from a menu) and its Icon carries an .ico extension that is not installed;
# rewrite both keys to the wrapper symlink installed above, as the terra
# helper did. That also drops the bash -c command substitutions F44's
# desktop-file-validate rejects inside quoted values.
install -Dpm644 %{buildroot}%{bundledir}/zotero.desktop \
    %{buildroot}%{_appsdir}/zotero.desktop
rm %{buildroot}%{bundledir}/zotero.desktop
sed -i -e 's|^Exec=.*|Exec=/usr/bin/zotero -url %%U|' \
       -e 's|^Icon=.*|Icon=zotero|' %{buildroot}%{_appsdir}/zotero.desktop

for size in 32 64 128; do
    install -Dpm644 %{buildroot}%{bundledir}/icons/icon${size}.png \
        %{buildroot}%{_hicolordir}/${size}x${size}/apps/zotero.png
done

# AUR zotero PKGBUILD also ships the symbolic icon (present in the tarball
# next to the sized PNGs) into the hicolor symbolic context
install -Dpm644 %{buildroot}%{bundledir}/icons/symbolic.svg \
    %{buildroot}%{_hicolordir}/symbolic/apps/zotero-symbolic.svg

# upstream: terra_appstream -o SOURCE1
install -Dpm644 %{SOURCE1} %{buildroot}%{_metainfodir}/%{appid}.metainfo.xml

%check
# upstream: %desktop_file_validate -f %{buildroot}%{_appsdir}/zotero.desktop
desktop-file-validate %{buildroot}%{_appsdir}/zotero.desktop
appstreamcli validate --no-net %{buildroot}%{_metainfodir}/%{appid}.metainfo.xml

%files
%{_bindir}/zotero
%{bundledir}/
%{_appsdir}/zotero.desktop
%{_hicolordir}/32x32/apps/zotero.png
%{_hicolordir}/64x64/apps/zotero.png
%{_hicolordir}/128x128/apps/zotero.png
%{_hicolordir}/symbolic/apps/zotero-symbolic.svg
%{_metainfodir}/%{appid}.metainfo.xml

%changelog
* Mon Sep 29 2026 halcyon-autoupdate <aahsnr041@proton.me> - 10.0.3-4
- ship distribution/policies.json (DisableAppUpdate) — RPM-managed installs
  must not self-update; the base-image verify gates grep for it

* Sun Sep 27 2026 Cypress Reed <cypress@fyralabs.com>
- back to 10.0.3: the 10.0.4 linux tarball is gone upstream (403) and killed
  the batch-0 submit job at spectool
- from the AUR PKGBUILD: Requires dbus-glib/nss/libXt, ship the symbolic
  icon, exec the launcher line
- rewrite the desktop file Exec/Icon for a system install (menu launches
  previously resolved against the .desktop's own location)

* Thu Sep 17 2026 Cypress Reed <cypress@fyralabs.com>
- initial commit

# Vendor rewrap of OpenAI's official ChatGPT desktop RPM (x86_64 only).
# The upstream RPM is fetched at SRPM-build time (Source0) and unpacked in
# %%prep with rpm2cpio; no build step. The version, the upstream release
# number and the RPM sha256 come from OpenAI's own yum repodata
# (ci/sweep/custom.py:custom_chatgpt_desktop).
#
# The packaging identity is the AUR chatgpt-desktop one: the upstream
# minimal launcher is replaced with the flags-file-aware one and the
# AppStream pkgname is retagged. The upstream RPM's /usr/bin/chatgpt is a
# symlink to /usr/lib/chatgpt/codex-launcher, so overwriting the launcher
# covers both entry points.
#
# Prebuilt foreign binary: no build-id or debuginfo can be produced, so the
# debug package is disabled and the brp hooks are emptied to keep the payload
# byte-identical to the upstream blob.
%global debug_package %{nil}
%global _build_id_links none
%global __os_install_post %{nil}

# NOTE: %%global debug_package %%{nil} is what makes the default ELF-rewriting
# brp hooks run, not what skips them — Fedora's %%__os_install_post gates
# brp-strip / brp-strip-comment-note on %%__debug_package being *undefined*.
# With them in place every ELF file in the bundle gets rewritten, so the
# packaged payload stops being byte-identical to the upstream blob.
# brp-strip-lto and brp-strip-static-archive are not gated at all. Empty all
# four so the payload matches the upstream blob bit for bit. Set them to
# %%{nil} rather than %%undefine'ing them: with rpm 6.0.2 %%undefine does not
# mask brp-strip / brp-strip-comment-note (the hooks still ran, while
# %%undefine on the lto one did take effect).
%global __brp_strip %{nil}
%global __brp_strip_comment_note %{nil}
%global __brp_strip_lto %{nil}
%global __brp_strip_static_archive %{nil}

# brp-mangle-shebangs is not an ELF hook but rewrites payload bytes just the
# same; unset it to keep byte-identity.
%global __brp_mangle_shebangs %{nil}

# add-determinism's brp hook would regenerate build-id links and otherwise
# normalize the payload. The blob must ship byte-identical.
%undefine __brp_add_determinism

# The bundled Electron/Chromium libs under /usr/lib/chatgpt carry SONAMEs,
# so the dependency generator would advertise them as system providers. They
# are private to the bundle, so suppress Provides from that directory and the
# Requires on the bundled libs nothing in Fedora provides. The node-hid
# prebuilds inside the bundle also carry Android-bionic, musl and ARM ELF
# objects whose bare sonames (libc.so, libdl.so, libm.so, liblog.so),
# namespaces (libc.so(LIBC), CXXABI_ARM_*, GCC_3.5) and companions
# (libc++_shared.so, libc.musl-*, the bundled libvips-cpp.so.8.18.7) are
# unresolvable — and libpthread.so.0(GLIBC_2.17) is a relic of upstream's
# older build toolchain: glibc 2.34+ serves the pthread symbols from
# libc.so.6, which these binaries also require and which resolves. The
# ([(]|$) anchors keep the Fedora glibc forms (libc.so.6, libdl.so.2,
# libm.so.6) out of the match. Brackets, not backslashes, escape the regex
# metacharacters: rpm consumes backslashes while expanding the macro, which
# left unbalanced parentheses that rpm silently discarded as an invalid regex
# (the previous revision's exclusions never applied).
%global __provides_exclude_from ^/usr/lib/chatgpt/
%global __requires_exclude ^libffmpeg[.]so|^libvulkan[.]so[.]1|^libEGL[.]so|^libGLESv2[.]so|^libvk_swiftshader[.]so|^libqt5_shim[.]so|^libqt6_shim[.]so|^libc[.]so([(]|$)|^libc[.]musl|^libc[+][+]_shared[.]so|^libdl[.]so([(]|$)|^libm[.]so([(]|$)|^liblog[.]so|^libpthread[.]so[.]0[(]GLIBC_2[.]17[)]|^libgcc_s[.]so[.]1[(]GCC_3[.]5[)]|^libstdc[+][+][.]so[.]6[(]CXXABI_ARM_|^libvips-cpp[.]so

# Pinned by the sweep from the upstream repodata; 'none' skips the check.
%global digest d5069043701a12760cce0447f7688859e9988dfbb04daaa9be0be0b762ff895f

# the upstream RPM's own release number, kept in sync by the sweep (it is
# part of the pool filename, not of our package NVR)
%global upstream_rel 1

Name:           chatgpt-desktop
Version:        26.1021.22027
Release:        4%{?dist}
Summary:        ChatGPT by OpenAI — official Linux desktop app
License:        LicenseRef-Proprietary
URL:            https://chatgpt.com/download
#!RemoteAsset
Source0:        https://persistent.oaistatic.com/codex-app-prod/linux/rpm/x86_64/chatgpt-%{version}-%{upstream_rel}.x86_64.rpm
Source1:        chatgpt-launcher.sh
Source2:        chatgpt-LICENSE
Source3:        com.openai.chatgpt.metainfo.xml

ExclusiveArch:  x86_64

BuildRequires:  appstream
BuildRequires:  coreutils
BuildRequires:  cpio
BuildRequires:  desktop-file-utils

# Runtime-only deps the ELF generator cannot see; linked libraries are
# auto-detected from DT_NEEDED and deliberately not repeated.
# - xdg-utils: the app shells out to xdg-open/xdg-settings.
# - libsecret: Electron uses it for keyring integration.
# - libnotify, libXScrnSaver: loaded indirectly via Electron.
# - libusb1, tpm2-tss: the upstream RPM requires libusb-1.0 and libtss2-esys.
# - xz: the upstream RPM requires xz (the bundled Codex uses it).
# - glib2: provides /usr/bin/gio, used by the app's desktop integration.
Requires:       xdg-utils
Requires:       libnotify
Requires:       libXScrnSaver
Requires:       libXtst
Requires:       libuuid
Requires:       libsecret
Requires:       mesa-libgbm
Requires:       at-spi2-core
Requires:       dbus
Requires:       alsa-lib
Requires:       nss
Requires:       gtk3
Requires:       libX11
Requires:       libXfixes
Requires:       libXrandr
Requires:       libXrender
Requires:       libXi
Requires:       libXcomposite
Requires:       libXdamage
Requires:       libXcursor
Requires:       libdrm
Requires:       libusb1
Requires:       tpm2-tss
Requires:       xz
Requires:       glib2

Recommends:     git

%description
ChatGPT desktop application for Linux, repackaged from OpenAI's official
RPM. The launcher honours ~/.config/chatgpt-flags.conf.

%prep
# Verify the vendored RPM against the digest the sweep pins in %%global digest.
# 'none' skips the check.
if [ '%{digest}' != 'none' ]; then
    actual="$(sha256sum %{SOURCE0} | cut -d' ' -f1)"
    if [ "$actual" != '%{digest}' ]; then
        echo "chatgpt-desktop: sha256 mismatch (expected %{digest}, got $actual)" >&2
        exit 1
    fi
    echo "chatgpt-desktop: sha256 verified"
fi

# Unpack the upstream RPM
rpm2cpio %{SOURCE0} | cpio -idmu

# The application license is OpenAI's terms (carried in the package dir);
# the upstream RPM ships LICENSE and LICENSES.chromium.html under
# /usr/lib/chatgpt/ for the bundled Electron runtime — the LICENSE file is
# the package's second license.
cp usr/lib/chatgpt/LICENSE LICENSE.electron
cp %{SOURCE2} LICENSE

%build
# Nothing to compile: the prebuilt upstream payload is unpacked in %%prep.

%install
cp -a usr %{buildroot}/

# Upstream's /etc (an AppArmor profile, the GPG keys and the
# yum.repos.d/chatgpt.repo drop-in of upstream's self-hosted repository)
# and the Debian-style doc tree have no consumer on Fedora — and the
# unclaimed doc files would fail the unpackaged-files check. Only usr/ is
# copied, so none of it is ever packaged; the doc tree must go.
rm -rf %{buildroot}%{_datadir}/doc/chatgpt

# Replace the upstream one-line launcher with the flags-file-aware one; the
# /usr/bin/chatgpt symlink points here, so both entry points honour the
# flags file.
install -Dm755 %{SOURCE1} %{buildroot}/usr/lib/chatgpt/codex-launcher

# Install the curated AppStream metainfo (the upstream one is minimal) and
# retag both metadata files for the Fedora package name.
install -Dm0644 %{SOURCE3} %{buildroot}%{_metainfodir}/com.openai.chatgpt.metainfo.xml
sed -i 's|<pkgname>chatgpt</pkgname>|<pkgname>chatgpt-desktop</pkgname>|' \
    %{buildroot}%{_metainfodir}/com.openai.chatgpt.metainfo.xml \
    %{buildroot}%{_datadir}/swcatalog/xml/com.openai.chatgpt.xml

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/chatgpt.desktop
appstreamcli validate --no-net %{buildroot}%{_metainfodir}/com.openai.chatgpt.metainfo.xml

%files
%license LICENSE LICENSE.electron
/usr/bin/chatgpt
/usr/lib/chatgpt/
%{_datadir}/applications/chatgpt.desktop
%{_metainfodir}/com.openai.chatgpt.metainfo.xml
%{_datadir}/swcatalog/xml/com.openai.chatgpt.xml
%{_datadir}/pixmaps/chatgpt.png

%changelog
* Tue Oct 27 2026 halcyon-linux <aahsnr041@proton.me> - 26.1021.22027-4
- Fix the requires exclusion: rpm strips backslashes when expanding the
  macro, so the regex was invalid and ignored. Use bracket escapes instead.

* Mon Oct 26 2026 halcyon-autoupdate <aahsnr041@proton.me> - 26.1021.22027-3
- Exclude the bundle-private sonames the dependency generator picks up from
  the node-hid prebuilds (bionic/musl/ARM forms, libc++_shared.so, the
  bundled libvips-cpp) and the libpthread.so.0(GLIBC_2.17) build-toolchain
  relic — repoclosure flagged 18 unresolved deps on -2

* Mon Oct 26 2026 halcyon-autoupdate <aahsnr041@proton.me> - 26.1021.22027-2
- Rewrap the official upstream RPM instead of the Debian package; the
  curated AppStream metainfo replaces upstream's minimal one and the
  flags-file-aware launcher is kept. License files are OpenAI's terms plus
  the bundled Electron runtime's LICENSE. Upstream's /etc machinery
  (AppArmor profile, GPG keys, self-repo drop-in) and the Debian-style doc
  tree are not packaged.

* Mon Oct 26 2026 halcyon-autoupdate <aahsnr041@proton.me> - 26.1021.22027-1
- Initial package: rewrap of OpenAI's official Debian package

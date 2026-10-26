# Vendor rewrap of OpenAI's official ChatGPT Debian package (x86_64 only).
# The .deb is fetched at SRPM-build time (Source0) and unpacked in %%prep with
# ar; no build step. The version and the .deb sha256 come from OpenAI's apt
# Packages index (ci/sweep/custom.py:custom_chatgpt_desktop).
#
# This is the AUR chatgpt-desktop packaging: the upstream minimal launcher is
# replaced with the flags-file-aware one, the AppStream pkgname is retagged,
# and the Debian-only apt/AppArmor machinery is dropped. It ships the same
# application files as the chatgpt RPM rewrap, so the two packages conflict.
#
# Prebuilt foreign binary: no build-id or debuginfo can be produced, so the
# debug package is disabled and the brp hooks are emptied to keep the payload
# byte-identical.
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
# Requires on the bundled libs nothing in Fedora provides.
%global __provides_exclude_from ^/usr/lib/chatgpt/
%global __requires_exclude ^libffmpeg\.so|^libvulkan\.so\.1|^libEGL\.so|^libGLESv2\.so|^libvk_swiftshader\.so|^libqt5_shim\.so|^libqt6_shim\.so

# Pinned by the sweep from the apt Packages index; 'none' skips the check.
%global digest eb0831c734f154f93f8ebcf0e17d118da0dea7dc1737dc61a1e71444375bf190

Name:           chatgpt-desktop
Version:        26.1021.22027
Release:        1%{?dist}
Summary:        ChatGPT by OpenAI — official Linux desktop app, Debian rewrap
License:        LicenseRef-Proprietary
URL:            https://chatgpt.com/download
#!RemoteAsset
Source0:        https://persistent.oaistatic.com/codex-app-prod/linux/deb/pool/main/c/chatgpt/chatgpt_%{version}_amd64.deb
Source1:        chatgpt-launcher.sh
Source2:        chatgpt-LICENSE

ExclusiveArch:  x86_64

BuildRequires:  appstream
BuildRequires:  binutils
BuildRequires:  coreutils
BuildRequires:  desktop-file-utils
BuildRequires:  xz

# Runtime-only deps the ELF generator cannot see; linked libraries are
# auto-detected from DT_NEEDED and deliberately not repeated.
# - xdg-utils: the app shells out to xdg-open/xdg-settings.
# - libsecret: Electron uses it for keyring integration.
# - libnotify, libXScrnSaver: loaded indirectly via Electron.
# - libusb1, tpm2-tss: upstream-declared Debian dependencies.
# - xz: upstream Depends: xz-utils (the bundled Codex uses it).
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

Conflicts:      chatgpt

%description
ChatGPT desktop application for Linux, repackaged from OpenAI's official
Debian package. The launcher honours ~/.config/chatgpt-flags.conf. This
package installs the same application files as the chatgpt RPM rewrap, so
the two packages conflict; install one or the other.

%prep
if [ '%{digest}' != 'none' ]; then
    actual="$(sha256sum %{SOURCE0} | cut -d' ' -f1)"
    if [ "$actual" != '%{digest}' ]; then
        echo "chatgpt-desktop: sha256 mismatch (expected %{digest}, got $actual)" >&2
        exit 1
    fi
    echo "chatgpt-desktop: sha256 verified"
fi

# A .deb is an ar archive: data.tar.xz is the file payload.
ar p %{SOURCE0} data.tar.xz > data.tar.xz
tar -xJf data.tar.xz

# The Debian copyright file covers the bundled Electron runtime; the upstream
# terms pointer is the application license.
cp usr/share/doc/chatgpt/copyright LICENSE.electron
cp %{SOURCE2} LICENSE

%build
# Nothing to compile: the prebuilt upstream payload is unpacked in %%prep.

%install
cp -a usr %{buildroot}/

# Replace the upstream one-line launcher with the flags-file-aware one.
install -Dm755 %{SOURCE1} %{buildroot}/usr/lib/chatgpt/codex-launcher

# Retag the AppStream metadata for the Fedora package name.
sed -i 's|<pkgname>chatgpt</pkgname>|<pkgname>chatgpt-desktop</pkgname>|' \
    %{buildroot}%{_metainfodir}/com.openai.chatgpt.metainfo.xml \
    %{buildroot}%{_datadir}/swcatalog/xml/com.openai.chatgpt.xml

# Debian-only integration: the AppArmor profile and the apt repository setup
# in the deb's maintainer scripts have no equivalent on Fedora (SELinux).
rm -rf %{buildroot}/etc

# Debian's linter override and doc tree have no consumer on Fedora.
rm -rf %{buildroot}%{_datadir}/doc/chatgpt %{buildroot}%{_datadir}/lintian

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
* Mon Oct 26 2026 halcyon-autoupdate <aahsnr041@proton.me> - 26.1021.22027-1
- Initial package: rewrap of OpenAI's official Debian package

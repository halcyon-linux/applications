# Vendor rewrap of the community claude-desktop-extra build's x86_64 RPM.
# The release asset is self-contained (Electron tree, patched app.asar, the
# Wayland-aware launcher, desktop file, icons, GNOME search provider and MIME
# registration), so the RPM's payload is installed as-is. No build step.
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

# The bundled Electron/Chromium libs under /usr/lib/claude-desktop carry
# SONAMEs, so the dependency generator would advertise them as system
# providers. They are private to the bundle, so suppress Provides from that
# directory and the Requires on the bundled libs nothing in Fedora provides.
%global __provides_exclude_from ^/usr/lib/claude-desktop/
%global __requires_exclude ^libffmpeg\.so|^libvulkan\.so\.1|^libvk_swiftshader\.so

# Upstream releases re-use a base version for several builds (v3.6556.2-7);
# extra_rel is the release number after the dash. The sweep pins both it and
# the RPM sha256 from the GitHub release asset digest.
%global extra_rel 7
%global digest 6f3a2e914ae6a6f76448ee185d7a3d157d8d70a2256b9ff096d561493f93681f

Name:           claude-desktop-extra
Version:        3.6556.2
Release:        1%{?dist}
Summary:        Claude Desktop with Computer Use, themes, multi-profile and Quick Entry
License:        LicenseRef-Proprietary
URL:            https://github.com/patrickjaja/claude-desktop-extra
#!RemoteAsset
Source0:        https://github.com/patrickjaja/claude-desktop-extra/releases/download/v%{version}-%{extra_rel}/claude-desktop-extra-%{version}-%{extra_rel}.x86_64.rpm

ExclusiveArch:  x86_64

BuildRequires:  cpio
BuildRequires:  coreutils
BuildRequires:  desktop-file-utils

# The upstream RPM's own non-ELF requirements, plus the icon theme. Linked
# libraries are auto-detected from DT_NEEDED and deliberately not repeated.
Requires:       bash
Requires:       xdg-utils
Requires:       libnotify
Requires:       libXScrnSaver
Requires:       libXtst
Requires:       libdrm
Requires:       libsecret
Requires:       mesa-libgbm
Requires:       at-spi2-core
Requires:       alsa-lib
Requires:       nss
Requires:       gtk3
Requires:       pipewire-libs
Requires:       xdg-desktop-portal
Requires:       hicolor-icon-theme
Requires:       shared-mime-info

# The extra build bundles its own virtiofsd and uses the system one when it is
# installed; Cowork's QEMU stack and the desktop integration stay soft, as in
# the Arch package's optdepends.
Recommends:     qemu-system-x86
Recommends:     edk2-ovmf
Recommends:     virtiofsd
Recommends:     bubblewrap
Recommends:     socat
Recommends:     gjs
Recommends:     gnome-keyring
Recommends:     libayatana-appindicator-gtk3
Recommends:     openssh
Recommends:     xdg-desktop-portal-gtk

Conflicts:      claude-desktop

%description
Claude Desktop based on Anthropic's official Linux build, with Computer Use,
custom themes, multi-profile and Quick Entry. This package rewraps the
upstream project's self-contained x86_64 RPM for Fedora. It installs the same
application files as claude-desktop, so the two packages conflict.

%prep
if [ '%{digest}' != 'none' ]; then
    actual="$(sha256sum %{SOURCE0} | cut -d' ' -f1)"
    if [ "$actual" != '%{digest}' ]; then
        echo "claude-desktop-extra: sha256 mismatch (expected %{digest}, got $actual)" >&2
        exit 1
    fi
    echo "claude-desktop-extra: sha256 verified"
fi

rpm2cpio %{SOURCE0} | cpio -idmu
cp usr/share/licenses/claude-desktop-extra/copyright LICENSE

%build
# Nothing to compile: the prebuilt upstream RPM is unpacked in %%prep.

%install
cp -a usr %{buildroot}/

# chrome-sandbox is Chromium's setuid helper. The upstream RPM's postinstall
# script sets 4755; a rewrap carries no scriptlets, so set it here.
chmod 4755 %{buildroot}/usr/lib/claude-desktop/chrome-sandbox

# Replaced by the %%license file above.
rm -rf %{buildroot}/usr/share/licenses/claude-desktop-extra

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/com.anthropic.Claude.desktop

%files
%license LICENSE
%{_bindir}/claude-desktop
/usr/lib/claude-desktop/
%{_datadir}/applications/com.anthropic.Claude.desktop
%{_datadir}/icons/hicolor/*/apps/claude-desktop.png
%{_datadir}/gnome-shell/search-providers/com.anthropic.Claude.search-provider.ini
%{_datadir}/dbus-1/services/com.anthropic.Claude.SearchProvider.service
%{_datadir}/mime/packages/com.anthropic.Claude.xml

%changelog
* Mon Oct 26 2026 halcyon-autoupdate <aahsnr041@proton.me> - 3.6556.2-1
- Initial package: rewrap of the claude-desktop-extra x86_64 RPM

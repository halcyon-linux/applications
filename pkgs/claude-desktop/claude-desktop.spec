# Vendor rewrap of Anthropic's official Debian package. Only the .deb's file
# payload (data.tar.xz) is used: its maintainer scripts do Debian-specific
# work (apt repository registration, AppArmor), none of which applies to
# Fedora. The payload's top-level tree is installed as-is; the launcher and
# the postinst-managed desktop integration files are added below.
#
# The version and the .deb sha256 come from Anthropic's apt Packages index
# (ci/sweep/custom.py:custom_claude_desktop); the digest is verified in
# %%prep.
#
# Prebuilt foreign binary: no build-id or debuginfo can be produced, so the
# debug package is disabled and the payload is kept byte-identical to the
# vendor blob.
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
# providers. They are private to the bundle (resolved via the $ORIGIN RPATH),
# so suppress Provides from that directory and the Requires on the bundled
# libs nothing in Fedora provides.
%global __provides_exclude_from ^/usr/lib/claude-desktop/
%global __requires_exclude ^libffmpeg[.]so|^libvulkan[.]so[.]1|^libvk_swiftshader[.]so

# Pinned by the sweep from the apt Packages index; 'none' skips the check.
%global digest 4aa0f763d6c05ac79502392dd50f5d7f5c455b2f0a405d5bdf1554acd8342a89

Name:           claude-desktop
Version:        4.29.0
Release:        1%{?dist}
Summary:        Official Claude AI desktop app — Chat, Cowork, and Claude Code
License:        LicenseRef-Proprietary
URL:            https://claude.com/download
#!RemoteAsset
Source0:        https://downloads.claude.ai/claude-desktop/apt/stable/pool/main/c/claude-desktop/claude-desktop_%{version}_amd64.deb
Source1:        claude-desktop.sh

ExclusiveArch:  x86_64

BuildRequires:  binutils
BuildRequires:  coreutils
BuildRequires:  desktop-file-utils
BuildRequires:  xz

# Runtime-only deps the ELF generator cannot see. Linked libs (gtk3, nss,
# cairo, ...) are auto-detected from DT_NEEDED and deliberately not repeated.
# - xdg-utils: the app shells out to xdg-open.
# - libsecret: Chromium dlopen()s it for keyring storage.
# - libnotify, libXScrnSaver, libXtst: Electron loads them indirectly.
# - pipewire-libs: upstream's Depends (screen sharing / audio).
# - virtiofsd: Cowork checks /usr/libexec/virtiofsd (Fedora's path).
# - bubblewrap, socat: Claude Code shell sandbox (upstream Recommends).
# - libcap-ng, libseccomp: linked by the bundled virtiofsd.
Requires:       bash
Requires:       xdg-utils
Requires:       libsecret
Requires:       libnotify
Requires:       libXScrnSaver
Requires:       libXtst
Requires:       libuuid
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
Requires:       pipewire-libs
Requires:       libcap-ng
Requires:       libseccomp
Requires:       bubblewrap
Requires:       socat
Requires:       virtiofsd
Requires:       xdg-desktop-portal
Requires:       hicolor-icon-theme
Requires:       shared-mime-info

# Cowork (the agent workspace VM) needs QEMU + UEFI firmware. Upstream ships
# them as Recommends; dnf installs weak deps by default, so the out-of-box
# experience matches apt while image builds can opt out.
Recommends:     qemu-system-x86
Recommends:     edk2-ovmf
Recommends:     gjs
Recommends:     libayatana-appindicator-gtk3
Recommends:     gnome-keyring
Recommends:     xdg-desktop-portal-gtk
Recommends:     openssh
Recommends:     ca-certificates

Conflicts:      claude-desktop-extra

%description
Official Claude desktop application from Anthropic: Chat, Cowork, and
Claude Code in one native app. This package rewraps the upstream Debian
package for Fedora and installs its file payload as shipped, with the
Wayland-aware launcher and the GNOME search provider / MIME registration
that the Debian postinst would otherwise create.

%prep
if [ '%{digest}' != 'none' ]; then
    actual="$(sha256sum %{SOURCE0} | cut -d' ' -f1)"
    if [ "$actual" != '%{digest}' ]; then
        echo "claude-desktop: sha256 mismatch (expected %{digest}, got $actual)" >&2
        exit 1
    fi
    echo "claude-desktop: sha256 verified"
fi

# A .deb is an ar archive: data.tar.xz is the file payload.
ar p %{SOURCE0} data.tar.xz > data.tar.xz
tar -xJf data.tar.xz

# Ship the Debian copyright text as the package license.
cp usr/share/doc/claude-desktop/copyright LICENSE

%build
# Nothing to compile: the prebuilt upstream payload is unpacked in %%prep.

%install
cp -a usr %{buildroot}/

# Upstream's /usr/bin/claude-desktop is a bare symlink to the Electron
# binary, which leaves Electron on its X11 default (blurry under Wayland).
# Replace it with the launcher the Arch package uses: it selects the Wayland
# backend and honours ~/.config/claude-desktop-flags.conf.
rm -f %{buildroot}%{_bindir}/claude-desktop
install -Dm755 %{SOURCE1} %{buildroot}%{_bindir}/claude-desktop

# chrome-sandbox is Chromium's setuid helper; the .deb's postinst sets 4755.
chmod 4755 %{buildroot}/usr/lib/claude-desktop/chrome-sandbox

# The .deb's postinst installs these desktop-integration files from resources/.
# On Fedora they are package files instead.
install -pDm644 %{buildroot}/usr/lib/claude-desktop/resources/gnome-search-provider/com.anthropic.Claude.search-provider.ini \
    %{buildroot}%{_datadir}/gnome-shell/search-providers/com.anthropic.Claude.search-provider.ini
install -pDm644 %{buildroot}/usr/lib/claude-desktop/resources/gnome-search-provider/com.anthropic.Claude.SearchProvider.service \
    %{buildroot}%{_datadir}/dbus-1/services/com.anthropic.Claude.SearchProvider.service
install -pDm644 %{buildroot}/usr/lib/claude-desktop/resources/linux-mime/com.anthropic.Claude.xml \
    %{buildroot}%{_datadir}/mime/packages/com.anthropic.Claude.xml

# Debian's linter override and the doc tree have no consumer on Fedora.
rm -rf %{buildroot}/usr/share/lintian %{buildroot}/usr/share/doc/claude-desktop

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
* Tue Oct 27 2026 halcyon-linux <aahsnr041@proton.me> - 3.6556.2-2
- Escape the __requires_exclude regex with brackets: rpm strips backslashes while
  expanding the macro, leaving a loose pattern (the bug that silently disabled
  chatgpt-desktop's exclusion)

* Mon Oct 26 2026 halcyon-autoupdate <aahsnr041@proton.me> - 3.6556.2-1
- Initial package: rewrap of Anthropic's official Debian package

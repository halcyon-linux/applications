# Vendor rewrap of JupyterLab Desktop's official Fedora RPM — upstream
# publishes a self-contained RPM at each GitHub release. The tag format is
# vX.Y.Z-N (e.g. v4.6.3-1) where X.Y.Z is the JupyterLab version and N is
# the desktop build number; the sweep extracts X.Y.Z as Version and pins the
# full tag in %%global upstream_tag for the Source URL. The RPM filename
# carries no version (JupyterLab-Setup-Fedora-x64.rpm), so the tag is
# required for the download URL. The payload stays byte-identical.
%global             debug_package %{nil}
%global _build_id_links none
%global             __os_install_post %{nil}

# The bundled libraries carry SONAMEs; exclude them from system Provides.
%global __provides_exclude_from ^%{_libdir}/jupyterlab-desktop/
# The Requires on the bundled Chromium libs nothing in Fedora provides are
# dropped as well. Brackets, not backslashes, escape regex metacharacters:
# rpm consumes backslashes while expanding the macro.
%global __requires_exclude ^libffmpeg[.]so|^libvulkan[.]so[.]1|^libEGL[.]so|^libGLESv2[.]so|^libvk_swiftshader[.]so

Name:           jupyterlab-desktop
Version:        4.6.3
Release:        1%{?dist}
Summary:        JupyterLab Desktop — cross-platform desktop application for JupyterLab
License:        BSD-3-Clause
URL:            https://jupyterlab.github.io/jupyterlab-desktop/
# The full tag (vX.Y.Z-N) is pinned in %%global upstream_tag by the sweep.
%global upstream_tag v4.6.3-1
# The RPM sha256 digest is pinned by the sweep (or 'none' when upstream
# publishes no digest). Verified in %%prep.
%global digest 704a3c432256a024e8fa37d0a50f227c5f5b752db4e1c069a38dcdd800564155
Source0:        https://github.com/jupyterlab/jupyterlab-desktop/releases/download/%{upstream_tag}/JupyterLab-Setup-Fedora-x64.rpm
Source1:        https://raw.githubusercontent.com/jupyterlab/jupyterlab-desktop/%{upstream_tag}/LICENSE

ExclusiveArch:  x86_64

# Vendor RPM deps (Electron runtime)
Requires:       gtk3
Requires:       nss
Requires:       libXScrnSaver
Requires:       libXtst
Requires:       libuuid
Requires:       at-spi2-core
Requires:       libnotify
Requires:       libsecret
Requires:       xdg-utils

%description
JupyterLab Desktop is a cross-platform desktop application that allows you to
run JupyterLab locally without a browser. This package rewraps the official
Fedora RPM published by the JupyterLab project at each GitHub release.

%prep
%setup -q -c -T
rpm2cpio %{_sourcedir}/JupyterLab-Setup-Fedora-x64.rpm | cpio -idmu

# Verify the RPM against the digest upstream publishes on the release
# (skipped when upstream publishes none — %%global digest is 'none' then).
if [ '%{digest}' != 'none' ]; then
    actual="$(sha256sum %{_sourcedir}/JupyterLab-Setup-Fedora-x64.rpm | cut -d' ' -f1)"
    if [ "$actual" != '%{digest}' ]; then
        echo "jupyterlab-desktop: sha256 mismatch (expected %{digest}, got $actual)" >&2
        exit 1
    fi
    echo "jupyterlab-desktop: sha256 verified"
fi

%install
%__rm -rf %{buildroot}

# The vendor RPM installs to /opt/jupyterlab-desktop — move it to our private libdir
install -dm755 %{buildroot}%{_libdir}
mv opt/jupyterlab-desktop %{buildroot}%{_libdir}/jupyterlab-desktop

# System launcher in /usr/bin
mkdir -p %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/jupyterlab-desktop <<'EOF'
#!/bin/sh
exec %{_libdir}/jupyterlab-desktop/jupyterlab-desktop "$@"
EOF
chmod 755 %{buildroot}%{_bindir}/jupyterlab-desktop

# Desktop file (vendor provides one at /usr/share/applications/jupyterlab-desktop.desktop)
%__install -Dm644 usr/share/applications/jupyterlab-desktop.desktop \
    %{buildroot}%{_datadir}/applications/jupyterlab-desktop.desktop

# Icons (vendor provides hicolor icons)
cp -a usr/share/icons %{buildroot}%{_datadir}/icons

# License
%__install -Dm644 %{SOURCE1} %{buildroot}%{_licensedir}/jupyterlab-desktop/LICENSE

%files
%{_bindir}/jupyterlab-desktop
%{_libdir}/jupyterlab-desktop/
%{_datadir}/applications/jupyterlab-desktop.desktop
%{_datadir}/icons/hicolor/*/apps/jupyterlab-desktop.png
%{_licensedir}/jupyterlab-desktop/LICENSE

%changelog
* Tue Oct 27 2026 halcyon-linux <aahsnr041@proton.me> - 4.6.3-1
- Initial package: vendor RPM rewrap of JupyterLab Desktop official Fedora RPM
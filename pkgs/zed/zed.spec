# Vendor rewrap of upstream's self-contained zed-linux tarball — the same
# archive zed.dev/install.sh deploys (bin/zed CLI, libexec/zed-editor, the
# bundled lib/ tree, desktop file and icons). Allowed for self-contained
# release archives per repo rules; the full brp nil set follows
# obsidian.spec. Reference for a source build of the same content: Terra's
# anda/devs/zed/stable spec (not used here — a 1-2h Copr build on every
# fortnightly upstream release).
%global             debug_package %{nil}
%global _build_id_links none
%global             __os_install_post %{nil}

Name:               zed
Version:            1.21.0
Release:            1%{?dist}
Summary:            A high-performance, multiplayer code editor
License:            Apache-2.0 AND GPL-3.0-or-later
URL:                https://zed.dev
Source0:            https://github.com/zed-industries/zed/releases/download/v%{version}/zed-linux-x86_64.tar.gz
Source1:            https://raw.githubusercontent.com/zed-industries/zed/v%{version}/LICENSE-APACHE
Source2:            https://raw.githubusercontent.com/zed-industries/zed/v%{version}/LICENSE-GPL

ExclusiveArch:      x86_64

Recommends:         git-core

%description
Zed is a high-performance, multiplayer code editor from the creators of
Atom and Tree-sitter. This packages upstream's self-contained Linux
tarball: the app tree installs to libdir, the zed CLI is exposed on PATH
via a symlink (the same mechanism zed.dev/install.sh uses).

%prep
%setup -q -c -T -a 0

%install
%__rm -rf %{buildroot}

install -dm755 %{buildroot}%{_libdir}
%__cp -r zed.app %{buildroot}%{_libdir}/zed.app

# upstream's own install.sh symlinks the CLI onto PATH, so the binary's
# libexec discovery works through the symlink
mkdir -p %{buildroot}%{_bindir}
ln -s %{_libdir}/zed.app/bin/zed %{buildroot}%{_bindir}/zed

%__install -Dm644 zed.app/share/applications/dev.zed.Zed.desktop \
    %{buildroot}%{_datadir}/applications/dev.zed.Zed.desktop
%__install -Dm644 zed.app/share/icons/hicolor/512x512/apps/zed.png \
    %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/zed.png
%__install -Dm644 zed.app/share/icons/hicolor/1024x1024/apps/zed.png \
    %{buildroot}%{_datadir}/icons/hicolor/1024x1024/apps/zed.png

%__install -Dm644 zed.app/licenses.md %{buildroot}%{_licensedir}/zed/licenses.md
%__install -Dm644 %{SOURCE1} %{buildroot}%{_licensedir}/zed/LICENSE-APACHE
%__install -Dm644 %{SOURCE2} %{buildroot}%{_licensedir}/zed/LICENSE-GPL

%files
%{_bindir}/zed
%{_libdir}/zed.app/
%{_datadir}/applications/dev.zed.Zed.desktop
%{_datadir}/icons/hicolor/512x512/apps/zed.png
%{_datadir}/icons/hicolor/1024x1024/apps/zed.png
%{_licensedir}/zed/

%changelog
* Mon Sep 28 2026 ahsan <aahsnr041@proton.me> - 1.21.0-1
- initial package (vendor rewrap of the self-contained release tarball,
  shape per obsidian.spec)

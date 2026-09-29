# Source build of GNU Emacs 31.1 from the official ftp.gnu.org tarball, kept
# in this repo because Fedora ships no pgtk emacs and the halcyon image wants
# the maintainer's exact configuration: pure-GTK Wayland windowing (gtk3),
# cairo drawing, harfbuzz shaping, libsystemd sd_notify, dynamic modules,
# tree-sitter and ahead-of-time native compilation (native-compilation=aot
# compiles every Lisp file during the build — expect a long Copr build;
# preloaded .eln live under /usr/lib/emacs/31.1/native-lisp, matching the
# libexecdir=/usr layout of the manual recipe).
# Beyond the explicit flags the build auto-enables whatever the BuildRequires
# provide: gnutls, dbus, gpm, gmp bignums, sqlite, the built-in JSON parser,
# svg/webp/tiff/jpeg/png/gif image support and ALSA sound.
# Sweep: custom_emacs_pgtk in ci/sweep/custom.py (emacs-mirror/emacs tags are
# "emacs-<version>" and pretest tarballs live on alpha.gnu.org, so tags are
# ranked with rpmvercmp and the ftp.gnu.org tarball is HEAD-probed zotero-style).
# Registration: ci/packages.toml (batch 0 — every BuildRequire is Fedora-side).
Name:           emacs-pgtk
Version:        31.1
Release:        1%{?dist}
%define debug_package %{nil}
Summary:        GNU Emacs with a pure-GTK (Wayland) UI, native compilation and tree-sitter
License:        GPL-3.0-or-later
URL:            https://www.gnu.org/software/emacs/
Source0:        https://ftp.gnu.org/gnu/emacs/emacs-%{version}.tar.xz

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  texinfo
BuildRequires:  desktop-file-utils
BuildRequires:  gtk3-devel
BuildRequires:  cairo-devel
BuildRequires:  harfbuzz-devel
BuildRequires:  libgccjit-devel
BuildRequires:  libtree-sitter-devel
BuildRequires:  systemd-devel
BuildRequires:  dbus-devel
BuildRequires:  gnutls-devel
BuildRequires:  libxml2-devel
BuildRequires:  ncurses-devel
BuildRequires:  gpm-devel
BuildRequires:  libacl-devel
BuildRequires:  gmp-devel
BuildRequires:  sqlite-devel
BuildRequires:  alsa-lib-devel
BuildRequires:  libjpeg-turbo-devel
BuildRequires:  libpng-devel
BuildRequires:  giflib-devel
BuildRequires:  libtiff-devel
BuildRequires:  libwebp-devel
BuildRequires:  librsvg2-devel

Requires(post): info
Requires(postun): info

%description
GNU Emacs is an extensible, customizable text editor and computing
environment. This is the pure-GTK (pgtk) build: it renders through GTK 3 and
runs natively on Wayland (and X11 via XWayland) with no X toolkit dependency,
configured with cairo drawing, harfbuzz text shaping, dynamic modules,
tree-sitter parsing and ahead-of-time native compilation of the Lisp tree,
so package Lisp ships pre-compiled with no deferred compilation on first use.

%prep
%autosetup -n emacs-%{version} -p1

%build
%configure \
  --disable-build-details \
  --with-pgtk \
  --with-cairo \
  --with-harfbuzz \
  --with-libsystemd \
  --with-modules \
  --with-native-compilation=aot \
  --with-tree-sitter \
  --with-systemduserunitdir=%{_userunitdir}
%make_build

%install
%make_install
rm -f %{buildroot}%{_infodir}/dir

%check
desktop-file-validate %{buildroot}%{_datadir}/applications/*.desktop

%files
%license COPYING
%{_bindir}/*
%{_libexecdir}/emacs/
%{_libdir}/emacs/
%{_includedir}/emacs-module.h
%{_datadir}/emacs/
%{_datadir}/glib-2.0/schemas/org.gnu.emacs.defaults.gschema.xml
%{_datadir}/applications/emacs*.desktop
%{_metainfodir}/*.xml
%{_datadir}/icons/hicolor/*/*/*
%{_infodir}/*
%{_mandir}/man1/*
%{_userunitdir}/emacs.service

%post
for f in %{_infodir}/*.info %{_infodir}/*.info.gz; do
    %{_sbindir}/install-info "$f" %{_infodir}/dir || :
done

%preun
if [ "$1" = 0 ]; then
    for f in %{_infodir}/*.info %{_infodir}/*.info.gz; do
        %{_sbindir}/install-info --delete "$f" %{_infodir}/dir || :
    done
fi

%changelog
* Mon Sep 28 2026 halcyon-autoupdate <aahsnr041@proton.me> - 31.1-1
- initial packaging: pgtk build with ahead-of-time native compilation,
  tree-sitter, cairo and harfbuzz per the maintainer's from-source recipe

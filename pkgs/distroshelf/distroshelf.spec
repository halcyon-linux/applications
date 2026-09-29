# DistroShelf — container-manager desktop app (ranfdev/DistroShelf).
# Build flow follows upstream's meson.build: meson + cargo (crates are fetched
# from crates.io during %build — the Copr project runs with --enable-net on),
# gnome.post_install() artifacts (gschemas.compiled, icon-theme.cache) are
# removed from the buildroot: glib2's and gtk's file triggers compile them on
# installed systems. distroshelf-helper.sh is this repo's host-side
# integration file (shipped as Source1, not an upstream file).
Name:           distroshelf
Version:	1.5.2
Release:        1%{?dist}
%define debug_package %{nil}
Summary:        Container manager for container-based workflows
License:        GPL-3.0-or-later
URL:            https://github.com/ranfdev/DistroShelf
Source0:        %{url}/archive/refs/tags/v%{version}/DistroShelf-%{version}.tar.gz
Source1:        distroshelf-helper.sh

BuildRequires:  meson
BuildRequires:  gcc
BuildRequires:  cargo
BuildRequires:  rust
BuildRequires:  gettext
BuildRequires:  desktop-file-utils
BuildRequires:  pkgconfig(gtk4)
BuildRequires:  pkgconfig(libadwaita-1)
# vte4-sys needs the GTK4 VTE pkg-config module (vte-2.91-gtk4)
BuildRequires:  vte291-gtk4-devel

%description
GUI to manage containers and box instances.

%prep
# GitHub's archive dir is DistroShelf-<version> (capital D)
%autosetup -n DistroShelf-%{version} -p1

%build
%meson
%meson_build

%install
%meson_install
# gnome.post_install() ran against the DESTDIR; the packaged system compiles
# these via file triggers (glib2, gtk)
rm -f %{buildroot}%{_datadir}/glib-2.0/schemas/gschemas.compiled
rm -f %{buildroot}%{_datadir}/icons/hicolor/icon-theme.cache
install -Dm0755 %{SOURCE1} %{buildroot}%{_bindir}/distroshelf-helper

%find_lang %{name}

%files -f %{name}.lang
%license COPYING
%doc README.md
%{_bindir}/distroshelf
%{_bindir}/distroshelf-helper
%{_datadir}/distroshelf/
%{_datadir}/applications/com.ranfdev.DistroShelf.desktop
%{_datadir}/metainfo/com.ranfdev.DistroShelf.metainfo.xml
%{_datadir}/glib-2.0/schemas/com.ranfdev.DistroShelf.gschema.xml
%{_datadir}/dbus-1/services/com.ranfdev.DistroShelf.service
%{_datadir}/icons/hicolor/scalable/apps/com.ranfdev.DistroShelf.svg
%{_datadir}/icons/hicolor/symbolic/apps/com.ranfdev.DistroShelf-symbolic.svg

%changelog
* Wed Sep 23 2026 halcyon-autobump <aahsnr041@proton.me>
- converted to an explicit Release and changelog for the Copr build

# Adapted from LionHeartP/hyprlandRPM's kitty.spec (their recipe tracks
# Fedora's kitty packaging), reworked for this repo: no go-vendor archive or
# GPG verify step — the Go modules for kitten are fetched from the module
# proxy during the build (Copr runs with network on; the nwg-look/cliphist
# pattern), and the appdata manifest is carried in-repo (upstream has none;
# LHP pulls it from kitty PR 2088). kitty's setup.py hard-requires the
# Symbols Nerd Font at build time on Linux (fc-list finds nothing in a
# buildroot), so the font tarball is a pinned URL source pre-seeded into
# fonts/ — a moving "latest" URL would not survive spectool reproducibility.
%define debug_package %{nil}

Name:           kitty
Version:        0.49.1
Release:        1%{?dist}
Summary:        Cross-platform, fast, feature full, GPU based terminal emulator

# GPL-3.0-only: kitty
# Zlib: glfw
# LGPL-2.1-or-later: kitty/iqsort.h
# MIT: docs/_static/custom.css, shell-integration/ssh/bootstrap-utils.sh
# MIT AND CC0-1.0: simde
# CC0-1.0: c-ringbuf
# BSD-2-Clause: base64simd
# MIT: NerdFontsSymbolsOnly
# Go dependencies:
# github.com/alecthomas/chroma: MIT
# github.com/ALTree/bigfloat: MIT
# github.com/bmatcuk/doublestar: MIT
# github.com/disintegration/imaging: MIT
# github.com/dlclark/regexp2: MIT
# github.com/google/go-cmp/cmp: BSD-3-Clause
# github.com/google/uuid: BSD-3-Clause
# github.com/klauspost/cpuid: MIT
# github.com/go-ole/go-ole: MIT
# github.com/lufia/plan9stats: BSD-3-Clause
# github.com/power-devops/perfstat: MIT
# github.com/seancfoley/bintree: Apache-2.0
# github.com/seancfoley/ipaddress-go/ipaddr: Apache-2.0
# github.com/shirou/gopsutil: BSD-3-Clause
# github.com/shoenig/go-m1cpu: MPL-2.0
# github.com/tklauser/go-sysconf: BSD-3-Clause
# github.com/tklauser/numcpus: Apache-2.0
# github.com/zeebo/xxh3: BSD-2-Clause
# golang.org/x/exp: BSD-3-Clause
# golang.org/x/image: BSD-3-Clause
# golang.org/x/sys: BSD-3-Clause
# howett.net/plist: BSD-2-Clause AND BSD-3-Clause
License:        GPL-3.0-only AND LGPL-2.1-or-later AND Zlib AND (MIT AND CC0-1.0) AND BSD-2-Clause AND CC0-1.0
URL:            https://github.com/kovidgoyal/kitty
Source0:        %{url}/releases/download/v%{version}/%{name}-%{version}.tar.xz
Source1:        https://github.com/ryanoasis/nerd-fonts/releases/download/v3.5.1/NerdFontsSymbolsOnly.tar.xz
Source2:        kitty.appdata.xml

# https://fedoraproject.org/wiki/Changes/EncourageI686LeafRemoval
ExcludeArch:    %{ix86}

BuildRequires:  golang
BuildRequires:  desktop-file-utils
BuildRequires:  gcc
BuildRequires:  python3-devel
BuildRequires:  lcms2-devel
BuildRequires:  libappstream-glib
BuildRequires:  ncurses
BuildRequires:  wayland-devel
BuildRequires:  simde-static
# kitty 0.49 generates its shaders at build time and hard-fails without
# slangc; shader-slang-devel is packaged in no Fedora 44 repo but resolves
# via the lionheartp/Hyprland bootstrap repo configured in the Copr chroot
BuildRequires:  shader-slang-devel
# man pages (sphinx; kitty bundles its doc tooling apart from the theme, which
# is swapped for the builtin classic in prep)
BuildRequires:  python3-sphinx
BuildRequires:  python3-sphinx-copybutton
BuildRequires:  python3-sphinx-design
BuildRequires:  python3-sphinxext-opengraph

BuildRequires:  pkgconfig(dbus-1)
BuildRequires:  pkgconfig(fontconfig)
BuildRequires:  pkgconfig(gl)
BuildRequires:  pkgconfig(harfbuzz)
BuildRequires:  pkgconfig(libcanberra)
BuildRequires:  pkgconfig(libpng)
BuildRequires:  pkgconfig(wayland-protocols)
BuildRequires:  pkgconfig(xcursor)
BuildRequires:  pkgconfig(xi)
BuildRequires:  pkgconfig(xinerama)
BuildRequires:  pkgconfig(xkbcommon-x11)
BuildRequires:  pkgconfig(xrandr)
BuildRequires:  pkgconfig(zlib)
BuildRequires:  pkgconfig(libcrypto)
BuildRequires:  pkgconfig(libxxhash)

Requires:       python3%{?_isa}
Requires:       hicolor-icon-theme

Recommends:     shader-slang

# Terminfo is split out (like Fedora/Arch) so it can be installed alone on
# remote machines for ssh from kitty; the version must match the terminal.
Requires:       %{name}-terminfo = %{version}-%{release}
Requires:       %{name}-shell-integration = %{version}-%{release}
Requires:       %{name}-kitten%{?_isa} = %{version}-%{release}

# For the "Hyperlinked grep" feature
Recommends:     ripgrep

# Very weak dependencies, these are required to enable all features of
# kitty's "kittens" functions install separately
Suggests:       ImageMagick%{?_isa}

Provides:       bundled(font(SymbolsNFM))

Provides:       bundled(Verstable) = 2.1.1
# modified version of https://github.com/dhess/c-ringbuf
Provides:       bundled(c-ringbuf)
# heavily modified
Provides:       bundled(glfw)
# https://github.com/aklomp/base64
Provides:       bundled(base64simd)

%description
- Offloads rendering to the GPU for lower system load and buttery smooth
  scrolling. Uses threaded rendering to minimize input latency.

- Supports all modern terminal features: graphics (images), unicode,
  true-color, OpenType ligatures, mouse protocol, focus tracking, bracketed
  paste and several new terminal protocol extensions.

- Supports tiling multiple terminal windows side by side in different
  layouts without needing to use an extra program like tmux.

- Can be controlled from scripts or the shell prompt, even over SSH.

- Has a framework for Kittens, small terminal programs that can be used to
  extend kitty's functionality. For example, they are used for Unicode
  input, Hints and Side-by-side diff.

- Supports startup sessions which allow you to specify the window/tab
  layout, working directories and programs to run on startup.

- Cross-platform: kitty works on Linux and macOS, but because it uses only
  OpenGL for rendering, it should be trivial to port to other Unix-like
  platforms.

- Allows you to open the scrollback buffer in a separate window using
  arbitrary programs of your choice. This is useful for browsing the
  history comfortably in a pager or editor.

- Has multiple copy/paste buffers, like vim.


# terminfo package
%package        terminfo
Summary:        The terminfo file for Kitty Terminal
License:        GPL-3.0-only
BuildArch:      noarch

Requires:       ncurses-base

%description    terminfo
Cross-platform, fast, feature full, GPU based terminal emulator.

The terminfo file for Kitty Terminal.

# shell-integration package
%package        shell-integration
Summary:        Shell integration scripts for %{name}
License:        GPL-3.0-only AND MIT
BuildArch:      noarch

Recommends:     %{name}-kitten

%description    shell-integration
%{summary}.

# kitten package
%package        kitten
Summary:        The kitten executable
License:        GPL-3.0-only AND MIT AND BSD-3-Clause AND BSD-2-Clause AND Apache-2.0 AND MPL-2.0 AND (BSD-2-Clause AND BSD-3-Clause)

%description    kitten
%{summary}.


%prep
%autosetup -p1
mkdir fonts
tar -xf %{SOURCE1} -C fonts

# the builtin classic theme instead of furo (kitty vendors no sphinx themes)
sed "s/html_theme = 'furo'/html_theme = 'classic'/" -i docs/conf.py

# Replace python shebangs to make them compatible with fedora
find -type f -name "*.py" -exec sed -e 's|/usr/bin/env python3|%{python3}|g'    \
                                    -e 's|/usr/bin/env python|%{python3}|g'     \
                                    -e 's|/usr/bin/env -S kitty|/usr/bin/kitty|g' \
                                    -i "{}" \;

%build
%set_build_flags
%{python3} setup.py linux-package   \
    --libdir-name=%{_lib}           \
    --update-check-interval=0       \
    --skip-building-kitten          \
    --verbose                       \
    --ignore-compiler-warnings

# kitten is a Go program at the module root's tools/cmd — modules come from
# the proxy at build time. LDFLAGS is dropped: rpm's linker flags break the
# go linker (same reason Fedora's go macros unset them).
unset LDFLAGS
mkdir -p _build/bin
export GOTOOLCHAIN=local
export GOFLAGS="-mod=mod"
go build -o _build/bin/kitten ./tools/cmd

# man pages (sphinx imports the just-built kitty.fast_data_types from the
# source tree via docs/conf.py, so this must follow linux-package). Their
# generator wants the built kitten at kitty/launcher/kitten.
ln -sr _build/bin/kitten kitty/launcher/
%make_build man

%install
# rpmlint fixes
find linux-package -type f ! -executable -name "*.py" -exec sed -i '1{\@^#!%{python3}@d}' "{}" \;
find linux-package/%{_lib}/%{name}/shell-integration -type f ! -executable -exec sed -r -i '1{\@^#!/bin/(fish|zsh|sh|bash)@d}' "{}" \;

# linux-package embeds the sphinx html docs (its bundle-gunk step runs
# `make docs` itself once a kitten binary exists, --skip-building-kitten
# notwithstanding); this repo ships the man pages only
rm -rf linux-package/share/doc/kitty/html

cp -r linux-package %{buildroot}%{_prefix}
install -m0755 -Dp _build/bin/kitten %{buildroot}%{_bindir}/kitten

install -m0644 -Dp %{SOURCE2} %{buildroot}%{_metainfodir}/%{name}.appdata.xml

install -m 0755 -vd %{buildroot}%{_mandir}/man{1,5}
install -m 0644 -p docs/_build/man/*.1 %{buildroot}%{_mandir}/man1
install -m 0644 -p docs/_build/man/*.5 %{buildroot}%{_mandir}/man5

%check
appstream-util validate-relax --nonet %{buildroot}%{_metainfodir}/*.xml
desktop-file-validate %{buildroot}/%{_datadir}/applications/*.desktop

%files
%license LICENSE
%{_bindir}/%{name}
%{_datadir}/applications/*.desktop
%{_datadir}/icons/hicolor/*/*/*.{png,svg}
%{_libdir}/%{name}/
%exclude %{_libdir}/%{name}/shell-integration
%{_mandir}/man{1,5}/*.{1,5}*
%{_metainfodir}/*.xml

%files kitten
%license LICENSE
%{_bindir}/kitten

%files terminfo
%license LICENSE
%{_datadir}/terminfo/x/xterm-%{name}

%files shell-integration
%license LICENSE
%{_libdir}/%{name}/shell-integration/

%changelog
* Sat Sep 26 2026 ahsan <aahsnr041@proton.me> - 0.49.1-1
- initial packaging: source build adapted from LionHeartP/hyprlandRPM's
  kitty.spec (online Go modules for kitten, in-repo appdata, pinned nerd
  font, sphinx man pages; no doc subpackage per repo convention)

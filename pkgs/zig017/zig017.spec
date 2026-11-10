%global debug_package %{nil}
%global _build_id_links none
%global __os_install_post %{nil}

Name:           zig017
Epoch:          1
Version:        0.17.0
Release:        1%{?dist}
Summary:        General-purpose programming language and toolchain

License:        MIT
URL:            https://ziglang.org
Source0:        https://ziglang.org/download/%{version}/zig-x86_64-linux-%{version}.tar.xz

%global upstream_sha256 1cbe9df9f27e6b78d14ccbca43b6703a404ef79ef1c463de901d7f088d4e2026

ExclusiveArch:  x86_64

BuildRequires:  coreutils

%description
Zig is a general-purpose programming language and toolchain for maintaining
robust, optimal, and reusable software.

This package repackages the official upstream prebuilt compiler so Ghostty can
be built with Zig %{version}, independently of Fedora's default Zig release.

%prep
%setup -q -c -T -n zig-%{version}

actual_sum="$(sha256sum %{SOURCE0} | cut -d' ' -f1)"
if [ "%{upstream_sha256}" != "$actual_sum" ]; then
    echo "ERROR: checksum verification failed for %{SOURCE0}" >&2
    echo "Expected: %{upstream_sha256}" >&2
    echo "Actual:   $actual_sum" >&2
    exit 1
fi

tar -xf %{SOURCE0} --strip-components=1

%build
# Upstream prebuilt compiler repackaging; nothing to build.

%install
install -Dpm 0755 zig %{buildroot}%{_libexecdir}/zig017/zig
install -d %{buildroot}%{_libexecdir}/zig017/lib
cp -a lib/. %{buildroot}%{_libexecdir}/zig017/lib/
install -d %{buildroot}%{_bindir}
ln -s ../libexec/zig017/zig %{buildroot}%{_bindir}/zig017

%check
test "$(%{buildroot}%{_bindir}/zig017 version)" = "%{version}"

%files
%license LICENSE
%doc README.md
%{_bindir}/zig017
%{_libexecdir}/zig017/

%changelog
* Tue Nov 10 2026 halcyon-linux <aahsnr041@proton.me> - 0.17.0-1
- Repackage the upstream Zig compiler for Ghostty

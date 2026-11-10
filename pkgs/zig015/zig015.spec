%global public_key RWSGOq2NVecA2UPNdBUZykf1CCb147pkmdtYxgb3Ti+JO/wCYvhbAb/U
%global debug_package %{nil}
%global _build_id_links none
%global __os_install_post %{nil}

Name:           zig015
Version:        0.15.2
Release:        1%{?dist}
Summary:        Zig 0.15 compiler and toolchain
License:        MIT
URL:            https://ziglang.org/
Source0:        https://ziglang.org/download/%{version}/zig-x86_64-linux-%{version}.tar.xz
Source1:        https://ziglang.org/download/%{version}/zig-x86_64-linux-%{version}.tar.xz.minisig
ExclusiveArch:  x86_64
BuildRequires:  minisign
BuildRequires:  tar
BuildRequires:  xz

%description
The Zig 0.15 compiler and standard library, packaged under a versioned name
for reproducible builds that need the Zig 0.15 series.

%prep
/usr/bin/minisign -V -m %{SOURCE0} -x %{SOURCE1} -P %{public_key}
%setup -q -c -T -n zig-%{version}
tar -xf %{SOURCE0} --strip-components=1

%build
# The official upstream archive contains the prebuilt compiler.

%install
install -Dpm 0755 zig %{buildroot}%{_libexecdir}/zig015/zig
install -d %{buildroot}%{_libexecdir}/zig015/lib
cp -a lib/. %{buildroot}%{_libexecdir}/zig015/lib/
install -d %{buildroot}%{_bindir}
ln -s ../libexec/zig015/zig %{buildroot}%{_bindir}/zig015

%check
test "$(%{buildroot}%{_bindir}/zig015 version)" = "%{version}"

%files
%license LICENSE
%doc README.md
%{_bindir}/zig015
%{_libexecdir}/zig015/

%changelog
* Tue Nov 10 2026 halcyon-linux <aahsnr041@proton.me> - 0.15.2-1
- Package the signed upstream Zig 0.15.2 compiler archive

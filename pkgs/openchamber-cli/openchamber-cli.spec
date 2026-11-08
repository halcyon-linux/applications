# Vendor source build: openchamber-web tarball + bundled Node.js runtime.
# The openchamber-web tarball (Source0) is the official upstream release asset.
# Node.js (Source1) is bundled from nodejs.org — the version is pinned in
# %%global node_version and must be updated when upstream changes its
# declared engine requirement (currently 24.22.1 per the v2.6.1 release).
# Sources are fetched by mock at SRPM-build time; nothing is downloaded in %prep.
%define debug_package %{nil}
%global __strip /bin/true
%global __provides_exclude_from ^/usr/lib/openchamber-web/node_modules/.*$
%global __requires_exclude_from ^/usr/lib/openchamber-web/node_modules/.*$
%global __requires_exclude ^/usr/bin/(node|pwsh|python3)$
%global node_version 24.22.1

Name:           openchamber-cli
Version:        2.7.0
Release:        1%{?dist}
Summary:        OpenChamber Web Server and CLI
License:        MIT
URL:            https://openchamber.dev/
Source0:        https://github.com/openchamber/openchamber/releases/download/v%{version}/openchamber-web-%{version}.tgz
Source1:        https://nodejs.org/dist/v%{node_version}/node-v%{node_version}-linux-x64.tar.xz
Source2:        LICENSE
ExclusiveArch:  x86_64

BuildRequires:  tar
BuildRequires:  xz

%description
OpenChamber Web Server and CLI for running OpenChamber on a workstation or
server. This package provides the openchamber-cli command, including API-only
and LAN server modes.

%prep
# Verify the openchamber-web tarball sha256 (pinned by the version sweep).
echo "6edb084bbeb06974a4815b3ac73c93e8fa81887bc8ba6251df1a52fc9cf933ab  %{SOURCE0}" | sha256sum --check
# Verify the Node.js tarball sha256 (pinned by the version sweep when node_version changes).
echo "6c172a9ab6718f7b801fb5a7bd486af2ee5e32758086a04b84fcce2aa77095e6  %{SOURCE1}" | sha256sum --check
mkdir -p package
tar -xzf %{SOURCE0} --strip-components=1 -C package
tar -xJf %{SOURCE1}

%build
export PATH="$PWD/node-v%{node_version}-linux-x64/bin:$PATH"
cd package
npm install --omit=dev --ignore-scripts --no-audit --no-fund

%install
export QA_RPATHS=0x12
mkdir -p %{buildroot}%{_prefix}/lib/openchamber-web
mkdir -p %{buildroot}%{_bindir}
cp -a package/. %{buildroot}%{_prefix}/lib/openchamber-web/
mkdir -p %{buildroot}%{_prefix}/lib/openchamber-web/runtime
cp -a node-v%{node_version}-linux-x64 \
    %{buildroot}%{_prefix}/lib/openchamber-web/runtime/
install -Dpm 0644 %{SOURCE2} \
    %{buildroot}%{_datadir}/licenses/%{name}/LICENSE

cat > %{buildroot}%{_bindir}/openchamber-cli <<'EOF'
#!/bin/sh
ROOT=/usr/lib/openchamber-web
export PATH="$ROOT/runtime/node-v%{node_version}-linux-x64/bin:$PATH"
exec node "$ROOT/bin/cli.js" "$@"
EOF
chmod 0755 %{buildroot}%{_bindir}/openchamber-cli

find %{buildroot} -mindepth 1 \( -type f -o -type l \) \
    ! -path '%{buildroot}%{_datadir}/licenses/%{name}/LICENSE' \
    -printf '/%%P\n' | sort -u > %{name}.files

%check
NODE=%{buildroot}%{_prefix}/lib/openchamber-web/runtime/node-v%{node_version}-linux-x64/bin/node
"$NODE" %{buildroot}%{_prefix}/lib/openchamber-web/bin/cli.js --version | grep -Fx '%{version}'
"$NODE" %{buildroot}%{_prefix}/lib/openchamber-web/bin/cli.js --help >/dev/null

%files -f %{name}.files
%license %{_datadir}/licenses/%{name}/LICENSE

%changelog
* Wed Nov 04 2026 halcyon-linux <aahsnr041@proton.me> - 2.6.1-1
- Initial packaging of openchamber-cli (from ok8219/OpenChamber Copr)
- Bundles Node.js 24.22.1
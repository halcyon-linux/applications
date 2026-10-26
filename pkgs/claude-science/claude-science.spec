# Repackaged from Anthropic's single-file linux-x64 release. The binary is a
# self-contained Bun executable with embedded resources; it must not be
# stripped or rewritten.
%global debug_package %{nil}
%global _build_id_links none
%global __os_install_post %{nil}

# NOTE: %%global debug_package %%{nil} is what makes the default ELF-rewriting
# brp hooks run, not what skips them — Fedora's %%__os_install_post gates
# brp-strip / brp-strip-comment-note on %%__debug_package being *undefined*.
# With them in place every ELF file gets rewritten, so the packaged payload
# stops being byte-identical to the upstream blob. Empty all four strip hooks
# as well: brp-strip-lto and brp-strip-static-archive are not gated at all.
%global __brp_strip %{nil}
%global __brp_strip_comment_note %{nil}
%global __brp_strip_lto %{nil}
%global __brp_strip_static_archive %{nil}

# brp-mangle-shebangs rewrites payload bytes; unset it for byte-identity.
%global __brp_mangle_shebangs %{nil}

# add-determinism's brp hook would regenerate build-id links and otherwise
# normalize the payload. The blob must ship byte-identical.
%undefine __brp_add_determinism

# Upstream publishes no sha256 for the release; the download endpoint carries
# an MD5 in its x-goog-hash header. The sweep pins that here; 'none' skips
# the check.
%global md5 03d9b45237913ac7ec476d027d5004f7

Name:           claude-science
Version:        0.1.70
Release:        1%{?dist}
Summary:        Anthropic's local research agent (beta)
License:        LicenseRef-Proprietary
URL:            https://claude.com/product/claude-science
#!RemoteAsset
Source0:        https://downloads.claude.ai/claude-science/%{version}/linux-x64
# The legal page is a live document (same one the upstream Arch package
# ships); it is committed here so the package carries a license text.
Source1:        LICENSE

ExclusiveArch:  x86_64

BuildRequires:  coreutils

Requires:       bash
Requires:       socat
Requires:       bubblewrap

Recommends:     xdg-utils
Recommends:     ca-certificates

%description
Claude Science runs Claude on your data locally and serves its UI in the
browser. This package installs Anthropic's single-file linux-x64 release as
/usr/bin/claude-science.

%prep
if [ '%{md5}' != 'none' ]; then
    actual="$(md5sum %{SOURCE0} | cut -d' ' -f1)"
    if [ "$actual" != '%{md5}' ]; then
        echo "claude-science: md5 mismatch (expected %{md5}, got $actual)" >&2
        exit 1
    fi
    echo "claude-science: md5 verified"
fi

cp %{SOURCE1} LICENSE

%build
# Nothing to compile: the upstream single-file executable is installed as-is.

%install
install -Dm755 %{SOURCE0} %{buildroot}%{_bindir}/claude-science

%files
%license LICENSE
%{_bindir}/claude-science

%changelog
* Mon Oct 26 2026 halcyon-autoupdate <aahsnr041@proton.me> - 0.1.70-1
- Initial package: Anthropic's single-file linux-x64 release

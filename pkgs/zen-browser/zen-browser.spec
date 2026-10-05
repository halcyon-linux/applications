# Vendor rewrap of Zen Browser's official Linux tarball (zen.linux-x86_64.tar.xz
# from the GitHub release) — the archive zen's own install instructions deploy.
# Firefox-based and prebuilt: the full brp nil set applies (no debug package,
# no build-id links, no strip pass, no shebang mangling), per obsidian.spec.
# The tarball ships no desktop file or license, so the desktop entry is
# authored in-repo and MPL-2.0 is pinned from the tag; distribution/
# policies.json disables the bundled self-updater (updates come from Copr).
%global             debug_package %{nil}
%global _build_id_links none
%global             __os_install_post %{nil}

Name:               zen-browser
Version:            1.23b
Release:            1%{?dist}
Summary:            Zen Browser — a Firefox-based browser focused on privacy and customization
License:            MPL-2.0
URL:                https://zen-browser.app
Source0:            https://github.com/zen-browser/desktop/releases/download/%{version}/zen.linux-x86_64.tar.xz
Source1:            https://raw.githubusercontent.com/zen-browser/desktop/%{version}/LICENSE
Source2:            zen-browser.desktop
Source3:            zen-browser.policies.json

ExclusiveArch:      x86_64

%description
Zen Browser is a Firefox-based web browser focused on privacy,
customization and performance (vertical tabs, workspaces, split views,
compact mode). This packages the official Linux tarball: the browser tree
installs to libdir, /usr/bin/zen is a symlink, and the bundled
self-updater is disabled via enterprise policy.

%prep
%setup -q -c
cp %{SOURCE1} LICENSE

%install
%__rm -rf %{buildroot}
install -dm755 %{buildroot}%{_libdir}/zen-browser
%__cp -a zen/. %{buildroot}%{_libdir}/zen-browser/
mkdir -p %{buildroot}%{_bindir}
ln -s %{_libdir}/zen-browser/zen %{buildroot}%{_bindir}/zen
%__install -Dm644 %{SOURCE2} %{buildroot}%{_datadir}/applications/zen-browser.desktop
for i in 16 32 48 64 128; do
    f="zen/browser/chrome/icons/default/default${i}.png"
    if [ -f "$f" ]; then
        %__install -Dm644 "$f" \
            %{buildroot}%{_datadir}/icons/hicolor/${i}x${i}/apps/zen-browser.png
    fi
done
%__install -Dm644 %{SOURCE3} %{buildroot}%{_libdir}/zen-browser/distribution/policies.json
%__install -Dm644 LICENSE %{buildroot}%{_licensedir}/zen-browser/LICENSE

%files
%{_bindir}/zen
%{_libdir}/zen-browser/
%{_datadir}/applications/zen-browser.desktop
%{_datadir}/icons/hicolor/*/apps/zen-browser.png
%license LICENSE

%changelog
* Tue Sep 29 2026 halcyon-autoupdate <aahsnr041@proton.me> - 1.22.3b-1
- initial package (vendor rewrap of the official Linux tarball,
  shape per zed.spec/obsidian.spec)

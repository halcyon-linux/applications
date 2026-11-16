# Configure Fedora COPR API Authentication for GitHub Actions

## Description

Uploads the local Fedora COPR API configuration file (`~/.config/copr`), containing COPR authentication credentials, to a GitHub repository as an encrypted GitHub Actions secret named `COPR_CONFIG`. This allows GitHub Actions workflows to authenticate with Fedora COPR and trigger remote RPM package builds without building the packages on GitHub runners.

## Command

```bash
gh secret set COPR_CONFIG --repo halcyon-linux/applications < ~/.config/copr
```

Replace `OWNER/REPO` with the GitHub repository's owner and name.

**Security:** Keep `~/.config/copr` private; never commit it to the repository. GitHub Actions must explicitly reference `secrets.COPR_CONFIG` in the workflow to use the uploaded configuration.

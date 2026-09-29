#!/usr/bin/env bash
# Launcher ported from the Arch Linux obsidian package (obsidian.sh): keeps
# the per-user flag file mechanism. The one adaptation vs Arch: Fedora has no
# system electron package, so this execs the Electron runtime bundled in the
# official tarball instead of the system electron43.
OBSIDIAN_USER_FLAGS_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/obsidian/user-flags.conf"

# Allow users to override command-line options
if [[ -f "${OBSIDIAN_USER_FLAGS_FILE}" ]]; then
   OBSIDIAN_USER_FLAGS=$(grep -v '^#' "$OBSIDIAN_USER_FLAGS_FILE")
fi

# Launch
exec /usr/lib/obsidian/obsidian $OBSIDIAN_USER_FLAGS "$@"

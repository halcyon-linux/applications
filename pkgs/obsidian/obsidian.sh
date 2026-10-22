#!/usr/bin/env bash
# Launcher ported from the Arch Linux obsidian package (obsidian.sh): keeps
# the per-user flag file mechanism. The one adaptation vs Arch: Fedora has no
# system electron package, so this execs the Electron runtime bundled in the
# official tarball instead of the system electron43.
#
# The bundled runtime lives in the package's private libdir. Arch installs it
# to /usr/lib/obsidian; on Fedora the 64-bit libdir is /usr/lib64, so the
# path is not fixed — the spec substitutes it into the placeholder below at
# build time.
OBSIDIAN_USER_FLAGS_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/obsidian/user-flags.conf"

# Allow users to override command-line options
if [[ -f "${OBSIDIAN_USER_FLAGS_FILE}" ]]; then
   OBSIDIAN_USER_FLAGS=$(grep -v '^#' "$OBSIDIAN_USER_FLAGS_FILE")
fi

# Launch
exec @OBSIDIAN_LIBDIR@/obsidian $OBSIDIAN_USER_FLAGS "$@"

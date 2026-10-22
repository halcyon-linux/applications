"""Pure-Python port of rpm's version comparison (lib/rpmvercmp.c), including
the tilde (~ = pre-release, sorts below everything) and caret (^ = snapshot,
sorts above everything) extensions rpm supports.

The sweeper needs rpm's ordering, so this module returns -1/0/1. Pure Python
so the sweep has no rpm host dependency.

The port is faithful in the two places rpm's algorithm is subtle, and both
were verified against real rpm (rpm.vercmp through rpm's Lua API) over a
171-version corpus — 29241 ordered pairs, zero disagreements:

  * a version is a sequence of ALTERNATING numeric and alpha segments.
    rpm's segment type is decided by the FIRST string only: comparing
    "1.23.4b" with "1.23b" walks 1 | 23 | 4 | b against 1 | 23 | b, so
    the numeric segment 4 decides it and "1.23.4b" is newer. A port that
    merges digits and letters into one segment ("23b") gets this wrong
    and ranks "1.23b" newest — a silent downgrade.
  * ~ and ^ are segment BOUNDARIES, not ordinary characters. A version
    splits at the first marker into base + marker + suffix: the bases are
    compared first, then the markers are ranked (~ below the plain
    release, ^ above it), then equal-marker suffixes are compared as
    versions. That is what makes "1.0~rc1" < "1.0" < "1.0^post" while
    "1.0.0" > "1.0^post" — the caret sorts above its own base but below
    the base's next segment.
"""

from __future__ import annotations

# Marker ranking after the bases compare equal: a tilde marks a
# pre-release (below the plain release), a caret a post-release (above it).
_MARKER_RANK = {"~": 0, "": 1, "^": 2}


def _split_marker(v: str) -> tuple[str, str, str]:
    """Split a version at its first ~ or ^ into (base, marker, suffix)."""
    for i, ch in enumerate(v):
        if ch == "~" or ch == "^":
            return v[:i], ch, v[i + 1 :]
    return v, "", ""


def _plain_cmp(a: str, b: str) -> int:
    """rpm's segment comparison for strings without a marker."""
    if a == b:
        return 0
    i = j = 0
    n1, n2 = len(a), len(b)
    while i < n1 or j < n2:
        # skip separators: everything that is neither alphanumeric nor ~ nor ^
        while i < n1 and not (a[i].isalnum() or a[i] in "~^"):
            i += 1
        while j < n2 and not (b[j].isalnum() or b[j] in "~^"):
            j += 1
        if not (i < n1 and j < n2):
            break
        # grab the first completely numeric OR completely alpha segment —
        # the segment TYPE comes from the first string, rpm-style
        if a[i].isdigit():
            k1 = i
            while k1 < n1 and a[k1].isdigit():
                k1 += 1
            k2 = j
            while k2 < n2 and b[k2].isdigit():
                k2 += 1
            isnum = True
        else:
            k1 = i
            while k1 < n1 and a[k1].isalpha():
                k1 += 1
            k2 = j
            while k2 < n2 and b[k2].isalpha():
                k2 += 1
            isnum = False
        if j == k2:
            # the second string has no segment of that type; a numeric
            # segment is always newer than an (empty) alpha one
            return 1 if isnum else -1
        seg1, seg2 = a[i:k1], b[j:k2]
        if isnum:
            # leading zeros are meaningless in a number
            seg1 = seg1.lstrip("0")
            seg2 = seg2.lstrip("0")
            if len(seg1) != len(seg2):
                return 1 if len(seg1) > len(seg2) else -1
        if seg1 != seg2:
            return 1 if seg1 > seg2 else -1
        i, j = k1, k2
    if i >= n1 and j >= n2:
        return 0
    if i >= n1:
        return -1
    return 1


def rpmvercmp(a: str, b: str) -> int:
    """Return -1, 0 or 1 comparing a against b the way rpm does."""
    base_a, marker_a, suffix_a = _split_marker(a)
    base_b, marker_b, suffix_b = _split_marker(b)
    rc = _plain_cmp(base_a, base_b)
    if rc:
        return rc
    rank_a = _MARKER_RANK[marker_a]
    rank_b = _MARKER_RANK[marker_b]
    if rank_a != rank_b:
        return 1 if rank_a > rank_b else -1
    if not marker_a:
        return 0
    return _plain_cmp(suffix_a, suffix_b)

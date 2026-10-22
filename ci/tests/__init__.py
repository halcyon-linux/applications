"""Test suite for the CI helpers of the applications repo.

Plain `unittest` (stdlib only — the validate job runs on a bare runner):

    python3 -m unittest discover -s ci/tests -t .

The modules under test live in `ci/` and `ci/sweep/`; the path setup below
makes them importable regardless of the working directory.
"""

from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_CI = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_CI)

for path in (_CI, os.path.join(_CI, "sweep")):
    if path not in sys.path:
        sys.path.insert(0, path)

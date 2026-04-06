"""engine_bridge.py — Make app/engine importable from app/android/.

The desktop app runs with `app/` as the top-level package (sys.path
includes the repo root).  When Buildozer packages the Android APK it
copies *only* the `app/android/` tree into the Python path.  This module
adds the parent (`app/`) directory to sys.path so that:

    from app.engine.profile import ProfileManager, AppProfile
    from app.engine.models  import AppProfile
    ...

all resolve correctly whether running on Android (where `app/` lives next
to `app/android/`) or on the desktop during development.

Usage — import this once at the very top of main.py:

    import engine_bridge  # noqa: F401 — sets up sys.path
"""

from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))          # …/app/android/
_APP_ROOT = os.path.dirname(_HERE)                           # …/app/
_REPO_ROOT = os.path.dirname(_APP_ROOT)                      # …/Ham-Radio-Hat-Software/

# Make both the repo root (so `from app.engine…` works) and
# `app/` itself (so `from engine…` works without the package prefix)
# available.
for _p in (_REPO_ROOT, _APP_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

del _HERE, _APP_ROOT, _REPO_ROOT, _p

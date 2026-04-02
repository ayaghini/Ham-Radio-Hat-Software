#!/usr/bin/env python3
"""Platform-aware application data directory resolution.

Returns a user-writable directory for app data (profiles, cache, logs)
appropriate for each target platform:

  Windows         : %APPDATA%\\{app_name}
                    e.g. C:\\Users\\<user>\\AppData\\Roaming\\HamHatCC
  macOS           : ~/Library/Application Support/{app_name}
                    e.g. /Users/<user>/Library/Application Support/HamHatCC
  Linux / RPi OS  : $XDG_DATA_HOME/{app_name}  (if XDG_DATA_HOME is set)
                    ~/.local/share/{app_name_lower}  (standard XDG default)
                    e.g. /home/<user>/.local/share/hamhatcc

Falls back to `fallback_dir` if the standard path cannot be resolved.

Usage
-----
    from app.engine.platform_paths import get_user_data_dir
    data_dir = get_user_data_dir("HamHatCC", fallback_dir=app_dir / "profiles")
    data_dir.mkdir(parents=True, exist_ok=True)

Migration notes (Phase 2 / CP-103)
-----------------------------------
AppState currently stores all data relative to `app_dir` (the app install
directory).  This is fine for Windows desktop installs and development runs
but is a blocker for:
  - macOS .app bundles (the bundle is read-only after signing/notarization)
  - Linux system installs (/usr/... paths are not user-writable)

To migrate, update AppState.__init__ to call:
    data_dir = get_user_data_dir("HamHatCC", fallback_dir=app_dir)
    self.profile_path = data_dir / "profiles" / "last_profile.json"
    self.audio_dir    = data_dir / "audio_out"

The fallback_dir parameter ensures existing Windows behaviour is preserved
when the standard path lookup fails.
"""

from __future__ import annotations

import os
import platform
from pathlib import Path
from typing import Optional


def get_user_data_dir(app_name: str, fallback_dir: Optional[Path] = None) -> Path:
    """Return a platform-appropriate user-writable data directory.

    Parameters
    ----------
    app_name:
        Human-readable application name used as the leaf directory name.
        On Linux/RPi the name is lowercased for XDG convention compliance.
    fallback_dir:
        Returned unchanged if the standard path cannot be resolved.
        If None and no standard path is available, returns Path.cwd() / app_name.
    """
    system = platform.system().lower()

    if system == "windows":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            return Path(appdata) / app_name

    elif system == "darwin":
        return Path.home() / "Library" / "Application Support" / app_name

    else:
        # Linux, Raspberry Pi OS, and other POSIX systems
        xdg = os.environ.get("XDG_DATA_HOME", "")
        if xdg:
            return Path(xdg) / app_name.lower()
        return Path.home() / ".local" / "share" / app_name.lower()

    # Fallback: use caller-provided directory or cwd
    return fallback_dir if fallback_dir is not None else Path.cwd() / app_name


def get_user_log_dir(app_name: str, fallback_dir: Optional[Path] = None) -> Path:
    """Return a platform-appropriate directory for log files.

    Parameters
    ----------
    app_name:
        Application name (same as passed to get_user_data_dir).
    fallback_dir:
        Used if the standard path cannot be resolved.
    """
    system = platform.system().lower()

    if system == "windows":
        # Logs alongside app data on Windows
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            return Path(appdata) / app_name / "logs"

    elif system == "darwin":
        return Path.home() / "Library" / "Logs" / app_name

    else:
        # Linux/RPi: ~/.local/share/<app>/logs or ~/.cache/<app>/logs
        xdg_cache = os.environ.get("XDG_CACHE_HOME", "")
        if xdg_cache:
            return Path(xdg_cache) / app_name.lower() / "logs"
        return Path.home() / ".cache" / app_name.lower() / "logs"

    return fallback_dir if fallback_dir is not None else Path.cwd() / app_name / "logs"

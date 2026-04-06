"""platform/paths.py — Android-aware data and log directory resolution.

On Android (detected via `kivy.utils.platform == 'android'`):
  data dir → App.user_data_dir   (/data/data/<pkg>/files/HamHatCC/)
  log  dir → App.user_data_dir/logs/

On desktop (development / CI):
  delegates to the existing app.engine.platform_paths module so this
  file produces the same result as the desktop app.

Import this module AFTER importing engine_bridge so that
`app.engine.platform_paths` is on sys.path.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from kivy.utils import platform as _kivy_platform
    from kivy.app import App as _KivyApp
    _ON_ANDROID: bool = (_kivy_platform == "android")
except ImportError:
    _ON_ANDROID = False


def get_user_data_dir(app_name: str = "HamHatCC") -> Path:
    """Return the writable user-data directory for *app_name*."""
    if _ON_ANDROID:
        try:
            base = Path(_KivyApp.get_running_app().user_data_dir)
        except Exception:
            # Fallback during early init before app object is created
            base = Path(os.environ.get("HOME", "/data/data/com.hamhat.hamhatcc/files"))
        data_dir = base / app_name
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir
    else:
        # Development/desktop — delegate to desktop engine
        try:
            from app.engine.platform_paths import get_user_data_dir as _desktop_fn
            return Path(_desktop_fn(app_name))
        except ImportError:
            fallback = Path.home() / ".local" / "share" / app_name.lower()
            fallback.mkdir(parents=True, exist_ok=True)
            return fallback


def get_user_log_dir(app_name: str = "HamHatCC") -> Path:
    """Return the writable log directory for *app_name*."""
    if _ON_ANDROID:
        log_dir = get_user_data_dir(app_name) / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir
    else:
        try:
            from app.engine.platform_paths import get_user_log_dir as _desktop_fn
            return Path(_desktop_fn(app_name))
        except ImportError:
            return get_user_data_dir(app_name) / "logs"


def get_profile_file(app_name: str = "HamHatCC") -> Path:
    """Return the path to last_profile.json."""
    return get_user_data_dir(app_name) / "profiles" / "last_profile.json"

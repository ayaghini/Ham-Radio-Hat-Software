"""hal/foreground_service.py — Android foreground service for background BLE.

Android kills background apps unless they hold a foreground service with a
persistent notification.  For HAM HAT, we need the PAKT BLE connection to
survive when the user switches to another app (e.g., a maps app).

On desktop this module is a no-op.

Android foreground service approach
────────────────────────────────────
Buildozer / python-for-android provides a Service template.  We start it via
AndroidService from python-for-android's plyer/jnius bridge.

Required additions to buildozer.spec
──────────────────────────────────────
    android.services = BleService:service/ble_service.py:foreground

And add to permissions:
    FOREGROUND_SERVICE

Notification channel
────────────────────
Android 8+ (API 26+) requires a notification channel to be registered before
displaying a persistent notification.  We create one named "hamhat_ble" at
IMPORTANCE_LOW (silent, no vibration — appropriate for a status notification).

Usage
─────
    from hal.foreground_service import start_ble_foreground_service, stop_ble_foreground_service

    # Call from on_start(), after BLE permissions granted:
    start_ble_foreground_service(title="HAM HAT", body="BLE active")

    # Call from on_stop():
    stop_ble_foreground_service()
"""

from __future__ import annotations

import logging

_log = logging.getLogger(__name__)

try:
    from kivy.utils import platform as _kivy_platform
    _ON_ANDROID: bool = (_kivy_platform == "android")
except ImportError:
    _ON_ANDROID = False

# Notification channel ID / service tag
_CHANNEL_ID   = "hamhat_ble"
_CHANNEL_NAME = "HAM HAT BLE Service"
_NOTIF_ID     = 1001


def start_ble_foreground_service(
    title: str = "HAM HAT Control Center",
    body:  str = "BLE connection active",
) -> None:
    """Start the Android foreground service so BLE stays alive in background.

    On desktop / non-Android this is a no-op.
    """
    if not _ON_ANDROID:
        _log.debug("foreground_service: not on Android — skipped")
        return
    try:
        _ensure_notification_channel()
        _start_service_notification(title, body)
        _log.info("Foreground BLE service started")
    except Exception as exc:
        _log.warning("Could not start foreground service: %s", exc)


def stop_ble_foreground_service() -> None:
    """Cancel the foreground notification (Android only)."""
    if not _ON_ANDROID:
        return
    try:
        from jnius import autoclass  # type: ignore[import]
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        NotifMgr       = autoclass("android.app.NotificationManager")
        Context        = autoclass("android.content.Context")

        ctx  = PythonActivity.mActivity
        nm   = ctx.getSystemService(Context.NOTIFICATION_SERVICE)
        nm.cancel(_NOTIF_ID)
        _log.info("Foreground BLE notification cancelled")
    except Exception as exc:
        _log.debug("stop_ble_foreground_service error (ignored): %s", exc)


def update_foreground_notification(
    title: str = "HAM HAT Control Center",
    body:  str = "BLE active",
) -> None:
    """Update the text of the persistent notification while running."""
    if not _ON_ANDROID:
        return
    try:
        _start_service_notification(title, body)
    except Exception as exc:
        _log.debug("update_foreground_notification error: %s", exc)


# ── internal ─────────────────────────────────────────────────────────────────

def _ensure_notification_channel() -> None:
    """Create the BLE notification channel (Android 8+, API 26+)."""
    try:
        from jnius import autoclass  # type: ignore[import]
        NotifChannel   = autoclass("android.app.NotificationChannel")
        NotifMgr       = autoclass("android.app.NotificationManager")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Context        = autoclass("android.content.Context")

        ctx  = PythonActivity.mActivity
        nm   = ctx.getSystemService(Context.NOTIFICATION_SERVICE)

        # Only create if API 26+
        if hasattr(nm, "createNotificationChannel"):
            channel = NotifChannel(
                _CHANNEL_ID,
                _CHANNEL_NAME,
                NotifMgr.IMPORTANCE_LOW,   # silent — no sound/vibration
            )
            channel.setDescription("Keeps BLE connection alive in background")
            nm.createNotificationChannel(channel)
    except Exception as exc:
        _log.debug("_ensure_notification_channel: %s", exc)


def _start_service_notification(title: str, body: str) -> None:
    """Build and display (or update) the foreground notification."""
    try:
        from jnius import autoclass  # type: ignore[import]
        NotifBuilder   = autoclass("android.app.Notification$Builder")
        NotifCompat    = autoclass("androidx.core.app.NotificationCompat")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Context        = autoclass("android.content.Context")
        NotifMgr       = autoclass("android.app.NotificationManager")

        ctx  = PythonActivity.mActivity

        # Build the notification
        builder = NotifCompat.Builder(ctx, _CHANNEL_ID)
        builder.setSmallIcon(ctx.getApplicationInfo().icon)
        builder.setContentTitle(title)
        builder.setContentText(body)
        builder.setOngoing(True)          # persistent — user cannot swipe away
        builder.setPriority(NotifCompat.PRIORITY_LOW)

        notif = builder.build()

        # Promote to foreground service
        try:
            ctx.startForeground(_NOTIF_ID, notif)
        except Exception:
            # Fallback: just update the notification manager (not a true foreground svc)
            nm = ctx.getSystemService(Context.NOTIFICATION_SERVICE)
            nm.notify(_NOTIF_ID, notif)
    except Exception as exc:
        _log.debug("_start_service_notification error: %s", exc)


# ── Plyer-based alternative (simpler, less control) ───────────────────────────

def try_plyer_notification(title: str, message: str) -> None:
    """Fallback: use plyer.notification for a one-shot notification."""
    try:
        from plyer import notification  # type: ignore[import]
        notification.notify(
            title=title,
            message=message,
            app_name="HAM HAT CC",
            timeout=0,   # persist
        )
    except Exception as exc:
        _log.debug("plyer notification fallback failed: %s", exc)

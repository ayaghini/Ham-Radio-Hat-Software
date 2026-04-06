"""platform/audio_manager.py — Audio device enumeration and playback for Android.

On Android:
  • Device enumeration uses Android AudioManager API (via pyjnius) to list
    audio output/input routes: speaker, earpiece, wired headset, Bluetooth.
  • Audio recording uses Android's AudioRecord (via pyjnius) or sounddevice
    if available.

On desktop (development):
  • Delegates to app.engine.audio_tools for full sounddevice integration.

For APRS:
  • TX: generate PCM samples (pure Python DSP in aprs_modem.py) → route to
    default audio output.
  • RX: capture mic audio → decode via aprs_modem.
"""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple

try:
    from kivy.utils import platform as _kivy_platform
    _ON_ANDROID: bool = (_kivy_platform == "android")
except ImportError:
    _ON_ANDROID = False

_log = logging.getLogger(__name__)

# ── Device types reported on Android ────────────────────────────────────────
DEVICE_SPEAKER   = "speaker"
DEVICE_EARPIECE  = "earpiece"
DEVICE_HEADSET   = "wired_headset"
DEVICE_BLUETOOTH = "bluetooth"
DEVICE_USB_AUDIO = "usb_audio"


def list_output_devices() -> List[Tuple[int, str]]:
    """Return (index, name) pairs for available audio output routes."""
    if _ON_ANDROID:
        return _android_list_outputs()
    else:
        return _desktop_list_outputs()


def list_input_devices() -> List[Tuple[int, str]]:
    """Return (index, name) pairs for available audio input routes."""
    if _ON_ANDROID:
        return _android_list_inputs()
    else:
        return _desktop_list_inputs()


def request_audio_permission() -> None:
    """Request Android RECORD_AUDIO permission at runtime."""
    if not _ON_ANDROID:
        return
    try:
        from android.permissions import request_permissions, Permission  # type: ignore[import]
        request_permissions([Permission.RECORD_AUDIO])
    except Exception as exc:
        _log.warning("Audio permission request failed: %s", exc)


# ── Android implementations ──────────────────────────────────────────────────

def _android_list_outputs() -> List[Tuple[int, str]]:
    """Use Android AudioManager to list available output devices."""
    try:
        from jnius import autoclass  # type: ignore[import]
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Context        = autoclass("android.content.Context")
        AudioManager   = autoclass("android.media.AudioManager")

        ctx = PythonActivity.mActivity
        am  = ctx.getSystemService(Context.AUDIO_SERVICE)

        # Build a simple list based on what routes are active
        devices = [(0, "Phone Speaker")]
        if am.isBluetoothA2dpOn():
            devices.append((1, "Bluetooth Audio"))
        if am.isWiredHeadsetOn():
            devices.append((2, "Wired Headset"))
        if am.isWiredHeadsetOn():  # also covers headphones
            devices.append((3, "Headphone"))
        return devices
    except Exception as exc:
        _log.debug("Android output device list failed: %s", exc)
        return [(0, "Phone Speaker"), (1, "Bluetooth")]


def _android_list_inputs() -> List[Tuple[int, str]]:
    """Return available microphone/input sources for Android."""
    try:
        from jnius import autoclass  # type: ignore[import]
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Context        = autoclass("android.content.Context")
        AudioManager   = autoclass("android.media.AudioManager")

        ctx = PythonActivity.mActivity
        am  = ctx.getSystemService(Context.AUDIO_SERVICE)

        devices = [(0, "Phone Microphone")]
        if am.isWiredHeadsetOn():
            devices.append((1, "Headset Microphone"))
        if am.isBluetoothScoOn():
            devices.append((2, "Bluetooth Microphone"))
        return devices
    except Exception as exc:
        _log.debug("Android input device list failed: %s", exc)
        return [(0, "Phone Microphone")]


# ── Desktop implementations (delegate to engine) ─────────────────────────────

def _desktop_list_outputs() -> List[Tuple[int, str]]:
    try:
        from app.engine.audio_tools import list_output_devices
        return list_output_devices()
    except Exception as exc:
        _log.warning("Desktop output device list failed: %s", exc)
        return []


def _desktop_list_inputs() -> List[Tuple[int, str]]:
    try:
        from app.engine.audio_tools import list_input_devices
        return list_input_devices()
    except Exception as exc:
        _log.warning("Desktop input device list failed: %s", exc)
        return []


# ── Tone / APRS TX playback (cross-platform) ─────────────────────────────────

def play_tone(freq_hz: float = 1200.0, duration_s: float = 1.0,
              device_idx: Optional[int] = None) -> None:
    """Play a sine-wave test tone at *freq_hz* for *duration_s* seconds."""
    if _ON_ANDROID:
        _android_play_tone(freq_hz, duration_s)
    else:
        _desktop_play_tone(freq_hz, duration_s, device_idx)


def _android_play_tone(freq_hz: float, duration_s: float) -> None:
    """Generate PCM and play via Android AudioTrack."""
    try:
        import math, struct
        from jnius import autoclass  # type: ignore[import]

        AudioTrack  = autoclass("android.media.AudioTrack")
        AudioFormat = autoclass("android.media.AudioFormat")
        AudioMgr    = autoclass("android.media.AudioManager")

        SAMPLE_RATE = 44100
        n_samples   = int(SAMPLE_RATE * duration_s)
        pcm = bytearray(n_samples * 2)
        for i in range(n_samples):
            v = int(32767 * math.sin(2 * math.pi * freq_hz * i / SAMPLE_RATE))
            struct.pack_into("<h", pcm, i * 2, v)

        track = AudioTrack(
            AudioMgr.STREAM_MUSIC,
            SAMPLE_RATE,
            AudioFormat.CHANNEL_OUT_MONO,
            AudioFormat.ENCODING_PCM_16BIT,
            len(pcm),
            AudioTrack.MODE_STATIC,
        )
        track.write(pcm, 0, len(pcm))
        track.play()
    except Exception as exc:
        _log.error("Android play_tone failed: %s", exc)


def _desktop_play_tone(freq_hz: float, duration_s: float,
                       device_idx: Optional[int]) -> None:
    try:
        from app.engine.audio_tools import play_wav_blocking_compatible
        import tempfile, wave, struct, math

        SAMPLE_RATE = 44100
        n_samples   = int(SAMPLE_RATE * duration_s)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            tmp_path = f.name

        with wave.open(tmp_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            data = struct.pack(
                f"<{n_samples}h",
                *[int(32767 * math.sin(2 * math.pi * freq_hz * i / SAMPLE_RATE))
                  for i in range(n_samples)]
            )
            wf.writeframes(data)

        play_wav_blocking_compatible(tmp_path, device_index=device_idx)
    except Exception as exc:
        _log.error("Desktop play_tone failed: %s", exc)

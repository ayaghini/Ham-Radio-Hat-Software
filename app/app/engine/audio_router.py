#!/usr/bin/env python3
"""AudioRouter: device selection, PTT integration, and playback management.

v2 improvements:
- Device selection state is fully encapsulated here; no tkinter vars read
  from worker threads.
- Playback uses subprocess worker for WASAPI compatibility (same as v1)
  but the router owns the logic.
- PTT timing and line config are value types passed in, not read from tk vars.
"""

from __future__ import annotations

import subprocess
import sys
import threading
import wave
from pathlib import Path
from time import sleep
from typing import Callable, Optional

import numpy as np

from .audio_tools import (
    capture_samples,
    estimate_wav_level,
    list_input_devices,
    list_output_devices,
    play_wav_blocking_compatible,
    record_wav,
    stop_playback,
    wav_duration_seconds,
)
from .models import AudioConfig, PttConfig


class AudioRouter:
    """Manages output/input device selection, PTT keying, and audio playback."""

    def __init__(self, app_dir: Path, audio_dir: Optional[Path] = None) -> None:
        self._app_dir = app_dir
        self._audio_dir = audio_dir or (app_dir / "audio_out")
        self._lock = threading.Lock()
        self._worker: Optional[threading.Thread] = None
        self._tx_active = False
        self._tx_level_hold = 0.0
        self._log_cb: Optional[Callable[[str], None]] = None

    def set_log_cb(self, cb: Callable[[str], None]) -> None:
        self._log_cb = cb

    def _log(self, msg: str) -> None:
        if self._log_cb:
            self._log_cb(msg)

    # ------------------------------------------------------------------
    # Device listing
    # ------------------------------------------------------------------

    def refresh_output_devices(self) -> list[tuple[int, str]]:
        return list_output_devices()

    def refresh_input_devices(self) -> list[tuple[int, str]]:
        return list_input_devices()

    # ------------------------------------------------------------------
    # Auto-select SA818 USB audio pair
    # ------------------------------------------------------------------

    def auto_select_usb_pair(self, out_hint: str, in_hint: str) -> Optional[tuple[int, int]]:
        """Try to find matching USB audio device pair.

        Strategy:
        1. Match saved device names if still present.
        2. Exactly one USB output and one USB input → use them.
        3. Match by shared USB token (Windows device number in parentheses).
        4. Match by shared ALSA card number from names like ``(hw:3,0)``.

        Returns (out_idx, in_idx) or None.
        """
        outs = list_output_devices()
        ins = list_input_devices()

        def norm(name: str) -> str:
            import re
            base = re.sub(r"\s*\[[^]]+\]\s*$", "", name.strip())
            return " ".join(base.lower().split())

        # 1) Saved hints
        if out_hint and in_hint:
            out_match = next((idx for idx, n in outs if norm(n) == norm(out_hint)), None)
            in_match = next((idx for idx, n in ins if norm(n) == norm(in_hint)), None)
            if out_match is not None and in_match is not None:
                return out_match, in_match

        # 2) Unique USB pair — USB audio device name keywords by platform:
        #    Windows MME/WASAPI : "usb audio device" (SA818), "usb pnp sound device" (DigiRig CP2102)
        #    macOS Core Audio   : "usb audio codec" (SA818 generic), "usb audio" (broad match)
        #    Linux ALSA         : "usb audio" (USB Audio Class generic)
        #    All platforms      : "digirig" (explicit DigiRig identification)
        _USB_KW = (
            "usb audio device",      # Windows: SA818 USB codec (MME/WASAPI name)
            "usb pnp sound device",  # Windows: DigiRig CP2102 (MME name)
            "usb audio codec",       # macOS: SA818 and generic USB codecs (Core Audio name)
            "usb audio",             # macOS + Linux: broad USB Audio Class match
            "usb sound",             # Linux: alternate USB audio class name
            "digirig",               # All: DigiRig explicit match
        )

        def _is_usb_audio(name: str) -> bool:
            nl = name.lower()
            return any(k in nl for k in _USB_KW)

        usb_outs = [(i, n) for i, n in outs if _is_usb_audio(n)]
        usb_ins = [(i, n) for i, n in ins if _is_usb_audio(n)]
        if len(usb_outs) == 1 and len(usb_ins) == 1:
            return usb_outs[0][0], usb_ins[0][0]

        # 3) Shared USB token — Windows MME device names include a parenthesised
        #    suffix like "(USB Audio Device 2)" that can be used to pair the
        #    output and input entries for the same physical device.
        #    On macOS and Linux, device names do not follow this pattern; this
        #    strategy is a no-op on those platforms and strategy 2 (unique pair)
        #    is the primary cross-platform path.
        import re
        def usb_token(name: str) -> str:
            m = re.search(
                r"\(([^)]*(?:usb audio|usb pnp sound device|usb sound|digirig)[^)]*)\)",
                name, flags=re.IGNORECASE,
            )
            return m.group(1).strip().lower() if m else ""

        out_tok: dict[str, int] = {}
        for idx, name in usb_outs:
            t = usb_token(name)
            if t:
                out_tok[t] = idx
        in_tok: dict[str, int] = {}
        for idx, name in usb_ins:
            t = usb_token(name)
            if t:
                in_tok[t] = idx
        shared = [t for t in out_tok if t in in_tok]
        if len(shared) == 1:
            return out_tok[shared[0]], in_tok[shared[0]]

        # 4) Linux ALSA / PortAudio names expose the card number in the device
        #    label itself, e.g. "(hw:3,0)". Use that to pair input/output for
        #    the same physical USB codec when multiple identical codecs exist.
        def alsa_card_token(name: str) -> str:
            m = re.search(r"\(hw:(\d+),\d+\)", name, flags=re.IGNORECASE)
            return m.group(1) if m else ""

        out_card: dict[str, int] = {}
        for idx, name in usb_outs:
            t = alsa_card_token(name)
            if t:
                out_card[t] = idx
        in_card: dict[str, int] = {}
        for idx, name in usb_ins:
            t = alsa_card_token(name)
            if t:
                in_card[t] = idx
        shared_cards = [t for t in out_card if t in in_card]
        if len(shared_cards) == 1:
            return out_card[shared_cards[0]], in_card[shared_cards[0]]

        # 5) Multiple matched pairs (e.g. two SA818s connected simultaneously).
        #    Sort by sum of device indices and return the lowest-index pair, which
        #    is typically the primary (first-connected) device.
        if shared:
            pairs = sorted(shared, key=lambda t: out_tok[t] + in_tok[t])
            best = pairs[0]
            self._log(
                f"Auto-audio: {len(shared)} USB pairs found; using lowest-index pair "
                f"({out_tok[best]}/{in_tok[best]}). Select manually if wrong."
            )
            return out_tok[best], in_tok[best]
        if shared_cards:
            pairs = sorted(shared_cards, key=lambda t: out_card[t] + in_card[t])
            best = pairs[0]
            self._log(
                f"Auto-audio: {len(shared_cards)} ALSA hw pairs found; using lowest-index pair "
                f"({out_card[best]}/{in_card[best]}). Select manually if wrong."
            )
            return out_card[best], in_card[best]

        return None

    # ------------------------------------------------------------------
    # Playback worker management
    # ------------------------------------------------------------------

    @property
    def worker_busy(self) -> bool:
        return bool(self._worker and self._worker.is_alive())

    def stop_audio(self) -> None:
        stop_playback()
        self._tx_active = False

    # ------------------------------------------------------------------
    # TX audio with PTT (runs blocking in current thread)
    # ------------------------------------------------------------------

    def play_with_ptt_blocking(
        self,
        wav_path: Path,
        out_dev: int,
        ptt: PttConfig,
        ptt_cb: Optional[Callable[[bool], None]] = None,
    ) -> None:
        """Play WAV with PTT keying. Blocks until done. Must run in worker thread."""
        pre_s = max(0.0, ptt.pre_ms / 1000.0)
        post_s = max(0.0, ptt.post_ms / 1000.0)
        duration = wav_duration_seconds(wav_path)
        self._log(f"TX: {wav_path.name} ({duration:.2f}s) → dev={out_dev}")

        with self._lock:
            try:
                if ptt.enabled and ptt_cb:
                    ptt_cb(True)
                    self._log("PTT asserted")
                    if pre_s > 0:
                        sleep(pre_s)

                self._tx_level_hold = estimate_wav_level(wav_path)
                self._tx_active = True
                _play_wav_subprocess(wav_path, out_dev, self._app_dir)
            finally:
                self._tx_active = False
                if ptt.enabled and ptt_cb:
                    if post_s > 0:
                        sleep(post_s)
                    try:
                        ptt_cb(False)
                        self._log("PTT released")
                    except Exception as exc:
                        self._log(f"PTT release failed: {exc}")

    # ------------------------------------------------------------------
    # RX capture (compatible: subprocess on Windows worker threads)
    # ------------------------------------------------------------------

    def capture_compatible(
        self,
        seconds: float,
        device_index: Optional[int],
        wav_out_path: Optional[Path] = None,
    ) -> tuple[int, "np.ndarray"]:
        """Capture audio. On Windows from a non-main thread uses a subprocess."""
        import platform
        import threading as _t

        on_windows = platform.system().lower() == "windows"
        on_worker = _t.current_thread() is not _t.main_thread()

        if on_windows and on_worker and not getattr(sys, "frozen", False):
            ts_path = wav_out_path or (self._audio_dir / f"rx_cap_{id(threading.current_thread())}.wav")
            ts_path.parent.mkdir(parents=True, exist_ok=True)
            _capture_wav_subprocess(ts_path, seconds, device_index, self._app_dir)
            with wave.open(str(ts_path), "rb") as wf:
                rate = int(wf.getframerate())
                channels = int(wf.getnchannels())
                frames = wf.readframes(wf.getnframes())
            mono = np.frombuffer(frames, dtype=np.int16)
            if channels > 1:
                mono = mono.reshape(-1, channels)[:, 0]
            if wav_out_path is None:
                try:
                    ts_path.unlink(missing_ok=True)
                except Exception:
                    pass
            return rate, mono.astype(np.float32) / 32768.0

        return capture_samples(seconds=seconds, device_index=device_index)

    def record_compatible(self, wav_path: Path, seconds: float, device_index: Optional[int]) -> None:
        """Record WAV. On Windows from a non-main thread uses a subprocess."""
        import platform
        import threading as _t

        if (
            platform.system().lower() == "windows"
            and _t.current_thread() is not _t.main_thread()
            and not getattr(sys, "frozen", False)
        ):
            _capture_wav_subprocess(wav_path, seconds, device_index, self._app_dir)
            return
        record_wav(wav_path, seconds=seconds, device_index=device_index)

    # ------------------------------------------------------------------
    # Output level tracking (for visualiser)
    # ------------------------------------------------------------------

    @property
    def tx_active(self) -> bool:
        return self._tx_active

    @property
    def tx_level_hold(self) -> float:
        return self._tx_level_hold


# ---------------------------------------------------------------------------
# Subprocess helpers (Windows WASAPI thread-affinity workaround)
# ---------------------------------------------------------------------------

def _play_wav_subprocess(wav_path: Path, device_index: int, app_dir: Path) -> None:
    import platform

    # In frozen PyInstaller apps, sys.executable is the app binary rather than a Python
    # interpreter, so `sys.executable script.py ...` recurses or fails instead of running
    # the helper worker.  Fall back to direct compatible playback there.
    if getattr(sys, "frozen", False):
        play_wav_blocking_compatible(wav_path, device_index=device_index)
        return

    script = app_dir / "scripts" / "play_wav_worker.py"
    if platform.system().lower() == "windows" and script.exists():
        proc = subprocess.run(
            [sys.executable, str(script), "--wav", str(wav_path), "--output-device", str(device_index)],
            capture_output=True, text=True, check=False,
        )
        if proc.returncode == 0:
            return
        detail = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(detail or f"Playback worker exit={proc.returncode}")
    play_wav_blocking_compatible(wav_path, device_index=device_index)


def _capture_wav_subprocess(wav_path: Path, seconds: float, device_index: Optional[int], app_dir: Path) -> None:
    # Same frozen-app issue as playback: PyInstaller bundles cannot run `.py` helper
    # scripts via sys.executable. Let callers fall back to in-process capture there.
    if getattr(sys, "frozen", False):
        raise RuntimeError("capture subprocess helper is unavailable in frozen builds")

    script = app_dir / "scripts" / "capture_wav_worker.py"
    if not script.exists():
        raise RuntimeError(f"Missing script: {script}")
    dev = -1 if device_index is None else int(device_index)
    proc = subprocess.run(
        [
            sys.executable, str(script),
            "--wav", str(wav_path),
            "--seconds", f"{float(seconds):.3f}",
            "--input-device", str(dev),
        ],
        capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or f"exit={proc.returncode}").strip()
        raise RuntimeError(detail)

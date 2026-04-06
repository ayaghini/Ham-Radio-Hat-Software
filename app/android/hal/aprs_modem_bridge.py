"""hal/aprs_modem_bridge.py — APRS modem TX/RX bridge for Android and desktop.

Reuses the engine's pure-Python APRS DSP (app.engine.aprs_modem) for both
encoding and decoding.  Only the audio I/O layer differs per platform:

  TX path (encode + play)
  ───────────────────────
  build_ax25_ui_frame(source, dest, path, info)
      → frame_to_bitstream()
          → nrzi_encode()
              → afsk_from_nrzi() → raw PCM bytes (int16 LE, 48 kHz mono)
                  → Android AudioTrack  (jnius)
                  → or sounddevice.play() (desktop)

  RX path (capture + decode)
  ──────────────────────────
  Android AudioRecord (jnius) → PCM bytes → np.int16 array → float32
      → decode_ax25_from_samples(rate, array) → [DecodedPacket, …]
          → on_packet_decoded callback (Kivy main thread via Clock.schedule_once)

  Desktop: sounddevice.InputStream → same decode pipeline

PTT control
───────────
  Android: PTT is sent as a serial RTS line (via SerialManager, if connected)
           or via VOX (no explicit PTT — user enables VOX on SA818).
  Desktop: delegates to app.engine.audio_tools / radio_ctrl.
"""

from __future__ import annotations

import logging
import struct
import threading
from typing import Callable, Optional

import numpy as np

try:
    from kivy.utils import platform as _kivy_platform
    _ON_ANDROID: bool = (_kivy_platform == "android")
except ImportError:
    _ON_ANDROID = False

_log = logging.getLogger(__name__)

# Sample rate must match engine modem
_SAMPLE_RATE = 48_000


# ── TX helpers ───────────────────────────────────────────────────────────────

def _build_pcm(source: str, dest: str, path: str, info: str,
               gain: float = 0.6) -> bytes:
    """Return int16-LE PCM for an APRS packet."""
    from app.engine.aprs_modem import (
        build_ax25_ui_frame,
        frame_to_bitstream,
        nrzi_encode,
        afsk_from_nrzi,
    )
    frame   = build_ax25_ui_frame(source, dest, path, info)
    bits    = frame_to_bitstream(frame)
    nrzi    = nrzi_encode(bits)
    pcm     = afsk_from_nrzi(nrzi, sample_rate=_SAMPLE_RATE, tx_gain=gain)
    return pcm   # bytes, int16-LE mono


# ── AprsModemBridge ──────────────────────────────────────────────────────────

class AprsModemBridge:
    """Cross-platform APRS modem.

    Callbacks (all invoked on a background thread; use Clock.schedule_once
    in your Kivy code)::

        on_packet_decoded(packet: DecodedPacket)
        on_tx_done()
        on_error(msg: str)
    """

    DECODE_CHUNK_MS = 200       # RX buffer slice duration
    DECODE_CHUNK    = int(_SAMPLE_RATE * DECODE_CHUNK_MS / 1000)

    def __init__(self) -> None:
        self._rx_thread:  Optional[threading.Thread] = None
        self._rx_stop     = threading.Event()
        self._tx_lock     = threading.Lock()

        # Callbacks — set by caller
        self.on_packet_decoded: Optional[Callable] = None
        self.on_tx_done:        Optional[Callable] = None
        self.on_error:          Optional[Callable[[str], None]] = None

        # Optional radio controller for PTT
        self._radio_ctrl = None    # RadioController instance

        # Audio device indices (desktop)
        self.output_device_idx: Optional[int] = None
        self.input_device_idx:  Optional[int] = None

    # ── PTT wiring ────────────────────────────────────────────────────────────

    def set_radio_controller(self, ctrl) -> None:
        """Optional: supply a RadioController for RTS PTT on SA818."""
        self._radio_ctrl = ctrl

    # ── TX ────────────────────────────────────────────────────────────────────

    def transmit(
        self,
        source: str,
        dest: str,
        path: str,
        info: str,
        gain: float = 0.6,
    ) -> None:
        """Encode and play an APRS packet.  Non-blocking (runs in thread)."""
        t = threading.Thread(
            target=self._tx_worker,
            args=(source, dest, path, info, gain),
            daemon=True,
            name="AprsModemTX",
        )
        t.start()

    def _tx_worker(self, source, dest, path, info, gain) -> None:
        with self._tx_lock:
            try:
                pcm = _build_pcm(source, dest, path, info, gain)
                self._ptt(True)
                if _ON_ANDROID:
                    self._android_play(pcm)
                else:
                    self._desktop_play(pcm)
            except Exception as exc:
                _log.error("APRS TX error: %s", exc)
                if self.on_error:
                    self.on_error(str(exc))
            finally:
                self._ptt(False)
                if self.on_tx_done:
                    self.on_tx_done()

    def _ptt(self, state: bool) -> None:
        """Assert/de-assert PTT via RadioController RTS."""
        if self._radio_ctrl is None:
            return
        try:
            if hasattr(self._radio_ctrl, "set_ptt"):
                self._radio_ctrl.set_ptt(state)
        except Exception as exc:
            _log.debug("PTT error (ignored): %s", exc)

    # Android audio output ───────────────────────────────────────────────────

    def _android_play(self, pcm: bytes) -> None:
        try:
            from jnius import autoclass  # type: ignore[import]
            AudioTrack  = autoclass("android.media.AudioTrack")
            AudioFormat = autoclass("android.media.AudioFormat")
            AudioMgr    = autoclass("android.media.AudioManager")

            track = AudioTrack(
                AudioMgr.STREAM_MUSIC,
                _SAMPLE_RATE,
                AudioFormat.CHANNEL_OUT_MONO,
                AudioFormat.ENCODING_PCM_16BIT,
                len(pcm),
                AudioTrack.MODE_STATIC,
            )
            track.write(pcm, 0, len(pcm))
            track.play()
            # Wait for playback to finish
            duration_s = len(pcm) / (2 * _SAMPLE_RATE)  # int16 = 2 bytes
            import time
            time.sleep(duration_s + 0.05)
            track.stop()
            track.release()
        except Exception as exc:
            raise RuntimeError(f"Android audio play failed: {exc}") from exc

    # Desktop audio output ───────────────────────────────────────────────────

    def _desktop_play(self, pcm: bytes) -> None:
        try:
            import sounddevice as sd  # type: ignore[import]
            samples = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768.0
            sd.play(samples, samplerate=_SAMPLE_RATE,
                    device=self.output_device_idx, blocking=True)
        except ImportError:
            # Fallback: write wav and play via system command
            import tempfile, wave, subprocess, os
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                tmp = f.name
            with wave.open(tmp, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(_SAMPLE_RATE)
                wf.writeframes(pcm)
            try:
                subprocess.run(["afplay", tmp], check=False, timeout=30)
            finally:
                os.unlink(tmp)

    # ── RX ────────────────────────────────────────────────────────────────────

    def start_rx(self) -> None:
        """Start the background audio capture + decode loop."""
        if self._rx_thread and self._rx_thread.is_alive():
            return
        self._rx_stop.clear()
        target = self._android_rx_loop if _ON_ANDROID else self._desktop_rx_loop
        self._rx_thread = threading.Thread(
            target=target, daemon=True, name="AprsModemRX"
        )
        self._rx_thread.start()
        _log.info("APRS RX started")

    def stop_rx(self) -> None:
        """Stop the background audio capture loop."""
        self._rx_stop.set()
        if self._rx_thread:
            self._rx_thread.join(timeout=3.0)
        self._rx_thread = None
        _log.info("APRS RX stopped")

    @property
    def rx_running(self) -> bool:
        return self._rx_thread is not None and self._rx_thread.is_alive()

    # Android audio input ────────────────────────────────────────────────────

    def _android_rx_loop(self) -> None:
        """Capture audio via Android AudioRecord and decode APRS packets."""
        try:
            from jnius import autoclass  # type: ignore[import]
            AudioRecord  = autoclass("android.media.AudioRecord")
            AudioFormat  = autoclass("android.media.AudioFormat")
            MediaRecorder= autoclass("android.media.MediaRecorder$AudioSource")

            buf_size = max(
                AudioRecord.getMinBufferSize(
                    _SAMPLE_RATE,
                    AudioFormat.CHANNEL_IN_MONO,
                    AudioFormat.ENCODING_PCM_16BIT,
                ),
                self.DECODE_CHUNK * 2,
            )

            recorder = AudioRecord(
                MediaRecorder.MIC,
                _SAMPLE_RATE,
                AudioFormat.CHANNEL_IN_MONO,
                AudioFormat.ENCODING_PCM_16BIT,
                buf_size,
            )
            recorder.startRecording()
            _log.info("Android AudioRecord started @ %d Hz", _SAMPLE_RATE)

            rolling = np.zeros(0, dtype=np.float32)

            try:
                while not self._rx_stop.is_set():
                    raw = bytearray(self.DECODE_CHUNK * 2)
                    n   = recorder.read(raw, 0, len(raw))
                    if n <= 0:
                        continue
                    chunk = np.frombuffer(bytes(raw[:n]), dtype="<i2").astype(np.float32) / 32768.0
                    rolling = np.concatenate([rolling, chunk])
                    # Decode in 1-second windows; keep 0.5 s overlap
                    window = _SAMPLE_RATE
                    if len(rolling) >= window:
                        packets = self._decode(rolling[:window])
                        for p in packets:
                            if self.on_packet_decoded:
                                self.on_packet_decoded(p)
                        rolling = rolling[window // 2:]
            finally:
                recorder.stop()
                recorder.release()
        except Exception as exc:
            _log.error("Android RX loop error: %s", exc)
            if self.on_error:
                self.on_error(str(exc))

    # Desktop audio input ────────────────────────────────────────────────────

    def _desktop_rx_loop(self) -> None:
        """Capture audio via sounddevice and decode APRS packets."""
        try:
            import sounddevice as sd  # type: ignore[import]
        except ImportError:
            _log.error("sounddevice not installed — APRS RX unavailable on desktop")
            if self.on_error:
                self.on_error("sounddevice not installed")
            return

        rolling = np.zeros(0, dtype=np.float32)

        def _callback(indata, frames, time_info, status):
            nonlocal rolling
            if status:
                _log.debug("sounddevice status: %s", status)
            chunk = indata[:, 0].copy()  # mono
            rolling = np.concatenate([rolling, chunk])
            window = _SAMPLE_RATE
            if len(rolling) >= window:
                packets = self._decode(rolling[:window])
                for p in packets:
                    if self.on_packet_decoded:
                        self.on_packet_decoded(p)
                rolling = rolling[window // 2:]

        try:
            with sd.InputStream(
                samplerate=_SAMPLE_RATE,
                channels=1,
                dtype="float32",
                blocksize=self.DECODE_CHUNK,
                device=self.input_device_idx,
                callback=_callback,
            ):
                self._rx_stop.wait()
        except Exception as exc:
            _log.error("Desktop RX loop error: %s", exc)
            if self.on_error:
                self.on_error(str(exc))

    # ── decode ────────────────────────────────────────────────────────────────

    def _decode(self, samples: np.ndarray) -> list:
        """Run engine APRS decoder on a float32 mono array."""
        try:
            from app.engine.aprs_modem import decode_ax25_from_samples
            return decode_ax25_from_samples(_SAMPLE_RATE, samples)
        except Exception as exc:
            _log.debug("APRS decode error: %s", exc)
            return []


# ── Module-level convenience: build position and message payloads ─────────────

def build_position_info(
    source: str,   # noqa: ARG001 — included for caller clarity; engine doesn't need it
    lat: float,
    lon: float,
    comment: str = "",
    symbol_table: str = "/",
    symbol_code: str = ">",
) -> str:
    """Build a standard uncompressed APRS position info string.

    The *source* callsign is embedded in the AX.25 frame header by
    ``AprsModemBridge.transmit()``, not in the info field; it is accepted
    here for call-site clarity only.
    """
    from app.engine.aprs_modem import build_aprs_position_payload
    return build_aprs_position_payload(
        lat_deg=lat,
        lon_deg=lon,
        comment=comment,
        symbol_table=symbol_table,
        symbol=symbol_code,
    )


def build_message_info(addressee: str, text: str, msg_id: str = "") -> str:
    """Build an APRS message info string (:CALLSIGN :text{id})."""
    from app.engine.aprs_modem import build_aprs_message_payload
    return build_aprs_message_payload(addressee=addressee, text=text, message_id=msg_id)

#!/usr/bin/env python3
"""Transmit a WAV file through SA818 with explicit PTT control — standalone worker.

This is the subprocess used by AudioRouter for WASAPI-compatible TX.
It connects to the radio, keys PTT, plays the WAV, then releases PTT.
Radio config is restored by the caller (parent process); this worker only
applies the given config and transmits.

Exit codes:
  0 — success
  1 — error (message on stderr)
  2 — WAV file not found
"""

from __future__ import annotations

import argparse
import sys
import time
import wave
from pathlib import Path


def _setup_path() -> None:
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="SA818 WAV TX worker")
    p.add_argument("--port",            required=True)
    p.add_argument("--wav",             required=True)
    p.add_argument("--frequency",       type=float, required=True)
    p.add_argument("--bandwidth",       type=int, choices=[0, 1], default=0)
    p.add_argument("--squelch",         type=int, default=4)
    p.add_argument("--volume",          type=int, default=5)
    p.add_argument("--output-device",   type=int, required=True)
    p.add_argument("--ptt-line",        choices=["RTS", "DTR"], default="RTS")
    p.add_argument("--ptt-pre-ms",      type=float, default=400.0)
    p.add_argument("--ptt-post-ms",     type=float, default=120.0)
    p.add_argument("--set-filters-flat", action="store_true",
                   help="Disable all SA818 audio filters before TX")

    ptt_grp = p.add_mutually_exclusive_group()
    ptt_grp.add_argument("--ptt-active-high", dest="ptt_active_high", action="store_true",
                         help="Active (TX) = logic HIGH on the control line")
    ptt_grp.add_argument("--ptt-active-low",  dest="ptt_active_high", action="store_false",
                         help="Active (TX) = logic LOW on the control line")
    p.set_defaults(ptt_active_high=True)
    return p.parse_args()


def _load_wav_float32(wav_path: Path) -> tuple["np.ndarray", int]:  # type: ignore[name-defined]
    """Load WAV → float32 in [-1, 1].

    Supported sample widths:
      1 byte  — 8-bit unsigned (WAV standard; bias-subtract before normalise)
      2 bytes — 16-bit signed int16
      3 bytes — 24-bit signed PCM (sign-extended to int32 before normalise)
      4 bytes — 32-bit signed int32
    Raises ValueError for any other sample width.
    """
    import numpy as np

    with wave.open(str(wav_path), "rb") as wf:
        rate      = wf.getframerate()
        channels  = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        frames    = wf.readframes(wf.getnframes())

    if sampwidth == 1:
        # 8-bit WAV is unsigned (range 0–255, centre at 128).
        raw = np.frombuffer(frames, dtype=np.uint8)
        data_f = (raw.astype(np.float32) - 128.0) / 128.0
    elif sampwidth == 2:
        raw = np.frombuffer(frames, dtype=np.int16)
        data_f = raw.astype(np.float32) / float(np.iinfo(np.int16).max)
    elif sampwidth == 3:
        # 24-bit PCM: 3 bytes per sample, little-endian signed.
        # NumPy has no native 3-byte dtype; sign-extend each sample to int32 manually.
        raw3 = np.frombuffer(frames, dtype=np.uint8).reshape(-1, 3)
        n = len(raw3)
        padded = np.empty((n, 4), dtype=np.uint8)
        padded[:, :3] = raw3
        # Sign-extend: if the MSB of the 3-byte sample has bit 7 set, fill with 0xFF.
        padded[:, 3] = np.where(raw3[:, 2] >= 0x80, np.uint8(0xFF), np.uint8(0x00))
        ints = padded.view(np.int32).reshape(-1)
        data_f = ints.astype(np.float32) / float(np.iinfo(np.int32).max >> 8)  # 2^23 - 1
    elif sampwidth == 4:
        raw = np.frombuffer(frames, dtype=np.int32)
        data_f = raw.astype(np.float32) / float(np.iinfo(np.int32).max)
    else:
        raise ValueError(
            f"unsupported WAV sample width {sampwidth} bytes "
            f"({sampwidth * 8}-bit PCM) in {wav_path.name!r}"
        )

    if channels > 1:
        data_f = data_f.reshape(-1, channels)
    return data_f, rate


def main() -> int:
    _setup_path()
    args = parse_args()

    wav_path = Path(args.wav)
    if not wav_path.exists():
        print(f"[tx_wav_worker] WAV not found: {wav_path}", file=sys.stderr)
        return 2

    from app.engine.sa818_client import SA818Client, SA818Error
    from app.engine.models import RadioConfig

    import sounddevice as sd

    _connected = False
    client = SA818Client()
    try:
        client.connect(args.port, timeout=1.5)
        _connected = True

        cfg = RadioConfig(
            frequency=float(args.frequency),
            offset=0.0,
            bandwidth=int(args.bandwidth),
            squelch=max(0, min(8, int(args.squelch))),
        )
        client.set_radio(cfg)
        client.set_volume(max(1, min(8, int(args.volume))))
        if args.set_filters_flat:
            try:
                client.set_filters(True, True, True)
            except Exception:
                pass

        data_f, rate = _load_wav_float32(wav_path)

        # PTT → pre-delay → play → post-delay → release PTT
        client.set_ptt(True, line=args.ptt_line, active_high=args.ptt_active_high)
        time.sleep(max(0.0, args.ptt_pre_ms / 1000.0))
        try:
            sd.play(data_f, samplerate=rate, device=int(args.output_device), blocking=True)
        finally:
            # Primary PTT release: always runs whether play succeeded or not.
            time.sleep(max(0.0, args.ptt_post_ms / 1000.0))
            client.set_ptt(False, line=args.ptt_line, active_high=args.ptt_active_high)

        return 0

    except SA818Error as exc:
        print(f"[tx_wav_worker] SA818 error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"[tx_wav_worker] Error: {exc}", file=sys.stderr)
        return 1
    finally:
        # Safety-net PTT release: guards against exceptions raised before set_ptt(True)
        # was reached or before the inner finally ran.  Harmless if PTT is already low.
        if _connected:
            try:
                client.set_ptt(False, line=args.ptt_line, active_high=args.ptt_active_high)
            except Exception:
                pass
        # Disconnect is always attempted but never allowed to mask the real exit code.
        try:
            client.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())

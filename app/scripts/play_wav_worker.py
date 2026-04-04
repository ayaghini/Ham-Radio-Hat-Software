#!/usr/bin/env python3
"""Play WAV on a specific output device — standalone subprocess worker.

Used by AudioRouter to work around Windows WASAPI thread-affinity restrictions.
The main process spawns this as a subprocess so audio plays from a fresh thread.
"""

from __future__ import annotations

import argparse
import sys
import wave
from pathlib import Path


def _setup_path() -> None:
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="WAV playback worker")
    p.add_argument("--wav", required=True, help="Path to WAV file")
    p.add_argument("--output-device", type=int, required=True,
                   help="sounddevice output device index")
    return p.parse_args()


def _validate_output_device(device_idx: int) -> None:
    """Raise ValueError with a clear message if device_idx is not a usable output device."""
    import sounddevice as sd
    try:
        info = sd.query_devices(device_idx)
    except Exception as exc:
        raise ValueError(f"output device index {device_idx} not found: {exc}") from exc
    if info["max_output_channels"] < 1:
        raise ValueError(
            f"device {device_idx} ({info['name']!r}) has no output channels"
        )


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
        print(f"[play_wav_worker] WAV not found: {wav_path}", file=sys.stderr)
        return 2

    try:
        import sounddevice as sd

        # Validate device before spending time loading the WAV.
        try:
            _validate_output_device(args.output_device)
        except ValueError as exc:
            print(f"[play_wav_worker] {exc}", file=sys.stderr)
            return 1

        data_f, rate = _load_wav_float32(wav_path)
        sd.play(data_f, samplerate=rate, device=int(args.output_device), blocking=True)
        return 0

    except Exception as exc:
        print(f"[play_wav_worker] Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Capture audio and print a voice-activity score — standalone subprocess worker.

Output: a single float on stdout (0.0 = silence, larger = louder).
Exit 0 on success.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _setup_path() -> None:
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="RX voice-activity score worker")
    p.add_argument("--seconds", type=float, required=True)
    p.add_argument("--sample-rate", type=int, default=48000)
    p.add_argument("--input-device", type=int, default=-1)
    return p.parse_args()


def _validate_capture_args(args: argparse.Namespace) -> str | None:
    if args.seconds <= 0:
        return "--seconds must be greater than 0"
    if args.sample_rate <= 0:
        return "--sample-rate must be greater than 0"
    frames = int(args.seconds * args.sample_rate)
    if frames <= 0:
        return "capture frame count must be greater than 0"
    return None


def _validate_input_device(sd, device: int | None) -> str | None:
    if device is None:
        return None
    try:
        info = sd.query_devices(device)
    except Exception as exc:
        return f"input device {device} is invalid: {exc}"
    max_inputs = int(info.get("max_input_channels", 0))
    if max_inputs <= 0:
        return f"input device {device} has no input channels"
    return None


def voice_activity_score(samples) -> float:
    """Weighted combination of RMS energy and 95th-percentile amplitude."""
    import numpy as np
    x = np.asarray(samples, dtype=np.float32).reshape(-1)
    if len(x) < 32:
        return 0.0
    x = x - float(np.mean(x))
    rms = float(np.sqrt(np.mean(x * x)))
    p95 = float(np.percentile(np.abs(x), 95))
    return (0.7 * rms) + (0.3 * p95)


def main() -> int:
    _setup_path()
    args = parse_args()

    device = None if int(args.input_device) < 0 else int(args.input_device)
    arg_error = _validate_capture_args(args)
    if arg_error:
        print(f"[rx_score_worker] Error: {arg_error}", file=sys.stderr)
        print("0.00000000")
        return 1

    try:
        import sounddevice as sd
        import numpy as np

        device_error = _validate_input_device(sd, device)
        if device_error:
            print(f"[rx_score_worker] Error: {device_error}", file=sys.stderr)
            print("0.00000000")
            return 1

        data = sd.rec(
            frames=int(args.seconds * args.sample_rate),
            samplerate=args.sample_rate,
            channels=1,
            dtype="float32",
            device=device,
        )
        sd.wait()

        if data is None or getattr(data, "size", 0) == 0:
            print("[rx_score_worker] Error: no audio captured", file=sys.stderr)
            print("0.00000000")
            return 1

        mono = data.reshape(-1).astype(np.float32)
        if mono.size == 0:
            print("[rx_score_worker] Error: no audio captured", file=sys.stderr)
            print("0.00000000")
            return 1
        score = voice_activity_score(mono)
        print(f"{score:.8f}")
        return 0

    except Exception as exc:
        print(f"[rx_score_worker] Error: {exc}", file=sys.stderr)
        # Print 0.0 so caller does not crash trying to parse stdout
        print("0.00000000")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

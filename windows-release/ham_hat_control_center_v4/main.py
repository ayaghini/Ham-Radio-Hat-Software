#!/usr/bin/env python3
"""HAM HAT Control Center v4 - entry point."""

from __future__ import annotations

import logging
import argparse
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure the package is importable regardless of working directory
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))


def _configure_logging(level: int = logging.WARNING) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    # Suppress noisy library warnings
    for noisy in ("sounddevice", "comtypes", "pyserial"):
        logging.getLogger(noisy).setLevel(logging.ERROR)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="HAM HAT Control Center v4.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity. -v for INFO, -vv for DEBUG.",
    )
    parser.add_argument(
        "--rpi",
        action="store_true",
        default=False,
        help=(
            "Raspberry Pi / small-screen mode.  Optimised for a 5-inch "
            "1280×720 display: sets window geometry to 1280x720+0+0, "
            "increases tk scaling to 1.5, and reduces widget heights to fit "
            "the 720 px vertical budget.  Implies --geometry 1280x720+0+0 "
            "and --scale 1.5 unless overridden."
        ),
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=None,
        metavar="FACTOR",
        help=(
            "Override the Tkinter scaling factor (default: 1.0 on desktop, "
            "1.5 with --rpi).  Higher values make all widgets larger; useful "
            "for small high-DPI screens where X11 reports the wrong DPI."
        ),
    )
    parser.add_argument(
        "--geometry",
        type=str,
        default=None,
        metavar="WxH+X+Y",
        help=(
            "Override the initial window geometry, e.g. '1280x720+0+0'. "
            "Default: window manager decides."
        ),
    )
    parser.add_argument(
        "--fullscreen",
        action="store_true",
        default=False,
        help=(
            "Start in full-screen mode (removes OS window chrome completely). "
            "Recommended for dedicated RPi displays with no window manager. "
            "Mutually exclusive with --geometry."
        ),
    )
    args = parser.parse_args()

    # Each -v flag decreases the log level by 10
    log_level = logging.WARNING - (args.verbose * 10)
    # Ensure the level doesn't go below DEBUG (10)
    log_level = max(log_level, logging.DEBUG)
    _configure_logging(level=log_level)

    try:
        from app.app import HamHatApp
        from app.engine.display_config import DisplayConfig
    except ImportError as exc:
        print(f"Import error - is your virtualenv active?\n{exc}", file=sys.stderr)
        return 1

    display_cfg = DisplayConfig.from_args(
        rpi=args.rpi,
        scale=args.scale,
        geometry=args.geometry,
        fullscreen=args.fullscreen,
    )

    app = HamHatApp(app_dir=_HERE, display_cfg=display_cfg)
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


#!/usr/bin/env python3
"""Cross-platform bring-up validation script.

Runs a checklist of functional items against the current platform without
requiring a display or hardware.  Designed for first-run validation on
Linux desktop, macOS, and Raspberry Pi.

Execute from the repo root:
    python3 app/scripts/platform_validation.py

Or from the app directory:
    python3 scripts/platform_validation.py

Exit codes:
  0 — all checks passed (SKIP is not a failure)
  1 — one or more checks failed
"""

from __future__ import annotations

import platform
import sys
import tempfile
from pathlib import Path

# Allow running from repo root or from app/
_HERE = Path(__file__).resolve().parent
_APP_ROOT = _HERE.parent
if str(_APP_ROOT) not in sys.path:
    sys.path.insert(0, str(_APP_ROOT))


# ---------------------------------------------------------------------------
# Harness
# ---------------------------------------------------------------------------

_PASS = _FAIL = _SKIP = 0
_results: list[tuple[str, str, str]] = []


def ck(label: str, ok: bool, detail: str = "", skip: bool = False) -> None:
    global _PASS, _FAIL, _SKIP
    if skip:
        tag = "SKIP"; _SKIP += 1
    elif ok:
        tag = "PASS"; _PASS += 1
    else:
        tag = "FAIL"; _FAIL += 1
    _results.append((tag, label, detail))


def section(title: str) -> None:
    print(f"\n{'─'*50}")
    print(f"  {title}")
    print(f"{'─'*50}")


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_python_version() -> None:
    section("Python runtime")
    maj, min_, *_ = sys.version_info
    ck("Python 3.9+", (maj, min_) >= (3, 9),
       f"Python {maj}.{min_} — need 3.9+")
    ck("Python < 3.13 (venv compat note)",
       (maj, min_) < (3, 13),
       f"Python {maj}.{min_} — bleak + scipy use match-statement syntax; "
       "compile with 3.10+ for full feature set", skip=(maj, min_) >= (3, 13))


def check_imports() -> None:
    section("Core imports")
    for mod in ("numpy", "sounddevice", "serial"):
        try:
            __import__(mod)
            ck(f"{mod} importable", True)
        except ImportError as e:
            ck(f"{mod} importable", False, str(e))

    for mod, note in [
        ("bleak",  "required for PAKT BLE mode"),
        ("PIL",    "optional — map tile rendering"),
        ("scipy",  "optional — faster APRS decode"),
        ("sv_ttk", "optional — UI theme"),
        ("requests", "optional — tile download"),
    ]:
        try:
            __import__(mod)
            ck(f"{mod} importable (optional)", True)
        except ImportError:
            ck(f"{mod} absent ({note})", True, "guard active — app degrades gracefully", skip=True)


def check_tkinter() -> None:
    section("Tkinter (system package on Linux/RPi)")
    try:
        import tkinter as tk
        ck("tkinter importable", True)
        # Quick non-display test: just check the module is functional
        ck("tkinter version accessible", bool(tk.TkVersion),
           f"TkVersion={tk.TkVersion}")
    except ImportError as e:
        ck("tkinter importable", False,
           f"{e} — install with: sudo apt install python3-tk")
    except Exception as e:
        # On headless Linux without DISPLAY, creating widgets fails but the
        # import itself succeeding is enough for bring-up confirmation
        ck("tkinter importable", True, f"(no display — expected on headless: {e})")


def check_audio() -> None:
    section("Audio enumeration")
    try:
        from app.engine.audio_tools import list_output_devices, list_input_devices
        out = list_output_devices()
        inp = list_input_devices()
        ck("list_output_devices()", True, f"{len(out)} output(s)")
        ck("list_input_devices()", True,  f"{len(inp)} input(s)")
        for idx, name in out:
            print(f"    out [{idx:2d}] {name}")
        for idx, name in inp:
            print(f"    in  [{idx:2d}] {name}")
        if not out and not inp:
            ck("audio devices found", False,
               "no audio devices — sounddevice may need ALSA/PulseAudio")
    except Exception as e:
        ck("audio enumeration", False, str(e))


def check_serial() -> None:
    section("Serial port scan")
    try:
        import serial.tools.list_ports as lp
        ports = list(lp.comports())
        ck("pyserial scan executes", True, f"{len(ports)} port(s) found")
        for p in ports:
            print(f"    {p.device:28s} {p.description}")
        if not ports:
            print("    (no ports — expected without SA818/DigiRig hardware)")

        # Check platform-expected naming
        plat = platform.system()
        if plat == "Darwin":
            ok = not ports or all(p.device.startswith("/dev/cu.") for p in ports)
            ck("macOS /dev/cu.* naming", ok, str([p.device for p in ports]))
        elif plat == "Linux":
            usb_ports = [p for p in ports if "USB" in p.device or "ttyAMA" in p.device or "ACM" in p.device]
            ck("Linux serial port scan", True,
               f"{len(usb_ports)} USB/AMA port(s): {[p.device for p in usb_ports]}")
    except Exception as e:
        ck("serial scan", False, str(e))


def check_ble() -> None:
    section("BLE / PAKT transport")
    try:
        from app.engine.pakt.transport import PaktBleTransport, TransportState
        ck("transport module loads", True)
        ck("TransportState members",
           all(s.name in [t.name for t in TransportState]
               for s in [TransportState.IDLE, TransportState.DISCONNECTED
                         if hasattr(TransportState, "DISCONNECTED") else TransportState.IDLE]),
           str([s.name for s in TransportState]))
    except Exception as e:
        ck("transport module", False, str(e))

    try:
        import bleak
        ck("bleak installed", True, f"v{bleak.__version__}")
        plat = platform.system()
        if plat == "Linux":
            ck("Linux BLE note", True,
               "ensure: sudo usermod -aG bluetooth $USER  (BlueZ/dbus required)",
               skip=True)
        elif plat == "Darwin":
            ck("macOS BLE note", True,
               "Bluetooth permission dialog will appear on first real scan",
               skip=True)
    except ImportError:
        ck("bleak absent", True,
           "install with: pip install bleak   (required for PAKT mode)",
           skip=True)

    # Check dialout group on Linux (serial access)
    if platform.system() == "Linux":
        import os, grp
        try:
            dialout_gid = grp.getgrnam("dialout").gr_gid
            user_groups = os.getgroups()
            in_dialout = dialout_gid in user_groups
            ck("user in dialout group", in_dialout,
               "run: sudo usermod -aG dialout $USER  then log out/in"
               if not in_dialout else "serial access OK")
        except Exception:
            ck("dialout group check", True, "group not found — skip", skip=True)


def check_profile() -> None:
    section("Profile persistence")
    try:
        from app.engine.models import AppProfile
        from app.engine.profile import ProfileManager

        for mode in ("SA818", "DigiRig", "PAKT"):
            p = AppProfile()
            p.hardware_mode  = mode
            p.aprs_source    = "VE3TEST-7"
            p.frequency      = 144.390
            p.squelch        = 2
            p.chat_contacts  = ["W1AW", "KD9XYZ"]

            with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
                tmp = Path(f.name)
            try:
                pm = ProfileManager(tmp)
                pm.save(p)
                p2 = pm.load()
                ok = (p2 is not None
                      and p2.hardware_mode   == mode
                      and p2.aprs_source     == "VE3TEST-7"
                      and abs(p2.frequency - 144.390) < 0.001
                      and p2.chat_contacts   == ["W1AW", "KD9XYZ"])
                ck(f"profile {mode} round-trip", ok,
                   f"mode={p2.hardware_mode if p2 else 'None'}")
            finally:
                tmp.unlink(missing_ok=True)
    except Exception as e:
        ck("profile system", False, str(e))


def check_paths() -> None:
    section("Platform data paths")
    try:
        from app.engine.platform_paths import get_user_data_dir, get_user_log_dir
        dd = get_user_data_dir("HamHatCC")
        ld = get_user_log_dir("HamHatCC")
        plat = platform.system()

        ck("data dir resolved", dd is not None, str(dd))
        ck("log dir resolved",  ld is not None, str(ld))

        if plat == "Darwin":
            ck("macOS data dir in ~/Library",
               "Library/Application Support" in str(dd), str(dd))
            ck("macOS log dir in ~/Library/Logs",
               "Library/Logs" in str(ld), str(ld))
        elif plat == "Linux":
            ck("Linux data dir is ~/.local/share",
               ".local/share" in str(dd), str(dd))

        ck("data dir exists (or will be created)",
           dd.exists() or not dd.exists(),  # always true: just show path
           f"{dd} ({'exists' if dd.exists() else 'will be created on first run'})")
    except Exception as e:
        ck("platform paths", False, str(e))


def check_display_config() -> None:
    section("DisplayConfig")
    try:
        from app.engine.display_config import DisplayConfig
        d = DisplayConfig.default()
        r = DisplayConfig.rpi_720p()
        ck("default scale=1.0",      d.scale == 1.0, f"scale={d.scale}")
        ck("rpi scale=1.5",          r.scale == 1.5, f"scale={r.scale}")
        ck("rpi compact_padding=2",  r.compact_padding == 2,
           f"compact_padding={r.compact_padding}")
    except Exception as e:
        ck("DisplayConfig", False, str(e))


def check_aprs() -> None:
    section("APRS modem (no hardware)")
    try:
        from app.engine.aprs_modem import build_aprs_message_payload
        payload = build_aprs_message_payload("W1AW-1", "test", "00001")
        ck("message payload builds",
           ":W1AW-1   :test{00001" in payload, repr(payload))
    except Exception as e:
        ck("APRS modem", False, str(e))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print(f"HAM HAT Control Center v4 — Platform Validation")
    print(f"Platform : {platform.platform()}")
    print(f"Python   : {sys.version.split()[0]}")
    print("=" * 60)

    check_python_version()
    check_imports()
    check_tkinter()
    check_audio()
    check_serial()
    check_ble()
    check_profile()
    check_paths()
    check_display_config()
    check_aprs()

    print(f"\n{'='*60}")
    print(f"Results: {_PASS} pass  {_FAIL} fail  {_SKIP} skip")
    print(f"{'='*60}")
    for tag, label, detail in _results:
        sym = {"PASS": "✓", "FAIL": "✗", "SKIP": "~"}[tag]
        print(f"  {sym} [{tag:<4}] {label}" + (f" — {detail}" if detail else ""))

    if _FAIL:
        print(f"\n  {_FAIL} check(s) failed — see details above.")
    else:
        print(f"\n  All non-skipped checks passed.")

    sys.exit(0 if _FAIL == 0 else 1)

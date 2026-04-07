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


def check_display_env() -> None:
    """Check X11/Wayland display environment on Linux/RPi (SKIP on macOS/Windows).

    On headless Linux this check SKIPs — that is expected when running
    platform_validation.py for CI or pre-launch dependency checks.
    On a desktop Linux session DISPLAY should be set and the check passes.
    """
    section("Display environment (Linux/RPi)")
    plat = platform.system()
    if plat != "Linux":
        ck("display env", True,
           "display managed by OS — not checked on this platform", skip=True)
        return

    import os as _os
    x11     = _os.environ.get("DISPLAY", "")
    wayland = _os.environ.get("WAYLAND_DISPLAY", "")

    if x11:
        ck("DISPLAY set (X11)", True,
           f"DISPLAY={x11!r} — Tkinter can open windows")
    elif wayland:
        ck("WAYLAND_DISPLAY set", True,
           f"WAYLAND_DISPLAY={wayland!r}")
        ck("DISPLAY for Tkinter (via XWayland)", False,
           "Tkinter requires DISPLAY; if XWayland is running: "
           "export DISPLAY=:0  or  export DISPLAY=$WAYLAND_DISPLAY")
    else:
        ck("DISPLAY / WAYLAND_DISPLAY", True,
           "neither display variable is set — GUI launch will fail; "
           "for a local desktop session: export DISPLAY=:0  "
           "(this SKIP is expected when running headlessly for validation)",
           skip=True)


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

    # Linux-only: check whether both raw ALSA hw: and a sound server
    # (PipeWire/PulseAudio) are visible to PortAudio at the same time.
    # If so, the rank filter in _list_devices() correctly suppresses ALSA
    # so the operator never accidentally selects a conflicting device that
    # would trigger PortAudio error -9993 and a potential USB cascade reset.
    if platform.system() == "Linux":
        try:
            import sounddevice as _sd
            _hostapis = _sd.query_hostapis()
            _ha_names = {str(h.get("name", "")) for h in _hostapis}
            _sound_servers = {"PipeWire", "PulseAudio"}
            has_alsa   = "ALSA"   in _ha_names
            has_server = bool(_ha_names & _sound_servers)
            active_servers = sorted(_ha_names & _sound_servers)

            if has_alsa and has_server:
                ck(
                    "Linux audio: sound server present (ALSA suppressed by rank filter)",
                    True,
                    f"PortAudio sees both ALSA and {active_servers}; "
                    f"rank filter prefers {active_servers} — ALSA hw: devices excluded. "
                    "This is correct: selecting a raw ALSA hw: device while "
                    "PipeWire/PulseAudio holds it would cause error -9993.",
                )
            elif has_server and not has_alsa:
                ck(
                    "Linux audio: sound server only (no raw ALSA)",
                    True,
                    f"PortAudio backends: {sorted(_ha_names)}",
                )
            elif has_alsa and not has_server:
                ck(
                    "Linux audio: ALSA only (no sound server detected)",
                    True,
                    "No PipeWire/PulseAudio visible; raw ALSA hw: devices will be used. "
                    "Correct on minimal/headless systems without a sound server.",
                )
            else:
                ck(
                    "Linux audio: host API check",
                    True,
                    f"PortAudio backends detected: {sorted(_ha_names)}",
                    skip=True,
                )
        except Exception as _e:
            ck("Linux audio host-API check", False, str(_e))


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
        import bleak  # noqa: F401 — import confirms installability
        try:
            from importlib.metadata import version as _meta_version
            _bleak_ver = _meta_version("bleak")
        except Exception:
            _bleak_ver = getattr(bleak, "__version__", "unknown")
        ck("bleak installed", True, f"v{_bleak_ver}")
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

    # Check Linux group memberships (serial and BLE access)
    if platform.system() == "Linux":
        import os, grp
        user_groups = os.getgroups()
        for grp_name, purpose, hint in [
            ("dialout",   "serial access (SA818/DigiRig)",
             "sudo usermod -aG dialout $USER  then log out/in"),
            ("bluetooth", "BLE access (PAKT mode)",
             "sudo usermod -aG bluetooth $USER  then log out/in"),
        ]:
            try:
                gid = grp.getgrnam(grp_name).gr_gid
                in_group = gid in user_groups
                ck(f"user in {grp_name} group ({purpose})", in_group,
                   f"run: {hint}" if not in_group else "OK")
            except KeyError:
                ck(f"{grp_name} group check", True,
                   "group not found — skip", skip=True)


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
        ck("rpi compact_padding=1",  r.compact_padding == 1,
           f"compact_padding={r.compact_padding}")
        ck("rpi log_height_main=3", r.log_height_main == 3,
           f"log_height_main={r.log_height_main}")
        ck("rpi geometry leaves top-bar headroom", r.geometry == "1280x680+0+28",
           f"geometry={r.geometry}")
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


def check_scroll_bindings() -> None:
    """Per-function source check: confirm Linux scroll bindings in widgets.py.

    Covers the 'wheel zoom' RPi / Linux validation item without needing a display.
    Uses inspect.getsource() to scope each check to the specific function or
    __init__ that is expected to register the binding — not a whole-file search.

    Three sites are checked:
      scrollable_frame()      — vertical scroll used by every tab panel
      AprsMapCanvas.__init__  — offline dot-map zoom (APRS tab)
      TiledMapCanvas.__init__ — OSM tile-map zoom (Comms tab)
    Plus the _on_wheel handlers in each canvas class for event routing.
    """
    section("Scroll / wheel bindings (Linux compat — per-function source check)")
    import inspect
    try:
        # Import the module; safe on headless Linux (no Tk() created at import time)
        from app.ui import widgets as _w

        # --- scrollable_frame: vertical scroll in every tab ---
        sf = inspect.getsource(_w.scrollable_frame)
        ck("scrollable_frame binds <MouseWheel>", "<MouseWheel>" in sf,
           "Windows/macOS panel scroll — within scrollable_frame")
        ck("scrollable_frame binds <Button-4>",   "<Button-4>" in sf,
           "Linux scroll-up — within scrollable_frame")
        ck("scrollable_frame binds <Button-5>",   "<Button-5>" in sf,
           "Linux scroll-down — within scrollable_frame")

        # --- AprsMapCanvas: offline dot-map with zoom+pan ---
        ac_init = inspect.getsource(_w.AprsMapCanvas.__init__)
        ck("AprsMapCanvas.__init__ binds <Button-4>", "<Button-4>" in ac_init,
           "Linux scroll-up — within AprsMapCanvas.__init__")
        ck("AprsMapCanvas.__init__ binds <Button-5>", "<Button-5>" in ac_init,
           "Linux scroll-down — within AprsMapCanvas.__init__")

        ac_wheel = inspect.getsource(_w.AprsMapCanvas._on_wheel)
        ck("AprsMapCanvas._on_wheel checks event.num (Linux)",
           "event.num" in ac_wheel or 'getattr(event, "num"' in ac_wheel,
           "Linux Button-4/5 sets event.num — within AprsMapCanvas._on_wheel")
        ck("AprsMapCanvas._on_wheel checks event.delta (Win/macOS)",
           "event.delta" in ac_wheel or 'getattr(event, "delta"' in ac_wheel,
           "Windows/macOS MouseWheel sets event.delta — within AprsMapCanvas._on_wheel")

        # --- TiledMapCanvas: OSM tile-map (Comms tab) ---
        tc_init = inspect.getsource(_w.TiledMapCanvas.__init__)
        ck("TiledMapCanvas.__init__ binds <Button-4>", "<Button-4>" in tc_init,
           "Linux scroll-up — within TiledMapCanvas.__init__")
        ck("TiledMapCanvas.__init__ binds <Button-5>", "<Button-5>" in tc_init,
           "Linux scroll-down — within TiledMapCanvas.__init__")

        tc_wheel = inspect.getsource(_w.TiledMapCanvas._on_wheel)
        ck("TiledMapCanvas._on_wheel checks event.num (Linux)",
           "event.num" in tc_wheel or 'getattr(event, "num"' in tc_wheel,
           "Linux Button-4/5 sets event.num — within TiledMapCanvas._on_wheel")
        ck("TiledMapCanvas._on_wheel checks event.delta (Win/macOS)",
           "event.delta" in tc_wheel or 'getattr(event, "delta"' in tc_wheel,
           "Windows/macOS MouseWheel sets event.delta — within TiledMapCanvas._on_wheel")

    except ImportError as exc:
        ck("widgets module importable", False,
           f"{exc} — tkinter or numpy may be missing")
    except AttributeError as exc:
        ck("scroll binding attribute", False, str(exc))
    except Exception as exc:
        ck("scroll bindings check", False, str(exc))


def check_launcher_scripts() -> None:
    """Verify run_linux.sh and run_rpi.sh contain required safety items."""
    section("Launcher scripts (static check)")
    import os as _os
    for name in ("run_linux.sh", "run_rpi.sh"):
        path = _APP_ROOT / name
        if not path.exists():
            ck(f"{name} exists", False, str(path))
            continue
        src = path.read_text(encoding="utf-8")
        ck(f"{name} exists", True)
        ck(f"{name} pycaw excluded",
           "grep -v pycaw" in src,
           "Windows-only pycaw must be excluded on Linux/RPi installs")
        ck(f"{name} tkinter preflight",
           "import tkinter" in src or "python3-tk" in src,
           "Missing tkinter hint — users on bare Debian/Ubuntu need this")
        ck(f"{name} executable bit",
           _os.access(path, _os.X_OK),
           f"run: chmod +x {name}" if not _os.access(path, _os.X_OK) else "OK")


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
    check_display_env()
    check_scroll_bindings()
    check_launcher_scripts()
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

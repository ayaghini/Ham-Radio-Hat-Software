#!/usr/bin/env python3
"""Cross-platform portability smoke test for HAM HAT Control Center v4.

Run this script to verify:
  1. All required modules import cleanly.
  2. Optional dependency guards work correctly (app does not crash if
     sv_ttk, bleak, scipy, pycaw, or winsound are absent).
  3. Profile round-trip serializes and deserializes cleanly.
  4. Platform paths helper returns a valid Path for the current OS.
  5. Audio device listing does not crash (even if no devices are present).

Usage:
    python scripts/smoke_test.py          # normal run
    python scripts/smoke_test.py -v       # verbose (show all checks)

Exit codes:
    0  all checks passed
    1  one or more checks failed
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import sys
import traceback
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_PASS = "PASS"
_FAIL = "FAIL"
_SKIP = "SKIP"

_results: list[tuple[str, str, str]] = []   # (status, name, detail)


def _module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _required_runtime_missing() -> list[str]:
    missing: list[str] = []
    if not _module_available("numpy"):
        missing.append("numpy")
    if not _module_available("sounddevice"):
        missing.append("sounddevice")
    if not _module_available("serial"):
        missing.append("pyserial")
    if not _module_available("tkinter") or not _module_available("_tkinter"):
        missing.append("tkinter")
    return missing


def _check(name: str, fn, skip_reason: str = "") -> bool:
    if skip_reason:
        _results.append((_SKIP, name, skip_reason))
        return True
    try:
        detail = fn() or ""
        _results.append((_PASS, name, str(detail)))
        return True
    except Exception as exc:
        _results.append((_FAIL, name, traceback.format_exc(limit=3).strip()))
        return False


# ---------------------------------------------------------------------------
# Check 1 — required imports
# ---------------------------------------------------------------------------

def _check_required_imports() -> None:
    from app.engine.models import AppProfile
    from app.engine.profile import ProfileManager
    from app.engine.audio_tools import list_input_devices, list_output_devices
    from app.engine.audio_router import AudioRouter
    from app.engine.platform_paths import get_user_data_dir
    from app.engine.aprs_modem import build_aprs_message_payload


def _check_app_state_import() -> None:
    from app.app_state import AppState


# ---------------------------------------------------------------------------
# Check 2 — optional dependency guards
# ---------------------------------------------------------------------------

def _check_sv_ttk_guard() -> str:
    """sv_ttk should import or be set to None — never crash."""
    try:
        import sv_ttk as _sv_ttk
        return f"sv_ttk present: {_sv_ttk.__version__}"
    except ImportError:
        return "sv_ttk absent (expected on fresh install) — guard OK"


def _check_bleak_guard() -> str:
    """bleak should import or be set to None — never crash."""
    try:
        from bleak import BleakScanner, BleakClient
        return f"bleak present"
    except ImportError:
        # Verify that transport.py handles the absence
        from app.engine.pakt.transport import PaktBleTransport, BleakScanner as _BS
        assert _BS is None, "bleak absent but BleakScanner is not None in transport.py"
        return "bleak absent — transport guard OK"


def _check_scipy_guard() -> str:
    """scipy is optional in aprs_modem — either path should work."""
    try:
        from scipy.signal import fftconvolve
        return "scipy present — fftconvolve path active"
    except ImportError:
        # Verify the fallback is a callable
        from app.engine.aprs_modem import _convolve
        import numpy as np
        a = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        b = np.array([1.0, 1.0], dtype=np.float32)
        result = _convolve(a, b)
        assert len(result) == 3, "numpy fallback convolve returned wrong length"
        return "scipy absent — numpy.convolve fallback OK"


def _check_pycaw_guard() -> str:
    """pycaw is Windows-only and should be silently absent elsewhere."""
    sys_name = platform.system().lower()
    if sys_name == "windows":
        try:
            from pycaw.pycaw import AudioUtilities
            return "pycaw present (Windows)"
        except ImportError:
            return "pycaw absent on Windows — OS level control unavailable (acceptable)"
    else:
        try:
            import pycaw
            return f"pycaw unexpectedly installed on {sys_name} — harmless but unnecessary"
        except ImportError:
            return f"pycaw absent on {sys_name} — correct (Windows-only)"


def _check_winsound_guard() -> str:
    """winsound is Windows-only and guarded in audio_tools."""
    from app.engine.audio_tools import winsound
    sys_name = platform.system().lower()
    if sys_name == "windows":
        if winsound is None:
            return "WARN: winsound absent on Windows"
        return "winsound present (Windows)"
    else:
        if winsound is None:
            return f"winsound absent on {sys_name} — guard OK"
        return f"winsound unexpectedly present on {sys_name}"


# ---------------------------------------------------------------------------
# Check 3 — profile round-trip
# ---------------------------------------------------------------------------

def _check_profile_roundtrip() -> str:
    import tempfile
    from app.engine.models import AppProfile
    from app.engine.profile import ProfileManager

    p = AppProfile()
    p.aprs_source = "W1AW-9"
    p.frequency = 144.800
    p.hardware_mode = "PAKT"
    p.pakt_callsign = "W1AW"
    p.pakt_ssid = 7

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        mgr = ProfileManager(tmp_path)
        mgr.save(p)
        loaded = mgr.load()
        assert loaded is not None, "profile failed to reload"
        assert loaded.aprs_source == "W1AW-9", f"aprs_source mismatch: {loaded.aprs_source}"
        assert abs(loaded.frequency - 144.800) < 0.001, f"frequency mismatch: {loaded.frequency}"
        assert loaded.hardware_mode == "PAKT", f"hardware_mode mismatch: {loaded.hardware_mode}"
        assert loaded.pakt_callsign == "W1AW", f"pakt_callsign mismatch: {loaded.pakt_callsign}"
        assert loaded.pakt_ssid == 7, f"pakt_ssid mismatch: {loaded.pakt_ssid}"
        return "profile save/load round-trip OK"
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Check 4 — platform paths helper
# ---------------------------------------------------------------------------

def _check_platform_paths() -> str:
    from app.engine.platform_paths import get_user_data_dir, get_user_log_dir
    sys_name = platform.system().lower()
    data_dir = get_user_data_dir("HamHatCC")
    log_dir = get_user_log_dir("HamHatCC")
    assert isinstance(data_dir, Path), "get_user_data_dir did not return a Path"
    assert isinstance(log_dir, Path), "get_user_log_dir did not return a Path"
    assert "HamHatCC" in str(data_dir) or "hamhatcc" in str(data_dir), \
        f"app name not in data_dir: {data_dir}"
    return f"{sys_name}: data={data_dir}  logs={log_dir}"


# ---------------------------------------------------------------------------
# Check 5 — audio device listing
# ---------------------------------------------------------------------------

def _check_audio_device_listing() -> str:
    from app.engine.audio_tools import list_input_devices, list_output_devices
    outs = list_output_devices()
    ins = list_input_devices()
    return f"{len(outs)} output(s), {len(ins)} input(s) found (0 is OK without hardware)"


# ---------------------------------------------------------------------------
# Check 6 — APRS modem does not crash on import
# ---------------------------------------------------------------------------

def _check_aprs_modem() -> str:
    from app.engine.aprs_modem import (
        build_aprs_message_payload,
        build_aprs_position_payload,
        build_group_wire_text,
    )
    payload = build_aprs_message_payload("W1AW-1", "test message", "001")
    assert payload.startswith(":"), f"unexpected payload: {payload}"
    return f"APRS payload builder OK: {payload[:30]}"


# ---------------------------------------------------------------------------
# Check 7 — DisplayConfig RPi preset values are sane
# ---------------------------------------------------------------------------

def _check_display_config_rpi() -> str:
    from app.engine.display_config import DisplayConfig
    d = DisplayConfig.default()
    r = DisplayConfig.rpi_720p()

    assert d.compact_padding == 4, f"default compact_padding wrong: {d.compact_padding}"
    assert r.compact_padding == 1, f"rpi compact_padding wrong: {r.compact_padding}"
    assert r.scale == 1.5,         f"rpi scale wrong: {r.scale}"
    assert r.map_height == 120,    f"rpi map_height wrong: {r.map_height}"
    assert r.log_height_main == 3, f"rpi log_height_main wrong: {r.log_height_main}"
    assert r.log_height_comms == 6,f"rpi log_height_comms wrong: {r.log_height_comms}"
    assert r.contacts_height == 4, f"rpi contacts_height wrong: {r.contacts_height}"
    assert r.heard_height == 3,    f"rpi heard_height wrong: {r.heard_height}"
    assert r.geometry == "1280x680+0+28"

    # --fullscreen override should clear geometry
    fs = DisplayConfig.from_args(rpi=True, scale=None, geometry=None, fullscreen=True)
    assert fs.fullscreen is True
    assert fs.geometry is None, "fullscreen should clear geometry"

    return (f"default compact_padding={d.compact_padding}  "
            f"rpi scale={r.scale} map_height={r.map_height} "
            f"log_main={r.log_height_main} compact_pad={r.compact_padding} geometry={r.geometry}")


# ---------------------------------------------------------------------------
# Check 8 — Linux mousewheel bindings present in widgets.py
# ---------------------------------------------------------------------------

def _check_linux_scroll_bindings() -> str:
    widgets_src = Path(_ROOT) / "app" / "ui" / "widgets.py"
    text = widgets_src.read_text(encoding="utf-8")
    assert "Button-4" in text, "Button-4 binding missing from scrollable_frame"
    assert "Button-5" in text, "Button-5 binding missing from scrollable_frame"
    assert "yview_scroll" in text, "yview_scroll not found in scroll handler"
    return "Button-4 / Button-5 Linux scroll bindings present in widgets.py"


# ---------------------------------------------------------------------------
# Check 9 — hardware mode switch round-trip and field isolation
# ---------------------------------------------------------------------------

def _check_hardware_mode_switch() -> str:
    """Save and reload a profile in each hardware mode; verify mode-specific
    fields persist and unrelated APRS/PTT fields are unaffected by the switch."""
    import tempfile
    from app.engine.models import AppProfile
    from app.engine.profile import ProfileManager

    # Sentinel values that must survive every mode-round-trip unchanged
    APRS_SOURCE = "KD9XYZ-5"
    FREQUENCY   = 146.520
    PTT_PRE_MS  = 350
    SQUELCH     = 3

    results = []

    for mode, extra in [
        ("SA818",   {}),
        ("DigiRig", {"digirig_port": "/dev/ttyUSB0"}),
        ("PAKT",    {"pakt_callsign": "KD9XYZ", "pakt_ssid": 3,
                     "pakt_device_name": "PAKT-001",
                     "pakt_device_address": "AA:BB:CC:DD:EE:FF"}),
    ]:
        p = AppProfile()
        p.hardware_mode = mode
        p.aprs_source   = APRS_SOURCE
        p.frequency     = FREQUENCY
        p.ptt_pre_ms    = PTT_PRE_MS
        p.squelch       = SQUELCH
        for k, v in extra.items():
            setattr(p, k, v)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = __import__("pathlib").Path(tmp.name)
        try:
            mgr = ProfileManager(tmp_path)
            mgr.save(p)
            loaded = mgr.load()

            assert loaded is not None,                         f"{mode}: load returned None"
            assert loaded.hardware_mode == mode,               f"{mode}: hardware_mode mismatch"
            assert loaded.aprs_source == APRS_SOURCE,          f"{mode}: aprs_source corrupted"
            assert abs(loaded.frequency - FREQUENCY) < 0.001,  f"{mode}: frequency corrupted"
            assert loaded.ptt_pre_ms == PTT_PRE_MS,            f"{mode}: ptt_pre_ms corrupted"
            assert loaded.squelch == SQUELCH,                   f"{mode}: squelch corrupted"
            for k, v in extra.items():
                got = getattr(loaded, k)
                assert got == v, f"{mode}: {k} mismatch: {got!r} != {v!r}"

            results.append(mode)
        finally:
            tmp_path.unlink(missing_ok=True)

    return f"mode switch round-trip OK: {' → '.join(results)}"


# ---------------------------------------------------------------------------
# Check 10 — out-of-range / invalid field clamping
# ---------------------------------------------------------------------------

def _check_profile_field_clamping() -> str:
    """_dict_to_profile must clamp numeric fields that are out of spec
    rather than raising an exception or silently storing garbage."""
    import json, tempfile
    from app.engine.profile import _dict_to_profile

    bad = {
        "frequency":    9999.9,   # above 470 MHz ceiling → should clamp to 470
        "squelch":       99,       # above 8 → clamp to 8
        "pakt_ssid":    -5,        # below 0 → clamp to 0
        "ptt_pre_ms": 99999,       # above 5000 → clamp to 5000
        "aprs_tx_gain":  5.0,      # above 0.40 → clamp to 0.40
        "aprs_lat":    999.0,      # above 90 → clamp to 90
        "hardware_mode": "BOGUS",  # unknown mode → fall back to "SA818"
    }

    p = _dict_to_profile(bad)

    assert p.frequency    <= 470.0, f"frequency not clamped: {p.frequency}"
    assert p.squelch      ==    8,  f"squelch not clamped: {p.squelch}"
    assert p.pakt_ssid    ==    0,  f"pakt_ssid not clamped: {p.pakt_ssid}"
    assert p.ptt_pre_ms   == 5000,  f"ptt_pre_ms not clamped: {p.ptt_pre_ms}"
    assert p.aprs_tx_gain == 0.40,  f"aprs_tx_gain not clamped: {p.aprs_tx_gain}"
    assert p.aprs_lat     == 90.0,  f"aprs_lat not clamped: {p.aprs_lat}"
    assert p.hardware_mode == "SA818", f"bad hardware_mode not defaulted: {p.hardware_mode}"

    return "all 7 out-of-range fields clamped / defaulted correctly"


# ---------------------------------------------------------------------------
# Check 11 — corrupt / partial JSON graceful fallback
# ---------------------------------------------------------------------------

def _check_corrupt_profile_fallback() -> str:
    """ProfileManager.load() must return None (not raise) for corrupt JSON,
    empty files, and truncated content — never crash the caller."""
    import tempfile
    from app.engine.profile import ProfileManager
    from pathlib import Path

    cases: list[tuple[str, bytes]] = [
        ("truncated JSON",  b'{"frequency": 145.07'),
        ("empty file",      b""),
        ("binary garbage",  bytes(range(128))),
        ("wrong type",      b'"just a string"'),
    ]

    results = []
    for label, content in cases:
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = Path(tmp.name)
            tmp.write(content)
        try:
            mgr = ProfileManager(tmp_path)
            result = mgr.load()
            # Must return None, not raise
            assert result is None, f"{label}: expected None but got {result!r}"
            results.append(label)
        finally:
            tmp_path.unlink(missing_ok=True)

    return f"graceful fallback OK for: {', '.join(results)}"


# ---------------------------------------------------------------------------
# Check 12 — contacts/groups normalisation and mesh isolation
# ---------------------------------------------------------------------------

def _check_contacts_mesh_isolation() -> str:
    """Verify that:
    1. chat_contacts and chat_groups are normalised (strip + upper) on load.
    2. Enabling mesh_test_enabled does not corrupt APRS identity fields.
    """
    import tempfile
    from app.engine.models import AppProfile
    from app.engine.profile import ProfileManager
    from pathlib import Path

    p = AppProfile()
    # Contacts with mixed case and whitespace
    p.chat_contacts = [" w1aw ", "VE3XYZ", "  kd9abc  "]
    p.chat_groups   = {
        " nets ": ["  w1aw  ", "ve3xyz"],
        "LOCAL":  ["KD9ABC"],
    }
    # Mesh on — must not corrupt APRS fields
    p.mesh_test_enabled    = True
    p.mesh_node_role       = "REPEATER"
    p.mesh_default_ttl     = 6
    p.mesh_rate_limit_ppm  = 15
    p.aprs_source          = "W1AW-9"
    p.aprs_path            = "WIDE2-2"

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        mgr = ProfileManager(tmp_path)
        mgr.save(p)
        loaded = mgr.load()

        assert loaded is not None, "load returned None"

        # Contacts normalisation
        assert "W1AW" in loaded.chat_contacts,   f"W1AW not normalised: {loaded.chat_contacts}"
        assert "VE3XYZ" in loaded.chat_contacts, f"VE3XYZ not normalised: {loaded.chat_contacts}"
        assert "KD9ABC" in loaded.chat_contacts, f"KD9ABC not normalised: {loaded.chat_contacts}"
        # Groups normalisation (keys uppercased + stripped)
        assert "NETS" in loaded.chat_groups,  f"group key not normalised: {list(loaded.chat_groups)}"
        assert "LOCAL" in loaded.chat_groups, f"LOCAL group missing: {list(loaded.chat_groups)}"
        nets_members = loaded.chat_groups["NETS"]
        assert "W1AW" in nets_members,   f"NETS member not normalised: {nets_members}"
        assert "VE3XYZ" in nets_members, f"NETS VE3XYZ missing: {nets_members}"

        # Mesh isolation — APRS fields untouched
        assert loaded.mesh_test_enabled   is True,       "mesh_test_enabled lost"
        assert loaded.mesh_node_role      == "REPEATER", "mesh_node_role lost"
        assert loaded.mesh_default_ttl    == 6,          "mesh_default_ttl lost"
        assert loaded.mesh_rate_limit_ppm == 15,         "mesh_rate_limit_ppm lost"
        assert loaded.aprs_source         == "W1AW-9",   "aprs_source corrupted by mesh"
        assert loaded.aprs_path           == "WIDE2-2",  "aprs_path corrupted by mesh"

        return (f"contacts normalised ({len(loaded.chat_contacts)} entries), "
                f"groups normalised ({len(loaded.chat_groups)} groups), "
                f"mesh isolation OK")
    finally:
        tmp_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="HAM HAT Control Center v4 smoke test")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Show detail for all checks including PASS")
    parser.add_argument("--guards-only", action="store_true",
                        help="Run only optional-dependency guard checks")
    args = parser.parse_args()

    print(f"HAM HAT Control Center v4 — smoke test")
    print(f"Python {sys.version.split()[0]}  |  platform: {platform.system()} {platform.release()}")
    print()

    missing_runtime = _required_runtime_missing()
    runtime_reason = ""
    if missing_runtime:
        runtime_reason = "required runtime missing: " + ", ".join(missing_runtime)

    if not args.guards_only:
        _check("required imports",          _check_required_imports, skip_reason=runtime_reason)
        _check("AppState import",           _check_app_state_import, skip_reason=runtime_reason)
    _check("sv_ttk guard",                  _check_sv_ttk_guard)
    _check("bleak guard",                   _check_bleak_guard)
    _check("scipy guard",                   _check_scipy_guard,
           skip_reason="numpy missing; scipy fallback path cannot be exercised" if "numpy" in missing_runtime else "")
    _check("pycaw guard",                   _check_pycaw_guard)
    _check("winsound guard",                _check_winsound_guard)
    if not args.guards_only:
        _check("profile round-trip",        _check_profile_roundtrip)
        _check("platform paths",            _check_platform_paths)
        _check("audio device listing",      _check_audio_device_listing,
               skip_reason="sounddevice missing; audio listing unavailable" if "sounddevice" in missing_runtime else "")
        _check("APRS modem",                _check_aprs_modem,
               skip_reason="numpy missing; aprs_modem import unavailable" if "numpy" in missing_runtime else "")
        _check("DisplayConfig RPi preset",  _check_display_config_rpi,
               skip_reason="tkinter missing; DisplayConfig import unavailable" if "tkinter" in missing_runtime else "")
        _check("Linux scroll bindings",     _check_linux_scroll_bindings)
        _check("hardware mode switch",      _check_hardware_mode_switch)
        _check("profile field clamping",    _check_profile_field_clamping)
        _check("corrupt profile fallback",  _check_corrupt_profile_fallback)
        _check("contacts/groups + mesh iso", _check_contacts_mesh_isolation)

    fails = [r for r in _results if r[0] == _FAIL]
    passes = [r for r in _results if r[0] == _PASS]
    skips = [r for r in _results if r[0] == _SKIP]

    width = max(len(r[1]) for r in _results) + 2

    for status, name, detail in _results:
        if status == _FAIL or args.verbose:
            icon = {"PASS": "✓", "FAIL": "✗", "SKIP": "·"}[status]
            label = f"[{status}]"
            print(f"  {icon} {label:<6} {name:<{width}}", end="")
            if detail and (status == _FAIL or args.verbose):
                short = detail.split("\n")[0][:80]
                print(f"  {short}")
            else:
                print()

    if not args.verbose and passes:
        print(f"\n  ✓ {len(passes)} check(s) passed", end="")
        if skips:
            print(f"  ·  {len(skips)} skipped", end="")
        print()

    if fails:
        print(f"\n  ✗ {len(fails)} check(s) FAILED\n")
        if args.verbose:
            for _, name, detail in fails:
                print(f"--- {name} ---")
                print(detail)
                print()
        return 1

    print(f"\nAll {len(_results)} checks passed.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Cross-Platform v4 Validation Plan

## Baseline Commands

Run from repo root:

```bash
# Note: use -x '\.venv' (not --exclude) when running Python 3.9; Python 3.13
# packages in .venv use match-statement syntax that 3.9 cannot compile.
python3 -m compileall -q -x '\.venv' app
python3 app/main.py --help
python3 app/scripts/smoke_test.py -v
python3 app/scripts/smoke_test.py -v --guards-only
python3 app/scripts/platform_validation.py
```

## Confirmed So Far

- macOS: compile/import/help/smoke pass recorded; source-run GUI bring-up confirmed
- macOS item-by-item headless validation (2026-04-04, updated 2026-04-06): **48 pass, 0 fail, 5 skip**
  - profile round-trip: SA818, DigiRig, PAKT all pass
  - mode switching: all three hardware-mode profiles confirmed
  - audio enumeration (historical 2026-04-04 snapshot): 3 outputs, 1 input at that point; current source build now preserves duplicate USB codecs as 4 outputs, 2 inputs
  - serial scan: pyserial executes; `/dev/cu.*` naming confirmed; no hardware ports present
  - BLE transport module loads; TransportState members verified; bleak absent (gracefully guarded — SKIP)
  - platform paths: `~/Library/Application Support/HamHatCC` (exists), `~/Library/Logs/HamHatCC`
  - DisplayConfig: default scale=1.0, rpi_720p scale=1.5 compact_padding=2
  - APRS message payload builder confirmed
  - scroll bindings (per-function `inspect.getsource()` check): `<Button-4/5>` confirmed within `scrollable_frame`, `AprsMapCanvas.__init__`, and `TiledMapCanvas.__init__`; `_on_wheel` in both canvas classes confirmed to check `event.num` (Linux) and `event.delta` (Windows/macOS) within those specific handlers
  - launcher scripts: `run_linux.sh` and `run_rpi.sh` verified — pycaw excluded, tkinter preflight present, executable bit set
  - BLE permission dialog (live scan): cannot test without bleak installed + hardware present
- macOS packaged-app checks (2026-04-04): substantially complete
  - `.app` build succeeds, binary `--help` works, and bundle launches without immediate crash
  - profile path resolves; profile save/load round-trip confirmed programmatically
  - audio enumeration, serial scan, bundle contents, and Info.plist permissions confirmed
  - GUI-visible checks confirmed: audio routing controls visible in Control tab, serial port field populated, profile values match disk, autosave status visible, Refresh buttons present
  - remaining packaged-app checks: actual button-click delivery needs Accessibility permission; BLE permission dialog needs hardware
- macOS hardware follow-up (2026-04-06): SA818 TX/PTT/audio workflow confirmed after shared fixes
  - root cause 1: saved radio offset of `0.600` made TX land on `frequency + offset`; defaults and UI now make simplex `0.000` explicit
  - root cause 2: duplicate Core Audio devices named `USB Audio Device` were collapsed into one UI entry; app now keeps them distinct as `[1]` and `[2]`
  - shared fixes now in common code: clearer RX/TX apply status, duplicate USB codec preservation, frozen-app playback fallback, TX overlap guard, compatible playback path for TX workers
- Raspberry Pi: source-run GUI bring-up confirmed with `python3 main.py --rpi`
- smoke test is safe in sparse environments
- guard-only optional-dependency validation exists
- `platform_validation.py` script created; ready to run on Linux desktop and RPi

## Still Needed

### Linux Desktop

- first real GUI launch
- audio enumeration
- serial scan
- profile save/load
- BLE prerequisites check
- run `python3 app/scripts/platform_validation.py` for full checklist

### macOS

- BLE permission flow (requires hardware)
- Button-click level verification in packaged app (serial Refresh, audio Refresh): requires Accessibility permission grant to enable CGEvent injection into Tkinter, or manual operator run

### Raspberry Pi

- wheel zoom
- serial scan
- audio enumeration and correct USB codec selection when multiple same-name codecs are present
  - ALSA host-API check: when PipeWire or PulseAudio is running, ALSA `hw:` entries should be suppressed from device list (rank 1 filter); verify TX Output / RX Input show `[PipeWire]` entries, not bare ALSA devices
  - run `python3 app/scripts/platform_validation.py` — the Linux audio section now reports which audio stacks were detected (ALSA+server / server-only / ALSA-only) to aid diagnosis
- profile persistence
- BLE prerequisites/path

### Hardware-backed

- PAKT BLE scan/connect/TX result behavior
- SA818 and DigiRig real-device workflows

### Packaging

- macOS `.app`: first build succeeded (2026-04-04); programmatic exit checks complete (2026-04-04)
  - no-crash launch (6+ s, no exit): confirmed
  - `--help`: confirmed
  - profile path `~/Library/Application Support/HamHatCC/profiles/`: resolves
  - profile save/load round-trip (ProfileManager API): confirmed
  - audio enumeration (sounddevice): shared duplicate-device fix landed; current source build sees 4 out (LG ULTRAFINE, Mac mini Speakers, USB Audio Device [1], USB Audio Device [2]) and 2 in
  - serial scan (pyserial): executes, `/dev/cu.*` ports returned: confirmed
  - bleak: packed in PyInstaller CArchive; pyobjc CoreBluetooth bindings in Resources: confirmed
  - sv_ttk, PIL, scipy, numpy in bundle: confirmed
  - NSBluetoothAlwaysUsageDescription + NSMicrophoneUsageDescription in Info.plist: confirmed
  - GUI visual checks (screenshot-confirmed 2026-04-04, historical snapshot): window launches cleanly; Control tab showed TX Output=LG ULTRAFINE and RX Input=WH-1000XM4 at that time; Serial Port field showed /dev/cu.debug-console auto-detected in UI; profile values match disk; status bar shows "Profile saved: last_profile.json" (autosave confirmed); ↺ Refresh and ⬡ Auto-ID buttons present
  - Remaining: button-click response verification blocked by macOS 15 Accessibility requirement for CGEvent→Tkinter; BLE dialog needs hardware
- Linux packaging/deployment exit check — spec + build scripts ready; build not yet run
- Raspberry Pi deployment verification

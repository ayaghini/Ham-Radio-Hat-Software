# Ham Radio HAT Software

Desktop control software for the uConsole HAM HAT ecosystem, including SA818 radio control and APRS workflows. Compatible with DigiRig hardware.

![HAM HAT Control Center Screenshot](screenshots/Screenshot%202026-03-05%20104010.png)

## Executive Summary

This repository now centers on [`app`](app), which is the active cross-platform app and the current source of truth for new work.

### Program Snapshot

| Area | Status | Notes |
|---|---|---|
| Core `v4` app | Active | Main desktop app, primary development target |
| `PAKT` hardware mode | Implemented | Native BLE-backed third mode alongside `SA818` and `DigiRig` |
| Whole-app integrity | Stronger | Recent passes fixed mode switching, status routing, startup behavior, and script validation gaps |
| Cross-platform runtime prep | In progress | macOS/Linux/RPi support work is now implemented in the `v4` codebase, with docs and audit trail updated |
| Real hardware validation | In progress | macOS source-run and packaged-app checks are substantially complete; Linux desktop and Raspberry Pi item-by-item validation still remain; BLE live scan still needs hardware |
| Launcher UX parity | Done | `run_mac.command`, `run_linux.sh`, and `run_rpi.sh` added to the active `v4` app; all four platforms now have first-class source launchers |
| Packaging verification | In progress | macOS: first `.app` build plus substantial exit checks complete; Linux build not yet run |
| **Android expansion** | **Phase 2 complete** | Full Kivy/KivyMD app in `app/android/`; SA818 AT commands, APRS TX/RX modem, PAKT mesh bridge, Android foreground service; all smoke tests pass |

### Progress View

```text
v4 app integrity            [##########] 100%
PAKT integration            [#########-]  90%
Cross-platform code prep    [##########] 100%
Smoke / CI coverage         [#######---]  70%
Real-device validation      [####------]  40%
Packaging verification      [#######---]  70%
Android Phase 1 (skeleton)  [##########] 100%
Android Phase 2 (hardware)  [########--]  80%
```

### What Changed Recently

- stabilized `v4` as the main app and central handoff target
- integrated `PAKT` as a first-class hardware mode in the desktop app
- improved mode switching, startup behavior, diagnostics, and optional dependency handling
- implemented cross-platform prep in the `v4` codebase for macOS, Linux, and Raspberry Pi
- fixed the biggest preflight portability blockers:
  - legacy profile migration into the new user-data location
  - PAKT config cache migration out of the install tree
  - Windows worker capture temp audio migration out of the install tree
  - Linux/RPi map wheel support
  - safer sparse-environment smoke behavior plus guard-only CI coverage

### Current Focus

The next useful session should start with:

1. **Android Phase 3** — first `buildozer android debug` APK build on Linux host; device install and functional validation; signing for release
2. Linux desktop bring-up and `platform_validation.py`
3. Raspberry Pi item-by-item validation
4. macOS packaged-app remaining interaction checks (Accessibility permission + BLE hardware)
5. PAKT BLE hardware validation on real devices
6. Linux packaging/build verification against the documented release checklist

### Best Jump-In Files

| Purpose | File |
|---|---|
| Canonical audit / handoff | [`app/audit_v4.md`](app/audit_v4.md) |
| Cross-platform roadmap | [`cross-platform-v4/roadmap.md`](cross-platform-v4/roadmap.md) |
| Cross-platform task tracker | [`cross-platform-v4/task-board.md`](cross-platform-v4/task-board.md) |
| Validation checklist | [`cross-platform-v4/validation-plan.md`](cross-platform-v4/validation-plan.md) |
| Support boundaries | [`cross-platform-v4/support-matrix.md`](cross-platform-v4/support-matrix.md) |
| Android architecture plan | [`cross-platform-v4/android-plan.md`](cross-platform-v4/android-plan.md) |
| Android app entry point | [`app/android/main.py`](app/android/main.py) |
| Android build script | [`app/android/run_android.sh`](app/android/run_android.sh) |
| PAKT workspace | [`integrations/pakt/`](integrations/pakt/) |

## Repository Layout

- `app` - active cross-platform `v4` app (`VERSION` = `4.0`); current source of truth
- `app/android` - Android Kivy/KivyMD app (Phase 1 complete); buildozer → APK
- `archive/windows-v3` - previous Windows snapshot
- `archive/windows-v1` - early Windows package with its own docs/build scripts
- `archive/pi-legacy` - legacy Raspberry Pi package for SA818 bring-up/control; stale relative to the active `v4` app
- `integrations/pakt` - PAKT integration roadmap, protocol notes, onboarding, fit analysis, and audit trail
- `cross-platform-v4` - cross-platform migration roadmap, task board, validation plan, packaging plan, Android plan, and agent handoff docs

## Hardware Repository

You can find the HAM Radio HAT hardware project here:
- https://github.com/ayaghini/uConsole_HAM_HAT

## What the Software Does

### Windows (`v4`)

- SA818 serial discovery, connect/disconnect, version read, and radio programming
- APRS TX/RX (message TX, reliable ACK/retry mode, one-shot and monitor decode)
- APRS Comms workflows (contacts, groups, heard stations, thread-based chat, `@INTRO`)
- Audio routing tools (device mapping, TX sweep, RX auto-detect helper)
- Offline APRS map plotting
- Profile import/export + autosave
- Hardware mode support:
  - `SA818` mode (full radio control + APRS)
  - `DigiRig` mode (APRS audio/PTT workflows without SA818 AT radio control)
  - `PAKT` mode (native BLE-backed platform with scan/connect, capabilities, config read/write, TX request, TX result handling, telemetry surfacing, and bonded-write error handling)

### Current v4 Integrity Status

Recent integrity and audit work on `v4` included:

- PAKT integration as a third hardware mode
- multiple bug-fix passes on PAKT TX state, scan/device selection, status routing, and Comms integration
- whole-app fixes for footer connection state, hardware-mode switching, startup population of shared UI state, and optional dependency fallback
- improved handling for stale pending PAKT outbound messages
- script validation hardening for selected support/diagnostic scripts
- cross-platform prep fixes for macOS/Linux/RPi startup, path handling, and screen/layout behavior

Known current limitations:

- real PAKT BLE hardware validation is still required for full confidence in scan/connect, bonded writes, TX result sequencing, and live telemetry behavior
- structured PAKT telemetry UI remains basic and is currently surfaced mainly via status/log output
- Linux desktop still has not had a real validation run
- Raspberry Pi bring-up is confirmed, but item-by-item workflow validation is still pending
- macOS packaged-app click-response checks are blocked until Accessibility permission is granted; BLE permission/dialog behavior still needs hardware

### Raspberry Pi

- SA818 serial setup and control UI
- Radio programming (frequency/offset/squelch/bandwidth, CTCSS/DCS, filters, volume)
- Profile save/load
- Third-party bootstrap helper for SA818/SRFRS tooling

## Project Status

- `app` is the current primary app and the recommended starting point for all new work across Windows, macOS, Linux, and Raspberry Pi.
- PAKT integration planning, implementation notes, and audit history are maintained under `integrations/pakt/`.
- Whole-app v4 integrity findings and fixes are tracked in `app/audit_v4.md`.
- A structured cross-platform migration program for macOS, Linux, and Raspberry Pi now exists under `cross-platform-v4/`.
- Legacy software now lives under `archive/`; current portability work happens in `app`, not by extending the old Pi-only package first.
- Source launchers for all four supported OS targets (`run_windows.ps1`, `run_windows.bat`, `run_mac.command`, `run_linux.sh`, `run_rpi.sh`) now live in the active `v4` app directory.

## Quick Start

### Active App (`v4`) by OS

**Windows:**
```powershell
cd app
.\run_windows.ps1
```

Alternative Windows launcher:
```bat
cd app
run_windows.bat
```

**macOS** (double-click in Finder, or run from Terminal):
```bash
cd app
./run_mac.command
```

**Linux desktop:**
```bash
cd app
./run_linux.sh
```

**Raspberry Pi** (1280×720 5-inch display preset):
```bash
cd app
./run_rpi.sh
```

All launchers: create/reuse a local `.venv`, install requirements (excluding the Windows-only `pycaw`), and launch `main.py`. On Linux and Raspberry Pi, `python3-tk` must be installed system-wide before first run (`sudo apt install python3-tk`).

**Android (desktop dev mode):**
```bash
cd app/android
pip install kivy kivymd bleak pyserial plyer
PYTHONPATH=../:./../.. python3 main.py
# or:
./run_android.sh dev
```

**Android (build APK — requires Linux host + Buildozer):**
```bash
pip install buildozer
cd app/android
./run_android.sh debug          # build only
./run_android.sh deploy         # build + install on connected device
./run_android.sh run            # build + install + launch
```

### Legacy Raspberry Pi Package

```bash
cd archive/pi-legacy
chmod +x run_pi.sh
./run_pi.sh
```

Use this only for the old Pi-only package. It is not the primary path for current cross-platform work.

## Requirements

- Windows package: Python 3.10+ (creates local `.venv` on first run)
- Raspberry Pi package: Python 3.9+, `python3-venv`, `python3-tk`, `git`
- USB serial access for radio/PTT control
- Audio input/output devices for APRS workflows
- Additional optional dependencies may be required for specific workflows such as theming, BLE, and diagnostics; recent v4 work has started improving graceful fallback behavior when some optional packages are absent.

## Key Package Docs

- Pi package README: `archive/pi-legacy/README.md`
- Pi quick start: `archive/pi-legacy/QUICK_START.md`
- Windows v1 README: `archive/windows-v1/README.md`
- Windows v4 functional spec: `app/doc/functional-specification.md`
- Windows v4 UI references: `app/doc/ui/`
- Windows v4 whole-app audit: `app/audit_v4.md`
- PAKT integration workspace: `integrations/pakt/`
- Cross-platform migration workspace: `cross-platform-v4/`

## Support

If this project helps you, your support is appreciated.
- Patreon: https://patreon.com/VA7AYG

## Notes

- This repository stores multiple release snapshots; use `app` for current app development and use across all supported OS targets.
- `app` is now the main reference point for current app behavior, integrity work, and future portability planning.
- `archive/pi-legacy` should now be treated strictly as a legacy package kept for historical reference.
- Regulatory and band-plan compliance is the operator's responsibility.

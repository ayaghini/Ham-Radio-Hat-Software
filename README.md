# Ham Radio HAT Software

Desktop control software for the uConsole HAM HAT ecosystem, including SA818 radio control and APRS workflows. Compatible with DigiRig hardware.

![HAM HAT Control Center Screenshot](screenshots/Screenshot%202026-03-05%20104010.png)

## Executive Summary

This repository currently centers on `windows-release/ham_hat_control_center_v4`, which is the active desktop app and the current primary development target.

Recent project work has focused on:

- stabilizing and auditing the v4 app as a whole
- adding `PAKT` as the third supported hardware mode alongside `SA818` and `DigiRig`
- improving whole-app integrity around mode switching, status handling, startup behavior, and optional dependencies
- documenting the current state of the PAKT integration and its remaining hardware-dependent validation gaps
- preparing a structured cross-platform migration program for future macOS, Linux, and Raspberry Pi support

Current high-level status:

- `v4` is the main app and has received the latest fixes and audits
- `PAKT` is integrated as a native BLE-backed third platform in the v4 app
- recent integrity passes improved app behavior, diagnostics, script validation, and dependency fallback behavior
- cross-platform implementation has not started yet, but a full migration roadmap and agent handoff workspace now exist under `cross-platform-v4/`
- Raspberry Pi support exists in `pi-release/`, but it is behind the Windows `v4` app in features and architecture

Important current planning and audit locations:

- PAKT integration docs: `integrations/pakt/`
- v4 whole-app audit: `windows-release/ham_hat_control_center_v4/audit_v4.md`
- cross-platform migration program: `cross-platform-v4/`

## Repository Layout

- `windows-release/ham_hat_control_center_v4` - latest Windows app (`VERSION` = `4.0`)
- `windows-release/ham_hat_control_center_v3` - previous Windows snapshot
- `windows-release/ham_hat_control_center_v1` - early Windows package with its own docs/build scripts
- `pi-release/ham_hat_control_center` - Raspberry Pi package for SA818 bring-up/control
- `integrations/pakt` - PAKT integration roadmap, protocol notes, onboarding, fit analysis, and audit trail
- `cross-platform-v4` - cross-platform migration roadmap, task board, validation plan, packaging plan, and agent handoff docs

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

Known current limitations:

- real PAKT BLE hardware validation is still required for full confidence in scan/connect, bonded writes, TX result sequencing, and live telemetry behavior
- structured PAKT telemetry UI remains basic and is currently surfaced mainly via status/log output
- the cross-platform migration plan is documented, but macOS/Linux/Raspberry Pi parity work has not yet begun in the v4 codebase

### Raspberry Pi

- SA818 serial setup and control UI
- Radio programming (frequency/offset/squelch/bandwidth, CTCSS/DCS, filters, volume)
- Profile save/load
- Third-party bootstrap helper for SA818/SRFRS tooling

## Project Status

- `windows-release/ham_hat_control_center_v4` is the current primary app and the recommended starting point for all new work.
- PAKT integration planning, implementation notes, and audit history are maintained under `integrations/pakt/`.
- Whole-app v4 integrity findings and fixes are tracked in `windows-release/ham_hat_control_center_v4/audit_v4.md`.
- A structured cross-platform migration program for macOS, Linux, and Raspberry Pi now exists under `cross-platform-v4/`.
- Raspberry Pi software is currently behind the Windows `v4` feature set and needs to be updated.

## Quick Start

### Windows (`v4`)

```powershell
cd windows-release/ham_hat_control_center_v4
.\run_windows.ps1
```

Alternative launcher:

```bat
run_windows.bat
```

### Raspberry Pi

```bash
cd pi-release/ham_hat_control_center
chmod +x run_pi.sh
./run_pi.sh
```

## Requirements

- Windows package: Python 3.10+ (creates local `.venv` on first run)
- Raspberry Pi package: Python 3.9+, `python3-venv`, `python3-tk`, `git`
- USB serial access for radio/PTT control
- Audio input/output devices for APRS workflows
- Additional optional dependencies may be required for specific workflows such as theming, BLE, and diagnostics; recent v4 work has started improving graceful fallback behavior when some optional packages are absent.

## Key Package Docs

- Pi package README: `pi-release/ham_hat_control_center/README.md`
- Pi quick start: `pi-release/ham_hat_control_center/QUICK_START.md`
- Windows v1 README: `windows-release/ham_hat_control_center_v1/README.md`
- Windows v4 functional spec: `windows-release/ham_hat_control_center_v4/doc/functional-specification.md`
- Windows v4 UI references: `windows-release/ham_hat_control_center_v4/doc/ui/`
- Windows v4 whole-app audit: `windows-release/ham_hat_control_center_v4/audit_v4.md`
- PAKT integration workspace: `integrations/pakt/`
- Cross-platform migration workspace: `cross-platform-v4/`

## Support

If this project helps you, your support is appreciated.
- Patreon: https://patreon.com/VA7AYG

## Notes

- This repository stores multiple release snapshots; use `windows-release/ham_hat_control_center_v4` for current Windows development/use.
- `windows-release/ham_hat_control_center_v4` is now the main reference point for current app behavior, integrity work, and future portability planning.
- Regulatory and band-plan compliance is the operator's responsibility.

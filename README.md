# Ham Radio HAT Software

Desktop control software for the uConsole HAM HAT ecosystem, including SA818 radio control and APRS workflows. Compatible with DigiRig hardware.

## Repository Layout

- `windows-release/ham_hat_control_center_v4` - latest Windows app (`VERSION` = `4.0`)
- `windows-release/ham_hat_control_center_v3` - previous Windows snapshot
- `windows-release/ham_hat_control_center_v1` - early Windows package with its own docs/build scripts
- `pi-release/ham_hat_control_center` - Raspberry Pi package for SA818 bring-up/control

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

### Raspberry Pi

- SA818 serial setup and control UI
- Radio programming (frequency/offset/squelch/bandwidth, CTCSS/DCS, filters, volume)
- Profile save/load
- Third-party bootstrap helper for SA818/SRFRS tooling

## Project Status

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

## Key Package Docs

- Pi package README: `pi-release/ham_hat_control_center/README.md`
- Pi quick start: `pi-release/ham_hat_control_center/QUICK_START.md`
- Windows v1 README: `windows-release/ham_hat_control_center_v1/README.md`
- Windows v4 functional spec: `windows-release/ham_hat_control_center_v4/doc/functional-specification.md`
- Windows v4 UI references: `windows-release/ham_hat_control_center_v4/doc/ui/`

## Support

If this project helps you, your support is appreciated.
- Patreon: https://patreon.com/VA7AYG?utm_medium=unknown&utm_source=join_link&utm_campaign=creatorshare_creator&utm_content=copyLink

## Notes

- This repository stores multiple release snapshots; use `windows-release/ham_hat_control_center_v4` for current Windows development/use.
- Regulatory and band-plan compliance is the operator's responsibility.

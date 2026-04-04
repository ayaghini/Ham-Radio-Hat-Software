# Cross-Platform v4 Roadmap

Status date: 2026-04-03
Target app: `app`
Program status: code prep complete enough for real validation; packaging builds and hardware-backed BLE validation still remain

## Done

- app-data migration to per-user writable locations
- launcher parity across Windows, macOS, Linux desktop, and Raspberry Pi
- non-Windows UI/runtime fixes for macOS/Linux/RPi startup
- smoke-test hardening and guard-only CI coverage
- repo cleanup: `app/` is canonical, `archive/` holds historical snapshots

## Confirmed Runtime State

- Windows: baseline platform
- macOS: source-run bring-up confirmed
- Raspberry Pi: source-run bring-up confirmed with `--rpi`
- Linux desktop: not yet validated in a real session

## Open Work

### Validation

- Linux desktop bring-up
- macOS item-by-item workflow validation
- Raspberry Pi item-by-item workflow validation

### Hardware

- SA818 serial workflow on macOS/Linux/RPi
- DigiRig workflow on macOS/Linux/RPi
- PAKT BLE runtime behavior and reconnect flow on real hardware

### Packaging

- macOS `.app` build and exit check
- Linux packaging/deployment verification
- Raspberry Pi deployment verification

## Current Blockers

- no real Linux desktop validation yet
- no real PAKT hardware validation yet
- packaging flows are documented but not build-verified

## Immediate Next

1. Run Linux desktop GUI bring-up with `app/run_linux.sh`
2. Run item-by-item macOS validation with `app/run_mac.command`
3. Run item-by-item Raspberry Pi validation with `app/run_rpi.sh`
4. Validate PAKT BLE on hardware
5. Run packaging build/exit checks

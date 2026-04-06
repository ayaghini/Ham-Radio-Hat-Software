# Cross-Platform v4 Roadmap

Status date: 2026-04-05
Target app: `app`
Program status: cross-platform prep is in place; macOS validation is farthest along; Linux desktop, Raspberry Pi workflow validation, and hardware-backed BLE still remain

## Done

- app-data migration to per-user writable locations
- launcher parity across Windows, macOS, Linux desktop, and Raspberry Pi
- non-Windows UI/runtime fixes for macOS/Linux/RPi startup
- smoke-test hardening and guard-only CI coverage
- repo cleanup: `app/` is canonical, `archive/` holds historical snapshots

## Confirmed Runtime State

- Windows: baseline platform
- macOS: source-run bring-up confirmed; packaged-app checks substantially complete
- Raspberry Pi: source-run bring-up confirmed with `--rpi`
- Linux desktop: not yet validated in a real session

## Open Work

### Validation

- Linux desktop bring-up
- Raspberry Pi item-by-item workflow validation
- macOS packaged-app interaction checks requiring Accessibility permission or hardware

### Hardware

- SA818 serial workflow on macOS/Linux/RPi
- DigiRig workflow on macOS/Linux/RPi
- PAKT BLE runtime behavior and reconnect flow on real hardware

### Packaging

- macOS `.app` first build and substantial exit checks completed; remaining interaction/BLE checks still open
- Linux packaging/deployment verification
- Raspberry Pi deployment verification

## Current Blockers

- no real Linux desktop validation yet
- macOS packaged-app button-click verification is blocked by Accessibility permission
- no real PAKT hardware validation yet
- Linux packaging flow is ready but not yet build-verified

## Immediate Next

1. Run Linux desktop GUI bring-up with `app/run_linux.sh`
2. Run item-by-item Raspberry Pi validation with `app/run_rpi.sh`
3. Finish macOS packaged-app interaction checks after granting Accessibility permission; verify BLE dialog when hardware is available
4. Validate PAKT BLE on hardware
5. Run Linux packaging build/exit checks

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
- **Android Phase 1 (2026-04-05):** full Kivy/KivyMD app in `app/android/`; 4 screens, HAL layer, buildozer.spec, responsive phone+tablet layout; engine bridge for code reuse; smoke test passes locally

## Confirmed Runtime State

- Windows: baseline platform
- macOS: source-run bring-up confirmed; packaged-app checks substantially complete
- Raspberry Pi: source-run bring-up confirmed with `--rpi`
- Linux desktop: not yet validated in a real session
- Android: Phase 1 implementation complete; `app/android/` ready for `buildozer android debug` build

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

### Android

- Phase 2 hardware wiring: usbserial4a (SA818/DigiRig USB OTG), real BLE (PaktService), APRS audio modem, GPS
- Phase 2 background service: foreground BLE service for background PAKT receive
- Phase 3: buildozer APK build, device install validation, signing, Play Store prep
- Phase 3: QR-code profile import, offline tile cache, dark/light theme toggle

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
6. Android Phase 2: wire usbserial4a + bleak Android backend; first `buildozer android debug` APK build

# Cross-Platform v4 Support Matrix

Last updated: 2026-04-01 (post-audit refresh)

## Target Platforms

### Windows

Target level: primary baseline

Expected support:

- full current v4 feature set
- existing packaging path maintained
- regression baseline for all other targets

### macOS

Target level: full desktop support

Expected support:

- app startup
- profile management
- UI and mode switching
- serial workflows where supported by device access
- BLE workflows where platform stack allows
- clear packaging and signing story

### Linux Desktop

Target level: full desktop support

Expected support:

- app startup
- profile management
- UI and mode switching
- serial workflows
- BLE workflows where stack and permissions allow
- package/install strategy

### Raspberry Pi OS

Target level: supported deployment target

Expected support:

- app startup
- profile management
- serial workflows
- platform-appropriate UI/runtime expectations
- packaging/install/update path

Special notes:

- treat Raspberry Pi as resource-sensitive
- account for audio, BLE, permissions, and display/headless realities separately from generic Linux desktop

## Capability Matrix

Last updated: 2026-04-01 (static audit + macOS smoke test + follow-up doc/audit sync; no hardware validation performed)

| Capability | Windows | macOS | Linux | Raspberry Pi | Notes |
|---|---|---|---|---|---|
| App startup (import/help) | baseline | passing ✓ | likely-ok | likely-ok | `main.py --help` verified locally; GUI startup still pending outside Windows |
| Profile persistence | baseline | passing ✓ | likely-ok | likely-ok | smoke_test.py covers round-trip and legacy profile migration is now implemented |
| Platform data path | baseline | passing ✓ | likely-ok | likely-ok | profile/audio path helper plus secondary mutable-path cleanup are now implemented; packaged-runtime verification still pending |
| Audio enumeration | baseline | passing ✓ | likely-ok | likely-ok | _list_devices() now handles Core Audio/ALSA/PipeWire; 2 outputs found on macOS |
| Auto USB audio select | baseline | likely-ok | likely-ok | likely-ok | USB keywords extended for macOS/Linux; runtime test pending |
| APRS audio TX | baseline | likely-ok | likely-ok | likely-ok | Subprocess worker cross-platform |
| APRS audio RX | baseline | likely-ok | likely-ok | likely-ok | Direct sounddevice path on non-Windows; Windows worker-temp path now uses writable audio storage |
| OS audio level control | baseline | no-op | no-op | no-op | pycaw Windows-only; guarded; silent no-op elsewhere |
| SA818 serial | baseline | likely-ok | likely-ok | likely-ok | pyserial cross-platform; port names documented (/dev/cu.usbserial-X on macOS) |
| DigiRig | baseline | likely-ok | likely-ok | likely-ok | CP2102 description keywords verified cross-platform |
| PAKT BLE scan | baseline | needs-perm | needs-perm | needs-perm | macOS: TCC Bluetooth permission + Info.plist key; Linux: BlueZ/dbus + bluetooth group |
| TTS announce | baseline | no-op | no-op | no-op | PowerShell TTS Windows-only; guarded |
| Auto-detect RX level | baseline | no-op | no-op | no-op | Explicitly Windows-only guarded |
| Mesh test mode | baseline | likely-ok | likely-ok | likely-ok | Pure Python; no OS coupling |
| Packaging strategy | baseline | documented | documented | documented | packaging flows are documented, but packaging build validation is still pending |
| Packaging runtime path safety | baseline | likely-ok | likely-ok | likely-ok | mutable app data now targets writable locations; packaged-runtime verification is still pending |
| Optional-dependency validation | baseline | improved | improved | improved | guard code exists, sparse envs now skip hard-runtime-dependent checks safely, and guard-only CI coverage exists on non-Windows |

## Support Level Definitions

- **baseline**: Windows; existing release path, full feature validation
- **passing**: confirmed working on this platform on this date by automated test
- **partial**: implemented in code but with known gaps or incomplete migration/validation
- **likely-ok**: cross-platform code path confirmed by static audit and/or unit-level test; full runtime test pending
- **needs-perm**: requires OS permission grant before feature works; will fail silently or with a clear error without it
- **no-op**: feature silently disabled on that platform (acceptable documented behavior)
- **unknown**: not yet evaluated

## Support Policy Rules

- "supported" means boot + core workflow + documented packaging path + known limitations
- "experimental" means runnable but not fully validated
- "unsupported" must fail clearly and be documented

## macOS-Specific Requirements Confirmed This Pass

- Bluetooth: NSBluetoothAlwaysUsageDescription key required in Info.plist for PAKT BLE in a packaged .app
- Profile storage: primary profile/audio path targets `~/Library/Application Support/HamHatCC`, and legacy-profile migration is now implemented
- Serial: ports appear as /dev/cu.usbserial-XXXXXXXX; dialout group not required on macOS (unlike Linux)

## Linux / Raspberry Pi Requirements Confirmed This Pass

- Serial: user must be in `dialout` group: `sudo usermod -aG dialout $USER` + re-login
- BLE: user must be in `bluetooth` group OR a polkit rule must grant access; BlueZ 5.43+ required
- Profile storage: platform_paths.py uses ~/.local/share/hamhatcc (XDG compliant)
- Audio (ALSA): devices appear as host API "ALSA"; PipeWire appears as "PipeWire" — both now rank 0 in _list_devices()
- Follow-up path-migration cleanup is now implemented for the PAKT config cache and Windows worker capture temp path

# Cross-Platform v4 Task Board

Status keys:

- `todo`
- `in_progress`
- `blocked`
- `done`

## Foundation

| ID | Status | Task | Notes / Exit Check |
|---|---|---|---|
| CP-001 | done | Build dependency inventory for v4 | All runtime imports classified — see architecture-plan.md |
| CP-002 | done | Record current startup and smoke baseline | compileall clean, --help green, historical smoke_test.py pass recorded on macOS Darwin 25.4.0 |
| CP-003 | done | Create platform assumption inventory | All seams documented in architecture-plan.md |
| CP-004 | done | Define support policy by target platform | Reflected in support-matrix.md |

## Architecture

| ID | Status | Task | Notes / Exit Check |
|---|---|---|---|
| CP-100 | done | Define serial adapter boundary | Port naming documented in scan_ports() and auto_identify_and_connect(); DigiRig CP2102 description keywords verified cross-platform |
| CP-101 | done | Define audio adapter boundary | `_list_devices()` now ranks Core Audio/ALSA/PipeWire at rank 0; `auto_select_usb_pair()` extended with macOS/Linux USB name keywords |
| CP-102 | done | Define BLE adapter/runtime boundary | macOS TCC + Linux BlueZ requirements documented in transport.py module docstring |
| CP-103 | done | Define app-data and filesystem path helper | `app/engine/platform_paths.py` created with `get_user_data_dir()` and `get_user_log_dir()`; legacy profile migration and secondary mutable-path cleanup now implemented |
| CP-104 | done | Normalize optional dependency handling | All optional deps confirmed guarded: sv_ttk ✓, bleak ✓, scipy ✓, pycaw ✓, winsound ✓, Pillow ✓, requests ✓; verified by smoke_test.py |

## Whole-App Integrity

| ID | Status | Task | Notes / Exit Check |
|---|---|---|---|
| CP-200 | done | Audit hardware-mode switching across all modes | Clean — all three modes use explicit routing; prior passes fixed all stale states |
| CP-201 | done | Audit profile save/load across all modes | Clean — all mode fields explicitly serialized; no cross-mode leakage found |
| CP-202 | done | Audit startup path for platform assumptions | Fixed: startup status message changed from "COM port" to "serial port"; _audio_dir missing attr also fixed |
| CP-203 | in_progress | Audit scripts for portability and argument safety | bootstrap --dev help text updated to note Windows-only pycaw, but canonical audit still tracks open hardening issues in worker/diagnostic/bootstrap scripts |
| CP-204 | done | Audit logging/status surfaces for consistency | Clean — structured log format established in SIP-005; no new inconsistencies found |

## PAKT-Specific Within Cross-Platform Scope

| ID | Status | Task | Notes / Exit Check |
|---|---|---|---|
| CP-300 | done | Define desktop BLE support expectations by OS | macOS (TCC/Bluetooth permission + Info.plist key), Linux (BlueZ/dbus, bluetooth group), Windows (WinRT, no special perms) — all documented in transport.py |
| CP-301 | done | Harden stale-pending PAKT TX policy | Fixed in SIP-001: 2-min timeout, 30s tick |
| CP-302 | done | Improve structured telemetry UX | Fixed in SIP-005 |
| CP-303 | done | Review reconnect/subscription behavior under non-Windows assumptions | Fixed: `_on_disconnect` now uses `call_soon_threadsafe` + `create_task` via a captured loop ref; safe against CoreBluetooth/BlueZ callback threads; hardware validation still deferred |

## Packaging and Release

| ID | Status | Task | Notes / Exit Check |
|---|---|---|---|
| CP-400 | done | Define Windows packaging baseline | PyInstaller `--onefile --windowed` documented in packaging-guide.md; exit check: HamHatCC.exe launches + writes to %APPDATA%\HamHatCC\ |
| CP-401 | done | Define macOS packaging path | PyInstaller .app + NSBluetoothAlwaysUsageDescription plist key + codesign/notarize/staple steps documented; exit check: .app opens + audio/serial scan + data in ~/Library |
| CP-402 | done | Define Linux packaging path | PyInstaller one-file primary; AppImage and .deb noted as alternatives; BlueZ/dialout group requirements documented |
| CP-403 | done | Define Raspberry Pi deployment path | venv install script, launch.sh, autostart, update procedure, and group requirements all documented in packaging-guide.md |

## Verification and CI

| ID | Status | Task | Notes / Exit Check |
|---|---|---|---|
| CP-500 | done | Create platform smoke checklist | `scripts/smoke_test.py` created; historical macOS pass recorded; sparse-environment behavior now skips hard-runtime-dependent checks cleanly |
| CP-501 | done | Add dependency-absence smoke coverage | `smoke_test.py` supports `--guards-only`, sparse env hard-runtime checks skip cleanly, and CI includes a non-Windows guard-only smoke step |
| CP-502 | done | Define CI matrix | `.github/workflows/smoke.yml` created — 3-platform matrix (Windows/macOS/Ubuntu, py3.11); runs compileall + --help + smoke_test.py -v on each |
| CP-503 | done | Add release verification checklist | `cross-platform-v4/release-checklist.md` created — pre-build, per-platform build+verify steps, and final gate |

## Follow-up Audit Findings (2026-04-01)

| ID | Severity | File | Description |
|---|---|---|---|
| CP-AUD-001 | fixed | `app/app_state.py` | Legacy profile migration / fallback implemented |
| CP-AUD-002 | fixed | `app/app.py` | `pakt_config_cache.json` moved to the migrated user-data directory |
| CP-AUD-003 | fixed | `app/engine/audio_router.py` | Windows worker-thread capture temp WAV path moved to the writable audio directory |
| CP-AUD-004 | improved | `scripts/smoke_test.py`, `.github/workflows/smoke.yml` | sparse-environment and optional-dependency validation coverage improved via clean skips and `--guards-only` CI step |

## Bugs Fixed — Pass 2 (2026-04-01)

| ID | Severity | File | Description |
|---|---|---|---|
| AUDIT-001 | Medium | `app/app.py` | `self._audio_dir` never assigned in HamHatApp.__init__ → AttributeError on play_manual_aprs_packet / tx_channel_sweep |
| AUDIT-002 | Low | `scripts/bootstrap_third_party.py` | argparse description said "v2" → fixed to "v4" |
| AUDIT-003 | Low | `app/app.py` | Startup status bar said "COM port" → fixed to "serial port" |
| AUDIT-004 | Low | `scripts/bootstrap_third_party.py` | --dev help text did not indicate pycaw is Windows-only → clarified |

## Code Changes — Pass 2 (2026-04-01)

| File | Change |
|---|---|
| `app/engine/audio_tools.py` | Extended `_list_devices()` host API ranking to include Core Audio (macOS), ALSA, PipeWire (Linux); documented exclusion logic |
| `app/engine/audio_router.py` | Extended `_USB_KW` in `auto_select_usb_pair()` to include "usb audio codec", "usb audio", "usb sound" for macOS/Linux; updated USB token regex; documented per-platform naming |
| `app/engine/platform_paths.py` | New file — `get_user_data_dir()` and `get_user_log_dir()` for cross-platform app data location |
| `app/engine/pakt/transport.py` | Added module-level docstring documenting BLE platform requirements for Windows/macOS/Linux/RPi |
| `app/app.py` | Added `self._audio_dir = self.state.audio_dir`; documented serial port naming in `scan_ports()`; documented DigiRig CP2102 description keywords; fixed startup status message |
| `scripts/bootstrap_third_party.py` | Fixed "v2" → "v4" in description; clarified --dev help text |
| `scripts/smoke_test.py` | New file — 11-check portability smoke test; 11/11 pass on macOS |

## Code Changes — Pass 3 (2026-04-01)

| File | Change |
|---|---|
| `app/app_state.py` | AppState path migration confirmed done — `get_user_data_dir("HamHatCC")` resolves to `~/Library/Application Support/HamHatCC` on macOS; dirs created at startup |
| `app/engine/pakt/transport.py` | CP-303: added `self._loop` captured via `asyncio.get_running_loop()` in `connect()`; `_on_disconnect` now uses `call_soon_threadsafe` + `_create_reconnect_task`; safe for CoreBluetooth/BlueZ callback threads on macOS/Linux |
| planning docs | Marked CP-103 migration, macOS import smoke, and CP-303 complete |

## Bugs Fixed — Pass 3 (2026-04-01)

Path-migration and smoke-validation follow-up items were addressed in the current pass.

## Recommended Execution Order (Next Pass)

1. Run macOS desktop validation: GUI startup, profile save/load, serial scan, audio enumeration, BLE permission flow
2. Run Linux desktop validation: GUI startup, ALSA/PipeWire enumeration, serial scan, BLE prerequisites, profile save/load
3. Run Raspberry Pi validation on the real 5-inch screen: `python3 main.py --rpi`, layout/readability, wheel zoom, serial/audio/BLE checks
4. Validate PAKT BLE on real hardware and watch reconnect behavior
5. Phase 6: run packaging builds and exit checks

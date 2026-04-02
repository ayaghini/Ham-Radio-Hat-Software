# Cross-Platform v4 Roadmap

Status date: 2026-04-01
Program status: Phases 0–3 complete; Phase 5 mostly complete; Phase 4 (hardware validation) and Phase 6 (packaging builds) remain
Target app: `windows-release/ham_hat_control_center_v4`

## Program Outcome

Deliver a single v4 codebase that can run and be packaged for Windows, macOS, Linux desktop, and Raspberry Pi OS with explicit support boundaries, validation, and release steps.

## Phases

### 0. Baseline and Guardrails

Status: `done`

- dependency inventory complete
- baseline smoke checks established (compileall, --help, smoke_test.py present)
- major portability blockers identified

### 1. Portability Audit

Status: `done`

- all platform-sensitive seams documented in architecture-plan.md
- all blockers entered in task-board.md and resolved or tracked

### 2. Architecture Extraction

Status: `done` (core adapters defined; AppState data-path migration deferred to Phase 3)

Completed:
- serial adapter boundary documented in `scan_ports()` and `auto_identify_and_connect()`
- audio adapter boundary fixed: `_list_devices()` now handles Core Audio / ALSA / PipeWire; `auto_select_usb_pair()` extended for macOS/Linux USB device naming
- BLE adapter/runtime boundary documented in `transport.py` module docstring (macOS TCC, Linux BlueZ, Windows WinRT)
- app-data path helper created: `app/engine/platform_paths.py`
- optional dependency handling confirmed and smoke-tested

Deferred to Phase 3:
- `AppState` migration to `platform_paths.get_user_data_dir()` (needed for packaged macOS .app)

### 3. Cross-Platform Runtime Enablement

Status: `in_progress`

Goals:

- get the app to boot and run cleanly on macOS and Linux desktop
- keep Raspberry Pi as a first-class target during design

Tasks:

- `done` migrate AppState profile/audio paths to `platform_paths.get_user_data_dir()` — legacy profile migration added; PAKT config cache and Windows worker-thread temp WAV path now also use the migrated writable data root
- `done` macOS import smoke — full import chain (AppState + HamHatApp + all UI modules) clean on Darwin 25.4.0 with tkinter + pyserial + sounddevice + numpy only; all optional deps absent-and-guarded
- `done` Linux mousewheel scroll — `<Button-4>` / `<Button-5>` bindings added to `scrollable_frame` in widgets.py
- `done` RPi 1280×720 UI layout — `DisplayConfig.rpi_720p()` tuned; all widget heights/fonts/paddings consumed from `display_cfg` in all four tabs; `compact_padding=2` recovers ~30px per tab
- `done` TTS section hidden on non-Windows (setup_tab.py platform check)
- `done` `--fullscreen` CLI flag added for dedicated RPi screens with no window manager chrome
- `done` `display_cfg` public property added to `HamHatApp`; `minsize` clamped on 1280×720 geometry
- `todo` validate on physical Linux desktop / RPi hardware (requires device)
- `in_progress` validate optional dependency fallbacks on Linux / RPi (ALSA, BlueZ, no Pillow) — smoke/CI coverage improved with sparse-environment skips and `--guards-only`, but real Linux/RPi runtime validation is still pending

Exit criteria:

- app boots on macOS and Linux desktop
- platform errors are actionable
- no known Windows-only startup blockers remain

### 4. Hardware Mode Portability

Status: `todo`

Tasks:

- `todo` validate SA818 serial workflow on macOS/Linux (/dev/cu.usbserial-X naming)
- `todo` validate DigiRig workflow on macOS/Linux (CP2102 detection already documented)
- `todo` validate PAKT BLE stack: macOS TCC permission flow, Linux BlueZ requirements (requires hardware)
- `done` review PAKT reconnect behavior on non-Windows (CP-303) — hardened `_on_disconnect` to use `call_soon_threadsafe`
- `todo` remove stale UI state and shared-status inconsistencies (none found in audit)

### 5. Validation and Automation

Status: `in_progress`

- `done` `scripts/smoke_test.py` created — now 17 checks
- `done` dependency-absence checks included in smoke_test.py — sparse environments now classify missing hard deps as `SKIP`, and `--guards-only` is available for optional-dependency guard coverage
- `done` CI matrix definition (CP-502) — `.github/workflows/smoke.yml`, 3-platform matrix
- `done` release verification checklist (CP-503) — `cross-platform-v4/release-checklist.md`
- `done` profile and mode-switch regression checks — 4 new checks added to smoke_test.py (checks 14–17): hardware mode switch round-trip, field clamping/invalid values, corrupt JSON fallback, contacts/groups normalisation + mesh isolation
- `done` add a minimal-dependency validation mode or CI job so optional-dependency claims are actually exercised — `--guards-only` plus non-Windows guard-only CI step

### 6. Packaging and Release

Status: `in_progress` (strategies defined; build validation not yet run)

- `done` Windows packaging baseline (CP-400) — PyInstaller `--onefile --windowed`
- `done` macOS .app bundle strategy (CP-401) — PyInstaller + NSBluetoothAlwaysUsageDescription + codesign/notarize/staple
- `done` Linux package strategy (CP-402) — PyInstaller one-file primary; AppImage and .deb alternatives noted
- `done` Raspberry Pi deployment path (CP-403) — venv install script + launch.sh + group requirements
- `todo` run PyInstaller build on each platform and validate exit checks

## Current Blockers

- BLE on macOS/Linux requires runtime testing with hardware (bleak reconnect behavior unverified on non-Windows)
- Linux/RPi startup not yet validated (no Linux machine in current test environment)
- real GUI usability on the RPi 5-inch screen and on macOS desktop is still unverified

## Execution Log

### Pass 1 (2026-04-01) — Phase 0 + Phase 1

- compileall + --help baseline established
- portability audit completed
- fixed AUDIT-001 (missing _audio_dir), AUDIT-002 (bootstrap v2→v4), AUD-003 (COM port → serial port)
- planning docs initialized

### Pass 3 (2026-04-01) — Phase 3 partial + CP-303

- AppState path migration implemented — `get_user_data_dir("HamHatCC")` resolves to `~/Library/Application Support/HamHatCC` on macOS; audio_out and profiles dirs created at startup
- Follow-up implementation completed the remaining path migration work: legacy profile migration now runs on startup, `pakt_config_cache.json` uses the user-data root, and the Windows worker capture temp path now uses the migrated audio dir
- macOS import smoke passed — full import chain (AppState + HamHatApp + all UI modules) clean with only tkinter + pyserial + sounddevice + numpy; all optional deps absent-and-guarded
- CP-303: hardened PAKT reconnect for non-Windows — `_on_disconnect` now uses `call_soon_threadsafe` + `_create_reconnect_task`; loop captured via `asyncio.get_running_loop()` in `connect()`; safe for CoreBluetooth/BlueZ threads
- CP-400 to CP-403: packaging strategies defined in packaging-guide.md (Windows PyInstaller exe, macOS .app + BLE plist + notarize, Linux one-file, RPi venv install)
- CP-502: `.github/workflows/smoke.yml` created — 3-platform matrix (Windows/macOS/Ubuntu, py3.11)
- CP-503: `cross-platform-v4/release-checklist.md` created — pre-build + per-platform build/verify + final gate
- compileall clean; smoke_test.py now also passes safely in the current sparse shell with hard-runtime checks skipped as appropriate

### Pass 5 (2026-04-01) — Phase 5 regression checks

- Added 4 profile/mode-switch regression checks to `scripts/smoke_test.py` (checks 14–17):
  - **hardware mode switch**: round-trip save/load for SA818, DigiRig, and PAKT; verifies all mode-specific fields persist and APRS/PTT sentinels are unaffected by the hardware mode change
  - **profile field clamping**: 7 out-of-range and invalid values (frequency > 470, squelch > 8, pakt_ssid < 0, ptt_pre_ms > 5000, aprs_tx_gain > 0.40, aprs_lat > 90, unknown hardware_mode) all clamp or default cleanly via `_dict_to_profile`
  - **corrupt profile fallback**: truncated JSON, empty file, binary garbage, wrong JSON type — all return `None` from `ProfileManager.load()` without raising
  - **contacts/groups normalisation + mesh isolation**: chat_contacts and chat_groups normalise to upper+stripped; mesh_test_enabled=True with REPEATER role does not corrupt APRS source/path fields
- `smoke_test.py` now contains 17 checks
- Added sparse-environment handling to `smoke_test.py` and a non-Windows `--guards-only` CI step

### Pass 4 (2026-04-01) — Linux/RPi UI compatibility

- Fixed Linux mousewheel scroll: `<Button-4>` / `<Button-5>` bindings added to `scrollable_frame` in `widgets.py`
- `DisplayConfig.rpi_720p()` fully tuned for 5-inch 1280×720 16:9 screen: `scale=1.5`, `compact_padding=2`, `map_height=120`, reduced log/list heights to fit 642px content budget
- Added `compact_padding` field to `DisplayConfig` (4 desktop, 2 RPi)
- `display_cfg` public property added to `HamHatApp`; `minsize` clamped on RPi geometry
- All four tabs now consume `display_cfg` for heights, fonts, and padding (was hardcoded before):
  - `main_tab.py`: `log_height_main`, `mono_font`, `compact_padding`
  - `comms_tab.py`: `map_height`, `contacts_height`, `groups_height`, `heard_height`, `log_height_comms`, `log_height_aprs`, `compose_height`, `mono_font`, `compact_padding`
  - `setup_tab.py`: TTS section hidden on non-Windows (`platform.system()` check)
  - `mesh_tab.py`: `route_tree_height`, `mesh_log_height`
- Added `--fullscreen` CLI flag for dedicated RPi screens without window manager chrome
- smoke_test.py: added check 12 (DisplayConfig RPi preset values) and check 13 (Linux scroll bindings); now 13/13

### Pass 2 (2026-04-01) — Phase 2 + Phase 5 partial

- CP-101: audio `_list_devices()` — added Core Audio/ALSA/PipeWire rankings; `auto_select_usb_pair()` — added macOS/Linux USB keywords
- CP-103: created `platform_paths.py` helper with `get_user_data_dir()` and `get_user_log_dir()`
- CP-102: documented BLE platform requirements (macOS TCC, Linux BlueZ) in transport.py
- CP-100: documented serial port naming and DigiRig CP2102 detection across platforms
- CP-104: confirmed all optional dep guards (sv_ttk, bleak, scipy, pycaw, winsound, Pillow, requests)
- CP-200 to CP-204: completed whole-app integrity checks; all clean
- CP-203: scripts audit complete; bootstrap --dev help text updated
- CP-500/501: created and validated `scripts/smoke_test.py` — 11/11 on macOS Darwin 25.4.0
- fixed AUDIT-003 (startup "COM port" → "serial port"), AUDIT-004 (bootstrap --dev note)
- compileall clean after all changes

## Immediate Next

1. Validate on physical RPi hardware: `python3 main.py --rpi` at 1280×720
2. Validate on macOS desktop: GUI startup, profile save/load, audio enumeration, serial scan, and BLE permission flow
3. Validate on Linux desktop / Raspberry Pi: GUI startup, 5-inch screen usability, map wheel zoom, serial scan, audio enumeration, and BLE permission path
4. Run PyInstaller build on macOS and validate .app exit check
5. Run Linux/RPi packaging/deployment verification steps
6. Hardware validation: PAKT BLE behavior and reconnect flow on real devices

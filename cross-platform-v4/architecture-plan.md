# Cross-Platform v4 Architecture Plan

## Current Reality

The current v4 app is a desktop-first Tkinter application with mixed responsibilities:

- UI orchestration in `app/app.py`
- hardware and APRS logic in `app/engine/`
- transport-specific details embedded in engine modules
- release structure centered on `windows-release/`

This is workable for migration, but only if OS-sensitive details are isolated instead of spreading further.

## Target Architecture

The target architecture should separate:

1. app orchestration
2. hardware-mode orchestration
3. OS/platform services
4. hardware transports
5. UI

## Required Boundaries

### 1. Platform Services

Introduce explicit service boundaries for:

- serial port enumeration and open/close behavior
- audio device enumeration and selection
- BLE capability detection and connection support
- app-data, cache, and profile paths
- dependency diagnostics

The app should ask for capabilities, not infer them from OS names scattered across the code.

### 2. Hardware Backends

Keep hardware modes explicit:

- SA818 backend
- DigiRig backend
- PAKT backend

Each backend should expose supported actions and reject unsupported ones clearly.

### 3. UI Layer

The UI should:

- bind to state
- call explicit app actions
- avoid direct OS or transport logic
- adapt visibility and enablement based on capabilities and hardware mode

### 4. Packaging Layer

Packaging should be treated as a separate concern with per-platform flows, not embedded assumptions inside runtime code.

## Migration Design Rules

- no new Windows-only assumptions
- no hidden mode fallthrough
- no direct path assumptions for per-user data
- no hard crash on optional dependency absence when a graceful fallback is possible
- platform-specific behavior must be documented and testable

## Platform Assumption Inventory (from first execution pass, 2026-04-01)

### Dependency Portability Classification

| Dependency | Risk | Classification | Notes |
|---|---|---|---|
| pyserial | Low | cross-platform | Port name format differs (COM3 vs /dev/ttyUSB0); no hardcoded port names found |
| bleak | Medium | cross-platform with OS variation | macOS needs CoreBluetooth TCC permission; Linux needs BlueZ + dbus access; Windows uses WinRT; transport code guards import |
| numpy | Low | pure-Python-native | Cross-platform |
| sounddevice | Low | cross-platform | Host API names differ by OS; see audio seam below |
| sv-ttk | Low | cross-platform, optional | Guarded with try/except; falls back to default ttk theme |
| Pillow | Low | cross-platform | |
| requests | Low | cross-platform | |
| scipy | Low | cross-platform, optional | Used for faster APRS FIR convolution; gracefully unused if absent |
| pycaw | High | Windows-only | Used for OS audio level control; guarded with `platform.system() != "windows"` check; silent no-op on non-Windows |
| comtypes | High | Windows-only | Used alongside pycaw; same guard |
| winsound | Medium | Windows-only | Fallback playback path; guarded with `try/except ImportError` in audio_tools.py |

### Serial Seam

- `serial.tools.list_ports.comports()` — cross-platform ✓
- No hardcoded `COM` port names in core app logic ✓
- Status messages say "COM port" — cosmetic, not a code assumption
- DigiRig CP2102 detection uses description string matching; Windows describes it as "CP210x" / "Silicon Labs"; Linux describes it as "cp210x converter"; macOS as "CP2102 USB to UART Bridge"; keywords ("cp210" / "silicon labs") partially match across OS — likely ok but should be tested

### Audio Seam

**`audio_tools._list_devices()` — portability gap**

The function ranks devices by Windows host API names:
- `"Windows WASAPI"` → rank 0 (preferred)
- `"MME"` → rank 1
- `"Windows DirectSound"` → excluded
- anything else → rank 3

On macOS (Core Audio) and Linux (ALSA, PipeWire, JACK):
- No rank-0 or rank-1 devices exist
- All devices fall through to rank 3
- The final filter passes all devices through (no rank-0 → no rank-1 → use all)
- **Result**: device enumeration works but loses WASAPI preference and Windows-specific dedup

**`auto_select_usb_pair()` — broken on macOS/Linux**

USB audio device detection uses Windows MME/WASAPI naming:
- keywords: `"usb audio device"`, `"usb pnp sound device"`, `"digirig"`
- Windows: SA818 codec appears as `"USB Audio Device [n]"` — matches ✓
- macOS: SA818 codec appears as `"USB Audio CODEC"` or manufacturer name — does not match ✗
- Linux (ALSA): appears as `"USB Audio"` or `"hw:CARD=..."` — does not match ✗
- **Result**: auto-select returns `None` on macOS/Linux; user must select manually

**Windows WASAPI thread-affinity workaround**

`capture_compatible()` and `record_compatible()` explicitly check `platform.system() == "windows"` and use subprocess workers on Windows worker threads. On non-Windows, they call `sounddevice` directly. This is correct and cross-platform ✓

**OS audio level control (`_apply_os_rx_level`, `_apply_os_tx_level`)**

Both explicitly check `platform.system().lower() != "windows"` and return immediately on non-Windows. Guarded; silent no-op on macOS/Linux ✓

**`auto_detect_rx()`** — explicit Windows-only guard ✓

### BLE Seam (PAKT)

- `bleak` is installed cross-platform
- `BleakScanner` / `BleakClient` import is guarded with `try/except` in `transport.py` ✓
- Platform-specific behavior not yet documented:
  - **macOS**: `BleakScanner.discover()` requires Bluetooth permission (TCC). First run will prompt; denial silently returns empty list or raises. App bundles need `NSBluetoothAlwaysUsageDescription` in `Info.plist`.
  - **Linux**: BlueZ must be running; user or process must have dbus access to `org.bluez`. Often requires `bluetoothctl` group or a polkit rule. Scanning may require root or `CAP_NET_ADMIN` on some distros.
  - **Windows**: WinRT BLE works without special permissions on modern Windows 10+

### Filesystem and App-Data Seam

Profile path: `app_dir / "profiles" / "last_profile.json"` — relative to app install directory

- On Windows desktop: writable ✓
- On macOS .app bundle: app bundle is typically read-only after signing/notarization — **blocker for packaged deployment**
- On Linux system install: `/usr/...` paths are read-only for non-root — **blocker for packaged deployment**
- On Raspberry Pi: likely writable if installed in home directory ✓

**Recommendation for Phase 2**: add a `platform_paths.py` helper that resolves user-writable app-data using `platformdirs` or manual OS-appropriate paths (`~/Library/Application Support/HamHatCC` on macOS, `~/.local/share/hamhatcc` on Linux).

### Scripts Seam

- `bootstrap_third_party.py` — uses `subprocess`, `git`, `pip`; cross-platform ✓. `--dev` installs `pycaw` (Windows-only) without warning — add a note in help text for Phase 2.
- `play_wav_worker.py`, `capture_wav_worker.py`, `rx_score_worker.py`, `tx_wav_worker.py` — use `sounddevice`/`numpy`; cross-platform ✓
- `two_radio_diagnostic.py` — uses `sounddevice`, `pyserial`; cross-platform ✓; argument validation fixed in SIP-007
- `mesh_sim_tests.py` — pure Python; cross-platform ✓
- `generate_agent_onboarding_pack.py` — uses `pathlib`; cross-platform ✓; typo fixed in AUD-003

### UI/Theme Seam

- Tkinter: cross-platform ✓
- `sv_ttk`: optional, guarded ✓. Falls back to default ttk theme.
- No Windows-specific window decorations, DPI handling, or win32 calls found in UI code ✓

### Launcher/Packaging Seam

`run_bootstrap()` and `run_two_radio_diagnostic()` both use:
```python
subprocess.Popen([sys.executable, str(script)],
    creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0)
```
Correctly guarded ✓

No other `subprocess.CREATE_NEW_CONSOLE`, `winreg`, or Win32-specific packaging calls found.

## Likely Refactoring Seams (updated)

- `app/engine/audio_tools.py` (`_list_devices`, `auto_select_usb_pair`)
  - add cross-platform host API name handling
  - add macOS/Linux USB audio device name keywords
- `app/app.py` (`_apply_os_rx_level`, `_apply_os_tx_level`)
  - currently correct (Windows-only guard); add documentation stub for future macOS/Linux volume control
- `app/app_state.py` (profile path)
  - introduce a `platform_paths` helper for packaged deployment
- `app/engine/pakt/transport.py`
  - add platform-specific BLE permission handling notes and error messages
- `scripts/bootstrap_third_party.py`
  - note that `--dev` installs Windows-only pycaw

## Non-Goals For The First Pass

- full UI framework rewrite
- redesigning APRS features for parity across all modes
- claiming hardware support before runtime and packaging paths are validated

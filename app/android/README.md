# HAM HAT Control Center — Android

Android client for the HAM HAT ecosystem built with **Kivy 2.3 + KivyMD 1.2** via Buildozer.
Reuses the entire `app/engine/` Python engine unchanged; only the UI and hardware layer are new.

## Status

| | |
|---|---|
| Phase | Phase 1 complete (2026-04-05) |
| Framework | Kivy 2.3.1 + KivyMD 1.2.0 |
| Target API | Android 13 (API 33), min Android 8 (API 26) |
| Architecture | arm64-v8a |
| Smoke test | All imports + HamHatApp() PASS |
| APK build | Not yet run — needs Linux build host |

## Quick Start

### Desktop Development Mode (macOS / Linux)

```bash
# Install deps (once)
pip install kivy kivymd bleak pyserial plyer numpy

# Run from this directory
cd app/android
./run_android.sh dev
# or
PYTHONPATH=../:./../.. python3 main.py
```

### Build APK (Linux build host required)

```bash
pip install buildozer
cd app/android

./run_android.sh debug          # debug APK → bin/
./run_android.sh deploy         # build + adb install
./run_android.sh run            # build + install + launch
./run_android.sh logcat         # stream device logs
./run_android.sh clean          # remove build artefacts
```

First build downloads Android SDK + NDK (~4 GB). Subsequent builds are fast.

### Release Build

```bash
export ANDROID_KEYSTORE=/path/to/hamhat.keystore
export ANDROID_KEY_ALIAS=hamhat
export ANDROID_KEY_PASS=yourpassword
./run_android.sh release
```

## Directory Structure

```
app/android/
├── main.py                    # HamHatApp (MDApp); responsive phone/tablet layout
├── engine_bridge.py           # sys.path injection → app.engine.* imports
├── buildozer.spec             # Buildozer config → arm64-v8a APK
├── run_android.sh             # Build helper script
├── requirements-android.txt   # Build host pip requirements
├── hal/                       # Hardware Abstraction Layer
│   ├── paths.py               # Android data dir (App.user_data_dir)
│   ├── ble_manager.py         # BleManager: bleak async; BleState enum; background thread
│   ├── serial_manager.py      # usbserial4a (Android) / pyserial (desktop)
│   └── audio_manager.py       # jnius AudioTrack (Android) / engine delegate (desktop)
├── screens/
│   ├── control_screen.py      # SA818/DigiRig/PAKT panels; BLE state chip; audio routing
│   ├── aprs_screen.py         # Packet log; position beacon; GPS via plyer
│   ├── setup_screen.py        # Profile save/load/reset; PTT; APRS tuning; PAKT config
│   └── mesh_screen.py         # PAKT mesh chat; node list; compose bar
└── assets/
    ├── icon.png               # 512×512 app icon (replace with final artwork)
    └── splash.png             # Splash screen (replace with final artwork)
```

## Architecture Notes

- **Engine reuse:** `app/engine/` is imported as-is via `engine_bridge.py`. `AppProfile`,
  `ProfileManager`, APRS modem, PAKT chunker/capability/telemetry are all unchanged.

- **HAL naming:** The platform layer is `hal/` (not `platform/`) to avoid overriding Python's
  stdlib `platform` module, which `app.engine.platform_paths` depends on.

- **Responsive layout:** `Window.width < dp(600)` → `MDBottomNavigation` (phone);
  `≥ dp(600)` → `MDNavigationRail` (tablet). Detection happens in `build()` before widget creation.

- **BLE:** `hal/ble_manager.py` runs bleak in a background asyncio event loop (daemon thread).
  All UI callbacks are delivered via `Clock.schedule_once()` to stay on the Kivy main thread.

- **Profile round-trip:** Every screen implements `load_profile(profile)` and
  `collect_profile(profile)`. `main.py` calls both on load and every 30 s autosave.

- **Android permissions:** Declared in `buildozer.spec`; runtime requests happen in `on_start()`
  via `hal.ble_manager.request_ble_permissions()` and equivalents.

## Phase Roadmap

| Phase | Status | Key items |
|---|---|---|
| Phase 1 — MVP | ✓ Done (2026-04-05) | All screens, HAL stubs, engine bridge, buildozer.spec, smoke test |
| Phase 2 — Hardware | ✓ Done (2026-04-06) | RadioController SA818 AT, AprsModemBridge TX/RX, PaktServiceBridge mesh, foreground service; all screens wired; smoke test PASS |
| Phase 3 — Device | Next | `buildozer android debug` APK; device install; hardware validation; signing |
| Phase 4 — Polish | Planned | Play Store, QR profile sync, offline tile cache, split-screen tablet map |

## Permissions Required

`BLUETOOTH`, `BLUETOOTH_ADMIN`, `BLUETOOTH_SCAN`, `BLUETOOTH_CONNECT`,
`ACCESS_FINE_LOCATION`, `RECORD_AUDIO`, `READ/WRITE_EXTERNAL_STORAGE`,
`INTERNET`, `FOREGROUND_SERVICE` — declared in `buildozer.spec`.

USB host feature declared for SA818 / DigiRig USB OTG use.

## See Also

- Architecture plan: [`cross-platform-v4/android-plan.md`](../../cross-platform-v4/android-plan.md)
- Support matrix: [`cross-platform-v4/support-matrix.md`](../../cross-platform-v4/support-matrix.md)
- Engine source: [`app/engine/`](../engine/)

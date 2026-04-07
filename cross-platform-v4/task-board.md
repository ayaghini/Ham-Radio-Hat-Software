# Cross-Platform v4 Task Board

Status keys: `todo`, `in_progress`, `done`

## Current Priorities

| ID | Status | Task | Exit Check |
|---|---|---|---|
| CP-512 | todo | Linux desktop bring-up | `app/run_linux.sh` launches cleanly; then run `python3 app/scripts/platform_validation.py` |
| CP-520 | in_progress | macOS workflow validation | SA818 serial/PTT/TX-audio workflow now confirmed after offset and duplicate-USB-device fixes; BLE permission flow still needs hardware |
| CP-521 | in_progress | Raspberry Pi workflow validation | next operator pass: wheel zoom, serial, audio pair selection, profile save/load, BLE prerequisites; run `platform_validation.py` |
| CP-530 | todo | PAKT hardware validation | real BLE scan/connect/TX result behavior verified |
| CP-540 | in_progress | macOS packaging verification | exit checks substantially complete; SA818 TX/PTT/audio workflow now works after shared offset/audio-enumeration fixes; remaining: button-click verification (blocked by macOS 15 Accessibility requirement) and BLE dialog (needs hardware) |
| CP-541 | todo | Linux packaging verification | spec + build script ready (`app/packaging/`); first real Linux build still needs to be run |
| CP-542 | todo | Raspberry Pi deployment verification | venv install + autostart flow verified on device |
| CP-600A | done | Android expansion — Phase 1 implementation | `app/android/` directory created with full Kivy/KivyMD app; all 4 screens + HAL layer + buildozer spec; engine imports verified; smoke test passed 2026-04-05 |
| CP-601A | done | Android Phase 2 — hardware wiring | RadioController (SA818 AT), AprsModemBridge (TX/RX), PaktServiceBridge (mesh), foreground_service (Android BG); all screens wired; smoke test PASS 2026-04-06 |
| CP-602A | todo | Android buildozer APK build | First `buildozer android debug` build on Linux host; install on device and validate launch |

## Completed Foundations

| ID | Status | Task | Notes |
|---|---|---|---|
| CP-100 | done | Architecture seams and platform assumptions | serial/audio/BLE/path assumptions documented |
| CP-103 | done | User-data path migration | writable app-data path implemented |
| CP-200 | done | Whole-app integrity audit | routing/state/profile issues fixed |
| CP-203 | done | Script hardening audit | worker/bootstrap script findings resolved |
| CP-303 | done | Non-Windows PAKT reconnect review | callback-thread safety hardened |
| CP-400 | done | Packaging strategies documented | Windows/macOS/Linux/RPi paths written down |
| CP-500 | done | Smoke coverage | smoke test + guard-only CI in place |
| CP-501 | done | Platform validation script | `platform_validation.py` — 44 pass 0 fail 7 skip on macOS; per-function scroll checks; display-env + group checks for Linux |
| CP-502 | done | Packaging artifacts (spec + build scripts) | `app/packaging/app_mac.spec`, `app_linux.spec`, `build_mac.sh`, `build_linux.sh` |
| CP-510 | done | Raspberry Pi bring-up | user-confirmed |
| CP-511 | done | macOS bring-up | user-confirmed |
| CP-600 | done | Repo cleanup | `app/` canonical, `archive/` for historical snapshots |
| CP-601 | done | Launcher parity | all supported OS targets have source launchers |

## Completed Foundations (Android)

| ID | Status | Task | Notes |
|---|---|---|---|
| CP-600A | done | Android architecture plan | `cross-platform-v4/android-plan.md` created; Kivy/KivyMD chosen over React Native/Flutter for Python code reuse |
| CP-600A | done | Android app skeleton | `app/android/` full directory: main.py, engine_bridge.py, hal/, screens/, buildozer.spec, run_android.sh |
| CP-600A | done | Android HAL layer | `hal/ble_manager.py` (bleak async), `hal/serial_manager.py` (usbserial4a/pyserial), `hal/audio_manager.py`, `hal/paths.py` |
| CP-600A | done | Android screens | 4 screens (Control/APRS/Setup/Mesh) with load_profile/collect_profile; responsive phone+tablet layout |
| CP-600A | done | Android engine bridge | `engine_bridge.py` — sys.path injection so `app.engine.*` imports cleanly from `app/android/` |
| CP-600A | done | Android smoke test | All imports + HamHatApp() instantiation verified 2026-04-05 (kivy 2.3.1, kivymd 1.2.0) |

## Notes

- Use `app/audit_v4.md` for current open app/script risks.
- Do not spend time on archived packages unless a historical reference is required.
- Android source is in `app/android/`; run desktop dev mode with `./run_android.sh dev` or `PYTHONPATH=../:./../.. python3 main.py` from `app/android/`.

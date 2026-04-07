# Cross-Platform v4 Support Matrix

Last updated: 2026-04-06 (macOS SA818 workflow confirmed; duplicate USB-audio fix landed)

## Desktop/Embedded Platform Status

| Capability | Windows | macOS | Linux | Raspberry Pi | Notes |
|---|---|---|---|---|---|
| Startup from source | baseline | confirmed | pending | confirmed | Linux desktop still needs first real run |
| Profile persistence | baseline | confirmed | pending | pending | macOS SA818/DigiRig/PAKT round-trips confirmed |
| Audio enumeration | baseline | confirmed | pending | pending | macOS duplicate same-name USB codecs now preserved: 4 outputs, 2 inputs (`USB Audio Device [1]/[2]`) |
| Serial scan | baseline | confirmed | likely-ok | likely-ok | macOS `/dev/cu.*` naming confirmed; no hardware ports present |
| Serial workflows | baseline | confirmed | likely-ok | likely-ok | macOS SA818 connect/apply/PTT/TX workflow confirmed on real hardware |
| DigiRig workflows | baseline | likely-ok | likely-ok | likely-ok | real-device validation still needed |
| PAKT BLE | baseline | needs hardware | needs hardware | needs hardware | transport module loads on macOS; live scan/permission dialog needs hardware |
| Packaging path | baseline | exit-checks-substantial | spec-ready | venv-install | macOS: exit checks substantially complete, plus shared fixes for frozen playback, TX offset clarity, and duplicate USB codec selection; button-click verification still needs Accessibility permission; BLE dialog needs hardware |

## Android Platform Status

| Capability | Android Phone | Android Tablet | Notes |
|---|---|---|---|
| App framework | Kivy 2.3 + KivyMD 1.2 | Kivy 2.3 + KivyMD 1.2 | MDBottomNavigation (phone) / MDNavigationRail (tablet) |
| Startup / smoke | imports-verified | imports-verified | Phase 2 full smoke test PASS 2026-04-06 (kivy 2.3.1, kivymd 1.2.0, macOS) |
| Profile persistence | engine-reuse | engine-reuse | Uses app.engine.profile.ProfileManager + app.engine.models.AppProfile unchanged |
| Audio enumeration | hal-impl | hal-impl | hal/audio_manager.py: jnius AudioManager on Android, delegates to engine on desktop |
| Serial (SA818/DigiRig) | hal-impl | hal-impl | hal/serial_manager.py + hal/radio_controller.py: DMOSETGROUP/DMOCONNECT over usbserial4a (Android) or pyserial (desktop) |
| APRS TX | hal-impl | hal-impl | hal/aprs_modem_bridge.py: engine AFSK encoder → Android AudioTrack / sounddevice (desktop) |
| APRS RX | hal-impl | hal-impl | hal/aprs_modem_bridge.py: AudioRecord (Android) / sounddevice InputStream → engine decoder |
| PAKT BLE | hal-impl | hal-impl | hal/ble_manager.py (scan/connect) + hal/pakt_service_bridge.py (PaktService commands) |
| Responsive layout | phone-layout | tablet-layout | Width < 600dp → BottomNavigation; ≥ 600dp → NavigationRail |
| Background BLE service | hal-impl | hal-impl | hal/foreground_service.py: jnius startForeground() persistent notification |
| Buildozer APK build | not-yet-run | not-yet-run | buildozer.spec ready with Phase 2 requirements (bleak, numpy, scipy); needs Linux build host |
| GPS (APRS beacon) | plyer-wired | plyer-wired | plyer.gps wired in AprsScreen; needs real device |

## Key Platform Notes

- macOS: packaged BLE needs `NSBluetoothAlwaysUsageDescription`
- Linux/Raspberry Pi: `dialout` and often `bluetooth` access are required
- Raspberry Pi uses the same active app as other platforms; use `app/run_rpi.sh`
- Android: buildozer APK build requires Linux host (Ubuntu recommended); use `app/android/run_android.sh`
- Android: `hal/` package named deliberately to avoid Python stdlib `platform` module collision

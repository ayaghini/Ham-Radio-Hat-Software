# Cross-Platform v4 Packaging Guide

Status date: 2026-04-03
App: `app`

## Source Launchers

| OS | Launcher |
|---|---|
| Windows | `run_windows.ps1`, `run_windows.bat` |
| macOS | `run_mac.command` |
| Linux desktop | `run_linux.sh` |
| Raspberry Pi | `run_rpi.sh` |

All launchers create/reuse `.venv`, install requirements as needed, and run `main.py`. Raspberry Pi launcher adds `--rpi`.

## Packaging Paths

| Target | Path | State |
|---|---|---|
| Windows | PyInstaller one-file exe | documented, not build-verified |
| macOS | PyInstaller `.app` + signing/notarization | documented, not build-verified |
| Linux desktop | PyInstaller binary, AppImage or `.deb` later | documented, not build-verified |
| Raspberry Pi | venv install + launcher/autostart | documented, not deployment-verified |

## Important Notes

- app data writes to per-user writable locations via `platform_paths.py`
- macOS packaged BLE needs `NSBluetoothAlwaysUsageDescription`
- Linux/RPi need system audio libs and typical `dialout` / `bluetooth` access
- archived packages under `archive/` are historical only

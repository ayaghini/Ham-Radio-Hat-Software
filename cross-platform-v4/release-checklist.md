# Release Verification Checklist

Use this checklist before tagging a release and distributing binaries.
Work through each section in order; do not skip steps.

---

## 1. Pre-build (all platforms)

- [ ] `git status` is clean (no uncommitted changes).
- [ ] `python -m compileall -q app/` exits 0.
- [ ] `python main.py --help` exits 0.
- [ ] `python scripts/smoke_test.py` all checks pass (11/11 or more).
- [ ] VERSION file reflects the correct version string.
- [ ] requirements.txt is up to date with all tested dep versions.

---

## 2. Windows build (CP-400)

### Build

```batch
pip install pyinstaller
pyinstaller --onefile --windowed ^
    --name HamHatCC ^
    --add-data "tiles;tiles" ^
    --add-data "VERSION;." ^
    main.py
```

### Verification

- [ ] `dist/HamHatCC.exe` exists and file size is reasonable (> 20 MB).
- [ ] Double-click `HamHatCC.exe` — window opens without error dialog.
- [ ] Serial port scan runs at startup (no crash).
- [ ] Profile saves to `%APPDATA%\HamHatCC\profiles\last_profile.json`.
- [ ] Audio device list populates (or shows "No devices" gracefully).
- [ ] `--help` works from a command prompt.
- [ ] Test on a clean Windows 10/11 machine without Python installed.

---

## 3. macOS build (CP-401)

### Build

```bash
pip install pyinstaller
pyinstaller --windowed \
    --name "HAM HAT Control Center" \
    --add-data "tiles:tiles" \
    --add-data "VERSION:." \
    --osx-bundle-identifier com.hamhat.controlcenter \
    main.py
```

### Add BLE Info.plist key (required for PAKT on macOS 12+)

```bash
/usr/libexec/PlistBuddy -c \
  "Add :NSBluetoothAlwaysUsageDescription string 'HAM HAT Control Center uses Bluetooth to connect to the PAKT TNC.'" \
  "dist/HAM HAT Control Center.app/Contents/Info.plist"
```

### Sign + notarize + staple

```bash
codesign --deep --force --options runtime \
    --sign "Developer ID Application: Your Name (TEAM_ID)" \
    "dist/HAM HAT Control Center.app"

# Zip for notarization
ditto -c -k --keepParent \
    "dist/HAM HAT Control Center.app" \
    "dist/HAM HAT Control Center.zip"

xcrun notarytool submit \
    "dist/HAM HAT Control Center.zip" \
    --apple-id you@example.com \
    --team-id TEAM_ID \
    --password APP_SPECIFIC_PASSWORD \
    --wait

xcrun stapler staple "dist/HAM HAT Control Center.app"
```

### Verification

- [ ] `dist/HAM HAT Control Center.app` launches via double-click.
- [ ] Gatekeeper does not block the app (staple verified).
- [ ] Serial port scan runs at startup (`/dev/cu.*` ports listed).
- [ ] Profile saves to `~/Library/Application Support/HamHatCC/profiles/`.
- [ ] Audio device list populates.
- [ ] BLE scan triggers OS Bluetooth permission dialog on first use.
- [ ] `Info.plist` contains `NSBluetoothAlwaysUsageDescription`.
- [ ] Test on a clean macOS 13+ machine without Python installed.

---

## 4. Linux build (CP-402)

### Build

```bash
pip install pyinstaller
pyinstaller --onefile \
    --name hamhatcc \
    --add-data "tiles:tiles" \
    --add-data "VERSION:." \
    main.py
```

### Verification

- [ ] `dist/hamhatcc` is executable and file size is reasonable.
- [ ] `./dist/hamhatcc` launches on Ubuntu 22.04+ desktop.
- [ ] Serial port scan runs (`/dev/ttyUSB*` listed if DigiRig connected).
- [ ] Profile saves to `~/.local/share/hamhatcc/profiles/`.
- [ ] Audio device list populates.
- [ ] BLE scan works when user is in `bluetooth` group.
- [ ] Test on a clean Ubuntu 22.04+ desktop without Python installed.

---

## 5. Raspberry Pi deployment (CP-403)

### Install

```bash
bash install.sh   # (from repo, see packaging-guide.md)
```

### Verification

- [ ] `python3 main.py --rpi` opens at 1280×720.
- [ ] Serial port scan lists GPIO UART (`/dev/ttyAMA0`) and/or USB serial.
- [ ] Profile saves to `~/.local/share/hamhatcc/profiles/`.
- [ ] Audio device list populates (USB audio if connected).
- [ ] BLE scan works when user is in `bluetooth` group.
- [ ] autostart entry launches the app on desktop login.

---

## 6. Final gate

- [ ] All platform builds pass their verification steps above.
- [ ] No regressions vs. the previous release.
- [ ] Git tag applied: `git tag -a v4.X.Y -m "Release v4.X.Y"`.
- [ ] Release notes drafted (bugs fixed, features added).

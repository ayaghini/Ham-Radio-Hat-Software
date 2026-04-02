# Cross-Platform v4 Packaging Guide

Status date: 2026-04-01
App: `windows-release/ham_hat_control_center_v4`

---

## Overview

All four targets share the same codebase.  Only the packaging mechanism
differs.  The app data directory is handled by `platform_paths.py` — no
runtime code needs to change between targets.

Required core deps (all platforms): `pyserial`, `numpy`, `sounddevice`
Optional deps by platform:

| Dep | Windows | macOS | Linux | RPi |
|---|---|---|---|---|
| bleak | required (WinRT) | required (CoreBluetooth) | required (BlueZ) | required (BlueZ) |
| Pillow | map tiles | map tiles | map tiles | map tiles |
| requests | tile download | tile download | tile download | tile download |
| scipy | audio speedup | audio speedup | audio speedup | audio speedup |
| sv-ttk | UI theme | UI theme | UI theme | UI theme |
| pycaw | vol control | not used | not used | not used |

---

## CP-400 — Windows Packaging Baseline

### Current state

- `run_windows.bat` and `run_windows.ps1` — launch scripts for running from
  source in a local `venv`.
- No compiled binary yet.

### Recommended path

**PyInstaller one-file exe** (simplest distribution, no install required):

```batch
pip install pyinstaller
pyinstaller --onefile --windowed ^
    --name HamHatCC ^
    --add-data "tiles;tiles" ^
    --add-data "VERSION;." ^
    main.py
```

- `--windowed` suppresses the console window on double-click.
- `--add-data` bundles the offline tile cache and VERSION file.
- Output: `dist/HamHatCC.exe` — single redistributable binary.

### Caveats

- pycaw requires comtypes; PyInstaller usually picks it up automatically.
- Test with bleak: WinRT backend may need `--collect-all bleak`.
- Windows Defender may flag unsigned executables; code signing with a
  purchased EV certificate removes the SmartScreen warning.
- App data writes to `%APPDATA%\HamHatCC` (handled by `platform_paths.py`).

### Exit check

`dist/HamHatCC.exe` launches, reaches the serial port scan, and writes
profiles to `%APPDATA%\HamHatCC\profiles\`.

---

## CP-401 — macOS Packaging

### Recommended path

**PyInstaller .app bundle** (Gatekeeper-compatible after signing):

```bash
pip install pyinstaller
pyinstaller --windowed \
    --name "HAM HAT Control Center" \
    --add-data "tiles:tiles" \
    --add-data "VERSION:." \
    --osx-bundle-identifier com.hamhat.controlcenter \
    main.py
```

Output: `dist/HAM HAT Control Center.app`

### Required: Info.plist BLE key

Without this key, the app crashes on first BLE scan on macOS 12+:

```xml
<key>NSBluetoothAlwaysUsageDescription</key>
<string>HAM HAT Control Center uses Bluetooth to connect to the PAKT TNC.</string>
```

Add it via a `--osx-entitlements-file` plist or by editing the generated
`Info.plist` in `dist/HAM HAT Control Center.app/Contents/` after the build:

```bash
/usr/libexec/PlistBuddy -c \
  "Add :NSBluetoothAlwaysUsageDescription string 'HAM HAT Control Center uses Bluetooth to connect to the PAKT TNC.'" \
  "dist/HAM HAT Control Center.app/Contents/Info.plist"
```

### Code signing and notarization

Required for distribution to users who are not developers:

```bash
# Sign (replace TEAM_ID with your Apple Developer team ID)
codesign --deep --force --options runtime \
    --sign "Developer ID Application: Your Name (TEAM_ID)" \
    "dist/HAM HAT Control Center.app"

# Notarize
xcrun notarytool submit \
    "dist/HAM HAT Control Center.zip" \
    --apple-id you@example.com \
    --team-id TEAM_ID \
    --password APP_SPECIFIC_PASSWORD \
    --wait

# Staple
xcrun stapler staple "dist/HAM HAT Control Center.app"
```

Wrap the .app in a .dmg with `hdiutil create` for distribution.

### Caveats

- BLE requires Bluetooth permission — first launch triggers OS dialog.
- App data writes to `~/Library/Application Support/HamHatCC/` (handled).
- Logs write to `~/Library/Logs/HamHatCC/`.
- sv-ttk uses tkinter theming; test on macOS — dark mode may need a
  `root.tk.call("source", "azure.tcl")` fallback if sv-ttk misbehaves.
- pyserial serial ports appear as `/dev/cu.usbserial-*` on macOS; the
  existing `scan_ports()` filter handles this.

### Exit check

App opens, serial port scan completes (listing `/dev/cu.*` ports), and app
data writes to `~/Library/Application Support/HamHatCC/`.

---

## CP-402 — Linux Desktop Packaging

### Recommended path

**PyInstaller one-file binary** (widest compatibility; no distro-specific packaging needed for initial release):

```bash
pip install pyinstaller
pyinstaller --onefile \
    --name hamhatcc \
    --add-data "tiles:tiles" \
    --add-data "VERSION:." \
    main.py
```

Output: `dist/hamhatcc` — single executable, no install required.

#### Alternative: AppImage (portable, distro-agnostic)

Wrap the PyInstaller output in an AppImage using `appimagetool` for a
`.AppImage` that users can mark executable and run directly.  This is
preferred for distribution but adds build complexity.

#### Alternative: .deb (Debian/Ubuntu)

For users on Debian/Ubuntu, a `.deb` that installs a venv + launcher script
is the most native experience.  Deferred until there is a target distro.

### Runtime requirements (not bundled)

These must be present on the user's system before running:

- `libasound2` or `libpulse` — required by sounddevice.
- BlueZ (`bluetoothd`) — required for PAKT BLE (`systemctl status bluetooth`).
- The user must be in the `bluetooth` group for non-root BLE access:
  `sudo usermod -aG bluetooth $USER` (then log out/in).

### Caveats

- tkinter must be available system-wide when not using PyInstaller
  (`sudo apt install python3-tk` on Debian/Ubuntu).
- PyInstaller bundles its own Python and tkinter; system tkinter not needed.
- Serial port access requires the `dialout` group:
  `sudo usermod -aG dialout $USER`.
- App data writes to `~/.local/share/hamhatcc/` (XDG, handled).

### Exit check

`./dist/hamhatcc` launches on a fresh Ubuntu 22.04+ desktop, serial scan
completes (listing `/dev/ttyUSB*` ports), and app data writes to
`~/.local/share/hamhatcc/`.

---

## CP-403 — Raspberry Pi Deployment

### Target

Raspberry Pi OS (Bookworm, 64-bit) on a Raspberry Pi 4 or 5 with a
5-inch 1280×720 touchscreen.

### Recommended path: venv install script

No compiled binary needed — run from source with a venv:

```bash
#!/usr/bin/env bash
# install.sh — run once on the RPi to set up the app
set -e
INSTALL_DIR="$HOME/hamhat"

sudo apt update
sudo apt install -y python3-venv python3-tk libasound2-dev

git clone <repo-url> "$INSTALL_DIR"
cd "$INSTALL_DIR/windows-release/ham_hat_control_center_v4"

python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
# Install without pycaw (Windows-only)
grep -v pycaw requirements.txt | pip install -r /dev/stdin
```

Launch script (`launch.sh`):

```bash
#!/usr/bin/env bash
cd "$HOME/hamhat/windows-release/ham_hat_control_center_v4"
source venv/bin/activate
python3 main.py --rpi
```

### Groups required

```bash
sudo usermod -aG dialout $USER    # serial port access
sudo usermod -aG bluetooth $USER  # BLE (PAKT) access
# Log out and back in, or reboot
```

### Auto-start on login (optional)

Add `launch.sh` to the desktop autostart:

```bash
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/hamhat.desktop <<EOF
[Desktop Entry]
Type=Application
Name=HAM HAT Control Center
Exec=$HOME/hamhat/launch.sh
X-GNOME-Autostart-enabled=true
EOF
```

### Update procedure

```bash
cd ~/hamhat
git pull
source windows-release/ham_hat_control_center_v4/venv/bin/activate
grep -v pycaw windows-release/ham_hat_control_center_v4/requirements.txt \
    | pip install -r /dev/stdin --upgrade
```

### Caveats

- Use `--rpi` flag for the 5-inch 1280×720 screen preset.
- Serial port on RPi is typically `/dev/ttyAMA0` (SA818 HAT GPIO UART) or
  `/dev/ttyUSB0` (DigiRig USB).  Disable serial console first if using GPIO:
  `sudo raspi-config → Interface Options → Serial Port`.
- BLE on RPi 4/5 uses the built-in Bluetooth module; same BlueZ group
  requirements as Linux desktop.
- App data writes to `~/.local/share/hamhatcc/`.

### Exit check

`python3 main.py --rpi` opens the app at 1280×720, serial scan finds GPIO
UART and/or USB serial adapters, and app data writes to
`~/.local/share/hamhatcc/`.

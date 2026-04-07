# Cross-Platform v4 Packaging and Release Plan

Updated: 2026-04-06 (macOS SA818 workflow confirmed; shared audio-device fix landed)

## Goal

Define a native-feeling release path for each target platform without fragmenting the codebase.

## Decisions Made

| Platform | Format | Artifacts | Status |
|---|---|---|---|
| Windows | PyInstaller one-file exe | (existing baseline) | baseline |
| macOS | PyInstaller `.app` bundle | `app/packaging/app_mac.spec`, `build_mac.sh` | **substantial pass 2026-04-06** — launch/no-crash, profile path + save/load, serial/PTT/TX audio confirmed; duplicate same-name USB codecs now stay distinct; button-click verification and BLE dialog still need Accessibility permission or hardware |
| Linux desktop | PyInstaller one-folder bundle | `app/packaging/app_linux.spec`, `build_linux.sh` | spec ready, build not yet run |
| Raspberry Pi | Source install via `run_rpi.sh` (venv) | `run_rpi.sh` | launcher in place |

## Build Notes (macOS — 2026-04-04)

Two fixes were required before the first build:
1. **pip shebang stale** — `.venv/bin/pip` pointed to an old path (venv was created elsewhere). Fixed: both build scripts now use `"$VENV_PY" -m pip` instead of `"$VENV_PIP"`.
2. **Spec path resolution** — PyInstaller resolves paths relative to the spec file's directory (`app/packaging/`), not the working directory. Fixed: both specs now derive absolute paths via the PyInstaller `SPECPATH` built-in.

Non-blocking build warnings (no action required):
- `pycparser.lextab`/`yacctab` — generated caching files, not real modules; pycparser handles absence gracefully
- `scipy.special._cdflib` — not present in the installed scipy version; not a runtime failure
- Windows-only ctypes libs (`setupapi`, `ole32`, `user32`, etc.) — expected absence on macOS

## Exit Check Results (macOS — 2026-04-04, programmatic)

Verified without display using binary CLI + module-level tests against the same profile dir:

| Check | Result | Notes |
|---|---|---|
| Binary `--help` | ✓ pass | |
| No-crash launch (6 s) | ✓ pass | |
| Profile path resolves | ✓ pass | `~/Library/Application Support/HamHatCC/profiles/` |
| Profile save/load round-trip | ✓ pass | AppProfile mutated, saved, reloaded, field verified |
| Audio enumeration | ✓ pass | source build now confirms 4 out, 2 in with duplicate USB codecs preserved as `USB Audio Device [1]` / `[2]` |
| Serial scan | ✓ pass | pyserial executes; `/dev/cu.*` ports returned |
| bleak bundled | ✓ pass | packed in CArchive; pyobjc CoreBluetooth bindings in Resources |
| sv_ttk / PIL / scipy / numpy | ✓ pass | present in Resources |
| NSBluetooth + NSMicro in plist | ✓ pass | |
| Audio routing shown in Control tab UI | ✓ pass | Historical 2026-04-04 screenshot showed TX Output: LG ULTRAFINE, RX Input: WH-1000XM4; current build now keeps duplicate USB codecs separately selectable as `USB Audio Device [1]` / `[2]` |
| Serial port auto-detected in UI | ✓ pass | /dev/cu.debug-console shown in Serial Port field on startup |
| Profile loaded correctly in UI | ✓ pass | Profile values shown in UI match disk; radio-apply status now reports both RX and TX frequencies |
| Profile autosave fires | ✓ pass | Status bar showed "Profile saved: last_profile.json" (30 s autosave confirmed) |
| Refresh Audio Devices button present | ✓ pass | Visible in Control tab (source + screenshot confirmed) |
| Serial Refresh button present | ✓ pass | Visible in Control tab (screenshot confirmed) |
| Button-click automation (Refresh, tab switch) | — blocked | CGEvent injection does not deliver to Tkinter on macOS 15 without Accessibility permission; needs human operator or permission grant |
| BLE permission dialog | — pending | requires hardware |

## Windows

Current status: existing baseline. Preserve as regression reference.

## macOS

**Strategy**: PyInstaller `.app` bundle
**Build**: `cd app && ./packaging/build_mac.sh`
**Output**: `dist/HamHatCC.app`

Permission requirements (in `Info.plist` — already in spec):
- `NSBluetoothAlwaysUsageDescription` — PAKT BLE scan/connect
- `NSMicrophoneUsageDescription` — APRS audio input (sounddevice)

Signing / notarization:
- Set `CODESIGN_IDENTITY` env var before running `build_mac.sh`
- After build: `codesign --deep --force --sign "$CODESIGN_IDENTITY" dist/HamHatCC.app`
- Notarization: `xcrun notarytool submit <zip> --apple-id … --team-id … --wait`
- Staple: `xcrun stapler staple dist/HamHatCC.app`

Install / update path: drag-install `.app` to `/Applications`; auto-update TBD.

Exit check (run after each build):
1. ✓ App launches cleanly (confirmed 2026-04-04)
2. ✓ Profile path `~/Library/Application Support/HamHatCC` resolves on first run (confirmed)
3. ✓ Profile save/load: autosave fires (status bar "Profile saved: last_profile.json" confirmed); API round-trip confirmed; on-close save confirmed via `_on_close` + `WM_DELETE_WINDOW` code review
4. ✓ Audio devices shown in UI: duplicate same-name USB codecs remain separately selectable as `USB Audio Device [1]` and `[2]` in the Control tab Audio Routing section
5. ✓ Serial port auto-detected in UI: /dev/cu.debug-console shown in Serial Port field; ↺ Refresh and ⬡ Auto-ID buttons visible
6. — BLE scan triggers Bluetooth permission dialog (requires hardware)
7. ✓ Optional deps bundled: sv_ttk, PIL, scipy, numpy in Resources; bleak in CArchive
8. ✓ SA818 simplex TX is now explicit: `TX Offset (MHz, 0.000 = simplex)` and status shows RX/TX frequencies after Apply Radio
Note: Button-click automation blocked by macOS 15 Accessibility permission requirement for CGEvent injection into Tkinter. Refresh/scan button click response and tab navigation need human operator verification.

## Linux Desktop

**Strategy**: PyInstaller one-folder bundle (`dist/hamhatcc/`)
**Build**: `cd app && ./packaging/build_linux.sh`
**Output**: `dist/hamhatcc/hamhatcc`

System prerequisites (install before building or running):
```
sudo apt install python3-tk libasound2-dev
sudo usermod -aG dialout $USER    # serial access
sudo usermod -aG bluetooth $USER  # BLE/PAKT access
```

Future: consider AppImage or `.deb` wrapper once the bare binary is build-verified.

Exit check (run after each build):
1. Binary launches cleanly: `./dist/hamhatcc/hamhatcc`
2. Profile path `~/.local/share/hamhatcc` resolves on first run
3. Profile save/load round-trip
4. TX Output / RX Input dropdowns populated in Control tab; prefer `[PipeWire]` entries on PipeWire systems
5. Serial scan responds (no hardware needed)
6. BLE prerequisites: BlueZ running, user in `bluetooth` group
7. Optional-dep fallback: sv_ttk absent → fallback theme; PIL absent → grid map

## Raspberry Pi

**Strategy**: Source install via `run_rpi.sh` (creates `.venv`, installs deps, launches with `--rpi`).
No PyInstaller packaging for MVP.
Future option: managed `.deb` or `systemd` service for kiosk deployments.

System prerequisites (once):
```
sudo apt install python3-venv python3-tk libasound2-dev
sudo usermod -aG dialout $USER
sudo usermod -aG bluetooth $USER
# If using SA818 GPIO UART:
# sudo raspi-config → Interface Options → Serial Port → disable login shell
```

Update path: `git pull` in the repo dir; launcher creates/repairs `.venv` on next run.

Exit check:
1. `./run_rpi.sh` launches, window fits 1280×720 display
2. Wheel scroll works on both map canvas and tab panels
3. Profile save/load round-trip
4. TX Output / RX Input dropdowns populated in Control tab; ALSA entries suppressed when PipeWire is running (verify `[PipeWire]` entries appear, not bare `hw:` devices); serial scan responds
5. BLE prerequisites messaging (bluetooth group check from `platform_validation.py`)

## Release Checklist Template

- [ ] Build artifact produced without errors
- [ ] App launches cleanly on target OS
- [ ] Profile path resolves correctly on first run
- [ ] Profile save/load confirmed
- [ ] Audio enumeration shows devices
- [ ] Serial scan executes
- [ ] Optional dependency fallback confirmed (no crash when sv_ttk/PIL/scipy absent)
- [ ] Platform-specific permissions noted in release notes

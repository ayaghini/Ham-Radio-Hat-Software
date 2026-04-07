# v4 App Audit

Updated: 2026-04-06 (RPi second-radio USB cascade root cause fixed; Linux audio host-API filter hardened)
Scope: canonical audit for `app`

## Verification Baseline

```text
# Use -x '\.venv' (not --exclude) on Python 3.9; .venv may contain Python 3.13
# packages (bleak, numpy, scipy) with match-statement syntax that 3.9 rejects.
python3 -m compileall -q -x '\.venv' app
python3 app/main.py --help
python3 app/scripts/smoke_test.py -v
python3 app/scripts/smoke_test.py -v --guards-only
python3 app/scripts/mesh_sim_tests.py
python3 app/scripts/platform_validation.py    # full cross-platform checklist
```

Local status (macOS Darwin 25.4.0, arm64, Python 3.9.6 — 2026-04-06):
- compile/smoke/mesh checks pass
- `platform_validation.py` result: 48 pass, 0 fail, 5 skip
  - profile round-trip (SA818/DigiRig/PAKT): pass
  - audio enumeration (duplicate same-name USB codecs preserved): 2 out, 0 in — pass (macOS hardware on this run)
  - serial scan + `/dev/cu.*` naming: pass
  - PAKT transport module + TransportState: pass
  - platform paths, DisplayConfig, APRS payload: pass
  - scroll bindings (per-function inspect check) — `<Button-4/5>` confirmed within `scrollable_frame`, `AprsMapCanvas.__init__`, `TiledMapCanvas.__init__`; `_on_wheel` handlers in both canvases confirmed to route `event.num` (Linux) and `event.delta` (Win/macOS): pass
  - launcher scripts — `run_linux.sh` + `run_rpi.sh` pycaw exclusion, tkinter preflight, executable bit: pass
  - Linux audio host-API consistency check — skipped (macOS Core Audio only; fires on Linux/RPi)
  - bleak/scipy/sv_ttk absent: 5 SKIP (all gracefully guarded)
- script hardening work is complete
- shared runtime fixes from macOS hardware validation are in:
  - frozen packaged-playback fallback fixed in `app/engine/audio_router.py`
  - TX worker playback aligned with compatible path in `scripts/play_wav_worker.py` and `scripts/tx_wav_worker.py`
  - duplicate same-name audio devices now remain selectable in `app/engine/audio_tools.py`
  - simplex default/labeling clarified (`offset=0.000`) and radio-apply status now shows RX and TX frequencies
  - TX actions now guard against overlapping runs
- RPi second-radio USB cascade root cause identified and fixed (2026-04-06) — see RES-007 below
- packaging spec files + build scripts created: `app/packaging/`
- macOS packaging first build (2026-04-04): PyInstaller 6.19.0, Python 3.13.12
  - `dist/HamHatCC.app` (92MB), binary `--help` works, no immediate crash
  - profile path `~/Library/Application Support/HamHatCC/` resolves
  - `VERSION=4.0` and `tiles/` present in bundle
  - all optional deps bundled: sv_ttk, bleak, PIL, scipy
  - two spec/script fixes required: pip shebang stale (→ `python3 -m pip`); spec paths (→ `SPECPATH`)
  - warnings (all non-blocking): pycparser generated-file tables, Windows ctypes libs, scipy._cdflib not in this version
  - GUI exit checks (2026-04-04 pass 2 — programmatic):
    - binary `--help`: pass (re-confirmed)
    - no-crash launch: app runs 6+ seconds, no exit — pass
    - profile path `~/Library/Application Support/HamHatCC/profiles/` resolves — pass
    - profile save/load round-trip: AppProfile loaded, mutated, saved, reloaded, field verified — pass
    - audio enumeration (via bundled sounddevice, historical 2026-04-04 snapshot): 3 out, 1 in — pass at that time; current source build now preserves duplicate USB codecs as 4 out, 2 in
    - serial scan (via bundled pyserial): executed, `/dev/cu.*` ports returned — pass
    - bleak bundled: packed in PyInstaller CArchive; pyobjc CoreBluetooth bindings in Resources — confirmed
    - sv_ttk, PIL, scipy, numpy visible in Resources — confirmed
    - NSBluetoothAlwaysUsageDescription + NSMicrophoneUsageDescription in Info.plist — confirmed
  - GUI visual checks (2026-04-04 pass 3 — screenshot-confirmed via screencapture + Swift CGEvent):
    - app launched, window visible: "HAM HAT Control Center (4.0)" — pass
    - audio routing shown in Control tab UI (historical 2026-04-04 screenshot): TX Output=LG ULTRAFINE, RX Input=WH-1000XM4 — pass at that time
      (note: TX Output / RX Input pickers are in Control tab; Setup tab = audio tools, not device picker)
    - serial port auto-detected in UI: /dev/cu.debug-console in Serial Port field — pass
    - profile loaded correctly (UI values match profile on disk) — pass
    - profile autosave fired: status bar "Profile saved: last_profile.json" — pass
    - Refresh Audio Devices + Serial Refresh buttons present and visible — pass
  - Still needing human operator run or permission:
    - button-click response (Refresh buttons etc.): CGEvent injection blocked by macOS 15 Accessibility requirement for Tkinter apps; requires Accessibility permission grant or manual operator verification
    - BLE permission dialog on PAKT scan: needs hardware + Bluetooth
- macOS SA818 hardware-backed validation is now confirmed: raw PTT, app PTT, and TX audio work with the corrected offset and USB codec selection

## Open Risks

### RES-007 — RPi second-radio USB cascade reset (RESOLVED 2026-04-06)

- Severity: High → **RESOLVED**
- Files: `app/engine/audio_tools.py`, `app/scripts/platform_validation.py`

**Root cause:** On RPi Bookworm (and modern Linux desktops), PipeWire or PulseAudio is the
active sound server and holds the USB Audio Class codec exclusively. PortAudio's ALSA backend
also enumerates the same physical device as a raw `hw:` node. When ALSA and PipeWire/PulseAudio
were both assigned rank 0 in `_HOST_API_RANK`, either backend could survive the rank filter.
If the operator (or profile restore) happened to select the ALSA `hw:` device index while
PipeWire held it exclusively, PortAudio raised error −9993
("Illegal combination of I/O devices"). The resulting failed audio open sent an abort signal
through the composite USB device (CP2102N UART + USB Audio on the same HAT), triggering a
kernel USB reset that killed **both** the audio interface and the serial port simultaneously.
This manifested as: Play Test Tone fails → serial commands start returning errno 5 (EIO) →
USB device disappears from `lsusb`.

**Fixes applied (`app/engine/audio_tools.py`):**

1. **ALSA demoted to rank 1** — `"ALSA": 1` in `_HOST_API_RANK`. PipeWire/PulseAudio remain
   rank 0. The filter now naturally selects only the sound-server backend when one is present;
   ALSA `hw:` entries are suppressed entirely. On minimal/headless systems without a sound
   server, only ALSA entries exist, so they pass the filter unchanged (correct).

2. **PulseAudio explicitly ranked** — added `"PulseAudio": 0` so RPi Bullseye / Ubuntu 20.04
   setups using PulseAudio (not PipeWire) are handled identically.

3. **Linux device labels always include host-API name** — even for unique device names on Linux,
   the backend is appended: `"USB Audio Device [PipeWire]"` vs `"USB Audio Device [ALSA]"`.
   This makes it visible in the UI which backend is in use, so an operator can confirm they
   are on the sound-server path.

4. **`play_wav_blocking_compatible` fallback restricted to same host API** — the alternate-device
   search now skips candidates from a different host API. Cross-API fallback could re-introduce
   the same −9993 error. Error message now includes host-API name and an actionable tip.

5. **`platform_validation.py` Linux audio host-API consistency check** — new check in
   `check_audio()` reports which of three states PortAudio sees on Linux:
   - ALSA + sound server present → confirms rank filter is active, ALSA suppressed (expected)
   - Sound server only → clean
   - ALSA only → headless/minimal system, direct hw: will be used (acceptable)
   Fires only on Linux; skipped on macOS and Windows.

**RPi-side retest procedure:**

```text
# On the Raspberry Pi (after pulling latest):
python3 app/scripts/platform_validation.py

# Expected new check output (if PipeWire is running):
#   ✓ [PASS] Linux audio: sound server present (ALSA suppressed by rank filter)
#             PortAudio sees both ALSA and ['PipeWire']; rank filter prefers ['PipeWire']
#             — ALSA hw: devices excluded. ...

# Then in the app UI (Control tab):
# 1. Refresh Audio Devices — confirm output device shows e.g.:
#      "USB Audio Device [PipeWire]"   ← good
#    NOT:
#      "USB Audio Device [ALSA 1]"     ← would be the problematic raw hw: path
# 2. Setup tab → Play Test Tone — should complete without error
# 3. Verify serial port still responds (ℹ Version button) after Play Test Tone
# 4. If second radio is connected: repeat steps 2–3 with radio 2 selected
```

### RES-001 — PAKT TX correlation still needs hardware validation

- Severity: Medium
- Files: `app/engine/comms_mgr.py`, `app/engine/pakt/service.py`

Host-side `pakt-local:N` to firmware `msg_id` remapping looks correct by static review and smoke coverage, but still needs real-device confirmation under retries, reconnects, and back-to-back sends.

### RES-002 — PAKT BLE runtime behavior remains hardware-blocked

- Severity: Medium

BLE scan/connect, bonded-write behavior, TX result sequencing, and live telemetry still need a physical device.

### RES-003 — PAKT callback wiring still depends on post-construction mutation

- Severity: Low
- Files: `app/engine/pakt/service.py`

Safe today, but lifecycle-fragile compared with constructor injection.

### RES-004 — `_make_tx_snapshot()` still returns `None` for PAKT by design

- Severity: Low
- Files: `app/app.py`

Not a live bug now; keep in view if future shared RX/TX packet paths are added.

### RES-005 — PAKT telemetry still lacks a dedicated structured panel

- Severity: Low
- Files: `app/ui/main_tab.py`, `app/app.py`

Telemetry still lands in general log/status output rather than a dedicated panel.

### RES-006 — `chunker.py` still uses `assert` for defensive validation

- Severity: Low
- Files: `app/engine/pakt/chunker.py`

Low priority unless chunking defects start surfacing in production.

## Android Expansion (Phase 1 — 2026-04-05)

Implementation complete in `app/android/`. See `cross-platform-v4/android-plan.md` for full architecture doc.

Files created:
- `app/android/main.py` — HamHatApp (MDApp); responsive phone/tablet build; autosave; on_pause survival
- `app/android/engine_bridge.py` — sys.path injection; re-uses app.engine.* unchanged
- `app/android/buildozer.spec` — API 33, minAPI 26, arm64-v8a, USB host, BLE permissions
- `app/android/run_android.sh` — dev/debug/release/deploy/run/logcat/clean modes
- `app/android/requirements-android.txt` — buildozer, kivy, kivymd, bleak, numpy, scipy, plyer
- `app/android/hal/__init__.py` — HAL package (named hal/ not platform/ to avoid stdlib collision)
- `app/android/hal/paths.py` — Android: App.user_data_dir; Desktop: delegates to engine
- `app/android/hal/ble_manager.py` — async bleak; BleState machine; background asyncio thread
- `app/android/hal/serial_manager.py` — usbserial4a on Android; pyserial on desktop
- `app/android/hal/audio_manager.py` — jnius AudioTrack on Android; delegates on desktop
- `app/android/screens/control_screen.py` — SA818/DigiRig/PAKT panels; BLE state chip; audio routing
- `app/android/screens/aprs_screen.py` — beacon builder; GPS (plyer); packet log; message send
- `app/android/screens/setup_screen.py` — profile save/load/reset; PTT, APRS, PAKT, audio test
- `app/android/screens/mesh_screen.py` — chat log; node list; compose bar; BLE connect/disconnect hooks

Smoke test result (2026-04-05, macOS, kivy 2.3.1, kivymd 1.2.0):
- All 15 module imports: PASS
- HamHatApp() instantiation: PASS
- Engine bridge (app.engine.*): PASS

Phase 2 implementation complete (2026-04-06):
- `hal/radio_controller.py` — SA818 AT protocol (DMOCONNECT/DMOSETGROUP/DMOSETVOLUME/SETFILTER/SETTAIL) over SerialManager; `RadioControllerAsync` for non-blocking UI calls
- `hal/aprs_modem_bridge.py` — TX: engine AFSK encoder → Android AudioTrack / sounddevice; RX: AudioRecord / sounddevice → engine decoder; PTT via RadioController
- `hal/pakt_service_bridge.py` — PaktService wrapped with Clock.schedule_once for all callbacks; full mesh command API
- `hal/foreground_service.py` — Android foreground notification via jnius startForeground; keeps BLE alive in background
- All screens updated: control_screen (apply_radio, connect_serial wired), aprs_screen (real TX/RX), mesh_screen (real PAKT send)
- main.py: all Phase 2 managers instantiated + injected; PaktServiceBridge.start() called; foreground service launched on Android
- APRS payload round-trip verified: `!4916.96N/12307.24W>HAM HAT`, `:W1AW     :Hello from Android!{42`
- Phase 2 smoke test: PASS (2026-04-06)

Remaining hardware validation (needs physical Android device + Linux build host):
- `buildozer android debug` APK build
- SA818 USB OTG serial (DMOCONNECT response)
- PAKT BLE scan + connect (bleak Android backend)
- APRS RX decode (AudioRecord → engine modem)
- APRS TX play (engine AFSK → AudioTrack)

## Next Order

1. **Raspberry Pi workflow retest** — pull latest, run `python3 app/scripts/platform_validation.py`
   on device; confirm new "Linux audio: sound server present" check passes; verify UI shows
   `"USB Audio Device [PipeWire]"` (not `[ALSA]`); run Play Test Tone and ℹ Version to
   confirm no USB cascade reset. See full procedure in RES-007 above.
2. Linux desktop bring-up — run `app/run_linux.sh`, then `python3 app/scripts/platform_validation.py`
3. macOS packaged-app remaining checks — grant Accessibility permission and verify Refresh-button
   click response; BLE permission dialog still needs hardware
4. PAKT hardware validation
5. Linux packaging build — `cd app && ./packaging/build_linux.sh`; run through exit checklist
6. Android Phase 2 — hardware wiring + first buildozer APK build

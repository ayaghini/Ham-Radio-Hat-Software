# HAM HAT Control Center v4 - Project Component Map

This document is a fast onboarding map for the current `v4` Windows app.

## 1) What this app does

Desktop control center (Tkinter) for HAM HAT workflows:

- SA818 serial control (connect, configure, filters, tail, volume).
- DigiRig mode for APRS audio/PTT workflows without SA818 AT control.
- APRS direct/group messaging with optional reliable ACK/retry for direct messages.
- APRS RX monitor (one-shot + continuous), map plotting, and offline tile tools.
- Contacts/groups/heard/threaded comms workflows.
- Profile persistence/import/export and diagnostics launchers.

## 2) Runtime architecture

Primary pattern:

1. `HamHatApp` (UI thread) receives user actions from tab widgets.
2. UI snapshots current settings into plain values (`AppProfile` / `_TxSnapshot`).
3. Engine work runs in worker threads (`AprsEngine`, `RadioController`, `AudioRouter`).
4. Worker threads push typed events into a thread-safe queue.
5. UI thread drains queue every 40 ms and updates widgets.

Rule: engine threads must never touch Tkinter objects.

## 3) Active UI tabs in v4

- `MainTab` (`app/ui/main_tab.py`) - connection, hardware mode, radio controls, audio routing, PTT, control log.
- `CommsTab` (`app/ui/comms_tab.py`) - APRS RX controls, contacts/groups/heard, map, thread messaging, intro/position send, APRS log.
- `SetupTab` (`app/ui/setup_tab.py`) - advanced radio/audio/APRS tuning, profile actions, diagnostics, optional TTS toggle.

Note: `app/ui/aprs_tab.py` exists as legacy module but is not added to the notebook in `app/app.py`.

## 4) High-level file map

### Entry and root config

- `main.py`
  - CLI entrypoint, logging setup, launches `HamHatApp`.
- `VERSION`
  - Release version string displayed in title bar.
- `requirements.txt`
  - Runtime deps (`pyserial`, `numpy`, `sounddevice`, `sv-ttk`) and optional deps (`scipy`, `pycaw`).

### Application shell

- `app/app.py` (`HamHatApp`)
  - Main coordinator: UI build, callback wiring, queue dispatch, action handlers.
- `app/app_state.py` (`AppState`)
  - Shared container for engine instances, queue, and Tk variables.

### Engine layer (`app/engine`)

- `models.py` - shared dataclasses and typed contracts.
- `sa818_client.py` - low-level SA818 serial protocol and PTT line control.
- `radio_ctrl.py` - thread-safe SA818 facade with config push/pop restore.
- `audio_tools.py` - audio device enumeration and WAV utilities.
- `audio_router.py` - playback/capture orchestration and PTT-aware TX.
- `aprs_modem.py` - APRS payload builders/parsers and AX.25/AFSK DSP.
- `aprs_engine.py` - APRS TX/RX runtime, reliable messaging, monitor loop.
- `comms_mgr.py` - contacts/groups/heard/thread state and helper logic.
- `profile.py` - validated profile JSON load/save mapping.

### UI layer (`app/ui`)

- `main_tab.py` - active Control tab.
- `comms_tab.py` - active APRS Comms tab.
- `setup_tab.py` - active Setup tab.
- `widgets.py` - shared UI widgets (bounded log, map canvas, helpers).
- `events.py` - alternate event dataclasses (not the primary queue contract).

### Scripts (`scripts`)

- `bootstrap_third_party.py` - dependency/tool bootstrap helper.
- `two_radio_diagnostic.py` - two-radio APRS diagnostics.
- `play_wav_worker.py`, `capture_wav_worker.py`, `rx_score_worker.py`, `tx_wav_worker.py`
  - subprocess audio/PTT workers used by compatibility paths.
- `generate_agent_onboarding_pack.py` - regenerates AI onboarding artifacts.

## 5) Core flows

### Direct message TX flow

1. `CommsTab` send action calls `HamHatApp.send_aprs_message(...)`.
2. `HamHatApp` creates `_TxSnapshot`.
3. `CommsManager.build_direct_chunks(...)` splits text as needed.
4. `build_aprs_message_payload(...)` builds wire payload.
5. `AprsEngine.send_payload(...)` or `.send_reliable(...)` executes TX.

### Group message TX flow

1. `CommsTab` send action on active group thread.
2. `HamHatApp.send_group_message(...)` builds group wire payload chunks.
3. `AprsEngine.send_payload(...)` transmits each chunk (no reliable checkbox effect for groups).

### RX monitor flow

1. `HamHatApp.start_rx_monitor()` configures APRS-safe receive setup.
2. `AprsEngine.start_rx_monitor()` starts monitor thread.
3. RX audio capture -> trim/level/clip/waterfall callbacks -> decode.
4. Decoded packet event is marshaled to UI queue and handled by `HamHatApp._handle_packet()`.
5. Comms/map/log views update from packet content.

### Profile flow

1. `HamHatApp._collect_profile_snapshot()` gathers values from all active tabs.
2. `ProfileManager.save()` writes JSON.
3. `ProfileManager.load()` parses/clamps JSON into `AppProfile`.
4. `HamHatApp._apply_profile_to_tabs()` restores UI + comms state.

## 6) Task-to-file routing

- Radio connection/config issue:
  - `app/app.py`
  - `app/engine/radio_ctrl.py`
  - `app/engine/sa818_client.py`
- APRS encode/decode issue:
  - `app/engine/aprs_modem.py`
  - `app/engine/aprs_engine.py`
- Contacts/groups/thread issue:
  - `app/engine/comms_mgr.py`
  - `app/ui/comms_tab.py`
  - `app/app.py`
- Audio device/PTT issue:
  - `app/engine/audio_router.py`
  - `app/engine/audio_tools.py`
  - worker scripts under `scripts/`
- Profile persistence issue:
  - `app/engine/models.py`
  - `app/engine/profile.py`
  - tab `apply_profile` / `collect_profile` methods

## 7) Critical invariants

- No Tkinter updates from worker threads.
- Worker threads must operate on plain snapshots, not live Tk vars.
- APRS TX/RX temporary radio config must restore user config.
- `AppProfile` field changes require synchronized updates in:
  - `models.py`
  - `profile.py`
  - tab `apply_profile`/`collect_profile`
- Thread key consistency is required for Comms thread rendering/unread handling.

## 8) Contributor quick checks

After meaningful changes:

1. `python -m compileall -q .`
2. `python main.py --help`
3. If hardware is present: run connect/apply/send/monitor smoke checks.
4. Regenerate onboarding artifacts when architecture docs are changed:
   - `python scripts/generate_agent_onboarding_pack.py`

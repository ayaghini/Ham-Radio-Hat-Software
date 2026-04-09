# Session Handoff

Last updated: 2026-04-07

## Project Model

- Active app: `app/`
- Primary desktop entrypoint: `app/main.py`
- Main coordinator: `app/app/app.py` (`HamHatApp`)
- Shared state + engines: `app/app/app_state.py`
- Main architecture: Tkinter UI thread + worker-thread engines + typed event queue

## Hardware vs Software Boundary

### Software-controlled

- SA818 serial AT control:
  - connect/disconnect
  - frequency/offset/squelch/bandwidth
  - filters, tail, volume
- PTT control:
  - serial modem lines `RTS` / `DTR`
  - polarity (`active_high`)
  - pre/post timing
- APRS audio routing:
  - output device selection
  - input device selection
  - auto USB pair selection
  - test tone / APRS WAV playback
  - RX capture / decode

### Hardware-observed

- Whether the radio actually keys on PTT
- Whether the HT hears transmitted audio
- Whether the selected USB codec corresponds to the intended physical device
- Any EMI-related behavior on the physical hat/cabling/radio path

Software can drive the path, but end-to-end confirmation still requires operator observation on real hardware.

## File Ownership for PTT / Audio

- UI audio + PTT controls:
  - `app/app/ui/main_tab.py`
  - `app/app/ui/setup_tab.py`
- App orchestration:
  - `app/app/app.py`
- Audio runtime:
  - `app/app/engine/audio_router.py`
  - `app/app/engine/audio_tools.py`
- Radio/PTT runtime:
  - `app/app/engine/radio_ctrl.py`
  - `app/app/engine/sa818_client.py`
- APRS TX integration:
  - `app/app/engine/aprs_engine.py`

## Current Understanding

- PTT sequencing is implemented in `AudioRouter.play_with_ptt_blocking(...)`:
  - assert PTT
  - wait `pre_ms`
  - play audio
  - wait `post_ms`
  - release PTT
- Recent EMI-related edits were in audio refresh/selection handling, not in the core PTT sequence.
- Recent local fix added:
  - repeated audio refresh retries after connect/enable
  - clearing stale audio selections instead of silently choosing index 0
  - protection against stale retry timers
  - protection against auto-pair overwriting a live manual selection

## Current Live-Test Constraint

- The app can be launched and code paths can be inspected locally.
- End-to-end PTT/audio success cannot be confirmed from the terminal alone because:
  - the GUI still requires operator interaction
  - carrier/tone success is only visible on the physical radio / HT

## Recommended Next Resume Point

1. Launch `app/main.py`
2. Operator runs:
   - `Run PTT Diagnostics`
   - `Play Test Tone`
   - manual audio device change test
3. Record observed HT behavior:
   - first polarity keys or not
   - second polarity keys or not
   - test tone keys or not
   - tone heard or not
   - chosen TX/RX device names
   - whether manual selection sticks after 2 seconds
4. If PTT fails:
   - inspect selected `PTT line`, polarity, and hardware mode
   - confirm serial/PTT port path for `SA818` vs `DigiRig`
5. If audio fails:
   - inspect selected output/input names
   - compare auto-pair result against actual USB codec
   - trace `list_output_devices()` / `list_input_devices()` behavior on that host

## Verification Already Done

- Syntax verification passed:
  - `app/.venv/bin/python -m py_compile app/app/app.py app/app/ui/main_tab.py app/app/engine/audio_router.py app/app/engine/sa818_client.py`
- App runtime imports present:
  - `tkinter`
  - `sounddevice`
  - `serial`


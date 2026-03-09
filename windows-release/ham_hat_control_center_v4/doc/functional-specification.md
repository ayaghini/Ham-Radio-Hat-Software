# Functional Specification

Document owner: uConsole HAM HAT project
Document version: 1.1
Last updated: 2026-03-09

## 1. Purpose

Define required functional behavior for the current HAM HAT software packages:
- Windows package: `windows-release/ham_hat_control_center_v4`
- Raspberry Pi package: `pi-release/ham_hat_control_center`

This document reflects implemented behavior as of 2026-03-09.

## 2. Scope

In scope:
- SA818 serial control workflows.
- DigiRig audio/PTT workflows.
- Local desktop UI workflows.
- APRS TX/RX and APRS comms workflows (Windows package).
- Local profile persistence and import/export.
- Local diagnostics/bootstrap launchers.

Out of scope:
- Cloud APIs and remote control.
- Automated regulatory compliance enforcement.
- Hardware manufacturing process details.

## 3. System Context

Primary components:
- SA818 radio module (serial AT control path).
- Optional DigiRig interface (PTT serial + USB audio path).
- Host computer running Python/Tkinter app.

Primary interfaces:
- Serial AT command path to SA818.
- Serial modem-line path for PTT (`RTS`/`DTR`).
- Audio input/output selection for APRS AFSK workflows.
- Local filesystem profile storage (`profiles/last_profile.json`).

## 4. Platform and Dependency Requirements

Windows package:
- Python 3.10+
- `pyserial`, `numpy`, `sounddevice`, `sv-ttk`
- Optional: `scipy` (decode performance), `pycaw` (Windows OS level helpers)

Raspberry Pi package:
- Python 3.9+
- `pyserial`
- `python3-tk` installed on OS

## 5. User Roles

- Operator: performs normal radio/APRS/comms operations.
- Integrator/tester: validates cabling, PTT timing, audio routing, diagnostics.

## 6. Functional Requirements

### FR-01: Application Startup and UI
- The app shall open a desktop UI with three active tabs: `Control`, `APRS Comms`, and `Setup`.
- The app shall auto-load the last saved profile if present.
- The app shall show operational logs for user-visible feedback.

### FR-02: Hardware Mode Selection
- The app shall support `SA818` mode and `DigiRig` mode.
- In `SA818` mode, serial connect/disconnect/version workflows shall be available.
- In `DigiRig` mode, SA818 connect/version flows shall be bypassed with clear status text.

### FR-03: Serial Port Discovery and Connection
- The app shall list available serial ports.
- The app shall support manual connect/disconnect in `SA818` mode.
- The app shall support SA818 version read when connected.
- The app shall support auto-identify workflow:
  - `SA818` mode: probe and connect to first SA818 candidate.
  - `DigiRig` mode: identify likely non-SA818 PTT serial candidate.

### FR-04: Radio Parameter Programming (SA818)
- The app shall support frequency, offset, squelch, bandwidth, CTCSS TX/RX, and DCS TX/RX.
- The app shall reject invalid tone combinations.
- The app shall apply valid settings via SA818 AT command path.

### FR-05: Filter, Tail, and Volume Control (SA818)
- The app shall support filter flag application (pre/de-emphasis, high-pass, low-pass).
- The app shall support squelch tail mode apply.
- The app shall support SA818 volume in range 1..8.

### FR-06: Profile Persistence
- The app shall save current state to JSON profile.
- The app shall load profile JSON and restore settings across tabs.
- The app shall support explicit import/export profile actions.
- The app shall autosave current profile periodically.

### FR-07: Audio Playback and PTT Control (Windows)
- The app shall support TX audio playback to selected output device.
- The app shall optionally assert PTT during TX.
- PTT shall support `RTS`/`DTR`, active-high toggle, and pre/post delays.
- The app shall provide test tone playback and manual APRS packet playback.

### FR-08: Audio Device Management (Windows)
- The app shall list available audio input/output devices.
- The app shall support manual selection of TX output and RX input.
- The app shall support automatic USB TX/RX pair selection.
- The app shall support TX channel sweep and RX auto-detect helper.

### FR-09: APRS Direct Message TX (Windows)
- The app shall build and transmit APRS direct message payloads.
- APRS source/destination/path shall be configurable.
- TX tuning controls shall include gain, preamble flags, and repeat count.

### FR-10: Reliable APRS Direct Messaging (Windows)
- Reliable mode shall support message IDs, ACK wait, and retry loop.
- ACK timeout and retry count shall be user-configurable.
- Reliable mode shall apply to direct messages, not group sends.

### FR-11: APRS Position and Intro TX (Windows)
- The app shall send APRS position packets from decimal lat/lon.
- The app shall validate latitude and longitude ranges.
- The app shall support `@INTRO` discovery packets from current callsign/location/note.

### FR-12: APRS RX Decode and Monitor (Windows)
- The app shall support one-shot decode capture.
- The app shall support continuous monitor mode with configurable chunk duration.
- The app shall decode APRS/AX.25 packets and log decoded activity.
- The app shall support optional auto-ACK for direct messages.

### FR-13: APRS Comms Workflows (Windows)
- The app shall support contacts management.
- The app shall support groups with editable member lists.
- The app shall track heard stations.
- The app shall maintain thread-based message history with unread indicators.
- Send actions shall target the currently active thread.

### FR-14: Map and Tile Workflows (Windows)
- The app shall plot decoded APRS station positions on map canvas.
- The app shall support map clear and open-last-position in browser.
- The app shall support offline tile download for bounded region/zoom.

### FR-15: Logging and Error Handling
- User-facing operations shall emit status and log messages.
- Recoverable input/config failures shall show clear UI errors.
- Background worker failures shall be surfaced to UI logs/errors.

### FR-16: Optional Windows TTS Announcements
- The app shall support optional TTS announcements for received APRS messages.
- TTS shall be disabled by default and user-toggleable in Setup.

## 7. Data Requirements

Profile storage:
- UTF-8 JSON.
- Backward-compatible loading with defaults for missing keys.

Comms/APRS data:
- Direct APRS message body constrained to APRS wire limits.
- Group wire format: `@GRP/GROUP[/part/total]:text`.
- Intro wire format: `@INTRO/CALL/LAT/LON:note`.

## 8. Non-Functional Requirements

- UI responsiveness: long operations run in background threads.
- Main-thread safety: only UI thread may update Tkinter widgets.
- Operational visibility: status bar + logs for major actions.
- Local-first operation: no remote telemetry requirement.

## 9. Constraints and Known Limitations

- Raspberry Pi package is behind Windows v4 feature set.
- Advanced audio helpers are Windows-focused.
- Regulatory and band-plan compliance remains operator responsibility.

## 10. Verification Checklist

Minimum acceptance checks:
- SA818 connect/disconnect/version read.
- Radio/filter/tail/volume apply workflows.
- Profile save/load/import/export and autosave restore.
- APRS direct message TX and position/intro TX.
- Reliable mode ACK success and timeout/retry behavior.
- One-shot and continuous RX monitor decode.
- Contacts/groups/heard/thread behaviors.
- Audio mapping, TX sweep, and RX auto-detect helper.

## 11. Change Control

When behavior changes, update this document with:
- Date of change.
- Added/modified FR IDs.
- Any changed defaults, ranges, or platform boundaries.

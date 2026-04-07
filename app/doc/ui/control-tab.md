# Control Tab (`MainTab`)

## Connection

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Hardware Mode | Read-only combobox | `hardware_mode_var` | Switches between `uConsole_HAT`, `DigiRig`, and `PAKT` workflows and UI visibility. | Select the hardware path before connecting/transmitting. |
| Status text | Label | `status_var` | Mirrors app status messages. | Quick feedback for connect/TX/RX actions. |
| Serial Port | Read-only combobox | `port_var` -> `connect()` | SA818 COM port used in `uConsole_HAT` mode. Hidden in `DigiRig` and `PAKT` modes. | Pick the SA818 port for AT command control. |
| DigiRig PTT Port | Entry | `digirig_port_var` | Serial port used for DigiRig PTT keying. Hidden in `uConsole_HAT` and `PAKT` modes. | Enter or auto-identify DigiRig serial PTT port. |
| PAKT Device | Read-only combobox | `pakt_device_var` | BLE device selected for PAKT mode. Populated after ⬡ Scan BLE. | Pick the PAKT device to connect to. |
| ⚡ Enable HAT | Button | `enable_uconsole_hat()` | Asserts GPIO 23 to power the SA818 on the uConsole HAT. uConsole_HAT mode only. | Run once after booting if the radio does not respond. |
| ↺ Refresh | Button | `refresh_ports()` | Re-scans serial ports. | Click after plugging/unplugging USB serial devices. |
| ⬡ Auto-ID | Button | `auto_identify()` | `uConsole_HAT`: probes and connects to the first SA818. `DigiRig`: finds non-SA818 serial candidates, prefers CP210x/Silicon Labs, sets DigiRig PTT port. | Fast port discovery for both SA818-type hardware modes. |
| ▶ Connect | Button | `connect()` | `uConsole_HAT`: connects and applies radio config. `DigiRig`: informational only (no SA818 connect required). | Start the active hardware workflow. |
| ■ Disconnect | Button | `disconnect()` | `uConsole_HAT`: disconnects serial/rx monitor. `DigiRig`: no-op status message. | End SA818 session safely. |
| ℹ Version | Button | `read_version()` | Reads SA818 firmware version string. `uConsole_HAT` mode only. | Confirm SA818 module is responding. |
| ⬡ Scan BLE | Button | `pakt_scan()` | Scans for nearby PAKT BLE devices (10 s). PAKT mode only. | Populate the PAKT Device dropdown. |
| ▶ Connect (PAKT) | Button | `pakt_connect_selected()` | Connects to the selected PAKT BLE device. | Establish BLE link to PAKT node. |
| ■ Disconnect (PAKT) | Button | `pakt_disconnect()` | Disconnects active PAKT BLE link. | End PAKT session safely. |

> **Profile import / export** moved to the **Setup tab** (Profile Management section).

## Radio Parameters (uConsole_HAT only)

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Frequency (MHz) | Entry | `frequency_var` | Used in SA818 apply config. | Set operating frequency. |
| TX Offset (MHz) | Entry | `offset_var` | Used in SA818 apply config. `0.000` = simplex. | Set repeater shift if needed; leave at 0.000 for simplex. |
| Squelch (0–8) | Entry | `squelch_var` | Used in SA818 apply config. | Tune noise gate sensitivity. 0 = open squelch. |
| Bandwidth | Read-only combobox | `bandwidth_var` | Maps `Wide`/`Narrow` to SA818 config. | Match channel plan. Wide = 25 kHz, Narrow = 12.5 kHz. |
| ▶ Apply Radio | Button | `apply_radio()` | Applies frequency/offset/squelch/bandwidth plus tone/filter/volume from profile. Disabled in DigiRig mode. | Commit SA818 radio settings. |
| DigiRig mode hint | Label | UI-only text block | Replaces radio controls in DigiRig mode. | Reminds user that radio is programmed manually in DigiRig mode. |

## PAKT BLE (PAKT mode only)

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Address | Label | `pakt_address_var` | MAC/BLE address of the connected PAKT node. | Confirm which device is active. |
| Status | Label | `pakt_status_var` | Current BLE link state. | Monitor connection health. |
| Capabilities | Label | `pakt_capabilities_var` | Feature flags reported by the PAKT device. | Understand what the node supports. |
| Callsign | Entry | `pakt_callsign_var` | Station callsign written to PAKT config. | Set station identity. |
| SSID (0–15) | Entry | `pakt_ssid_var` | Station SSID; digits only, range 0–15. | Distinguish multiple stations at the same callsign. |
| Read Caps | Button | `pakt_read_capabilities()` | Queries PAKT device capabilities. | Refresh capabilities display. |
| Read Config | Button | `pakt_read_config()` | Reads current PAKT device config. | Verify device state. |
| Write Config | Button | `pakt_write_config()` | Writes callsign/SSID to PAKT device. | Commit station identity. |
| Send TX | Button | `pakt_send_tx_request()` | Sends a TX request over the BLE link. | Trigger a test transmission. |

## Audio Routing

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| TX Output | Read-only combobox | `audio_out_var` -> `set_output_device()` | Sets output device for APRS / test-tone TX playback. | Choose TX audio path. On Linux/RPi, prefer the `[PipeWire]` or `[PulseAudio]` entry. |
| RX Input | Read-only combobox | `audio_in_var` -> `set_input_device()` | Sets input device for APRS RX decode/monitoring. | Choose RX audio path. |
| ↺ Refresh Audio Devices | Button | `refresh_audio_devices()` | Re-enumerates OS audio devices. | Use after audio device changes. |
| ▶ Sweep TX Channels | Button | `tx_channel_sweep()` | Plays a tone sequence through TX output with PTT keying. | Validate TX route/channel. |
| ▶ Auto-Detect RX Input Level | Button | `auto_detect_rx()` | Captures a short sample and suggests OS mic gain level. | Fast RX level calibration. |

## PTT

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Key PTT during TX audio | Checkbutton | `ptt_enabled_var` | Enables/disables PTT keying during audio TX. | Disable for dry-run audio tests. |
| PTT Line | Read-only combobox | `ptt_line_var` | Selects `RTS` or `DTR` control line. | Match hardware wiring. |
| PTT Active High | Checkbutton | `ptt_active_high_var` | Sets PTT polarity. | Flip if keying polarity is reversed. |
| PTT Pre (ms) | Entry | `ptt_pre_ms_var` | Delay before TX audio starts. | Avoid clipping first symbols. |
| PTT Post (ms) | Entry | `ptt_post_ms_var` | Delay before unkey after TX audio ends. | Avoid clipping TX tail. |

## Radio Log

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Radio Log panel | `BoundedLog` | `append_log()` via app event queue | Shows connection/radio/APRS status lines and errors. | Primary low-level operational log on Control tab. |

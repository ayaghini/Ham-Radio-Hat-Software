# Control Tab (`MainTab`)

## Connection

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Hardware Mode | Read-only combobox | `hardware_mode_var` | Switches between `SA818` and `DigiRig` workflows and UI visibility. | Select the hardware path before connecting/transmitting. |
| Status text | Label | `status_var` | Mirrors app status messages. | Quick feedback for connect/TX/RX actions. |
| SA818 Serial Port | Read-only combobox | `port_var` -> `connect()` | SA818 COM port used in `SA818` mode. Hidden in `DigiRig` mode. | Pick the SA818 port for AT command control. |
| DigiRig PTT Port | Entry | `digirig_port_var` | Serial port used for DigiRig PTT keying. Hidden in `SA818` mode. | Enter or auto-identify DigiRig serial PTT port. |
| Refresh | Button | `refresh_ports()` | Re-scans serial ports. | Click after plugging/unplugging USB serial devices. |
| Auto Identify | Button | `auto_identify()` | `SA818`: probes and connects to first SA818. `DigiRig`: finds non-SA818 serial candidates, prefers CP210x/Silicon Labs, sets DigiRig PTT port. | Fast port discovery for both hardware modes. |
| Connect | Button | `connect()` | `SA818`: connects and applies radio config. `DigiRig`: informational only (no SA818 connect required). | Start the active hardware workflow. |
| Disconnect | Button | `disconnect()` | `SA818`: disconnects serial/rx monitor. `DigiRig`: no-op status message. | End SA818 session safely. |
| Read Version | Button | `read_version()` | Reads SA818 version in `SA818` mode only. | Confirm SA818 module is responding. |
| Import Profile | Button | `import_profile()` | Loads profile JSON and applies across tabs. | Restore saved station configuration. |
| Export Profile | Button | `export_profile()` | Saves full profile snapshot to JSON. | Backup/share setup. |

## Radio Parameters (SA818 only)

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Frequency (MHz) | Entry | `frequency_var` | Used in SA818 apply config. | Set operating frequency. |
| Offset (MHz) | Entry | `offset_var` | Used in SA818 apply config. | Set repeater shift if needed. |
| Squelch (0-8) | Entry | `squelch_var` | Used in SA818 apply config. | Tune noise gate sensitivity. |
| Bandwidth | Read-only combobox | `bandwidth_var` | Maps `Wide`/`Narrow` to SA818 config. | Match channel plan. |
| Apply Radio | Button | `apply_radio()` | Applies frequency/offset/squelch/bandwidth (+tone/filter/volume from profile). Disabled by mode logic in DigiRig. | Commit SA818 radio settings. |
| DigiRig mode hint | Label | UI-only text block | Replaces radio controls in DigiRig mode. | Reminds user that radio is programmed manually in DigiRig mode. |

## Audio Routing + Auto Detection

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Audio Output | Read-only combobox | `audio_out_var` -> `set_output_device()` | Sets output device for APRS/test-tone TX playback. | Choose TX audio path. |
| Audio Input | Read-only combobox | `audio_in_var` -> `set_input_device()` | Sets input device for APRS RX decode/monitoring. | Choose RX audio path. |
| Refresh Audio Devices | Button | `refresh_audio_devices()` | Re-enumerates OS audio devices. | Use after audio device changes. |
| Auto Find TX/RX Pair | Button | `auto_find_audio_pair()` | Auto-selects matching USB TX/RX device pair (SA818 USB audio or DigiRig USB PnP). | Quick audio routing setup. |
| TX Channel Announce Sweep | Button | `tx_channel_sweep()` | Plays tone sequence and keys PTT according to config. | Validate TX route/channel. |
| Auto Detect RX by Voice | Button | `auto_detect_rx()` | Captures short sample and suggests mic level target. | Fast RX level calibration. |
| Auto-select USB audio pair on connect | Checkbutton | `auto_audio_var` | Enables automatic USB pair selection at startup/connect flow. | Keep on for stable setups. |

## PTT

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Key PTT during TX audio | Checkbutton | `ptt_enabled_var` | Enables/disables PTT keying during audio TX. | Disable for dry-run audio tests. |
| PTT Line | Read-only combobox | `ptt_line_var` | Selects `RTS` or `DTR` control line. | Match hardware wiring. |
| PTT Active High | Checkbutton | `ptt_active_high_var` | Sets PTT polarity. | Flip if keying polarity is reversed. |
| PTT Pre (ms) | Entry | `ptt_pre_ms_var` | Delay before TX audio starts. | Avoid clipping first symbols. |
| PTT Post (ms) | Entry | `ptt_post_ms_var` | Delay before unkey after TX audio. | Avoid clipping TX tail. |

## Radio Log

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Radio Log panel | `BoundedLog` | `append_log()` via app event queue | Shows connection/radio/APRS status lines and errors. | Primary low-level operational log on Control tab. |

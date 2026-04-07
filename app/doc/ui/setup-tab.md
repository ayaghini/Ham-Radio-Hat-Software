# Setup Tab (`SetupTab`)

## Advanced Radio (SA818-focused)

### Audio Filters (SA818)

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Bypass Pre/De-emphasis | Checkbutton | `_filter_emphasis_var` -> `apply_filters()` | Sets SA818 pre/de-emphasis bypass flag. Bypasses the built-in pre/de-emphasis curve applied by the SA818. | Enable for flat-response data modes; leave unchecked for voice. |
| Bypass High-pass Filter | Checkbutton | `_filter_highpass_var` -> `apply_filters()` | Sets SA818 high-pass bypass flag. | Reduces filtering of modem tones below the voice passband. |
| Bypass Low-pass Filter | Checkbutton | `_filter_lowpass_var` -> `apply_filters()` | Sets SA818 low-pass bypass flag. | Preserves APRS tone content above the normal voice ceiling. |
| Apply Filters | Button | `_apply_filters()` | Applies all three filter bypass flags immediately on the connected SA818. | Commit filter settings. Radio must be connected. |

### Volume

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Volume slider (1–8) | Scale | `_volume_var` | Stores desired SA818 volume level; live readout label shows current value in bold as you drag. | Set target hardware speaker/line volume. |
| Set Volume | Button | `_set_volume()` | Applies the slider value (clamped 1–8) to the connected SA818. | Commit volume. Radio must be connected. |

### CTCSS / DCS Tones

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| CTCSS TX / RX | Comboboxes | `_ctcss_tx_var`, `_ctcss_rx_var` | Persisted in profile and applied on ▶ Apply Radio. | Configure analog sub-audible access tones. |
| DCS TX / RX | Entries | `_dcs_tx_var`, `_dcs_rx_var` | Persisted in profile and applied on ▶ Apply Radio. | Configure digital coded squelch. |

### Squelch Tail

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Open squelch tail | Checkbutton | `_open_tail_var` | Selects desired tail mode (open vs. tight). | Choose tail behavior before apply. |
| Apply Tail | Button | `_apply_tail()` -> `apply_tail()` | Sends tail command to SA818 immediately. | Commit tail setting. Radio must be connected. |

## Shared Configuration Blocks

These controls are bound to shared app vars and affect runtime behavior across tabs.

### PTT Configuration

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| PTT Enabled | Checkbutton | `ptt_enabled_var` | Global TX PTT enable/disable. | Toggle keying for all TX workflows. |
| Line | Combobox | `ptt_line_var` | Selects `RTS` or `DTR`. | Match interface wiring. |
| Active High | Checkbutton | `ptt_active_high_var` | Global PTT polarity. | Correct inverted keying behavior. |
| Pre-delay / Post-delay | Spinboxes | `ptt_pre_ms_var`, `ptt_post_ms_var` | Global TX keying timing (ms). | Prevent packet clipping at start and end. |

### APRS TX Advanced

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Destination | Entry | `aprs_dest_var` | APRS destination field. | Override default `APRS` when needed. |
| Path | Entry | `aprs_path_var` | APRS path field. | Set digipeater path. |
| Re-program radio before each TX | Checkbutton | `aprs_reinit_var` | Enables optional SA818 re-init before each APRS TX. | Use for unstable radio link behavior. |
| Preamble flags | Spinbox | `aprs_preamble_var` | Number of opening HDLC flags before payload. | Improve receiver sync on weak links. |
| TX repeats | Spinbox | `aprs_repeats_var` | Number of packet repeats per send action. | Increase reliability (more airtime). |
| TX gain | Spinbox | `aprs_tx_gain_var` | AFSK output amplitude scale. | Balance decode reliability vs. clipping. |
| ACK timeout | Spinbox | `aprs_ack_timeout_var` | Reliable-send timeout per attempt (s). | Tune for link latency/noise. |
| ACK retries | Spinbox | `aprs_ack_retries_var` | Number of reliable-message retry attempts. | Tune reliable-message persistence. |

### APRS RX Advanced

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Monitor duration (s) | Spinbox | `aprs_rx_dur_var` | One-shot capture duration. | Control one-shot decode window. |
| Chunk size (s) | Spinbox | `aprs_rx_chunk_var` | Continuous monitor chunk duration. | Tradeoff latency vs. decode robustness. |
| Trim threshold (dB) | Spinbox | `aprs_rx_trim_var` | RX DSP trim threshold. | Reduce overload artifact before decode. |
| OS mic level (0–100) | Spinbox | `aprs_rx_os_level_var` | Stored target for host mic level helper. | Set/maintain RX input gain target. |

## Audio Tools

### Test Tone

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Frequency (Hz) | Spinbox | `_tone_freq_var` | Sets generated tone frequency. | Choose test tone frequency. |
| Duration (s) | Spinbox | `_tone_duration_var` | Sets playback duration. | Choose test length. |
| ▶ Play Test Tone | Button | `_play_test_tone()` | Plays tone on the selected TX output with current PTT settings. | Validate TX path and keying. |
| ■ Stop Audio | Button | `_stop_audio()` | Stops active audio playback immediately. | Abort ongoing playback. |

### Manual APRS Packet

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Packet text | Entry | `_manual_aprs_var` | Text used to build a manual APRS test packet WAV. | Set custom test payload. |
| Encode & Play (no PTT) | Button | `_play_manual_aprs()` | Encodes and plays APRS packet with PTT disabled. | Dry-run modem/audio validation without keying. |

### Audio Routing Helpers

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| ▶ Run TX Channel Sweep | Button | `_tx_channel_sweep()` | Plays a sweep of tones through the TX output and listens on RX input to confirm the audio loopback path. | Find the correct TX/RX device pair for a new radio setup. |
| ▶ Auto-detect RX Level | Button | `_auto_detect_rx()` | Captures a sample from the RX input and suggests an OS microphone gain level for optimal APRS decode SNR. | Fast receive gain setup after first connection. |

### PTT Diagnostics

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Description label | Label | UI-only | Explains that the configured PTT line will be tested in both polarities (active-high then active-low, 1.5 s each). | Inform operator of what the test does before running. |
| ▶ Run PTT Diagnostics | Button | `_ptt_diagnostics()` | Tests the PTT line set in the active Profile in both polarities (active-high, then active-low), 1.5 s each. Publishes results to the status bar. uConsole_HAT mode only. | Identify the correct PTT polarity for your hardware by watching your radio for a carrier. |

> **Safety note**: Only the line configured in your Profile is tested. The other modem-control line is intentionally not probed because exercising it can reset composite USB radio interfaces (e.g., the DigiRig). If you need to test the other line, change the Profile setting first.

## Profile Management

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Save Profile... | Button | `_save_profile()` -> `save_profile(path)` | Saves full profile to a selected JSON file. | Persist station configuration. |
| Load Profile... | Button | `_load_profile()` -> `load_profile(path)` | Loads a selected profile JSON into app state. | Restore a known configuration. |
| Reset Defaults | Button | `_reset_defaults()` | Resets app profile to defaults after confirmation dialog. | Return to baseline. |

## Bootstrap and Optional TTS

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Install / Update Dependencies | Button | `_bootstrap()` -> `run_bootstrap()` | Launches bootstrap script in a new console. | Install or update helper dependencies (e.g., after a `git pull`). |
| Run Two-Radio Diagnostic | Button | `_two_radio_diagnostic()` | Launches diagnostic script in a new console. | Troubleshoot dual-radio / USB cascade setups. |
| Announce received APRS messages via TTS | Checkbutton | `tts_enabled` property used by app message handler | Enables Windows SpeechSynthesizer announcements for received APRS messages. | Audible message notifications on Windows. |

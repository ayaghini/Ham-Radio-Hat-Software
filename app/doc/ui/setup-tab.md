# Setup Tab (`SetupTab`)

## Advanced Radio (SA818-focused)

### Audio Filters (SA818)

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Disable Pre/De-emphasis | Checkbutton | `_filter_emphasis_var` -> `apply_filters()` | Sets SA818 pre/de-emphasis disable flag. | Keep flatter response for data modes. |
| Disable High-pass Filter | Checkbutton | `_filter_highpass_var` -> `apply_filters()` | Sets SA818 high-pass disable flag. | Reduce filtering of modem tones. |
| Disable Low-pass Filter | Checkbutton | `_filter_lowpass_var` -> `apply_filters()` | Sets SA818 low-pass disable flag. | Preserve APRS tone content. |
| Apply Filters | Button | `_apply_filters()` | Applies all filter flags immediately on connected SA818. | Commit filter settings. |

### Volume

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Volume slider (1-8) | Scale | `_volume_var` | Stores desired SA818 volume level. | Set target hardware volume. |
| Set Volume | Button | `_set_volume()` | Applies clamped SA818 volume. | Commit volume setting. |

### CTCSS / DCS Tones

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| CTCSS TX / RX | Comboboxes | `_ctcss_tx_var`, `_ctcss_rx_var` | Persisted in profile and used on radio apply. | Configure analog access tones. |
| DCS TX / RX | Entries | `_dcs_tx_var`, `_dcs_rx_var` | Persisted in profile and used on radio apply. | Configure digital coded squelch. |

### Squelch Tail

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Open squelch tail | Checkbutton | `_open_tail_var` | Selects desired tail mode value. | Choose tail behavior before apply. |
| Apply Tail | Button | `_apply_tail()` -> `apply_tail()` | Sends tail command to SA818 immediately. | Commit tail setting. |

## Shared Configuration Blocks

These controls are bound to shared app vars and affect runtime behavior across tabs.

### PTT Configuration

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| PTT Enabled | Checkbutton | `ptt_enabled_var` | Global TX PTT enable. | Toggle keying for all TX workflows. |
| Line | Combobox | `ptt_line_var` | Selects `RTS`/`DTR`. | Match interface wiring. |
| Active High | Checkbutton | `ptt_active_high_var` | Global PTT polarity. | Correct inverted keying behavior. |
| Pre-delay / Post-delay | Spinboxes | `ptt_pre_ms_var`, `ptt_post_ms_var` | Global TX keying timing. | Prevent packet clipping. |

### APRS TX Advanced

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Destination | Entry | `aprs_dest_var` | APRS destination field. | Override default `APRS` when needed. |
| Path | Entry | `aprs_path_var` | APRS path field. | Set digipeater path. |
| Re-program radio before each TX | Checkbutton | `aprs_reinit_var` | Enables optional SA818 re-init before APRS TX. | Use for unstable radio link behavior. |
| Preamble flags | Spinbox | `aprs_preamble_var` | Number of opening flags before payload. | Improve receiver sync in weak links. |
| TX repeats | Spinbox | `aprs_repeats_var` | Number of repeats per send action. | Increase reliability (more airtime). |
| TX gain | Spinbox | `aprs_tx_gain_var` | AFSK output amplitude scale. | Balance decode reliability vs clipping. |
| ACK timeout | Spinbox | `aprs_ack_timeout_var` | Reliable-send timeout per attempt. | Tune for link latency/noise. |
| ACK retries | Spinbox | `aprs_ack_retries_var` | Number of retry attempts. | Tune reliable-message persistence. |

### APRS RX Advanced

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Monitor duration (s) | Spinbox | `aprs_rx_dur_var` | One-shot capture duration. | Control one-shot decode window. |
| Chunk size (s) | Spinbox | `aprs_rx_chunk_var` | Continuous monitor chunk duration. | Tradeoff latency vs decode robustness. |
| Trim threshold (dB) | Spinbox | `aprs_rx_trim_var` | RX DSP trim threshold. | Reduce overload before decode. |
| OS mic level (0-100) | Spinbox | `aprs_rx_os_level_var` | Stored target for host mic level helper. | Set/maintain RX input gain target. |

## Audio Tools

### Test Tone

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Frequency (Hz) | Spinbox | `_tone_freq_var` | Sets generated tone frequency. | Choose test tone frequency. |
| Duration (s) | Spinbox | `_tone_duration_var` | Sets playback duration. | Choose test length. |
| Play Test Tone | Button | `_play_test_tone()` | Plays tone on selected output with current PTT settings. | Validate TX path/keying. |
| Stop Audio | Button | `_stop_audio()` | Stops active audio playback. | Abort ongoing playback quickly. |

### Manual APRS Packet

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Packet text | Entry | `_manual_aprs_var` | Text used to build manual APRS test packet WAV. | Set custom test payload. |
| Encode & Play (no PTT) | Button | `_play_manual_aprs()` | Encodes and plays APRS packet with PTT disabled. | Dry-run modem/audio validation. |

### TX/RX Helpers

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Run TX Channel Sweep | Button | `_tx_channel_sweep()` | Runs 1200-2200 Hz sweep for channel/routing checks. | Find correct TX path. |
| Auto-detect RX Level | Button | `_auto_detect_rx()` | Captures sample audio and suggests RX mic level. | Fast receive gain setup. |

## Profile, Bootstrap, and Optional TTS

| Element | Type | Connected code | What it actually does | Purpose and how to use |
|---|---|---|---|---|
| Save Profile... | Button | `_save_profile()` -> `save_profile(path)` | Saves full profile to selected JSON file. | Persist station configuration. |
| Load Profile... | Button | `_load_profile()` -> `load_profile(path)` | Loads selected profile JSON into app state. | Restore known configuration. |
| Reset Defaults | Button | `_reset_defaults()` | Resets app profile to defaults after confirmation. | Return to baseline. |
| Install / Update Dependencies | Button | `_bootstrap()` -> `run_bootstrap()` | Launches bootstrap script in a new console. | Install/update helper dependencies. |
| Run Two-Radio Diagnostic | Button | `_two_radio_diagnostic()` | Launches diagnostic script in a new console. | Troubleshoot dual-radio setups. |
| Announce received APRS messages via TTS | Checkbutton | `tts_enabled` property used by app message handler | Enables Windows SpeechSynthesizer announcements for received APRS messages. | Audible message notifications. |

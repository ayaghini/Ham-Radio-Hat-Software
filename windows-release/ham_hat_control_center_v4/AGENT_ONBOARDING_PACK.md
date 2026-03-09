# Agent Onboarding Pack

This file is generated. Rebuild with:
`python scripts/generate_agent_onboarding_pack.py`

## Project Snapshot

- Project: `HAM HAT Control Center v4`
- Python files indexed: `28`
- Top-level functions: `115`
- Classes: `64`
- Class methods: `350`

## Fast Read Order

- `main.py`
- `app/app.py`
- `app/app_state.py`
- `app/engine/models.py`
- `app/engine/aprs_engine.py`
- `app/engine/aprs_modem.py`
- `app/engine/radio_ctrl.py`
- `app/engine/sa818_client.py`
- `app/ui/main_tab.py`
- `app/ui/comms_tab.py`
- `app/ui/setup_tab.py`

## Component File Lists

### app_core

- `app/__init__.py`
- `app/app.py`
- `app/app_state.py`

### engine

- `app/engine/__init__.py`
- `app/engine/aprs_engine.py`
- `app/engine/aprs_modem.py`
- `app/engine/audio_router.py`
- `app/engine/audio_tools.py`
- `app/engine/comms_mgr.py`
- `app/engine/models.py`
- `app/engine/profile.py`
- `app/engine/radio_ctrl.py`
- `app/engine/sa818_client.py`
- `app/engine/tile_provider.py`

### ui

- `app/ui/__init__.py`
- `app/ui/aprs_tab.py`
- `app/ui/comms_tab.py`
- `app/ui/events.py`
- `app/ui/main_tab.py`
- `app/ui/setup_tab.py`
- `app/ui/widgets.py`

### scripts

- `scripts/bootstrap_third_party.py`
- `scripts/capture_wav_worker.py`
- `scripts/generate_agent_onboarding_pack.py`
- `scripts/play_wav_worker.py`
- `scripts/rx_score_worker.py`
- `scripts/two_radio_diagnostic.py`
- `scripts/tx_wav_worker.py`

### entry


## Class and Function Index

### app/__init__.py

- Size: `1 lines`, `0 bytes`

### app/app.py

- Module: HamHatApp — main application window.
- Size: `1576 lines`, `64279 bytes`
- Constants: `_VERSION_FILE`
- Classes:
  - `_LogEvt`  [L75]
  - `_AprsLogEvt`  [L77]
  - `_ErrorEvt`  [L79]
  - `_ConnectEvt`  [L81]
  - `_DisconnectEvt`  [L83]
  - `_PacketEvt`  [L85]
  - `_AudioPairEvt`  [L87]
  - `_InputLevelEvt`  [L89]
  - `_OutputLevelEvt`  [L91]
  - `_WaterfallEvt`  [L93]
  - `_RxClipEvt`  [L95]
  - `_HeardEvt`  [L97]
  - `_ChatMsgEvt`  [L99]
  - `_ContactsEvt`  [L101]
  - `_StatusEvt`  [L103]
  - `_SuggestRxOsLevelEvt`  [L105]
  - `HamHatApp` (tk.Tk)  [L108]
    - `__init__(self, app_dir)`  [L115]
    - `_build_ui(self)`  [L208]
    - `_wire_callbacks(self)`  [L251]
    - `_wire_comms(self)`  [L268]
    - `_drain_queue(self)`  [L279]
    - `_dispatch(self, evt)`  [L289]
    - `_vis_tick(self)`  [L356]
    - `_on_tab_changed(self, _e)`  [L373]
    - `_startup_auto_tasks(self)`  [L383]
    - `_auto_find_audio_background(self)`  [L391]
    - `_hw_mode(self)`  [L417]
    - `connect(self, port)`  [L425]
    - `_apply_radio_after_connect(self)`  [L448]
    - `disconnect(self)`  [L452]
    - `scan_ports(self)`  [L466]
    - `auto_identify_and_connect(self)`  [L474]
    - `apply_radio(self)`  [L562]
    - `_apply_radio_config(self, p)`  [L573]
    - `apply_filters(self, emphasis, highpass, lowpass)`  [L603]
    - `set_volume(self, level)`  [L618]
    - `apply_tail(self, open_tail)`  [L633]
    - `refresh_audio_devices(self)`  [L652]
    - `auto_find_audio_pair(self)`  [L658]
    - `stop_audio(self)`  [L661]
    - `set_output_device(self, idx, name)`  [L665]
    - `set_input_device(self, idx, name)`  [L669]
    - `apply_callsign_preset(self, src, dst)`  [L677]
    - `send_aprs_message(self, to, text, reliable)`  [L681]
    - `_send_aprs_message_impl(self, to, text, reliable)`  [L693]
    - `send_direct_message(self, to, text, reliable)`  [L725]
    - `send_aprs_position(self)`  [L729]
    - `apply_os_rx_level(self)`  [L740]
    - `on_rx_auto_toggle(self)`  [L745]
    - `rx_one_shot(self)`  [L752]
    - `aprs_log(self, msg)`  [L756]
    - `send_group_message(self, group, text)`  [L760]
    - `send_position(self, lat, lon, comment)`  [L781]
    - `send_intro(self, note)`  [L796]
    - `start_rx_monitor(self)`  [L811]
    - `stop_rx_monitor(self)`  [L834]
    - `one_shot_rx(self)`  [L840]
    - `play_test_tone(self, freq, duration)`  [L851]
    - `play_manual_aprs_packet(self, text)`  [L858]
    - `tx_channel_sweep(self)`  [L886]
    - `auto_detect_rx(self)`  [L941]
    - `_handle_packet(self, pkt)`  [L977]
    - `add_contact(self, call)`  [L1059]
    - `remove_contact(self, call)`  [L1062]
    - `import_heard_to_contacts(self)`  [L1065]
    - `clear_heard(self)`  [L1068]
    - `set_group(self, name, members)`  [L1072]
    - `delete_group(self, name)`  [L1075]
    - `save_profile(self, path)`  [L1082]
    - `load_profile(self, path)`  [L1096]
    - `import_profile(self)`  [L1105]
    - `export_profile(self)`  [L1117]
    - `reset_defaults(self)`  [L1130]
    - `_load_and_apply_profile(self)`  [L1134]
    - `_apply_profile_to_tabs(self, p)`  [L1138]
    - `_restore_audio_from_profile(self, p)`  [L1152]
    - `_collect_profile_snapshot(self)`  [L1167]
    - `_get_current_profile(self)`  [L1180]
    - `_autosave(self)`  [L1187]
    - `_make_tx_snapshot(self)`  [L1198]
    - `_make_ptt_config(self)`  [L1271]
    - `_apply_os_rx_level(self, level)`  [L1287]
    - `_apply_os_tx_level(self, level)`  [L1373]
    - `_tts_announce(self, source, text)`  [L1460]
    - `run_bootstrap(self)`  [L1490]
    - `run_two_radio_diagnostic(self)`  [L1501]
    - `refresh_ports(self)`  [L1516]
    - `auto_identify(self)`  [L1524]
    - `read_version(self)`  [L1528]
    - `_set_status(self, text)`  [L1544]
    - `_on_close(self)`  [L1552]
- Top-level functions:
  - `_read_version()`  [L63]

### app/app_state.py

- Module: AppState — shared application state (tk.Var containers + engine instances).
- Size: `83 lines`, `3776 bytes`
- Classes:
  - `AppState`  [L18]
    - `__init__(self, app_dir)`  [L21]

### app/engine/__init__.py

- Size: `1 lines`, `0 bytes`

### app/engine/aprs_engine.py

- Module: AprsEngine: manages APRS TX, RX monitor, and reliable messaging.
- Size: `814 lines`, `32126 bytes`
- Classes:
  - `_TxSnapshot`  [L58]
    - `__init__(self, source, destination, path, gain, preamble_flags, trailing_flags, repeats, out_dev, ptt, radio, volume, reinit, port, hw_mode, ptt_serial_port)`  [L67]
  - `AprsEngine`  [L102]
    - `__init__(self, radio, audio, audio_dir)`  [L108]
    - `on_log(self, cb)`  [L148]
    - `on_aprs_log(self, cb)`  [L151]
    - `on_error(self, cb)`  [L154]
    - `on_packet(self, cb)`  [L157]
    - `on_ack_tx(self, cb)`  [L160]
    - `on_output_level(self, cb)`  [L163]
    - `on_input_level(self, cb)`  [L166]
    - `on_waterfall(self, cb)`  [L169]
    - `on_rx_clip(self, cb)`  [L172]
    - `send_payload(self, payload, snap)`  [L179]
    - `send_payload_blocking(self, payload, snap)`  [L184]
    - `_tx_worker(self, payload, snap)`  [L188]
    - `_do_tx(self, payload, snap, attempt)`  [L200]
    - `_do_tx_digirig(self, payload, snap, attempt)`  [L273]
    - `send_reliable(self, addressee, text, snap, message_id, timeout_s, retries)`  [L334]
    - `_reliable_worker(self, addressee, text, snap, message_id, timeout_s, retries)`  [L351]
    - `note_ack(self, message_id)`  [L379]
    - `_wait_ack(self, message_id, timeout_s)`  [L387]
    - `new_message_id()`  [L404]
    - `play_test_tone(self, freq_hz, duration_s, out_dev, ptt, ptt_cb, ptt_serial_port)`  [L411]
    - `rx_running(self)`  [L471]
    - `start_rx_monitor(self, in_dev, chunk_s, trim_db, aprs_radio, hw_mode)`  [L474]
    - `stop_rx_monitor(self)`  [L533]
    - `_rx_loop(self, in_dev, chunk_s, trim_db)`  [L561]
    - `_decode_loop(self, chunk_s)`  [L616]
    - `one_shot_decode(self, in_dev, duration_s, trim_db)`  [L674]
    - `handle_received_packet(self, pkt, local_calls, auto_ack, snap)`  [L714]
    - `_dispatch_auto_ack(self, addressee, msg_id, snap)`  [L779]
    - `_log(self, msg)`  [L797]
    - `_aprs_log(self, msg)`  [L801]
- Top-level functions:
  - `_apply_trim_db(mono, trim_db)`  [L810]

### app/engine/aprs_modem.py

- Module: APRS payload helpers and AX.25/AFSK modem.
- Size: `799 lines`, `27772 bytes`
- Constants: `APRS_MESSAGE_BODY_MAX, APRS_MESSAGE_TEXT_MAX, APRS_POSITION_COMMENT_MAX, FLAG_BITS, GROUP_WIRE_RE, INTRO_WIRE_RE, _CRC16_TABLE, _FLAG_ARR, _LSB_WEIGHTS`
- Top-level functions:
  - `build_ax25_ui_frame(source, destination, path_via, info)`  [L65]
  - `frame_to_bitstream(frame, preamble_flags, trailing_flags)`  [L86]
  - `nrzi_encode(bits)`  [L106]
  - `afsk_from_nrzi(nrzi, sample_rate, tx_gain)`  [L116]
  - `write_aprs_wav(path, source, destination, message, path_via, sample_rate, tx_gain, preamble_flags, trailing_flags)`  [L171]
  - `write_test_tone_wav(path, frequency_hz, seconds, sample_rate)`  [L191]
  - `build_aprs_message_payload(addressee, text, message_id)`  [L205]
  - `build_aprs_ack_payload(addressee, message_id)`  [L213]
  - `build_aprs_position_payload(lat_deg, lon_deg, comment, symbol_table, symbol)`  [L221]
  - `build_group_wire_text(group, body, part, total)`  [L238]
  - `build_intro_wire_text(callsign, lat, lon, note)`  [L256]
  - `split_text_for_group(text, group)`  [L271]
  - `split_aprs_text_chunks(text, max_len)`  [L280]
  - `_split_chunks(body, limit)`  [L285]
  - `parse_aprs_message_info(info)`  [L309]
  - `parse_aprs_position_info(info, destination)`  [L329]
  - `_parse_compressed_position(payload)`  [L360]
  - `_mic_e_digit_flag(c)`  [L382]
  - `_parse_mice_position(dest, info)`  [L391]
  - `parse_group_wire_text(text)`  [L431]
  - `parse_intro_wire_text(text)`  [L442]
  - `decode_ax25_from_wav(path)`  [L459]
  - `decode_ax25_from_samples(rate, mono)`  [L464]
  - `_build_crc16_table()`  [L510]
  - `crc16_x25(data)`  [L526]
  - `_write_pcm16_mono(path, sample_rate, data)`  [L537]
  - `_read_wav_mono(path)`  [L548]
  - `_byte_lsb(value)`  [L562]
  - `_encode_ax25_addr(value, is_last)`  [L566]
  - `_decode_addr(adr)`  [L582]
  - `_format_lat(lat)`  [L588]
  - `_format_lon(lon)`  [L596]
  - `_parse_aprs_lat(token)`  [L604]
  - `_parse_aprs_lon(token)`  [L619]
  - `_lowpass_kernel(rate, cutoff_hz, taps)`  [L637]
  - `_preprocess_samples(samples, rate)`  [L650]
  - `_afsk_discriminator(samples, rate, mark_hz, space_hz)`  [L667]
  - `_extract_nrzi_levels(demod, spb, offset, invert_tones)`  [L687]
  - `_nrzi_to_bits(levels)`  [L699]
  - `_extract_hdlc_frames(bits)`  [L712]
  - `_remove_bit_stuffing(bits)`  [L736]
  - `_bits_to_bytes_lsb(bits)`  [L761]
  - `_decode_ax25_frame(frame)`  [L769]

### app/engine/audio_router.py

- Module: AudioRouter: device selection, PTT integration, and playback management.
- Size: `288 lines`, `10849 bytes`
- Classes:
  - `AudioRouter`  [L37]
    - `__init__(self, app_dir)`  [L40]
    - `set_log_cb(self, cb)`  [L48]
    - `_log(self, msg)`  [L51]
    - `refresh_output_devices(self)`  [L59]
    - `refresh_input_devices(self)`  [L62]
    - `auto_select_usb_pair(self, out_hint, in_hint)`  [L69]
    - `worker_busy(self)`  [L148]
    - `stop_audio(self)`  [L151]
    - `play_with_ptt_blocking(self, wav_path, out_dev, ptt, ptt_cb)`  [L159]
    - `capture_compatible(self, seconds, device_index, wav_out_path)`  [L198]
    - `record_compatible(self, wav_path, seconds, device_index)`  [L230]
    - `tx_active(self)`  [L245]
    - `tx_level_hold(self)`  [L249]
- Top-level functions:
  - `_play_wav_subprocess(wav_path, device_index, app_dir)`  [L257]
  - `_capture_wav_subprocess(wav_path, seconds, device_index, app_dir)`  [L271]

### app/engine/audio_tools.py

- Module: Audio I/O helpers for playback, recording, and device enumeration.
- Size: `260 lines`, `9533 bytes`
- Top-level functions:
  - `_list_devices(direction)`  [L35]
  - `list_output_devices()`  [L86]
  - `list_input_devices()`  [L90]
  - `play_wav(path, device_index)`  [L98]
  - `play_wav_blocking(path, device_index)`  [L110]
  - `play_wav_blocking_compatible(path, device_index)`  [L122]
  - `stop_playback()`  [L169]
  - `record_wav(path, seconds, device_index, sample_rate)`  [L183]
  - `capture_samples(seconds, device_index, sample_rate)`  [L196]
  - `wav_duration_seconds(path)`  [L214]
  - `estimate_wav_level(path)`  [L221]
  - `_load_wav_as_int16(path)`  [L239]
  - `_write_pcm16_mono(path, sample_rate, data)`  [L253]

### app/engine/comms_mgr.py

- Module: CommsManager: contacts, groups, and chat thread logic.
- Size: `270 lines`, `9692 bytes`
- Classes:
  - `CommsManager`  [L23]
    - `__init__(self)`  [L26]
    - `on_contacts_changed(self, cb)`  [L45]
    - `on_message_added(self, cb)`  [L48]
    - `on_heard_changed(self, cb)`  [L51]
    - `contacts(self)`  [L59]
    - `add_contact(self, call)`  [L62]
    - `remove_contact(self, call)`  [L71]
    - `ensure_contact(self, call)`  [L80]
    - `add_heard_to_contacts(self)`  [L83]
    - `groups(self)`  [L97]
    - `set_group(self, name, members)`  [L100]
    - `delete_group(self, name)`  [L107]
    - `heard(self)`  [L119]
    - `note_heard(self, call)`  [L122]
    - `clear_heard(self)`  [L129]
    - `messages(self)`  [L139]
    - `add_message(self, msg)`  [L142]
    - `mark_delivered(self, msg_id)`  [L149]
    - `messages_for_thread(self, thread_key)`  [L164]
    - `all_thread_keys(self)`  [L167]
    - `unread_for_thread(self, thread_key)`  [L174]
    - `set_active_thread(self, thread_key)`  [L177]
    - `active_thread(self)`  [L182]
    - `last_direct_sender(self)`  [L186]
    - `set_last_direct_sender(self, call)`  [L189]
    - `build_direct_chunks(self, text)`  [L196]
    - `build_group_chunks(self, group, text)`  [L200]
    - `build_intro_payload(self, callsign, lat, lon, note)`  [L208]
    - `should_process_intro(self, src_call, lat, lon, note)`  [L215]
    - `infer_thread_key(self, src, dst, text, local_calls)`  [L226]
    - `to_dict(self)`  [L244]
    - `from_dict(self, data)`  [L250]
- Top-level functions:
  - `_norm_call(token)`  [L267]

### app/engine/models.py

- Module: Shared dataclasses, enums, and type aliases used across the engine layer.
- Size: `204 lines`, `5522 bytes`
- Constants: `MSG_ID_COUNTER`
- Classes:
  - `RadioConfig`  [L16]
    - `clone(self)`  [L26]
  - `DecodedPacket`  [L44]
  - `AprsConfig`  [L53]
  - `ReliableConfig`  [L66]
  - `PttConfig`  [L78]
  - `AudioConfig`  [L87]
  - `ChatMessage`  [L99]
  - `_MsgIdCounter`  [L114]
    - `__init__(self)`  [L115]
    - `next(self)`  [L119]
  - `AppProfile`  [L133]

### app/engine/profile.py

- Module: ProfileManager: validated load/save of AppProfile to JSON.
- Size: `199 lines`, `8767 bytes`
- Classes:
  - `ProfileManager`  [L24]
    - `__init__(self, profile_path)`  [L25]
    - `path(self)`  [L29]
    - `save(self, profile)`  [L32]
    - `load(self)`  [L37]
- Top-level functions:
  - `_profile_to_dict(p)`  [L52]
  - `_dict_to_profile(d)`  [L108]

### app/engine/radio_ctrl.py

- Module: RadioController: thread-safe radio state manager with save/restore.
- Size: `157 lines`, `5831 bytes`
- Classes:
  - `RadioController`  [L21]
    - `__init__(self)`  [L22]
    - `set_on_connect(self, cb)`  [L34]
    - `set_on_disconnect(self, cb)`  [L37]
    - `connected(self)`  [L45]
    - `client(self)`  [L49]
    - `connect(self, port, baud, timeout)`  [L56]
    - `disconnect(self)`  [L64]
    - `probe_and_connect(self, port, baud, timeout)`  [L72]
    - `apply_config(self, cfg)`  [L87]
    - `push_config(self, cfg)`  [L94]
    - `pop_config(self)`  [L108]
    - `has_saved_config(self)`  [L121]
    - `set_volume(self, level)`  [L129]
    - `set_filters(self, disable_emphasis, disable_highpass, disable_lowpass)`  [L133]
    - `set_tail(self, open_tail)`  [L137]
    - `version(self)`  [L141]
    - `set_ptt(self, enabled, line, active_high)`  [L145]
    - `release_ptt(self, line, active_high)`  [L149]

### app/engine/sa818_client.py

- Module: SA818 serial control backend.
- Size: `290 lines`, `10228 bytes`
- Constants: `CTCSS, DCS_CODES`
- Classes:
  - `SA818Error` (Exception)  [L46]
  - `SA818Client`  [L50]
    - `__init__(self)`  [L55]
    - `connected(self)`  [L64]
    - `connect(self, port, baud, timeout)`  [L67]
    - `probe(cls, port, baud, timeout)`  [L89]
    - `disconnect(self)`  [L104]
    - `_command(self, cmd, pause)`  [L117]
    - `command(self, cmd, pause)`  [L140]
    - `version(self)`  [L149]
    - `set_volume(self, level)`  [L152]
    - `set_filters(self, disable_emphasis, disable_highpass, disable_lowpass)`  [L160]
    - `set_tail(self, open_tail)`  [L167]
    - `set_radio(self, cfg)`  [L173]
    - `set_ptt(self, enabled, line, active_high)`  [L197]
    - `_release_ptt_safe(self)`  [L215]
    - `_safe_modem_lines(self)`  [L225]
    - `_flush_rx(self)`  [L235]
- Top-level functions:
  - `_validate_frequency(freq)`  [L248]
  - `_encode_tones(cfg)`  [L255]
  - `_encode_ctcss(value)`  [L267]
  - `_encode_dcs(value)`  [L280]

### app/engine/tile_provider.py

- Module: TileProvider — OSM slippy-map tile cache (online + offline).
- Size: `328 lines`, `11478 bytes`
- Constants: `OSM_TILE_URL, TILE_SIZE, _DOWNLOAD_RATE_LIMIT_S, _MEM_CACHE_SIZE, _USER_AGENT`
- Classes:
  - `TileProvider`  [L75]
    - `__init__(self, cache_dir, url_template, max_workers)`  [L82]
    - `pil_available(self)`  [L106]
    - `online(self)`  [L111]
    - `set_online(self, value)`  [L114]
    - `get_tile(self, z, x, y)`  [L121]
    - `request_tile(self, z, x, y, on_ready)`  [L142]
    - `tile_count_for_region(self, lat_min, lat_max, lon_min, lon_max, z_min, z_max)`  [L179]
    - `download_region(self, lat_min, lat_max, lon_min, lon_max, z_min, z_max, progress_cb, cancel_flag)`  [L196]
    - `cached_tile_count(self)`  [L248]
    - `clear_disk_cache(self)`  [L254]
    - `_fetch_worker(self, z, x, y)`  [L264]
    - `_fetch_online(self, z, x, y)`  [L284]
    - `_load_disk(self, z, x, y)`  [L307]
    - `_store_mem(self, key, img)`  [L319]
    - `_tile_path(self, z, x, y)`  [L326]
- Top-level functions:
  - `lat_lon_to_tile(lat, lon, z)`  [L42]
  - `lat_lon_to_world_px(lat, lon, z)`  [L53]
  - `world_px_to_lat_lon(px, py, z)`  [L62]

### app/ui/__init__.py

- Size: `1 lines`, `0 bytes`

### app/ui/aprs_tab.py

- Module: APRS Tab — TX, RX monitor, position, and map.
- Size: `301 lines`, `15147 bytes`
- Classes:
  - `AprsTab` (ttk.Frame)  [L19]
    - `__init__(self, parent, app)`  [L20]
    - `_build(self)`  [L25]
    - `_build_identity(self, parent)`  [L51]
    - `_build_message(self, parent)`  [L71]
    - `_build_position(self, parent)`  [L85]
    - `_build_rx(self, parent)`  [L97]
    - `_build_map(self, parent)`  [L147]
    - `_build_monitor(self, parent)`  [L160]
    - `aprs_log(self, msg)`  [L168]
    - `add_map_point(self, lat, lon, label)`  [L171]
    - `_clear_map(self)`  [L174]
    - `_open_in_browser(self)`  [L178]
    - `apply_profile(self, p)`  [L192]
    - `collect_profile(self, p)`  [L217]
    - `append_log(self, msg)`  [L273]
    - `set_monitor_active(self, active)`  [L277]
    - `set_input_level(self, level)`  [L281]
    - `set_output_level(self, level)`  [L286]
    - `push_waterfall(self, mono, rate)`  [L290]
    - `set_rx_clip(self, pct)`  [L295]

### app/ui/comms_tab.py

- Module: CommsTab — Merged APRS Comms tab.
- Size: `965 lines`, `41129 bytes`
- Classes:
  - `CommsTab` (ttk.Frame)  [L23]
    - `__init__(self, parent, app)`  [L26]
    - `_build(self)`  [L35]
    - `_build_left(self, parent)`  [L53]
    - `_build_right(self, parent)`  [L186]
    - `_add_contact(self)`  [L276]
    - `_remove_contact(self)`  [L281]
    - `_import_heard_to_contacts(self)`  [L289]
    - `_clear_heard(self)`  [L292]
    - `_new_group(self)`  [L299]
    - `_edit_group(self)`  [L313]
    - `_delete_group(self)`  [L331]
    - `_on_group_select(self, _e)`  [L339]
    - `_activate_thread(self, thread_key)`  [L356]
    - `_on_contact_select(self, _e)`  [L370]
    - `_on_heard_select(self, _e)`  [L377]
    - `_send_intro(self)`  [L388]
    - `_send_position(self)`  [L391]
    - `_clear_map(self)`  [L398]
    - `_open_map_in_browser(self)`  [L402]
    - `_open_download_dialog(self)`  [L413]
    - `_load_thread(self, thread_key)`  [L420]
    - `_render_message(self, msg)`  [L429]
    - `_on_compose_enter(self, event)`  [L446]
    - `_send_message(self)`  [L453]
    - `_on_msg_log_resize(self, event)`  [L471]
    - `on_message(self, msg)`  [L479]
    - `on_delivered(self, thread_key)`  [L488]
    - `refresh_contacts(self)`  [L493]
    - `refresh_heard(self)`  [L520]
    - `append_log(self, msg)`  [L537]
    - `set_monitor_active(self, active)`  [L541]
    - `set_input_level(self, level)`  [L545]
    - `set_output_level(self, level)`  [L550]
    - `push_waterfall(self, mono, rate)`  [L554]
    - `set_rx_clip(self, pct)`  [L558]
    - `add_map_point(self, lat, lon, label)`  [L565]
    - `apply_profile(self, p)`  [L573]
    - `collect_profile(self, p)`  [L601]
  - `DownloadRegionDialog` (tk.Toplevel)  [L661]
    - `__init__(self, parent, tile_provider, map_canvas)`  [L671]
    - `_build(self)`  [L696]
    - `_prefill(self)`  [L793]
    - `_update_estimate(self)`  [L822]
    - `_refresh_cache_label(self)`  [L847]
    - `_start_download(self)`  [L855]
    - `_download_worker(self, lamin, lamax, lomin, lomax, zmin, zmax)`  [L910]
    - `_update_progress(self, done, total, pct)`  [L927]
    - `_download_done(self, downloaded, skipped)`  [L934]
    - `_cancel(self)`  [L950]
    - `_clear_cache(self)`  [L954]

### app/ui/events.py

- Module: Typed event dataclasses for the engine→UI queue.
- Size: `124 lines`, `1921 bytes`
- Classes:
  - `LogEvent`  [L20]
  - `AprsLogEvent`  [L25]
  - `ErrorEvent`  [L30]
  - `ConnectionEvent`  [L36]
  - `PacketEvent`  [L42]
  - `MapPointEvent`  [L53]
  - `AudioPairEvent`  [L60]
  - `InputDeviceEvent`  [L66]
  - `InputLevelEvent`  [L71]
  - `OutputLevelEvent`  [L76]
  - `WaterfallEvent`  [L81]
  - `RxClipEvent`  [L87]
  - `HeardStationEvent`  [L92]
  - `ChatMessageEvent`  [L97]
  - `ContactsChangedEvent`  [L102]

### app/ui/main_tab.py

- Module: Main Tab — Radio control, connection, and audio routing.
- Size: `322 lines`, `15690 bytes`
- Classes:
  - `MainTab` (ttk.Frame)  [L19]
    - `__init__(self, parent, state)`  [L22]
    - `_build(self)`  [L32]
    - `_build_params(self, parent)`  [L52]
    - `_on_hw_mode_changed(self, _e)`  [L172]
    - `_apply_hw_mode_visibility(self)`  [L175]
    - `apply_profile(self, p)`  [L212]
    - `collect_profile(self, p)`  [L229]
    - `_on_out_selected(self, _e)`  [L266]
    - `_on_in_selected(self, _e)`  [L271]
    - `refresh_audio_devices(self)`  [L280]
    - `populate_audio_devices(self, outs, ins)`  [L287]
    - `on_audio_pair(self, out_idx, out_name, in_idx, in_name)`  [L306]
    - `on_connect(self, port)`  [L313]
    - `on_disconnect(self)`  [L316]
    - `append_log(self, msg)`  [L319]

### app/ui/setup_tab.py

- Module: SetupTab — Advanced Radio, Audio Tools, Profile, Bootstrap.
- Size: `422 lines`, `19308 bytes`
- Classes:
  - `SetupTab` (ttk.Frame)  [L26]
    - `__init__(self, parent, app)`  [L29]
    - `_build(self)`  [L38]
    - `_build_left(self, parent)`  [L54]
    - `_build_right(self, parent)`  [L206]
    - `_apply_filters(self)`  [L308]
    - `_set_volume(self)`  [L315]
    - `_apply_tail(self)`  [L318]
    - `_play_test_tone(self)`  [L321]
    - `_stop_audio(self)`  [L327]
    - `_play_manual_aprs(self)`  [L330]
    - `_tx_channel_sweep(self)`  [L333]
    - `_auto_detect_rx(self)`  [L336]
    - `_save_profile(self)`  [L339]
    - `_load_profile(self)`  [L349]
    - `_reset_defaults(self)`  [L358]
    - `_bootstrap(self)`  [L363]
    - `_two_radio_diagnostic(self)`  [L366]
    - `apply_profile(self, p)`  [L373]
    - `collect_profile(self, p)`  [L396]
    - `tts_enabled(self)`  [L420]

### app/ui/widgets.py

- Module: Shared UI widget helpers and reusable components.
- Size: `583 lines`, `23365 bytes`
- Constants: `_WF_LUT`
- Classes:
  - `BoundedLog` (ScrolledText)  [L62]
    - `__init__(self, parent, **kwargs)`  [L67]
    - `append(self, msg)`  [L70]
  - `WaterfallCanvas` (tk.Canvas)  [L115]
    - `__init__(self, parent, width, height, **kwargs)`  [L118]
    - `_on_resize(self, event)`  [L129]
    - `push_spectrum(self, rate, mono)`  [L141]
    - `_spectrum_row(self, rate, mono)`  [L150]
    - `_redraw(self)`  [L178]
  - `AprsMapCanvas` (tk.Canvas)  [L192]
    - `__init__(self, parent, **kwargs)`  [L195]
    - `set_on_pick(self, cb)`  [L212]
    - `add_point(self, lat, lon, label)`  [L215]
    - `clear(self)`  [L229]
    - `last_position(self)`  [L238]
    - `_latlon_to_xy(self, lat, lon, w, h)`  [L241]
    - `_xy_to_latlon(self, x, y, w, h)`  [L248]
    - `_draw(self)`  [L257]
    - `_on_press(self, event)`  [L281]
    - `_on_drag(self, event)`  [L284]
    - `_on_release(self, event)`  [L293]
    - `_on_wheel(self, event)`  [L312]
  - `TiledMapCanvas` (tk.Canvas)  [L329]
    - `__init__(self, parent, tile_provider, **kwargs)`  [L344]
    - `set_on_pick(self, cb)`  [L367]
    - `add_point(self, lat, lon, label)`  [L370]
    - `clear(self)`  [L380]
    - `last_position(self)`  [L386]
    - `_canvas_to_latlon(self, cx, cy)`  [L393]
    - `_latlon_to_canvas(self, lat, lon)`  [L400]
    - `_schedule_draw(self)`  [L412]
    - `_do_draw(self)`  [L418]
    - `_draw(self)`  [L422]
    - `_draw_tiled(self, w, h)`  [L435]
    - `_draw_grid_fallback(self, w, h)`  [L470]
    - `_draw_points(self, w, h)`  [L482]
    - `_draw_overlay(self, w, h)`  [L497]
    - `_on_press(self, event)`  [L527]
    - `_on_drag(self, event)`  [L531]
    - `_on_release(self, event)`  [L544]
    - `_on_wheel(self, event)`  [L562]
- Top-level functions:
  - `add_row(frame, label, widget, row)`  [L22]
  - `scrollable_frame(parent)`  [L27]
  - `_build_wf_lut()`  [L92]

### scripts/bootstrap_third_party.py

- Module: Install core Python requirements and optional third-party SA818 tools.
- Size: `132 lines`, `4247 bytes`
- Constants: `REPOS, _HERE, _ROOT`
- Top-level functions:
  - `_run(cmd, cwd)`  [L31]
  - `_pip(*packages)`  [L37]
  - `install_core_requirements()`  [L41]
  - `install_pycaw()`  [L51]
  - `clone_or_pull(name, url, target_root)`  [L56]
  - `copy_local_fallback(target_root)`  [L69]
  - `install_sa818_package(target_root)`  [L83]
  - `main()`  [L90]

### scripts/capture_wav_worker.py

- Module: Capture audio from a selected input device and write a WAV — standalone subprocess worker.
- Size: `71 lines`, `2016 bytes`
- Top-level functions:
  - `_setup_path()`  [L17]
  - `parse_args()`  [L23]
  - `main()`  [L34]

### scripts/generate_agent_onboarding_pack.py

- Module: Generate AI onboarding artifacts for this repository.
- Size: `334 lines`, `10092 bytes`
- Constants: `ROOT, ROOT_FILES, SKIP_DIRS, TARGET_DIRS`
- Classes:
  - `FuncInfo`  [L28]
  - `ClassInfo`  [L38]
  - `ImportInfo`  [L49]
  - `FileInfo`  [L56]
- Top-level functions:
  - `_safe_read(path)`  [L67]
  - `_short_doc(node)`  [L71]
  - `_unparse(node)`  [L77]
  - `_decorators(node)`  [L86]
  - `_func_info(node)`  [L95]
  - `_class_info(node)`  [L115]
  - `_imports(tree)`  [L131]
  - `_constants(tree)`  [L153]
  - `analyze_python_file(path)`  [L167]
  - `iter_python_files()`  [L194]
  - `build_index()`  [L210]
  - `build_markdown(index)`  [L252]
  - `main()`  [L321]

### scripts/play_wav_worker.py

- Module: Play WAV on a specific output device — standalone subprocess worker.
- Size: `69 lines`, `2007 bytes`
- Top-level functions:
  - `_setup_path()`  [L16]
  - `parse_args()`  [L22]
  - `main()`  [L30]

### scripts/rx_score_worker.py

- Module: Capture audio and print a voice-activity score — standalone subprocess worker.
- Size: `74 lines`, `2005 bytes`
- Top-level functions:
  - `_setup_path()`  [L15]
  - `parse_args()`  [L21]
  - `voice_activity_score(samples)`  [L29]
  - `main()`  [L41]

### scripts/two_radio_diagnostic.py

- Module: Two-radio APRS TX/RX reliability diagnostic.
- Size: `264 lines`, `9802 bytes`
- Constants: `_HERE, _ROOT`
- Top-level functions:
  - `_build_radio_cfg(freq, squelch, bw)`  [L41]
  - `_serial_ptt_stress(client, loops, ptt_line, active_high)`  [L45]
  - `_record_into(path, seconds, device, rate)`  [L63]
  - `_play_wav(path, device, rate)`  [L76]
  - `_decode_wav(path, rate)`  [L85]
  - `run(args)`  [L98]
  - `_build_parser()`  [L221]
  - `main()`  [L258]

### scripts/tx_wav_worker.py

- Module: Transmit a WAV file through SA818 with explicit PTT control — standalone worker.
- Size: `128 lines`, `4516 bytes`
- Top-level functions:
  - `_setup_path()`  [L24]
  - `parse_args()`  [L30]
  - `main()`  [L54]

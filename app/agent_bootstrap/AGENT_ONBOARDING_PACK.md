# Agent Onboarding Pack

This file is generated. Rebuild with:
`python scripts/generate_agent_onboarding_pack.py`

## Project Snapshot

- Project: `HAM HAT Control Center v4`
- Python files indexed: `43`
- Top-level functions: `196`
- Classes: `100`
- Class methods: `484`

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
- Legacy note: `app/ui/aprs_tab.py` exists, but `HamHatApp._build_ui` mounts `MainTab`, `CommsTab`, and `SetupTab`.

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
- `app/engine/display_config.py`
- `app/engine/mesh_mgr.py`
- `app/engine/models.py`
- `app/engine/pakt/__init__.py`
- `app/engine/pakt/capability.py`
- `app/engine/pakt/chunker.py`
- `app/engine/pakt/constants.py`
- `app/engine/pakt/service.py`
- `app/engine/pakt/telemetry.py`
- `app/engine/pakt/transport.py`
- `app/engine/platform_paths.py`
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
- `app/ui/mesh_tab.py`
- `app/ui/setup_tab.py`
- `app/ui/widgets.py`

### scripts

- `scripts/bootstrap_third_party.py`
- `scripts/capture_wav_worker.py`
- `scripts/generate_agent_onboarding_pack.py`
- `scripts/mesh_sim_tests.py`
- `scripts/platform_validation.py`
- `scripts/play_wav_worker.py`
- `scripts/rx_score_worker.py`
- `scripts/smoke_test.py`
- `scripts/two_radio_diagnostic.py`
- `scripts/tx_wav_worker.py`

### entry

- `main.py`

## Class and Function Index

### app/__init__.py

- Size: `1 lines`, `0 bytes`

### app/app.py

- Module: HamHatApp — main application window.
- Size: `2132 lines`, `88915 bytes`
- Constants: `_VERSION_FILE`
- Classes:
  - `_LogEvt`  [L94]
  - `_AprsLogEvt`  [L96]
  - `_ErrorEvt`  [L98]
  - `_ConnectEvt`  [L100]
  - `_DisconnectEvt`  [L102]
  - `_PacketEvt`  [L104]
  - `_AudioPairEvt`  [L106]
  - `_InputLevelEvt`  [L108]
  - `_OutputLevelEvt`  [L110]
  - `_WaterfallEvt`  [L112]
  - `_RxClipEvt`  [L114]
  - `_HeardEvt`  [L116]
  - `_ChatMsgEvt`  [L118]
  - `_ContactsEvt`  [L120]
  - `_StatusEvt`  [L122]
  - `_PaktScanEvt`  [L124]
  - `_PaktConnEvt`  [L126]
  - `_PaktCapsEvt`  [L128]
  - `_PaktInfoEvt`  [L130]
  - `_PaktConfigEvt`  [L132]
  - `_PaktTelemEvt`  [L134]
  - `_PaktTxQueuedEvt`  [L136]
  - `_PaktTxEvt`  [L138]
  - `_PaktSysStatusEvt`  [L140]
  - `_SuggestRxOsLevelEvt`  [L142]
  - `_MeshLogEvt`  [L144]
  - `_MeshRouteUpdateEvt`  [L146]
  - `HamHatApp` (tk.Tk)  [L149]
    - `__init__(self, app_dir, display_cfg)`  [L156]
    - `display_cfg(self)`  [L290]
    - `_build_ui(self)`  [L302]
    - `_check_linux_permissions(self)`  [L347]
    - `_wire_callbacks(self)`  [L422]
    - `_wire_comms(self)`  [L450]
    - `_drain_queue(self)`  [L461]
    - `_dispatch(self, evt)`  [L471]
    - `_vis_tick(self)`  [L620]
    - `_on_tab_changed(self, _e)`  [L637]
    - `_startup_auto_tasks(self)`  [L647]
    - `_auto_find_audio_background(self)`  [L658]
    - `_hw_mode(self)`  [L684]
    - `on_hw_mode_changed(self)`  [L688]
    - `connect(self, port)`  [L696]
    - `_apply_radio_after_connect(self)`  [L722]
    - `disconnect(self)`  [L726]
    - `scan_ports(self)`  [L743]
    - `auto_identify_and_connect(self)`  [L760]
    - `apply_radio(self)`  [L856]
    - `_apply_radio_config(self, p)`  [L870]
    - `apply_filters(self, emphasis, highpass, lowpass)`  [L900]
    - `set_volume(self, level)`  [L917]
    - `apply_tail(self, open_tail)`  [L934]
    - `refresh_audio_devices(self)`  [L955]
    - `auto_find_audio_pair(self)`  [L961]
    - `stop_audio(self)`  [L964]
    - `set_output_device(self, idx, name)`  [L968]
    - `set_input_device(self, idx, name)`  [L972]
    - `apply_callsign_preset(self, src, dst)`  [L980]
    - `send_aprs_message(self, to, text, reliable)`  [L984]
    - `_send_aprs_message_impl(self, to, text, reliable)`  [L996]
    - `send_direct_message(self, to, text, reliable)`  [L1032]
    - `send_aprs_position(self)`  [L1036]
    - `apply_os_rx_level(self)`  [L1047]
    - `on_rx_auto_toggle(self)`  [L1052]
    - `rx_one_shot(self)`  [L1059]
    - `aprs_log(self, msg)`  [L1063]
    - `send_group_message(self, group, text)`  [L1067]
    - `send_position(self, lat, lon, comment)`  [L1091]
    - `send_intro(self, note)`  [L1109]
    - `start_rx_monitor(self)`  [L1127]
    - `stop_rx_monitor(self)`  [L1153]
    - `one_shot_rx(self)`  [L1159]
    - `play_test_tone(self, freq, duration)`  [L1172]
    - `play_manual_aprs_packet(self, text)`  [L1182]
    - `tx_channel_sweep(self)`  [L1213]
    - `auto_detect_rx(self)`  [L1268]
    - `_handle_packet(self, pkt)`  [L1304]
    - `_handle_mesh_packet(self, pkt)`  [L1394]
    - `_mesh_tx(self, payload)`  [L1409]
    - `mesh_discover(self, target)`  [L1423]
    - `mesh_send(self, dst, body)`  [L1435]
    - `mesh_apply_config(self)`  [L1447]
    - `add_contact(self, call)`  [L1463]
    - `remove_contact(self, call)`  [L1466]
    - `import_heard_to_contacts(self)`  [L1469]
    - `clear_heard(self)`  [L1472]
    - `set_group(self, name, members)`  [L1476]
    - `delete_group(self, name)`  [L1479]
    - `save_profile(self, path)`  [L1486]
    - `load_profile(self, path)`  [L1500]
    - `import_profile(self)`  [L1509]
    - `export_profile(self)`  [L1521]
    - `reset_defaults(self)`  [L1534]
    - `_load_and_apply_profile(self)`  [L1538]
    - `_apply_profile_to_tabs(self, p)`  [L1542]
    - `_restore_audio_from_profile(self, p)`  [L1572]
    - `_collect_profile_snapshot(self)`  [L1587]
    - `_get_current_profile(self)`  [L1615]
    - `_autosave(self)`  [L1622]
    - `_pakt_tx_timeout_tick(self)`  [L1629]
    - `_mesh_tick(self)`  [L1640]
    - `_make_tx_snapshot(self)`  [L1658]
    - `_make_ptt_config(self)`  [L1734]
    - `_apply_os_rx_level(self, level)`  [L1750]
    - `_apply_os_tx_level(self, level)`  [L1836]
    - `_tts_announce(self, source, text)`  [L1923]
    - `run_bootstrap(self)`  [L1953]
    - `run_two_radio_diagnostic(self)`  [L1964]
    - `refresh_ports(self)`  [L1979]
    - `auto_identify(self)`  [L1987]
    - `read_version(self)`  [L1991]
    - `pakt_scan(self)`  [L2010]
    - `pakt_connect_selected(self)`  [L2013]
    - `pakt_disconnect(self)`  [L2020]
    - `pakt_read_capabilities(self)`  [L2023]
    - `pakt_read_config(self)`  [L2029]
    - `pakt_write_config(self)`  [L2035]
    - `pakt_send_tx_request(self, dest, text)`  [L2056]
    - `_apply_pakt_config_to_vars(self, text)`  [L2085]
    - `_set_status(self, text)`  [L2096]
    - `_on_close(self)`  [L2104]
- Top-level functions:
  - `_read_version()`  [L82]

### app/app_state.py

- Module: AppState — shared application state (tk.Var containers + engine instances).
- Size: `131 lines`, `6310 bytes`
- Classes:
  - `AppState`  [L22]
    - `__init__(self, app_dir)`  [L25]

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
- Size: `306 lines`, `12156 bytes`
- Classes:
  - `AudioRouter`  [L37]
    - `__init__(self, app_dir, audio_dir)`  [L40]
    - `set_log_cb(self, cb)`  [L49]
    - `_log(self, msg)`  [L52]
    - `refresh_output_devices(self)`  [L60]
    - `refresh_input_devices(self)`  [L63]
    - `auto_select_usb_pair(self, out_hint, in_hint)`  [L70]
    - `worker_busy(self)`  [L165]
    - `stop_audio(self)`  [L168]
    - `play_with_ptt_blocking(self, wav_path, out_dev, ptt, ptt_cb)`  [L176]
    - `capture_compatible(self, seconds, device_index, wav_out_path)`  [L215]
    - `record_compatible(self, wav_path, seconds, device_index)`  [L248]
    - `tx_active(self)`  [L263]
    - `tx_level_hold(self)`  [L267]
- Top-level functions:
  - `_play_wav_subprocess(wav_path, device_index, app_dir)`  [L275]
  - `_capture_wav_subprocess(wav_path, seconds, device_index, app_dir)`  [L289]

### app/engine/audio_tools.py

- Module: Audio I/O helpers for playback, recording, and device enumeration.
- Size: `282 lines`, `10528 bytes`
- Top-level functions:
  - `_list_devices(direction)`  [L35]
  - `list_output_devices()`  [L108]
  - `list_input_devices()`  [L112]
  - `play_wav(path, device_index)`  [L120]
  - `play_wav_blocking(path, device_index)`  [L132]
  - `play_wav_blocking_compatible(path, device_index)`  [L144]
  - `stop_playback()`  [L191]
  - `record_wav(path, seconds, device_index, sample_rate)`  [L205]
  - `capture_samples(seconds, device_index, sample_rate)`  [L218]
  - `wav_duration_seconds(path)`  [L236]
  - `estimate_wav_level(path)`  [L243]
  - `_load_wav_as_int16(path)`  [L261]
  - `_write_pcm16_mono(path, sample_rate, data)`  [L275]

### app/engine/comms_mgr.py

- Module: CommsManager: contacts, groups, and chat thread logic.
- Size: `341 lines`, `12086 bytes`
- Classes:
  - `CommsManager`  [L24]
    - `__init__(self)`  [L27]
    - `on_contacts_changed(self, cb)`  [L46]
    - `on_message_added(self, cb)`  [L49]
    - `on_heard_changed(self, cb)`  [L52]
    - `contacts(self)`  [L60]
    - `add_contact(self, call)`  [L63]
    - `remove_contact(self, call)`  [L72]
    - `ensure_contact(self, call)`  [L81]
    - `add_heard_to_contacts(self)`  [L84]
    - `groups(self)`  [L98]
    - `set_group(self, name, members)`  [L101]
    - `delete_group(self, name)`  [L108]
    - `heard(self)`  [L120]
    - `note_heard(self, call)`  [L123]
    - `clear_heard(self)`  [L130]
    - `messages(self)`  [L140]
    - `add_message(self, msg)`  [L143]
    - `mark_delivered(self, msg_id)`  [L150]
    - `mark_pakt_tx_result(self, msg_id, status)`  [L165]
    - `expire_stale_pakt_tx(self, max_age_s)`  [L207]
    - `messages_for_thread(self, thread_key)`  [L235]
    - `all_thread_keys(self)`  [L238]
    - `unread_for_thread(self, thread_key)`  [L245]
    - `set_active_thread(self, thread_key)`  [L248]
    - `active_thread(self)`  [L253]
    - `last_direct_sender(self)`  [L257]
    - `set_last_direct_sender(self, call)`  [L260]
    - `build_direct_chunks(self, text)`  [L267]
    - `build_group_chunks(self, group, text)`  [L271]
    - `build_intro_payload(self, callsign, lat, lon, note)`  [L279]
    - `should_process_intro(self, src_call, lat, lon, note)`  [L286]
    - `infer_thread_key(self, src, dst, text, local_calls)`  [L297]
    - `to_dict(self)`  [L315]
    - `from_dict(self, data)`  [L321]
- Top-level functions:
  - `_norm_call(token)`  [L338]

### app/engine/display_config.py

- Module: DisplayConfig — cross-platform display/font configuration helper.
- Size: `225 lines`, `9028 bytes`
- Classes:
  - `DisplayConfig`  [L59]
    - `default()`  [L118]
    - `rpi_720p()`  [L123]
    - `from_args(rpi, scale, geometry, fullscreen)`  [L165]
    - `apply_to_root(self, root)`  [L196]
- Top-level functions:
  - `_resolve_mono_font()`  [L36]
  - `_resolve_ui_font()`  [L49]

### app/engine/mesh_mgr.py

- Module: MeshManager — APRS AX.25 Mesh (Test) layer v0.
- Size: `725 lines`, `27079 bytes`
- Constants: `CHUNK_REASSEMBLY_TIMEOUT_S, DEDUPE_WINDOW_S, HELLO_INTERVAL_S, MAX_BODY_BYTES, MAX_FWD_PPM_CAP, MAX_PAYLOAD_LEN, MAX_TTL, MESH_PREFIX, _REQUIRED_FIELDS`
- Classes:
  - `MeshManager`  [L129]
    - `__init__(self, local_call_provider)`  [L136]
    - `set_config(self, cfg)`  [L163]
    - `get_route(self, destination)`  [L166]
    - `toggle_pin(self, destination)`  [L170]
    - `get_routes(self, now)`  [L182]
    - `get_stats(self)`  [L188]
    - `invalidate_route(self, destination)`  [L191]
    - `discover_route(self, target, now)`  [L197]
    - `send_data(self, dst, body, now)`  [L224]
    - `handle_rx(self, packet_text, from_call, now)`  [L259]
    - `_can_forward(self)`  [L275]
    - `tick(self, now)`  [L279]
    - `_handle_rx_inner(self, packet_text, from_call, now)`  [L297]
    - `_on_rreq(self, pkt, from_call, now)`  [L330]
    - `_on_rrep(self, pkt, from_call, now)`  [L412]
    - `_on_data(self, pkt, from_call, now)`  [L468]
    - `_on_rerr(self, pkt, from_call, now)`  [L540]
    - `_on_hello(self, pkt, from_call, now)`  [L556]
    - `_learn_route(self, destination, next_hop, hop_count, metric, learned_from, now)`  [L567]
    - `_route_for(self, dst, now)`  [L592]
    - `_expire_routes(self, now)`  [L598]
    - `_expire_dedupe(self, now)`  [L605]
    - `_rate_ok(self, now)`  [L613]
    - `_record_rate(self, now)`  [L618]
    - `_reassemble(self, src, mid, part, total, decoded_body, now)`  [L625]
    - `_expire_reassembly(self, now)`  [L641]
    - `_build_hello(self, now)`  [L652]
    - `_build_rerr(self, src, dst, code, detail, reporter)`  [L675]
- Top-level functions:
  - `_pct_encode(s)`  [L61]
  - `_pct_decode(s)`  [L65]
  - `parse_mesh_payload(text)`  [L73]
  - `build_mesh_payload(pkt)`  [L111]
  - `_rand_id(length)`  [L121]
  - `_safe_int(s, default)`  [L697]
  - `_chunk_body(encoded_body, max_bytes)`  [L704]

### app/engine/models.py

- Module: Shared dataclasses, enums, and type aliases used across the engine layer.
- Size: `277 lines`, `7332 bytes`
- Constants: `MSG_ID_COUNTER`
- Classes:
  - `RadioConfig`  [L17]
    - `clone(self)`  [L27]
  - `DecodedPacket`  [L45]
  - `AprsConfig`  [L54]
  - `ReliableConfig`  [L67]
  - `PttConfig`  [L79]
  - `AudioConfig`  [L88]
  - `ChatMessage`  [L100]
  - `_MsgIdCounter`  [L118]
    - `__init__(self)`  [L119]
    - `next(self)`  [L123]
  - `MeshConfig`  [L137]
  - `MeshRoute`  [L147]
  - `MeshPacket`  [L159]
  - `MeshStats`  [L166]
  - `AppProfile`  [L193]

### app/engine/pakt/__init__.py

- Module: PAKT native BLE backend package.
- Size: `29 lines`, `565 bytes`

### app/engine/pakt/capability.py

- Module: PAKT capability parsing.
- Size: `72 lines`, `2208 bytes`
- Classes:
  - `Feature`  [L10]
  - `PaktCapabilities`  [L22]
    - `parse(cls, json_str)`  [L31]
    - `assumed(cls, source, raw_json)`  [L46]
    - `supports(self, feature)`  [L65]
    - `summary(self)`  [L68]

### app/engine/pakt/chunker.py

- Module: PAKT BLE chunk split/reassembly.
- Size: `89 lines`, `2496 bytes`
- Constants: `HEADER_SIZE, MAX_CHUNKS`
- Classes:
  - `Reassembler`  [L33]
    - `__init__(self, callback, timeout_s)`  [L36]
    - `feed(self, chunk)`  [L41]
    - `reset(self)`  [L77]
    - `_expire(self)`  [L80]
- Top-level functions:
  - `split_payload(payload, msg_id, mtu)`  [L13]

### app/engine/pakt/constants.py

- Module: PAKT BLE UUIDs and constants.
- Size: `36 lines`, `1031 bytes`
- Constants: `DEVICE_NAME_PREFIX, MAX_RECONNECT_ATTEMPTS, NOTIFY_UUIDS, RECONNECT_DELAY_S, UUID_DEV_CAPS, UUID_DEV_COMMAND, UUID_DEV_CONFIG, UUID_DEV_STATUS, UUID_FW_REV, UUID_GPS_TELEM, UUID_MANUFACTURER, UUID_MODEL_NUM, UUID_POWER_TELEM, UUID_RX_PACKET, UUID_SYS_TELEM, UUID_TX_REQUEST, UUID_TX_RESULT, _B`

### app/engine/pakt/service.py

- Module: PAKT BLE service facade for the host app.
- Size: `334 lines`, `12492 bytes`
- Classes:
  - `PaktScanResult`  [L32]
  - `PaktConnectionEvent`  [L38]
  - `PaktDeviceInfoEvent`  [L45]
  - `PaktStatusEvent`  [L52]
  - `PaktConfigEvent`  [L57]
  - `PaktTelemetryEvent`  [L63]
  - `PaktTxResultEvent`  [L70]
  - `PaktTxQueuedEvent`  [L77]
  - `PaktService`  [L84]
    - `__init__(self, on_scan_results, on_connection, on_status, on_capabilities, on_device_info, on_config, on_telemetry, on_tx_queued, on_tx_result)`  [L87]
    - `is_connected(self)`  [L125]
    - `capabilities(self)`  [L129]
    - `address(self)`  [L133]
    - `set_config_cache_path(self, path)`  [L136]
    - `scan(self, timeout)`  [L139]
    - `connect(self, address)`  [L142]
    - `disconnect(self)`  [L145]
    - `read_device_info(self)`  [L148]
    - `read_capabilities(self)`  [L151]
    - `read_config(self)`  [L154]
    - `write_config(self, json_str)`  [L157]
    - `send_tx_request(self, dest, text, ssid)`  [L160]
    - `_run_loop(self)`  [L165]
    - `_submit(self, coro)`  [L169]
    - `_scan(self, timeout)`  [L172]
    - `_connect(self, address)`  [L180]
    - `_disconnect(self)`  [L190]
    - `_read_device_info(self)`  [L200]
    - `_read_capabilities(self)`  [L219]
    - `_read_config(self)`  [L233]
    - `_write_config(self, json_str)`  [L246]
    - `_send_tx_request(self, json_str, dest, text, ssid, local_id)`  [L252]
    - `_write_chunked(self, uuid, name, payload, response)`  [L258]
    - `_subscribe_all(self)`  [L275]
    - `_resubscribe(self)`  [L286]
    - `_on_notify(self, characteristic, data)`  [L291]
    - `_on_reassembled(self, name, data)`  [L298]
    - `_handle_transport_state(self, state, message)`  [L315]
    - `_next_msg_id(self)`  [L318]
    - `_next_local_tx_id(self)`  [L322]
    - `_cache_config(self, text)`  [L326]

### app/engine/pakt/telemetry.py

- Module: PAKT notification parsing helpers.
- Size: `93 lines`, `2459 bytes`
- Classes:
  - `DeviceStatus`  [L12]
  - `TxResult`  [L22]
  - `RxPacket`  [L28]
- Top-level functions:
  - `_load(json_str)`  [L35]
  - `parse_device_status(json_str)`  [L43]
  - `parse_tx_result(json_str)`  [L57]
  - `parse_rx_packet(json_str)`  [L67]
  - `parse_notify(name, json_str)`  [L79]

### app/engine/pakt/transport.py

- Module: PAKT BLE transport.
- Size: `211 lines`, `8435 bytes`
- Constants: `_AUTH_KEYWORDS`
- Classes:
  - `TransportState` (Enum)  [L58]
  - `PaktBleTransport`  [L67]
    - `__init__(self, on_state, on_reconnected, on_reconnect_failed)`  [L68]
    - `state(self)`  [L88]
    - `client(self)`  [L92]
    - `mtu(self)`  [L98]
    - `address(self)`  [L104]
    - `is_connected(self)`  [L108]
    - `scan(self, timeout)`  [L111]
    - `connect(self, address)`  [L125]
    - `disconnect(self)`  [L142]
    - `_on_disconnect(self, _)`  [L151]
    - `_create_reconnect_task(self)`  [L165]
    - `_reconnect(self)`  [L174]
    - `_set_state(self, state, message)`  [L192]
- Top-level functions:
  - `is_auth_error(exc)`  [L208]

### app/engine/platform_paths.py

- Module: Platform-aware application data directory resolution.
- Size: `110 lines`, `3993 bytes`
- Top-level functions:
  - `get_user_data_dir(app_name, fallback_dir)`  [L48]
  - `get_user_log_dir(app_name, fallback_dir)`  [L81]

### app/engine/profile.py

- Module: ProfileManager: validated load/save of AppProfile to JSON.
- Size: `225 lines`, `10358 bytes`
- Classes:
  - `ProfileManager`  [L24]
    - `__init__(self, profile_path)`  [L25]
    - `path(self)`  [L29]
    - `save(self, profile)`  [L32]
    - `load(self)`  [L37]
- Top-level functions:
  - `_profile_to_dict(p)`  [L52]
  - `_dict_to_profile(d)`  [L120]

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
- Size: `980 lines`, `41854 bytes`
- Classes:
  - `CommsTab` (ttk.Frame)  [L23]
    - `__init__(self, parent, app)`  [L26]
    - `_build(self)`  [L35]
    - `_build_left(self, parent)`  [L53]
    - `_build_right(self, parent)`  [L189]
    - `_add_contact(self)`  [L284]
    - `_remove_contact(self)`  [L289]
    - `_import_heard_to_contacts(self)`  [L297]
    - `_clear_heard(self)`  [L300]
    - `_new_group(self)`  [L307]
    - `_edit_group(self)`  [L321]
    - `_delete_group(self)`  [L339]
    - `_on_group_select(self, _e)`  [L347]
    - `_activate_thread(self, thread_key)`  [L364]
    - `_on_contact_select(self, _e)`  [L378]
    - `_on_heard_select(self, _e)`  [L385]
    - `_send_intro(self)`  [L396]
    - `_send_position(self)`  [L399]
    - `_clear_map(self)`  [L406]
    - `_open_map_in_browser(self)`  [L410]
    - `_open_download_dialog(self)`  [L421]
    - `_load_thread(self, thread_key)`  [L428]
    - `_render_message(self, msg)`  [L437]
    - `_on_compose_enter(self, event)`  [L456]
    - `_send_message(self)`  [L463]
    - `_on_msg_log_resize(self, event)`  [L481]
    - `on_message(self, msg)`  [L489]
    - `on_delivered(self, thread_key)`  [L498]
    - `on_message_updated(self, thread_key)`  [L503]
    - `refresh_contacts(self)`  [L508]
    - `refresh_heard(self)`  [L535]
    - `append_log(self, msg)`  [L552]
    - `set_monitor_active(self, active)`  [L556]
    - `set_input_level(self, level)`  [L560]
    - `set_output_level(self, level)`  [L565]
    - `push_waterfall(self, mono, rate)`  [L569]
    - `set_rx_clip(self, pct)`  [L573]
    - `add_map_point(self, lat, lon, label)`  [L580]
    - `apply_profile(self, p)`  [L588]
    - `collect_profile(self, p)`  [L616]
  - `DownloadRegionDialog` (tk.Toplevel)  [L676]
    - `__init__(self, parent, tile_provider, map_canvas)`  [L686]
    - `_build(self)`  [L711]
    - `_prefill(self)`  [L808]
    - `_update_estimate(self)`  [L837]
    - `_refresh_cache_label(self)`  [L862]
    - `_start_download(self)`  [L870]
    - `_download_worker(self, lamin, lamax, lomin, lomax, zmin, zmax)`  [L925]
    - `_update_progress(self, done, total, pct)`  [L942]
    - `_download_done(self, downloaded, skipped)`  [L949]
    - `_cancel(self)`  [L965]
    - `_clear_cache(self)`  [L969]

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
- Size: `493 lines`, `23619 bytes`
- Classes:
  - `MainTab` (ttk.Frame)  [L19]
    - `__init__(self, parent, state)`  [L22]
    - `_build(self)`  [L34]
    - `_build_params(self, parent)`  [L57]
    - `_on_hw_mode_changed(self, _e)`  [L257]
    - `_apply_hw_mode_visibility(self)`  [L265]
    - `apply_profile(self, p)`  [L322]
    - `collect_profile(self, p)`  [L344]
    - `_on_out_selected(self, _e)`  [L389]
    - `_on_in_selected(self, _e)`  [L394]
    - `_on_pakt_device_selected(self, _e)`  [L399]
    - `refresh_audio_devices(self)`  [L407]
    - `populate_audio_devices(self, outs, ins)`  [L414]
    - `on_audio_pair(self, out_idx, out_name, in_idx, in_name)`  [L433]
    - `set_pakt_ble_state(self, state)`  [L440]
    - `set_pakt_scan_results(self, devices)`  [L452]
    - `set_pakt_status(self, text)`  [L475]
    - `set_pakt_capabilities(self, text)`  [L478]
    - `set_pakt_config_text(self, text)`  [L481]
    - `on_connect(self, port)`  [L484]
    - `on_disconnect(self)`  [L487]
    - `append_log(self, msg)`  [L490]

### app/ui/mesh_tab.py

- Module: MeshTab — Mesh (Test) feature tab.
- Size: `402 lines`, `15935 bytes`
- Classes:
  - `MeshTab` (ttk.Frame)  [L28]
    - `__init__(self, parent, app)`  [L33]
    - `_build(self)`  [L43]
    - `_build_control(self, parent)`  [L73]
    - `_build_discovery(self, parent)`  [L137]
    - `_build_routes(self, parent)`  [L162]
    - `_build_send(self, parent)`  [L203]
    - `_build_diagnostics(self, parent)`  [L227]
    - `apply_profile(self, p)`  [L267]
    - `collect_profile(self, p)`  [L271]
    - `append_log(self, msg)`  [L275]
    - `refresh_routes(self)`  [L281]
    - `_on_enable_toggle(self)`  [L289]
    - `_apply_config(self)`  [L293]
    - `_refresh_enabled_state(self)`  [L298]
    - `_discover(self)`  [L317]
    - `_send_mesh(self)`  [L327]
    - `_invalidate_selected(self)`  [L345]
    - `_toggle_pin(self)`  [L354]
    - `_refresh_route_table(self)`  [L364]
    - `_refresh_stats(self)`  [L390]
    - `_auto_refresh_routes(self)`  [L396]

### app/ui/setup_tab.py

- Module: SetupTab — Advanced Radio, Audio Tools, Profile, Bootstrap.
- Size: `426 lines`, `19560 bytes`
- Classes:
  - `SetupTab` (ttk.Frame)  [L27]
    - `__init__(self, parent, app)`  [L30]
    - `_build(self)`  [L39]
    - `_build_left(self, parent)`  [L55]
    - `_build_right(self, parent)`  [L207]
    - `_apply_filters(self)`  [L312]
    - `_set_volume(self)`  [L319]
    - `_apply_tail(self)`  [L322]
    - `_play_test_tone(self)`  [L325]
    - `_stop_audio(self)`  [L331]
    - `_play_manual_aprs(self)`  [L334]
    - `_tx_channel_sweep(self)`  [L337]
    - `_auto_detect_rx(self)`  [L340]
    - `_save_profile(self)`  [L343]
    - `_load_profile(self)`  [L353]
    - `_reset_defaults(self)`  [L362]
    - `_bootstrap(self)`  [L367]
    - `_two_radio_diagnostic(self)`  [L370]
    - `apply_profile(self, p)`  [L377]
    - `collect_profile(self, p)`  [L400]
    - `tts_enabled(self)`  [L424]

### app/ui/widgets.py

- Module: Shared UI widget helpers and reusable components.
- Size: `598 lines`, `24100 bytes`
- Constants: `_WF_LUT`
- Classes:
  - `BoundedLog` (ScrolledText)  [L71]
    - `__init__(self, parent, **kwargs)`  [L76]
    - `append(self, msg)`  [L79]
  - `WaterfallCanvas` (tk.Canvas)  [L124]
    - `__init__(self, parent, width, height, **kwargs)`  [L127]
    - `_on_resize(self, event)`  [L138]
    - `push_spectrum(self, rate, mono)`  [L150]
    - `_spectrum_row(self, rate, mono)`  [L159]
    - `_redraw(self)`  [L187]
  - `AprsMapCanvas` (tk.Canvas)  [L201]
    - `__init__(self, parent, **kwargs)`  [L204]
    - `set_on_pick(self, cb)`  [L223]
    - `add_point(self, lat, lon, label)`  [L226]
    - `clear(self)`  [L240]
    - `last_position(self)`  [L249]
    - `_latlon_to_xy(self, lat, lon, w, h)`  [L252]
    - `_xy_to_latlon(self, x, y, w, h)`  [L259]
    - `_draw(self)`  [L268]
    - `_on_press(self, event)`  [L292]
    - `_on_drag(self, event)`  [L295]
    - `_on_release(self, event)`  [L304]
    - `_on_wheel(self, event)`  [L323]
  - `TiledMapCanvas` (tk.Canvas)  [L341]
    - `__init__(self, parent, tile_provider, **kwargs)`  [L356]
    - `set_on_pick(self, cb)`  [L381]
    - `add_point(self, lat, lon, label)`  [L384]
    - `clear(self)`  [L394]
    - `last_position(self)`  [L400]
    - `_canvas_to_latlon(self, cx, cy)`  [L407]
    - `_latlon_to_canvas(self, lat, lon)`  [L414]
    - `_schedule_draw(self)`  [L426]
    - `_do_draw(self)`  [L432]
    - `_draw(self)`  [L436]
    - `_draw_tiled(self, w, h)`  [L449]
    - `_draw_grid_fallback(self, w, h)`  [L484]
    - `_draw_points(self, w, h)`  [L496]
    - `_draw_overlay(self, w, h)`  [L511]
    - `_on_press(self, event)`  [L541]
    - `_on_drag(self, event)`  [L545]
    - `_on_release(self, event)`  [L558]
    - `_on_wheel(self, event)`  [L576]
- Top-level functions:
  - `add_row(frame, label, widget, row)`  [L22]
  - `scrollable_frame(parent)`  [L27]
  - `_build_wf_lut()`  [L101]

### main.py

- Module: HAM HAT Control Center v4 - entry point.
- Size: `115 lines`, `3509 bytes`
- Constants: `_HERE`
- Top-level functions:
  - `_configure_logging(level)`  [L19]
  - `main()`  [L30]

### scripts/bootstrap_third_party.py

- Module: Install core Python requirements and optional third-party SA818 tools.
- Size: `178 lines`, `6407 bytes`
- Constants: `REPOS, _HERE, _OFFLINE_FALLBACKS, _RESOURCES, _ROOT`
- Top-level functions:
  - `_run(cmd, cwd)`  [L40]
  - `_pip(*packages)`  [L46]
  - `install_core_requirements()`  [L50]
  - `install_pycaw()`  [L60]
  - `validate_offline_sources()`  [L65]
  - `clone_or_pull(name, url, target_root)`  [L78]
  - `copy_local_fallback(target_root)`  [L97]
  - `install_sa818_package(target_root)`  [L114]
  - `main()`  [L128]

### scripts/capture_wav_worker.py

- Module: Capture audio from a selected input device and write a WAV — standalone subprocess worker.
- Size: `104 lines`, `3176 bytes`
- Top-level functions:
  - `_setup_path()`  [L16]
  - `parse_args()`  [L22]
  - `_validate_capture_args(args)`  [L33]
  - `_validate_input_device(sd, device)`  [L46]
  - `main()`  [L59]

### scripts/generate_agent_onboarding_pack.py

- Module: Generate AI onboarding artifacts for this repository.
- Size: `343 lines`, `10375 bytes`
- Constants: `DOC_ROOT, ROOT, ROOT_FILES, SKIP_DIRS, TARGET_DIRS`
- Classes:
  - `FuncInfo`  [L35]
  - `ClassInfo`  [L45]
  - `ImportInfo`  [L56]
  - `FileInfo`  [L63]
- Top-level functions:
  - `_safe_read(path)`  [L74]
  - `_short_doc(node)`  [L78]
  - `_unparse(node)`  [L84]
  - `_decorators(node)`  [L93]
  - `_func_info(node)`  [L102]
  - `_class_info(node)`  [L122]
  - `_imports(tree)`  [L138]
  - `_constants(tree)`  [L160]
  - `analyze_python_file(path)`  [L174]
  - `iter_python_files()`  [L201]
  - `build_index()`  [L217]
  - `build_markdown(index)`  [L259]
  - `main()`  [L329]

### scripts/mesh_sim_tests.py

- Module: Deterministic mesh simulation tests (MESH-008).
- Size: `452 lines`, `18707 bytes`
- Constants: `NOW`
- Classes:
  - `_Counts`  [L32]
    - `__init__(self)`  [L35]
- Top-level functions:
  - `_result(name, ok, detail)`  [L42]
  - `_make_mgr(call, enabled, role, ttl, rate_ppm)`  [L52]
  - `test_parse_build_roundtrip()`  [L73]
  - `test_rreq_dedupe()`  [L98]
  - `test_rreq_ttl_drop()`  [L113]
  - `test_3node_discovery()`  [L126]
  - `test_3node_data_delivery()`  [L164]
  - `test_data_dedupe()`  [L193]
  - `test_chunked_reassembly()`  [L209]
  - `test_rate_limit()`  [L246]
  - `test_route_expiry()`  [L266]
  - `test_mesh_disabled()`  [L282]
  - `test_endpoint_no_forward()`  [L296]
  - `test_tick_expires_reassembly()`  [L333]
  - `test_chunk_boundary_pct_encode()`  [L368]
  - `_make_route(dst, via, hops, now, expiry_s)`  [L404]

### scripts/platform_validation.py

- Module: Cross-platform bring-up validation script.
- Size: `453 lines`, `17604 bytes`
- Constants: `_APP_ROOT, _FAIL, _HERE, _PASS, _SKIP`
- Top-level functions:
  - `ck(label, ok, detail, skip)`  [L41]
  - `section(title)`  [L52]
  - `check_python_version()`  [L62]
  - `check_imports()`  [L73]
  - `check_tkinter()`  [L96]
  - `check_display_env()`  [L113]
  - `check_audio()`  [L148]
  - `check_serial()`  [L167]
  - `check_ble()`  [L191]
  - `check_profile()`  [L241]
  - `check_paths()`  [L274]
  - `check_display_config()`  [L301]
  - `check_aprs()`  [L315]
  - `check_scroll_bindings()`  [L326]
  - `check_launcher_scripts()`  [L393]

### scripts/play_wav_worker.py

- Module: Play WAV on a specific output device — standalone subprocess worker.
- Size: `123 lines`, `4291 bytes`
- Top-level functions:
  - `_setup_path()`  [L16]
  - `parse_args()`  [L22]
  - `_validate_output_device(device_idx)`  [L30]
  - `_load_wav_float32(wav_path)`  [L43]
  - `main()`  [L93]

### scripts/rx_score_worker.py

- Module: Capture audio and print a voice-activity score — standalone subprocess worker.
- Size: `118 lines`, `3536 bytes`
- Top-level functions:
  - `_setup_path()`  [L15]
  - `parse_args()`  [L21]
  - `_validate_capture_args(args)`  [L29]
  - `_validate_input_device(sd, device)`  [L40]
  - `voice_activity_score(samples)`  [L53]
  - `main()`  [L65]

### scripts/smoke_test.py

- Module: Cross-platform portability smoke test for HAM HAT Control Center v4.
- Size: `557 lines`, `23136 bytes`
- Constants: `_FAIL, _HERE, _PASS, _ROOT, _SKIP`
- Top-level functions:
  - `_module_available(name)`  [L43]
  - `_required_runtime_missing()`  [L47]
  - `_check(name, fn, skip_reason)`  [L60]
  - `_check_required_imports()`  [L77]
  - `_check_app_state_import()`  [L86]
  - `_check_sv_ttk_guard()`  [L94]
  - `_check_bleak_guard()`  [L103]
  - `_check_scipy_guard()`  [L115]
  - `_check_pycaw_guard()`  [L131]
  - `_check_winsound_guard()`  [L148]
  - `_check_profile_roundtrip()`  [L166]
  - `_check_platform_paths()`  [L203]
  - `_check_audio_device_listing()`  [L219]
  - `_check_aprs_modem()`  [L230]
  - `_check_display_config_rpi()`  [L245]
  - `_check_linux_scroll_bindings()`  [L274]
  - `_check_hardware_mode_switch()`  [L287]
  - `_check_profile_field_clamping()`  [L346]
  - `_check_corrupt_profile_fallback()`  [L379]
  - `_check_contacts_mesh_isolation()`  [L414]
  - `main()`  [L478]

### scripts/two_radio_diagnostic.py

- Module: Two-radio APRS TX/RX reliability diagnostic.
- Size: `310 lines`, `11774 bytes`
- Constants: `_HERE, _ROOT`
- Top-level functions:
  - `_build_radio_cfg(freq, squelch, bw)`  [L41]
  - `_validate_device(device_idx, kind)`  [L45]
  - `_serial_ptt_stress(client, loops, ptt_line, active_high)`  [L62]
  - `_record_into(path, seconds, device, rate)`  [L80]
  - `_play_wav(path, device, rate)`  [L93]
  - `_decode_wav(path, rate)`  [L102]
  - `run(args)`  [L115]
  - `_build_parser()`  [L259]
  - `main()`  [L296]

### scripts/tx_wav_worker.py

- Module: Transmit a WAV file through SA818 with explicit PTT control — standalone worker.
- Size: `175 lines`, `6575 bytes`
- Top-level functions:
  - `_setup_path()`  [L24]
  - `parse_args()`  [L30]
  - `_load_wav_float32(wav_path)`  [L54]
  - `main()`  [L104]

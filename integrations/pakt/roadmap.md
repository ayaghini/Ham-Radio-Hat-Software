# PAKT Integration Roadmap

Status date: 2026-03-16 (updated after whole-app integrity audit pass)
Scope: `app` only

## Phases

### 1. Discovery and fit analysis

- `done` Read PAKT handoff package and primary source files.
- `done` Inspect host app architecture and existing hardware modes.
- `done` Identify PAKT insertion points and minimal shared changes.

### 2. Host app platform insertion

- `done` Add `PAKT` as the third hardware mode in profile, state, and UI.
- `done` Add PAKT-specific persisted fields for BLE device context.
- `done` Route host app actions explicitly by hardware mode.

### 3. PAKT BLE backend scaffold

- `done` Add dedicated PAKT engine package.
- `done` Implement asyncio BLE worker thread and transport state machine.
- `done` Implement capability parsing, chunking, config/TX helpers, and notify handling.

### 4. UI wiring for scan/connect/config/status

- `done` Add PAKT controls to the main tab.
- `done` Surface scan results, capability summary, config text, and status.
- `done` Show bonded/auth-required errors clearly.

### 5. TX and telemetry integration

- `done` Route direct outbound message action to native PAKT `tx_request`.
- `done` Surface TX result notifications in host app logs/status.
- `done` Surface telemetry and reserved endpoint state without overstating hardware readiness.

### 6. Validation and follow-up gaps

- `done` Run static verification and import smoke.
- `done` Document hardware-blocked items and post-first-pass follow-ups.
- `done` Audit and fix implementation bugs (see bug-fix pass below).

### Bug-fix pass (2026-03-16)

All bugs were found via static audit; no hardware was present for live verification.

Fixed:
- **BUG-003** `capability.py`: `Feature` was a frozen dataclass with instance fields, making `Feature.APRS_2M` raise `AttributeError`. Converted to a plain class with class-level string constants.
- **BUG-004** `service.py`: `_submit` type annotation used `asyncio.coroutines` (a module) as a type. Fixed to `Coroutine[Any, Any, None]`.
- **BUG-006/double-log** `service.py`: `_on_reassembled` routed `tx_result` through both `_on_telemetry` AND `_on_tx_result`, causing double log entries and status bar thrash. Fixed: `tx_result` now routes only through `_on_tx_result`.
- **BUG-009** `service.py`: `_write_config` fired `_on_config` and cached config to disk even when the BLE write failed silently. Fixed: `_write_chunked` now returns `bool`; config event and cache only fire on `True`.
- **BUG-010** `service.py`: `_send_tx_request` reported "PAKT TX request queued" even when write failed. Fixed: status event only fires on write success.
- **BUG-012/013** `app.py`: `pakt_write_config` had no client-side validation of callsign format or SSID range; invalid values were silently rejected by firmware with no visible error. Fixed: added `re.fullmatch` callsign validation (`[A-Z0-9-]`, 1–6 chars) and SSID range check (0–15) before write.

Not fixed (architectural, no current crash):
- **BUG-001/002** Callback wiring happens by mutating private `_on_*` attributes post-construction rather than passing to constructor. Safe as-is (BLE thread is idle until first `scan()` call); deferring to a future refactor.
- **BUG-005** `_make_tx_snapshot()` returns `None` for PAKT mode; not triggered today since RX packets don't route through `_handle_packet`.
- **BUG-007** Telemetry data surfaces only in the status bar and log, not a dedicated panel. Deferred — needs dedicated tab work.
- **BUG-008** `chunker.py` uses `assert` for defensive checks; not load-bearing, low priority.
- **BUG-018** PAKT outbound messages in CommsTab never get marked delivered (no TX result → CommsManager wiring). Deferred to dedicated tab / comms generalization pass.

### Second fix pass (2026-03-16)

Fixed the four issues called out for this session, plus two UX improvements:

- **Issue 1 — False-positive chat messages on PAKT TX**: `_send_aprs_message_impl` added a ChatMessage immediately without checking whether the BLE write was even submitted. Fixed: `pakt_send_tx_request` now returns `bool`; chat message only added when `True`.
- **Issue 2 — Duplicate-name device collision**: `set_pakt_scan_results` keyed the device map by name, so two `PAKT-TNC` devices overwrote each other. Fixed: display labels are now `name` when unique, `name (address)` when colliding. Combobox and address lookup use these labels correctly.
- **Issue 3 — PAKT status panel stale on backend errors**: `_on_status` events (auth errors, write failures, scan results) only reached the global status bar, not the PAKT panel. Fixed: new `_PaktSysStatusEvt` internal event routes PAKT backend status to both `_set_status()` and `set_pakt_status()`.
- **Issue 4 — Missing TX payload validation**: `pakt_send_tx_request` did not enforce `dest` format, `text` length (max 67 printable chars), or `ssid` range before writing. Fixed: full contract validation added; function returns `False` and shows a specific message on any violation.
- **UX: SSID entry validation**: SSID entry widget now only accepts digits (0-9, max 2 chars) via `validatecommand`; label updated to "SSID (0-15)".
- **UX: Scan button feedback**: `set_pakt_ble_state(state)` method added to MainTab; called from `_PaktConnEvt` dispatch. Scan button shows "Scanning…" and is disabled during scan. Connect/Disconnect buttons enable/disable based on connection state.
- **Cleanup**: Removed redundant `pakt_device_var`/`pakt_address_var` assignment in `_PaktScanEvt` dispatch (already handled by `set_pakt_scan_results`). Moved `import re` to top-level in `app.py`. Shortened PAKT button labels (PAKT prefix removed since they're only visible in PAKT mode).

### Whole-app integrity audit pass (2026-03-16)

Fixed three issues found during a broad v4 audit (see `audit_v4.md`):

- **AUD-001** Footer `_conn_lbl` had no branch for PAKT `SCANNING` state. Fixed: scanning shows
  "🔵 PAKT Scanning…" so the indicator does not falsely show a prior connected state during scan.
- **AUD-002** `_conn_lbl` was not reset when the Hardware Mode combobox changed modes. Fixed:
  `MainTab._on_hw_mode_changed` now calls `app.on_hw_mode_changed()` which resets the indicator
  to "⚫ Disconnected", preventing SA818 "🟢 COM3" from persisting into PAKT mode.
- **AUD-003** `scripts/generate_agent_onboarding_pack.py` had `"agent_bootstap"` typo (missing
  'r') in 3 places. Fixed: all occurrences corrected to `"agent_bootstrap"`.

### Third fix pass (2026-03-16)

Fixed:
- **Async false-positive sends**: PAKT outbound messages are now added to Comms only after the BLE `tx_request` write succeeds. The service emits a dedicated queued event after a successful write instead of relying on preflight validation alone.
- **TX result to Comms state**: PAKT `tx_result` notifications now reconcile back into `CommsManager`. Host-side placeholder IDs are remapped to firmware-assigned `msg_id` values on first result, `acked` marks the message delivered, and `timeout` / `cancelled` / `error` mark it failed.
- **Footer connection state**: the shared app footer connection indicator now reflects PAKT connect, reconnect, and disconnect state instead of remaining stuck on SA818-only events.
- **Scan selection refresh**: PAKT scan refresh now always re-synchronizes `pakt_address_var` from the rebuilt device map when the selected label still exists, preventing stale address carry-over.
- **Comms rendering**: failed PAKT outbound messages now render distinctly in the Comms thread instead of looking permanently pending.

### Second integrity pass (2026-03-16)

Fixed PAKT-relevant items from the second whole-app audit pass:

- **RES-007 closed**: `ChatMessage` gained `timestamp: float` field. `CommsManager.expire_stale_pakt_tx(max_age_s)` now marks stale PAKT TX messages failed after 2 minutes. `HamHatApp._pakt_tx_timeout_tick` runs every 30 s. The "pending forever" gap is eliminated for the no-tx_result-received case.
- **Telemetry status thrash (RES-005, partial)**: `_PaktTelemEvt` dispatch now only calls `set_pakt_status()` for `device_status` and `tx_result` events. Rapid-fire telemetry (GPS, power, system) no longer thrashes the PAKT status panel. Log format improved to `[PAKT telem/{name}] {text}`.
- **TX result log format**: `_PaktTxEvt` log entry is now `[PAKT tx/{msg_id}] status={status}` instead of a raw JSON dump.
- **PAKT button state reset**: Switching back TO PAKT mode now resets PAKT button states to IDLE to prevent stale connect/disconnect button state from a prior PAKT session.
- **Audio device list in PAKT startup**: Audio device comboboxes are now populated even when the app starts in PAKT mode.

## Blockers

- Capability payload docs drift: `payload_contracts.md` shows an older boolean example, while firmware/client implementation uses `fw_ver/hw_rev/protocol/features`. The integration docs under `integrations/pakt/` are correct; the upstream PAKT repo doc is stale.
- Some firmware endpoints are specified but not yet proven live on hardware: device status, RX packet stream, some telemetry sources, command execution.
- Local validation covers compile/import flows only; real BLE hardware behavior requires a PAKT device.

## Next

- **Hardware**: Validate against real PAKT hardware — BLE scan, bonded write pairing flow, TX results, live telemetry.
- **Dedicated tab**: Decide whether PAKT should get a richer dedicated tab for telemetry display, per-characteristic status, and device command support.
- **RX packet surfacing**: Revisit routing received APRS packets to the CommsTab packet view once firmware/hardware maturity is confirmed.
- **Command characteristic**: Expose device command write once firmware behavior is live and tested.

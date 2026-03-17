# v4 App Integrity Audit

Date: 2026-03-16
Scope: whole `windows-release/ham_hat_control_center_v4` app — all hardware modes, all flows.
Prior scope: `integrations/pakt/audit.md` covers PAKT-only findings from the earlier PAKT integration passes.

## Verification Run

```
python3 -m compileall -q <v4 root> <integrations/pakt>   # clean
python3 main.py --help                                     # green
```

## Fixed in This Pass

### Second Integrity Pass (2026-03-16)

#### SIP-001 — PAKT pending-message host-side timeout (RES-007 resolved)

- Files: `app/engine/models.py`, `app/engine/comms_mgr.py`, `app/app.py`
- Severity: Low (UX gap closed)

Added `timestamp: float = field(default_factory=time.monotonic)` to `ChatMessage` in `models.py`
(with `import time`). Added `CommsManager.expire_stale_pakt_tx(max_age_s: float) -> list[str]`
that finds all TX/PAKT/non-terminal messages older than `max_age_s` seconds, marks them
`failed = True`, and returns their `thread_key` values for UI refresh.

Added `HamHatApp._pakt_tx_timeout_tick()` that calls `expire_stale_pakt_tx(120.0)` every 30 s
and calls `self._comms_tab.on_message_updated(thread_key)` for each expired message. Tick started
in `__init__` after the other `self.after(...)` calls. 2-minute timeout policy.

#### SIP-002 — PAKT mode audio device list empty on startup (hardware mode switch gap)

- Files: `app/app.py`
- Severity: Low (empty comboboxes in PAKT mode on first run)

`_startup_auto_tasks` called `refresh_audio_devices()` only in non-PAKT paths. When the app
started in PAKT mode the audio device comboboxes were left empty for the session.

Fixed: moved `self._main_tab.refresh_audio_devices()` before the `if hw_mode == "PAKT"` check
so audio device lists are always populated regardless of hardware mode.

#### SIP-003 — PAKT button state not reset on hardware mode switch TO PAKT

- Files: `app/ui/main_tab.py`
- Severity: Low (stale button states after mode round-trip)

When switching away from PAKT and back, `_btn_pakt_connect` / `_btn_pakt_disconnect` retained
whatever enabled/disabled state was last set by `set_pakt_ble_state()`. A prior CONNECTING or
CONNECTED state would leave Disconnect enabled and Connect disabled even though no connection
exists.

Fixed: `_on_hw_mode_changed` now calls `self.set_pakt_ble_state("IDLE")` when switching TO PAKT
mode, ensuring buttons start in a clean, known state.

#### SIP-004 — FIX 3: `pakt_status_var` and `pakt_last_tx_result_var` not in profile (verified)

- Files: `app/app.py`, `app/ui/main_tab.py`
- Severity: None (no change needed)

Verified `collect_profile` (MainTab) and `_collect_profile_snapshot` (app.py) do not write
`pakt_status_var` or `pakt_last_tx_result_var` to the profile. These are runtime-only vars.
`pakt_capabilities_var` is correctly persisted as `pakt_capabilities_summary` (last-known value).
`apply_profile` in MainTab sets `pakt_capabilities_var` from the saved summary, which is the
correct "last known" behavior. No code changes required.

#### SIP-005 — PAKT telemetry log format and selective status panel updates

- Files: `app/app.py`
- Severity: Low (UX improvement)

The `_PaktTelemEvt` dispatcher called `set_pakt_status()` for every telemetry event regardless
of type, causing rapid-fire telemetry (GPS, power, system telem) to thrash the PAKT status panel.

Fixed: `set_pakt_status()` is now called only for `name in {"device_status", "tx_result"}` — the
high-signal events. All telemetry still goes to the log with the structured format
`[PAKT telem/{name}] {text}` instead of the bare `[PAKT] {name}: {text}`.

`_PaktTxEvt` log entry changed from `[PAKT] tx_result: {raw_json}` (raw JSON dump) to the
structured form `[PAKT tx/{msg_id}] status={status}` for clarity.

#### SIP-006 — `sv_ttk` optional dependency guard in `app.py`

- Files: `app/app.py`
- Severity: Low (would crash on import if sv_ttk not installed)

`import sv_ttk` was at module level without a guard. If `sv_ttk` is absent (e.g. fresh venv
without requirements installed) the app would crash at import, preventing SA818/DigiRig users
from running the app at all.

Fixed: wrapped as `try: import sv_ttk as _sv_ttk except ImportError: _sv_ttk = None`. The
`set_theme("dark")` call is guarded by `if _sv_ttk is not None:`. App opens with the default
ttk theme if `sv_ttk` is absent.

Note: `bleak` is already guarded in `transport.py`. `pycaw` is already guarded with
`except ImportError: pass` in its worker functions. No further changes needed for those.

#### SIP-007 — `two_radio_diagnostic.py` argument validation

- Files: `scripts/two_radio_diagnostic.py`
- Severity: Medium (zero/negative values caused silent bad behavior)

`--extra-record-sec`, `--serial-loops`, and `--aprs-loops` had no positive-value validation.
A zero or negative `--extra-record-sec` would cause `sd.rec(0, ...)` or `sd.rec(-N, ...)`,
producing an empty or invalid recording with no error.

Fixed: added explicit checks after `parse_args()` in `main()` that call `parser.error()`
for any of the three arguments that are `<= 0`.

### AUD-001 — Footer connection indicator blind to PAKT SCANNING state

- Files: `app/app.py`
- Severity: Low-Medium (misleading UI)

The `_PaktConnEvt` dispatch handled `CONNECTED`, `CONNECTING`, `RECONNECTING`, `IDLE`, and `ERROR`
but had no branch for `state == "SCANNING"`. When `PaktBleTransport` entered a scan, the footer
`_conn_lbl` stayed at whatever it showed before (potentially "🟢 PAKT addr" if a prior connection
had been made), giving a false "connected" indicator during an active scan.

Fixed: added `elif evt.event.state == "SCANNING":` → `"🔵 PAKT Scanning…"` in `#6ab0e0`.

### AUD-002 — Footer connection indicator not reset on hardware mode switch

- Files: `app/app.py`, `app/ui/main_tab.py`
- Severity: Low-Medium (stale UI)

When the user changed the Hardware Mode combobox (e.g. SA818 → PAKT), `_on_hw_mode_changed` in
`MainTab` called only `_apply_hw_mode_visibility()`. The footer `_conn_lbl` inherited whatever
indicator the previous mode had set (e.g. "🟢 COM3" persisting into PAKT mode).

Fixed:
- Added `HamHatApp.on_hw_mode_changed()` that resets `_conn_lbl` to `"⚫ Disconnected"`.
- `MainTab._on_hw_mode_changed` now calls `self._state.on_hw_mode_changed()` after
  `_apply_hw_mode_visibility()`.

### AUD-003 — DOC_ROOT typo in `generate_agent_onboarding_pack.py`

- Files: `scripts/generate_agent_onboarding_pack.py`
- Severity: Low (breaks script output path; script not run at app startup)

Three occurrences of `"agent_bootstap"` (missing 'r'). The script writes outputs under this
incorrectly named directory, so the agent onboarding artifacts end up in the wrong place if the
script is run.

Fixed: replaced all three occurrences with `"agent_bootstrap"`.

## Pre-existing PAKT Issues Fixed in Earlier Passes

See `integrations/pakt/audit.md` and `integrations/pakt/roadmap.md` for the full record.
All four original bug-fix pass items, all second-pass items, and all third-pass items are complete.

## Known Residual Risks

### RES-001 — PAKT TX correlation needs hardware validation

- Severity: Medium
- Files: `app/engine/comms_mgr.py`, `app/engine/pakt/service.py`

The host-side `pakt-local:N` → firmware `msg_id` remapping is correct against the documented
contract and passes local smoke tests. Real-device behavior under retries, reconnects, and
back-to-back sends has not been exercised.

### RES-002 — All PAKT BLE behavior is hardware-blocked

- Severity: Medium

BLE scan, bonded-pairing flow, live TX result sequencing, live telemetry, and reserved endpoints
all require a physical PAKT device. No hardware was present during any development pass.

### RES-003 — BUG-001/002: callback wiring via post-construction mutation

- Severity: Low (no crash path today)
- Files: `app/engine/pakt/service.py`

Callbacks are wired by mutating `_on_*` attributes after construction rather than injecting at
`__init__` time. Safe because the BLE thread is idle until the first `scan()` call, but fragile
if construction order or lifecycle ever changes. Deferred to a future refactor.

### RES-004 — BUG-005: `_make_tx_snapshot()` returns `None` for PAKT

- Severity: Low (no crash path today)
- Files: `app/app.py`

Intentional: PAKT TX does not use the audio/APRS snapshot path. Not triggered today because no
RX packets route through `_handle_packet` in PAKT mode. Documents the gap for future PAKT RX work.

### RES-005 — BUG-007: PAKT telemetry panel (partially addressed)

- Severity: Low
- Files: `app/ui/main_tab.py`, `app/app.py`

The second integrity pass (SIP-005) improved the log format and prevents rapid-fire telemetry
from thrashing the PAKT status panel. However, there is still no dedicated structured telemetry
panel — all telemetry surfaces only in the radio log. A dedicated panel (e.g. a BoundedLog
in the PAKT BLE frame) would require layout changes and is deferred until firmware/hardware
behavior is confirmed.

### RES-006 — BUG-008: `chunker.py` uses `assert` for defensive checks

- Severity: Low
- Files: `app/engine/pakt/chunker.py`

`assert` statements are stripped under `-O` (optimized). Not load-bearing in production mode.
Low priority; can be hardened with explicit `ValueError` raises if chunking errors ever surface.

### ~~RES-007~~ — PAKT pending-message timeout: FIXED (SIP-001)

Fixed in the second integrity pass. `expire_stale_pakt_tx(120.0)` runs every 30 s. Pending
PAKT outbound messages older than 2 minutes are marked failed and the Comms thread is refreshed.

## Not-Fixed Script Bugs (from `audit.md`)

The pre-existing `audit.md` at the repo root documents 32 issues across 8 scripts (SA818
diagnostic and utility scripts). None are app startup paths.

Fixed in the second integrity pass:
- `two_radio_diagnostic.py`: added validation for `--extra-record-sec`, `--serial-loops`, and
  `--aprs-loops` (all must be positive).

Still deferred:
- `capture_wav_worker.py` / `rx_score_worker.py`: zero/negative seconds gap (out of scope,
  no app startup path).
- Other medium/low script issues from `audit.md`.

## Summary

All three code-level bugs found in the first app audit pass are fixed. The second integrity pass
(2026-03-16) added six additional targeted fixes: PAKT TX timeout, audio device list in PAKT
mode, PAKT button state reset, telemetry log format improvements, `sv_ttk` optional-dep guard,
and script argument validation. Compile and `--help` smoke remain green.

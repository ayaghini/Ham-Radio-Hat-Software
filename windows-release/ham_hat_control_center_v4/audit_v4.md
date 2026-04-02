# v4 App Audit

Updated: 2026-04-01
Scope: canonical audit for `windows-release/ham_hat_control_center_v4`, including app issues, residual risks, and open script findings.
Prior history: resolved PAKT-only findings remain documented in `integrations/pakt/audit.md` and `integrations/pakt/roadmap.md`.

## Verification Run

Reviewed against the current workspace state on 2026-04-01.

Local verification performed:

```text
python3 -m compileall -q app                         # clean
python3 scripts/smoke_test.py -v                     # passes; sparse env now classifies missing hard deps as SKIP
python3 scripts/smoke_test.py -v --guards-only       # passes
```

Notes:
- `compileall` passed.
- `smoke_test.py` now behaves safely in sparse environments and supports `--guards-only` for optional-dependency guard coverage.
- No hardware was available for SA818, DigiRig, or PAKT runtime validation.

## Recently Fixed In This Pass

### AUD-004 — Existing installs lose their saved profile on upgrade: FIXED

- Files: `app/app_state.py`

`AppState` now performs a best-effort migration from the legacy in-tree
`profiles/last_profile.json` into the new user-data location before creating `ProfileManager`.

### AUD-005 — PAKT config cache still writes into the install tree: FIXED

- Files: `app/app.py`

The PAKT config cache path now uses the migrated user-data root instead of `app_dir/profiles/`.

### AUD-006 — Windows worker-thread audio capture still uses a legacy in-tree temp path: FIXED

- Files: `app/engine/audio_router.py`

`AudioRouter.capture_compatible()` now uses the migrated writable audio directory for Windows
worker-thread temp WAVs.

### AUD-007 — Smoke test does not validate the minimal bootstrap environment it claims to cover: IMPROVED

- Files: `scripts/smoke_test.py`, `.github/workflows/smoke.yml`

The smoke test now:
- classifies missing hard runtime dependencies as `SKIP` instead of failing early
- supports `--guards-only` for sparse-environment optional-dependency validation

CI now adds a non-Windows guard-only smoke run in a clean venv with only the hard runtime
dependencies installed.

## Open Findings

No app-level open findings remain from the 2026-04-01 cross-platform preflight fixes.

## Residual Risks Still Open

### RES-001 — PAKT TX correlation still needs hardware validation

- Severity: Medium
- Files: `app/engine/comms_mgr.py`, `app/engine/pakt/service.py`

The host-side `pakt-local:N` to firmware `msg_id` remapping looks correct by static review and local
smoke coverage, but it has not been exercised against a real device under retries, reconnects, or
back-to-back sends.

### RES-002 — All PAKT BLE runtime behavior remains hardware-blocked

- Severity: Medium

BLE scan, bonded-pairing flow, live TX result sequencing, live telemetry, and reserved endpoints all
still require a physical PAKT device. No hardware validation was performed in this pass.

### RES-003 — PAKT callback wiring still depends on post-construction mutation

- Severity: Low
- Files: `app/engine/pakt/service.py`

Callbacks are still assigned by mutating `_on_*` attributes after `PaktService` construction rather
than being injected once at construction time. This is safe today because the BLE loop is idle until
the first operation, but it remains lifecycle-fragile.

### RES-004 — `_make_tx_snapshot()` still returns `None` for PAKT by design

- Severity: Low
- Files: `app/app.py`

This is still intentional and not a live bug today because PAKT TX does not use the APRS audio
snapshot path. Keep it in view if future work adds PAKT RX or shared packet-handling paths.

### RES-005 — PAKT telemetry still lacks a dedicated structured panel

- Severity: Low
- Files: `app/ui/main_tab.py`, `app/app.py`

Telemetry log formatting and status-thrashing behavior were improved, but all telemetry still lands
in the general radio log. A dedicated telemetry panel is still deferred until runtime behavior is
confirmed on hardware.

### RES-006 — `chunker.py` still uses `assert` for defensive validation

- Severity: Low
- Files: `app/engine/pakt/chunker.py`

The current assertions are not load-bearing in normal runs, but they disappear under `python -O`.
This remains low priority unless chunking errors begin surfacing in production.

## Open Script Findings

### SCR-001 — bootstrap_third_party.py fallback and validation behavior still needs hardening

- Severity: Medium
- Files: `scripts/bootstrap_third_party.py`

Open script-level issues still present from the earlier script audit:
- fallback resource lookup is still packaging-layout-sensitive
- clone failures can still degrade into mixed dependency state
- offline mode still needs explicit validation that fallback sources exist
- bundled SA818 package inputs are not deeply validated before install

### SCR-002 — two_radio_diagnostic.py still lacks device validation and tighter playback/record teardown

- Severity: Medium
- Files: `scripts/two_radio_diagnostic.py`

The positive-value CLI validation issue is fixed, but the script still has open robustness gaps:
- output device indices are not pre-validated before `sd.play()`
- cleanup semantics still rely on broad exception-safe teardown rather than explicit connection state
- record/playback coordination is still timing-dependent in error paths

### SCR-003 — mesh_sim_tests.py still relies on globals and internal structures

- Severity: Medium
- Files: `scripts/mesh_sim_tests.py`

Remaining issues:
- unused import
- module-level mutable test state
- synthetic fixed timestamp base
- assertions against `_reassembly` internals instead of a public contract

### SCR-004 — play_wav_worker.py still lacks unsigned WAV and device hardening

- Severity: Medium
- Files: `scripts/play_wav_worker.py`

Remaining issues:
- uint8/unsigned WAV handling is incomplete
- peak normalization still assumes signed ranges
- output device indices are not pre-validated

### SCR-005 — capture_wav_worker.py still accepts invalid recording durations

- Severity: High
- Files: `scripts/capture_wav_worker.py`

`args.seconds` is still used directly in `int(args.seconds * args.sample_rate)` with no positive-value
validation, and the input device is still not explicitly validated before recording.

### SCR-006 — rx_score_worker.py still accepts invalid durations and does not classify empty capture cleanly

- Severity: High
- Files: `scripts/rx_score_worker.py`

`args.seconds` is still used directly for capture length with no positive-value validation. The worker
also still has no explicit "no audio captured" classification, so zero-frame or effectively empty
captures collapse into generic error handling.

### SCR-007 — tx_wav_worker.py cleanup semantics still need tightening

- Severity: Medium
- Files: `scripts/tx_wav_worker.py`

Remaining issues:
- PTT cleanup still relies on broad finally behavior rather than explicit connection-state handling
- playback exception handling should more directly guarantee teardown ordering

## Recommended Next Order

1. Do real-device validation on Raspberry Pi and macOS now that the preflight blockers are addressed.
2. Validate PAKT BLE behavior on hardware for RES-001 and RES-002.
3. Fix SCR-005 and SCR-006 next because they are still the highest-severity remaining script issues.
4. If packaging starts next, run the documented macOS/Linux/RPi exit checks against real builds.

# PAKT Integration Audit

Date: 2026-03-16
Target: `app`
Scope: PAKT-only review plus review of the existing repo-level `audit.md`

## Verification Run

Verified locally:

- `python3 -m compileall -q /Users/mac4pro64/Desktop/hamsoftware/Ham-Radio-Hat-Software/app /Users/mac4pro64/Desktop/hamsoftware/Ham-Radio-Hat-Software/integrations/pakt`
- `python3 /Users/mac4pro64/Desktop/hamsoftware/Ham-Radio-Hat-Software/app/main.py --help`
- PAKT import smoke:
  - `PaktService`
  - `Feature.APRS_2M`
  - `PaktCapabilities.assumed()`

Result: all passed locally.

## Review Of Existing `audit.md`

Reviewed:

- `/Users/mac4pro64/Desktop/hamsoftware/Ham-Radio-Hat-Software/audit.md`

Assessment:

- The existing audit file is a script audit for `app/scripts`.
- It is useful but unrelated to the new PAKT BLE integration work.
- It does not cover the new `app/engine/pakt/` backend, PAKT UI wiring, or PAKT mode dispatch logic.
- This file exists to cover that gap.

## Findings Status

The four findings from this audit are now fixed in code:

1. PAKT direct-send no longer creates a Comms chat row before the BLE write succeeds.
2. The shared footer connection indicator now reflects PAKT connection state.
3. PAKT scan refresh now re-synchronizes the selected address even when the display label persists.
4. PAKT `tx_result` notifications now reconcile back into `CommsManager` delivery state for PAKT outbound messages.

## Residual Risks

### 1. PAKT TX correlation is now host-side and still needs hardware validation

- Severity: Medium
- Files:
  - `/Users/mac4pro64/Desktop/hamsoftware/Ham-Radio-Hat-Software/app/engine/comms_mgr.py`
  - `/Users/mac4pro64/Desktop/hamsoftware/Ham-Radio-Hat-Software/app/engine/pakt/service.py`

What changed:

- The host app now creates a PAKT outbound message only after the BLE write succeeds.
- It uses a local placeholder ID until the first firmware `tx_result` arrives, then remaps that message to the firmware-assigned `msg_id`.

Remaining risk:

- This correlation path is correct against the documented contract and local smoke tests, but it still needs real-device confirmation under retries, reconnects, and back-to-back sends.

### 2. Hardware-backed PAKT behavior is still the main validation gap

- Severity: Medium

What remains:

- BLE scan/connect on real hardware
- bonded pairing flow for encrypted writes
- live TX result sequencing
- live telemetry and any reserved endpoints that may still be hardware-blocked

## Summary

The previously reported code-level gaps are fixed, and local verification remains green. The remaining work is now mostly on-device validation and product decisions, not obvious host-app wiring defects.

## Recommended Next Steps

1. Validate the new PAKT TX lifecycle on hardware: queue, first `tx`, terminal `acked` or failure.
2. Validate bonded-write UX on real pairing/auth failure paths.
3. Decide whether PAKT needs a dedicated richer tab for telemetry and command support.
4. Revisit RX packet surfacing once firmware maturity is confirmed.

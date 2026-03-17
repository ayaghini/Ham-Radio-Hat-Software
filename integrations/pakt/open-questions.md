# PAKT Open Questions

## Resolved for this pass

- Integration target is native PAKT BLE, not KISS-over-BLE.
- PAKT is a dedicated third hardware mode, not an SA818/DigiRig variation.
- Implementation code and desktop client behavior outrank stale prose examples.

## Outstanding protocol and source drift

1. Capability payload drift
   - `payload_contracts.md` still shows an older boolean capability example.
   - Firmware, handoff docs, and desktop client use `fw_ver/hw_rev/protocol/features`.
   - Host app follows the implemented shape.

2. Endpoint maturity drift
   - Device command is writable but not mature in firmware behavior.
   - Device status and RX packet schemas exist, but live production is incomplete or hardware-gated.

## App-side decisions captured in this first pass

1. UI shape
   - PAKT appears as the third hardware mode in the main selector.
   - First pass exposes dedicated PAKT controls rather than forcing full parity with APRS audio UI.

2. Direct outbound messaging
   - Existing direct-send action may map to native PAKT `tx_request` in PAKT mode.
   - APRS-specific audio tuning fields remain ignored for PAKT TX.

## Follow-up items after first pass

1. Decide whether PAKT should eventually get a richer dedicated tab instead of only a main-tab control section.
2. Decide how much of the Comms thread model should be generalized for native backends.
3. Revisit command endpoint support once firmware behavior is live.
4. Revisit RX packet/status surfacing when hardware validation is complete.
5. Add KISS-over-BLE only after the protocol becomes real and preferred by project direction.

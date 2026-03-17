# PAKT Onboarding

## What PAKT is

PAKT is a BLE-connected APRS pocket TNC/tracker built around an ESP32-S3 with SA818 radio, SGTL5000 codec, GPS, and BLE GATT host integration.

For the Windows host app, the current integration target is native PAKT BLE, not KISS-over-BLE.

## Source-of-truth order

Use these sources in this order when they disagree:

1. Firmware implementation
2. Desktop BLE test client behavior
3. Canonical payload contracts
4. Older prose/spec examples

Most relevant files:

- `/Users/mac4pro64/Desktop/pakt/PAKT/firmware/main/main.cpp`
- `/Users/mac4pro64/Desktop/pakt/PAKT/firmware/components/ble_services/BleServer.cpp`
- `/Users/mac4pro64/Desktop/pakt/PAKT/firmware/components/ble_services/include/pakt/BleUuids.h`
- `/Users/mac4pro64/Desktop/pakt/PAKT/app/desktop_test/pakt_client.py`
- `/Users/mac4pro64/Desktop/pakt/PAKT/app/desktop_test/transport.py`
- `/Users/mac4pro64/Desktop/pakt/PAKT/app/desktop_test/chunker.py`
- `/Users/mac4pro64/Desktop/pakt/PAKT/app/desktop_test/capability.py`
- `/Users/mac4pro64/Desktop/pakt/PAKT/app/desktop_test/telemetry.py`
- `/Users/mac4pro64/Desktop/pakt/PAKT/doc/aprs_mvp_docs/payload_contracts.md`

## Integration truths

- Discovery target: BLE device names beginning with `PAKT`
- Current advertised device name in repo: `PAKT-TNC`
- Write-capable BLE endpoints require encrypted and bonded links
- Capability read should happen immediately after connect
- Chunking is required when payload length exceeds `negotiated_mtu - 3`
- Native PAKT BLE is the current contract
- KISS-over-BLE is future-only

## Implemented vs not-yet-live

### Implemented in code

- BLE GATT table and UUID layout
- Capabilities endpoint
- Config read/write path
- TX request write path
- TX result notify path
- Chunking/reassembly model
- Desktop BLE client reconnect flow
- Telemetry parsers and notify subscriptions on the client side

### Specified but not fully live

- Device status production
- RX packet stream production
- Command characteristic behavior beyond accepting writes

### Hardware-blocked or stubbed

- Full on-device RF/audio APRS TX path validation
- Full on-device RX packet production
- GPS and power telemetry from complete live hardware sources

## Host-app fit summary

The host app already supports `SA818` and `DigiRig`, but both are tied to audio/PTT workflows. PAKT should be added as a third hardware mode with its own BLE-native backend and UI controls, while reusing the app’s queue/thread/UI coordination pattern.

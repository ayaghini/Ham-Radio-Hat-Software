# PAKT Native BLE Protocol Summary

## Discovery

- Match devices whose advertised name starts with `PAKT`
- Current repo-advertised name: `PAKT-TNC`

## UUID base

- Base UUID template: `544E4332-8A48-4328-9844-3F5C00000000`
- Insert the 16-bit endpoint id into the `0000` segment before the final `0000`

## Services and characteristics

### APRS service

- Service: `544E4332-8A48-4328-9844-3F5CA0000000`
- Config: `A001`, read/write, write requires encrypted+bonded
- Command: `A002`, write-without-response, encrypted+bonded, currently stub-like
- Status: `A003`, notify, schema reserved, not fully live
- Capabilities: `A004`, read
- RX packet: `A010`, notify, contract reserved, hardware-gated
- TX request: `A011`, write, encrypted+bonded
- TX result: `A012`, notify

### Telemetry service

- Service: `544E4332-8A48-4328-9844-3F5CA0200000`
- GPS telemetry: `A021`, notify
- Power telemetry: `A022`, notify
- System telemetry: `A023`, notify

## Canonical payloads used by host integration

### Capabilities

Implemented shape used by firmware and desktop client:

```json
{"fw_ver":"0.1.0","hw_rev":"EVT-A","protocol":1,"features":["aprs_2m","ble_chunking","telemetry","msg_ack","config_rw","gps_onboard"]}
```

Do not use the older boolean example when implementing host behavior.

### Config

```json
{"callsign":"W1AW","ssid":0}
```

### TX request

```json
{"dest":"APRS","text":"Hello, this is a beacon message","ssid":0}
```

### TX result

```json
{"msg_id":"42","status":"acked"}
```

Known statuses:

- `tx`
- `acked`
- `timeout`
- `cancelled`
- `error`

### Device status

```json
{"radio":"idle","bonded":true,"gps_fix":true,"pending_tx":0,"rx_queue":0,"uptime_s":3600}
```

### RX packet

```json
{"from":"W1AW-9","to":"APRS","path":"WIDE1-1","info":">PAKT v0.1"}
```

### GPS telemetry

```json
{"lat":43.8130,"lon":-79.3943,"alt_m":75.0,"speed_kmh":11.1,"course":54.7,"sats":8,"fix":1,"ts":764426119}
```

### Power telemetry

```json
{"batt_v":3.95,"batt_pct":72,"tx_dbm":30.0,"vswr":1.3,"temp_c":34.5}
```

### System telemetry

```json
{"free_heap":145000,"min_heap":112000,"cpu_pct":17,"tx_pkts":42,"rx_pkts":11,"tx_errs":0,"rx_errs":1,"uptime_s":1800}
```

## Chunking

- Header bytes: `msg_id`, `chunk_idx`, `chunk_total`
- Use chunking whenever payload length exceeds `mtu - 3`
- Effective payload bytes per chunk: `mtu - 6`
- Reassembly should tolerate duplicates and out-of-order chunks
- Reassembly should drop stale incomplete messages after timeout

## Security and error handling

- Config writes, command writes, and TX requests should be treated as encrypted+bonded operations
- Host app should classify insufficient-authentication/encryption BLE errors and surface pairing guidance
- Connect/reconnect should re-subscribe notifications after reconnect

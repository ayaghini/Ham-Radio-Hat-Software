# Cross-Platform v4 Support Matrix

Last updated: 2026-04-03

## Platform Status

| Capability | Windows | macOS | Linux | Raspberry Pi | Notes |
|---|---|---|---|---|---|
| Startup from source | baseline | confirmed | pending | confirmed | Linux desktop still needs first real run |
| Profile persistence | baseline | confirmed | pending | pending | macOS SA818/DigiRig/PAKT round-trips confirmed 2026-04-03 |
| Audio enumeration | baseline | confirmed | pending | pending | macOS: 3 outputs, 1 input confirmed 2026-04-03 |
| Serial scan | baseline | confirmed | likely-ok | likely-ok | macOS `/dev/cu.*` naming confirmed; no hardware ports present |
| Serial workflows | baseline | likely-ok | likely-ok | likely-ok | real-device validation still needed |
| DigiRig workflows | baseline | likely-ok | likely-ok | likely-ok | real-device validation still needed |
| PAKT BLE | baseline | needs hardware | needs hardware | needs hardware | transport module loads on macOS; live scan/permission dialog needs hardware |
| Packaging path | baseline | documented | documented | documented | build verification still open |

## Key Platform Notes

- macOS: packaged BLE needs `NSBluetoothAlwaysUsageDescription`
- Linux/Raspberry Pi: `dialout` and often `bluetooth` access are required
- Raspberry Pi uses the same active app as other platforms; use `app/run_rpi.sh`

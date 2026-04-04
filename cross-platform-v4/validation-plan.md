# Cross-Platform v4 Validation Plan

## Baseline Commands

Run from repo root:

```bash
# Note: use -x '\.venv' (not --exclude) when running Python 3.9; Python 3.13
# packages in .venv use match-statement syntax that 3.9 cannot compile.
python3 -m compileall -q -x '\.venv' app
python3 app/main.py --help
python3 app/scripts/smoke_test.py -v
python3 app/scripts/smoke_test.py -v --guards-only
python3 app/scripts/platform_validation.py
```

## Confirmed So Far

- macOS: compile/import/help/smoke pass recorded; source-run GUI bring-up confirmed
- macOS item-by-item headless validation (2026-04-03): **25 pass, 0 fail, 6 skip**
  - profile round-trip: SA818, DigiRig, PAKT all pass
  - mode switching: all three hardware-mode profiles confirmed
  - audio enumeration: 3 outputs (LG UltraFine, Mac mini Speakers, WH-1000XM4), 1 input
  - serial scan: pyserial executes; `/dev/cu.*` naming confirmed; no hardware ports present
  - BLE transport module loads; TransportState members verified; bleak absent (gracefully guarded — SKIP)
  - platform paths: `~/Library/Application Support/HamHatCC` (exists), `~/Library/Logs/HamHatCC`
  - DisplayConfig: default scale=1.0, rpi_720p scale=1.5 compact_padding=2
  - APRS message payload builder confirmed
  - BLE permission dialog (live scan): cannot test without bleak installed + hardware present
- Raspberry Pi: source-run GUI bring-up confirmed with `python3 main.py --rpi`
- smoke test is safe in sparse environments
- guard-only optional-dependency validation exists
- `platform_validation.py` script created; ready to run on Linux desktop and RPi

## Still Needed

### Linux Desktop

- first real GUI launch
- audio enumeration
- serial scan
- profile save/load
- BLE prerequisites check
- run `python3 app/scripts/platform_validation.py` for full checklist

### macOS

- BLE permission flow (requires bleak + hardware; all other items confirmed)

### Raspberry Pi

- wheel zoom
- serial scan
- audio enumeration
- profile persistence
- BLE prerequisites/path

### Hardware-backed

- PAKT BLE scan/connect/TX result behavior
- SA818 and DigiRig real-device workflows

### Packaging

- macOS `.app` exit check
- Linux packaging/deployment exit check
- Raspberry Pi deployment verification

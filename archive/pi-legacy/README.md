# uConsole HAM HAT Control Center (Raspberry Pi)

Legacy status:
- This package is a stale Raspberry Pi-specific snapshot.
- It is no longer the primary app path for current work.
- The active cross-platform app now lives at `app`, even for Raspberry Pi.

Raspberry Pi package for SA818 bring-up and radio control.

## Includes

- Serial port discovery and SA818 connect test
- SA818 radio programming (frequency, offset, bandwidth, squelch)
- CTCSS or DCS tone setup
- Audio filter setup (`AT+SETFILTER`)
- Volume setup (`AT+DMOSETVOLUME`)
- Local profile save/load
- Optional third-party bootstrap (SA818 + SRFRS repos)

## Requirements

- Raspberry Pi OS with desktop
- Python 3.9+
- `python3-venv`, `python3-tk`, `git`
- USB serial access permissions

Install system packages:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-tk git
```

## Quick Start

Preferred current path for Raspberry Pi work:

```bash
cd ../../app
python3 main.py --rpi
```

Legacy package quick start:

```bash
cd archive/pi-legacy
chmod +x run_pi.sh build_pi.sh
./run_pi.sh
```

## Optional Build

```bash
./build_pi.sh
```

Binary output:
- `dist/ham-hat-control`

## Docs

- Quick start: `QUICK_START.md`
- Full user manual: `../../docs/user-manual.md`
- Functional spec: `../../docs/specifications/functional-specification.md`

## Notes

- Use either CTCSS or DCS at one time.
- DCS format is `047N` or `047I`.
- Stay within legal frequencies for your license and region.

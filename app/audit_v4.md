# v4 App Audit

Updated: 2026-04-03
Scope: canonical audit for `app`

## Verification Baseline

```text
# Use -x '\.venv' (not --exclude) on Python 3.9; .venv may contain Python 3.13
# packages (bleak, numpy, scipy) with match-statement syntax that 3.9 rejects.
python3 -m compileall -q -x '\.venv' app
python3 app/main.py --help
python3 app/scripts/smoke_test.py -v
python3 app/scripts/smoke_test.py -v --guards-only
python3 app/scripts/mesh_sim_tests.py
python3 app/scripts/platform_validation.py    # full cross-platform checklist
```

Local status (macOS Darwin 25.4.0, arm64, Python 3.9.6 — 2026-04-03):
- compile/smoke/mesh checks pass
- `platform_validation.py` result: 25 pass, 0 fail, 6 skip
  - profile round-trip (SA818/DigiRig/PAKT): pass
  - audio enumeration (3 out, 1 in): pass
  - serial scan + `/dev/cu.*` naming: pass
  - PAKT transport module + TransportState: pass
  - platform paths, DisplayConfig, APRS payload: pass
  - bleak/PIL/scipy/sv_ttk/requests absent: 6 SKIP (all gracefully guarded)
- script hardening work is complete
- no hardware-backed validation was performed locally

## Open Risks

### RES-001 — PAKT TX correlation still needs hardware validation

- Severity: Medium
- Files: `app/engine/comms_mgr.py`, `app/engine/pakt/service.py`

Host-side `pakt-local:N` to firmware `msg_id` remapping looks correct by static review and smoke coverage, but still needs real-device confirmation under retries, reconnects, and back-to-back sends.

### RES-002 — PAKT BLE runtime behavior remains hardware-blocked

- Severity: Medium

BLE scan/connect, bonded-write behavior, TX result sequencing, and live telemetry still need a physical device.

### RES-003 — PAKT callback wiring still depends on post-construction mutation

- Severity: Low
- Files: `app/engine/pakt/service.py`

Safe today, but lifecycle-fragile compared with constructor injection.

### RES-004 — `_make_tx_snapshot()` still returns `None` for PAKT by design

- Severity: Low
- Files: `app/app.py`

Not a live bug now; keep in view if future shared RX/TX packet paths are added.

### RES-005 — PAKT telemetry still lacks a dedicated structured panel

- Severity: Low
- Files: `app/ui/main_tab.py`, `app/app.py`

Telemetry still lands in general log/status output rather than a dedicated panel.

### RES-006 — `chunker.py` still uses `assert` for defensive validation

- Severity: Low
- Files: `app/engine/pakt/chunker.py`

Low priority unless chunking defects start surfacing in production.

## Next Order

1. Linux desktop bring-up — run `app/run_linux.sh`, then `python3 app/scripts/platform_validation.py`
2. macOS BLE permission flow — requires bleak installed + real device
3. Raspberry Pi workflow validation — run `app/scripts/platform_validation.py` on device
4. PAKT hardware validation
5. packaging build/exit checks

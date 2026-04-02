# Cross-Platform v4 Validation Plan

## Validation Philosophy

Portability work should be measured at three levels:

1. static integrity
2. local runtime smoke
3. platform-specific runtime validation

## Baseline Checks

Run on every substantial pass:

```
python3 -m compileall -q <v4 root>
python3 <v4 root>/main.py --help
python3 <v4 root>/scripts/smoke_test.py
```

## Baseline Results

### Pass 1 (2026-04-01 — macOS Darwin 25.4.0)

```
python3 -m compileall -q windows-release/ham_hat_control_center_v4   → clean (exit 0)
python3 main.py --help                                                 → green (exit 0)
```

### Pass 2 (2026-04-01 — macOS Darwin 25.4.0, after all Phase 2 changes)

```
python3 -m compileall -q windows-release/ham_hat_control_center_v4   → clean (exit 0)
python3 main.py --help                                                 → green (exit 0)
python3 scripts/smoke_test.py -v                                       → 11/11 PASS
```

Smoke test detail:
- required imports          PASS
- AppState import           PASS
- sv_ttk guard              PASS  (absent, guard OK)
- bleak guard               PASS  (absent, guard OK)
- scipy guard               PASS  (absent, numpy fallback OK)
- pycaw guard               PASS  (absent on darwin, correct)
- winsound guard            PASS  (absent on darwin, correct)
- profile round-trip        PASS
- platform paths            PASS  (data=~/Library/Application Support/HamHatCC)
- audio device listing      PASS  (2 outputs, 0 inputs — no audio hardware connected)
- APRS modem                PASS

### Follow-up Audit Note (2026-04-01 — current workspace)

```
python3 -m compileall -q windows-release/ham_hat_control_center_v4/app  → clean (exit 0)
python3 windows-release/ham_hat_control_center_v4/main.py --help         → green (exit 0)
python3 windows-release/ham_hat_control_center_v4/scripts/smoke_test.py -v
  → passes; missing hard runtime deps are now classified as SKIP
python3 windows-release/ham_hat_control_center_v4/scripts/smoke_test.py -v --guards-only
  → passes
```

Interpretation:
- this does not invalidate the earlier macOS pass result
- `smoke_test.py` is now safe to run in sparse environments
- CI now has a guard-only smoke step on non-Windows runners

## Whole-App Smoke Areas

### Startup

- app imports cleanly ✓
- optional dependency failures are partially validated only; guard code exists, but current smoke coverage does not fully separate missing required runtime deps from missing optional deps
- theme fallback works if sv_ttk is absent ✓

### Profiles and State

- default profile loads ✓
- profile save/load round-trips ✓ (verified in smoke_test.py)
- upgrade-safe migration from legacy in-tree profiles is now implemented
- switching hardware mode does not corrupt stored settings ✓ (static audit confirmed)

### Mode Switching

- SA818 to DigiRig: static audit — clean routing
- DigiRig to PAKT: static audit — clean routing
- PAKT to SA818: static audit — clean routing
- stale button state on PAKT round-trip: fixed in SIP-003
- footer indicator reset on mode change: fixed in AUD-002

### Messaging and Comms

- PAKT pending timeout: fixed in SIP-001 (2 min, 30s tick)
- TX result reconciliation: fixed in third fix pass
- No hard crash without hardware: confirmed by --help and import smoke

### Scripts

- `scripts/smoke_test.py`: historical macOS pass recorded; sparse-environment behavior now skips hard-runtime-dependent checks cleanly
- `scripts/two_radio_diagnostic.py`: argument validation improved in SIP-007; cross-platform ✓
- `scripts/bootstrap_third_party.py`: cross-platform; --dev help note updated ✓
- Worker scripts (play/capture/rx_score/tx_wav): sounddevice/numpy based and portable in principle, but several script-level hardening issues remain in the canonical audit

## Platform Validation Checklist

| Check | Windows | macOS | Linux | Raspberry Pi |
|---|---|---|---|---|
| compileall | passing (prior) | passing ✓ 2026-04-01 | pending | pending |
| import smoke | passing (prior) | passing ✓ 2026-04-01 | pending | pending |
| startup smoke (--help) | passing (prior) | passing ✓ 2026-04-01 | pending | pending |
| smoke_test.py | n/a | historical pass ✓ 2026-04-01 | pending | pending |
| GUI startup | passing (prior) | pending | pending | pending |
| profile round-trip | passing (prior) | passing ✓ (smoke_test) | pending | pending |
| mode switch smoke | passing (prior) | pending | pending | pending |
| audio enumeration | passing (prior) | 2 outputs found ✓ | pending | pending |
| auto USB audio select | passing (prior) | pending (keywords added) | pending | pending |
| BLE scan | passing (prior) | pending (TCC perm needed) | pending | pending |
| dependency absence smoke | passing (prior) | improved | pending | pending |
| packaging smoke | passing (prior) | unknown | unknown | unknown |

## Acceptance Criteria For "Platform Boot Support"

A platform can be considered boot-supported when:

- the app launches without code changes specific to that machine
- missing optional dependencies do not crash the app unexpectedly
- profile load/save works
- hardware mode switching works
- unsupported hardware paths fail with clear messaging

## Running the Smoke Test

```
# From the app root directory:
python3 scripts/smoke_test.py        # quick pass/fail
python3 scripts/smoke_test.py -v     # verbose (all checks with detail)
```

The test requires: `numpy`, `sounddevice`, `pyserial` (hard requirements).
Guard checks for optional deps (sv_ttk, bleak, scipy, pycaw, winsound) exist, but the current test
flow now skips hard-runtime-dependent checks cleanly and supports `--guards-only` for guard-only validation.

## Next Validation Steps

1. Run full GUI startup on macOS with installed requirements and verify profile save/load plus BLE permission flow
2. Run smoke_test.py and GUI startup on Linux (Ubuntu/Debian recommended) — verify ALSA/PipeWire enumeration and serial scan
3. Run `python3 main.py --rpi` on the real 5-inch Raspberry Pi screen and verify layout, wheel zoom, and hardware permission messaging
4. Validate PAKT BLE on real hardware (macOS and Linux/RPi)
5. Run packaging/deployment verification steps from the release checklist

# Cross-Platform v4 Validation Plan

## Validation Philosophy

Portability work should be measured at three levels:

1. static integrity
2. local runtime smoke
3. platform-specific runtime validation

## Baseline Checks

Run on every substantial pass:

- `python3 -m compileall -q /Users/mac4pro64/Desktop/hamsoftware/Ham-Radio-Hat-Software/windows-release/ham_hat_control_center_v4`
- `python3 /Users/mac4pro64/Desktop/hamsoftware/Ham-Radio-Hat-Software/windows-release/ham_hat_control_center_v4/main.py --help`
- import smoke for high-value app modules

## Whole-App Smoke Areas

### Startup

- app imports cleanly
- optional dependency failures are actionable
- theme fallback works if optional theming dependency is absent

### Profiles and State

- default profile loads
- profile save/load round-trips
- switching hardware mode does not corrupt stored settings

### Mode Switching

- SA818 to DigiRig
- DigiRig to PAKT
- PAKT to SA818
- no stale connection labels
- no stale control enablement
- no wrong backend action routing

### Messaging and Comms

- direct message path
- PAKT pending timeout behavior
- delivery/failure state rendering
- no hard crash without hardware attached

### Scripts

- scripts parse `--help`
- argument validation catches obviously invalid values
- path assumptions are documented

## Future Platform Validation Checklist

These should be filled in per platform during execution:

| Check | Windows | macOS | Linux | Raspberry Pi |
|---|---|---|---|---|
| import smoke | pending | pending | pending | pending |
| startup smoke | pending | pending | pending | pending |
| profile round-trip | pending | pending | pending | pending |
| mode switch smoke | pending | pending | pending | pending |
| dependency absence smoke | pending | pending | pending | pending |
| packaging smoke | pending | pending | pending | pending |

## Acceptance Criteria For “Platform Boot Support”

A platform can be considered boot-supported when:

- the app launches without code changes specific to that machine
- missing optional dependencies do not crash the app unexpectedly
- profile load/save works
- hardware mode switching works
- unsupported hardware paths fail with clear messaging

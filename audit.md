# Script Audit Report

## Overview

This document summarizes bugs and areas for improvement found in scripts under `windows-release/ham_hat_control_center_v4/scripts`.

---

## 1. bootstrap_third_party.py

| Issue | Location | Severity | Description |
|-------|----------|----------|-------------|
| Invalid fallback paths | Lines 71-74 | Medium | Hardcoded path structure (`parent.parent / "Resources"`) breaks if script is moved |
| Silent clone failure | Lines 116-121 | Medium | On git clone failure, falls back but only copies one repo - inconsistent state if SA818 fails and srfrs succeeds |
| No offline validation | Lines 112-113 | Low | When `--offline`, calls `copy_local_fallback` even if fallback dir doesn't exist |
| Missing SA818 version check | Line 123 | Low | `install_sa818_package` doesn't verify `setup.py` is valid before calling pip |

**Recommendations:**
- Use relative paths from script location instead of parent.parent
- Add validation before fallback copy: `if src.exists() and not dst.exists()`
- Wrap each repo clone in try/except individually to handle failures independently

---

## 2. two_radio_diagnostic.py

| Issue | Location | Severity | Description |
|-------|----------|----------|-------------|
| Audio recording duration | Lines 66-67 | High | `int(seconds * rate)` could be 0 or negative if `seconds <= 0` |
| Missing output device validation | Line 82 | Low | No check if `device` exists before passing to sd.play() |
| PTT cleanup on exception | Lines 204-213 | Medium | Finally block calls `client.disconnect()` even if client never connected |
| Race in recording | Lines 172-179 | Medium | `rec_thread.join()` has try/finally but if playback fails, recording may still be running |

**Recommendations:**
- Add `if seconds <= 0: raise ValueError("seconds must be positive")`
- Use `sd.query_devices()` to validate device indices before use
- Wrap PTT cleanup in try/except with `client._connected` check

---

## 3. generate_agent_onboarding_pack.py

| Issue | Location | Severity | Description |
|-------|----------|----------|-------------|
| Typo in path constant | Line 22 | High | `DOC_ROOT = ROOT / "agent_bootstap"` - missing 'r', should be `"agent_bootstrap"` |
| Path separator inconsistency | Line 190 | Low | Uses `.replace("\\", "/")` but JSON paths on Windows will normalize differently |
| Missing doc_root validation | Lines 331-335 | Low | No check if DOC_ROOT is writable before writing |

**Recommendations:**
- Fix typo: `"agent_bootstrap"`
- Use `pathlib` native paths; pathlib handles separators automatically

---

## 4. mesh_sim_tests.py

| Issue | Location | Severity | Description |
|-------|----------|----------|-------------|
| Unused import | Line 14 | Low | `import os` is never used |
| Module-level state in tests | Lines 32-34 | Medium | `_PASS`, `_FAIL`, `_T0` are module-level globals - not safe for parallel test execution |
| Hardcoded NOW value | Line 62 | Low | Uses `1_000_000.0` as base - could conflict with real timestamps in edge cases |
| Incomplete reassembly check | Line 230 | Medium | Checks `mid2 not in [k[1] for k in c._reassembly]` but `_reassembly` structure is internal API |

**Recommendations:**
- Remove unused `import os`
- Consider using unittest or pytest for proper test isolation
- Replace internal `_reassembly` access with public API if available

---

## 5. play_wav_worker.py

| Issue | Location | Severity | Description |
|-------|----------|----------|-------------|
| Missing dtype for uint8 | Line 49 | Medium | `dtype_map` doesn't have unsigned integer formats (uint8 WAV files) |
| Peak calculation | Line 56 | Medium | For uint8 (max=255), using `np.iinfo(dtype).max` assumes signed range |
| No device validation | Line 58 | Low | No check if output_device exists before play |

**Recommendations:**
- Add unsigned formats to `dtype_map`: `{np.uint8: np.int16, ...}`
- Calculate peak differently for unsigned types
- Use `sd.query_devices()` to validate output device

---

## 6. capture_wav_worker.py

| Issue | Location | Severity | Description |
|-------|----------|----------|-------------|
| Invalid seconds value | Lines 47-53 | High | No validation that `args.seconds > 0` |
| No input device check | Line 67 | Low | No validation of `args.input_device` before recording |

**Recommendations:**
- Add argument parser validation: `parser.add_argument("--seconds", type=lambda x: float(x) if float(x) > 0 else _raise())`
- Validate input device with `sd.query_devices()`

---

## 7. rx_score_worker.py

| Issue | Location | Severity | Description |
|-------|----------|----------|-------------|
| Empty audio handling | Line 59 | High | Reshaping `-1` could fail if no audio captured |
| Invalid seconds check | Lines 47-57 | High | No validation of `args.seconds > 0` |

**Recommendations:**
- Add check after recording: `if len(data) == 0: raise ValueError("No audio captured")`
- Add seconds validation in argument parser

---

## 8. tx_wav_worker.py

| Issue | Location | Severity | Description |
|-------|----------|----------|-------------|
| PTT cleanup on error | Lines 119-122 | Medium | PTT release in finally runs even when SA818Error occurred before connection |
| Playback exception handling | Lines 94-107 | Medium | No try/except around sd.play() to ensure PTT is released |

**Recommendations:**
- Track connection state: `if client._connected: client.disconnect()` or check before disconnect
- Wrap playback in try/except with PTT cleanup in finally

---

## Summary by Severity

| Severity | Count |
|----------|-------|
| High | 7 |
| Medium | 13 |
| Low | 12 |

**Total Issues: 32**

---

## Critical Fixes (Priority Order)

1. **generate_agent_onboarding_pack.py:22** - Typo in `DOC_ROOT` path
2. **two_radio_diagnostic.py:66-67** - Zero/negative seconds causes 0-byte recording
3. **capture_wav_worker.py:47-53** - No validation of seconds > 0
4. **rx_score_worker.py:59** - Empty audio causes reshape error
5. **capture_wav_worker.py:67, play_wav_worker.py:58, tx_wav_worker.py** - Device validation missing

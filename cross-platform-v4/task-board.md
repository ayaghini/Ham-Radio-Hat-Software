# Cross-Platform v4 Task Board

Status keys: `todo`, `in_progress`, `done`

## Current Priorities

| ID | Status | Task | Exit Check |
|---|---|---|---|
| CP-512 | todo | Linux desktop bring-up | `app/run_linux.sh` launches cleanly; then run `python3 app/scripts/platform_validation.py` |
| CP-520 | in_progress | macOS workflow validation | source-run validation is substantially complete; BLE permission flow still needs hardware |
| CP-521 | todo | Raspberry Pi workflow validation | wheel zoom, serial, audio, profile save/load, BLE prerequisites; run `platform_validation.py` |
| CP-530 | todo | PAKT hardware validation | real BLE scan/connect/TX result behavior verified |
| CP-540 | in_progress | macOS packaging verification | exit checks substantially complete (2026-04-04): launch/no-crash, profile autosave (status bar confirmed), audio devices visible in UI (Output: LG ULTRAFINE, Input: WH-1000XM4 in Control tab), serial port auto-detected in UI (/dev/cu.debug-console), bundle contents confirmed, plist permissions present; remaining: button-click verification (blocked by macOS 15 Accessibility requirement) and BLE dialog (needs hardware) |
| CP-541 | todo | Linux packaging verification | spec + build script ready (`app/packaging/`); first real Linux build still needs to be run |
| CP-542 | todo | Raspberry Pi deployment verification | venv install + autostart flow verified on device |

## Completed Foundations

| ID | Status | Task | Notes |
|---|---|---|---|
| CP-100 | done | Architecture seams and platform assumptions | serial/audio/BLE/path assumptions documented |
| CP-103 | done | User-data path migration | writable app-data path implemented |
| CP-200 | done | Whole-app integrity audit | routing/state/profile issues fixed |
| CP-203 | done | Script hardening audit | worker/bootstrap script findings resolved |
| CP-303 | done | Non-Windows PAKT reconnect review | callback-thread safety hardened |
| CP-400 | done | Packaging strategies documented | Windows/macOS/Linux/RPi paths written down |
| CP-500 | done | Smoke coverage | smoke test + guard-only CI in place |
| CP-501 | done | Platform validation script | `platform_validation.py` — 44 pass 0 fail 7 skip on macOS; per-function scroll checks; display-env + group checks for Linux |
| CP-502 | done | Packaging artifacts (spec + build scripts) | `app/packaging/app_mac.spec`, `app_linux.spec`, `build_mac.sh`, `build_linux.sh` |
| CP-510 | done | Raspberry Pi bring-up | user-confirmed |
| CP-511 | done | macOS bring-up | user-confirmed |
| CP-600 | done | Repo cleanup | `app/` canonical, `archive/` for historical snapshots |
| CP-601 | done | Launcher parity | all supported OS targets have source launchers |

## Notes

- Use `app/audit_v4.md` for current open app/script risks.
- Do not spend time on archived packages unless a historical reference is required.

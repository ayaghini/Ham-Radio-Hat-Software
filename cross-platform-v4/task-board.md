# Cross-Platform v4 Task Board

Status keys:

- `todo`
- `in_progress`
- `blocked`
- `done`

## Foundation

| ID | Status | Task | Notes / Exit Check |
|---|---|---|---|
| CP-001 | todo | Build dependency inventory for v4 | Every runtime import classified by portability risk |
| CP-002 | todo | Record current startup and smoke baseline | Startup, profile load, mode switch, message flow documented |
| CP-003 | todo | Create platform assumption inventory | Windows-only and platform-sensitive assumptions listed |
| CP-004 | todo | Define support policy by target platform | Must be reflected in `support-matrix.md` |

## Architecture

| ID | Status | Task | Notes / Exit Check |
|---|---|---|---|
| CP-100 | todo | Define serial adapter boundary | No UI code should depend on platform-specific serial details |
| CP-101 | todo | Define audio adapter boundary | Device enumeration and routing isolated |
| CP-102 | todo | Define BLE adapter/runtime boundary | PAKT transport behavior isolated from OS stack details |
| CP-103 | todo | Define app-data and filesystem path helper | Profiles, logs, caches portable |
| CP-104 | todo | Normalize optional dependency handling | App starts cleanly with actionable errors/fallbacks |

## Whole-App Integrity

| ID | Status | Task | Notes / Exit Check |
|---|---|---|---|
| CP-200 | todo | Audit hardware-mode switching across all modes | No stale controls, labels, or fallthrough actions |
| CP-201 | todo | Audit profile save/load across all modes | No stale values leaking across modes |
| CP-202 | todo | Audit startup path for platform assumptions | Clean behavior on dependency absence |
| CP-203 | todo | Audit scripts for portability and argument safety | High-value scripts validated first |
| CP-204 | todo | Audit logging/status surfaces for consistency | Shared status and per-mode status remain coherent |

## PAKT-Specific Within Cross-Platform Scope

| ID | Status | Task | Notes / Exit Check |
|---|---|---|---|
| CP-300 | todo | Define desktop BLE support expectations by OS | macOS/Linux behavior documented even if hardware validation is deferred |
| CP-301 | todo | Harden stale-pending PAKT TX policy | Timeout behavior documented and tested |
| CP-302 | todo | Improve structured telemetry UX | Must not overstate unverified firmware behavior |
| CP-303 | todo | Review reconnect/subscription behavior under non-Windows assumptions | Design and code paths documented |

## Packaging and Release

| ID | Status | Task | Notes / Exit Check |
|---|---|---|---|
| CP-400 | todo | Define Windows packaging baseline | Existing release path documented |
| CP-401 | todo | Define macOS packaging path | Bundle/signing/notarization documented |
| CP-402 | todo | Define Linux packaging path | At least one preferred distribution format selected |
| CP-403 | todo | Define Raspberry Pi deployment path | Install/update/runtime access documented |

## Verification and CI

| ID | Status | Task | Notes / Exit Check |
|---|---|---|---|
| CP-500 | todo | Create platform smoke checklist | Must include import/startup/profile/mode-switch coverage |
| CP-501 | todo | Add dependency-absence smoke coverage | Optional dependency failures must be actionable |
| CP-502 | todo | Define CI matrix | Windows, macOS, Linux |
| CP-503 | todo | Add release verification checklist | Packaging plus runtime sanity checks |

## Recommended Execution Order

1. CP-001
2. CP-002
3. CP-003
4. CP-100 to CP-104
5. CP-200 to CP-204
6. CP-500 to CP-502
7. CP-400 to CP-403

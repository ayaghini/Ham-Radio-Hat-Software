# Cross-Platform v4 Migration Program

Scope: expand `windows-release/ham_hat_control_center_v4` into a maintainable multi-platform app that supports:

- Windows
- macOS
- Linux desktop
- Raspberry Pi OS

This folder is the execution workspace for that migration effort. It is designed so future agent passes can pick up work in a structured way, update status, and leave a clear trail.

## Goals

- Preserve current v4 behavior while removing Windows-only assumptions.
- Keep hardware modes working across platforms:
  - SA818
  - DigiRig
  - PAKT
- Isolate platform-specific code behind explicit adapters.
- Add validation, packaging, and release paths per platform.
- Avoid a rewrite unless the existing app architecture proves to be a hard blocker.

## Program Principles

- Prefer incremental portability over a risky big-bang rewrite.
- Separate app logic from OS-specific access layers.
- Treat Raspberry Pi as its own deployment target, not just “Linux desktop”.
- Make all platform claims test-backed.
- Keep documentation current as implementation truth changes.

## Files In This Folder

- `roadmap.md`
  - phased migration plan and current program status
- `task-board.md`
  - execution tracker with ownership-ready tasks
- `architecture-plan.md`
  - target architecture and refactoring seams
- `support-matrix.md`
  - platform support definition and dependency matrix
- `validation-plan.md`
  - checks, smoke tests, and acceptance criteria
- `packaging-and-release.md`
  - packaging strategy by target platform
- `risk-register.md`
  - major risks, mitigations, and monitoring points
- `agent-prompt.md`
  - ready-to-use prompt for a future agent pass

## Status

Program state: planning prepared, implementation not started.

Recommended first execution pass:

1. perform a portability audit of the current v4 app
2. classify all Windows-specific assumptions
3. create a platform abstraction backlog
4. establish baseline smoke tests before refactoring

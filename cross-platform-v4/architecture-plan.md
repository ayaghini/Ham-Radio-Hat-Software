# Cross-Platform v4 Architecture Plan

## Current Reality

The current v4 app is a desktop-first Tkinter application with mixed responsibilities:

- UI orchestration in `app/app.py`
- hardware and APRS logic in `app/engine/`
- transport-specific details embedded in engine modules
- release structure centered on `windows-release/`

This is workable for migration, but only if OS-sensitive details are isolated instead of spreading further.

## Target Architecture

The target architecture should separate:

1. app orchestration
2. hardware-mode orchestration
3. OS/platform services
4. hardware transports
5. UI

## Required Boundaries

### 1. Platform Services

Introduce explicit service boundaries for:

- serial port enumeration and open/close behavior
- audio device enumeration and selection
- BLE capability detection and connection support
- app-data, cache, and profile paths
- dependency diagnostics

The app should ask for capabilities, not infer them from OS names scattered across the code.

### 2. Hardware Backends

Keep hardware modes explicit:

- SA818 backend
- DigiRig backend
- PAKT backend

Each backend should expose supported actions and reject unsupported ones clearly.

### 3. UI Layer

The UI should:

- bind to state
- call explicit app actions
- avoid direct OS or transport logic
- adapt visibility and enablement based on capabilities and hardware mode

### 4. Packaging Layer

Packaging should be treated as a separate concern with per-platform flows, not embedded assumptions inside runtime code.

## Migration Design Rules

- no new Windows-only assumptions
- no hidden mode fallthrough
- no direct path assumptions for per-user data
- no hard crash on optional dependency absence when a graceful fallback is possible
- platform-specific behavior must be documented and testable

## Likely Refactoring Seams

- `app/app.py`
  - startup flow
  - event dispatch
  - mode switching
  - dependency setup
- `app/app_state.py`
  - profile/application path handling
  - shared state lifecycle
- `app/engine/`
  - serial, audio, BLE transport seams
  - hardware backend capability boundaries
- `scripts/`
  - shell/path assumptions
  - validation hardening

## Non-Goals For The First Pass

- full UI framework rewrite
- redesigning APRS features for parity across all modes
- claiming hardware support before runtime and packaging paths are validated

# Cross-Platform v4 Risk Register

## High Risks

### R-001 Audio portability

Why it matters:

- APRS audio workflows depend on device enumeration and timing-sensitive behavior

Mitigation:

- isolate audio adapter
- add mode-specific smoke checks
- document unsupported combinations clearly

### R-002 BLE portability for PAKT

Why it matters:

- desktop BLE behavior can vary by OS and dependency stack

Mitigation:

- isolate BLE runtime checks
- make fallback/error messaging explicit
- define support expectations per platform before claiming parity

### R-003 Hidden Windows assumptions

Why it matters:

- paths, scripts, packaging, and startup behavior may silently rely on Windows norms

Mitigation:

- complete Phase 1 portability audit before broad refactoring

## Medium Risks

### R-010 UI framework limits

Why it matters:

- Tkinter may remain workable, but portability polish may expose framework limits

Mitigation:

- keep Tk for first migration passes
- reassess only if it becomes a real blocker

### R-011 Optional dependency drift

Why it matters:

- some dependencies may be available on the original development machine but missing elsewhere

Mitigation:

- add dependency-absence smoke checks
- guard optional imports cleanly

### R-012 Platform packaging sprawl

Why it matters:

- each platform can create its own one-off packaging path unless standardized

Mitigation:

- document packaging strategy early
- keep per-platform specifics in one file

## Monitoring Signals

- startup crashes on missing imports
- platform-specific “works on one machine only” fixes
- stale status/UI state after mode switching
- growing number of conditional branches by OS name
- packaging instructions drifting from runtime reality

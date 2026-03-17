# Cross-Platform v4 Roadmap

Status date: 2026-03-16
Program status: planned
Target app: `windows-release/ham_hat_control_center_v4`

## Program Outcome

Deliver a single v4 codebase that can run and be packaged for Windows, macOS, Linux desktop, and Raspberry Pi OS with explicit support boundaries, validation, and release steps.

## Phases

### 0. Baseline and Guardrails

Status: `todo`

Goals:

- capture current behavior before portability work starts
- establish a no-regression baseline
- identify the highest-risk platform dependencies

Tasks:

- `todo` capture current startup, mode-switch, profile, and messaging smoke paths
- `todo` inventory all dependencies in `requirements.txt` and runtime imports
- `todo` classify dependencies as pure Python, optional native, OS-coupled, or packaging-coupled
- `todo` create a baseline failure matrix for missing dependencies
- `todo` record current release assumptions from `windows-release/ham_hat_control_center_v4`

Exit criteria:

- baseline smoke checks are documented
- dependency inventory is complete
- major portability blockers are known

### 1. Portability Audit

Status: `todo`

Goals:

- understand exactly what is Windows-specific today
- map every OS-sensitive seam in the app

Tasks:

- `todo` audit serial access assumptions
- `todo` audit audio device enumeration and routing assumptions
- `todo` audit BLE transport assumptions for PAKT
- `todo` audit filesystem path and app-data assumptions
- `todo` audit scripts for shell, path, and dependency portability
- `todo` audit UI/theme dependencies and startup behavior
- `todo` audit packaging and launcher assumptions

Exit criteria:

- all platform-sensitive seams are documented in `architecture-plan.md`
- all blockers are entered in `task-board.md`

### 2. Architecture Extraction

Status: `todo`

Goals:

- isolate platform-specific behavior behind explicit adapters
- reduce direct OS coupling in UI and orchestration layers

Tasks:

- `todo` define adapter interfaces for serial, audio, BLE, and app paths
- `todo` move direct OS access out of UI code where needed
- `todo` normalize startup checks and dependency-failure handling
- `todo` reduce hardware-mode fallthrough across shared flows
- `todo` add capability-based runtime checks instead of implicit platform assumptions

Exit criteria:

- platform-sensitive operations are reachable through explicit service boundaries
- app startup and error reporting remain intact

### 3. Cross-Platform Runtime Enablement

Status: `todo`

Goals:

- get the app to boot and run cleanly on macOS and Linux desktop
- keep Raspberry Pi as a first-class target during design

Tasks:

- `todo` enable clean startup on macOS with missing-feature fallbacks where needed
- `todo` enable clean startup on Linux desktop with missing-feature fallbacks where needed
- `todo` add Raspberry Pi specific runtime notes and access requirements
- `todo` ensure profiles, logs, and app-data paths resolve cleanly on all targets
- `todo` validate optional dependency fallbacks on each platform

Exit criteria:

- app boots on macOS and Linux desktop
- platform errors are actionable
- no known Windows-only startup blockers remain

### 4. Hardware Mode Portability

Status: `todo`

Goals:

- ensure each hardware mode behaves correctly on supported targets

Tasks:

- `todo` validate SA818 serial workflow portability assumptions
- `todo` validate DigiRig workflow portability assumptions
- `todo` validate PAKT BLE stack abstraction and OS-specific constraints
- `todo` review mode-switch integrity across platforms
- `todo` remove stale UI state and shared-status inconsistencies

Exit criteria:

- support boundaries are explicit per mode and per platform
- unsupported combinations fail clearly

### 5. Validation and Automation

Status: `todo`

Goals:

- make the migration measurable and repeatable

Tasks:

- `todo` add platform-oriented smoke tests
- `todo` add profile and mode-switch regression checks
- `todo` add import and dependency-absence checks
- `todo` add script validation coverage where practical
- `todo` define CI strategy for Windows, macOS, and Linux

Exit criteria:

- verification steps are documented and runnable
- regression coverage exists for high-risk flows

### 6. Packaging and Release

Status: `todo`

Goals:

- define sustainable release flows for each platform

Tasks:

- `todo` define Windows packaging continuation path
- `todo` define macOS app-bundle and signing/notarization path
- `todo` define Linux package strategy
- `todo` define Raspberry Pi install/update strategy
- `todo` document platform-specific prerequisites for users

Exit criteria:

- each platform has a release path
- platform prerequisites are documented

## Current Program Blockers

- no portability audit has been completed yet
- audio stack behavior across platforms is still unknown
- BLE behavior across desktop platforms is still unverified
- packaging strategy is not yet standardized outside Windows

## Immediate Next

- perform Phase 0 and Phase 1 before any major refactor
- use `task-board.md` as the working execution tracker

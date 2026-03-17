# PAKT Fit Analysis For Host App v4

## Host app current shape

`ham_hat_control_center_v4` is a Tkinter app with a main-thread UI and worker-thread engine callbacks marshaled through a queue. It already supports two hardware modes:

- `SA818`
- `DigiRig`

Those modes are not abstracted as interchangeable backends. `DigiRig` is mostly implemented as conditional branches inside SA818/APRS audio workflows.

## Where PAKT should fit

PAKT should be added as the third hardware mode and treated as a dedicated backend. The best fit is:

- profile/state level: hardware mode plus small PAKT-specific persisted fields
- UI level: a dedicated PAKT control section in the main tab
- engine level: a separate `app/engine/pakt/` package
- app coordination level: explicit routing in `HamHatApp` by selected hardware mode

## Reusable parts

- Event queue and worker-to-UI dispatch in `app/app.py`
- Profile and Tk-variable plumbing in `app/app_state.py` and `app/engine/profile.py`
- Existing hardware mode selection and conditional visibility in `app/ui/main_tab.py`
- Existing comms/message log plumbing for showing outbound/inbound state

## New code required

- BLE-native transport and service layer for PAKT
- Asyncio worker thread for BLE operations
- PAKT-specific parse helpers for capabilities, chunking, telemetry, and TX results
- UI controls for scan/connect/config/status/telemetry
- Mode-aware host app action routing

## Shared changes that are justified

- Extend allowed `hardware_mode` values
- Persist a small amount of PAKT device context
- Add PAKT queue events and action methods
- Add `bleak` dependency

These are minimal and directly required by PAKT integration.

## Shared changes that are not justified in this pass

- Refactoring SA818 and DigiRig into a full backend interface hierarchy
- Reworking APRS audio TX/RX flows for non-PAKT reasons
- Broad UI redesign outside the minimum needed to expose PAKT

## First-pass behavioral boundary

PAKT first pass should support:

- BLE scan and connect/reconnect
- capability read
- config read/write
- TX request send
- TX result tracking
- telemetry subscription
- auth/bonding guidance

PAKT first pass should not claim support for:

- KISS-over-BLE
- the existing APRS RX audio monitor workflow
- mature command endpoint support
- fully live RX packet/status production if hardware/firmware is not there yet

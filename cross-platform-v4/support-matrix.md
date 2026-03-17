# Cross-Platform v4 Support Matrix

## Target Platforms

### Windows

Target level: primary baseline

Expected support:

- full current v4 feature set
- existing packaging path maintained
- regression baseline for all other targets

### macOS

Target level: full desktop support

Expected support:

- app startup
- profile management
- UI and mode switching
- serial workflows where supported by device access
- BLE workflows where platform stack allows
- clear packaging and signing story

### Linux Desktop

Target level: full desktop support

Expected support:

- app startup
- profile management
- UI and mode switching
- serial workflows
- BLE workflows where stack and permissions allow
- package/install strategy

### Raspberry Pi OS

Target level: supported deployment target

Expected support:

- app startup
- profile management
- serial workflows
- platform-appropriate UI/runtime expectations
- packaging/install/update path

Special notes:

- treat Raspberry Pi as resource-sensitive
- account for audio, BLE, permissions, and display/headless realities separately from generic Linux desktop

## Capability Matrix To Fill During Execution

| Capability | Windows | macOS | Linux | Raspberry Pi | Notes |
|---|---|---|---|---|---|
| App startup | baseline | unknown | unknown | unknown | |
| Profile persistence | baseline | unknown | unknown | unknown | |
| SA818 serial | baseline | unknown | unknown | unknown | |
| DigiRig | baseline | unknown | unknown | unknown | |
| PAKT BLE | baseline | unknown | unknown | unknown | |
| Audio enumeration | baseline | unknown | unknown | unknown | |
| APRS audio flow | baseline | unknown | unknown | unknown | |
| Mesh test mode | baseline | unknown | unknown | unknown | |
| Packaging | baseline | unknown | unknown | unknown | |

## Support Policy Rules

- “supported” means boot + core workflow + documented packaging path + known limitations
- “experimental” means runnable but not fully validated
- “unsupported” must fail clearly and be documented

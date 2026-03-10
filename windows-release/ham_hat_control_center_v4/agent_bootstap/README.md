# Agent Bootstrap Folder

This folder is the single source of truth for AI/agent onboarding artifacts in `ham_hat_control_center_v4`.

## Active Files

- `AGENT_CONTEXT.json`  
  Curated machine-readable architecture and routing context.
- `PROJECT_COMPONENT_MAP.md`  
  Human-maintained architecture map and task routing guide.
- `AGENT_CODE_INDEX.json`  
  Generated machine index of files/classes/functions.
- `AGENT_ONBOARDING_PACK.md`  
  Generated human-readable onboarding pack.
- `APRS_MESH_TEST_IMPLEMENTATION_ROADMAP.md`
  Research-backed test implementation roadmap for introducing APRS AX.25 mesh support.

## Legacy Copies

- `legacy_root_copies/` stores previously generated root-level files preserved during consolidation.

## Regeneration

From `windows-release/ham_hat_control_center_v4` run:

```powershell
python scripts/generate_agent_onboarding_pack.py
```

This updates:
- `agent_bootstap/AGENT_CODE_INDEX.json`
- `agent_bootstap/AGENT_ONBOARDING_PACK.md`

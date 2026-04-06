# Agent Bootstrap Folder

Purpose: lightweight entrypoint for agent-facing app docs.
Note: the canonical folder name in this repo is the historical `agent_bootstap/` spelling; the generator now writes here as well.

## Read First

1. `README.md` at repo root
2. `cross-platform-v4/roadmap.md`
3. `cross-platform-v4/task-board.md`
4. `app/audit_v4.md`
5. this folder only if you need deeper app structure

## Key Files

- `AGENT_CONTEXT.json` — machine-readable architecture context
- `PROJECT_COMPONENT_MAP.md` — app structure map
- `AGENT_CODE_INDEX.json` — generated file/class/function index
- `AGENT_ONBOARDING_PACK.md` — generated long-form pack

## Regenerate

From `app/` run:

```bash
python scripts/generate_agent_onboarding_pack.py
```

This refreshes `AGENT_CODE_INDEX.json` and `AGENT_ONBOARDING_PACK.md` after major repo moves or architecture changes.

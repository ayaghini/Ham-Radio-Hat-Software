# APRS Mesh Audit

Date: 2026-03-09
Scope: Re-audit after mesh fixes under `windows-release/ham_hat_control_center_v4`
Audited areas:
- `app/engine/mesh_mgr.py`
- `app/ui/mesh_tab.py`
- integration in `app/app.py`, `app/app_state.py`, `app/engine/models.py`, `app/engine/profile.py`
- validation script `scripts/mesh_sim_tests.py`

## Verification Performed

Commands executed:

1. `python -m compileall -q windows-release/ham_hat_control_center_v4/app windows-release/ham_hat_control_center_v4/scripts/mesh_sim_tests.py`
- Result: PASS

2. `python windows-release/ham_hat_control_center_v4/scripts/mesh_sim_tests.py`
- Result: PASS (`54 passed, 0 failed`)

3. `python windows-release/ham_hat_control_center_v4/main.py --help`
- Result: PASS

## Fix Verification Summary

Previously reported high-severity items were rechecked.

1. **Role-based forwarding enforcement**
- Status: FIXED
- Evidence:
  - `_can_forward()` added: `app/engine/mesh_mgr.py:275`
  - applied in RREQ/RREP/DATA forward paths
  - deterministic tests added and passing: `mesh_sim_tests.py` Test 11

2. **Reassembly timeout cleanup execution**
- Status: FIXED
- Evidence:
  - `tick()` now calls `_expire_reassembly(now)`: `app/engine/mesh_mgr.py:286`
  - deterministic test added and passing: `mesh_sim_tests.py` Test 12

3. **Percent-encoding chunk boundary split risk**
- Status: FIXED
- Evidence:
  - `_chunk_body()` boundary logic updated: `app/engine/mesh_mgr.py:704`
  - deterministic boundary tests added and passing: `mesh_sim_tests.py` Test 13

4. **MeshTab direct mutation of private route table**
- Status: FIXED
- Evidence:
  - manager API added: `get_route()` / `toggle_pin()` (`mesh_mgr.py:166`, `:170`)
  - tab now uses manager API: `mesh_tab.py:357`

5. **Unused mesh parser/builder imports in app integration**
- Status: FIXED (partially)
- Evidence:
  - parser/builder imports removed
  - `MeshManager` import remains unused in `app/app.py:40` (residual low issue below)

## Findings (current, ordered by severity)

## Medium

1. **Operator-facing send log can still be misleading for `mesh_send` no-route case**
- Impact: ambiguous user feedback.
- Evidence:
  - `app/app.py:1147` logs: `"DATA to {dst}: not sent (mesh disabled or no route)"`.
  - Current `send_data()` may still emit packets with `route='*'` when mesh is enabled, so `"no route"` in this message is not a strict condition.
- Recommendation:
  - Change log text to condition-specific messaging based on explicit return reason from `MeshManager`.
  - Prefer returning `(packets, reason)` from manager methods.

## Low

2. **Unused import: `MeshManager` in app module**
- Impact: minor code hygiene issue.
- Evidence:
  - imported at `app/app.py:40`, not otherwise referenced.
- Recommendation:
  - remove unused symbol from import list.

3. **Mesh packet intercept returns before standard APRS processing when mesh prefix is present**
- Impact: mesh-prefixed packets are excluded from standard APRS pipeline/logging when mesh handling path is taken.
- Evidence:
  - early-return intercept in `app/app.py:1009-1014`.
- Recommendation:
  - keep as-is if intentional and document it explicitly,
  - or add an APRS log line noting mesh packet interception.

## Test Coverage Status

`mesh_sim_tests.py` now includes the key regression tests previously missing:

- ENDPOINT no-forward enforcement (Test 11)
- tick-driven reassembly expiry (Test 12)
- chunk boundary `%XX` integrity (Test 13)

Coverage level is good for deterministic engine behavior.

## Overall Assessment

- Mesh implementation quality improved materially since prior audit.
- All previously identified High findings are resolved and verified by automated tests.
- Remaining issues are low-risk/operational clarity items.

Recommended status: **Accept for ongoing test-phase use**, with minor follow-up cleanup.

## Suggested Next Cleanup (small PR)

1. Remove unused `MeshManager` import from `app/app.py`.
2. Improve `mesh_discover` / `mesh_send` user feedback to reason-specific messages.
3. Document mesh packet intercept behavior in operator docs (`Mesh (Test)` section).

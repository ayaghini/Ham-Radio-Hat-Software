# APRS Mesh Audit

Date: 2026-03-09
Scope: Audit of mesh test implementation under `windows-release/ham_hat_control_center_v4`
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
- Result: PASS (38 passed, 0 failed)

3. `python windows-release/ham_hat_control_center_v4/main.py --help`
- Result: PASS

Additional behavioral probes:

1. Endpoint forwarding check (`node_role=ENDPOINT`) on RREQ handling
- Result: node still forwards (unexpected)

2. Reassembly timeout check via `tick()`
- Result: stale reassembly entries are not cleared

3. Percent-encoding chunk split probe
- Result: `%xx` sequence can be split across chunk boundary

## Findings (ordered by severity)

## High

1. **Forwarding role is not enforced; ENDPOINT nodes still relay mesh traffic**
- Impact: breaks routing model and can increase RF flooding risk.
- Evidence: forwarding paths in RREQ/RREP/DATA only check `enabled` and rate/ttl, never `node_role`.
- References:
  - `app/engine/mesh_mgr.py:313` (`_on_rreq`)
  - `app/engine/mesh_mgr.py:447` (`_on_data`)
  - `app/engine/mesh_mgr.py:386`, `:440`, `:509` (forward counters incremented without role gate)
- Recommendation:
  - Add `_can_forward()` guard (`self._cfg.node_role == "REPEATER"`) and apply before forwarding in `_on_rreq`, `_on_rrep`, `_on_data`.
  - Add deterministic test case: ENDPOINT receives forwarded candidate and must drop.

2. **Reassembly timeout logic exists but is never executed in runtime path**
- Impact: stale partial DATA chunks can accumulate indefinitely (memory growth, stale state).
- Evidence:
  - Cleanup method exists: `app/engine/mesh_mgr.py:617` (`_expire_reassembly`)
  - `tick()` does not call `_expire_reassembly`: `app/engine/mesh_mgr.py:263`
- Recommendation:
  - Call `_expire_reassembly(now)` inside `tick()`.
  - Add test asserting stale partial chunks are removed by `tick()` after timeout.

3. **Chunking can split percent-encoded triplets, corrupting DATA reassembly/decoding**
- Impact: message corruption for chunked payloads containing encoded tokens near boundaries.
- Evidence:
  - Split logic only avoids boundary directly after `%`, not after `%x`: `app/engine/mesh_mgr.py:680` (`_chunk_body`).
  - Repro produced chunks like `...%3` and `B...` (invalid split).
- Recommendation:
  - Replace boundary logic with safe scanner that never ends inside `%[0-9A-Fa-f]{2}` sequence.
  - Add deterministic test vector for boundary at `%`, `%x`, and `%xx` positions.

## Medium

4. **UI mutates mesh manager internal private state directly**
- Impact: bypasses manager invariants and complicates future refactors.
- Evidence:
  - `app/ui/mesh_tab.py:357` (`self._app.mesh._routes.get(dst)`)
- Recommendation:
  - Expose API methods on `MeshManager` for pin/unpin and route lookup.
  - Keep `_routes` private.

5. **User log messages can report successful send/discovery when nothing was transmitted**
- Impact: operator confusion during mesh-disabled state or zero-packet generation conditions.
- Evidence:
  - `app/app.py:1132` logs `RREQ sent` unconditionally.
  - `app/app.py:1141` logs `DATA sent ...` unconditionally.
- Recommendation:
  - Log explicit outcomes: `sent N packet(s)` and if zero, reason (disabled/no route/no payload).

## Low

6. **Unused imports in app integration path**
- Impact: code noise and maintenance drift.
- Evidence:
  - `parse_mesh_payload`, `build_mesh_payload` imported but unused at `app/app.py:40`.
- Recommendation:
  - Remove unused imports or use intentionally.

7. **Mesh packet intercept returns early before any APRS logging when mesh is disabled**
- Impact: mesh-prefixed packets are ignored from APRS visibility path while feature is off.
- Evidence:
  - intercept + early return in `app/app.py:1009`.
- Recommendation:
  - Decide policy:
    - either keep drop behavior and explicitly document,
    - or log as ignored packet when disabled.

## Test Coverage Gaps

Current `scripts/mesh_sim_tests.py` is strong for baseline flows but misses key regressions:

- No ENDPOINT forwarding prohibition test.
- No tick-driven reassembly expiry test.
- No chunk-boundary `%xx` integrity test.
- No UI-contract tests for disabled state behavior and route pin actions.

## Overall Assessment

- Core structure is solid and test scaffold is useful.
- Current implementation is **not yet safe to treat as role-correct mesh behavior** due to forwarding-role and chunk/reassembly issues.
- Recommended status: **Proceed after fixing High findings and adding the missing tests**.

## Suggested Fix Order

1. Implement role-based forwarding guard + tests.
2. Wire reassembly expiry into `tick()` + tests.
3. Fix chunk boundary algorithm + tests.
4. Refactor MeshTab pinning to manager API.
5. Improve operator logging for zero-send outcomes.

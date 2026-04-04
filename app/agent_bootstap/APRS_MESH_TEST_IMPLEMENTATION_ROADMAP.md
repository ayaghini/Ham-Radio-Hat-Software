# APRS AX.25 Mesh (Test) - Full Agent Implementation Spec

Last updated: 2026-03-09
Target app: `app`
Status: Execution-ready specification for agent implementation

## 1) Objective

Implement a test-only mesh layer in the v4 app using APRS AX.25 text payload transport, with:

- Route discovery (RREQ/RREP)
- Routed delivery (DATA)
- Route error handling (RERR)
- Optional neighbor beaconing (HELLO)
- Dedicated `Mesh (Test)` UI tab

The feature must be fully disabled by default and must not alter existing APRS behavior unless explicitly enabled.

## 2) Scope and Non-Goals

In scope for v0:

- Application-layer mesh over APRS message payload text
- Multi-hop forwarding with bounded flood and dedupe
- Route table + expiry + basic scoring
- Mesh diagnostics and route visibility in dedicated tab

Out of scope for v0:

- Wire-level compatibility with MeshCore internals
- Cryptographic identity, encryption, or signatures
- Automatic internet gateway bridging
- Production APRS-IS routing behavior

## 3) Hard Safety Guardrails

These must be enforced in code:

- Mesh default: OFF (`mesh_test_enabled = False`)
- Max forwarding TTL hard cap: `8`
- Max payload body bytes per DATA frame (before chunking): `48`
- Max forwarded mesh frames per minute: `60` hard cap (UI can set lower only)
- Flood duplicate suppression window: `>= 120s`
- Drop reason must be logged for every non-forwarded mesh packet

## 4) Wire Protocol v0 (Exact)

All mesh packets are APRS text payloads beginning with `@M0/`.

General format:

- `@M0/<TYPE>/<KV-PAIRS>`
- KV pairs are `key=value` separated by `;`
- Reserved chars in values (`;`, `=`, `%`) must be percent-encoded (`%3B`, `%3D`, `%25`)
- Keys are lowercase ASCII

Example envelope:

- `@M0/RREQ/ver=1;orig=VA7ABC-9;tgt=VA7XYZ-1;rid=K3F91;ttl=4;path=VA7ABC-9`

Supported packet types:

- `RREQ`
- `RREP`
- `DATA`
- `RERR`
- `HELLO`

Required fields by type:

`RREQ`
- `ver` protocol version (must be `1`)
- `orig` origin node callsign
- `tgt` target node callsign
- `rid` route request ID (1..8 alnum)
- `ttl` integer 1..8
- `path` comma-delimited hop list (at least `orig`)

`RREP`
- `ver`
- `orig` original route requester
- `tgt` final target that generated reply
- `rid` request ID being answered
- `ttl`
- `path` reverse/forward path as comma list
- `metric` integer hop metric

`DATA`
- `ver`
- `src` source callsign
- `dst` destination callsign
- `mid` message ID (1..10 alnum)
- `ttl`
- `route` comma list of planned hops, or `*` for next-hop dynamic
- `body` percent-encoded payload text
- `part` optional chunk part number (1-based)
- `total` optional total chunk count

`RERR`
- `ver`
- `src` reporter callsign
- `dst` intended destination that failed
- `code` one of: `NOROUTE`, `NEXTHOP`, `TTL`, `RATE`
- `detail` short percent-encoded text

`HELLO`
- `ver`
- `src` sender callsign
- `role` `ENDPOINT` or `REPEATER`
- `ttl` fixed `1`

Normalization rules:

- Callsigns are uppercased and trimmed.
- Unknown keys are ignored.
- Unknown packet type -> parse failure.
- Missing required key -> parse failure.

Size constraints:

- Max mesh text payload length: `220` chars (drop if longer)
- If DATA `body` exceeds limit, chunk into multiple DATA packets with same `mid`, with `part` and `total`.

## 5) Runtime Data Contracts

Add to `app/engine/models.py`:

- `MeshConfig`
  - `enabled: bool = False`
  - `node_role: str = "ENDPOINT"`
  - `default_ttl: int = 4`
  - `rate_limit_ppm: int = 20`
  - `hello_enabled: bool = False`
  - `route_expiry_s: int = 600`

- `MeshRoute`
  - `destination: str`
  - `next_hop: str`
  - `hop_count: int`
  - `metric: int`
  - `learned_from: str` (`RREQ`, `RREP`, `DATA`, `MANUAL`)
  - `last_seen_ts: float`
  - `expiry_ts: float`
  - `pinned: bool = False`

- `MeshPacket`
  - `ptype: str`
  - `fields: dict[str, str]`
  - `raw: str`

- `MeshStats`
  - Counters: `rreq_tx`, `rreq_rx`, `rreq_fwd`, `rreq_drop`, `rrep_tx`, `rrep_rx`, `rrep_fwd`, `data_tx`, `data_rx`, `data_fwd`, `data_drop`, `rerr_tx`, `rerr_rx`, `hello_tx`, `hello_rx`, `dedupe_drop`, `ttl_drop`, `rate_drop`, `noroute_drop`

Extend `AppProfile`:

- `mesh_test_enabled: bool = False`
- `mesh_node_role: str = "ENDPOINT"`
- `mesh_default_ttl: int = 4`
- `mesh_rate_limit_ppm: int = 20`
- `mesh_hello_enabled: bool = False`
- `mesh_route_expiry_s: int = 600`

## 6) Mesh Manager Interface Contract

Create `app/engine/mesh_mgr.py` with these public methods.

Required signatures:

- `parse_mesh_payload(text: str) -> MeshPacket | None`
- `build_mesh_payload(pkt: MeshPacket) -> str`
- `discover_route(target: str, now: float) -> list[MeshPacket]`
- `send_data(dst: str, body: str, now: float) -> list[MeshPacket]`
- `handle_rx(packet_text: str, from_call: str, now: float) -> tuple[list[MeshPacket], list[str]]`
: returns `(outbound_packets, local_deliveries)`
- `get_routes(now: float) -> list[MeshRoute]`
- `get_stats() -> MeshStats`
- `set_config(cfg: MeshConfig) -> None`
- `invalidate_route(destination: str) -> None`
- `tick(now: float) -> list[MeshPacket]`
: for scheduled HELLO and cleanup

Internal state (required):

- route table: `dict[destination, MeshRoute]`
- pending RREQ map: `dict[(orig, rid), expiry_ts]`
- seen DATA map: `dict[(src, mid, part), expiry_ts]`
- outbound rate bucket timestamps list
- chunk reassembly buffer keyed by `(src, mid)`

## 7) State Machine Rules (Exact)

On `RREQ` receive:

1. Parse + validate.
2. If dedupe seen (`orig`, `rid`) -> drop (`dedupe_drop`).
3. If `ttl <= 0` -> drop (`ttl_drop`).
4. Learn reverse route to `orig` via `from_call`.
5. If local node == `tgt`:
- emit `RREP` to `orig` with discovered path.
6. Else if forwarding allowed (`enabled` and role permits):
- decrement ttl
- append self to `path` if not present
- rate-limit check then forward

On `RREP` receive:

1. Validate + dedupe by (`orig`, `rid`, `from_call`) optional short window.
2. Learn forward route to `tgt` via `from_call`.
3. If local node == `orig`: discovery completes.
4. Else forward toward `orig` using reverse route.

On `DATA` receive:

1. Validate + dedupe (`src`, `mid`, `part`).
2. If local node == `dst`:
- if chunked, reassemble with timeout 60s.
- emit local delivery string when complete.
3. Else forward when route exists and forwarding permitted.
4. If no route, emit `RERR(code=NOROUTE)` if allowed.

On `RERR` receive:

1. Invalidate route for `dst` if next hop matches reporter path.
2. Log reason.

On `HELLO` receive:

1. Record neighbor freshness.
2. Optional opportunistic route hint for `src` via `from_call` (1-hop).

## 8) Route Selection Policy

Primary sort key:

1. lower `hop_count`
2. lower `metric`
3. newer `last_seen_ts`

Pinned route always wins unless expired hard by timeout and `pinned=False` fallback exists.

Route expiry:

- Non-pinned route expires at `now > expiry_ts`.
- Refresh expiry on successful RREP/DATA observed.

## 9) App Wiring Contract

`app/app_state.py`:

- Add `self.mesh = MeshManager(local_call_provider=...)`
- Add Tk vars for mesh profile fields.

`app/app.py`:

- Instantiate `MeshTab` and add notebook tab label `Mesh (Test)`.
- In packet handling path:
  - detect payload prefix `@M0/`
  - call mesh manager `handle_rx(...)`
  - for outbound packets returned, send through existing APRS TX path
- Add mesh event dataclasses if needed (route update, mesh log, stats).

Important:

- Mesh handling must be wrapped so parse errors never crash APRS RX loop.

## 10) Mesh Tab UI Contract (Exact)

Create `app/ui/mesh_tab.py` with these sections:

`Mesh Control`
- checkbox: enable mesh test mode
- combobox: node role (`ENDPOINT`, `REPEATER`)
- spinbox: default TTL (1..8)
- spinbox: rate limit ppm (1..60)
- checkbox: HELLO beacons

`Discovery`
- entry: destination callsign
- button: discover route
- status label: last discovery result

`Routes`
- table columns: destination, next_hop, hops, metric, age_s, expires_in_s, learned_from, pinned
- actions: invalidate route, pin/unpin

`Mesh Send`
- destination entry
- text box (max 240 chars before chunking)
- send button

`Diagnostics`
- counters grid for MeshStats
- bounded log panel (drop reasons, forwards, route updates)

Behavior:

- All controls disabled when mesh disabled except the enable checkbox.
- Validation errors shown inline and in log.

## 11) Test Plan (Deterministic)

Add tests under `tests/mesh/` if test harness exists, otherwise `scripts/mesh_sim_tests.py`.

Minimum deterministic cases:

1. Parse/build round-trip for all packet types.
2. RREQ dedupe drop on repeated same (`orig`,`rid`).
3. RREQ ttl drop when `ttl=0`.
4. 3-node discovery: A->C through B produces route on A.
5. 3-node DATA: A->C through B delivers exactly once.
6. DATA duplicate suppression prevents duplicate local delivery.
7. Chunked DATA reassembly success and timeout failure path.
8. Rate limit drop when ppm exceeded.
9. Route expiry removes stale route.
10. Mesh disabled path does nothing.

Manual smoke after integration:

- App starts and existing APRS features still work with mesh off.
- Mesh tab can discover/send in controlled test setup.

## 12) Step-by-Step Execution Plan

## Step 0 - Preflight

- create feature branch `feature/mesh-test-v0`
- run baseline compile and CLI checks

## Step 1 - Models + profile persistence

Files:
- `app/engine/models.py`
- `app/engine/profile.py`
- `app/app_state.py` (vars only)

Done when:
- profile fields persist and load with defaults

## Step 2 - Mesh manager core + parser

Files:
- `app/engine/mesh_mgr.py` (new)
- test file/script for parser and dedupe

Done when:
- all deterministic parser/dedupe tests pass

## Step 3 - Discovery (RREQ/RREP)

Files:
- `app/engine/mesh_mgr.py`
- tests/sim for 2-node and 3-node route discovery

Done when:
- route discovery converges, no replay storms

## Step 4 - DATA + RERR

Files:
- `app/engine/mesh_mgr.py`
- tests/sim for forwarding and errors

Done when:
- multi-hop data delivery and error invalidation verified

## Step 5 - App integration

Files:
- `app/app.py`
- `app/app_state.py`

Done when:
- mesh packets can flow RX->manager->TX intent path
- mesh disabled means no behavior change

## Step 6 - Mesh tab

Files:
- `app/ui/mesh_tab.py` (new)
- `app/app.py`

Done when:
- operators can enable mesh, discover, send, view routes/stats

## Step 7 - Validation and docs

Files:
- `agent_bootstap/AGENT_CONTEXT.json`
- `agent_bootstap/PROJECT_COMPONENT_MAP.md`
- regen onboarding pack
- UI docs add Mesh tab note

Done when:
- docs and runbook match actual code paths

## 13) Ticket Breakdown (Assignable)

- `MESH-001` models/profile
- `MESH-002` parser/builders
- `MESH-003` dedupe/route table
- `MESH-004` discovery
- `MESH-005` data+rerr
- `MESH-006` app integration
- `MESH-007` mesh tab UI
- `MESH-008` deterministic tests + smoke report
- `MESH-009` docs and onboarding refresh

Each ticket must include:

- changed files
- tests executed and output summary
- user-visible change
- rollback approach

## 14) Acceptance Gate

All must be true:

- mesh off by default
- no APRS regression with mesh off
- 2-node and 3-node route/data tests pass
- dedupe/ttl/rate limit enforcement proven by tests
- profile persistence works for mesh settings
- mesh tab functional and stable
- compile checks pass

## 15) References

MeshCore:
- https://github.com/meshcore-dev/MeshCore
- https://github.com/meshcore-dev/MeshCore/issues/1031

APRS/AX.25:
- https://tapr.org/pdf/AX25.2.2.pdf
- https://www.aprs.org/aprs11.html
- https://github.com/wb2osz/aprsspec

## 16) Scope Reminder

This spec adapts MeshCore-style routing ideas to APRS AX.25 for a controlled test implementation. It is not a claim of MeshCore protocol compatibility.

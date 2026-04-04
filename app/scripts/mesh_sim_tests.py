#!/usr/bin/env python3
"""Deterministic mesh simulation tests (MESH-008).

Runs without hardware or Tkinter. Execute from the repo root:
    python scripts/mesh_sim_tests.py

Each test prints PASS / FAIL. Exit code 0 = all pass.
"""

from __future__ import annotations

import sys
import time
import os

# Allow import from parent package without full install
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.engine.mesh_mgr import (
    MeshManager,
    parse_mesh_payload,
    build_mesh_payload,
    MESH_PREFIX,
)
from app.engine.models import MeshConfig, MeshPacket


# ---------------------------------------------------------------------------
# Test harness
# ---------------------------------------------------------------------------

class _Counts:
    """Accumulates pass/fail counts for one test run without module-level mutation."""
    __slots__ = ("passed", "failed")
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

_counts = _Counts()


def _result(name: str, ok: bool, detail: str = "") -> None:
    status = "PASS" if ok else "FAIL"
    suffix = f" — {detail}" if detail else ""
    print(f"  [{status}] {name}{suffix}")
    if ok:
        _counts.passed += 1
    else:
        _counts.failed += 1


def _make_mgr(call: str, enabled: bool = True, role: str = "ENDPOINT",
               ttl: int = 4, rate_ppm: int = 20) -> MeshManager:
    m = MeshManager(local_call_provider=lambda: call)
    m.set_config(MeshConfig(
        enabled=enabled,
        node_role=role,
        default_ttl=ttl,
        rate_limit_ppm=rate_ppm,
        hello_enabled=False,
        route_expiry_s=600,
    ))
    return m


NOW = 1_000_000.0   # stable fake clock baseline (unrelated to wall time)


# ---------------------------------------------------------------------------
# Test 1: Parse/build round-trip for all packet types
# ---------------------------------------------------------------------------

def test_parse_build_roundtrip() -> None:
    print("\n[Test 1] Parse/build round-trip")

    cases = [
        ("RREQ", "ver=1;orig=VA7ABC-9;tgt=VA7XYZ-1;rid=K3F91A;ttl=4;path=VA7ABC-9"),
        ("RREP", "ver=1;orig=VA7ABC-9;tgt=VA7XYZ-1;rid=K3F91A;ttl=3;path=VA7ABC-9,VA7XYZ-1;metric=2"),
        ("DATA", "ver=1;src=VA7ABC-9;dst=VA7XYZ-1;mid=ABCD1234;ttl=4;route=*;body=hello"),
        ("RERR", "ver=1;src=VA7ABC-9;dst=VA7XYZ-1;code=NOROUTE;detail=no%20route"),
        ("HELLO", "ver=1;src=VA7ABC-9;role=ENDPOINT;ttl=1"),
    ]
    for ptype, kv in cases:
        raw = f"{MESH_PREFIX}{ptype}/{kv}"
        pkt = parse_mesh_payload(raw)
        ok = pkt is not None and pkt.ptype == ptype
        _result(f"parse {ptype}", ok)
        if pkt:
            rebuilt = build_mesh_payload(pkt)
            reparsed = parse_mesh_payload(rebuilt)
            _result(f"round-trip {ptype}", reparsed is not None and reparsed.ptype == ptype)


# ---------------------------------------------------------------------------
# Test 2: RREQ dedupe drop
# ---------------------------------------------------------------------------

def test_rreq_dedupe() -> None:
    print("\n[Test 2] RREQ dedupe drop")
    m = _make_mgr("VA7B-1", role="REPEATER")
    raw = f"{MESH_PREFIX}RREQ/ver=1;orig=VA7A-9;tgt=VA7C-1;rid=AAA111;ttl=3;path=VA7A-9"
    out1, _ = m.handle_rx(raw, "VA7A-9", NOW)
    out2, _ = m.handle_rx(raw, "VA7A-9", NOW + 1)
    _result("first RREQ forwarded", len(out1) == 1, f"packets={len(out1)}")
    _result("duplicate RREQ dropped", len(out2) == 0, f"packets={len(out2)}")
    _result("dedupe_drop counter", m.get_stats().dedupe_drop >= 1)


# ---------------------------------------------------------------------------
# Test 3: RREQ TTL drop when ttl=0
# ---------------------------------------------------------------------------

def test_rreq_ttl_drop() -> None:
    print("\n[Test 3] RREQ TTL drop (ttl=0)")
    m = _make_mgr("VA7B-1")
    raw = f"{MESH_PREFIX}RREQ/ver=1;orig=VA7A-9;tgt=VA7C-1;rid=BBB222;ttl=0;path=VA7A-9"
    out, _ = m.handle_rx(raw, "VA7A-9", NOW)
    _result("ttl=0 RREQ dropped", len(out) == 0, f"packets={len(out)}")
    _result("ttl_drop counter", m.get_stats().ttl_drop >= 1)


# ---------------------------------------------------------------------------
# Test 4: 3-node discovery — A->C through B produces route on A
# ---------------------------------------------------------------------------

def test_3node_discovery() -> None:
    print("\n[Test 4] 3-node discovery A->C through B")
    a = _make_mgr("VA7A-9")
    b = _make_mgr("VA7B-1", role="REPEATER")
    c = _make_mgr("VA7C-2")

    # A initiates discovery
    pkts_from_a = a.discover_route("VA7C-2", NOW)
    _result("A emits RREQ", len(pkts_from_a) == 1)

    # B receives RREQ and forwards it
    rreq_raw = pkts_from_a[0].raw
    out_b, _ = b.handle_rx(rreq_raw, "VA7A-9", NOW + 0.1)
    _result("B forwards RREQ", len(out_b) == 1, f"packets={len(out_b)}")

    # C receives forwarded RREQ and sends RREP
    fwd_raw = out_b[0].raw
    out_c, deliveries_c = c.handle_rx(fwd_raw, "VA7B-1", NOW + 0.2)
    _result("C emits RREP", len(out_c) == 1 and out_c[0].ptype == "RREP",
            f"packets={len(out_c)}")

    # B receives RREP and forwards toward A
    rrep_raw = out_c[0].raw
    out_b2, _ = b.handle_rx(rrep_raw, "VA7C-2", NOW + 0.3)
    _result("B forwards RREP toward A", len(out_b2) == 1)

    # A receives RREP — discovery complete
    rrep2_raw = out_b2[0].raw
    out_a2, _ = a.handle_rx(rrep2_raw, "VA7B-1", NOW + 0.4)
    routes_a = a.get_routes(NOW + 0.5)
    has_route = any(r.destination == "VA7C-2" for r in routes_a)
    _result("A has route to C after RREP", has_route)


# ---------------------------------------------------------------------------
# Test 5: 3-node DATA: A->C through B delivers exactly once
# ---------------------------------------------------------------------------

def test_3node_data_delivery() -> None:
    print("\n[Test 5] 3-node DATA A->C through B")
    a = _make_mgr("VA7A-9")
    b = _make_mgr("VA7B-1", role="REPEATER")
    c = _make_mgr("VA7C-2")

    # Pre-load routes so we can skip discovery in this test
    now = NOW + 100
    a._routes["VA7C-2"] = _make_route("VA7C-2", "VA7B-1", 2, now)
    b._routes["VA7C-2"] = _make_route("VA7C-2", "VA7C-2", 1, now)

    pkts = a.send_data("VA7C-2", "hello mesh", now)
    _result("A sends DATA", len(pkts) >= 1)

    data_raw = pkts[0].raw
    out_b, deliveries_b = b.handle_rx(data_raw, "VA7A-9", now + 0.1)
    _result("B forwards DATA", len(out_b) == 1)
    _result("B no local delivery", len(deliveries_b) == 0)

    fwd_raw = out_b[0].raw
    out_c, deliveries_c = c.handle_rx(fwd_raw, "VA7B-1", now + 0.2)
    _result("C delivers DATA locally", len(deliveries_c) == 1)
    _result("C delivery contains body", "hello mesh" in deliveries_c[0] if deliveries_c else False)


# ---------------------------------------------------------------------------
# Test 6: DATA duplicate suppression
# ---------------------------------------------------------------------------

def test_data_dedupe() -> None:
    print("\n[Test 6] DATA duplicate suppression")
    c = _make_mgr("VA7C-2")
    now = NOW + 200
    raw = f"{MESH_PREFIX}DATA/ver=1;src=VA7A-9;dst=VA7C-2;mid=TEST9999;ttl=2;route=*;body=hello"
    _, d1 = c.handle_rx(raw, "VA7B-1", now)
    _, d2 = c.handle_rx(raw, "VA7B-1", now + 1)
    _result("first delivery", len(d1) == 1)
    _result("duplicate suppressed", len(d2) == 0)
    _result("dedupe_drop counter", c.get_stats().dedupe_drop >= 1)


# ---------------------------------------------------------------------------
# Test 7: Chunked DATA reassembly success and timeout failure
# ---------------------------------------------------------------------------

def test_chunked_reassembly() -> None:
    print("\n[Test 7] Chunked DATA reassembly")
    c = _make_mgr("VA7C-2")
    now = NOW + 300
    mid = "CHUNK01"

    raw1 = (f"{MESH_PREFIX}DATA/ver=1;src=VA7A-9;dst=VA7C-2;mid={mid};"
            f"ttl=2;route=*;body=helloXX;part=1;total=2")
    raw2 = (f"{MESH_PREFIX}DATA/ver=1;src=VA7A-9;dst=VA7C-2;mid={mid};"
            f"ttl=2;route=*;body=world;part=2;total=2")

    _, d1 = c.handle_rx(raw1, "VA7B-1", now)
    _result("part 1 no delivery yet", len(d1) == 0)
    _, d2 = c.handle_rx(raw2, "VA7B-1", now + 0.1)
    _result("reassembled delivery after part 2", len(d2) == 1)
    _result("body correct", "helloXXworld" in d2[0] if d2 else False,
            repr(d2[0]) if d2 else "no delivery")

    # Timeout path: send only part 1 with a different mid, then expire it via tick().
    # After expiry the partial entry is cleared; sending part 2 alone should NOT deliver
    # (public contract: incomplete reassembly was discarded, not completed).
    mid2 = "CHUNK02"
    raw3_p1 = (f"{MESH_PREFIX}DATA/ver=1;src=VA7A-9;dst=VA7C-2;mid={mid2};"
               f"ttl=2;route=*;body=part1only;part=1;total=2")
    raw3_p2 = (f"{MESH_PREFIX}DATA/ver=1;src=VA7A-9;dst=VA7C-2;mid={mid2};"
               f"ttl=2;route=*;body=part2only;part=2;total=2")
    c.handle_rx(raw3_p1, "VA7B-1", now + 1)
    c.tick(now + 200)   # advance well past 60s reassembly timeout
    _, d_late = c.handle_rx(raw3_p2, "VA7B-1", now + 201)
    _result("partial reassembly expired on timeout",
            len(d_late) == 0, f"got {len(d_late)} deliveries (expected 0 — part1 was expired)")


# ---------------------------------------------------------------------------
# Test 8: Rate limit drop when ppm exceeded
# ---------------------------------------------------------------------------

def test_rate_limit() -> None:
    print("\n[Test 8] Rate limit drop")
    m = _make_mgr("VA7B-1", rate_ppm=2, role="REPEATER")
    now = NOW + 400
    drops = 0
    total = 5
    for i in range(total):
        raw = (f"{MESH_PREFIX}RREQ/ver=1;orig=VA7A-9;tgt=VA7C-2;"
               f"rid=RL{i:04d};ttl=3;path=VA7A-9")
        out, _ = m.handle_rx(raw, "VA7A-9", now + i * 0.001)
        if len(out) == 0:
            drops += 1
    _result("rate limit drops occurred", drops > 0, f"drops={drops}/{total}")
    _result("rate_drop counter", m.get_stats().rate_drop >= drops)


# ---------------------------------------------------------------------------
# Test 9: Route expiry removes stale route
# ---------------------------------------------------------------------------

def test_route_expiry() -> None:
    print("\n[Test 9] Route expiry")
    m = _make_mgr("VA7A-9")
    now = NOW + 500
    # Inject a short-lived route
    m._routes["VA7C-2"] = _make_route("VA7C-2", "VA7B-1", 2, now, expiry_s=5)
    routes_before = m.get_routes(now + 1)
    _result("route present before expiry", any(r.destination == "VA7C-2" for r in routes_before))
    routes_after = m.get_routes(now + 10)
    _result("route absent after expiry", not any(r.destination == "VA7C-2" for r in routes_after))


# ---------------------------------------------------------------------------
# Test 10: Mesh disabled path does nothing
# ---------------------------------------------------------------------------

def test_mesh_disabled() -> None:
    print("\n[Test 10] Mesh disabled — no-op")
    m = _make_mgr("VA7B-1", enabled=False)
    raw = f"{MESH_PREFIX}RREQ/ver=1;orig=VA7A-9;tgt=VA7C-2;rid=DIS001;ttl=3;path=VA7A-9"
    out, deliveries = m.handle_rx(raw, "VA7A-9", NOW + 600)
    _result("no output when disabled", len(out) == 0 and len(deliveries) == 0)
    pkts = m.discover_route("VA7C-2", NOW + 600)
    _result("discover_route no-op when disabled", len(pkts) == 0)


# ---------------------------------------------------------------------------
# Test 11: ENDPOINT does NOT forward (role guard)
# ---------------------------------------------------------------------------

def test_endpoint_no_forward() -> None:
    print("\n[Test 11] ENDPOINT does not forward RREQ/RREP/DATA")
    ep = _make_mgr("VA7B-1", role="ENDPOINT")   # ENDPOINT
    rep = _make_mgr("VA7B-1", role="REPEATER")  # REPEATER

    rreq_raw = f"{MESH_PREFIX}RREQ/ver=1;orig=VA7A-9;tgt=VA7C-2;rid=EP001;ttl=3;path=VA7A-9"
    out_ep, _ = ep.handle_rx(rreq_raw, "VA7A-9", NOW + 700)
    out_rep, _ = rep.handle_rx(rreq_raw, "VA7A-9", NOW + 700)
    _result("ENDPOINT drops RREQ (not target)", len(out_ep) == 0, f"packets={len(out_ep)}")
    _result("REPEATER forwards RREQ", len(out_rep) == 1, f"packets={len(out_rep)}")

    rrep_raw = (f"{MESH_PREFIX}RREP/ver=1;orig=VA7A-9;tgt=VA7C-2;rid=EP001;"
                f"ttl=2;path=VA7A-9,VA7C-2;metric=2")
    ep2 = _make_mgr("VA7B-1", role="ENDPOINT")
    rep2 = _make_mgr("VA7B-1", role="REPEATER")
    # Pre-load route to orig so REPEATER can forward RREP
    rep2._routes["VA7A-9"] = _make_route("VA7A-9", "VA7A-9", 1, NOW + 700)
    out_ep2, _ = ep2.handle_rx(rrep_raw, "VA7C-2", NOW + 700)
    out_rep2, _ = rep2.handle_rx(rrep_raw, "VA7C-2", NOW + 700)
    _result("ENDPOINT drops RREP forward", len(out_ep2) == 0, f"packets={len(out_ep2)}")
    _result("REPEATER forwards RREP", len(out_rep2) == 1, f"packets={len(out_rep2)}")

    data_raw = (f"{MESH_PREFIX}DATA/ver=1;src=VA7A-9;dst=VA7C-2;"
                f"mid=EP002;ttl=3;route=*;body=hello")
    ep3 = _make_mgr("VA7B-1", role="ENDPOINT")
    rep3 = _make_mgr("VA7B-1", role="REPEATER")
    rep3._routes["VA7C-2"] = _make_route("VA7C-2", "VA7C-2", 1, NOW + 700)
    out_ep3, _ = ep3.handle_rx(data_raw, "VA7A-9", NOW + 700)
    out_rep3, _ = rep3.handle_rx(data_raw, "VA7A-9", NOW + 700)
    _result("ENDPOINT drops DATA forward", len(out_ep3) == 0, f"packets={len(out_ep3)}")
    _result("REPEATER forwards DATA", len(out_rep3) == 1, f"packets={len(out_rep3)}")


# ---------------------------------------------------------------------------
# Test 12: tick() drives reassembly expiry
# ---------------------------------------------------------------------------

def test_tick_expires_reassembly() -> None:
    print("\n[Test 12] tick() clears stale reassembly entries")
    c = _make_mgr("VA7C-2")
    now = NOW + 800
    mid = "TICK01"
    raw1 = (f"{MESH_PREFIX}DATA/ver=1;src=VA7A-9;dst=VA7C-2;mid={mid};"
            f"ttl=2;route=*;body=part1;part=1;total=2")
    raw2 = (f"{MESH_PREFIX}DATA/ver=1;src=VA7A-9;dst=VA7C-2;mid={mid};"
            f"ttl=2;route=*;body=part2;part=2;total=2")

    # Positive case: tick well before expiry, then part 2 completes the reassembly.
    c.handle_rx(raw1, "VA7B-1", now)
    c.tick(now + 30)                            # 30s < 60s timeout — entry still live
    _, d_before = c.handle_rx(raw2, "VA7B-1", now + 30)
    _result("part 2 delivers when part 1 still buffered", len(d_before) == 1,
            f"got {len(d_before)} deliveries (expected 1)")

    # Expiry case: a fresh mid, only part 1 sent, then tick past timeout.
    # Sending part 2 after expiry should NOT deliver (part 1 is gone).
    mid2 = "TICK02"
    raw_a = (f"{MESH_PREFIX}DATA/ver=1;src=VA7A-9;dst=VA7C-2;mid={mid2};"
             f"ttl=2;route=*;body=part1;part=1;total=2")
    raw_b = (f"{MESH_PREFIX}DATA/ver=1;src=VA7A-9;dst=VA7C-2;mid={mid2};"
             f"ttl=2;route=*;body=part2;part=2;total=2")
    c.handle_rx(raw_a, "VA7B-1", now + 31)
    c.tick(now + 200)                           # advance well past 60s timeout
    _, d_after = c.handle_rx(raw_b, "VA7B-1", now + 201)
    _result("part 2 does not deliver after part 1 expired by tick()",
            len(d_after) == 0, f"got {len(d_after)} deliveries (expected 0 — part1 expired)")


# ---------------------------------------------------------------------------
# Test 13: Chunk boundary never splits a %XX triplet
# ---------------------------------------------------------------------------

def test_chunk_boundary_pct_encode() -> None:
    print("\n[Test 13] Chunk boundary does not split %XX sequences")
    from app.engine.mesh_mgr import _chunk_body, _pct_encode, _pct_decode

    # Build a string where a reserved char lands at/around the boundary
    # max_bytes=4: body "a;bc" encodes to "a%3Bbc" (6 chars)
    # Naively splitting at 4 would yield "a%3B" and "bc" — but %3B is valid there.
    # Tricky case: split at 3 yields "a%3" / "Bbc" — invalid.
    encoded = "a%3Bbc"
    chunks = _chunk_body(encoded, 3)
    reassembled = "".join(chunks)
    _result("chunks rejoin to original", reassembled == encoded, repr(chunks))
    for i, c in enumerate(chunks):
        bad = (c.endswith("%") or (len(c) >= 2 and c[-2] == "%" and c[-1].upper() in "0123456789ABCDEF"))
        _result(f"chunk {i} not split inside %XX", not bad, repr(c))

    # Boundary at %: "ab%3Bc" split at 3 → cut on "ab%" → should step back to "ab"
    encoded2 = "ab%3Bc"
    chunks2 = _chunk_body(encoded2, 3)
    for i, c in enumerate(chunks2):
        bad = c.endswith("%") or (len(c) >= 2 and c[-2] == "%")
        _result(f"case2 chunk {i} safe boundary", not bad, repr(c))

    # Round-trip: encode a message with reserved chars, chunk, rejoin, decode
    original = "hello;world=test%done"
    enc = _pct_encode(original)
    chunks3 = _chunk_body(enc, 5)
    rejoined = _pct_decode("".join(chunks3))
    _result("pct round-trip through chunks", rejoined == original,
            f"got={repr(rejoined)} want={repr(original)}")


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_route(dst: str, via: str, hops: int, now: float, expiry_s: int = 600):
    from app.engine.models import MeshRoute
    return MeshRoute(
        destination=dst,
        next_hop=via,
        hop_count=hops,
        metric=hops,
        learned_from="MANUAL",
        last_seen_ts=now,
        expiry_ts=now + expiry_s,
        pinned=False,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Reset counters and start timer here, not at import time.
    _counts.passed = 0
    _counts.failed = 0
    t0 = time.monotonic()

    print("=" * 60)
    print("Mesh Simulation Tests (MESH-008)")
    print("=" * 60)

    test_parse_build_roundtrip()
    test_rreq_dedupe()
    test_rreq_ttl_drop()
    test_3node_discovery()
    test_3node_data_delivery()
    test_data_dedupe()
    test_chunked_reassembly()
    test_rate_limit()
    test_route_expiry()
    test_mesh_disabled()
    test_endpoint_no_forward()
    test_tick_expires_reassembly()
    test_chunk_boundary_pct_encode()

    print()
    print("=" * 60)
    elapsed = time.monotonic() - t0
    print(f"Results: {_counts.passed} passed, {_counts.failed} failed  ({elapsed:.2f}s)")
    print("=" * 60)
    sys.exit(0 if _counts.failed == 0 else 1)

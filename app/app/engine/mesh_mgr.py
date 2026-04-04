#!/usr/bin/env python3
"""MeshManager — APRS AX.25 Mesh (Test) layer v0.

All mesh packets are APRS text payloads beginning with ``@M0/``.

Wire format:
    @M0/<TYPE>/<key=value;key=value;...>

Reserved chars in values (``;``, ``=``, ``%``) are percent-encoded.

This module is fully self-contained; it only imports from .models.
The caller (HamHatApp) is responsible for wiring RX detection and TX dispatch.

Safety guardrails (enforced here):
- mesh_test_enabled defaults to False; all public methods return empty when disabled.
- Max TTL hard cap: 8
- Max payload body bytes per DATA frame before chunking: 48
- Max forwarded frames per minute: 60 (hard cap); config can lower only
- Flood duplicate suppression window: >= 120s
- Every dropped packet is logged via _log.
"""

from __future__ import annotations

import logging
import random
import string
import time
from typing import Callable, Optional

from .models import MeshConfig, MeshPacket, MeshRoute, MeshStats

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Protocol constants
# ---------------------------------------------------------------------------

MESH_PREFIX = "@M0/"
MAX_TTL = 8
MAX_BODY_BYTES = 48         # DATA body bytes before chunking
MAX_FWD_PPM_CAP = 60        # hard cap regardless of config
DEDUPE_WINDOW_S = 120.0     # minimum duplicate suppression window
MAX_PAYLOAD_LEN = 220       # drop if raw mesh text longer than this
CHUNK_REASSEMBLY_TIMEOUT_S = 60.0
HELLO_INTERVAL_S = 60.0     # emit HELLO every N seconds when enabled

_REQUIRED_FIELDS: dict[str, list[str]] = {
    "RREQ":  ["ver", "orig", "tgt", "rid", "ttl", "path"],
    "RREP":  ["ver", "orig", "tgt", "rid", "ttl", "path", "metric"],
    "DATA":  ["ver", "src", "dst", "mid", "ttl", "route", "body"],
    "RERR":  ["ver", "src", "dst", "code", "detail"],
    "HELLO": ["ver", "src", "role", "ttl"],
}


# ---------------------------------------------------------------------------
# Percent-encode / decode (only ; = %)
# ---------------------------------------------------------------------------

def _pct_encode(s: str) -> str:
    return s.replace("%", "%25").replace(";", "%3B").replace("=", "%3D")


def _pct_decode(s: str) -> str:
    return s.replace("%3B", ";").replace("%3D", "=").replace("%25", "%")


# ---------------------------------------------------------------------------
# Parse / build
# ---------------------------------------------------------------------------

def parse_mesh_payload(text: str) -> Optional[MeshPacket]:
    """Parse an APRS text payload into a MeshPacket, or return None on failure."""
    if not text.startswith(MESH_PREFIX):
        return None
    if len(text) > MAX_PAYLOAD_LEN:
        _log.debug("Mesh drop: payload too long (%d chars)", len(text))
        return None
    body = text[len(MESH_PREFIX):]
    parts = body.split("/", 1)
    if len(parts) != 2:
        _log.debug("Mesh parse fail: missing type separator in %r", text[:60])
        return None
    ptype = parts[0].upper()
    if ptype not in _REQUIRED_FIELDS:
        _log.debug("Mesh parse fail: unknown type %r", ptype)
        return None
    kv_str = parts[1]
    fields: dict[str, str] = {}
    for pair in kv_str.split(";"):
        pair = pair.strip()
        if not pair:
            continue
        if "=" not in pair:
            continue
        k, _, v = pair.partition("=")
        fields[k.strip().lower()] = _pct_decode(v.strip())
    # Validate required fields
    for req in _REQUIRED_FIELDS[ptype]:
        if req not in fields:
            _log.debug("Mesh parse fail: missing required field %r in %s", req, ptype)
            return None
    # Normalize callsigns
    for cs_key in ("orig", "tgt", "src", "dst"):
        if cs_key in fields:
            fields[cs_key] = fields[cs_key].upper().strip()
    return MeshPacket(ptype=ptype, fields=fields, raw=text)


def build_mesh_payload(pkt: MeshPacket) -> str:
    """Serialise a MeshPacket to its APRS text payload string."""
    kv = ";".join(f"{k}={_pct_encode(v)}" for k, v in pkt.fields.items())
    return f"{MESH_PREFIX}{pkt.ptype}/{kv}"


# ---------------------------------------------------------------------------
# Random ID generators
# ---------------------------------------------------------------------------

def _rand_id(length: int = 6) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


# ---------------------------------------------------------------------------
# MeshManager
# ---------------------------------------------------------------------------

class MeshManager:
    """Application-layer mesh manager over APRS text payloads.

    All state lives here; no Tkinter access.  The caller supplies the local
    callsign via ``local_call_provider`` (a zero-arg callable that returns str).
    """

    def __init__(self, local_call_provider: Callable[[], str]) -> None:
        self._local_call = local_call_provider
        self._cfg = MeshConfig()
        self._stats = MeshStats()

        # Route table  {destination -> MeshRoute}
        self._routes: dict[str, MeshRoute] = {}

        # Pending RREQ map  {(orig, rid) -> expiry_ts}
        self._seen_rreq: dict[tuple[str, str], float] = {}

        # Seen DATA map  {(src, mid, part) -> expiry_ts}
        self._seen_data: dict[tuple[str, str, str], float] = {}

        # Outbound rate bucket: list of timestamps of recent forwards
        self._rate_bucket: list[float] = []

        # Chunk reassembly  {(src, mid) -> {part_no: body, _total: int, _ts: float}}
        self._reassembly: dict[tuple[str, str], dict] = {}

        # Last HELLO emit timestamp
        self._last_hello_ts: float = 0.0

    # -----------------------------------------------------------------------
    # Configuration
    # -----------------------------------------------------------------------

    def set_config(self, cfg: MeshConfig) -> None:
        self._cfg = cfg

    def get_route(self, destination: str) -> Optional[MeshRoute]:
        """Return the live route for *destination*, or None if not found."""
        return self._routes.get(destination.upper().strip())

    def toggle_pin(self, destination: str) -> Optional[bool]:
        """Toggle pinned state for *destination*. Returns new pinned value, or None if no route."""
        route = self._routes.get(destination.upper().strip())
        if route:
            route.pinned = not route.pinned
            return route.pinned
        return None

    # -----------------------------------------------------------------------
    # Public interface
    # -----------------------------------------------------------------------

    def get_routes(self, now: float) -> list[MeshRoute]:
        self._expire_routes(now)
        routes = list(self._routes.values())
        routes.sort(key=lambda r: (r.hop_count, r.metric, -r.last_seen_ts))
        return routes

    def get_stats(self) -> MeshStats:
        return self._stats

    def invalidate_route(self, destination: str) -> None:
        dst = destination.upper().strip()
        if dst in self._routes:
            del self._routes[dst]
            _log.debug("Mesh: route to %s manually invalidated", dst)

    def discover_route(self, target: str, now: float) -> list[MeshPacket]:
        """Initiate route discovery to *target*; return list of outbound packets."""
        if not self._cfg.enabled:
            return []
        target = target.upper().strip()
        local = self._local_call().upper().strip()
        rid = _rand_id(6)
        ttl = min(self._cfg.default_ttl, MAX_TTL)
        pkt = MeshPacket(
            ptype="RREQ",
            fields={
                "ver": "1",
                "orig": local,
                "tgt": target,
                "rid": rid,
                "ttl": str(ttl),
                "path": local,
            },
            raw="",
        )
        pkt.raw = build_mesh_payload(pkt)
        self._stats.rreq_tx += 1
        # Mark as seen so we don't re-process our own flood
        self._seen_rreq[(local, rid)] = now + DEDUPE_WINDOW_S
        _log.debug("Mesh RREQ: discover %s rid=%s ttl=%d", target, rid, ttl)
        return [pkt]

    def send_data(self, dst: str, body: str, now: float) -> list[MeshPacket]:
        """Build DATA packet(s) for *body* to *dst*; chunks if needed."""
        if not self._cfg.enabled:
            return []
        dst = dst.upper().strip()
        local = self._local_call().upper().strip()
        mid = _rand_id(8)
        ttl = min(self._cfg.default_ttl, MAX_TTL)
        # Find route
        route_str = self._route_for(dst, now)
        # Chunk body
        encoded_body = _pct_encode(body)
        chunks = _chunk_body(encoded_body, MAX_BODY_BYTES)
        total = len(chunks)
        out: list[MeshPacket] = []
        for i, chunk in enumerate(chunks):
            fields: dict[str, str] = {
                "ver": "1",
                "src": local,
                "dst": dst,
                "mid": mid,
                "ttl": str(ttl),
                "route": route_str,
                "body": chunk,
            }
            if total > 1:
                fields["part"] = str(i + 1)
                fields["total"] = str(total)
            pkt = MeshPacket(ptype="DATA", fields=fields, raw="")
            pkt.raw = build_mesh_payload(pkt)
            out.append(pkt)
            self._stats.data_tx += 1
        _log.debug("Mesh DATA: dst=%s mid=%s chunks=%d", dst, mid, total)
        return out

    def handle_rx(
        self, packet_text: str, from_call: str, now: float
    ) -> tuple[list[MeshPacket], list[str]]:
        """Process an incoming mesh payload.

        Returns ``(outbound_packets, local_deliveries)``.
        Guaranteed not to raise; parse errors are logged.
        """
        if not self._cfg.enabled:
            return [], []
        try:
            return self._handle_rx_inner(packet_text, from_call, now)
        except Exception as exc:
            _log.warning("Mesh handle_rx error: %s", exc, exc_info=True)
            return [], []

    def _can_forward(self) -> bool:
        """True only when this node is configured as a REPEATER."""
        return self._cfg.node_role == "REPEATER"

    def tick(self, now: float) -> list[MeshPacket]:
        """Scheduled tick: emit HELLO if enabled, expire stale state."""
        out: list[MeshPacket] = []
        if not self._cfg.enabled:
            return out
        self._expire_routes(now)
        self._expire_dedupe(now)
        self._expire_reassembly(now)
        if self._cfg.hello_enabled and (now - self._last_hello_ts) >= HELLO_INTERVAL_S:
            hello = self._build_hello(now)
            if hello:
                out.append(hello)
        return out

    # -----------------------------------------------------------------------
    # Internal RX dispatch
    # -----------------------------------------------------------------------

    def _handle_rx_inner(
        self, packet_text: str, from_call: str, now: float
    ) -> tuple[list[MeshPacket], list[str]]:
        pkt = parse_mesh_payload(packet_text)
        if pkt is None:
            return [], []

        from_call = from_call.upper().strip()
        outbound: list[MeshPacket] = []
        deliveries: list[str] = []

        if pkt.ptype == "RREQ":
            outbound = self._on_rreq(pkt, from_call, now)
            self._stats.rreq_rx += 1
        elif pkt.ptype == "RREP":
            outbound = self._on_rrep(pkt, from_call, now)
            self._stats.rrep_rx += 1
        elif pkt.ptype == "DATA":
            outbound, deliveries = self._on_data(pkt, from_call, now)
            self._stats.data_rx += 1
        elif pkt.ptype == "RERR":
            self._on_rerr(pkt, from_call, now)
            self._stats.rerr_rx += 1
        elif pkt.ptype == "HELLO":
            self._on_hello(pkt, from_call, now)
            self._stats.hello_rx += 1

        return outbound, deliveries

    # -----------------------------------------------------------------------
    # RREQ handler
    # -----------------------------------------------------------------------

    def _on_rreq(self, pkt: MeshPacket, from_call: str, now: float) -> list[MeshPacket]:
        f = pkt.fields
        orig = f["orig"]
        tgt = f["tgt"]
        rid = f["rid"]
        ttl = _safe_int(f["ttl"], 0)
        path = f["path"]
        local = self._local_call().upper().strip()

        # Dedupe check
        key = (orig, rid)
        if key in self._seen_rreq and now < self._seen_rreq[key]:
            _log.debug("Mesh RREQ dedupe drop: orig=%s rid=%s", orig, rid)
            self._stats.dedupe_drop += 1
            self._stats.rreq_drop += 1
            return []
        self._seen_rreq[key] = now + DEDUPE_WINDOW_S

        # TTL check
        if ttl <= 0:
            _log.debug("Mesh RREQ TTL drop: orig=%s rid=%s ttl=%d", orig, rid, ttl)
            self._stats.ttl_drop += 1
            self._stats.rreq_drop += 1
            return []

        # Learn reverse route to orig via from_call
        self._learn_route(orig, from_call, hop_count=1, metric=1,
                          learned_from="RREQ", now=now)

        # Are we the target?
        if local == tgt:
            hop_count = len(path.split(",")) + 1
            rrep = MeshPacket(
                ptype="RREP",
                fields={
                    "ver": "1",
                    "orig": orig,
                    "tgt": tgt,
                    "rid": rid,
                    "ttl": str(min(hop_count + 2, MAX_TTL)),
                    "path": path + "," + local,
                    "metric": str(hop_count),
                },
                raw="",
            )
            rrep.raw = build_mesh_payload(rrep)
            self._stats.rrep_tx += 1
            _log.debug("Mesh RREP: sending reply to orig=%s", orig)
            return [rrep]

        # Forward (REPEATER role only)
        if not self._can_forward():
            _log.debug("Mesh RREQ: ENDPOINT not forwarding orig=%s rid=%s", orig, rid)
            return []
        if not self._rate_ok(now):
            _log.debug("Mesh RREQ rate drop: orig=%s rid=%s", orig, rid)
            self._stats.rate_drop += 1
            self._stats.rreq_drop += 1
            return []
        new_path = path + ("," + local if local not in path.split(",") else "")
        fwd = MeshPacket(
            ptype="RREQ",
            fields={
                "ver": "1",
                "orig": orig,
                "tgt": tgt,
                "rid": rid,
                "ttl": str(ttl - 1),
                "path": new_path,
            },
            raw="",
        )
        fwd.raw = build_mesh_payload(fwd)
        self._record_rate(now)
        self._stats.rreq_fwd += 1
        _log.debug("Mesh RREQ fwd: orig=%s tgt=%s ttl=%d", orig, tgt, ttl - 1)
        return [fwd]

    # -----------------------------------------------------------------------
    # RREP handler
    # -----------------------------------------------------------------------

    def _on_rrep(self, pkt: MeshPacket, from_call: str, now: float) -> list[MeshPacket]:
        f = pkt.fields
        orig = f["orig"]
        tgt = f["tgt"]
        rid = f["rid"]
        ttl = _safe_int(f["ttl"], 0)
        path = f["path"]
        metric = _safe_int(f["metric"], 99)
        local = self._local_call().upper().strip()

        # Learn route to tgt via from_call
        self._learn_route(tgt, from_call, hop_count=metric, metric=metric,
                          learned_from="RREP", now=now)

        # Are we the original requester?
        if local == orig:
            _log.debug("Mesh RREP: route to %s discovered via %s hops=%d", tgt, from_call, metric)
            return []

        # Forward toward orig (REPEATER role only)
        if not self._can_forward():
            _log.debug("Mesh RREP: ENDPOINT not forwarding toward orig=%s", orig)
            return []
        if ttl <= 0:
            _log.debug("Mesh RREP TTL drop: toward orig=%s", orig)
            self._stats.ttl_drop += 1
            return []
        route_to_orig = self._routes.get(orig)
        if route_to_orig is None or now > route_to_orig.expiry_ts:
            _log.debug("Mesh RREP: no route to orig=%s to forward RREP", orig)
            return []
        if not self._rate_ok(now):
            self._stats.rate_drop += 1
            return []
        fwd = MeshPacket(
            ptype="RREP",
            fields={
                "ver": "1",
                "orig": orig,
                "tgt": tgt,
                "rid": rid,
                "ttl": str(ttl - 1),
                "path": path,
                "metric": str(metric),
            },
            raw="",
        )
        fwd.raw = build_mesh_payload(fwd)
        self._record_rate(now)
        self._stats.rrep_fwd += 1
        return [fwd]

    # -----------------------------------------------------------------------
    # DATA handler
    # -----------------------------------------------------------------------

    def _on_data(
        self, pkt: MeshPacket, from_call: str, now: float
    ) -> tuple[list[MeshPacket], list[str]]:
        f = pkt.fields
        src = f["src"]
        dst = f["dst"]
        mid = f["mid"]
        ttl = _safe_int(f["ttl"], 0)
        body = f["body"]  # still pct-encoded from wire
        part_str = f.get("part", "1")
        total_str = f.get("total", "1")
        part = _safe_int(part_str, 1)
        total = _safe_int(total_str, 1)
        local = self._local_call().upper().strip()

        # Dedupe
        dkey = (src, mid, part_str)
        if dkey in self._seen_data and now < self._seen_data[dkey]:
            _log.debug("Mesh DATA dedupe drop: src=%s mid=%s part=%s", src, mid, part_str)
            self._stats.dedupe_drop += 1
            self._stats.data_drop += 1
            return [], []
        self._seen_data[dkey] = now + DEDUPE_WINDOW_S

        # Learn reverse route
        self._learn_route(src, from_call, hop_count=1, metric=1,
                          learned_from="DATA", now=now)

        # Are we the destination?
        if local == dst:
            decoded = _pct_decode(body)
            if total == 1:
                delivery = f"[MESH DATA] from={src} body={decoded}"
                _log.debug("Mesh DATA local delivery: %s", delivery)
                return [], [delivery]
            else:
                return [], self._reassemble(src, mid, part, total, decoded, now)

        # Forward (REPEATER role only)
        if not self._can_forward():
            _log.debug("Mesh DATA: ENDPOINT not forwarding src=%s mid=%s", src, mid)
            return [], []
        if ttl <= 0:
            _log.debug("Mesh DATA TTL drop: src=%s mid=%s", src, mid)
            self._stats.ttl_drop += 1
            self._stats.data_drop += 1
            return [], []
        route = self._routes.get(dst)
        if route is None or now > route.expiry_ts:
            _log.debug("Mesh DATA no route to %s; emitting RERR", dst)
            self._stats.noroute_drop += 1
            self._stats.data_drop += 1
            rerr = self._build_rerr(src, dst, "NOROUTE", "no route", local)
            out = [rerr] if rerr else []
            self._stats.rerr_tx += len(out)
            return out, []
        if not self._rate_ok(now):
            self._stats.rate_drop += 1
            self._stats.data_drop += 1
            return [], []
        fwd_fields = dict(f)
        fwd_fields["ttl"] = str(ttl - 1)
        fwd = MeshPacket(ptype="DATA", fields=fwd_fields, raw="")
        fwd.raw = build_mesh_payload(fwd)
        self._record_rate(now)
        self._stats.data_fwd += 1
        return [fwd], []

    # -----------------------------------------------------------------------
    # RERR handler
    # -----------------------------------------------------------------------

    def _on_rerr(self, pkt: MeshPacket, from_call: str, now: float) -> None:
        f = pkt.fields
        dst = f["dst"]
        code = f["code"]
        detail = _pct_decode(f.get("detail", ""))
        _log.info("Mesh RERR: dst=%s code=%s detail=%s from=%s", dst, code, detail, from_call)
        # Invalidate route if next hop matches reporter
        route = self._routes.get(dst)
        if route and route.next_hop == from_call and not route.pinned:
            del self._routes[dst]
            _log.debug("Mesh: invalidated route to %s via RERR from %s", dst, from_call)

    # -----------------------------------------------------------------------
    # HELLO handler
    # -----------------------------------------------------------------------

    def _on_hello(self, pkt: MeshPacket, from_call: str, now: float) -> None:
        src = pkt.fields.get("src", from_call).upper().strip()
        _log.debug("Mesh HELLO from %s (from_call=%s)", src, from_call)
        # Opportunistic 1-hop route hint
        self._learn_route(src, from_call, hop_count=1, metric=1,
                          learned_from="RREQ", now=now)

    # -----------------------------------------------------------------------
    # Route table helpers
    # -----------------------------------------------------------------------

    def _learn_route(
        self, destination: str, next_hop: str, hop_count: int, metric: int,
        learned_from: str, now: float
    ) -> None:
        expiry = now + self._cfg.route_expiry_s
        existing = self._routes.get(destination)
        if existing and existing.pinned:
            return  # pinned routes don't get overwritten
        if existing and existing.hop_count <= hop_count and now < existing.expiry_ts:
            # Refresh expiry only
            existing.last_seen_ts = now
            existing.expiry_ts = expiry
            return
        self._routes[destination] = MeshRoute(
            destination=destination,
            next_hop=next_hop,
            hop_count=hop_count,
            metric=metric,
            learned_from=learned_from,
            last_seen_ts=now,
            expiry_ts=expiry,
        )
        _log.debug("Mesh route learned: %s via %s hops=%d src=%s",
                   destination, next_hop, hop_count, learned_from)

    def _route_for(self, dst: str, now: float) -> str:
        route = self._routes.get(dst)
        if route and now < route.expiry_ts:
            return route.next_hop
        return "*"

    def _expire_routes(self, now: float) -> None:
        expired = [d for d, r in self._routes.items()
                   if not r.pinned and now > r.expiry_ts]
        for d in expired:
            del self._routes[d]
            _log.debug("Mesh: route to %s expired", d)

    def _expire_dedupe(self, now: float) -> None:
        self._seen_rreq = {k: v for k, v in self._seen_rreq.items() if v > now}
        self._seen_data = {k: v for k, v in self._seen_data.items() if v > now}

    # -----------------------------------------------------------------------
    # Rate limiting
    # -----------------------------------------------------------------------

    def _rate_ok(self, now: float) -> bool:
        cap = min(self._cfg.rate_limit_ppm, MAX_FWD_PPM_CAP)
        self._rate_bucket = [t for t in self._rate_bucket if now - t < 60.0]
        return len(self._rate_bucket) < cap

    def _record_rate(self, now: float) -> None:
        self._rate_bucket.append(now)

    # -----------------------------------------------------------------------
    # Chunk reassembly
    # -----------------------------------------------------------------------

    def _reassemble(
        self, src: str, mid: str, part: int, total: int,
        decoded_body: str, now: float
    ) -> list[str]:
        key = (src, mid)
        buf = self._reassembly.setdefault(key, {"_total": total, "_ts": now})
        buf[part] = decoded_body
        buf["_ts"] = now  # refresh timeout
        if len(buf) - 2 >= total:  # -2 for _total and _ts keys
            body = "".join(buf[i] for i in range(1, total + 1))
            del self._reassembly[key]
            delivery = f"[MESH DATA] from={src} body={body}"
            _log.debug("Mesh DATA reassembled: src=%s mid=%s", src, mid)
            return [delivery]
        return []

    def _expire_reassembly(self, now: float) -> None:
        expired = [k for k, v in self._reassembly.items()
                   if now - v.get("_ts", 0) > CHUNK_REASSEMBLY_TIMEOUT_S]
        for k in expired:
            _log.debug("Mesh: reassembly timeout for src=%s mid=%s", k[0], k[1])
            del self._reassembly[k]

    # -----------------------------------------------------------------------
    # HELLO builder
    # -----------------------------------------------------------------------

    def _build_hello(self, now: float) -> Optional[MeshPacket]:
        local = self._local_call().upper().strip()
        if not local or local == "N0CALL-0":
            return None
        self._last_hello_ts = now
        pkt = MeshPacket(
            ptype="HELLO",
            fields={
                "ver": "1",
                "src": local,
                "role": self._cfg.node_role,
                "ttl": "1",
            },
            raw="",
        )
        pkt.raw = build_mesh_payload(pkt)
        self._stats.hello_tx += 1
        return pkt

    # -----------------------------------------------------------------------
    # RERR builder
    # -----------------------------------------------------------------------

    def _build_rerr(
        self, src: str, dst: str, code: str, detail: str, reporter: str
    ) -> Optional[MeshPacket]:
        pkt = MeshPacket(
            ptype="RERR",
            fields={
                "ver": "1",
                "src": reporter,
                "dst": dst,
                "code": code,
                "detail": _pct_encode(detail),
            },
            raw="",
        )
        pkt.raw = build_mesh_payload(pkt)
        return pkt


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe_int(s: str, default: int) -> int:
    try:
        return int(s)
    except (ValueError, TypeError):
        return default


def _chunk_body(encoded_body: str, max_bytes: int) -> list[str]:
    """Split encoded body into chunks of at most max_bytes chars.

    Never cuts inside a percent-encoded triplet (%XX).
    Checks both the last char (%) and second-to-last char (%X) of the cut point.
    """
    if not encoded_body:
        return [""]
    chunks = []
    while encoded_body:
        end = min(max_bytes, len(encoded_body))
        if end < len(encoded_body):
            # Step back if the cut lands inside a %XX sequence
            if end >= 2 and encoded_body[end - 2] == "%":
                end -= 2
            elif end >= 1 and encoded_body[end - 1] == "%":
                end -= 1
        chunk = encoded_body[:end]
        encoded_body = encoded_body[end:]
        chunks.append(chunk)
    return chunks or [""]

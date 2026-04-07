#!/usr/bin/env python3
"""Shared dataclasses, enums, and type aliases used across the engine layer."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Radio
# ---------------------------------------------------------------------------

@dataclass
class RadioConfig:
    frequency: float
    offset: float = 0.0
    bandwidth: int = 1       # 0 = narrow, 1 = wide
    squelch: int = 4         # 0..8
    ctcss_tx: Optional[str] = None
    ctcss_rx: Optional[str] = None
    dcs_tx: Optional[str] = None
    dcs_rx: Optional[str] = None

    def clone(self) -> "RadioConfig":
        return RadioConfig(
            frequency=self.frequency,
            offset=self.offset,
            bandwidth=self.bandwidth,
            squelch=self.squelch,
            ctcss_tx=self.ctcss_tx,
            ctcss_rx=self.ctcss_rx,
            dcs_tx=self.dcs_tx,
            dcs_rx=self.dcs_rx,
        )


# ---------------------------------------------------------------------------
# APRS
# ---------------------------------------------------------------------------

@dataclass
class DecodedPacket:
    source: str
    destination: str
    path: list[str]
    info: str
    text: str   # full TNC2 formatted string


@dataclass
class AprsConfig:
    source: str = "N0CALL-0"
    destination: str = "APRS"
    path: str = "WIDE1-1"
    tx_gain: float = 0.34
    preamble_flags: int = 60
    trailing_flags: int = 16
    tx_repeats: int = 1
    symbol_table: str = "/"
    symbol: str = ">"


@dataclass
class ReliableConfig:
    enabled: bool = False
    ack_timeout_s: float = 8.0
    retries: int = 4
    auto_ack: bool = True


# ---------------------------------------------------------------------------
# PTT / Audio
# ---------------------------------------------------------------------------

@dataclass
class PttConfig:
    enabled: bool = True
    line: str = "RTS"       # "RTS" or "DTR"
    active_high: bool = True
    pre_ms: int = 400
    post_ms: int = 120


@dataclass
class AudioConfig:
    output_device_index: Optional[int] = None   # None = system default
    input_device_index: Optional[int] = None
    output_device_name: str = ""                 # hint for auto-restore
    input_device_name: str = ""


# ---------------------------------------------------------------------------
# Comms
# ---------------------------------------------------------------------------

@dataclass
class ChatMessage:
    direction: str     # "TX", "RX", "SYS"
    src: str
    dst: str
    text: str
    msg_id: str = ""
    thread_key: str = ""
    group: str = ""
    backend: str = "APRS"
    delivered: bool = False   # True once an ACK is received for this message
    failed: bool = False
    timestamp: float = field(default_factory=time.monotonic)


# ---------------------------------------------------------------------------
# Thread-safe monotonic message ID counter (APRS spec: 1-5 alnum chars)
# ---------------------------------------------------------------------------

class _MsgIdCounter:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counter = 0

    def next(self) -> str:
        with self._lock:
            self._counter = ((self._counter + 1) % 99999) or 1  # never return "00000"
            return f"{self._counter:05d}"


MSG_ID_COUNTER = _MsgIdCounter()


# ---------------------------------------------------------------------------
# Mesh (Test) — data contracts
# ---------------------------------------------------------------------------

@dataclass
class MeshConfig:
    enabled: bool = False
    node_role: str = "ENDPOINT"     # "ENDPOINT" or "REPEATER"
    default_ttl: int = 4
    rate_limit_ppm: int = 20
    hello_enabled: bool = False
    route_expiry_s: int = 600


@dataclass
class MeshRoute:
    destination: str
    next_hop: str
    hop_count: int
    metric: int
    learned_from: str               # "RREQ", "RREP", "DATA", "MANUAL"
    last_seen_ts: float
    expiry_ts: float
    pinned: bool = False


@dataclass
class MeshPacket:
    ptype: str
    fields: dict
    raw: str


@dataclass
class MeshStats:
    rreq_tx: int = 0
    rreq_rx: int = 0
    rreq_fwd: int = 0
    rreq_drop: int = 0
    rrep_tx: int = 0
    rrep_rx: int = 0
    rrep_fwd: int = 0
    data_tx: int = 0
    data_rx: int = 0
    data_fwd: int = 0
    data_drop: int = 0
    rerr_tx: int = 0
    rerr_rx: int = 0
    hello_tx: int = 0
    hello_rx: int = 0
    dedupe_drop: int = 0
    ttl_drop: int = 0
    rate_drop: int = 0
    noroute_drop: int = 0


# ---------------------------------------------------------------------------
# App-level profile snapshot (fully typed so load/save can validate)
# ---------------------------------------------------------------------------

@dataclass
class AppProfile:
    # Radio
    frequency: float = 145.070
    offset: float = 0.0
    squelch: int = 4
    bandwidth: str = "Wide"
    ctcss_tx: str = ""
    ctcss_rx: str = ""
    dcs_tx: str = ""
    dcs_rx: str = ""
    disable_emphasis: bool = True
    disable_highpass: bool = True
    disable_lowpass: bool = True
    volume: int = 8

    # APRS identity + TX tuning
    aprs_source: str = "N0CALL-0"
    aprs_dest: str = "APRS"
    aprs_path: str = "WIDE1-1"
    aprs_tx_gain: float = 0.34
    aprs_preamble_flags: int = 60
    aprs_tx_repeats: int = 1
    aprs_tx_reinit: bool = True
    aprs_symbol_table: str = "/"
    aprs_symbol: str = ">"

    # APRS messaging
    aprs_msg_to: str = "N0CALL-1"
    aprs_msg_text: str = ""
    aprs_reliable: bool = False
    aprs_ack_timeout: float = 30.0
    aprs_ack_retries: int = 4
    aprs_auto_ack: bool = True

    # APRS position
    aprs_lat: float = 49.2827
    aprs_lon: float = -123.1207
    aprs_comment: str = "uConsole HAM HAT"

    # APRS RX
    aprs_rx_duration: float = 10.0
    aprs_rx_chunk: float = 8.0
    aprs_rx_trim_db: float = -12.0
    aprs_rx_os_level: int = 35
    aprs_rx_auto: bool = False

    # Audio
    output_device_name: str = ""
    input_device_name: str = ""
    auto_audio_select: bool = True

    # PTT
    ptt_enabled: bool = True
    ptt_line: str = "RTS"
    ptt_active_high: bool = True
    ptt_pre_ms: int = 400
    ptt_post_ms: int = 120

    # Tools
    test_tone_freq: float = 1200.0
    test_tone_duration: float = 2.0
    manual_aprs_text: str = "uConsole HAM HAT test"

    # Comms
    chat_contacts: list[str] = field(default_factory=list)
    chat_groups: dict[str, list[str]] = field(default_factory=dict)
    chat_intro_note: str = "uConsole HAM HAT online"

    # Hardware mode
    hardware_mode: str = "SA818"  # "SA818", "DigiRig", or "PAKT"
    digirig_port: str = ""        # serial port for DigiRig PTT (e.g. "COM5")
    pakt_device_name: str = ""
    pakt_device_address: str = ""
    pakt_callsign: str = ""
    pakt_ssid: int = 0
    pakt_capabilities_summary: str = ""

    # Mesh (Test) — all disabled by default; must not alter APRS behavior when off
    mesh_test_enabled: bool = False
    mesh_node_role: str = "ENDPOINT"   # "ENDPOINT" or "REPEATER"
    mesh_default_ttl: int = 4
    mesh_rate_limit_ppm: int = 20
    mesh_hello_enabled: bool = False
    mesh_route_expiry_s: int = 600

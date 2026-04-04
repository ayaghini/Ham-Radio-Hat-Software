#!/usr/bin/env python3
"""PAKT notification parsing helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional


@dataclass
class DeviceStatus:
    radio: str = "unknown"
    bonded: bool = False
    gps_fix: bool = False
    pending_tx: int = 0
    rx_queue: int = 0
    uptime_s: int = 0


@dataclass
class TxResult:
    msg_id: str = ""
    status: str = ""


@dataclass
class RxPacket:
    source: str = ""
    destination: str = ""
    path: str = ""
    info: str = ""


def _load(json_str: str) -> Optional[dict]:
    try:
        data = json.loads(json_str)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def parse_device_status(json_str: str) -> Optional[DeviceStatus]:
    data = _load(json_str)
    if data is None:
        return None
    return DeviceStatus(
        radio=str(data.get("radio", "unknown")),
        bonded=bool(data.get("bonded", False)),
        gps_fix=bool(data.get("gps_fix", False)),
        pending_tx=int(data.get("pending_tx", 0)),
        rx_queue=int(data.get("rx_queue", 0)),
        uptime_s=int(data.get("uptime_s", 0)),
    )


def parse_tx_result(json_str: str) -> Optional[TxResult]:
    data = _load(json_str)
    if data is None:
        return None
    return TxResult(
        msg_id=str(data.get("msg_id", "")),
        status=str(data.get("status", "")),
    )


def parse_rx_packet(json_str: str) -> Optional[RxPacket]:
    data = _load(json_str)
    if data is None:
        return None
    return RxPacket(
        source=str(data.get("from", "")),
        destination=str(data.get("to", "")),
        path=str(data.get("path", "")),
        info=str(data.get("info", "")),
    )


def parse_notify(name: str, json_str: str) -> Optional[dict]:
    data = _load(json_str)
    if data is None:
        return None
    if name == "device_status":
        status = parse_device_status(json_str)
        return None if status is None else {"type": name, "parsed": status, "raw": data}
    if name == "tx_result":
        result = parse_tx_result(json_str)
        return None if result is None else {"type": name, "parsed": result, "raw": data}
    if name == "rx_packet":
        packet = parse_rx_packet(json_str)
        return None if packet is None else {"type": name, "parsed": packet, "raw": data}
    return {"type": name, "parsed": data, "raw": data}

#!/usr/bin/env python3
"""PAKT capability parsing."""

from __future__ import annotations

import json
from dataclasses import dataclass, field


class Feature:
    """Class-level string constants for PAKT capability feature names."""
    APRS_2M = "aprs_2m"
    BLE_CHUNKING = "ble_chunking"
    TELEMETRY = "telemetry"
    MSG_ACK = "msg_ack"
    CONFIG_RW = "config_rw"
    GPS_ONBOARD = "gps_onboard"
    HF_AUDIO = "hf_audio"


@dataclass
class PaktCapabilities:
    fw_ver: str = "unknown"
    hw_rev: str = "unknown"
    protocol: int = 0
    features: frozenset[str] = field(default_factory=frozenset)
    source: str = "read"
    raw_json: str = ""

    @classmethod
    def parse(cls, json_str: str) -> "PaktCapabilities":
        try:
            data = json.loads(json_str)
            return cls(
                fw_ver=str(data.get("fw_ver", "unknown")),
                hw_rev=str(data.get("hw_rev", "unknown")),
                protocol=int(data.get("protocol", 0)),
                features=frozenset(str(item) for item in data.get("features", [])),
                source="read",
                raw_json=json_str,
            )
        except (TypeError, ValueError, json.JSONDecodeError):
            return cls.assumed(source="error", raw_json=json_str)

    @classmethod
    def assumed(cls, source: str = "assumed", raw_json: str = "") -> "PaktCapabilities":
        return cls(
            fw_ver="unknown",
            hw_rev="unknown",
            protocol=1,
            features=frozenset(
                {
                    "aprs_2m",
                    "ble_chunking",
                    "telemetry",
                    "msg_ack",
                    "config_rw",
                    "gps_onboard",
                }
            ),
            source=source,
            raw_json=raw_json,
        )

    def supports(self, feature: str) -> bool:
        return feature in self.features

    def summary(self) -> str:
        feats = ", ".join(sorted(self.features)) if self.features else "(none)"
        suffix = "" if self.source == "read" else f" [{self.source}]"
        return f"protocol={self.protocol} fw={self.fw_ver} hw={self.hw_rev} features=[{feats}]{suffix}"

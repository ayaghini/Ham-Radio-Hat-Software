#!/usr/bin/env python3
"""PAKT BLE chunk split/reassembly."""

from __future__ import annotations

import time
from typing import Callable

HEADER_SIZE = 3
MAX_CHUNKS = 64


def split_payload(payload: bytes, msg_id: int, mtu: int) -> list[bytes]:
    """Split a logical payload into PAKT BLE wire chunks."""
    chunk_payload_max = max(1, int(mtu) - 6)
    if not payload:
        return []

    parts = [
        payload[i : i + chunk_payload_max]
        for i in range(0, len(payload), chunk_payload_max)
    ]
    if len(parts) > MAX_CHUNKS:
        raise ValueError(f"Payload requires {len(parts)} chunks; max is {MAX_CHUNKS}")

    total = len(parts)
    return [
        bytes([msg_id & 0xFF, idx, total]) + part
        for idx, part in enumerate(parts)
    ]


class Reassembler:
    """Reassemble chunked notifications into full payloads."""

    def __init__(self, callback: Callable[[bytes], None], timeout_s: float = 5.0) -> None:
        self._callback = callback
        self._timeout_s = timeout_s
        self._slots: dict[int, dict[str, object]] = {}

    def feed(self, chunk: bytes) -> bool:
        if len(chunk) < HEADER_SIZE:
            return False

        msg_id = int(chunk[0])
        chunk_idx = int(chunk[1])
        chunk_total = int(chunk[2])
        payload = bytes(chunk[HEADER_SIZE:])

        if chunk_total == 0 or chunk_idx >= chunk_total or chunk_total > MAX_CHUNKS:
            return False

        self._expire()
        slot = self._slots.get(msg_id)
        if slot is None:
            slot = {
                "chunk_total": chunk_total,
                "chunks": {},
                "start": time.monotonic(),
            }
            self._slots[msg_id] = slot
        elif int(slot["chunk_total"]) != chunk_total:
            return False

        chunks = slot["chunks"]
        assert isinstance(chunks, dict)
        if chunk_idx in chunks:
            return True

        chunks[chunk_idx] = payload
        if len(chunks) == chunk_total:
            data = b"".join(chunks[i] for i in range(chunk_total))
            del self._slots[msg_id]
            self._callback(data)
        return True

    def reset(self) -> None:
        self._slots.clear()

    def _expire(self) -> None:
        now = time.monotonic()
        stale = [
            msg_id
            for msg_id, slot in self._slots.items()
            if now - float(slot["start"]) > self._timeout_s
        ]
        for msg_id in stale:
            del self._slots[msg_id]

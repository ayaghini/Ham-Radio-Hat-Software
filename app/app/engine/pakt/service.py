#!/usr/bin/env python3
"""PAKT BLE service facade for the host app."""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Coroutine, Optional

from .capability import PaktCapabilities
from .chunker import Reassembler, split_payload
from .constants import (
    NOTIFY_UUIDS,
    UUID_DEV_CAPS,
    UUID_DEV_CONFIG,
    UUID_FW_REV,
    UUID_MANUFACTURER,
    UUID_MODEL_NUM,
    UUID_TX_REQUEST,
)
from .telemetry import parse_notify, parse_tx_result
from .transport import PaktBleTransport, TransportState, is_auth_error

_log = logging.getLogger(__name__)


@dataclass
class PaktScanResult:
    name: str
    address: str


@dataclass
class PaktConnectionEvent:
    state: str
    message: str
    address: str = ""


@dataclass
class PaktDeviceInfoEvent:
    manufacturer: str = ""
    model: str = ""
    firmware_rev: str = ""


@dataclass
class PaktStatusEvent:
    text: str


@dataclass
class PaktConfigEvent:
    text: str
    source: str


@dataclass
class PaktTelemetryEvent:
    name: str
    text: str
    parsed: object | None = None


@dataclass
class PaktTxResultEvent:
    msg_id: str
    status: str
    raw_json: str


@dataclass
class PaktTxQueuedEvent:
    local_id: str
    dest: str
    text: str
    ssid: int


class PaktService:
    """Threaded facade that owns an asyncio loop for BLE operations."""

    def __init__(
        self,
        on_scan_results: Optional[Callable[[list[PaktScanResult]], None]] = None,
        on_connection: Optional[Callable[[PaktConnectionEvent], None]] = None,
        on_status: Optional[Callable[[PaktStatusEvent], None]] = None,
        on_capabilities: Optional[Callable[[PaktCapabilities], None]] = None,
        on_device_info: Optional[Callable[[PaktDeviceInfoEvent], None]] = None,
        on_config: Optional[Callable[[PaktConfigEvent], None]] = None,
        on_telemetry: Optional[Callable[[PaktTelemetryEvent], None]] = None,
        on_tx_queued: Optional[Callable[[PaktTxQueuedEvent], None]] = None,
        on_tx_result: Optional[Callable[[PaktTxResultEvent], None]] = None,
    ) -> None:
        self._on_scan_results = on_scan_results or (lambda items: None)
        self._on_connection = on_connection or (lambda event: None)
        self._on_status = on_status or (lambda event: None)
        self._on_capabilities = on_capabilities or (lambda caps: None)
        self._on_device_info = on_device_info or (lambda event: None)
        self._on_config = on_config or (lambda event: None)
        self._on_telemetry = on_telemetry or (lambda event: None)
        self._on_tx_queued = on_tx_queued or (lambda event: None)
        self._on_tx_result = on_tx_result or (lambda event: None)

        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="pakt-ble-loop")
        self._thread.start()

        self._transport = PaktBleTransport(
            on_state=self._handle_transport_state,
            on_reconnected=lambda: asyncio.run_coroutine_threadsafe(self._resubscribe(), self._loop),
            on_reconnect_failed=lambda: self._on_status(PaktStatusEvent("PAKT reconnect failed")),
        )
        self._msg_id = 0
        self._local_tx_id = 0
        self._reassemblers: dict[str, Reassembler] = {}
        self._capabilities = PaktCapabilities.assumed(source="init")
        self._config_cache_path: Optional[Path] = None

    @property
    def is_connected(self) -> bool:
        return self._transport.is_connected

    @property
    def capabilities(self) -> PaktCapabilities:
        return self._capabilities

    @property
    def address(self) -> str:
        return self._transport.address

    def set_config_cache_path(self, path: Path) -> None:
        self._config_cache_path = path

    def scan(self, timeout: float = 8.0) -> None:
        self._submit(self._scan(timeout))

    def connect(self, address: str) -> None:
        self._submit(self._connect(address))

    def disconnect(self) -> None:
        self._submit(self._disconnect())

    def read_device_info(self) -> None:
        self._submit(self._read_device_info())

    def read_capabilities(self) -> None:
        self._submit(self._read_capabilities())

    def read_config(self) -> None:
        self._submit(self._read_config())

    def write_config(self, json_str: str) -> None:
        self._submit(self._write_config(json_str))

    def send_tx_request(self, dest: str, text: str, ssid: int = 0) -> None:
        local_id = self._next_local_tx_id()
        payload = json.dumps({"dest": dest, "text": text, "ssid": int(ssid)})
        self._submit(self._send_tx_request(payload, dest=dest, text=text, ssid=int(ssid), local_id=local_id))

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def _submit(self, coro: Coroutine[Any, Any, None]) -> None:
        asyncio.run_coroutine_threadsafe(coro, self._loop)

    async def _scan(self, timeout: float) -> None:
        try:
            found = await self._transport.scan(timeout=timeout)
            self._on_scan_results([PaktScanResult(name=name, address=address) for name, address in found])
            self._on_status(PaktStatusEvent(f"PAKT scan complete: {len(found)} device(s)"))
        except Exception as exc:
            self._on_status(PaktStatusEvent(f"PAKT scan failed: {exc}"))

    async def _connect(self, address: str) -> None:
        try:
            await self._transport.connect(address)
            await self._read_capabilities()
            await self._subscribe_all()
            await self._read_device_info()
            self._on_status(PaktStatusEvent(f"PAKT connected: {address}"))
        except Exception as exc:
            self._on_status(PaktStatusEvent(f"PAKT connect failed: {exc}"))

    async def _disconnect(self) -> None:
        try:
            await self._transport.disconnect()
            for reassembler in self._reassemblers.values():
                reassembler.reset()
            self._reassemblers.clear()
            self._on_status(PaktStatusEvent("PAKT disconnected"))
        except Exception as exc:
            self._on_status(PaktStatusEvent(f"PAKT disconnect failed: {exc}"))

    async def _read_device_info(self) -> None:
        client = self._transport.client
        if client is None:
            self._on_status(PaktStatusEvent("PAKT not connected"))
            return
        try:
            manufacturer = (await client.read_gatt_char(UUID_MANUFACTURER)).decode("utf-8", errors="replace")
            model = (await client.read_gatt_char(UUID_MODEL_NUM)).decode("utf-8", errors="replace")
            firmware_rev = (await client.read_gatt_char(UUID_FW_REV)).decode("utf-8", errors="replace")
            self._on_device_info(
                PaktDeviceInfoEvent(
                    manufacturer=manufacturer,
                    model=model,
                    firmware_rev=firmware_rev,
                )
            )
        except Exception as exc:
            self._on_status(PaktStatusEvent(f"PAKT device info read failed: {exc}"))

    async def _read_capabilities(self) -> None:
        client = self._transport.client
        if client is None:
            return
        try:
            raw = await client.read_gatt_char(UUID_DEV_CAPS)
            text = raw.decode("utf-8", errors="replace")
            self._capabilities = PaktCapabilities.parse(text)
            self._on_capabilities(self._capabilities)
        except Exception as exc:
            self._capabilities = PaktCapabilities.assumed(source="error", raw_json=str(exc))
            self._on_capabilities(self._capabilities)
            self._on_status(PaktStatusEvent(f"PAKT capability read fallback: {exc}"))

    async def _read_config(self) -> None:
        client = self._transport.client
        if client is None:
            self._on_status(PaktStatusEvent("PAKT not connected"))
            return
        try:
            raw = await client.read_gatt_char(UUID_DEV_CONFIG)
            text = raw.decode("utf-8", errors="replace")
            self._cache_config(text)
            self._on_config(PaktConfigEvent(text=text, source="read"))
        except Exception as exc:
            self._on_status(PaktStatusEvent(f"PAKT config read failed: {exc}"))

    async def _write_config(self, json_str: str) -> None:
        ok = await self._write_chunked(UUID_DEV_CONFIG, "config", json_str.encode("utf-8"), response=True)
        if ok:
            self._cache_config(json_str)
            self._on_config(PaktConfigEvent(text=json_str, source="write"))

    async def _send_tx_request(self, json_str: str, dest: str, text: str, ssid: int, local_id: str) -> None:
        ok = await self._write_chunked(UUID_TX_REQUEST, "tx_request", json_str.encode("utf-8"), response=True)
        if ok:
            self._on_tx_queued(PaktTxQueuedEvent(local_id=local_id, dest=dest, text=text, ssid=ssid))
            self._on_status(PaktStatusEvent("PAKT TX request queued"))

    async def _write_chunked(self, uuid: str, name: str, payload: bytes, response: bool) -> bool:
        """Write payload in chunks. Returns True on success, False on any failure."""
        client = self._transport.client
        if client is None:
            self._on_status(PaktStatusEvent("PAKT not connected"))
            return False
        try:
            for chunk in split_payload(payload, self._next_msg_id(), self._transport.mtu):
                await client.write_gatt_char(uuid, chunk, response=response)
            return True
        except Exception as exc:
            if is_auth_error(exc):
                self._on_status(PaktStatusEvent(f"PAKT {name} write requires pairing/bonding"))
            else:
                self._on_status(PaktStatusEvent(f"PAKT {name} write failed: {exc}"))
            return False

    async def _subscribe_all(self) -> None:
        client = self._transport.client
        if client is None:
            return
        for name, uuid in NOTIFY_UUIDS.items():
            try:
                self._reassemblers[uuid] = Reassembler(lambda data, _name=name: self._on_reassembled(_name, data))
                await client.start_notify(uuid, self._on_notify)
            except Exception as exc:
                self._on_status(PaktStatusEvent(f"PAKT subscribe failed for {name}: {exc}"))

    async def _resubscribe(self) -> None:
        self._on_status(PaktStatusEvent("PAKT reconnected - re-subscribing"))
        await self._read_capabilities()
        await self._subscribe_all()

    def _on_notify(self, characteristic, data: bytearray) -> None:
        uuid = getattr(characteristic, "uuid", "").lower()
        reassembler = self._reassemblers.get(uuid)
        if reassembler is None:
            return
        reassembler.feed(bytes(data))

    def _on_reassembled(self, name: str, data: bytes) -> None:
        text = data.decode("utf-8", errors="replace")
        parsed = parse_notify(name, text)
        if name == "tx_result":
            # tx_result has a dedicated handler — do not double-route through telemetry.
            result = parse_tx_result(text)
            if result is not None:
                self._on_tx_result(PaktTxResultEvent(msg_id=result.msg_id, status=result.status, raw_json=text))
        else:
            self._on_telemetry(
                PaktTelemetryEvent(
                    name=name,
                    text=text,
                    parsed=None if parsed is None else parsed.get("parsed"),
                )
            )

    def _handle_transport_state(self, state: TransportState, message: str) -> None:
        self._on_connection(PaktConnectionEvent(state=state.name, message=message, address=self._transport.address))

    def _next_msg_id(self) -> int:
        self._msg_id = (self._msg_id + 1) % 256
        return self._msg_id

    def _next_local_tx_id(self) -> str:
        self._local_tx_id = (self._local_tx_id + 1) % 100000
        return f"pakt-local:{self._local_tx_id or 1}"

    def _cache_config(self, text: str) -> None:
        if self._config_cache_path is None:
            return
        try:
            self._config_cache_path.parent.mkdir(parents=True, exist_ok=True)
            self._config_cache_path.write_text(text, encoding="utf-8")
        except Exception as exc:
            _log.debug("PAKT config cache write failed: %s", exc)

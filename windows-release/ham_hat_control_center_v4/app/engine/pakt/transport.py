#!/usr/bin/env python3
"""PAKT BLE transport."""

from __future__ import annotations

import asyncio
import logging
from enum import Enum, auto
from typing import Callable, Optional

try:
    from bleak import BleakClient, BleakScanner
except Exception:  # pragma: no cover - optional dependency during bootstrap
    BleakClient = None
    BleakScanner = None

from .constants import DEVICE_NAME_PREFIX, MAX_RECONNECT_ATTEMPTS, RECONNECT_DELAY_S

_log = logging.getLogger(__name__)


class TransportState(Enum):
    IDLE = auto()
    SCANNING = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    RECONNECTING = auto()
    ERROR = auto()


class PaktBleTransport:
    def __init__(
        self,
        on_state: Optional[Callable[[TransportState, str], None]] = None,
        on_reconnected: Optional[Callable[[], None]] = None,
        on_reconnect_failed: Optional[Callable[[], None]] = None,
    ) -> None:
        self._on_state = on_state or (lambda state, message: None)
        self._on_reconnected = on_reconnected or (lambda: None)
        self._on_reconnect_failed = on_reconnect_failed or (lambda: None)
        self._client: Optional[BleakClient] = None
        self._state = TransportState.IDLE
        self._address = ""
        self._user_disconnected = False
        self._reconnect_task: Optional[asyncio.Task] = None

    @property
    def state(self) -> TransportState:
        return self._state

    @property
    def client(self) -> Optional[BleakClient]:
        if self._client and self._client.is_connected:
            return self._client
        return None

    @property
    def mtu(self) -> int:
        if self._client is None:
            return 23
        return getattr(self._client, "mtu_size", 23)

    @property
    def address(self) -> str:
        return self._address

    @property
    def is_connected(self) -> bool:
        return self.client is not None and self._state == TransportState.CONNECTED

    async def scan(self, timeout: float = 8.0) -> list[tuple[str, str]]:
        if BleakScanner is None:
            raise RuntimeError("bleak is not installed")
        self._set_state(TransportState.SCANNING, f"scanning ({timeout:.0f}s)")
        try:
            devices = await BleakScanner.discover(timeout=timeout)
            return [
                (device.name or "?", device.address)
                for device in devices
                if device.name and DEVICE_NAME_PREFIX in device.name
            ]
        finally:
            self._set_state(TransportState.IDLE, "scan complete")

    async def connect(self, address: str) -> None:
        if BleakClient is None:
            raise RuntimeError("bleak is not installed")
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
        self._address = address
        self._user_disconnected = False
        self._set_state(TransportState.CONNECTING, f"connecting to {address}")
        self._client = BleakClient(address, disconnected_callback=self._on_disconnect)
        await self._client.connect()
        self._set_state(TransportState.CONNECTED, f"connected (mtu={self.mtu})")

    async def disconnect(self) -> None:
        self._user_disconnected = True
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
        if self._client and self._client.is_connected:
            await self._client.disconnect()
        self._client = None
        self._set_state(TransportState.IDLE, "disconnected")

    def _on_disconnect(self, _: BleakClient) -> None:
        if self._user_disconnected:
            return
        self._set_state(TransportState.RECONNECTING, "connection lost - reconnecting")
        self._reconnect_task = asyncio.ensure_future(self._reconnect())

    async def _reconnect(self) -> None:
        for attempt in range(1, MAX_RECONNECT_ATTEMPTS + 1):
            await asyncio.sleep(RECONNECT_DELAY_S)
            self._set_state(
                TransportState.RECONNECTING,
                f"reconnect attempt {attempt}/{MAX_RECONNECT_ATTEMPTS}",
            )
            try:
                self._client = BleakClient(self._address, disconnected_callback=self._on_disconnect)
                await self._client.connect()
                self._set_state(TransportState.CONNECTED, f"reconnected (mtu={self.mtu})")
                self._on_reconnected()
                return
            except Exception as exc:
                _log.warning("PAKT reconnect attempt %s failed: %s", attempt, exc)
        self._set_state(TransportState.ERROR, "reconnect failed")
        self._on_reconnect_failed()

    def _set_state(self, state: TransportState, message: str) -> None:
        self._state = state
        self._on_state(state, message)


_AUTH_KEYWORDS = (
    "authentication",
    "authorization",
    "insufficient",
    "access denied",
    "not permitted",
    "0x0005",
    "0x000f",
)


def is_auth_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(keyword in text for keyword in _AUTH_KEYWORDS)

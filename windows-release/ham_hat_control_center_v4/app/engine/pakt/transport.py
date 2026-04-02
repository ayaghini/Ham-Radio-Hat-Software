#!/usr/bin/env python3
"""PAKT BLE transport.

Cross-platform BLE requirements (CP-102)
-----------------------------------------
bleak is cross-platform and handles the underlying OS BLE stack, but each
platform has additional requirements that must be met before scanning and
connecting will work:

Windows (WinRT BLE)
  - Windows 10 version 1709+ is required for bleak's WinRT backend.
  - No special permissions are needed for scanning on modern Windows 10/11.
  - Bonded device pairing is handled by the OS pairing dialog.

macOS (CoreBluetooth)
  - The first BleakScanner.discover() call will trigger an OS permission
    prompt: "Allow <app> to use Bluetooth?". If denied, the scan returns an
    empty list with no error.
  - Packaged .app bundles MUST include NSBluetoothAlwaysUsageDescription in
    their Info.plist (required since macOS 12+; absence causes a crash on
    first BLE access).
  - The key to add to Info.plist:
      <key>NSBluetoothAlwaysUsageDescription</key>
      <string>HAM HAT Control Center uses Bluetooth to connect to the PAKT TNC.</string>
  - BLE device addresses on macOS are UUIDs (not MAC addresses); the stored
    pakt_device_address may differ from the address shown on Windows.

Linux / Raspberry Pi OS (BlueZ via D-Bus)
  - BlueZ must be installed and running: `systemctl status bluetooth`
  - The user must be in the `bluetooth` group, OR a polkit rule must grant
    access, OR the process must run as root.
  - To add a user to the bluetooth group: `sudo usermod -aG bluetooth $USER`
  - On Raspberry Pi OS, Bluetooth is enabled by default; group membership is
    still required for non-root BLE access.
  - BlueZ version 5.43+ is required; check with: `bluetoothctl --version`
  - If scan returns empty on Linux, run `bluetoothctl scan on` to verify the
    adapter works outside the app before debugging bleak.
"""

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
        # Captured from the running event loop during connect() so that
        # _on_disconnect can safely schedule reconnect via call_soon_threadsafe
        # regardless of which thread bleak invokes the callback from.
        self._loop: Optional[asyncio.AbstractEventLoop] = None

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
        # Capture the event loop here — we are running inside it (called via
        # run_coroutine_threadsafe from PaktService).  Storing the reference
        # lets _on_disconnect schedule reconnect safely via call_soon_threadsafe
        # regardless of which thread bleak delivers the callback from.
        self._loop = asyncio.get_running_loop()
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
        if self._loop is not None:
            # Use call_soon_threadsafe so this is always safe regardless of
            # which thread bleak delivers the callback from (CoreBluetooth
            # dispatch queue on macOS, D-Bus thread on Linux, etc.).
            self._loop.call_soon_threadsafe(self._create_reconnect_task)
        else:
            # Fallback: assume we are already inside the event loop (Windows
            # WinRT path with older bleak where _loop may not be set yet).
            self._reconnect_task = asyncio.ensure_future(self._reconnect())

    def _create_reconnect_task(self) -> None:
        """Schedule the reconnect coroutine as a Task on the event loop.

        Always called from within the event loop via call_soon_threadsafe,
        so create_task is safe here.
        """
        if not self._user_disconnected and self._loop is not None:
            self._reconnect_task = self._loop.create_task(self._reconnect())

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

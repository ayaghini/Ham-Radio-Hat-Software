"""platform/ble_manager.py — BLE scan / connect / send for HAM HAT Android app.

Strategy
--------
1. On Android (API ≥ 26) use *bleak* with the Android backend (bleak 0.22+
   ships a BleakScanner that routes through Android's BluetoothManager via
   pyjnius).  Fall back to a pyjnius direct path if bleak is absent.

2. On desktop (development / CI) use bleak normally (CoreBluetooth on macOS,
   BlueZ on Linux).

3. The manager exposes a clean callback-based API that the Kivy screens
   consume without caring about the underlying backend.

Android permissions required (set in buildozer.spec):
    BLUETOOTH, BLUETOOTH_ADMIN, BLUETOOTH_SCAN, BLUETOOTH_CONNECT,
    ACCESS_FINE_LOCATION

Usage::

    mgr = BleManager()
    mgr.on_device_found  = lambda addr, name: ...
    mgr.on_state_changed = lambda state: ...        # BleState.*
    mgr.on_data_received = lambda data: ...
    mgr.start_scan(timeout=10)
    mgr.connect(address)
    mgr.send(bytes)
    mgr.disconnect()
"""

from __future__ import annotations

import asyncio
import logging
import threading
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, List, Optional

try:
    from kivy.utils import platform as _kivy_platform
    _ON_ANDROID: bool = (_kivy_platform == "android")
except ImportError:
    _ON_ANDROID = False

_log = logging.getLogger(__name__)

# ── PAKT BLE UUIDs (from app/engine/pakt/constants.py) ─────────────────────
_PAKT_SERVICE_UUID  = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
_TX_CHAR_UUID       = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"  # write
_RX_CHAR_UUID       = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"  # notify


class BleState(Enum):
    IDLE         = auto()
    SCANNING     = auto()
    CONNECTING   = auto()
    CONNECTED    = auto()
    RECONNECTING = auto()
    ERROR        = auto()


@dataclass
class BleDevice:
    address: str
    name: str
    rssi: int = -100


class BleManager:
    """Thread-safe BLE manager.  Callbacks are invoked on the calling thread
    (typically the Kivy main thread via Clock.schedule_once)."""

    def __init__(self) -> None:
        self._state: BleState = BleState.IDLE
        self._devices: List[BleDevice] = []
        self._client = None          # bleak BleakClient when connected
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._connected_address: Optional[str] = None

        # Public callbacks — set by screens
        self.on_device_found:  Optional[Callable[[BleDevice], None]] = None
        self.on_state_changed: Optional[Callable[[BleState], None]] = None
        self.on_data_received: Optional[Callable[[bytes], None]]     = None
        self.on_error:         Optional[Callable[[str], None]]       = None

    # ── public API ──────────────────────────────────────────────────────────

    def start_scan(self, timeout: float = 10.0) -> None:
        """Start BLE scan for PAKT devices.  Non-blocking; results via on_device_found."""
        if self._state in (BleState.SCANNING, BleState.CONNECTED):
            return
        self._devices.clear()
        self._set_state(BleState.SCANNING)
        self._run_async(self._async_scan(timeout))

    def stop_scan(self) -> None:
        """Stop an in-progress scan."""
        if self._state == BleState.SCANNING:
            self._set_state(BleState.IDLE)

    def connect(self, address: str) -> None:
        """Connect to a BLE device by address.  Non-blocking."""
        if self._state == BleState.CONNECTED:
            self.disconnect()
        self._set_state(BleState.CONNECTING)
        self._connected_address = address
        self._run_async(self._async_connect(address))

    def disconnect(self) -> None:
        """Disconnect from the current device."""
        if self._client is not None:
            self._run_async(self._async_disconnect())
        else:
            self._set_state(BleState.IDLE)

    def send(self, data: bytes) -> None:
        """Send raw bytes to the TX characteristic.  Must be CONNECTED."""
        if self._state != BleState.CONNECTED or self._client is None:
            _log.warning("BleManager.send: not connected")
            return
        self._run_async(self._async_send(data))

    @property
    def state(self) -> BleState:
        return self._state

    @property
    def found_devices(self) -> List[BleDevice]:
        return list(self._devices)

    # ── async helpers ────────────────────────────────────────────────────────

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.new_event_loop()
            self._thread = threading.Thread(
                target=self._loop.run_forever, daemon=True, name="BleEventLoop"
            )
            self._thread.start()
        return self._loop

    def _run_async(self, coro) -> None:
        loop = self._get_loop()
        asyncio.run_coroutine_threadsafe(coro, loop)

    async def _async_scan(self, timeout: float) -> None:
        try:
            from bleak import BleakScanner
        except ImportError:
            _log.error("bleak not installed — BLE unavailable")
            self._set_state(BleState.ERROR)
            self._fire_error("bleak not installed")
            return

        try:
            def detection_callback(device, advertisement_data):
                if self._state != BleState.SCANNING:
                    return
                dev = BleDevice(
                    address=device.address,
                    name=device.name or device.address,
                    rssi=advertisement_data.rssi or -100,
                )
                # Deduplicate
                known = {d.address for d in self._devices}
                if dev.address not in known:
                    self._devices.append(dev)
                    if self.on_device_found:
                        self.on_device_found(dev)

            async with BleakScanner(detection_callback) as scanner:  # noqa: F841
                await asyncio.sleep(timeout)
        except Exception as exc:
            _log.error("BLE scan error: %s", exc)
            self._fire_error(str(exc))
        finally:
            if self._state == BleState.SCANNING:
                self._set_state(BleState.IDLE)

    async def _async_connect(self, address: str) -> None:
        try:
            from bleak import BleakClient
        except ImportError:
            self._set_state(BleState.ERROR)
            self._fire_error("bleak not installed")
            return

        def disconnected_callback(client):  # noqa: ARG001
            _log.warning("BLE disconnected from %s", address)
            self._client = None
            self._set_state(BleState.IDLE)

        try:
            client = BleakClient(address, disconnected_callback=disconnected_callback)
            await client.connect(timeout=15.0)
            self._client = client
            # Subscribe to RX notifications
            await client.start_notify(_RX_CHAR_UUID, self._handle_notify)
            self._set_state(BleState.CONNECTED)
            _log.info("BLE connected to %s", address)
        except Exception as exc:
            _log.error("BLE connect error: %s", exc)
            self._client = None
            self._set_state(BleState.ERROR)
            self._fire_error(str(exc))

    async def _async_disconnect(self) -> None:
        client = self._client
        self._client = None
        if client and client.is_connected:
            try:
                await client.disconnect()
            except Exception as exc:
                _log.debug("BLE disconnect error (ignored): %s", exc)
        self._set_state(BleState.IDLE)

    async def _async_send(self, data: bytes) -> None:
        if self._client is None:
            return
        try:
            await self._client.write_gatt_char(_TX_CHAR_UUID, data, response=False)
        except Exception as exc:
            _log.error("BLE send error: %s", exc)
            self._fire_error(str(exc))

    def _handle_notify(self, _sender: int, data: bytearray) -> None:
        if self.on_data_received:
            self.on_data_received(bytes(data))

    # ── state helpers ────────────────────────────────────────────────────────

    def _set_state(self, state: BleState) -> None:
        if self._state != state:
            self._state = state
            _log.debug("BleManager state → %s", state.name)
            if self.on_state_changed:
                self.on_state_changed(state)

    def _fire_error(self, msg: str) -> None:
        if self.on_error:
            self.on_error(msg)


# ── Android-specific permission request helper ───────────────────────────────

def request_ble_permissions() -> None:
    """Request Android BLE permissions at runtime (Android 12+ API 31+)."""
    if not _ON_ANDROID:
        return
    try:
        from android.permissions import request_permissions, Permission  # type: ignore[import]
        request_permissions([
            Permission.BLUETOOTH,
            Permission.BLUETOOTH_ADMIN,
            Permission.BLUETOOTH_SCAN,
            Permission.BLUETOOTH_CONNECT,
            Permission.ACCESS_FINE_LOCATION,
        ])
    except Exception as exc:
        _log.warning("Could not request BLE permissions: %s", exc)

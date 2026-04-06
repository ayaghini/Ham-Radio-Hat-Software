"""hal/pakt_service_bridge.py — PaktService bridge with Kivy-thread-safe callbacks.

The engine's PaktService delivers all callbacks on its own internal asyncio
event loop thread.  Kivy widgets must only be touched from the main thread.

This bridge:
  1. Creates a PaktService instance.
  2. Wraps every callback with Clock.schedule_once() so UI updates are safe.
  3. Exposes a simplified API that the mesh_screen and control_screen use.

Architecture
────────────
  PaktService  (background thread)
      ↓ raw callbacks
  PaktServiceBridge  (wraps in Clock.schedule_once)
      ↓ main-thread callbacks
  MeshScreen / ControlScreen

Event types forwarded
─────────────────────
  on_scan_results(results: list[PaktScanResult])
  on_connected(event: PaktConnectionEvent)
  on_disconnected()
  on_status(msg: str)
  on_device_info(event: PaktDeviceInfoEvent)
  on_capabilities(caps: PaktCapabilities)
  on_config(event: PaktConfigEvent)
  on_telemetry(event: PaktTelemetryEvent)
  on_tx_queued(event: PaktTxQueuedEvent)
  on_tx_result(event: PaktTxResultEvent)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Optional

_log = logging.getLogger(__name__)


def _ui(fn: Callable, *args) -> None:
    """Schedule *fn(*args)* on the Kivy main thread."""
    try:
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: fn(*args), 0)
    except Exception:
        fn(*args)   # fall back to direct call (desktop CI / tests)


class PaktServiceBridge:
    """Thin wrapper around PaktService that ensures Kivy-thread-safe callbacks.

    Usage::

        bridge = PaktServiceBridge()
        bridge.on_connected    = lambda evt: ...
        bridge.on_tx_result    = lambda evt: ...
        bridge.start()

        bridge.scan(timeout=8.0)
        bridge.connect("AA:BB:CC:DD:EE:FF")
        bridge.send("W1AW", "Hello mesh!")
        bridge.disconnect()
        bridge.stop()
    """

    def __init__(self) -> None:
        self._service = None    # PaktService — created in start()

        # ── Public callbacks (set by screens) ──────────────────────────────
        self.on_scan_results: Optional[Callable] = None
        self.on_connected:    Optional[Callable] = None
        self.on_disconnected: Optional[Callable] = None
        self.on_status:       Optional[Callable[[str], None]] = None
        self.on_device_info:  Optional[Callable] = None
        self.on_capabilities: Optional[Callable] = None
        self.on_config:       Optional[Callable] = None
        self.on_telemetry:    Optional[Callable] = None
        self.on_tx_queued:    Optional[Callable] = None
        self.on_tx_result:    Optional[Callable] = None

        # Optional: path for config cache (set before start())
        self.config_cache_path: Optional[Path] = None

    # ── lifecycle ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Instantiate PaktService and start its background loop."""
        if self._service is not None:
            return
        try:
            from app.engine.pakt.service import PaktService
        except ImportError as exc:
            _log.error("PaktService import failed: %s", exc)
            return

        self._service = PaktService(
            on_scan_results  = self._wrap(self._fwd_scan_results),
            on_connection    = self._wrap(self._fwd_connection),
            on_status        = self._wrap(self._fwd_status),
            on_capabilities  = self._wrap(self._fwd_capabilities),
            on_device_info   = self._wrap(self._fwd_device_info),
            on_config        = self._wrap(self._fwd_config),
            on_telemetry     = self._wrap(self._fwd_telemetry),
            on_tx_queued     = self._wrap(self._fwd_tx_queued),
            on_tx_result     = self._wrap(self._fwd_tx_result),
        )
        if self.config_cache_path:
            self._service.set_config_cache_path(self.config_cache_path)
        _log.info("PaktServiceBridge started")

    def stop(self) -> None:
        """Disconnect and stop the service."""
        if self._service is None:
            return
        try:
            self._service.disconnect()
        except Exception as exc:
            _log.debug("PaktService disconnect on stop: %s", exc)
        self._service = None
        _log.info("PaktServiceBridge stopped")

    @property
    def is_running(self) -> bool:
        return self._service is not None

    @property
    def is_connected(self) -> bool:
        return self._service is not None and self._service.is_connected

    # ── command API ───────────────────────────────────────────────────────────

    def scan(self, timeout: float = 8.0) -> None:
        if self._service:
            self._service.scan(timeout=timeout)

    def connect(self, address: str) -> None:
        if self._service:
            self._service.connect(address)

    def disconnect(self) -> None:
        if self._service:
            self._service.disconnect()

    def send(self, dest: str, text: str, ssid: int = 0) -> None:
        """Send a PAKT mesh TX request."""
        if self._service:
            self._service.send_tx_request(dest=dest, text=text, ssid=ssid)

    def read_device_info(self) -> None:
        if self._service:
            self._service.read_device_info()

    def read_capabilities(self) -> None:
        if self._service:
            self._service.read_capabilities()

    def read_config(self) -> None:
        if self._service:
            self._service.read_config()

    def write_config(self, json_str: str) -> None:
        if self._service:
            self._service.write_config(json_str)

    # ── internal forwarding (called from PaktService background thread) ───────

    @staticmethod
    def _wrap(fn: Callable) -> Callable:
        """Return a callback that schedules *fn* on the Kivy main thread."""
        def _cb(*args, **kwargs):
            _ui(fn, *args)
        return _cb

    def _fwd_scan_results(self, results) -> None:
        if self.on_scan_results:
            self.on_scan_results(results)

    def _fwd_connection(self, event) -> None:
        # PaktConnectionEvent has .connected bool and .address str
        try:
            connected = event.connected
            address   = getattr(event, "address", "")
        except Exception:
            connected = False
            address   = ""
        if connected:
            if self.on_connected:
                self.on_connected(event)
        else:
            if self.on_disconnected:
                self.on_disconnected()
            if self.on_status:
                self.on_status("PAKT disconnected")

    def _fwd_status(self, event) -> None:
        msg = getattr(event, "message", str(event))
        if self.on_status:
            self.on_status(msg)

    def _fwd_capabilities(self, caps) -> None:
        if self.on_capabilities:
            self.on_capabilities(caps)

    def _fwd_device_info(self, event) -> None:
        if self.on_device_info:
            self.on_device_info(event)

    def _fwd_config(self, event) -> None:
        if self.on_config:
            self.on_config(event)

    def _fwd_telemetry(self, event) -> None:
        if self.on_telemetry:
            self.on_telemetry(event)

    def _fwd_tx_queued(self, event) -> None:
        if self.on_tx_queued:
            self.on_tx_queued(event)

    def _fwd_tx_result(self, event) -> None:
        if self.on_tx_result:
            self.on_tx_result(event)

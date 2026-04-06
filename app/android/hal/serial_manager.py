"""platform/serial_manager.py — USB serial management for Android (USB OTG).

On Android the device acts as USB host.  Standard pyserial *cannot*
enumerate Android USB devices directly; instead we use:

  • `usbserial4a` — a pure-Python pyjnius wrapper around the
    felHR85/UsbSerial Android library.  Handles CH340, CP210x, FTDI, etc.
    Add to buildozer.spec:
        android.gradle_dependencies = com.github.felHR85:UsbSerial:6.1.0

On desktop (development):
  • Falls back to standard `pyserial` (serial.tools.list_ports).

The API mirrors what the desktop app expects: list_ports() returns a
list of (device, description) tuples; connect/disconnect/send/read are
synchronous calls wrapped in a background thread.

Permissions required (buildozer.spec):
    android.features = android.hardware.usb.host
    android.meta_data = android.hardware.usb.action.USB_DEVICE_ATTACHED

A `device_filter.xml` in `app/android/assets/` restricts which USB VIDs
the system auto-prompts for (optional; all devices visible without it).
"""

from __future__ import annotations

import logging
import threading
from typing import Callable, List, Optional, Tuple

try:
    from kivy.utils import platform as _kivy_platform
    _ON_ANDROID: bool = (_kivy_platform == "android")
except ImportError:
    _ON_ANDROID = False

_log = logging.getLogger(__name__)


class SerialManager:
    """Wraps USB serial for Android and pyserial for desktop.

    Callbacks:
        on_data_received(data: bytes)  — called from reader thread
        on_state_changed(connected: bool)
        on_error(msg: str)
    """

    def __init__(self) -> None:
        self._connected = False
        self._port = None          # serial.Serial or usbserial4a device
        self._reader_thread: Optional[threading.Thread] = None
        self._stop_reader = threading.Event()

        self.on_data_received: Optional[Callable[[bytes], None]] = None
        self.on_state_changed: Optional[Callable[[bool], None]]  = None
        self.on_error:         Optional[Callable[[str], None]]   = None

    # ── public API ──────────────────────────────────────────────────────────

    def list_ports(self) -> List[Tuple[str, str]]:
        """Return list of (device, description) for available serial ports."""
        if _ON_ANDROID:
            return self._android_list_ports()
        else:
            return self._desktop_list_ports()

    def connect(self, port: str, baudrate: int = 9600) -> bool:
        """Open a serial connection.  Returns True on success."""
        if self._connected:
            self.disconnect()
        if _ON_ANDROID:
            return self._android_connect(port, baudrate)
        else:
            return self._desktop_connect(port, baudrate)

    def disconnect(self) -> None:
        self._stop_reader.set()
        if self._port is not None:
            try:
                self._port.close()
            except Exception:
                pass
            self._port = None
        self._connected = False
        self._stop_reader.clear()
        if self.on_state_changed:
            self.on_state_changed(False)

    def send(self, data: bytes) -> None:
        if not self._connected or self._port is None:
            _log.warning("SerialManager.send: not connected")
            return
        try:
            self._port.write(data)
        except Exception as exc:
            _log.error("Serial send error: %s", exc)
            self._fire_error(str(exc))

    @property
    def is_connected(self) -> bool:
        return self._connected

    # ── Android implementation ───────────────────────────────────────────────

    def _android_list_ports(self) -> List[Tuple[str, str]]:
        try:
            from usbserial4a import serial4a  # type: ignore[import]
            devices = serial4a.get_serial_port_list()
            return [(str(i), d.deviceName) for i, d in enumerate(devices)]
        except ImportError:
            _log.warning("usbserial4a not installed — USB serial unavailable")
            return []
        except Exception as exc:
            _log.error("Android list_ports error: %s", exc)
            return []

    def _android_connect(self, port: str, baudrate: int) -> bool:
        try:
            from usbserial4a import serial4a  # type: ignore[import]
            devices = serial4a.get_serial_port_list()
            idx = int(port)
            if idx >= len(devices):
                self._fire_error(f"USB device index {idx} out of range")
                return False
            device = devices[idx]
            ser = serial4a.get_serial_port(
                device.deviceName, baudrate, 8, "N", 1, timeout=2
            )
            if ser is None:
                self._fire_error("Could not open USB serial port (permission?)")
                return False
            self._port = ser
            self._connected = True
            self._start_reader()
            if self.on_state_changed:
                self.on_state_changed(True)
            return True
        except Exception as exc:
            _log.error("Android connect error: %s", exc)
            self._fire_error(str(exc))
            return False

    # ── Desktop implementation ───────────────────────────────────────────────

    def _desktop_list_ports(self) -> List[Tuple[str, str]]:
        try:
            import serial.tools.list_ports as lp
            return [(p.device, p.description or p.device) for p in lp.comports()]
        except ImportError:
            return []
        except Exception as exc:
            _log.error("Desktop list_ports error: %s", exc)
            return []

    def _desktop_connect(self, port: str, baudrate: int) -> bool:
        try:
            import serial
            ser = serial.Serial(port, baudrate=baudrate, timeout=2)
            self._port = ser
            self._connected = True
            self._start_reader()
            if self.on_state_changed:
                self.on_state_changed(True)
            return True
        except Exception as exc:
            _log.error("Desktop connect error: %s", exc)
            self._fire_error(str(exc))
            return False

    # ── reader thread ────────────────────────────────────────────────────────

    def _start_reader(self) -> None:
        self._stop_reader.clear()
        self._reader_thread = threading.Thread(
            target=self._reader_loop, daemon=True, name="SerialReader"
        )
        self._reader_thread.start()

    def _reader_loop(self) -> None:
        while not self._stop_reader.is_set():
            try:
                if self._port is None:
                    break
                data = self._port.read(256)
                if data and self.on_data_received:
                    self.on_data_received(data)
            except Exception as exc:
                if not self._stop_reader.is_set():
                    _log.error("Serial reader error: %s", exc)
                    self._fire_error(str(exc))
                break
        _log.debug("Serial reader thread exiting")

    def _fire_error(self, msg: str) -> None:
        self._connected = False
        if self.on_error:
            self.on_error(msg)


def request_usb_permission() -> None:
    """Android: request USB host permission for attached devices."""
    if not _ON_ANDROID:
        return
    try:
        from android.permissions import request_permissions, Permission  # type: ignore[import]
        # USB_PERMISSION is granted per-device via BroadcastReceiver;
        # no manifest permission string needed for USB host mode.
        # ACCESS_FINE_LOCATION may still be needed for some drivers.
        request_permissions([Permission.ACCESS_FINE_LOCATION])
    except Exception as exc:
        _log.warning("USB permission request failed: %s", exc)

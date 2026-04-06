"""hal/radio_controller.py — SA818 AT command controller over SerialManager.

Implements the SA818 / DigiRig serial protocol on top of our cross-platform
SerialManager (usbserial4a on Android, pyserial on desktop).

Unlike the desktop SA818Client (which owns a serial.Serial directly), this
class is *injected* with an already-opened SerialManager so that the same
USB serial connection is shared between radio control and the response reader
thread.

Architecture
────────────
  SerialManager.on_data_received  →  _ingest(data)  →  _rx_buf
  _send_command()  writes AT cmd  →  waits on threading.Event  →  returns response

SA818 command set used
──────────────────────
  AT+DMOCONNECT\r\n          version / ping (→ +DMOCONNECT:0)
  AT+DMOSETGROUP=…\r\n       set radio params (→ +DMOSETGROUP:0)
  AT+DMOSETVOLUME=N\r\n      set volume 1-8
  AT+SETFILTER=x,x,x\r\n     audio filters
  AT+SETTAIL=x\r\n            squelch tail
"""

from __future__ import annotations

import logging
import threading
from typing import Callable, Optional

_log = logging.getLogger(__name__)

# SA818 response terminators
_EOL = b"\r\n"
_CMD_TIMEOUT = 3.0   # seconds

# ── SA818 encoding helpers (mirrors app.engine.sa818_client) ─────────────────

_CTCSS = (
    "None",
    "67.0","71.9","74.4","77.0","79.7","82.5","85.4","88.5","91.5","94.8",
    "97.4","100.0","103.5","107.2","110.9","114.8","118.8","123.0","127.3","131.8",
    "136.5","141.3","146.2","151.4","156.7","162.2","167.9","173.8","179.9","186.2",
    "192.8","203.5","210.7","218.1","225.7","233.6","241.8","250.3",
)

def _encode_ctcss(value: str) -> str:
    if value.startswith("D"):
        return value          # DCS passthrough
    val = value.strip()
    if val in ("None", "0", "", "0.0"):
        return "0000"
    try:
        idx = list(_CTCSS).index(val)
        return f"{idx:04d}"
    except ValueError:
        return "0000"


def _encode_dcs(value: str) -> str:
    """Return DCS code string for SA818, e.g. 'D023N'."""
    v = value.strip()
    if v.startswith("D") and len(v) >= 4:
        return v
    return "0000"


def _encode_tones(tx_tone: str, rx_tone: str) -> tuple[str, str]:
    """Encode CTCSS/DCS tones into SA818 format strings."""
    def _enc(t: str) -> str:
        t = t.strip()
        if t.startswith("D"):
            return _encode_dcs(t)
        return _encode_ctcss(t)
    return _enc(tx_tone), _enc(rx_tone)


def _validate_frequency(freq: float) -> None:
    if not (136.0 <= freq <= 174.0 or 400.0 <= freq <= 480.0):
        raise ValueError(f"Frequency {freq} MHz out of SA818 range")


# ── RadioController ──────────────────────────────────────────────────────────

class RadioController:
    """SA818 AT command interface over SerialManager.

    Usage::

        rc = RadioController()
        rc.attach(serial_manager)   # call after serial_manager.connect()
        version = rc.version()      # → "+DMOCONNECT:0\\r\\n"
        rc.set_radio(...)
        rc.detach()
    """

    def __init__(self) -> None:
        self._serial_mgr = None
        self._rx_buf     = bytearray()
        self._resp_event = threading.Event()
        self._resp_lock  = threading.Lock()
        self._last_resp: Optional[str] = None
        self._io_lock    = threading.Lock()

        # Public callbacks
        self.on_response: Optional[Callable[[str], None]] = None
        self.on_error:    Optional[Callable[[str], None]] = None

    # ── wiring ───────────────────────────────────────────────────────────────

    def attach(self, serial_mgr) -> None:
        """Hook into a SerialManager that is already connected."""
        self._serial_mgr = serial_mgr
        self._prev_on_data = serial_mgr.on_data_received
        serial_mgr.on_data_received = self._ingest

    def detach(self) -> None:
        """Restore the previous on_data_received callback."""
        if self._serial_mgr and hasattr(self, "_prev_on_data"):
            self._serial_mgr.on_data_received = self._prev_on_data
        self._serial_mgr = None

    @property
    def is_attached(self) -> bool:
        return self._serial_mgr is not None and self._serial_mgr.is_connected

    # ── public command API ───────────────────────────────────────────────────

    def version(self) -> str:
        """Send AT+DMOCONNECT and return the response string."""
        return self._send_command("AT+DMOCONNECT")

    def set_radio(
        self,
        frequency: float,
        offset: float = 0.0,
        tx_tone: str = "None",
        rx_tone: str = "None",
        squelch: int = 4,
        bandwidth: str = "Wide",
    ) -> str:
        """Program SA818 radio parameters.

        bandwidth: "Wide" → 0, "Narrow" → 1
        """
        _validate_frequency(frequency)
        bw_code = "0" if bandwidth.lower().startswith("w") else "1"
        tx_enc, rx_enc = _encode_tones(tx_tone, rx_tone)

        # SA818 set-group command format:
        # AT+DMOSETGROUP=BW,TxF,RxF,Tx_CTCSS,Squelch,Rx_CTCSS
        tx_f = f"{frequency + offset:.4f}"
        rx_f = f"{frequency:.4f}"
        cmd = (
            f"AT+DMOSETGROUP={bw_code},"
            f"{tx_f},{rx_f},"
            f"{tx_enc},{squelch},{rx_enc}"
        )
        return self._send_command(cmd)

    def set_volume(self, level: int) -> str:
        """Set audio volume 1–8."""
        level = max(1, min(8, int(level)))
        return self._send_command(f"AT+DMOSETVOLUME={level}")

    def set_filters(
        self,
        disable_emphasis: bool = False,
        disable_highpass: bool = False,
        disable_lowpass: bool = False,
    ) -> str:
        """Configure SA818 audio filters (0=enabled, 1=disabled)."""
        e = "1" if disable_emphasis else "0"
        h = "1" if disable_highpass else "0"
        lo = "1" if disable_lowpass else "0"
        return self._send_command(f"AT+SETFILTER={e},{h},{lo}")

    def set_tail(self, open_tail: bool) -> str:
        """Enable/disable squelch tail tone (1=enabled, 0=disabled)."""
        return self._send_command(f"AT+SETTAIL={'1' if open_tail else '0'}")

    def raw_command(self, cmd: str) -> str:
        """Send an arbitrary AT command string and return the response."""
        return self._send_command(cmd)

    # ── internal ─────────────────────────────────────────────────────────────

    def _send_command(self, cmd: str) -> str:
        if self._serial_mgr is None or not self._serial_mgr.is_connected:
            raise RuntimeError("RadioController: serial not connected")
        with self._io_lock:
            self._last_resp = None
            self._resp_event.clear()
            raw = (cmd + "\r\n").encode("ascii")
            _log.debug("SA818 TX: %r", raw)
            self._serial_mgr.send(raw)
            # Wait for response (set by _ingest when a complete line arrives)
            got = self._resp_event.wait(timeout=_CMD_TIMEOUT)
            if not got:
                raise TimeoutError(f"SA818 no response to: {cmd!r}")
            resp = self._last_resp or ""
            _log.debug("SA818 RX: %r", resp)
            return resp

    def _ingest(self, data: bytes) -> None:
        """Called by SerialManager.on_data_received with raw bytes."""
        self._rx_buf.extend(data)
        # Emit complete lines
        while _EOL in self._rx_buf:
            idx = self._rx_buf.index(_EOL)
            line = self._rx_buf[:idx].decode("ascii", errors="replace").strip()
            self._rx_buf = self._rx_buf[idx + len(_EOL):]
            if not line:
                continue
            _log.debug("SA818 line: %r", line)
            with self._resp_lock:
                self._last_resp = line
            self._resp_event.set()
            if self.on_response:
                self.on_response(line)

    def _fire_error(self, msg: str) -> None:
        _log.error("RadioController error: %s", msg)
        if self.on_error:
            self.on_error(msg)


# ── Async runner (non-blocking helper for UI) ────────────────────────────────

import threading as _threading


class RadioControllerAsync:
    """Runs RadioController commands in a daemon thread so the Kivy UI
    never blocks.  Results are delivered via callbacks on the caller's thread
    (use Clock.schedule_once in Kivy callbacks)."""

    def __init__(self, controller: RadioController) -> None:
        self._ctrl = controller

    def version_async(
        self,
        on_result: Callable[[str], None],
        on_error: Optional[Callable[[str], None]] = None,
    ) -> None:
        self._run(self._ctrl.version, on_result, on_error)

    def set_radio_async(
        self,
        on_result: Callable[[str], None],
        on_error: Optional[Callable[[str], None]] = None,
        **kwargs,
    ) -> None:
        self._run(lambda: self._ctrl.set_radio(**kwargs), on_result, on_error)

    def raw_command_async(
        self,
        cmd: str,
        on_result: Callable[[str], None],
        on_error: Optional[Callable[[str], None]] = None,
    ) -> None:
        self._run(lambda: self._ctrl.raw_command(cmd), on_result, on_error)

    def _run(self, fn, on_result, on_error):
        def _worker():
            try:
                result = fn()
                on_result(result)
            except Exception as exc:
                _log.error("RadioControllerAsync error: %s", exc)
                if on_error:
                    on_error(str(exc))
        t = _threading.Thread(target=_worker, daemon=True)
        t.start()

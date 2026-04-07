#!/usr/bin/env python3
"""HamHatApp — main application window.

Architecture:
  - One tk.Tk root window with 3 active tab pages.
  - Engine components run in daemon worker threads; they NEVER touch Tkinter.
  - Worker threads push events into a thread.Queue; the main thread drains
    it every 40 ms via after() and dispatches to tab widgets.
  - All action methods are called by tab widgets on the main thread; they
    capture the needed state as plain Python values, then hand off to engine.
"""

from __future__ import annotations

import json
import logging
import os
import queue
import re
import subprocess
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import tkinter as tk
from tkinter import messagebox, ttk
try:
    import sv_ttk as _sv_ttk
except ImportError:
    _sv_ttk = None  # type: ignore[assignment]

from .app_state import AppState
from .engine.display_config import DisplayConfig
from .engine.aprs_engine import AprsEngine, _TxSnapshot
from .engine.aprs_modem import (
    build_aprs_message_payload,
    build_aprs_position_payload,
    write_aprs_wav,
    write_test_tone_wav,
)
from .engine.audio_router import AudioRouter
from .engine.audio_tools import list_input_devices, list_output_devices
from .engine.comms_mgr import CommsManager
from .engine.mesh_mgr import MeshManager, MESH_PREFIX
from .engine.models import (
    AppProfile,
    AprsConfig,
    AudioConfig,
    ChatMessage,
    DecodedPacket,
    MeshConfig,
    MSG_ID_COUNTER,
    PttConfig,
    RadioConfig,
    ReliableConfig,
)
from .engine.pakt import (
    PaktCapabilities,
    PaktConfigEvent,
    PaktConnectionEvent,
    PaktDeviceInfoEvent,
    PaktScanResult,
    PaktTelemetryEvent,
    PaktTxQueuedEvent,
    PaktTxResultEvent,
)
from .engine.profile import ProfileManager
from .engine.radio_ctrl import RadioController
from .engine.sa818_client import SA818Error
from .ui.comms_tab import CommsTab
from .ui.main_tab import MainTab
from .ui.mesh_tab import MeshTab
from .ui.setup_tab import SetupTab

_log = logging.getLogger(__name__)

_VERSION_FILE = Path(__file__).parent.parent / "VERSION"


def _read_version() -> str:
    try:
        return _VERSION_FILE.read_text(encoding="utf-8").strip()
    except Exception:
        return "dev"


# ---------------------------------------------------------------------------
# Thread-safe event types (pushed from worker threads, consumed on main thread)
# ---------------------------------------------------------------------------

@dataclass
class _LogEvt:         msg: str
@dataclass
class _AprsLogEvt:     msg: str
@dataclass
class _ErrorEvt:       title: str; msg: str
@dataclass
class _ConnectEvt:     port: str
@dataclass
class _DisconnectEvt:  pass
@dataclass
class _PacketEvt:      pkt: "DecodedPacket"
@dataclass
class _AudioPairEvt:   out_idx: int; out_name: str; in_idx: int; in_name: str
@dataclass
class _InputLevelEvt:  level: float
@dataclass
class _OutputLevelEvt: level: float
@dataclass
class _WaterfallEvt:   mono: object; rate: int
@dataclass
class _RxClipEvt:      pct: float
@dataclass
class _HeardEvt:       call: str
@dataclass
class _ChatMsgEvt:     msg: "ChatMessage"
@dataclass
class _ContactsEvt:    pass
@dataclass
class _StatusEvt:      text: str
@dataclass
class _PaktScanEvt:       devices: list[PaktScanResult]
@dataclass
class _PaktConnEvt:       event: PaktConnectionEvent
@dataclass
class _PaktCapsEvt:       caps: PaktCapabilities
@dataclass
class _PaktInfoEvt:       info: PaktDeviceInfoEvent
@dataclass
class _PaktConfigEvt:     event: PaktConfigEvent
@dataclass
class _PaktTelemEvt:      event: PaktTelemetryEvent
@dataclass
class _PaktTxQueuedEvt:   event: PaktTxQueuedEvent
@dataclass
class _PaktTxEvt:         event: PaktTxResultEvent
@dataclass
class _PaktSysStatusEvt:  text: str  # backend status → both global bar and PAKT panel
@dataclass
class _SuggestRxOsLevelEvt: level: int
@dataclass
class _MeshLogEvt:          msg: str
@dataclass
class _MeshRouteUpdateEvt:  pass


class HamHatApp(tk.Tk):
    """Main application window — thin coordinator between engine and tabs."""

    POLL_MS = 40            # UI queue drain interval
    VIS_MS  = 120           # level visualiser update interval
    AUTOSAVE_MS = 30_000    # profile auto-save interval

    def __init__(self, app_dir: Path, display_cfg: Optional["DisplayConfig"] = None) -> None:
        super().__init__()
        self.state = AppState(app_dir)
        self._app_dir = app_dir
        self._user_data_dir = self.state.user_data_dir
        self._audio_dir = self.state.audio_dir
        self._display_cfg = display_cfg or DisplayConfig.default()

        self._version = _read_version()
        self.title(f"HAM HAT Control Center  ({self._version})")

        # Minimum window size.  On a 1280×720 RPi display the window is fixed
        # to that resolution, so clamp the minimum to avoid the window manager
        # enforcing a size larger than the screen.
        if self._display_cfg.geometry and "1280x720" in self._display_cfg.geometry:
            self.minsize(640, 480)
        else:
            self.minsize(860, 600)

        # Set the theme (sv_ttk is optional; falls back to default ttk theme)
        if _sv_ttk is not None:
            _sv_ttk.set_theme("dark")

        # Apply display configuration (scaling, geometry, fonts).
        # Must happen after sv_ttk theme is applied so Style overrides take effect.
        self._display_cfg.apply_to_root(self)

        # On Linux/RPi, warn if the user is not in required OS groups.
        self.after(500, self._check_linux_permissions)

        # Pass references from state to self for convenience
        self.radio = self.state.radio
        self.audio = self.state.audio
        self.aprs = self.state.aprs
        self.comms = self.state.comms
        self.pakt = self.state.pakt
        self.tiles = self.state.tiles
        self._prof = self.state.prof
        self._evq = self.state.evq
        self.port_var = self.state.port_var
        self.status_var = self.state.status_var
        self.frequency_var = self.state.frequency_var
        self.offset_var = self.state.offset_var
        self.squelch_var = self.state.squelch_var
        self.bandwidth_var = self.state.bandwidth_var
        self.audio_out_var = self.state.audio_out_var
        self.audio_in_var = self.state.audio_in_var
        self.auto_audio_var = self.state.auto_audio_var
        self.ptt_enabled_var = self.state.ptt_enabled_var
        self.ptt_line_var = self.state.ptt_line_var
        self.ptt_active_high_var = self.state.ptt_active_high_var
        self.ptt_pre_ms_var = self.state.ptt_pre_ms_var
        self.ptt_post_ms_var = self.state.ptt_post_ms_var
        self.aprs_source_var = self.state.aprs_source_var
        self.aprs_dest_var = self.state.aprs_dest_var
        self.aprs_path_var = self.state.aprs_path_var
        self.aprs_tx_gain_var = self.state.aprs_tx_gain_var
        self.aprs_preamble_var = self.state.aprs_preamble_var
        self.aprs_repeats_var = self.state.aprs_repeats_var
        self.aprs_reinit_var = self.state.aprs_reinit_var
        self.aprs_symbol_table_var = self.state.aprs_symbol_table_var
        self.aprs_symbol_var = self.state.aprs_symbol_var
        self.aprs_msg_to_var = self.state.aprs_msg_to_var
        self.aprs_msg_text_var = self.state.aprs_msg_text_var
        self.aprs_msg_id_var = self.state.aprs_msg_id_var
        self.aprs_reliable_var = self.state.aprs_reliable_var
        self.aprs_ack_timeout_var = self.state.aprs_ack_timeout_var
        self.aprs_ack_retries_var = self.state.aprs_ack_retries_var
        self.aprs_auto_ack_var = self.state.aprs_auto_ack_var
        self.aprs_lat_var = self.state.aprs_lat_var
        self.aprs_lon_var = self.state.aprs_lon_var
        self.aprs_comment_var = self.state.aprs_comment_var
        self.aprs_rx_dur_var = self.state.aprs_rx_dur_var
        self.aprs_rx_chunk_var = self.state.aprs_rx_chunk_var
        self.aprs_rx_trim_var = self.state.aprs_rx_trim_var
        self.rx_clip_var = self.state.rx_clip_var
        self.aprs_rx_level_var = self.state.aprs_rx_level_var
        self.aprs_rx_os_level_var = self.state.aprs_rx_os_level_var
        self.aprs_rx_auto_var = self.state.aprs_rx_auto_var
        self.hardware_mode_var = self.state.hardware_mode_var
        self.digirig_port_var  = self.state.digirig_port_var
        self.pakt_device_var = self.state.pakt_device_var
        self.pakt_address_var = self.state.pakt_address_var
        self.pakt_callsign_var = self.state.pakt_callsign_var
        self.pakt_ssid_var = self.state.pakt_ssid_var
        self.pakt_capabilities_var = self.state.pakt_capabilities_var
        self.pakt_status_var = self.state.pakt_status_var
        self.pakt_last_config_var = self.state.pakt_last_config_var
        self.pakt_last_tx_result_var = self.state.pakt_last_tx_result_var

        # --- Mesh ---
        self.mesh = self.state.mesh
        self.mesh_enabled_var        = self.state.mesh_enabled_var
        self.mesh_node_role_var      = self.state.mesh_node_role_var
        self.mesh_default_ttl_var    = self.state.mesh_default_ttl_var
        self.mesh_rate_limit_ppm_var = self.state.mesh_rate_limit_ppm_var
        self.mesh_hello_enabled_var  = self.state.mesh_hello_enabled_var
        self.mesh_route_expiry_var   = self.state.mesh_route_expiry_var
        # Wire local_call_provider so mesh manager always sees current callsign
        self.mesh._local_call = lambda: self.aprs_source_var.get().upper().strip()

        # --- Build UI ---
        self._build_ui()

        # --- Wire engine callbacks → queue ---
        self._wire_callbacks()

        # --- Wire comms manager callbacks ---
        self._wire_comms()

        # --- Load profile (populates tabs) ---
        self._load_and_apply_profile()

        # --- Start periodic jobs ---
        self.after(self.POLL_MS, self._drain_queue)
        self.after(self.VIS_MS,  self._vis_tick)
        self.after(self.AUTOSAVE_MS, self._autosave)
        self.after(5000, self._mesh_tick)
        self.after(30_000, self._pakt_tx_timeout_tick)

        # --- Window close ---
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # --- Status bar startup ---
        self._set_status("Ready. Select serial port and click Connect.")

        # --- Auto-find audio and auto-connect ---
        self.after(200, self._startup_auto_tasks)

    # -----------------------------------------------------------------------
    # Display configuration (public — read by tab widgets)
    # -----------------------------------------------------------------------

    @property
    def display_cfg(self) -> "DisplayConfig":
        """Return the active DisplayConfig for this session.

        Tab widgets read this to get platform-appropriate heights, font names,
        and padding values instead of hardcoding desktop-sized defaults.
        """
        return self._display_cfg

    # -----------------------------------------------------------------------
    # UI construction
    # -----------------------------------------------------------------------

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)

        self._notebook = ttk.Notebook(self)
        self._notebook.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        self._main_tab  = MainTab(self._notebook, self)
        self._comms_tab = CommsTab(self._notebook, self)
        self._setup_tab = SetupTab(self._notebook, self)
        self._mesh_tab  = MeshTab(self._notebook, self)

        self._notebook.add(self._main_tab,  text="  Control  ")
        self._notebook.add(self._comms_tab, text="  APRS Comms  ")
        self._notebook.add(self._setup_tab, text="  Setup  ")
        self._notebook.add(self._mesh_tab,  text="  Mesh (Test)  ")

        # Auto-start RX monitor when APRS Comms tab is selected (if Always-on is enabled)
        self._notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # Status bar
        self._status_var = tk.StringVar(value="")
        sb = ttk.Frame(self, relief="sunken")
        sb.grid(row=1, column=0, sticky="ew")
        sb.columnconfigure(0, weight=1)

        self._status_lbl = ttk.Label(sb, textvariable=self._status_var,
                                      anchor="w", padding=(6, 2))
        self._status_lbl.grid(row=0, column=0, sticky="ew")

        self._conn_lbl = ttk.Label(sb, text="⚫ Disconnected",
                                    foreground="#e07070", padding=(6, 2))
        self._conn_lbl.grid(row=0, column=1, sticky="e")

        self._rx_lbl = ttk.Label(sb, text="RX: —", padding=(4, 2))
        self._rx_lbl.grid(row=0, column=2, sticky="e")

        self._tx_lbl = ttk.Label(sb, text="TX: —", padding=(4, 2))
        self._tx_lbl.grid(row=0, column=3, sticky="e", padx=(0, 6))

    # -----------------------------------------------------------------------
    # Linux / RPi permission checks
    # -----------------------------------------------------------------------

    def _check_linux_permissions(self) -> None:
        """On Linux/RPi, warn if the user is missing required OS group memberships.

        Called 500 ms after startup (via after()) so the window is visible first.

        Common groups checked:
          - dialout : usually needed for serial port access (uConsole_HAT, DigiRig)
          - bluetooth : often needed for BLE access (PAKT), though some
            systems allow BLE via polkit rules or root instead

        On non-Linux platforms this is a no-op.
        """
        import platform as _plat
        if _plat.system().lower() != "linux":
            return

        import grp
        try:
            username = os.environ.get("USER") or os.environ.get("LOGNAME") or ""
            if not username:
                import pwd
                username = pwd.getpwuid(os.getuid()).pw_name
        except Exception:
            return

        missing: list[str] = []
        for group_name in ("dialout", "bluetooth"):
            try:
                members = grp.getgrnam(group_name).gr_mem
                # Also check if user's primary group IS dialout/bluetooth
                gid = grp.getgrnam(group_name).gr_gid
                try:
                    import pwd
                    primary_gid = pwd.getpwnam(username).pw_gid
                except Exception:
                    primary_gid = -1
                if username not in members and primary_gid != gid:
                    missing.append(group_name)
            except KeyError:
                # Group doesn't exist on this system — skip
                pass
            except Exception:
                pass

        if missing:
            lines = [
                "Your user is missing one or more common Linux hardware-access groups:\n"
            ]
            serial_blocked = False
            for g in missing:
                if g == "dialout":
                    serial_blocked = True
                    lines.append(f"  • dialout — needed for serial port (uConsole_HAT, DigiRig)")
                    lines.append(f"    Fix: sudo usermod -aG dialout $USER")
                elif g == "bluetooth":
                    lines.append(f"  • bluetooth — commonly needed for BLE (PAKT TNC)")
                    lines.append(f"    Fix: sudo usermod -aG bluetooth $USER")
            lines.append("")
            if "bluetooth" in missing:
                lines.append("Note: BLE may still work on some systems via polkit or root access.")
            lines.append("You must log out and back in for group changes to take effect.")
            if serial_blocked:
                lines.append("Serial hardware will not work until dialout access is fixed.")
            else:
                lines.append("Hardware access may fail until group or equivalent OS permissions are configured.")
            messagebox.showwarning(
                "Linux Permission Warning",
                "\n".join(lines),
                parent=self,
            )

    # -----------------------------------------------------------------------
    # Callback wiring
    # -----------------------------------------------------------------------

    def _wire_callbacks(self) -> None:
        def _post(evt): self._evq.put_nowait(evt)

        self.radio.set_on_connect(lambda port: _post(_ConnectEvt(port)))
        self.radio.set_on_disconnect(lambda: _post(_DisconnectEvt()))

        self.audio.set_log_cb(lambda msg: _post(_LogEvt(msg)))

        self.aprs.on_log(lambda msg: _post(_LogEvt(msg)))
        self.aprs.on_aprs_log(lambda msg: _post(_AprsLogEvt(msg)))
        self.aprs.on_error(lambda t, m: _post(_ErrorEvt(t, m)))
        self.aprs.on_packet(lambda pkt: _post(_PacketEvt(pkt)))
        self.aprs.on_input_level(lambda lv: _post(_InputLevelEvt(lv)))
        self.aprs.on_output_level(lambda lv: _post(_OutputLevelEvt(lv)))
        self.aprs.on_waterfall(lambda mono, rate: _post(_WaterfallEvt(mono, rate)))
        self.aprs.on_rx_clip(lambda pct: _post(_RxClipEvt(pct)))

        self.pakt.set_config_cache_path(self._user_data_dir / "profiles" / "pakt_config_cache.json")
        self.pakt._on_scan_results = lambda items: _post(_PaktScanEvt(items))
        self.pakt._on_connection = lambda event: _post(_PaktConnEvt(event))
        self.pakt._on_status = lambda event: _post(_PaktSysStatusEvt(event.text))
        self.pakt._on_capabilities = lambda caps: _post(_PaktCapsEvt(caps))
        self.pakt._on_device_info = lambda info: _post(_PaktInfoEvt(info))
        self.pakt._on_config = lambda event: _post(_PaktConfigEvt(event))
        self.pakt._on_telemetry = lambda event: _post(_PaktTelemEvt(event))
        self.pakt._on_tx_queued = lambda event: _post(_PaktTxQueuedEvt(event))
        self.pakt._on_tx_result = lambda event: _post(_PaktTxEvt(event))

    def _wire_comms(self) -> None:
        def _post(evt): self._evq.put_nowait(evt)

        self.comms.on_contacts_changed(lambda: _post(_ContactsEvt()))
        self.comms.on_message_added(lambda msg: _post(_ChatMsgEvt(msg)))
        self.comms.on_heard_changed(lambda: self.after_idle(self._comms_tab.refresh_heard))

    # -----------------------------------------------------------------------
    # Queue drain (runs on main thread every POLL_MS)
    # -----------------------------------------------------------------------

    def _drain_queue(self) -> None:
        limit = 80  # max events to process per tick
        for _ in range(limit):
            try:
                evt = self._evq.get_nowait()
            except queue.Empty:
                break
            self._dispatch(evt)
        self.after(self.POLL_MS, self._drain_queue)

    def _dispatch(self, evt) -> None:
        if isinstance(evt, _LogEvt):
            self._main_tab.append_log(evt.msg)

        elif isinstance(evt, _AprsLogEvt):
            self._comms_tab.append_log(evt.msg)
            self._main_tab.append_log(f"[APRS] {evt.msg}")

        elif isinstance(evt, _ErrorEvt):
            messagebox.showerror(evt.title, evt.msg, parent=self)

        elif isinstance(evt, _ConnectEvt):
            self._conn_lbl.configure(text=f"🟢 {evt.port}", foreground="#70c070")
            self._main_tab.on_connect(evt.port)
            self._set_status(f"Connected: {evt.port}")
            # Keep port_var in sync so manual reconnect after disconnect uses the right port
            self.port_var.set(evt.port)

        elif isinstance(evt, _DisconnectEvt):
            self._conn_lbl.configure(text="⚫ Disconnected", foreground="#e07070")
            self._main_tab.on_disconnect()
            self._set_status("Disconnected")

        elif isinstance(evt, _PacketEvt):
            self._handle_packet(evt.pkt)

        elif isinstance(evt, _AudioPairEvt):
            self._main_tab.on_audio_pair(evt.out_idx, evt.out_name, evt.in_idx, evt.in_name)
            self._set_status(f"Audio: {evt.out_name} / {evt.in_name}")
            # Set OS levels immediately after device selection so both PCs have
            # consistent TX FM deviation (output → 100%) and RX capture level.
            self._apply_os_tx_level(100)
            self._apply_os_rx_level(self._current_os_rx_level)

        elif isinstance(evt, _InputLevelEvt):
            self._comms_tab.set_input_level(evt.level)
            pct = int(min(100, max(0, evt.level * 100.0)))
            self._rx_lbl.configure(text=f"RX: {pct:3d}%")

        elif isinstance(evt, _OutputLevelEvt):
            self._comms_tab.set_output_level(evt.level)

        elif isinstance(evt, _WaterfallEvt):
            self._comms_tab.push_waterfall(evt.mono, evt.rate)

        elif isinstance(evt, _RxClipEvt):
            self._comms_tab.set_rx_clip(evt.pct)

        elif isinstance(evt, _HeardEvt):
            self.comms.note_heard(evt.call)

        elif isinstance(evt, _ChatMsgEvt):
            self._comms_tab.on_message(evt.msg)

        elif isinstance(evt, _ContactsEvt):
            self._comms_tab.refresh_contacts()

        elif isinstance(evt, _StatusEvt):
            self._set_status(evt.text)

        elif isinstance(evt, _PaktScanEvt):
            pairs = [(item.name, item.address) for item in evt.devices]
            self._main_tab.set_pakt_scan_results(pairs)
            # set_pakt_scan_results handles device_var and address_var selection.

        elif isinstance(evt, _PaktConnEvt):
            self._main_tab.set_pakt_status(evt.event.message)
            self._main_tab.set_pakt_ble_state(evt.event.state)
            self.pakt_status_var.set(evt.event.message)
            if evt.event.address:
                self.pakt_address_var.set(evt.event.address)
            if evt.event.state == "CONNECTED":
                addr = evt.event.address or self.pakt_address_var.get().strip()
                self._conn_lbl.configure(text=f"🟢 PAKT {addr}", foreground="#70c070")
            elif evt.event.state in {"CONNECTING", "RECONNECTING"}:
                addr = evt.event.address or self.pakt_address_var.get().strip()
                suffix = f" {addr}" if addr else ""
                self._conn_lbl.configure(text=f"🟡 PAKT{suffix}", foreground="#d6b34c")
            elif evt.event.state == "SCANNING":
                self._conn_lbl.configure(text="🔵 PAKT Scanning…", foreground="#6ab0e0")
            elif evt.event.state in {"IDLE", "ERROR"}:
                self._conn_lbl.configure(text="⚫ Disconnected", foreground="#e07070")

        elif isinstance(evt, _PaktCapsEvt):
            summary = evt.caps.summary()
            self._main_tab.set_pakt_capabilities(summary)
            self.pakt_capabilities_var.set(summary)

        elif isinstance(evt, _PaktInfoEvt):
            if evt.info.model:
                self._main_tab.append_log(
                    f"[PAKT] {evt.info.manufacturer} {evt.info.model} fw={evt.info.firmware_rev}"
                )

        elif isinstance(evt, _PaktConfigEvt):
            self.pakt_last_config_var.set(evt.event.text)
            self._main_tab.set_pakt_config_text(evt.event.text)
            if evt.event.source == "read":
                self._apply_pakt_config_to_vars(evt.event.text)

        elif isinstance(evt, _PaktTelemEvt):
            # Only push high-signal events to the status panel to avoid thrashing.
            # All telemetry is written to the log with a structured format.
            if evt.event.name in {"device_status", "tx_result"}:
                self._main_tab.set_pakt_status(f"{evt.event.name}: {evt.event.text}")
            self._main_tab.append_log(f"[PAKT telem/{evt.event.name}] {evt.event.text}")

        elif isinstance(evt, _PaktTxQueuedEvt):
            self.comms.add_message(
                ChatMessage(
                    direction="TX",
                    src=self.pakt_callsign_var.get().strip().upper() or self.aprs_source_var.get().strip().upper(),
                    dst=evt.event.dest,
                    text=evt.event.text,
                    msg_id=evt.event.local_id,
                    thread_key=evt.event.dest,
                    backend="PAKT",
                )
            )

        elif isinstance(evt, _PaktTxEvt):
            self.pakt_last_tx_result_var.set(evt.event.raw_json)
            self._main_tab.set_pakt_status(f"TX {evt.event.msg_id}: {evt.event.status}")
            self._main_tab.append_log(
                f"[PAKT tx/{evt.event.msg_id}] status={evt.event.status}"
            )
            thread_key = self.comms.mark_pakt_tx_result(evt.event.msg_id, evt.event.status)
            if thread_key:
                self._comms_tab.on_message_updated(thread_key)

        elif isinstance(evt, _PaktSysStatusEvt):
            self._set_status(evt.text)
            self._main_tab.set_pakt_status(evt.text)

        elif isinstance(evt, _SuggestRxOsLevelEvt):
            self.aprs_rx_os_level_var.set(evt.level)

        elif isinstance(evt, _MeshLogEvt):
            if hasattr(self, "_mesh_tab"):
                self._mesh_tab.append_log(evt.msg)

        elif isinstance(evt, _MeshRouteUpdateEvt):
            if hasattr(self, "_mesh_tab"):
                self._mesh_tab.refresh_routes()

    # -----------------------------------------------------------------------
    # Visualiser tick (TX/RX level bars, updated on main thread)
    # -----------------------------------------------------------------------

    def _vis_tick(self) -> None:
        if self.audio.tx_active:
            pct = int(min(100, self.audio.tx_level_hold * 100.0))
            self._tx_lbl.configure(text=f"TX: {pct:3d}%")
        else:
            self._tx_lbl.configure(text="TX: —")
        rx_active = self.aprs.rx_running
        if not rx_active:
            self._rx_lbl.configure(text="RX: —")
            self.aprs_rx_level_var.set("—")
        self._comms_tab.set_monitor_active(rx_active)
        self.after(self.VIS_MS, self._vis_tick)

    # -----------------------------------------------------------------------
    # Startup tasks (deferred by 200ms so window is visible first)
    # -----------------------------------------------------------------------

    def _on_tab_changed(self, _e) -> None:
        """Auto-start RX monitor when APRS Comms tab is selected (if Always-on is set)."""
        try:
            selected = self._notebook.select()
            if selected == str(self._comms_tab):
                if self.aprs_rx_auto_var.get() and not self.aprs.rx_running:
                    self.start_rx_monitor()
        except Exception:
            pass

    def _startup_auto_tasks(self) -> None:
        # Populate serial port list (FR-02: app shall list available serial ports)
        self.refresh_ports()
        # Refresh audio device lists for all modes so comboboxes are populated
        self._main_tab.refresh_audio_devices()
        if self._hw_mode() == "PAKT":
            self.pakt_scan()
            return
        # Try auto-select USB audio
        self._auto_find_audio_background()

    def _auto_find_audio_background(self) -> None:
        p = self._get_current_profile()
        out_hint = p.output_device_name
        in_hint  = p.input_device_name
        if not p.auto_audio_select:
            return

        def worker():
            try:
                result = self.audio.auto_select_usb_pair(out_hint, in_hint)
                if result:
                    out_idx, in_idx = result
                    outs = dict(list_output_devices())
                    ins  = dict(list_input_devices())
                    out_name = outs.get(out_idx, f"Device {out_idx}")
                    in_name  = ins.get(in_idx, f"Device {in_idx}")
                    self._evq.put_nowait(_AudioPairEvt(out_idx, out_name, in_idx, in_name))
            except Exception as exc:
                _log.debug("Auto-audio select error: %s", exc)

        threading.Thread(target=worker, daemon=True).start()

    # -----------------------------------------------------------------------
    # Hardware mode helper
    # -----------------------------------------------------------------------

    def _hw_mode(self) -> str:
        """Return current hardware mode."""
        hw = self.hardware_mode_var.get()
        return "SA818" if hw == "uConsole_HAT" else hw

    def on_hw_mode_changed(self) -> None:
        """Reset the footer connection indicator when the hardware mode selector changes."""
        self._conn_lbl.configure(text="⚫ Disconnected", foreground="#e07070")

    # -----------------------------------------------------------------------
    # Connection actions
    # -----------------------------------------------------------------------

    def connect(self, port: str = "") -> None:
        """Connect to SA818 on given port (called from main thread)."""
        if self._hw_mode() == "PAKT":
            self.pakt_connect_selected()
            return
        if self._hw_mode() == "DigiRig":
            self._set_status("DigiRig mode: no uConsole_HAT connection needed. Set PTT port and select audio device.")
            return

        port = (port or self.port_var.get()).strip()
        if not port:
            self._set_status("Select a COM port first")
            return

        def worker():
            try:
                self.radio.connect(port)
                # Apply radio settings from profile
                self.after_idle(self._apply_radio_after_connect)
            except SA818Error as exc:
                self._evq.put_nowait(_ErrorEvt("Connection Failed", str(exc)))
            except Exception as exc:
                self._evq.put_nowait(_ErrorEvt("Connection Error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def _apply_radio_after_connect(self) -> None:
        p = self._get_current_profile()
        self._apply_radio_config(p)

    def disconnect(self) -> None:
        if self._hw_mode() == "PAKT":
            self.pakt_disconnect()
            return
        if self._hw_mode() == "DigiRig":
            self._set_status("DigiRig mode: nothing to disconnect.")
            return

        def worker():
            try:
                self.aprs.stop_rx_monitor()
                self.radio.disconnect()
            except Exception as exc:
                _log.warning("Disconnect error: %s", exc)

        threading.Thread(target=worker, daemon=True).start()

    def scan_ports(self) -> list[str]:
        """Return list of available serial port names (called on main thread).

        Port name format differs by platform (CP-100):
          Windows     : "COM3", "COM8", …
          macOS       : "/dev/cu.usbserial-…", "/dev/tty.usbserial-…"
          Linux / RPi : "/dev/ttyUSB0", "/dev/ttyACM0", …

        On Linux/RPi the user must be in the 'dialout' group (or equivalent)
        to open serial ports: `sudo usermod -aG dialout $USER` then re-login.
        """
        try:
            import serial.tools.list_ports
            return [p.device for p in serial.tools.list_ports.comports()]
        except Exception:
            return []

    def auto_identify_and_connect(self) -> None:
        """Probe COM ports. SA818 mode: connect to first SA818. DigiRig mode: find non-SA818 port."""
        if self._hw_mode() == "PAKT":
            self.pakt_scan()
            return
        if self._hw_mode() == "DigiRig":
            def digirig_worker():
                """
                Identify the DigiRig PTT port even when both SA818 and DigiRig are connected.

                Strategy:
                  1. Collect all serial ports.
                  2. Probe each with AT+DMOCONNECT (short timeout).
                     - Responds with +DMOCONNECT:0 → it's the SA818 HAT → skip.
                     - No response / wrong reply → SA818-negative candidate.
                  3. Among SA818-negative candidates prefer ports whose USB description
                     contains "CP210x" / "Silicon Labs" (DigiRig uses CP2102).
                  4. Auto-select if exactly one candidate, otherwise log all choices.
                """
                try:
                    import serial.tools.list_ports
                    all_ports = list(serial.tools.list_ports.comports())
                except Exception:
                    all_ports = []

                if not all_ports:
                    self._evq.put_nowait(_StatusEvt("DigiRig auto-identify: no serial ports found."))
                    return

                from .engine.sa818_client import SA818Client as _SA818Client
                sa818_ports: list[str] = []
                non_sa818_ports: list[tuple[str, str]] = []   # (device, description)

                for port_info in all_ports:
                    device = port_info.device
                    desc = (port_info.description or "").strip()
                    ok, _ = _SA818Client.probe(device, timeout=0.6)
                    if ok:
                        sa818_ports.append(device)
                    else:
                        non_sa818_ports.append((device, desc))

                if sa818_ports:
                    self._evq.put_nowait(_LogEvt(f"DigiRig auto-identify: uConsole_HAT found on {', '.join(sa818_ports)} (skipped)"))

                if not non_sa818_ports:
                    self._evq.put_nowait(_StatusEvt("DigiRig auto-identify: no non-uConsole_HAT port found. Is DigiRig connected?"))
                    return

                # Prefer CP210x / Silicon Labs ports (DigiRig uses CP2102).
                # Description string format differs by platform (CP-100):
                #   Windows : "Silicon Labs CP210x USB to UART Bridge (COMn)"
                #   macOS   : "CP2102 USB to UART Bridge Controller"
                #   Linux   : "CP210x UART Bridge" or "CP2102 USB to UART Bridge"
                # The keywords "cp210" and "silicon labs" match across all platforms.
                cp210x_candidates = [
                    (dev, desc) for dev, desc in non_sa818_ports
                    if "cp210" in desc.lower() or "silicon labs" in desc.lower()
                ]
                candidates = cp210x_candidates if cp210x_candidates else non_sa818_ports

                if len(candidates) == 1:
                    suggested = candidates[0][0]
                    desc = candidates[0][1]
                    self.after_idle(lambda p=suggested: self.digirig_port_var.set(p))
                    self._evq.put_nowait(_StatusEvt(
                        f"DigiRig auto-identify: set PTT port to {suggested} ({desc})"
                    ))
                else:
                    names = ", ".join(f"{dev} ({desc})" for dev, desc in candidates)
                    self._evq.put_nowait(_StatusEvt(
                        f"DigiRig auto-identify: multiple candidates — {names}. Select manually."
                    ))

            threading.Thread(target=digirig_worker, daemon=True).start()
            return

        def worker():
            ports = self.scan_ports()
            if not ports:
                self._evq.put_nowait(_StatusEvt("No COM ports found"))
                return
            for port in ports:
                ok, detail = self.radio.probe_and_connect(port)
                if ok:
                    self._evq.put_nowait(_StatusEvt(f"Auto-connected: {port} ({detail})"))
                    self.after_idle(self._apply_radio_after_connect)
                    return
            self._evq.put_nowait(_StatusEvt("Auto-identify: no uConsole_HAT found on any port"))

        threading.Thread(target=worker, daemon=True).start()

    # -----------------------------------------------------------------------
    # Radio config actions
    # -----------------------------------------------------------------------

    def apply_radio(self) -> None:
        """Read radio params from main tab and apply to SA818."""
        if self._hw_mode() == "PAKT":
            self._set_status("Radio control not available in PAKT mode.")
            return
        if self._hw_mode() == "DigiRig":
            self._set_status("Radio control not available in DigiRig mode — program radio manually.")
            return
        if not self.radio.connected:
            self._set_status("Radio not connected")
            return
        p = self._collect_profile_snapshot()
        self._apply_radio_config(p)

    def _apply_radio_config(self, p: AppProfile) -> None:
        def worker():
            try:
                bw = 1 if p.bandwidth.lower().startswith("w") else 0
                ctcss_tx = p.ctcss_tx or None
                ctcss_rx = p.ctcss_rx or None
                dcs_tx   = p.dcs_tx or None
                dcs_rx   = p.dcs_rx or None
                cfg = RadioConfig(
                    frequency=p.frequency,
                    offset=p.offset,
                    bandwidth=bw,
                    squelch=p.squelch,
                    ctcss_tx=ctcss_tx,
                    ctcss_rx=ctcss_rx,
                    dcs_tx=dcs_tx,
                    dcs_rx=dcs_rx,
                )
                self.radio.apply_config(cfg)
                self.radio.set_filters(p.disable_emphasis, p.disable_highpass, p.disable_lowpass)
                self.radio.set_volume(p.volume)
                tx_freq = p.frequency + p.offset
                self._evq.put_nowait(_StatusEvt(
                    f"Radio applied: RX {p.frequency:.4f} MHz  TX {tx_freq:.4f} MHz  squelch={p.squelch}  vol={p.volume}"))
            except SA818Error as exc:
                self._evq.put_nowait(_ErrorEvt("Radio Error", str(exc)))
            except Exception as exc:
                self._evq.put_nowait(_ErrorEvt("Radio Error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def apply_filters(self, emphasis: bool, highpass: bool, lowpass: bool) -> None:
        if self._hw_mode() == "PAKT":
            self._set_status("Filter control not available in PAKT mode."); return
        if self._hw_mode() == "DigiRig":
            self._set_status("Filter control not available in DigiRig mode."); return
        if not self.radio.connected:
            self._set_status("Not connected"); return

        def worker():
            try:
                self.radio.set_filters(emphasis, highpass, lowpass)
                self._evq.put_nowait(_StatusEvt("Filters applied"))
            except Exception as exc:
                self._evq.put_nowait(_ErrorEvt("Filter Error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def set_volume(self, level: int) -> None:
        if self._hw_mode() == "PAKT":
            self._set_status("Volume control not available in PAKT mode."); return
        if self._hw_mode() == "DigiRig":
            self._set_status("Volume control not available in DigiRig mode."); return
        if not self.radio.connected:
            self._set_status("Not connected"); return

        def worker():
            try:
                self.radio.set_volume(max(1, min(8, level)))
                self._evq.put_nowait(_StatusEvt(f"Volume set to {level}"))
            except Exception as exc:
                self._evq.put_nowait(_ErrorEvt("Volume Error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def apply_tail(self, open_tail: bool) -> None:
        if self._hw_mode() == "PAKT":
            self._set_status("Squelch tail not available in PAKT mode."); return
        if self._hw_mode() == "DigiRig":
            self._set_status("Squelch tail not available in DigiRig mode."); return
        if not self.radio.connected:
            self._set_status("Not connected"); return

        def worker():
            try:
                self.radio.set_tail(open_tail)
                self._evq.put_nowait(_StatusEvt(f"Squelch tail: {'open' if open_tail else 'closed'}"))
            except Exception as exc:
                self._evq.put_nowait(_ErrorEvt("Tail Error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    # -----------------------------------------------------------------------
    # Audio device actions
    # -----------------------------------------------------------------------

    def refresh_audio_devices(self) -> None:
        """Called from MainTab to refresh device lists."""
        outs = self.audio.refresh_output_devices()
        ins  = self.audio.refresh_input_devices()
        self._main_tab.populate_audio_devices(outs, ins)

    def auto_find_audio_pair(self) -> None:
        self._auto_find_audio_background()

    def stop_audio(self) -> None:
        self.audio.stop_audio()
        self._set_status("Audio stopped")

    def set_output_device(self, idx: Optional[int], name: str) -> None:
        self._output_dev_idx  = idx
        self._output_dev_name = name

    def set_input_device(self, idx: Optional[int], name: str) -> None:
        self._input_dev_idx  = idx
        self._input_dev_name = name

    def _resolve_output_dev_fallback(self) -> int:
        """Return the best available output device index when none is explicitly selected.

        Preference order:
          1. First USB / external audio output (catches SA818 / DigiRig audio interface)
          2. Device 0 as a last resort
        """
        try:
            devs = list_output_devices()  # list of (idx, name)
            for idx, name in devs:
                if "usb" in name.lower():
                    _log.debug("_resolve_output_dev_fallback: selected USB device %s (%s)", idx, name)
                    return idx
        except Exception as exc:
            _log.debug("_resolve_output_dev_fallback: device scan error: %s", exc)
        return 0

    # -----------------------------------------------------------------------
    # APRS helper actions (read from tk vars; called by tab buttons)
    # -----------------------------------------------------------------------

    def apply_callsign_preset(self, src: str, dst: str) -> None:
        self.aprs_source_var.set(src)
        self.aprs_msg_to_var.set(dst)

    def send_aprs_message(self, to: str = "", text: str = "", reliable: bool = False) -> None:
        """Send direct APRS message. When called with no args reads from tab vars."""
        if not to:
            to = self.aprs_msg_to_var.get().strip().upper()
        if not text:
            text = self.aprs_msg_text_var.get().strip()
        if not to or not text:
            self._set_status("Enter To and Message text")
            return
        reliable = reliable or self.aprs_reliable_var.get()
        self._send_aprs_message_impl(to, text, reliable)

    def _send_aprs_message_impl(self, to: str, text: str, reliable: bool) -> None:
        if self._hw_mode() == "PAKT":
            self.pakt_send_tx_request(dest=to, text=text)
            return

        snap = self._make_tx_snapshot()
        if snap is None:
            self._set_status("Cannot TX: check connection / audio device")
            return

        chunks = self.comms.build_direct_chunks(text)
        p = self._get_current_profile()

        for i, chunk in enumerate(chunks):
            # Each chunk gets its own unique message ID so ACK tracking and
            # remote dedup work correctly for multi-part messages.
            msg_id = AprsEngine.new_message_id()
            payload = build_aprs_message_payload(to, chunk, msg_id)
            if reliable:
                self.aprs.send_reliable(
                    addressee=to, text=chunk, snap=snap,
                    message_id=msg_id,
                    timeout_s=p.aprs_ack_timeout,
                    retries=p.aprs_ack_retries,
                )
            else:
                self.aprs.send_payload(payload, snap)

            # Add to comms manager
            msg = ChatMessage(
                direction="TX", src=snap.source, dst=to,
                text=chunk, msg_id=msg_id,
                thread_key=to,
            )
            self.comms.add_message(msg)

    def send_direct_message(self, to: str, text: str, reliable: bool = False) -> None:
        """Alias used by CommsTab."""
        self._send_aprs_message_impl(to, text, reliable)

    def send_aprs_position(self) -> None:
        """Read lat/lon/comment from APRS tab vars and send position."""
        try:
            lat = float(self.aprs_lat_var.get())
            lon = float(self.aprs_lon_var.get())
        except ValueError:
            self._set_status("Invalid lat/lon")
            return
        comment = self.aprs_comment_var.get().strip()
        self.send_position(lat, lon, comment)

    def apply_os_rx_level(self) -> None:
        """Read OS mic level from APRS tab var and apply."""
        level = int(self.aprs_rx_os_level_var.get())
        self._apply_os_rx_level(level)

    def on_rx_auto_toggle(self) -> None:
        """Called when the 'Always-on RX Monitor' checkbox is toggled."""
        if self.aprs_rx_auto_var.get():
            self.start_rx_monitor()
        else:
            self.stop_rx_monitor()

    def rx_one_shot(self) -> None:
        """One-shot RX decode — alias for APRS tab button."""
        self.one_shot_rx()

    def aprs_log(self, msg: str) -> None:
        """Log a message to the APRS monitor (called from tab callbacks)."""
        self._evq.put_nowait(_AprsLogEvt(msg))

    def send_group_message(self, group: str, text: str) -> None:
        if self._hw_mode() == "PAKT":
            self._set_status("Group TX is not implemented for PAKT in this pass")
            return
        snap = self._make_tx_snapshot()
        if snap is None:
            self._set_status("Cannot TX: check connection / audio device")
            return
        chunks = self.comms.build_group_chunks(group, text)
        for i, wire_text in enumerate(chunks):
            msg_id = AprsEngine.new_message_id()
            payload = build_aprs_message_payload(
                group,
                wire_text, msg_id,
            )
            self.aprs.send_payload(payload, snap)
            msg = ChatMessage(
                direction="TX", src=snap.source, dst=group,
                text=text if len(chunks) == 1 else f"[{i+1}/{len(chunks)}] {text}",
                msg_id=msg_id,
                thread_key=f"GROUP:{group}",
            )
            self.comms.add_message(msg)

    def send_position(self, lat: float, lon: float, comment: str) -> None:
        if self._hw_mode() == "PAKT":
            self._set_status("Position TX is not implemented for PAKT in this pass")
            return
        snap = self._make_tx_snapshot()
        if snap is None:
            self._set_status("Cannot TX: check connection / audio device")
            return
        p = self._get_current_profile()
        payload = build_aprs_position_payload(
            lat, lon,
            symbol_table=p.aprs_symbol_table,
            symbol=p.aprs_symbol,
            comment=comment,
        )
        self.aprs.send_payload(payload, snap)
        self._set_status(f"Position TX: {lat:.4f}, {lon:.4f}")

    def send_intro(self, note: str) -> None:
        if self._hw_mode() == "PAKT":
            self._set_status("Intro TX is not implemented for PAKT in this pass")
            return
        snap = self._make_tx_snapshot()
        if snap is None:
            self._set_status("Cannot TX: check connection / audio device")
            return
        p = self._get_current_profile()
        payload = self.comms.build_intro_payload(
            snap.source, p.aprs_lat, p.aprs_lon, note)
        self.aprs.send_payload(payload, snap)
        self._set_status(f"Intro TX: {snap.source}")

    # -----------------------------------------------------------------------
    # APRS RX
    # -----------------------------------------------------------------------

    def start_rx_monitor(self) -> None:
        hw = self._hw_mode()
        if hw == "PAKT":
            self._set_status("PAKT uses BLE notifications instead of the audio RX monitor")
            return
        if hw != "DigiRig" and not self.radio.connected:
            self._set_status("Not connected"); return
        p = self._get_current_profile()
        bw = 1 if p.bandwidth.lower().startswith("w") else 0
        aprs_radio = RadioConfig(
            frequency=p.frequency, offset=0.0, bandwidth=bw,
            squelch=0, ctcss_tx=None, ctcss_rx=None, dcs_tx=None, dcs_rx=None)
        in_dev = getattr(self, "_input_dev_idx", None)
        self.aprs.start_rx_monitor(
            in_dev=in_dev,
            chunk_s=p.aprs_rx_chunk,
            trim_db=p.aprs_rx_trim_db,
            aprs_radio=aprs_radio,
            hw_mode=hw,
        )
        self._set_status("RX monitor started")
        # Ensure SA818 TX path is at full OS volume for maximum FM deviation,
        # then set the capture level to the profile's configured value.
        self._apply_os_tx_level(100)
        self._apply_os_rx_level(p.aprs_rx_os_level)

    def stop_rx_monitor(self) -> None:
        def worker():
            self.aprs.stop_rx_monitor()
            self._evq.put_nowait(_StatusEvt("RX monitor stopped"))
        threading.Thread(target=worker, daemon=True).start()

    def one_shot_rx(self) -> None:
        if self._hw_mode() == "PAKT":
            self._set_status("One-shot audio RX is not available in PAKT mode"); return
        if self._hw_mode() != "DigiRig" and not self.radio.connected:
            self._set_status("Not connected"); return
        p = self._get_current_profile()
        in_dev = getattr(self, "_input_dev_idx", None)
        self.aprs.one_shot_decode(in_dev, p.aprs_rx_duration, p.aprs_rx_trim_db)

    # -----------------------------------------------------------------------
    # Audio tools
    # -----------------------------------------------------------------------

    def play_test_tone(self, freq: float = 1200.0, duration: float = 2.0) -> None:
        if self.audio.tx_active:
            self._set_status("TX already in progress")
            return
        out_dev = getattr(self, "_output_dev_idx", None)
        if out_dev is None:
            out_dev = self._resolve_output_dev_fallback()
        ptt = self._make_ptt_config()
        if self._hw_mode() == "PAKT":
            # Audio routing test is still useful in PAKT mode; skip PTT keying.
            ptt = PttConfig(enabled=False)
        dr_port = self.digirig_port_var.get().strip() if self._hw_mode() == "DigiRig" else ""
        if self._hw_mode() == "SA818":
            try:
                port = str(self.radio.client.ser.port) if self.radio.connected and self.radio.client.ser else "(not connected)"
            except Exception:
                port = "(unknown)"
            self._set_status(
                f"Test tone queued: out_dev={out_dev}, PTT={ptt.line}, active_high={ptt.active_high}, uConsole_HAT port={port}"
            )
        self.aprs.play_test_tone(freq, duration, out_dev, ptt, ptt_serial_port=dr_port)
        if self._hw_mode() != "SA818":
            self._set_status(f"Test tone: {freq:.0f} Hz  {duration:.1f}s → device {out_dev}")

    def play_manual_aprs_packet(self, text: str) -> None:
        if self.audio.tx_active:
            self._set_status("TX already in progress")
            return
        if self._hw_mode() == "PAKT":
            self._set_status("Manual APRS audio generation is not applicable in PAKT mode")
            return
        snap = self._make_tx_snapshot()
        if snap is None:
            self._set_status("Cannot TX: check audio device")
            return
        def worker():
            try:
                wav_path = self._audio_dir / "manual_aprs.wav"
                self._audio_dir.mkdir(parents=True, exist_ok=True)
                write_aprs_wav(
                    wav_path,
                    source=snap.source,
                    destination=snap.destination,
                    path_via=snap.path,
                    message=text,
                    tx_gain=snap.gain,
                    preamble_flags=snap.preamble_flags,
                    trailing_flags=snap.trailing_flags,
                )
                # No PTT — dry run only
                no_ptt = PttConfig(enabled=False)
                self.audio.play_with_ptt_blocking(wav_path, snap.out_dev, no_ptt, None)
                self._evq.put_nowait(_StatusEvt("Manual APRS packet played (no PTT)"))
            except Exception as exc:
                self._evq.put_nowait(_ErrorEvt("Manual APRS Error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def tx_channel_sweep(self) -> None:
        """Run TX channel sweep to help find the correct audio routing."""
        if self.audio.tx_active:
            self._set_status("TX already in progress")
            return
        out_dev = getattr(self, "_output_dev_idx", None)
        if out_dev is None:
            out_dev = self._resolve_output_dev_fallback()
        ptt = self._make_ptt_config()
        if self._hw_mode() == "PAKT":
            # No PTT keying in PAKT mode; sweep plays audio only.
            ptt = PttConfig(enabled=False)
        sweep_freqs = [1200, 1500, 1800, 2200]
        dr_port = self.digirig_port_var.get().strip() if self._hw_mode() == "DigiRig" else ""

        def worker():
            dr_ser = None
            if ptt.enabled and dr_port:
                # DigiRig: open serial once for the whole sweep, close at end
                import serial as _serial
                try:
                    dr_ser = _serial.Serial(
                        dr_port, 9600,
                        dsrdtr=False, rtscts=False, xonxoff=False, timeout=0.1,
                    )
                    dr_ser.rts = False
                    dr_ser.dtr = False
                except Exception as exc:
                    _log.debug("DigiRig: sweep PTT port open failed (%s): %s", dr_port, exc)

            def ptt_cb(state: bool) -> None:
                if dr_ser and dr_ser.is_open:
                    try:
                        drive = state if ptt.active_high else (not state)
                        dr_ser.rts = drive
                    except Exception as exc:
                        _log.warning("DigiRig PTT error (state=%s): %s", state, exc)
                        self._evq.put_nowait(_StatusEvt(f"DigiRig PTT error ({'ON' if state else 'OFF'}): {exc}"))
                elif not dr_port:
                    try:
                        self.radio.set_ptt(state, line=ptt.line, active_high=ptt.active_high)
                        _log.debug("PTT %s: line=%s active_high=%s", 'ON' if state else 'OFF', ptt.line, ptt.active_high)
                    except Exception as exc:
                        _log.warning("SA818 PTT error (state=%s): %s", state, exc)
                        self._evq.put_nowait(_StatusEvt(f"PTT error ({'ON' if state else 'OFF'}): {exc}"))

            try:
                for f in sweep_freqs:
                    try:
                        wav_path = self._audio_dir / f"sweep_{f}.wav"
                        write_test_tone_wav(wav_path, frequency_hz=float(f), seconds=0.4)
                        self.audio.play_with_ptt_blocking(wav_path, out_dev, ptt, ptt_cb)
                    except Exception as exc:
                        _log.warning("TX sweep error at %s Hz (dev=%s): %s", f, out_dev, exc)
                        self._evq.put_nowait(_StatusEvt(f"Sweep error at {f} Hz (dev {out_dev}): {exc}"))
            finally:
                if dr_ser is not None:
                    try:
                        dr_ser.rts = False
                        dr_ser.close()
                    except Exception:
                        pass
            self._evq.put_nowait(_StatusEvt("TX channel sweep complete"))

        threading.Thread(target=worker, daemon=True).start()
        self._set_status("Running TX sweep…")

    def ptt_diagnostics(self) -> None:
        """Cycle through RTS/DTR + active-high/low for 1.5 s each to identify the correct PTT wiring.

        Results appear in the main log.  Watch the radio/handheld for a carrier during each step.
        """
        if self._hw_mode() not in ("SA818",):
            self._set_status("PTT diagnostics: uConsole_HAT mode only"); return
        if not self.radio.connected:
            self._set_status("PTT diagnostics: radio not connected"); return

        combos = [
            ("RTS", True,  "RTS active-high  (current profile)"),
            ("RTS", False, "RTS active-low   (inverted)"),
            ("DTR", True,  "DTR active-high"),
            ("DTR", False, "DTR active-low   (inverted)"),
        ]

        def worker():
            self._evq.put_nowait(_StatusEvt("PTT diagnostics: starting — watch for carrier on radio…"))
            for line, active_high, label in combos:
                try:
                    self._evq.put_nowait(_StatusEvt(f"PTT diag: keying {label}"))
                    self.radio.set_ptt(True,  line=line, active_high=active_high)
                    import time as _t; _t.sleep(1.5)
                except Exception as exc:
                    self._evq.put_nowait(_StatusEvt(f"PTT diag error ({label}): {exc}"))
                finally:
                    try:
                        self.radio.release_ptt(line=line, active_high=active_high)
                    except Exception:
                        pass
                    import time as _t; _t.sleep(0.8)
            try:
                # Final safety-net release using the current profile settings so a failed
                # diagnostic step cannot leave the radio keyed until the cable is replugged.
                _p = self._get_current_profile()
                self.radio.release_ptt(line=_p.ptt_line, active_high=_p.ptt_active_high)
            except Exception:
                pass
            self._evq.put_nowait(_StatusEvt("PTT diagnostics complete — note which step keyed the radio"))

        threading.Thread(target=worker, daemon=True).start()

    def auto_detect_rx(self) -> None:
        """Capture a short audio sample and suggest OS mic level."""
        import platform
        if platform.system().lower() != "windows":
            self._set_status("Auto-detect RX level: Windows only")
            return
        in_dev = getattr(self, "_input_dev_idx", None)

        def worker():
            try:
                import numpy as np
                rate, mono = self.audio.capture_compatible(3.0, in_dev)
                rms = float(np.sqrt(np.mean(mono.astype(np.float32) ** 2)))
                # Target: ~-20 dB RMS (0.1 linear) → suggest scaling OS level proportionally
                target = 0.10
                current_level_guess = getattr(self, "_current_os_rx_level", 35)
                if rms > 1e-6:
                    ratio = target / rms
                    suggested = int(max(5, min(100, current_level_guess * ratio)))
                    msg = f"Auto-detect: RMS={rms:.4f}  Suggested OS level={suggested}%"
                    self._evq.put_nowait(_SuggestRxOsLevelEvt(suggested))
                else:
                    suggested = 35
                    msg = "Auto-detect: silence detected — check mic connection"
                self._evq.put_nowait(_StatusEvt(msg))
                self._evq.put_nowait(_AprsLogEvt(msg))
            except Exception as exc:
                self._evq.put_nowait(_StatusEvt(f"Auto-detect error: {exc}"))

        threading.Thread(target=worker, daemon=True).start()
        self._set_status("Capturing 3s for auto-detect…")

    # -----------------------------------------------------------------------
    # Packet handling
    # -----------------------------------------------------------------------

    def _handle_packet(self, pkt: "DecodedPacket") -> None:
        """Process a received APRS packet on the main thread."""
        # --- Mesh intercept (must not crash APRS RX loop) ---
        if pkt.info.startswith(MESH_PREFIX):
            try:
                self._handle_mesh_packet(pkt)
            except Exception as exc:
                _log.warning("Mesh packet handler error: %s", exc)
            return

        p = self._get_current_profile()
        local_calls = {p.aprs_source.upper()}
        snap = self._make_tx_snapshot()

        result = self.aprs.handle_received_packet(
            pkt=pkt,
            local_calls=local_calls,
            auto_ack=p.aprs_auto_ack,
            snap=snap,
        )
        if result is None:
            return
        if result.get("duplicate"):
            return

        # Heard station
        src = pkt.source.split("*")[0].strip()
        self.comms.note_heard(src)

        # Map position
        pos = result.get("position")
        if pos:
            lat, lon, comment = pos
            self._comms_tab.add_map_point(lat, lon, pkt.source)

        # ACK received
        if "ack_id" in result:
            ack_id = result["ack_id"]
            self._comms_tab.append_log(f"ACK received: id={ack_id} from {pkt.source}")
            thread_key = self.comms.mark_delivered(ack_id)
            if thread_key is not None:
                self._comms_tab.on_delivered(thread_key)
            return

        # Intro
        intro = result.get("intro")
        if intro:
            call, lat, lon, note = intro
            if self.comms.should_process_intro(call, lat, lon, note):
                self.comms.ensure_contact(call)
                self._comms_tab.add_map_point(lat, lon, call)
                msg = ChatMessage(direction="RX", src=call, dst=p.aprs_source,
                                   text=f"[Intro] Lat={lat:.4f} Lon={lon:.4f} '{note}'",
                                   thread_key=call)
                self.comms.add_message(msg)
            return

        # Chat message
        msg_fields = result.get("message")
        if msg_fields:
            addressee, msg_text, msg_id = msg_fields

            # Group
            group_fields = result.get("group")
            if group_fields:
                group_name, body, part, total = group_fields
                thread_key = f"GROUP:{group_name}"
                chat_msg = ChatMessage(
                    direction="RX", src=pkt.source, dst=group_name,
                    text=body if (part is None or total is None or total == 1) else f"[{part}/{total}] {body}",
                    thread_key=thread_key, group=group_name,
                )
            else:
                thread_key = self.comms.infer_thread_key(pkt.source, addressee, msg_text, local_calls)
                chat_msg = ChatMessage(
                    direction="RX", src=pkt.source, dst=addressee,
                    text=msg_text, msg_id=msg_id, thread_key=thread_key,
                )

            self.comms.add_message(chat_msg)
            self.comms.set_last_direct_sender(pkt.source)

        # TTS announce
        if hasattr(self, "_setup_tab") and self._setup_tab.tts_enabled:
            self._tts_announce(pkt.source, msg_text if msg_fields else pkt.info)

    # -----------------------------------------------------------------------
    # Mesh actions
    # -----------------------------------------------------------------------

    def _handle_mesh_packet(self, pkt: "DecodedPacket") -> None:
        """Process a received mesh packet (called on main thread, errors must not propagate)."""
        import time as _time
        now = _time.monotonic()
        outbound, deliveries = self.mesh.handle_rx(pkt.info, pkt.source, now)
        # Log deliveries
        for msg in deliveries:
            self._evq.put_nowait(_MeshLogEvt(f"[RX] {msg}"))
        # Dispatch outbound packets via APRS TX
        for mpkt in outbound:
            self._mesh_tx(mpkt.raw)
        # Notify tab of route update
        if outbound or deliveries:
            self._evq.put_nowait(_MeshRouteUpdateEvt())

    def _mesh_tx(self, payload: str) -> None:
        """Send a mesh payload string over the APRS TX path (fire and forget)."""
        snap = self._make_tx_snapshot()
        if snap is None:
            _log.debug("Mesh TX skipped: no TX snapshot available")
            return
        import threading as _threading
        def _worker():
            try:
                self.aprs.send_payload(payload, snap)
            except Exception as exc:
                _log.warning("Mesh TX error: %s", exc)
        _threading.Thread(target=_worker, daemon=True).start()

    def mesh_discover(self, target: str) -> None:
        """Initiate route discovery to target (called from MeshTab)."""
        import time as _time
        now = _time.monotonic()
        pkts = self.mesh.discover_route(target, now)
        for mpkt in pkts:
            self._mesh_tx(mpkt.raw)
        if pkts:
            self._evq.put_nowait(_MeshLogEvt(f"RREQ sent to {target}"))
        else:
            self._evq.put_nowait(_MeshLogEvt(f"Discover {target}: no packet sent (mesh disabled)"))

    def mesh_send(self, dst: str, body: str) -> None:
        """Send mesh DATA to dst (called from MeshTab)."""
        import time as _time
        now = _time.monotonic()
        pkts = self.mesh.send_data(dst, body, now)
        for mpkt in pkts:
            self._mesh_tx(mpkt.raw)
        if pkts:
            self._evq.put_nowait(_MeshLogEvt(f"DATA sent to {dst} ({len(pkts)} packet(s))"))
        else:
            self._evq.put_nowait(_MeshLogEvt(f"DATA to {dst}: not sent (mesh disabled or no route)"))

    def mesh_apply_config(self) -> None:
        """Push current mesh Tk vars into MeshManager config."""
        cfg = MeshConfig(
            enabled=self.mesh_enabled_var.get(),
            node_role=self.mesh_node_role_var.get(),
            default_ttl=self.mesh_default_ttl_var.get(),
            rate_limit_ppm=self.mesh_rate_limit_ppm_var.get(),
            hello_enabled=self.mesh_hello_enabled_var.get(),
            route_expiry_s=self.mesh_route_expiry_var.get(),
        )
        self.mesh.set_config(cfg)

    # -----------------------------------------------------------------------
    # Comms actions (called by CommsTab)
    # -----------------------------------------------------------------------

    def add_contact(self, call: str) -> None:
        self.comms.add_contact(call)

    def remove_contact(self, call: str) -> None:
        self.comms.remove_contact(call)

    def import_heard_to_contacts(self) -> None:
        self.comms.add_heard_to_contacts()

    def clear_heard(self) -> None:
        self.comms.clear_heard()
        self._comms_tab.refresh_heard()

    def set_group(self, name: str, members: list[str]) -> None:
        self.comms.set_group(name, members)

    def delete_group(self, name: str) -> None:
        self.comms.delete_group(name)

    # -----------------------------------------------------------------------
    # Profile management
    # -----------------------------------------------------------------------

    def save_profile(self, path: Optional[str] = None) -> None:
        """Collect profile from all tabs and save."""
        p = self._collect_profile_snapshot()
        # Add comms data
        comms_data = self.comms.to_dict()
        p.chat_contacts = comms_data["contacts"]
        p.chat_groups   = comms_data["groups"]
        target = ProfileManager(Path(path)) if path else self._prof
        try:
            target.save(p)
            self._set_status(f"Profile saved: {target.path.name}")
        except Exception as exc:
            messagebox.showerror("Save Error", str(exc), parent=self)

    def load_profile(self, path: Optional[str] = None) -> None:
        src = ProfileManager(Path(path)) if path else self._prof
        p = src.load()
        if p is None:
            messagebox.showinfo("Load Profile", "Profile not found or invalid", parent=self)
            return
        self._apply_profile_to_tabs(p)
        self._set_status(f"Profile loaded: {src.path.name}")

    def import_profile(self) -> None:
        """Open a file dialog and apply the chosen profile (called from MainTab button)."""
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Import Profile",
            filetypes=(("JSON", "*.json"), ("All files", "*.*")),
            parent=self,
        )
        if not path:
            return
        self.load_profile(path)

    def export_profile(self) -> None:
        """Collect current profile and save it to a user-chosen file (called from MainTab button)."""
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(
            title="Export Profile",
            filetypes=(("JSON", "*.json"), ("All files", "*.*")),
            defaultextension=".json",
            parent=self,
        )
        if not path:
            return
        self.save_profile(path)

    def reset_defaults(self) -> None:
        self._apply_profile_to_tabs(AppProfile())
        self._set_status("Settings reset to defaults")

    def _load_and_apply_profile(self) -> None:
        p = self._prof.load() or AppProfile()
        self._apply_profile_to_tabs(p)

    def _apply_profile_to_tabs(self, p: AppProfile) -> None:
        self._main_tab.apply_profile(p)
        self._comms_tab.apply_profile(p)
        self._setup_tab.apply_profile(p)
        if hasattr(self, "_mesh_tab"):
            self._mesh_tab.apply_profile(p)
        # Restore comms contacts/groups
        self.comms.from_dict({"contacts": p.chat_contacts, "groups": p.chat_groups})
        self._comms_tab.refresh_contacts()
        # Restore hardware mode vars
        hw = p.hardware_mode if p.hardware_mode in ("SA818", "uConsole_HAT", "DigiRig", "PAKT") else "SA818"
        self.hardware_mode_var.set("uConsole_HAT" if hw == "SA818" else hw)
        self.digirig_port_var.set(p.digirig_port)
        self.pakt_device_var.set(p.pakt_device_name)
        self.pakt_address_var.set(p.pakt_device_address)
        self.pakt_callsign_var.set(p.pakt_callsign)
        self.pakt_ssid_var.set(str(p.pakt_ssid))
        self.pakt_capabilities_var.set(p.pakt_capabilities_summary or "not connected")
        # Restore mesh vars and push config into manager
        self.mesh_enabled_var.set(p.mesh_test_enabled)
        role = p.mesh_node_role if p.mesh_node_role in ("ENDPOINT", "REPEATER") else "ENDPOINT"
        self.mesh_node_role_var.set(role)
        self.mesh_default_ttl_var.set(p.mesh_default_ttl)
        self.mesh_rate_limit_ppm_var.set(p.mesh_rate_limit_ppm)
        self.mesh_hello_enabled_var.set(p.mesh_hello_enabled)
        self.mesh_route_expiry_var.set(p.mesh_route_expiry_s)
        self.mesh_apply_config()
        # Cache device indices from names (best-effort)
        self._restore_audio_from_profile(p)

    def _restore_audio_from_profile(self, p: AppProfile) -> None:
        if not p.output_device_name and not p.input_device_name:
            return
        try:
            outs = {n: i for i, n in list_output_devices()}
            ins  = {n: i for i, n in list_input_devices()}
            if p.output_device_name in outs:
                self._output_dev_idx  = outs[p.output_device_name]
                self._output_dev_name = p.output_device_name
            else:
                for name, idx in outs.items():
                    if name == p.output_device_name or name.startswith(f"{p.output_device_name} ["):
                        self._output_dev_idx = idx
                        self._output_dev_name = name
                        break
            if p.input_device_name in ins:
                self._input_dev_idx  = ins[p.input_device_name]
                self._input_dev_name = p.input_device_name
            else:
                for name, idx in ins.items():
                    if name == p.input_device_name or name.startswith(f"{p.input_device_name} ["):
                        self._input_dev_idx = idx
                        self._input_dev_name = name
                        break
        except Exception:
            pass

    def _collect_profile_snapshot(self) -> AppProfile:
        p = AppProfile()
        self._main_tab.collect_profile(p)
        self._comms_tab.collect_profile(p)
        self._setup_tab.collect_profile(p)
        # Store audio device names for future restore
        p.output_device_name = getattr(self, "_output_dev_name", "")
        p.input_device_name  = getattr(self, "_input_dev_name", "")
        # Hardware mode
        hw = self.hardware_mode_var.get()
        p.hardware_mode = "SA818" if hw == "uConsole_HAT" else hw
        p.digirig_port  = self.digirig_port_var.get().strip()
        p.pakt_device_name = self.pakt_device_var.get().strip()
        p.pakt_device_address = self.pakt_address_var.get().strip()
        p.pakt_callsign = self.pakt_callsign_var.get().strip().upper()
        try:
            p.pakt_ssid = int(self.pakt_ssid_var.get())
        except ValueError:
            pass
        p.pakt_capabilities_summary = self.pakt_capabilities_var.get().strip()
        # Mesh
        p.mesh_test_enabled    = self.mesh_enabled_var.get()
        p.mesh_node_role       = self.mesh_node_role_var.get()
        p.mesh_default_ttl     = self.mesh_default_ttl_var.get()
        p.mesh_rate_limit_ppm  = self.mesh_rate_limit_ppm_var.get()
        p.mesh_hello_enabled   = self.mesh_hello_enabled_var.get()
        p.mesh_route_expiry_s  = self.mesh_route_expiry_var.get()
        return p

    def _get_current_profile(self) -> AppProfile:
        """Collect a lightweight snapshot for engine calls."""
        try:
            return self._collect_profile_snapshot()
        except Exception:
            return AppProfile()

    def _autosave(self) -> None:
        try:
            self.save_profile()
        except Exception:
            pass
        self.after(self.AUTOSAVE_MS, self._autosave)

    def _pakt_tx_timeout_tick(self) -> None:
        """Expire PAKT outbound messages that never received a tx_result."""
        try:
            expired_keys = self.comms.expire_stale_pakt_tx(max_age_s=120.0)
            for thread_key in expired_keys:
                _log.debug("PAKT TX expired (no tx_result) for thread %s", thread_key)
                self._comms_tab.on_message_updated(thread_key)
        except Exception as exc:
            _log.debug("PAKT TX timeout tick error: %s", exc)
        self.after(30_000, self._pakt_tx_timeout_tick)

    def _mesh_tick(self) -> None:
        """Periodic mesh housekeeping (HELLO, route expiry)."""
        try:
            import time as _time
            now = _time.monotonic()
            pkts = self.mesh.tick(now)
            for mpkt in pkts:
                self._mesh_tx(mpkt.raw)
            if pkts:
                self._evq.put_nowait(_MeshRouteUpdateEvt())
        except Exception as exc:
            _log.debug("Mesh tick error: %s", exc)
        self.after(10_000, self._mesh_tick)  # every 10s

    # -----------------------------------------------------------------------
    # TX snapshot builder (captures all values needed by engine threads)
    # -----------------------------------------------------------------------

    def _make_tx_snapshot(self) -> Optional[_TxSnapshot]:
        p = self._get_current_profile()
        hw = self._hw_mode()
        out_dev = getattr(self, "_output_dev_idx", None)
        if out_dev is None:
            out_dev = 0   # system default
        bw = 1 if p.bandwidth.lower().startswith("w") else 0
        radio = RadioConfig(
            frequency=p.frequency,
            offset=p.offset,
            bandwidth=bw,
            squelch=p.squelch,
            ctcss_tx=p.ctcss_tx or None,
            ctcss_rx=p.ctcss_rx or None,
            dcs_tx=p.dcs_tx or None,
            dcs_rx=p.dcs_rx or None,
        )
        ptt = PttConfig(
            enabled=p.ptt_enabled,
            line=p.ptt_line,
            active_high=p.ptt_active_high,
            pre_ms=p.ptt_pre_ms,
            post_ms=p.ptt_post_ms,
        )

        if hw == "DigiRig":
            # DigiRig: no SA818 port needed; PTT via separate serial port
            ptt_serial_port = self.digirig_port_var.get().strip()
            return _TxSnapshot(
                source=p.aprs_source,
                destination=p.aprs_dest,
                path=p.aprs_path,
                gain=p.aprs_tx_gain,
                preamble_flags=p.aprs_preamble_flags,
                trailing_flags=16,
                repeats=p.aprs_tx_repeats,
                out_dev=int(out_dev),
                ptt=ptt,
                radio=radio,
                volume=p.volume,
                reinit=False,
                port="",
                hw_mode="DigiRig",
                ptt_serial_port=ptt_serial_port,
            )

        if hw == "PAKT":
            return None

        # --- SA818 path ---
        # Derive port from RadioController client
        port = ""
        try:
            if self.radio.connected and self.radio.client.ser:
                port = str(self.radio.client.ser.port)
        except Exception:
            pass

        return _TxSnapshot(
            source=p.aprs_source,
            destination=p.aprs_dest,
            path=p.aprs_path,
            gain=p.aprs_tx_gain,
            preamble_flags=p.aprs_preamble_flags,
            trailing_flags=16,
            repeats=p.aprs_tx_repeats,
            out_dev=int(out_dev),
            ptt=ptt,
            radio=radio,
            volume=p.volume,
            reinit=p.aprs_tx_reinit,
            port=port,
            hw_mode="SA818",
            ptt_serial_port="",
        )

    def _make_ptt_config(self) -> PttConfig:
        p = self._get_current_profile()
        return PttConfig(
            enabled=p.ptt_enabled,
            line=p.ptt_line,
            active_high=p.ptt_active_high,
            pre_ms=p.ptt_pre_ms,
            post_ms=p.ptt_post_ms,
        )

    # -----------------------------------------------------------------------
    # OS mic level control (Windows / pycaw)
    # -----------------------------------------------------------------------

    _current_os_rx_level: int = 35

    def _apply_os_rx_level(self, level: int) -> None:
        self._current_os_rx_level = level
        import platform
        if platform.system().lower() != "windows":
            return

        selected_name: str = getattr(self, "_input_dev_name", "")

        def worker():
            # Every new Python thread must call CoInitialize before using any COM
            # object (pycaw/comtypes uses COM under the hood).  Failure to do so
            # raises WinError -2147221008 (CO_E_NOTINITIALIZED).
            try:
                from comtypes import CoInitialize, CoUninitialize
                CoInitialize()
            except Exception:
                CoInitialize = CoUninitialize = None  # type: ignore[assignment]

            try:
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                from comtypes import CLSCTX_ALL

                scalar = max(0.0, min(1.0, level / 100.0))
                device = None
                matched_name = ""

                # Find the selected input device by name among Windows audio endpoints.
                # GetAllDevices() returns BOTH render (output) and capture (input) endpoints.
                # Windows MMDevice IDs encode data flow: "{0.0.0.…}.{GUID}" = render,
                # "{0.0.1.…}.{GUID}" = capture.  We skip confirmed render endpoints so that
                # when the SA818 USB codec names both endpoints identically (e.g. "USB Audio
                # Device"), we do not accidentally set the speaker volume instead of the mic.
                if selected_name:
                    sel_lower = selected_name.lower()
                    try:
                        import warnings as _w
                        with _w.catch_warnings():
                            _w.simplefilter("ignore")   # suppress pycaw COMError UserWarnings
                            all_devs = AudioUtilities.GetAllDevices()
                        for d in all_devs:
                            if not (d.FriendlyName and sel_lower in d.FriendlyName.lower()):
                                continue
                            # Skip confirmed render endpoints (ID contains ".0.0.")
                            dev_id = ""
                            try:
                                dev_id = d.id or ""
                            except Exception:
                                pass
                            if dev_id and ".0.0." in dev_id:
                                continue   # render endpoint — skip
                            device = d
                            matched_name = d.FriendlyName
                            break
                    except Exception as exc:
                        err = f"OS mic level scan error: {exc}"
                        _log.debug(err)
                        self._evq.put_nowait(_AprsLogEvt(err))

                if device is None:
                    device = AudioUtilities.GetMicrophone()
                    matched_name = "default microphone"

                # AudioDevice is a pycaw wrapper; the underlying IMMDevice COM object
                # (which has Activate()) is at ._dev.
                imm_dev = device._dev if hasattr(device, "_dev") else device
                interface = imm_dev.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                vol = interface.QueryInterface(IAudioEndpointVolume)
                vol.SetMasterVolumeLevelScalar(scalar, None)
                msg = f"OS mic level → {level}% on \"{matched_name}\""
                self._evq.put_nowait(_StatusEvt(msg))
                self._evq.put_nowait(_AprsLogEvt(msg))
            except ImportError:
                pass  # pycaw not installed — graceful fallback
            except Exception as exc:
                err = f"OS mic level error: {exc}"
                _log.debug(err)
                self._evq.put_nowait(_AprsLogEvt(err))
            finally:
                try:
                    if CoUninitialize is not None:
                        CoUninitialize()
                except Exception:
                    pass

        threading.Thread(target=worker, daemon=True).start()

    def _apply_os_tx_level(self, level: int) -> None:
        """Set the SA818 USB playback device to `level` % in Windows.

        The SA818's Windows playback volume directly scales the audio level fed into
        the SA818's MIC input, which determines FM deviation.  Different PCs may have
        different auto-configured playback levels; setting it explicitly ensures
        consistent FM deviation across machines.
        """
        import platform
        if platform.system().lower() != "windows":
            return

        selected_name: str = getattr(self, "_output_dev_name", "")

        def worker():
            try:
                from comtypes import CoInitialize, CoUninitialize
                CoInitialize()
            except Exception:
                CoInitialize = CoUninitialize = None  # type: ignore[assignment]

            try:
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                from comtypes import CLSCTX_ALL

                scalar = max(0.0, min(1.0, level / 100.0))
                device = None
                matched_name = ""

                # Find the selected output device among Windows endpoints.
                # Skip confirmed capture endpoints (ID contains ".0.1.").
                if selected_name:
                    sel_lower = selected_name.lower()
                    try:
                        import warnings as _w
                        with _w.catch_warnings():
                            _w.simplefilter("ignore")
                            all_devs = AudioUtilities.GetAllDevices()
                        for d in all_devs:
                            if not (d.FriendlyName and sel_lower in d.FriendlyName.lower()):
                                continue
                            dev_id = ""
                            try:
                                dev_id = d.id or ""
                            except Exception:
                                pass
                            if dev_id and ".0.1." in dev_id:
                                continue   # capture endpoint — skip
                            device = d
                            matched_name = d.FriendlyName
                            break
                    except Exception as exc:
                        err = f"OS speaker level scan error: {exc}"
                        _log.debug(err)
                        self._evq.put_nowait(_AprsLogEvt(err))

                if device is None:
                    device = AudioUtilities.GetSpeaker()
                    matched_name = "default speaker"

                # AudioDevice is a pycaw wrapper; the underlying IMMDevice COM object
                # (which has Activate()) is at ._dev.
                imm_dev = device._dev if hasattr(device, "_dev") else device
                interface = imm_dev.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                vol = interface.QueryInterface(IAudioEndpointVolume)
                vol.SetMasterVolumeLevelScalar(scalar, None)
                msg = f"OS speaker level → {level}% on \"{matched_name}\""
                self._evq.put_nowait(_AprsLogEvt(msg))
            except ImportError:
                pass
            except Exception as exc:
                err = f"OS speaker level error: {exc}"
                _log.debug(err)
                self._evq.put_nowait(_AprsLogEvt(err))
            finally:
                try:
                    if CoUninitialize is not None:
                        CoUninitialize()
                except Exception:
                    pass

        threading.Thread(target=worker, daemon=True).start()

    # -----------------------------------------------------------------------
    # TTS (Windows PowerShell — safe, no injection)
    # -----------------------------------------------------------------------

    def _tts_announce(self, source: str, text: str) -> None:
        import platform
        if platform.system().lower() != "windows":
            return
        # Build speech string safely without any shell interpolation
        speech = f"From {source}: {text}"
        # Escape single quotes for PS string literal
        speech_escaped = speech.replace("'", "''")

        def worker():
            try:
                ps_script = (
                    "Add-Type -AssemblyName System.Speech; "
                    f"(New-Object System.Speech.Synthesis.SpeechSynthesizer)"
                    f".Speak('{speech_escaped}')"
                )
                subprocess.run(
                    ["powershell", "-WindowStyle", "Hidden", "-NonInteractive",
                     "-Command", ps_script],
                    check=False, capture_output=True, timeout=15,
                )
            except Exception:
                pass

        threading.Thread(target=worker, daemon=True).start()

    # -----------------------------------------------------------------------
    # Bootstrap / diagnostics
    # -----------------------------------------------------------------------

    def run_bootstrap(self) -> None:
        script = self._app_dir / "scripts" / "bootstrap_third_party.py"
        if not script.exists():
            messagebox.showinfo("Bootstrap", f"Script not found:\n{script}", parent=self)
            return
        try:
            subprocess.Popen([sys.executable, str(script)], creationflags=subprocess.CREATE_NEW_CONSOLE
                              if sys.platform == "win32" else 0)
        except Exception as exc:
            messagebox.showerror("Bootstrap Error", str(exc), parent=self)

    def run_two_radio_diagnostic(self) -> None:
        script = self._app_dir / "scripts" / "two_radio_diagnostic.py"
        if not script.exists():
            messagebox.showinfo("Diagnostic", f"Script not found:\n{script}", parent=self)
            return
        try:
            subprocess.Popen([sys.executable, str(script)], creationflags=subprocess.CREATE_NEW_CONSOLE
                              if sys.platform == "win32" else 0)
        except Exception as exc:
            messagebox.showerror("Diagnostic Error", str(exc), parent=self)

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def refresh_ports(self) -> None:
        """Refresh COM port list in the port combobox (main thread)."""
        ports = self.scan_ports()
        self._main_tab.port_combo["values"] = ports
        if ports and not self.port_var.get():
            self.port_var.set(ports[0])
        self._set_status(f"{len(ports)} port(s) found")

    def auto_identify(self) -> None:
        """Auto-identify SA818 — alias matching MainTab button command."""
        self.auto_identify_and_connect()

    def read_version(self) -> None:
        if self._hw_mode() == "PAKT":
            self.pakt_read_capabilities()
            return
        if self._hw_mode() == "DigiRig":
            self._set_status("Version read not available in DigiRig mode."); return
        if not self.radio.connected:
            self._set_status("Not connected"); return

        def worker():
            try:
                ver = self.radio.version()
                self._evq.put_nowait(_StatusEvt(f"uConsole_HAT version: {ver}"))
                self._evq.put_nowait(_LogEvt(f"uConsole_HAT version: {ver}"))
            except Exception as exc:
                self._evq.put_nowait(_StatusEvt(f"Version error: {exc}"))

        threading.Thread(target=worker, daemon=True).start()

    def pakt_scan(self) -> None:
        self.pakt.scan(timeout=8.0)

    def pakt_connect_selected(self) -> None:
        address = self.pakt_address_var.get().strip()
        if not address:
            self._set_status("Select a PAKT device first")
            return
        self.pakt.connect(address)

    def pakt_disconnect(self) -> None:
        self.pakt.disconnect()

    def pakt_read_capabilities(self) -> None:
        if not self.pakt.is_connected:
            self._set_status("PAKT not connected")
            return
        self.pakt.read_capabilities()

    def pakt_read_config(self) -> None:
        if not self.pakt.is_connected:
            self._set_status("PAKT not connected")
            return
        self.pakt.read_config()

    def pakt_write_config(self) -> None:
        if not self.pakt.is_connected:
            self._set_status("PAKT not connected")
            return
        callsign = self.pakt_callsign_var.get().strip().upper()
        if not callsign:
            self._set_status("Enter a PAKT callsign first")
            return
        if not (1 <= len(callsign) <= 6) or not re.fullmatch(r"[A-Z0-9\-]+", callsign):
            self._set_status("PAKT callsign must be 1-6 chars [A-Z0-9-]")
            return
        try:
            ssid = int(self.pakt_ssid_var.get().strip() or "0")
        except ValueError:
            self._set_status("PAKT SSID must be 0-15")
            return
        if not (0 <= ssid <= 15):
            self._set_status("PAKT SSID must be 0-15")
            return
        self.pakt.write_config(json.dumps({"callsign": callsign, "ssid": ssid}))

    def pakt_send_tx_request(self, dest: str = "", text: str = "") -> bool:
        """Validate and submit a PAKT TX request. Returns True if submitted, False on any pre-flight failure."""
        if not self.pakt.is_connected:
            self._set_status("PAKT not connected")
            return False
        dest = (dest or self.aprs_msg_to_var.get()).strip().upper()
        text = (text or self.aprs_msg_text_var.get()).strip()
        if not dest or not text:
            self._set_status("Enter destination and text for PAKT TX")
            return False
        # Validate dest: 1-6 chars [A-Z0-9-] per PAKT contract.
        if not (1 <= len(dest) <= 6) or not re.fullmatch(r"[A-Z0-9\-]+", dest):
            self._set_status("PAKT dest must be 1-6 chars [A-Z0-9-]")
            return False
        # Validate text: 1-67 printable chars per PAKT contract.
        if len(text) > 67 or not text.isprintable():
            self._set_status("PAKT text must be 1-67 printable characters")
            return False
        try:
            ssid = int(self.pakt_ssid_var.get().strip() or "0")
        except ValueError:
            self._set_status("PAKT SSID must be 0-15")
            return False
        if not (0 <= ssid <= 15):
            self._set_status("PAKT SSID must be 0-15")
            return False
        self.pakt.send_tx_request(dest=dest, text=text, ssid=ssid)
        return True

    def _apply_pakt_config_to_vars(self, text: str) -> None:
        try:
            data = json.loads(text)
        except Exception:
            return
        callsign = str(data.get("callsign", "")).strip().upper()
        ssid = str(data.get("ssid", 0))
        if callsign:
            self.pakt_callsign_var.set(callsign)
        self.pakt_ssid_var.set(ssid)

    def _set_status(self, text: str) -> None:
        self._status_var.set(text)
        self.status_var.set(text)

    # -----------------------------------------------------------------------
    # Window close
    # -----------------------------------------------------------------------

    def _on_close(self) -> None:
        try:
            self.save_profile()
        except Exception:
            pass
        # Signal RX monitor to stop (non-blocking; daemon thread will exit on its own)
        try:
            self.aprs._rx_running = False
        except Exception:
            pass
        # Disconnect radio (quick serial close)
        try:
            self.pakt.disconnect()
        except Exception:
            pass
        try:
            _close_profile = self._get_current_profile()
            self.radio.release_ptt(
                line=_close_profile.ptt_line,
                active_high=_close_profile.ptt_active_high,
            )
        except Exception:
            pass
        try:
            self.radio.disconnect()
        except Exception:
            pass
        self.destroy()

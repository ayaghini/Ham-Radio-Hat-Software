#!/usr/bin/env python3
"""Main Tab — Radio control, connection, and audio routing."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

import tkinter as tk
from tkinter import messagebox, ttk

from ..engine.models import AppProfile
from ..engine.sa818_client import CTCSS
from .widgets import BoundedLog, add_row, scrollable_frame

if TYPE_CHECKING:
    from ..app import HamHatApp


class MainTab(ttk.Frame):
    """Control tab: connection, radio params, audio routing, log."""

    _UI_PRIMARY_HW = "uConsole_HAT"

    def __init__(self, parent: ttk.Notebook, state: "HamHatApp") -> None:
        super().__init__(parent)
        self._state = state
        self._out_device_map: dict[str, int] = {}
        self._in_device_map:  dict[str, int] = {}
        # Widgets that change visibility / state based on hardware mode
        self._sa818_only_widgets: list[tk.Widget] = []
        self._digirig_only_widgets: list[tk.Widget] = []
        self._pakt_only_widgets: list[tk.Widget] = []
        self._pakt_device_map: dict[str, str] = {}
        self._build()

    def _build(self) -> None:
        cfg = self._state.display_cfg
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)  # scrollable params fills available space

        # Scrollable params container
        params_host = ttk.Frame(self)
        params_host.grid(row=0, column=0, sticky="nsew")
        _, _, top = scrollable_frame(params_host)
        self._build_params(top)

        # Log panel at bottom — height from DisplayConfig so RPi gets a
        # shorter log (fewer lines) that fits within the 720px vertical budget.
        pad = cfg.compact_padding
        lf = ttk.LabelFrame(self, text="Radio Log", padding=4)
        lf.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, pad))
        lf.columnconfigure(0, weight=1)
        lf.rowconfigure(0, weight=1)
        self._log = BoundedLog(lf, height=cfg.log_height_main, wrap="word",
                                font=(cfg.mono_font, 8), state="disabled",
                                background="#0f2531", foreground="#9cc4dd")
        self._log.grid(row=0, column=0, sticky="nsew")

    def _build_params(self, parent: ttk.Frame) -> None:
        cfg = self._state.display_cfg
        _sp = cfg.compact_padding  # section vertical gap (4 desktop, 2 RPi)
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)
        parent.columnconfigure(2, weight=1)
        parent.columnconfigure(3, weight=1)

        # --- Connection ---
        conn = ttk.LabelFrame(parent, text="Connection", padding=8)
        conn.grid(row=0, column=0, columnspan=4, sticky="ew")
        conn.columnconfigure(1, weight=1)
        conn.columnconfigure(3, weight=1)

        # uConsole_HAT serial port and hardware mode on one row
        sa818_port_lbl = ttk.Label(conn, text="uConsole_HAT Serial Port")
        sa818_port_lbl.grid(row=0, column=0, sticky="w", pady=3)
        self.port_combo = ttk.Combobox(conn, textvariable=self._state.port_var, width=22, state="readonly")
        self.port_combo.grid(row=0, column=1, sticky="ew", padx=6, pady=3)
        self._sa818_only_widgets += [sa818_port_lbl, self.port_combo]

        ttk.Label(conn, text="Hardware Mode").grid(row=0, column=2, sticky="w", padx=(12, 0), pady=3)
        hw_combo = ttk.Combobox(
            conn, textvariable=self._state.hardware_mode_var,
            values=[self._UI_PRIMARY_HW, "DigiRig", "PAKT"], width=14, state="readonly",
        )
        hw_combo.grid(row=0, column=3, sticky="w", padx=6, pady=3)
        hw_combo.bind("<<ComboboxSelected>>", self._on_hw_mode_changed)
        ttk.Label(conn, textvariable=self._state.status_var).grid(row=0, column=4, sticky="e", padx=(12, 0))

        # DigiRig PTT port (hidden in SA818 mode)
        dr_port_lbl = ttk.Label(conn, text="DigiRig PTT Port")
        dr_port_lbl.grid(row=1, column=0, sticky="w", pady=3)
        dr_port_entry = ttk.Entry(conn, textvariable=self._state.digirig_port_var, width=22)
        dr_port_entry.grid(row=1, column=1, sticky="ew", padx=6, pady=3)
        self._digirig_only_widgets += [dr_port_lbl, dr_port_entry]

        pakt_dev_lbl = ttk.Label(conn, text="PAKT Device")
        pakt_dev_lbl.grid(row=1, column=0, sticky="w", pady=3)
        self._pakt_device_combo = ttk.Combobox(
            conn,
            textvariable=self._state.pakt_device_var,
            width=22,
            state="readonly",
        )
        self._pakt_device_combo.grid(row=1, column=1, sticky="ew", padx=6, pady=3)
        self._pakt_device_combo.bind("<<ComboboxSelected>>", self._on_pakt_device_selected)
        self._pakt_only_widgets += [pakt_dev_lbl, self._pakt_device_combo]

        btn_row = ttk.Frame(conn)
        btn_row.grid(row=2, column=0, columnspan=5, sticky="ew", pady=(6, 0))
        for i in range(5):
            btn_row.columnconfigure(i, weight=1)
        ttk.Button(btn_row, text="Refresh", command=self._state.refresh_ports).grid(row=0, column=0, sticky="ew")
        self._btn_auto_identify = ttk.Button(btn_row, text="Auto Identify", command=self._state.auto_identify)
        self._btn_auto_identify.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        self._btn_connect = ttk.Button(btn_row, text="Connect", command=self._state.connect)
        self._btn_connect.grid(row=0, column=2, sticky="ew", padx=(6, 0))
        self._btn_disconnect = ttk.Button(btn_row, text="Disconnect", command=self._state.disconnect)
        self._btn_disconnect.grid(row=0, column=3, sticky="ew", padx=(6, 0))
        self._btn_read_version = ttk.Button(btn_row, text="Read Version", command=self._state.read_version)
        self._btn_read_version.grid(row=0, column=4, sticky="ew", padx=(6, 0))
        self._sa818_only_widgets += [self._btn_connect, self._btn_disconnect, self._btn_read_version]

        self._btn_pakt_scan = ttk.Button(btn_row, text="Scan", command=self._state.pakt_scan)
        self._btn_pakt_connect = ttk.Button(btn_row, text="Connect", command=self._state.pakt_connect_selected)
        self._btn_pakt_disconnect = ttk.Button(btn_row, text="Disconnect", command=self._state.pakt_disconnect)
        self._btn_pakt_scan.grid(row=0, column=2, sticky="ew", padx=(6, 0))
        self._btn_pakt_connect.grid(row=0, column=3, sticky="ew", padx=(6, 0))
        self._btn_pakt_disconnect.grid(row=0, column=4, sticky="ew", padx=(6, 0))
        self._pakt_only_widgets += [self._btn_pakt_scan, self._btn_pakt_connect, self._btn_pakt_disconnect]

        # --- Radio params ---
        self._radio_frame = ttk.LabelFrame(parent, text="Radio Parameters (uConsole_HAT)", padding=8)
        self._radio_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(_sp, 0))
        self._radio_frame.columnconfigure(1, weight=1)
        add_row(self._radio_frame, "Frequency (MHz)", ttk.Entry(self._radio_frame, textvariable=self._state.frequency_var, width=14), 0)
        add_row(
            self._radio_frame,
            "TX Offset (MHz, 0.000 = simplex)",
            ttk.Entry(self._radio_frame, textvariable=self._state.offset_var, width=14),
            1,
        )
        add_row(self._radio_frame, "Squelch (0-8)", ttk.Entry(self._radio_frame, textvariable=self._state.squelch_var, width=14), 2)
        bw = ttk.Combobox(self._radio_frame, textvariable=self._state.bandwidth_var, values=["Wide", "Narrow"], width=12, state="readonly")
        add_row(self._radio_frame, "Bandwidth", bw, 3)
        ttk.Button(self._radio_frame, text="Apply Radio", command=self._state.apply_radio).grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=(8, 0))

        # DigiRig mode hint (shown instead of radio params)
        self._digirig_hint = ttk.Label(
            parent,
            text="DigiRig mode: program your radio manually.\nAPRS TX/RX audio routes through the DigiRig USB audio device.",
            justify="left", wraplength=300,
        )
        self._digirig_hint.grid(row=1, column=0, columnspan=2, sticky="nw", padx=8, pady=(_sp, 0))
        self._digirig_only_widgets.append(self._digirig_hint)

        self._pakt_frame = ttk.LabelFrame(parent, text="PAKT BLE", padding=8)
        self._pakt_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(_sp, 0))
        self._pakt_frame.columnconfigure(1, weight=1)
        add_row(
            self._pakt_frame,
            "Address",
            ttk.Label(self._pakt_frame, textvariable=self._state.pakt_address_var, width=24),
            0,
        )
        add_row(
            self._pakt_frame,
            "Status",
            ttk.Label(self._pakt_frame, textvariable=self._state.pakt_status_var, width=24),
            1,
        )
        add_row(
            self._pakt_frame,
            "Capabilities",
            ttk.Label(
                self._pakt_frame,
                textvariable=self._state.pakt_capabilities_var,
                justify="left",
                wraplength=260,
            ),
            2,
        )
        add_row(
            self._pakt_frame,
            "Callsign",
            ttk.Entry(self._pakt_frame, textvariable=self._state.pakt_callsign_var, width=14),
            3,
        )
        # SSID entry: digits only, max 2 chars (range 0-15 enforced on write).
        _vcmd = (self.register(lambda p: p.isdigit() and len(p) <= 2 or p == ""), "%P")
        add_row(
            self._pakt_frame,
            "SSID (0-15)",
            ttk.Entry(
                self._pakt_frame,
                textvariable=self._state.pakt_ssid_var,
                width=8,
                validate="key",
                validatecommand=_vcmd,
            ),
            4,
        )
        pakt_btns = ttk.Frame(self._pakt_frame)
        pakt_btns.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        for i in range(4):
            pakt_btns.columnconfigure(i, weight=1)
        ttk.Button(pakt_btns, text="Read Caps", command=self._state.pakt_read_capabilities).grid(row=0, column=0, sticky="ew")
        ttk.Button(pakt_btns, text="Read Config", command=self._state.pakt_read_config).grid(row=0, column=1, sticky="ew", padx=(6, 0))
        ttk.Button(pakt_btns, text="Write Config", command=self._state.pakt_write_config).grid(row=0, column=2, sticky="ew", padx=(6, 0))
        ttk.Button(pakt_btns, text="Send TX", command=self._state.pakt_send_tx_request).grid(row=0, column=3, sticky="ew", padx=(6, 0))
        self._pakt_only_widgets.append(self._pakt_frame)

        # --- Audio routing ---
        audio = ttk.LabelFrame(parent, text="Audio Routing", padding=8)
        audio.grid(row=1, column=2, columnspan=2, sticky="nsew", padx=(_sp * 2, 0), pady=(_sp, 0))
        audio.columnconfigure(1, weight=1)
        self.out_combo = ttk.Combobox(audio, textvariable=self._state.audio_out_var, width=34, state="readonly")
        add_row(audio, "Audio Output", self.out_combo, 0)
        self.out_combo.bind("<<ComboboxSelected>>", self._on_out_selected)
        self.in_combo = ttk.Combobox(audio, textvariable=self._state.audio_in_var, width=34, state="readonly")
        add_row(audio, "Audio Input", self.in_combo, 1)
        self.in_combo.bind("<<ComboboxSelected>>", self._on_in_selected)
        ttk.Button(audio, text="Refresh Audio Devices", command=self._state.refresh_audio_devices).grid(
            row=2, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        ttk.Button(audio, text="TX Channel Announce Sweep", command=self._state.tx_channel_sweep).grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        ttk.Button(audio, text="Auto Detect RX by Voice", command=self._state.auto_detect_rx).grid(
            row=4, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        self._shared_audio_frame = audio

        # Apply initial visibility based on current mode
        self._apply_hw_mode_visibility()

    # ------------------------------------------------------------------
    # Hardware mode visibility
    # ------------------------------------------------------------------

    def _on_hw_mode_changed(self, _e=None) -> None:
        self._apply_hw_mode_visibility()
        if hasattr(self._state, "on_hw_mode_changed"):
            self._state.on_hw_mode_changed()
        # When switching INTO PAKT mode, ensure PAKT buttons start in a clean state
        if self._state.hardware_mode_var.get() == "PAKT":
            self.set_pakt_ble_state("IDLE")

    def _apply_hw_mode_visibility(self) -> None:
        hw = self._state.hardware_mode_var.get()
        is_digirig = (hw == "DigiRig")
        is_pakt = (hw == "PAKT")

        # SA818-only widgets: visible in SA818 mode, hidden in DigiRig mode
        for w in self._sa818_only_widgets:
            try:
                if is_digirig or is_pakt:
                    w.grid_remove()
                else:
                    w.grid()
            except Exception:
                pass

        # DigiRig-only widgets: hidden in SA818 mode, visible in DigiRig mode
        for w in self._digirig_only_widgets:
            try:
                if is_digirig:
                    w.grid()
                else:
                    w.grid_remove()
            except Exception:
                pass

        for w in self._pakt_only_widgets:
            try:
                if is_pakt:
                    w.grid()
                else:
                    w.grid_remove()
            except Exception:
                pass

        # Radio params frame: visible in SA818 mode only
        try:
            if is_digirig or is_pakt:
                self._radio_frame.grid_remove()
            else:
                self._radio_frame.grid()
        except Exception:
            pass

        try:
            if is_pakt:
                self._shared_audio_frame.grid_remove()
            else:
                self._shared_audio_frame.grid()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Update from profile
    # ------------------------------------------------------------------

    def apply_profile(self, p: AppProfile) -> None:
        self._state.frequency_var.set(str(p.frequency))
        self._state.offset_var.set(str(p.offset))
        self._state.squelch_var.set(str(p.squelch))
        self._state.bandwidth_var.set(p.bandwidth)
        self._state.ptt_enabled_var.set(p.ptt_enabled)
        self._state.ptt_line_var.set(p.ptt_line)
        self._state.ptt_active_high_var.set(p.ptt_active_high)
        self._state.ptt_pre_ms_var.set(str(p.ptt_pre_ms))
        self._state.ptt_post_ms_var.set(str(p.ptt_post_ms))
        self._state.auto_audio_var.set(p.auto_audio_select)
        # Restore audio device name vars so populate_audio_devices does not default to the first
        # available device when the profile-specified device is already present in the list.
        if p.output_device_name:
            self._state.audio_out_var.set(p.output_device_name)
        if p.input_device_name:
            self._state.audio_in_var.set(p.input_device_name)
        # Hardware mode (note: app.py also sets these vars; this is a redundant but safe belt-and-suspenders)
        hw = p.hardware_mode if p.hardware_mode in ("SA818", self._UI_PRIMARY_HW, "DigiRig", "PAKT") else "SA818"
        self._state.hardware_mode_var.set(self._UI_PRIMARY_HW if hw == "SA818" else hw)
        self._state.digirig_port_var.set(p.digirig_port)
        self._state.pakt_device_var.set(p.pakt_device_name)
        self._state.pakt_address_var.set(p.pakt_device_address)
        self._state.pakt_callsign_var.set(p.pakt_callsign)
        self._state.pakt_ssid_var.set(str(p.pakt_ssid))
        self._state.pakt_capabilities_var.set(p.pakt_capabilities_summary or "not connected")
        self._apply_hw_mode_visibility()

    def collect_profile(self, p: AppProfile) -> None:
        try:
            p.frequency = float(self._state.frequency_var.get())
        except ValueError:
            pass
        try:
            p.offset = float(self._state.offset_var.get())
        except ValueError:
            pass
        try:
            p.squelch = int(self._state.squelch_var.get())
        except ValueError:
            pass
        p.bandwidth = self._state.bandwidth_var.get()
        p.ptt_enabled = self._state.ptt_enabled_var.get()
        p.ptt_line = self._state.ptt_line_var.get()
        p.ptt_active_high = self._state.ptt_active_high_var.get()
        try:
            p.ptt_pre_ms = int(self._state.ptt_pre_ms_var.get())
        except ValueError:
            pass
        try:
            p.ptt_post_ms = int(self._state.ptt_post_ms_var.get())
        except ValueError:
            pass
        p.auto_audio_select = self._state.auto_audio_var.get()
        # Audio device names for profile restore
        p.output_device_name = self._state.audio_out_var.get()
        p.input_device_name  = self._state.audio_in_var.get()
        # Hardware mode
        hw = self._state.hardware_mode_var.get()
        p.hardware_mode = "SA818" if hw == self._UI_PRIMARY_HW else hw
        p.digirig_port  = self._state.digirig_port_var.get().strip()
        p.pakt_device_name = self._state.pakt_device_var.get().strip()
        p.pakt_device_address = self._state.pakt_address_var.get().strip()
        p.pakt_callsign = self._state.pakt_callsign_var.get().strip().upper()
        try:
            p.pakt_ssid = int(self._state.pakt_ssid_var.get())
        except ValueError:
            pass
        p.pakt_capabilities_summary = self._state.pakt_capabilities_var.get().strip()

    # ------------------------------------------------------------------
    # Event handlers from combobox selection
    # ------------------------------------------------------------------

    def _on_out_selected(self, _e=None) -> None:
        name = self._state.audio_out_var.get()
        idx = self._out_device_map.get(name)
        self._state.set_output_device(idx, name)

    def _on_in_selected(self, _e=None) -> None:
        name = self._state.audio_in_var.get()
        idx = self._in_device_map.get(name)
        self._state.set_input_device(idx, name)

    def _on_pakt_device_selected(self, _e=None) -> None:
        name = self._state.pakt_device_var.get()
        self._state.pakt_address_var.set(self._pakt_device_map.get(name, ""))

    # ------------------------------------------------------------------
    # Public API called from app.py dispatcher
    # ------------------------------------------------------------------

    def refresh_audio_devices(self) -> None:
        """Ask app for updated device lists and repopulate comboboxes."""
        from ..engine.audio_tools import list_output_devices, list_input_devices
        outs = list_output_devices()
        ins  = list_input_devices()
        self.populate_audio_devices(outs, ins)

    def populate_audio_devices(
        self,
        outs: list[tuple[int, str]],
        ins:  list[tuple[int, str]],
    ) -> None:
        self._out_device_map = {name: idx for idx, name in outs}
        self._in_device_map  = {name: idx for idx, name in ins}
        out_names = [name for _, name in outs]
        in_names  = [name for _, name in ins]
        self.out_combo["values"] = out_names
        self.in_combo["values"]  = in_names
        # Restore selection if device name still present
        if self._state.audio_out_var.get() not in out_names and out_names:
            self._state.audio_out_var.set(out_names[0])
            self._on_out_selected()
        if self._state.audio_in_var.get() not in in_names and in_names:
            self._state.audio_in_var.set(in_names[0])
            self._on_in_selected()

    def on_audio_pair(self, out_idx: int, out_name: str, in_idx: int, in_name: str) -> None:
        """Called by app dispatcher when auto-pair succeeds."""
        self._state.audio_out_var.set(out_name)
        self._state.audio_in_var.set(in_name)
        self._state.set_output_device(out_idx, out_name)
        self._state.set_input_device(in_idx, in_name)

    def set_pakt_ble_state(self, state: str) -> None:
        """Update PAKT button states based on transport state name."""
        scanning = state == "SCANNING"
        connecting = state in ("CONNECTING", "RECONNECTING")
        connected = state == "CONNECTED"
        self._btn_pakt_scan.configure(
            text="Scanning…" if scanning else "Scan",
            state="disabled" if scanning else "normal",
        )
        self._btn_pakt_connect.configure(state="disabled" if connected or connecting else "normal")
        self._btn_pakt_disconnect.configure(state="normal" if connected or connecting else "disabled")

    def set_pakt_scan_results(self, devices: list[tuple[str, str]]) -> None:
        # Count name occurrences so duplicates get disambiguated with the BLE address.
        name_counts: dict[str, int] = {}
        for name, _ in devices:
            name_counts[name] = name_counts.get(name, 0) + 1

        self._pakt_device_map = {}
        for name, address in devices:
            label = f"{name} ({address})" if name_counts[name] > 1 else name
            self._pakt_device_map[label] = address

        labels = list(self._pakt_device_map.keys())
        self._pakt_device_combo["values"] = labels
        selected_label = self._state.pakt_device_var.get()
        if labels:
            if selected_label in self._pakt_device_map:
                self._state.pakt_address_var.set(self._pakt_device_map[selected_label])
            else:
                self._state.pakt_device_var.set(labels[0])
                self._state.pakt_address_var.set(self._pakt_device_map[labels[0]])
        else:
            self._state.pakt_address_var.set("")

    def set_pakt_status(self, text: str) -> None:
        self._state.pakt_status_var.set(text)

    def set_pakt_capabilities(self, text: str) -> None:
        self._state.pakt_capabilities_var.set(text)

    def set_pakt_config_text(self, text: str) -> None:
        self._state.pakt_last_config_var.set(text)

    def on_connect(self, port: str) -> None:
        pass  # Status bar in app.py already updated

    def on_disconnect(self) -> None:
        pass  # Status bar in app.py already updated

    def append_log(self, msg: str) -> None:
        """Append a line to the radio log panel."""
        self._log.append(msg.rstrip())

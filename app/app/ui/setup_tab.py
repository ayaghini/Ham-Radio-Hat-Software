#!/usr/bin/env python3
"""SetupTab — Advanced Radio, Audio Tools, Profile, Bootstrap.

Sections:
  Left  : Advanced radio settings (filters, volume, CTCSS/DCS detail)
          PTT configuration
          APRS TX advanced options
  Right : Audio tools (test tone, manual APRS packet)
          Profile management
          Bootstrap / diagnostics
"""

from __future__ import annotations

import platform as _platform
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import TYPE_CHECKING

from ..engine.sa818_client import CTCSS
from .widgets import Tooltip, add_row, scrollable_frame

if TYPE_CHECKING:
    from ..app import HamHatApp


class SetupTab(ttk.Frame):
    """Advanced setup and tools tab."""

    def __init__(self, parent: ttk.Notebook, app: "HamHatApp") -> None:
        super().__init__(parent)
        self._app = app
        self._build()

    # ------------------------------------------------------------------
    # Build layout
    # ------------------------------------------------------------------

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        pane = ttk.PanedWindow(self, orient="horizontal")
        pane.grid(row=0, column=0, columnspan=2, sticky="nsew")

        left_host = ttk.Frame(pane)
        right_host = ttk.Frame(pane)
        pane.add(left_host, weight=1)
        pane.add(right_host, weight=1)

        self._build_left(left_host)
        self._build_right(right_host)

    def _build_left(self, parent: ttk.Frame) -> None:
        _canvas, _vsb, inner = scrollable_frame(parent)
        inner.columnconfigure(1, weight=1)

        row = 0

        # ---- Audio Filters ----
        ff = ttk.LabelFrame(inner, text="Audio Filters (uConsole_HAT)", padding=8)
        ff.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        ff.columnconfigure(0, weight=1)
        row += 1

        self._filter_emphasis_var = tk.BooleanVar(value=True)
        self._filter_highpass_var = tk.BooleanVar(value=True)
        self._filter_lowpass_var  = tk.BooleanVar(value=True)

        _cb_emp = ttk.Checkbutton(ff, text="Bypass Pre/De-emphasis",
                                   variable=self._filter_emphasis_var)
        _cb_emp.grid(row=0, column=0, sticky="w")
        Tooltip(_cb_emp,
                "Checked = SA818 bypasses the built-in pre/de-emphasis filter.\n"
                "Usually leave checked for APRS (software modulation handles it).")
        _cb_hp = ttk.Checkbutton(ff, text="Bypass High-pass Filter",
                                  variable=self._filter_highpass_var)
        _cb_hp.grid(row=1, column=0, sticky="w")
        Tooltip(_cb_hp, "Checked = high-pass filter disabled in SA818 hardware.")
        _cb_lp = ttk.Checkbutton(ff, text="Bypass Low-pass Filter",
                                  variable=self._filter_lowpass_var)
        _cb_lp.grid(row=2, column=0, sticky="w")
        Tooltip(_cb_lp, "Checked = low-pass filter disabled in SA818 hardware.")
        _apply_filt_btn = ttk.Button(ff, text="Apply Filters", command=self._apply_filters)
        _apply_filt_btn.grid(row=3, column=0, sticky="ew", pady=(6, 0))
        Tooltip(_apply_filt_btn, "Send AT+SETFILTER to apply the filter configuration to the SA818.")

        # ---- Volume ----
        vf = ttk.LabelFrame(inner, text="Volume", padding=8)
        vf.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        vf.columnconfigure(1, weight=1)
        row += 1

        self._volume_var = tk.IntVar(value=8)
        _vol_hdr = ttk.Frame(vf)
        _vol_hdr.grid(row=0, column=0, columnspan=2, sticky="ew")
        _vol_hdr.columnconfigure(0, weight=1)
        ttk.Label(_vol_hdr, text="Level:").pack(side="left")
        self._vol_val_lbl = ttk.Label(_vol_hdr, text="8", width=3, anchor="w",
                                      foreground="#9cc4dd", font=("TkDefaultFont", 9, "bold"))
        self._vol_val_lbl.pack(side="left", padx=(4, 0))

        def _on_vol_change(*_):
            self._vol_val_lbl.configure(text=str(int(self._volume_var.get())))

        vol_scale = ttk.Scale(vf, from_=1, to=8, orient="horizontal",
                              variable=self._volume_var, length=160,
                              command=lambda v: _on_vol_change())
        vol_scale.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        _min_max = ttk.Frame(vf)
        _min_max.grid(row=2, column=0, columnspan=2, sticky="ew")
        _min_max.columnconfigure(0, weight=1)
        ttk.Label(_min_max, text="1 (min)", foreground="#888888",
                  font=("TkDefaultFont", 7)).pack(side="left")
        ttk.Label(_min_max, text="8 (max)", foreground="#888888",
                  font=("TkDefaultFont", 7)).pack(side="right")
        _set_vol_btn = ttk.Button(vf, text="Set Volume", command=self._set_volume)
        _set_vol_btn.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        Tooltip(_set_vol_btn, "Send AT+DMOSETVOLUME to update the SA818 speaker/headset volume (1–8).")

        # ---- CTCSS / DCS ----
        tf = ttk.LabelFrame(inner, text="CTCSS / DCS Tones", padding=8)
        tf.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        tf.columnconfigure(1, weight=1)
        row += 1

        ctcss_opts = list(CTCSS)

        self._ctcss_tx_var = tk.StringVar(value="None")
        self._ctcss_rx_var = tk.StringVar(value="None")
        self._dcs_tx_var   = tk.StringVar(value="None")
        self._dcs_rx_var   = tk.StringVar(value="None")

        add_row(tf, "CTCSS TX:",
                ttk.Combobox(tf, textvariable=self._ctcss_tx_var,
                             values=ctcss_opts, state="readonly", width=10), row=0)
        add_row(tf, "CTCSS RX:",
                ttk.Combobox(tf, textvariable=self._ctcss_rx_var,
                             values=ctcss_opts, state="readonly", width=10), row=1)
        ttk.Separator(tf, orient="horizontal").grid(row=2, column=0, columnspan=2,
                                                     sticky="ew", pady=4)
        add_row(tf, "DCS TX:",
                ttk.Entry(tf, textvariable=self._dcs_tx_var, width=10), row=3)
        ttk.Label(tf, text="(e.g. 047N or 047I)", foreground="#9cc4dd",
                  font=("TkDefaultFont", 8)).grid(row=3, column=2, sticky="w", padx=(4, 0))
        add_row(tf, "DCS RX:",
                ttk.Entry(tf, textvariable=self._dcs_rx_var, width=10), row=4)
        ttk.Label(tf, text="(None to disable)", foreground="#9cc4dd",
                  font=("TkDefaultFont", 8)).grid(row=5, column=0, columnspan=3, sticky="w", pady=(2, 0))

        # ---- Squelch tail ----
        sf = ttk.LabelFrame(inner, text="Squelch Tail", padding=8)
        sf.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        sf.columnconfigure(0, weight=1)
        row += 1
        self._open_tail_var = tk.BooleanVar(value=False)
        _tail_cb = ttk.Checkbutton(sf, text="Open squelch tail (AT+SETTAIL=1)",
                                    variable=self._open_tail_var)
        _tail_cb.grid(row=0, column=0, sticky="w")
        Tooltip(_tail_cb,
                "When checked, the SA818 holds the squelch open briefly after a signal ends.\n"
                "Useful for receiving full APRS packet tails.")
        _tail_btn = ttk.Button(sf, text="Apply Tail", command=self._apply_tail)
        _tail_btn.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        Tooltip(_tail_btn, "Send AT+SETTAIL to apply the squelch tail setting.")

        # ---- PTT ----
        # Bind directly to shared vars defined in app.py (same as main_tab.py)
        # This avoids a collect_profile conflict where two tabs write the same AppProfile fields.
        pf = ttk.LabelFrame(inner, text="PTT Configuration", padding=8)
        pf.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        pf.columnconfigure(1, weight=1)
        row += 1

        ttk.Checkbutton(pf, text="PTT Enabled",
                        variable=self._app.ptt_enabled_var).grid(
            row=0, column=0, columnspan=2, sticky="w")
        add_row(pf, "Line:", ttk.Combobox(pf, textvariable=self._app.ptt_line_var,
                values=["RTS", "DTR"], state="readonly", width=8), row=1)
        ttk.Checkbutton(pf, text="Active High (normal polarity)",
                        variable=self._app.ptt_active_high_var).grid(
            row=2, column=0, columnspan=2, sticky="w")
        add_row(pf, "Pre-delay (ms):",
                ttk.Spinbox(pf, textvariable=self._app.ptt_pre_ms_var,
                            from_=0, to=2000, width=8), row=3)
        add_row(pf, "Post-delay (ms):",
                ttk.Spinbox(pf, textvariable=self._app.ptt_post_ms_var,
                            from_=0, to=2000, width=8), row=4)

        # ---- APRS TX advanced ----
        # Bind to shared vars (same as comms_tab.py) to avoid collect_profile conflicts.
        af = ttk.LabelFrame(inner, text="APRS TX Advanced", padding=8)
        af.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        af.columnconfigure(1, weight=1)
        row += 1

        add_row(af, "Destination:",
                ttk.Entry(af, textvariable=self._app.aprs_dest_var, width=12), row=0)
        add_row(af, "Path:",
                ttk.Entry(af, textvariable=self._app.aprs_path_var, width=16), row=1)
        ttk.Checkbutton(af, text="Re-program radio before each TX",
                        variable=self._app.aprs_reinit_var).grid(
            row=2, column=0, columnspan=2, sticky="w")
        add_row(af, "Preamble flags:",
                ttk.Spinbox(af, textvariable=self._app.aprs_preamble_var,
                            from_=10, to=500, width=8), row=3)
        add_row(af, "TX repeats:",
                ttk.Spinbox(af, textvariable=self._app.aprs_repeats_var,
                            from_=1, to=5, width=8), row=4)
        add_row(af, "TX gain (0.01-1.0):",
                ttk.Spinbox(af, textvariable=self._app.aprs_tx_gain_var,
                            from_=0.01, to=1.0, increment=0.01, format="%.2f", width=8), row=5)
        add_row(af, "ACK timeout (s):",
                ttk.Spinbox(af, textvariable=self._app.aprs_ack_timeout_var,
                            from_=5.0, to=120.0, increment=1.0, width=8), row=6)
        add_row(af, "ACK retries:",
                ttk.Spinbox(af, textvariable=self._app.aprs_ack_retries_var,
                            from_=1, to=10, width=8), row=7)

        # ---- RX Monitor advanced ----
        # Bind to shared vars (same as aprs_tab.py) to avoid collect_profile conflicts.
        rf = ttk.LabelFrame(inner, text="APRS RX Advanced", padding=8)
        rf.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        rf.columnconfigure(1, weight=1)
        row += 1

        add_row(rf, "Monitor duration (s):",
                ttk.Spinbox(rf, textvariable=self._app.aprs_rx_dur_var,
                            from_=2.0, to=120.0, increment=1.0, width=8), row=0)
        add_row(rf, "Chunk size (s):",
                ttk.Spinbox(rf, textvariable=self._app.aprs_rx_chunk_var,
                            from_=1.0, to=30.0, increment=0.5, width=8), row=1)
        add_row(rf, "Trim threshold (dB):",
                ttk.Spinbox(rf, textvariable=self._app.aprs_rx_trim_var,
                            from_=-40.0, to=0.0, increment=1.0, width=8), row=2)
        add_row(rf, "OS mic level (0-100):",
                ttk.Spinbox(rf, textvariable=self._app.aprs_rx_os_level_var,
                            from_=0, to=100, width=8), row=3)

    def _build_right(self, parent: ttk.Frame) -> None:
        _canvas, _vsb, inner = scrollable_frame(parent)
        inner.columnconfigure(1, weight=1)

        row = 0

        # ---- Audio routing helpers ----
        ah = ttk.LabelFrame(inner, text="Audio Routing Helpers", padding=8)
        ah.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        ah.columnconfigure(0, weight=1)
        row += 1

        _pair_btn = ttk.Button(ah, text="⬡ Auto-Find TX/RX Pair",
                                command=self._app.auto_find_audio_pair)
        _pair_btn.grid(row=0, column=0, sticky="ew")
        Tooltip(_pair_btn,
                "Searches for a USB audio device with both an output (TX) and input (RX)\n"
                "channel and selects them automatically.")
        _auto_cb = ttk.Checkbutton(ah, text="Auto-select USB audio pair on connect",
                                    variable=self._app.auto_audio_var)
        _auto_cb.grid(row=1, column=0, sticky="w", pady=(6, 0))
        Tooltip(_auto_cb,
                "When enabled, the app finds the best USB audio pair every time it\n"
                "connects to the radio, without requiring a manual selection.")

        # ---- Test tone ----
        tf = ttk.LabelFrame(inner, text="Audio Tools — Test Tone", padding=8)
        tf.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        tf.columnconfigure(1, weight=1)
        row += 1

        self._tone_freq_var     = tk.DoubleVar(value=1200.0)
        self._tone_duration_var = tk.DoubleVar(value=2.0)

        add_row(tf, "Frequency (Hz):",
                ttk.Spinbox(tf, textvariable=self._tone_freq_var,
                            from_=100.0, to=3000.0, increment=100.0, format="%.0f", width=10), row=0)
        add_row(tf, "Duration (s):",
                ttk.Spinbox(tf, textvariable=self._tone_duration_var,
                            from_=0.5, to=30.0, increment=0.5, format="%.1f", width=10), row=1)

        btn_row = ttk.Frame(tf)
        btn_row.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        btn_row.columnconfigure(0, weight=1)
        btn_row.columnconfigure(1, weight=1)
        _play_tone_btn = ttk.Button(btn_row, text="▶ Play Test Tone",
                                     command=self._play_test_tone)
        _play_tone_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        Tooltip(_play_tone_btn,
                "Play a sine wave at the specified frequency through the TX output device.\n"
                "Useful to verify audio routing before transmitting.")
        _stop_btn = ttk.Button(btn_row, text="■ Stop Audio",
                                command=self._stop_audio)
        _stop_btn.grid(row=0, column=1, sticky="ew")
        Tooltip(_stop_btn, "Stop any audio that is currently playing.")

        # ---- Manual APRS packet ----
        mf = ttk.LabelFrame(inner, text="Audio Tools — Manual APRS Packet", padding=8)
        mf.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        mf.columnconfigure(1, weight=1)
        row += 1

        self._manual_aprs_var = tk.StringVar(value="uConsole HAM HAT test")
        add_row(mf, "Packet text:", ttk.Entry(mf, textvariable=self._manual_aprs_var), row=0)
        _enc_btn = ttk.Button(mf, text="▶ Encode & Play (no PTT)",
                               command=self._play_manual_aprs)
        _enc_btn.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        Tooltip(_enc_btn,
                "AFSK-encodes the packet text and plays it through the TX output device.\n"
                "PTT is NOT asserted — useful to hear what a packet sounds like.")

        # ---- Tone sweep / channel detection ----
        sf = ttk.LabelFrame(inner, text="TX Tone Sweep (channel detection)", padding=8)
        sf.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        sf.columnconfigure(0, weight=1)
        row += 1

        ttk.Label(sf, text="Sweeps 1200–2200 Hz to detect RX channel.\nListens for echo on input device.",
                  foreground="#9cc4dd", font=("TkDefaultFont", 8)).grid(
            row=0, column=0, columnspan=2, sticky="w")
        _sweep_btn = ttk.Button(sf, text="▶ Run TX Channel Sweep",
                                 command=self._tx_channel_sweep)
        _sweep_btn.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        Tooltip(_sweep_btn,
                "Plays tones at multiple frequencies through every output device while\n"
                "recording on the input device. Identifies which output/input pair\n"
                "forms the correct audio loopback through the radio.")

        # ---- PTT Diagnostics ----
        pttd = ttk.LabelFrame(inner, text="PTT Diagnostics", padding=8)
        pttd.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        pttd.columnconfigure(0, weight=1)
        row += 1
        ttk.Label(pttd,
                  text="Tests the configured PTT line (active-high, then active-low) — 1.5 s each.\n"
                       "Watch your radio for a carrier; note which polarity keys it.\n"
                       "Only the line set in your Profile is tested. uConsole_HAT mode only.",
                  foreground="#9cc4dd", font=("TkDefaultFont", 8)).grid(
            row=0, column=0, columnspan=2, sticky="w")
        _ptt_diag_btn = ttk.Button(pttd, text="▶ Run PTT Diagnostics",
                                    command=self._ptt_diagnostics)
        _ptt_diag_btn.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        Tooltip(_ptt_diag_btn,
                "Tests the PTT line configured in your Profile in both polarities\n"
                "(active-high then active-low, 1.5 s each). The other modem-control\n"
                "line is not probed — exercising it can reset composite USB radio\n"
                "interfaces. Watch your radio or a nearby receiver for a carrier.")

        # ---- Auto RX detect ----
        arf = ttk.LabelFrame(inner, text="Auto-detect RX Level", padding=8)
        arf.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        arf.columnconfigure(0, weight=1)
        row += 1

        ttk.Label(arf, text="Captures audio and suggests OS microphone level\nfor best APRS decode SNR.",
                  foreground="#9cc4dd", font=("TkDefaultFont", 8)).grid(
            row=0, column=0, columnspan=2, sticky="w")
        _rx_lvl_btn = ttk.Button(arf, text="▶ Auto-detect RX Level",
                                  command=self._auto_detect_rx)
        _rx_lvl_btn.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        Tooltip(_rx_lvl_btn,
                "Records a few seconds of audio from the RX input device and\n"
                "suggests an OS microphone gain level for optimal APRS decoding.")

        # ---- Profile management ----
        pf = ttk.LabelFrame(inner, text="Profile Management", padding=8)
        pf.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        pf.columnconfigure(0, weight=1)
        pf.columnconfigure(1, weight=1)
        pf.columnconfigure(2, weight=1)
        row += 1

        _exp_btn = ttk.Button(pf, text="⬆ Export…", command=self._save_profile)
        _exp_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        Tooltip(_exp_btn, "Save the current profile to a JSON file of your choice.")
        _imp_btn = ttk.Button(pf, text="⬇ Import…", command=self._load_profile)
        _imp_btn.grid(row=0, column=1, sticky="ew", padx=4)
        Tooltip(_imp_btn, "Load a previously exported profile JSON file.")
        _rst_btn = ttk.Button(pf, text="↺ Reset Defaults", command=self._reset_defaults)
        _rst_btn.grid(row=0, column=2, sticky="ew", padx=(4, 0))
        Tooltip(_rst_btn, "Reset ALL settings to factory defaults. Cannot be undone.")

        # ---- Bootstrap ----
        bf = ttk.LabelFrame(inner, text="Bootstrap / Diagnostics", padding=8)
        bf.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        bf.columnconfigure(0, weight=1)
        row += 1

        _boot_btn = ttk.Button(bf, text="Install / Update Dependencies",
                                command=self._bootstrap)
        _boot_btn.grid(row=0, column=0, sticky="ew")
        Tooltip(_boot_btn,
                "Runs pip to install or update sounddevice, pyserial, numpy and other\n"
                "required packages. Safe to run at any time.")
        _diag_btn = ttk.Button(bf, text="Run Two-Radio Diagnostic",
                                command=self._two_radio_diagnostic)
        _diag_btn.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        Tooltip(_diag_btn,
                "Cycles through both connected radios and verifies audio routing.\n"
                "Useful when two HAT radios are attached to the same system.")

        # ---- TTS / Speech (Windows only) ----
        # Only shown on Windows — the backend uses PowerShell SpeechSynthesizer
        # which is not available on Linux/macOS/RPi.
        self._tts_enabled_var = tk.BooleanVar(value=False)
        if _platform.system().lower() == "windows":
            tsf = ttk.LabelFrame(inner, text="Text-to-Speech (optional, Windows only)", padding=8)
            tsf.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
            row += 1

            ttk.Checkbutton(tsf, text="Announce received APRS messages via TTS",
                            variable=self._tts_enabled_var).pack(anchor="w")
            ttk.Label(tsf,
                      text="Uses Windows PowerShell SpeechSynthesizer.\nRequires no additional dependencies.",
                      foreground="#9cc4dd", font=("TkDefaultFont", 8)).pack(anchor="w", pady=(4, 0))

    # ------------------------------------------------------------------
    # Action handlers
    # ------------------------------------------------------------------

    def _apply_filters(self) -> None:
        self._app.apply_filters(
            self._filter_emphasis_var.get(),
            self._filter_highpass_var.get(),
            self._filter_lowpass_var.get(),
        )

    def _set_volume(self) -> None:
        self._app.set_volume(int(self._volume_var.get()))

    def _apply_tail(self) -> None:
        self._app.apply_tail(self._open_tail_var.get())

    def _play_test_tone(self) -> None:
        self._app.play_test_tone(
            freq=float(self._tone_freq_var.get()),
            duration=float(self._tone_duration_var.get()),
        )

    def _stop_audio(self) -> None:
        self._app.stop_audio()

    def _play_manual_aprs(self) -> None:
        self._app.play_manual_aprs_packet(self._manual_aprs_var.get())

    def _tx_channel_sweep(self) -> None:
        self._app.tx_channel_sweep()

    def _auto_detect_rx(self) -> None:
        self._app.auto_detect_rx()

    def _ptt_diagnostics(self) -> None:
        self._app.ptt_diagnostics()

    def _save_profile(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Save Profile",
            defaultextension=".json",
            filetypes=[("JSON Profile", "*.json"), ("All Files", "*.*")],
        )
        if path:
            self._app.save_profile(path)

    def _load_profile(self) -> None:
        path = filedialog.askopenfilename(
            parent=self,
            title="Load Profile",
            filetypes=[("JSON Profile", "*.json"), ("All Files", "*.*")],
        )
        if path:
            self._app.load_profile(path)

    def _reset_defaults(self) -> None:
        if messagebox.askyesno("Reset Defaults", "Reset all settings to factory defaults?",
                               parent=self):
            self._app.reset_defaults()

    def _bootstrap(self) -> None:
        self._app.run_bootstrap()

    def _two_radio_diagnostic(self) -> None:
        self._app.run_two_radio_diagnostic()

    # ------------------------------------------------------------------
    # Profile integration
    # ------------------------------------------------------------------

    def apply_profile(self, p) -> None:
        """Load profile values into setup tab widgets.

        Note: PTT, APRS TX advanced, and APRS RX advanced fields are NOT loaded
        here — they use shared vars (self._app.*_var) populated by main_tab and
        aprs_tab respectively, so they're already correct before this runs.
        """
        self._filter_emphasis_var.set(getattr(p, "disable_emphasis", True))
        self._filter_highpass_var.set(getattr(p, "disable_highpass", True))
        self._filter_lowpass_var.set(getattr(p, "disable_lowpass", True))
        vol = int(getattr(p, "volume", 8))
        self._volume_var.set(vol)
        try:
            self._vol_val_lbl.configure(text=str(vol))
        except Exception:
            pass

        self._ctcss_tx_var.set(getattr(p, "ctcss_tx", "") or "None")
        self._ctcss_rx_var.set(getattr(p, "ctcss_rx", "") or "None")
        self._dcs_tx_var.set(getattr(p, "dcs_tx", "") or "None")
        self._dcs_rx_var.set(getattr(p, "dcs_rx", "") or "None")

        self._open_tail_var.set(False)  # not persisted separately

        self._tone_freq_var.set(float(getattr(p, "test_tone_freq", 1200.0)))
        self._tone_duration_var.set(float(getattr(p, "test_tone_duration", 2.0)))
        self._manual_aprs_var.set(getattr(p, "manual_aprs_text", "uConsole HAM HAT test"))

    def collect_profile(self, p) -> None:
        """Write setup tab widget values back into profile object.

        PTT, APRS TX advanced, and APRS RX advanced fields are NOT written here —
        they are owned by main_tab and aprs_tab (shared vars) and already saved by
        those tabs' collect_profile calls earlier in the collection chain.
        """
        p.disable_emphasis = self._filter_emphasis_var.get()
        p.disable_highpass = self._filter_highpass_var.get()
        p.disable_lowpass  = self._filter_lowpass_var.get()
        p.volume           = int(self._volume_var.get())

        ctcss_tx = self._ctcss_tx_var.get()
        ctcss_rx = self._ctcss_rx_var.get()
        p.ctcss_tx = "" if ctcss_tx == "None" else ctcss_tx
        p.ctcss_rx = "" if ctcss_rx == "None" else ctcss_rx
        p.dcs_tx   = "" if self._dcs_tx_var.get() in ("None", "") else self._dcs_tx_var.get()
        p.dcs_rx   = "" if self._dcs_rx_var.get() in ("None", "") else self._dcs_rx_var.get()

        p.test_tone_freq     = float(self._tone_freq_var.get())
        p.test_tone_duration = float(self._tone_duration_var.get())
        p.manual_aprs_text   = self._manual_aprs_var.get()

    @property
    def tts_enabled(self) -> bool:
        return self._tts_enabled_var.get()

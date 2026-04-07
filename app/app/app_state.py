#!/usr/bin/env python3
"""AppState — shared application state (tk.Var containers + engine instances)."""

from __future__ import annotations

import queue
import shutil
import tkinter as tk
from pathlib import Path

from .engine.aprs_engine import AprsEngine
from .engine.audio_router import AudioRouter
from .engine.comms_mgr import CommsManager
from .engine.mesh_mgr import MeshManager
from .engine.pakt import PaktService
from .engine.platform_paths import get_user_data_dir
from .engine.profile import ProfileManager
from .engine.radio_ctrl import RadioController
from .engine.tile_provider import TileProvider


class AppState:
    """A container for shared application state."""

    def __init__(self, app_dir: Path) -> None:
        self.app_dir = app_dir

        # Use cross-platform user data directory for mutable files (profiles,
        # audio output) so that the app works correctly when installed outside
        # the source tree (e.g. a signed macOS .app bundle or a Linux system
        # install where the source directory is read-only).
        #
        # Falls back to app_dir-relative paths when the platform helper returns
        # the fallback, which preserves the existing behaviour for local dev
        # runs where app_dir is writable.
        _user_data = get_user_data_dir("HamHatCC", fallback_dir=app_dir)
        self.user_data_dir = _user_data

        self.audio_dir = _user_data / "audio_out"
        self.profile_path = _user_data / "profiles" / "last_profile.json"
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.profile_path.parent.mkdir(parents=True, exist_ok=True)

        # Upgrade-safe profile migration: if the new user-data location has no
        # profile yet but a legacy in-tree profile exists, copy it forward.
        legacy_profile_path = app_dir / "profiles" / "last_profile.json"
        if self.profile_path != legacy_profile_path:
            if not self.profile_path.exists() and legacy_profile_path.exists():
                try:
                    shutil.copy2(legacy_profile_path, self.profile_path)
                except Exception:
                    # Best-effort migration only; ProfileManager will still
                    # fall back cleanly if the copy or the legacy file is bad.
                    pass

        # --- Engine components ---
        self.radio = RadioController()
        self.audio = AudioRouter(app_dir, audio_dir=self.audio_dir)
        self.aprs = AprsEngine(self.radio, self.audio, self.audio_dir)
        self.comms = CommsManager()
        self.pakt = PaktService()
        self.prof = ProfileManager(self.profile_path)
        self.tiles = TileProvider(app_dir / "tiles")
        # Mesh manager — local_call_provider wired after AppState is passed to app
        self.mesh: MeshManager = MeshManager(local_call_provider=lambda: "N0CALL-0")

        # --- Thread-safe event queue ---
        self.evq: queue.Queue = queue.Queue()

        # --- Tk vars ---
        self.port_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.frequency_var = tk.StringVar(value="145.070")
        self.offset_var = tk.StringVar(value="0.000")
        self.squelch_var = tk.StringVar(value="4")
        self.bandwidth_var = tk.StringVar(value="Wide")
        self.audio_out_var = tk.StringVar()
        self.audio_in_var = tk.StringVar()
        self.auto_audio_var = tk.BooleanVar(value=True)
        self.ptt_enabled_var = tk.BooleanVar(value=True)
        self.ptt_line_var = tk.StringVar(value="RTS")
        self.ptt_active_high_var = tk.BooleanVar(value=True)
        self.ptt_pre_ms_var = tk.StringVar(value="400")
        self.ptt_post_ms_var = tk.StringVar(value="120")
        self.aprs_source_var = tk.StringVar(value="N0CALL-0")
        self.aprs_dest_var = tk.StringVar(value="APRS")
        self.aprs_path_var = tk.StringVar(value="WIDE1-1")
        self.aprs_tx_gain_var = tk.StringVar(value="0.34")
        self.aprs_preamble_var = tk.StringVar(value="60")
        self.aprs_repeats_var = tk.StringVar(value="1")
        self.aprs_reinit_var = tk.BooleanVar(value=True)
        self.aprs_symbol_table_var = tk.StringVar(value="/")
        self.aprs_symbol_var = tk.StringVar(value=">")
        self.aprs_msg_to_var = tk.StringVar(value="N0CALL-1")
        self.aprs_msg_text_var = tk.StringVar()
        self.aprs_msg_id_var = tk.StringVar()
        self.aprs_reliable_var = tk.BooleanVar(value=False)
        self.aprs_ack_timeout_var = tk.StringVar(value="30.0")
        self.aprs_ack_retries_var = tk.StringVar(value="4")
        self.aprs_auto_ack_var = tk.BooleanVar(value=True)
        self.aprs_lat_var = tk.StringVar(value="49.2827")
        self.aprs_lon_var = tk.StringVar(value="-123.1207")
        self.aprs_comment_var = tk.StringVar(value="uConsole HAM HAT")
        self.aprs_rx_dur_var = tk.StringVar(value="10.0")
        self.aprs_rx_chunk_var = tk.StringVar(value="8.0")
        self.aprs_rx_trim_var = tk.DoubleVar(value=-12.0)
        self.rx_clip_var = tk.StringVar(value="—")
        self.aprs_rx_level_var = tk.StringVar(value="—")   # input level (separate from clip)
        self.aprs_rx_os_level_var = tk.IntVar(value=35)
        self.aprs_rx_auto_var = tk.BooleanVar(value=True)

        # --- Hardware mode (uConsole_HAT, DigiRig, or PAKT) ---
        self.hardware_mode_var = tk.StringVar(value="uConsole_HAT")
        self.digirig_port_var = tk.StringVar(value="")
        self.pakt_device_var = tk.StringVar(value="")
        self.pakt_address_var = tk.StringVar(value="")
        self.pakt_callsign_var = tk.StringVar(value="")
        self.pakt_ssid_var = tk.StringVar(value="0")
        self.pakt_capabilities_var = tk.StringVar(value="not connected")
        self.pakt_status_var = tk.StringVar(value="idle")
        self.pakt_last_config_var = tk.StringVar(value="")
        self.pakt_last_tx_result_var = tk.StringVar(value="")

        # --- Mesh (Test) ---
        self.mesh_enabled_var        = tk.BooleanVar(value=False)
        self.mesh_node_role_var      = tk.StringVar(value="ENDPOINT")
        self.mesh_default_ttl_var    = tk.IntVar(value=4)
        self.mesh_rate_limit_ppm_var = tk.IntVar(value=20)
        self.mesh_hello_enabled_var  = tk.BooleanVar(value=False)
        self.mesh_route_expiry_var   = tk.IntVar(value=600)

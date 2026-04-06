"""screens/setup_screen.py — Profile management and device configuration.

Features:
  • Profile load / save / reset to defaults
  • Radio parameter fine-tuning (CTCSS/DCS, filters, PTT)
  • PAKT callsign and SSID
  • Audio output/input level settings
  • App information / version

This screen is the Android equivalent of the desktop Setup tab.
"""

from __future__ import annotations

import logging

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.snackbar import Snackbar

_log = logging.getLogger(__name__)

Builder.load_string("""
<SetupScreen>:
    name: "setup"
    ScrollView:
        MDBoxLayout:
            orientation: "vertical"
            padding: dp(8)
            spacing: dp(8)
            size_hint_y: None
            height: self.minimum_height

            # ── Profile section ───────────────────────────────────────
            MDCard:
                radius: [dp(8)]
                padding: dp(12)
                size_hint_y: None
                height: self.minimum_height
                MDBoxLayout:
                    orientation: "vertical"
                    spacing: dp(8)
                    size_hint_y: None
                    height: self.minimum_height

                    MDLabel:
                        text: "Profile"
                        font_style: "Subtitle1"
                        bold: True
                        size_hint_y: None
                        height: dp(24)

                    MDLabel:
                        id: lbl_profile_path
                        text: root.profile_path_text
                        font_style: "Caption"
                        size_hint_y: None
                        height: dp(20)

                    MDBoxLayout:
                        size_hint_y: None
                        height: dp(44)
                        spacing: dp(8)
                        MDRaisedButton:
                            text: "Save"
                            size_hint_x: 1
                            on_release: root.save_profile()
                        MDRaisedButton:
                            text: "Load"
                            size_hint_x: 1
                            on_release: root.load_profile_from_disk()
                        MDFlatButton:
                            text: "Defaults"
                            size_hint_x: 1
                            on_release: root.reset_to_defaults()

            # ── PTT configuration ─────────────────────────────────────
            MDCard:
                radius: [dp(8)]
                padding: dp(12)
                size_hint_y: None
                height: self.minimum_height
                MDBoxLayout:
                    orientation: "vertical"
                    spacing: dp(8)
                    size_hint_y: None
                    height: self.minimum_height

                    MDLabel:
                        text: "PTT Settings"
                        font_style: "Subtitle1"
                        bold: True
                        size_hint_y: None
                        height: dp(24)

                    MDBoxLayout:
                        size_hint_y: None
                        height: dp(40)
                        MDLabel:
                            text: "PTT via serial RTS/DTR"
                        MDSwitch:
                            id: sw_ptt
                            active: True

                    MDDropDownItem:
                        id: dd_ptt_line
                        text: "RTS"
                        size_hint_y: None
                        height: dp(40)
                        font_size: dp(14)

                    MDBoxLayout:
                        size_hint_y: None
                        height: dp(56)
                        spacing: dp(8)
                        MDTextField:
                            id: tf_ptt_pre
                            hint_text: "Pre-PTT delay (ms)"
                            text: "400"
                            input_filter: "int"
                        MDTextField:
                            id: tf_ptt_post
                            hint_text: "Post-PTT delay (ms)"
                            text: "120"
                            input_filter: "int"

            # ── APRS tuning ───────────────────────────────────────────
            MDCard:
                radius: [dp(8)]
                padding: dp(12)
                size_hint_y: None
                height: self.minimum_height
                MDBoxLayout:
                    orientation: "vertical"
                    spacing: dp(8)
                    size_hint_y: None
                    height: self.minimum_height

                    MDLabel:
                        text: "APRS Tuning"
                        font_style: "Subtitle1"
                        bold: True
                        size_hint_y: None
                        height: dp(24)

                    MDTextField:
                        id: tf_path
                        hint_text: "APRS path (e.g. WIDE1-1)"
                        text: "WIDE1-1"
                        size_hint_y: None
                        height: dp(56)

                    MDTextField:
                        id: tf_symbol
                        hint_text: "Symbol (table/code e.g. />)"
                        text: "/>"
                        size_hint_y: None
                        height: dp(56)

                    MDBoxLayout:
                        size_hint_y: None
                        height: dp(56)
                        spacing: dp(8)
                        MDTextField:
                            id: tf_tx_gain
                            hint_text: "TX gain (0.0–1.0)"
                            input_filter: "float"
                            text: "0.34"
                        MDTextField:
                            id: tf_preamble
                            hint_text: "Preamble flags"
                            input_filter: "int"
                            text: "60"

            # ── PAKT / BLE config ─────────────────────────────────────
            MDCard:
                radius: [dp(8)]
                padding: dp(12)
                size_hint_y: None
                height: self.minimum_height
                MDBoxLayout:
                    orientation: "vertical"
                    spacing: dp(8)
                    size_hint_y: None
                    height: self.minimum_height

                    MDLabel:
                        text: "PAKT Configuration"
                        font_style: "Subtitle1"
                        bold: True
                        size_hint_y: None
                        height: dp(24)

                    MDBoxLayout:
                        size_hint_y: None
                        height: dp(56)
                        spacing: dp(8)
                        MDTextField:
                            id: tf_pakt_cs
                            hint_text: "PAKT callsign"
                            text: ""
                        MDTextField:
                            id: tf_pakt_ssid
                            hint_text: "SSID (0-15)"
                            input_filter: "int"
                            text: "0"

                    MDTextField:
                        id: tf_pakt_name
                        hint_text: "PAKT device name (for auto-reconnect)"
                        size_hint_y: None
                        height: dp(56)

            # ── Audio test tone ───────────────────────────────────────
            MDCard:
                radius: [dp(8)]
                padding: dp(12)
                size_hint_y: None
                height: self.minimum_height
                MDBoxLayout:
                    orientation: "vertical"
                    spacing: dp(8)
                    size_hint_y: None
                    height: self.minimum_height

                    MDLabel:
                        text: "Audio Test"
                        font_style: "Subtitle1"
                        bold: True
                        size_hint_y: None
                        height: dp(24)

                    MDBoxLayout:
                        size_hint_y: None
                        height: dp(56)
                        spacing: dp(8)
                        MDTextField:
                            id: tf_tone_freq
                            hint_text: "Tone freq (Hz)"
                            input_filter: "float"
                            text: "1200.0"
                        MDTextField:
                            id: tf_tone_dur
                            hint_text: "Duration (s)"
                            input_filter: "float"
                            text: "2.0"

                    MDRaisedButton:
                        text: "Play Test Tone"
                        size_hint_y: None
                        height: dp(40)
                        on_release: root.play_test_tone()

            # ── App info ──────────────────────────────────────────────
            MDCard:
                radius: [dp(8)]
                padding: dp(12)
                size_hint_y: None
                height: self.minimum_height
                MDBoxLayout:
                    orientation: "vertical"
                    spacing: dp(4)
                    size_hint_y: None
                    height: self.minimum_height

                    MDLabel:
                        text: "HAM HAT Control Center v4.0"
                        font_style: "Subtitle1"
                        size_hint_y: None
                        height: dp(24)
                    MDLabel:
                        text: "Android client — PAKT BLE + SA818 USB OTG"
                        font_style: "Caption"
                        size_hint_y: None
                        height: dp(20)
                    MDLabel:
                        text: "github.com/hamhat/ham-radio-hat-software"
                        font_style: "Caption"
                        size_hint_y: None
                        height: dp(20)

                    MDBoxLayout:
                        size_hint_y: None
                        height: dp(44)
                        padding: [0, dp(8), 0, 0]

            # bottom padding for nav bar
            MDBoxLayout:
                size_hint_y: None
                height: dp(72)
""")


class SetupScreen(MDScreen):
    """Settings and profile management screen."""

    profile_path_text = StringProperty("Profile: (not loaded)")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._profile = None
        self._profile_manager = None
        self._confirm_dialog: MDDialog | None = None

    # ── profile wiring ────────────────────────────────────────────────────────

    def set_profile_manager(self, pm) -> None:
        self._profile_manager = pm

    def load_profile(self, profile) -> None:
        self._profile = profile
        ids = self.ids
        ids.sw_ptt.active        = profile.ptt_enabled
        ids.dd_ptt_line.set_item(profile.ptt_line)
        ids.tf_ptt_pre.text      = str(profile.ptt_pre_ms)
        ids.tf_ptt_post.text     = str(profile.ptt_post_ms)
        ids.tf_path.text         = profile.aprs_path
        sym = (profile.aprs_symbol_table or "/") + (profile.aprs_symbol or ">")
        ids.tf_symbol.text       = sym
        ids.tf_tx_gain.text      = str(profile.aprs_tx_gain)
        ids.tf_preamble.text     = str(profile.aprs_preamble_flags)
        ids.tf_pakt_cs.text      = profile.pakt_callsign or ""
        ids.tf_pakt_ssid.text    = str(profile.pakt_ssid)
        ids.tf_pakt_name.text    = profile.pakt_device_name or ""
        ids.tf_tone_freq.text    = str(profile.test_tone_freq)
        ids.tf_tone_dur.text     = str(profile.test_tone_duration)
        if self._profile_manager:
            self.profile_path_text = f"Profile: {self._profile_manager.path}"

    def collect_profile(self, profile) -> None:
        ids = self.ids
        profile.ptt_enabled = ids.sw_ptt.active
        profile.ptt_line    = ids.dd_ptt_line.current_item
        try:
            profile.ptt_pre_ms  = int(ids.tf_ptt_pre.text)
            profile.ptt_post_ms = int(ids.tf_ptt_post.text)
        except ValueError:
            pass
        profile.aprs_path = ids.tf_path.text
        sym = ids.tf_symbol.text
        if len(sym) >= 2:
            profile.aprs_symbol_table = sym[0]
            profile.aprs_symbol       = sym[1]
        try:
            profile.aprs_tx_gain        = float(ids.tf_tx_gain.text)
            profile.aprs_preamble_flags = int(ids.tf_preamble.text)
        except ValueError:
            pass
        profile.pakt_callsign    = ids.tf_pakt_cs.text.strip().upper()
        try:
            profile.pakt_ssid    = int(ids.tf_pakt_ssid.text)
        except ValueError:
            pass
        profile.pakt_device_name = ids.tf_pakt_name.text.strip()
        try:
            profile.test_tone_freq     = float(ids.tf_tone_freq.text)
            profile.test_tone_duration = float(ids.tf_tone_dur.text)
        except ValueError:
            pass

    # ── actions ───────────────────────────────────────────────────────────────

    def save_profile(self) -> None:
        if self._profile is None or self._profile_manager is None:
            Snackbar(text="Profile not loaded").open()
            return
        try:
            self._profile_manager.save(self._profile)
            Snackbar(text="Profile saved").open()
            _log.info("Profile saved to %s", self._profile_manager.path)
        except Exception as exc:
            _log.error("Profile save failed: %s", exc)
            Snackbar(text=f"Save failed: {exc}").open()

    def load_profile_from_disk(self) -> None:
        if self._profile_manager is None:
            Snackbar(text="Profile manager not available").open()
            return
        try:
            p = self._profile_manager.load()
            if p is not None:
                self._profile = p
                self.load_profile(p)
                Snackbar(text="Profile loaded").open()
            else:
                Snackbar(text="No saved profile found — using defaults").open()
        except Exception as exc:
            _log.error("Profile load failed: %s", exc)
            Snackbar(text=f"Load failed: {exc}").open()

    def reset_to_defaults(self) -> None:
        if self._confirm_dialog:
            return
        self._confirm_dialog = MDDialog(
            title="Reset Profile?",
            text="This will reset all settings to factory defaults.",
            buttons=[
                MDFlatButton(
                    text="CANCEL",
                    on_release=lambda x: self._close_dialog(),
                ),
                MDFlatButton(
                    text="RESET",
                    on_release=lambda x: self._do_reset(),
                ),
            ],
        )
        self._confirm_dialog.open()

    def _close_dialog(self) -> None:
        if self._confirm_dialog:
            self._confirm_dialog.dismiss()
            self._confirm_dialog = None

    def _do_reset(self) -> None:
        self._close_dialog()
        try:
            from app.engine.models import AppProfile
            fresh = AppProfile()
            self._profile.__dict__.update(fresh.__dict__)
            self.load_profile(self._profile)
            Snackbar(text="Profile reset to defaults").open()
        except Exception as exc:
            Snackbar(text=f"Reset failed: {exc}").open()

    def play_test_tone(self) -> None:
        from hal import audio_manager
        try:
            freq = float(self.ids.tf_tone_freq.text)
            dur  = float(self.ids.tf_tone_dur.text)
        except ValueError:
            Snackbar(text="Invalid frequency or duration").open()
            return
        import threading
        threading.Thread(
            target=audio_manager.play_tone,
            args=(freq, dur),
            daemon=True,
        ).start()
        Snackbar(text=f"Playing {freq:.0f} Hz for {dur:.1f} s…").open()

"""screens/aprs_screen.py — APRS packet log, position beacon, and messaging.

Features:
  • Scrollable packet log (decoded APRS frames)
  • Position beacon: callsign, lat/lon, symbol, comment
  • Quick-send message to a callsign
  • Manual APRS text packet (for testing)
  • RX toggle (listen for APRS via microphone)
"""

from __future__ import annotations

import logging
import time
from typing import List

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty, NumericProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.list import TwoLineListItem
from kivymd.uix.snackbar import Snackbar

_log = logging.getLogger(__name__)

Builder.load_string("""
<AprsScreen>:
    name: "aprs"
    MDBoxLayout:
        orientation: "vertical"
        padding: dp(8)
        spacing: dp(8)

        # ── Callsign + status row ──────────────────────────────────────
        MDCard:
            size_hint_y: None
            height: dp(56)
            radius: [dp(8)]
            padding: dp(8)
            MDBoxLayout:
                spacing: dp(8)
                MDTextField:
                    id: tf_callsign
                    hint_text: "Your callsign (e.g. N0CALL-9)"
                    text: root.callsign
                    size_hint_y: None
                    height: dp(40)
                MDFlatButton:
                    text: "Save"
                    size_hint: None, None
                    size: dp(60), dp(40)
                    on_release: root.save_callsign()

        # ── Beacon card ───────────────────────────────────────────────
        MDCard:
            size_hint_y: None
            height: self.minimum_height
            radius: [dp(8)]
            padding: dp(12)
            MDBoxLayout:
                orientation: "vertical"
                spacing: dp(6)
                size_hint_y: None
                height: self.minimum_height

                MDLabel:
                    text: "Position Beacon"
                    font_style: "Subtitle1"
                    bold: True
                    size_hint_y: None
                    height: dp(24)

                MDBoxLayout:
                    size_hint_y: None
                    height: dp(56)
                    spacing: dp(8)
                    MDTextField:
                        id: tf_lat
                        hint_text: "Latitude"
                        input_filter: "float"
                        text: root.aprs_lat
                    MDTextField:
                        id: tf_lon
                        hint_text: "Longitude"
                        input_filter: "float"
                        text: root.aprs_lon

                MDTextField:
                    id: tf_comment
                    hint_text: "Beacon comment"
                    text: "uConsole HAM HAT"
                    size_hint_y: None
                    height: dp(56)

                MDBoxLayout:
                    size_hint_y: None
                    height: dp(44)
                    spacing: dp(8)
                    MDRaisedButton:
                        text: "Beacon Now"
                        size_hint_x: 1
                        on_release: root.send_beacon()
                    MDRaisedButton:
                        text: "Get GPS"
                        size_hint_x: None
                        width: dp(96)
                        on_release: root.get_gps_position()

        # ── Quick message ─────────────────────────────────────────────
        MDCard:
            size_hint_y: None
            height: self.minimum_height
            radius: [dp(8)]
            padding: dp(12)
            MDBoxLayout:
                orientation: "vertical"
                spacing: dp(6)
                size_hint_y: None
                height: self.minimum_height

                MDLabel:
                    text: "Send Message"
                    font_style: "Subtitle1"
                    bold: True
                    size_hint_y: None
                    height: dp(24)

                MDBoxLayout:
                    size_hint_y: None
                    height: dp(56)
                    spacing: dp(8)
                    MDTextField:
                        id: tf_msg_to
                        hint_text: "To callsign"
                        text: "N0CALL-1"
                    MDTextField:
                        id: tf_msg_text
                        hint_text: "Message text"

                MDRaisedButton:
                    text: "Send"
                    size_hint_y: None
                    height: dp(40)
                    on_release: root.send_message()

        # ── RX toggle ─────────────────────────────────────────────────
        MDCard:
            size_hint_y: None
            height: dp(56)
            radius: [dp(8)]
            padding: dp(8)
            MDBoxLayout:
                spacing: dp(8)
                MDRaisedButton:
                    id: btn_rx
                    text: "Start RX"
                    size_hint_x: 1
                    on_release: root.toggle_rx()
                MDLabel:
                    id: lbl_rx_status
                    text: "RX idle"
                    font_style: "Caption"

        # ── Packet log ────────────────────────────────────────────────
        MDLabel:
            text: "Received Packets"
            font_style: "Subtitle2"
            size_hint_y: None
            height: dp(24)

        ScrollView:
            MDList:
                id: packet_list
                size_hint_y: None
                height: self.minimum_height
""")


class AprsScreen(MDScreen):
    """APRS screen: beacon, message send, packet log."""

    callsign = StringProperty("N0CALL-9")
    aprs_lat  = StringProperty("49.2827")
    aprs_lon  = StringProperty("-123.1207")

    # packet log entries: list of (time_str, decoded_str)
    _packets: List[tuple] = []
    _rx_active = False
    _msg_id_counter = 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._profile     = None
        self._aprs_modem  = None   # AprsModemBridge — set by main.py
        self._gps_running = False

    # ── profile ───────────────────────────────────────────────────────────────

    def load_profile(self, profile) -> None:
        self._profile = profile
        self.callsign = profile.aprs_source or "N0CALL-9"
        self.aprs_lat = str(profile.aprs_lat)
        self.aprs_lon = str(profile.aprs_lon)
        self.ids.tf_comment.text  = profile.aprs_comment or ""
        self.ids.tf_msg_to.text   = profile.aprs_msg_to or ""
        self.ids.tf_msg_text.text = profile.aprs_msg_text or ""

    def collect_profile(self, profile) -> None:
        try:
            profile.aprs_lat = float(self.ids.tf_lat.text)
        except ValueError:
            pass
        try:
            profile.aprs_lon = float(self.ids.tf_lon.text)
        except ValueError:
            pass
        profile.aprs_source  = self.ids.tf_callsign.text.strip().upper()
        profile.aprs_comment = self.ids.tf_comment.text
        profile.aprs_msg_to  = self.ids.tf_msg_to.text.strip().upper()
        profile.aprs_msg_text = self.ids.tf_msg_text.text

    # ── modem wiring ──────────────────────────────────────────────────────────

    def set_aprs_modem(self, modem) -> None:
        """Wire an AprsModemBridge from main.py."""
        self._aprs_modem = modem
        modem.on_packet_decoded = self._on_packet_decoded
        modem.on_tx_done        = lambda: Clock.schedule_once(
            lambda dt: Snackbar(text="APRS TX complete").open()
        )
        modem.on_error = lambda msg: Clock.schedule_once(
            lambda dt: Snackbar(text=f"APRS error: {msg}").open()
        )

    def _on_packet_decoded(self, packet) -> None:
        """Called from AprsModemBridge background thread → schedule on main thread."""
        Clock.schedule_once(lambda dt: self._display_packet(packet))

    def _display_packet(self, packet) -> None:
        raw = getattr(packet, "raw", None) or str(packet)
        self.add_packet(f"RX: {raw}")

    # ── beacon / message ──────────────────────────────────────────────────────

    def save_callsign(self) -> None:
        cs = self.ids.tf_callsign.text.strip().upper()
        self.callsign = cs
        if self._profile:
            self._profile.aprs_source = cs
        Snackbar(text=f"Callsign set to {cs}").open()

    def send_beacon(self) -> None:
        try:
            lat = float(self.ids.tf_lat.text)
            lon = float(self.ids.tf_lon.text)
        except ValueError:
            Snackbar(text="Invalid lat/lon").open()
            return

        source  = self.callsign or "N0CALL-9"
        comment = self.ids.tf_comment.text
        path    = "WIDE1-1,WIDE2-1"

        if self._aprs_modem is not None:
            # Use engine modem for proper AX.25 encoding
            from hal.aprs_modem_bridge import build_position_info
            info = build_position_info(
                source=source, lat=lat, lon=lon, comment=comment
            )
            _log.info("APRS beacon TX: %s>APRS,%s:%s", source, path, info)
            self.add_packet(f"TX>{source}: {info[:60]}")
            Snackbar(text="Transmitting beacon…").open()
            self._aprs_modem.transmit(
                source=source, dest="APRS", path=path, info=info
            )
        else:
            # Stub (no modem available)
            lat_d  = abs(lat)
            lat_ns = "N" if lat >= 0 else "S"
            lon_d  = abs(lon)
            lon_ew = "E" if lon >= 0 else "W"
            lat_str = f"{int(lat_d):02d}{(lat_d % 1) * 60:05.2f}{lat_ns}"
            lon_str = f"{int(lon_d):03d}{(lon_d % 1) * 60:05.2f}{lon_ew}"
            info    = f"={lat_str}//{lon_str}>{comment}"
            self.add_packet(f"TX(stub)>{source}: {info}")
            Snackbar(text="Beacon built (no audio modem attached)").open()

    def send_message(self) -> None:
        to_cs   = self.ids.tf_msg_to.text.strip().upper()
        msg_txt = self.ids.tf_msg_text.text.strip()
        if not to_cs or not msg_txt:
            Snackbar(text="Enter destination callsign and message").open()
            return

        source = self.callsign or "N0CALL-9"
        path   = "WIDE1-1,WIDE2-1"

        # Increment msg ID
        AprsScreen._msg_id_counter += 1
        msg_id = str(AprsScreen._msg_id_counter % 10000)

        if self._aprs_modem is not None:
            from hal.aprs_modem_bridge import build_message_info
            info = build_message_info(to_cs, msg_txt, msg_id)
            _log.info("APRS message TX: %s>APRS,%s:%s", source, path, info)
            self.add_packet(f"TX→{to_cs}: {msg_txt} [{msg_id}]")
            Snackbar(text=f"Transmitting to {to_cs}…").open()
            self._aprs_modem.transmit(
                source=source, dest="APRS", path=path, info=info
            )
        else:
            self.add_packet(f"TX(stub)→{to_cs}: {msg_txt}")
            Snackbar(text=f"Message queued (no audio modem attached)").open()

    def get_gps_position(self) -> None:
        """Request GPS fix from the Android location manager."""
        try:
            from kivy.utils import platform
            if platform == "android":
                from android.permissions import request_permissions, Permission  # type: ignore[import]
                request_permissions([Permission.ACCESS_FINE_LOCATION])
                from plyer import gps  # type: ignore[import]
                gps.configure(on_location=self._on_gps_location,
                               on_status=self._on_gps_status)
                gps.start(minTime=1000, minDistance=0)
                Snackbar(text="Getting GPS fix…").open()
            else:
                Snackbar(text="GPS only available on Android device").open()
        except Exception as exc:
            _log.warning("GPS error: %s", exc)
            Snackbar(text=f"GPS unavailable: {exc}").open()

    def _on_gps_location(self, **kwargs) -> None:
        lat = kwargs.get("lat", 0.0)
        lon = kwargs.get("lon", 0.0)
        def _upd(dt):
            self.ids.tf_lat.text = f"{lat:.6f}"
            self.ids.tf_lon.text = f"{lon:.6f}"
            self.aprs_lat = str(lat)
            self.aprs_lon = str(lon)
            Snackbar(text=f"GPS: {lat:.4f}, {lon:.4f}").open()
        Clock.schedule_once(_upd)

    def _on_gps_status(self, **kwargs) -> None:
        _log.debug("GPS status: %s", kwargs)

    # ── RX ────────────────────────────────────────────────────────────────────

    def toggle_rx(self) -> None:
        if self._rx_active:
            self._rx_active = False
            self.ids.btn_rx.text = "Start RX"
            self.ids.lbl_rx_status.text = "RX idle"
            if self._aprs_modem is not None:
                self._aprs_modem.stop_rx()
            Snackbar(text="APRS RX stopped").open()
        else:
            self._rx_active = True
            self.ids.btn_rx.text = "Stop RX"
            self.ids.lbl_rx_status.text = "Listening…"
            if self._aprs_modem is not None:
                self._aprs_modem.start_rx()
                Snackbar(text="APRS RX listening…").open()
            else:
                Snackbar(text="APRS modem not attached").open()

    # ── packet log ────────────────────────────────────────────────────────────

    def add_packet(self, decoded: str) -> None:
        """Add a decoded APRS packet to the scrollable log."""
        ts = time.strftime("%H:%M:%S")
        self._packets.append((ts, decoded))
        item = TwoLineListItem(
            text=ts,
            secondary_text=decoded[:80],
        )
        self.ids.packet_list.add_widget(item, index=0)   # newest at top
        # Keep at most 100 entries
        if len(self._packets) > 100:
            self._packets.pop()
            widgets = self.ids.packet_list.children
            if widgets:
                self.ids.packet_list.remove_widget(widgets[-1])

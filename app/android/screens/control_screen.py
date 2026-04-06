"""screens/control_screen.py — Radio Control screen for Android.

Provides:
  • Hardware mode selection  (SA818 | DigiRig | PAKT)
  • SA818/DigiRig sub-panel: radio parameters (freq/offset/squelch/bandwidth),
    serial port picker, Connect button
  • PAKT sub-panel: BLE scan, device list, connect/disconnect, status chip
  • Audio routing section: output/input device pickers, Refresh button
  • Connection status bar at the top

All engine calls are delegated to platform layer managers that are set
on the screen from main.py after construction.
"""

from __future__ import annotations

import logging
from typing import Optional

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty
from kivy.metrics import dp
from kivymd.uix.screen import MDScreen
from kivymd.uix.list import MDList, TwoLineListItem
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRaisedButton
from kivymd.uix.snackbar import Snackbar

_log = logging.getLogger(__name__)

Builder.load_string("""
<ControlScreen>:
    name: "control"
    MDBoxLayout:
        orientation: "vertical"
        padding: dp(8)
        spacing: dp(8)

        # ── Status chip ───────────────────────────────────────────────
        MDCard:
            size_hint_y: None
            height: dp(48)
            radius: [dp(8)]
            padding: dp(8)
            MDBoxLayout:
                spacing: dp(8)
                MDIcon:
                    icon: root.status_icon
                    theme_text_color: "Custom"
                    text_color: root.status_color
                    size_hint_x: None
                    width: dp(24)
                MDLabel:
                    text: root.status_text
                    font_style: "Body1"

        # ── Hardware mode ─────────────────────────────────────────────
        MDCard:
            size_hint_y: None
            height: dp(72)
            radius: [dp(8)]
            padding: dp(8)
            MDBoxLayout:
                orientation: "vertical"
                spacing: dp(4)
                MDLabel:
                    text: "Hardware Mode"
                    font_style: "Caption"
                    size_hint_y: None
                    height: dp(20)
                MDBoxLayout:
                    spacing: dp(8)
                    MDRaisedButton:
                        id: btn_sa818
                        text: "SA818"
                        size_hint_x: 1
                        on_release: root.set_mode("SA818")
                    MDRaisedButton:
                        id: btn_digirig
                        text: "DigiRig"
                        size_hint_x: 1
                        on_release: root.set_mode("DigiRig")
                    MDRaisedButton:
                        id: btn_pakt
                        text: "PAKT"
                        size_hint_x: 1
                        on_release: root.set_mode("PAKT")

        # ── Scrollable content ─────────────────────────────────────────
        ScrollView:
            MDBoxLayout:
                id: content_box
                orientation: "vertical"
                spacing: dp(8)
                size_hint_y: None
                height: self.minimum_height
                padding: [0, 0, 0, dp(80)]   # space for bottom nav

                # SA818 / DigiRig panel (shown when mode != PAKT)
                MDCard:
                    id: card_serial
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
                            text: "Radio Parameters"
                            font_style: "Subtitle1"
                            bold: True
                            size_hint_y: None
                            height: dp(24)

                        MDTextField:
                            id: tf_freq
                            hint_text: "Frequency (MHz)"
                            input_filter: "float"
                            text: "145.070"
                            size_hint_y: None
                            height: dp(56)

                        MDTextField:
                            id: tf_offset
                            hint_text: "Offset (MHz)"
                            input_filter: "float"
                            text: "0.6"
                            size_hint_y: None
                            height: dp(56)

                        MDBoxLayout:
                            size_hint_y: None
                            height: dp(56)
                            spacing: dp(8)
                            MDTextField:
                                id: tf_squelch
                                hint_text: "Squelch (0-8)"
                                input_filter: "int"
                                text: "4"
                            MDTextField:
                                id: tf_bw
                                hint_text: "Bandwidth"
                                text: "Wide"

                        MDLabel:
                            text: "Serial Port"
                            font_style: "Caption"
                            size_hint_y: None
                            height: dp(20)

                        MDBoxLayout:
                            size_hint_y: None
                            height: dp(48)
                            spacing: dp(8)
                            MDDropDownItem:
                                id: dd_port
                                text: "(scan for ports)"
                                size_hint_x: 1
                            MDFlatButton:
                                text: "Refresh"
                                size_hint_x: None
                                width: dp(80)
                                on_release: root.refresh_serial_ports()

                        MDBoxLayout:
                            size_hint_y: None
                            height: dp(48)
                            spacing: dp(8)
                            MDRaisedButton:
                                text: "Connect"
                                size_hint_x: 1
                                on_release: root.connect_serial()
                            MDFlatButton:
                                text: "Disconnect"
                                size_hint_x: None
                                width: dp(100)
                                on_release: root.disconnect_serial()

                        MDBoxLayout:
                            size_hint_y: None
                            height: dp(48)
                            spacing: dp(8)
                            MDRaisedButton:
                                text: "Apply Radio"
                                size_hint_x: 1
                                on_release: root.apply_radio()
                            MDRaisedButton:
                                text: "Read Version"
                                size_hint_x: 1
                                on_release: root.read_version()

                # PAKT BLE panel (shown when mode == PAKT)
                MDCard:
                    id: card_pakt
                    radius: [dp(8)]
                    padding: dp(12)
                    size_hint_y: None
                    height: self.minimum_height
                    opacity: 0

                    MDBoxLayout:
                        orientation: "vertical"
                        spacing: dp(8)
                        size_hint_y: None
                        height: self.minimum_height

                        MDLabel:
                            text: "PAKT BLE Device"
                            font_style: "Subtitle1"
                            bold: True
                            size_hint_y: None
                            height: dp(24)

                        MDTextField:
                            id: tf_pakt_addr
                            hint_text: "Device address (leave blank to scan)"
                            size_hint_y: None
                            height: dp(56)

                        MDBoxLayout:
                            size_hint_y: None
                            height: dp(48)
                            spacing: dp(8)
                            MDRaisedButton:
                                id: btn_scan
                                text: "Scan BLE"
                                size_hint_x: 1
                                on_release: root.start_ble_scan()
                            MDRaisedButton:
                                id: btn_ble_connect
                                text: "Connect"
                                size_hint_x: 1
                                on_release: root.ble_connect()

                        MDLabel:
                            text: "Found devices:"
                            font_style: "Caption"
                            size_hint_y: None
                            height: dp(20)

                        MDList:
                            id: ble_device_list
                            size_hint_y: None
                            height: self.minimum_height

                # Audio routing (always visible)
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
                            text: "Audio Routing"
                            font_style: "Subtitle1"
                            bold: True
                            size_hint_y: None
                            height: dp(24)

                        MDDropDownItem:
                            id: dd_audio_out
                            text: "(select output)"
                            size_hint_y: None
                            height: dp(40)
                            font_size: dp(14)

                        MDDropDownItem:
                            id: dd_audio_in
                            text: "(select input)"
                            size_hint_y: None
                            height: dp(40)
                            font_size: dp(14)

                        MDRaisedButton:
                            text: "Refresh Audio Devices"
                            on_release: root.refresh_audio()
                            size_hint_y: None
                            height: dp(40)
""")


class ControlScreen(MDScreen):
    """Radio control screen — hardware mode / serial / PAKT / audio."""

    # KV-observable properties
    status_text  = StringProperty("Disconnected")
    status_icon  = StringProperty("radio-tower")
    status_color = ObjectProperty([0.6, 0.6, 0.6, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._mode = "SA818"
        self._ble_mgr    = None    # set by main.py
        self._serial_mgr = None    # set by main.py
        self._radio_ctrl = None    # RadioController — set by main.py
        self._radio_async = None   # RadioControllerAsync — set by main.py
        self._profile    = None    # AppProfile — set by main.py
        self._ble_dialog: Optional[MDDialog] = None
        self._found_devices: list = []
        self._port_list: list = []  # [(device, description)]
        Clock.schedule_once(self._post_init, 0)

    def _post_init(self, _dt) -> None:
        self._update_mode_ui()

    # ── mode switching ────────────────────────────────────────────────────────

    def set_mode(self, mode: str) -> None:
        self._mode = mode
        self._update_mode_ui()
        if self._profile:
            self._profile.hardware_mode = mode

    def _update_mode_ui(self) -> None:
        card_serial = self.ids.get("card_serial")
        card_pakt   = self.ids.get("card_pakt")
        if card_serial is None:
            return
        if self._mode == "PAKT":
            card_serial.opacity = 0
            card_serial.disabled = True
            card_pakt.opacity = 1
            card_pakt.disabled = False
        else:
            card_serial.opacity = 1
            card_serial.disabled = False
            card_pakt.opacity = 0
            card_pakt.disabled = True

    # ── profile population ────────────────────────────────────────────────────

    def load_profile(self, profile) -> None:
        """Populate UI from an AppProfile dataclass instance."""
        self._profile = profile
        ids = self.ids
        ids.tf_freq.text    = str(profile.frequency)
        ids.tf_offset.text  = str(profile.offset)
        ids.tf_squelch.text = str(profile.squelch)
        ids.tf_bw.text      = profile.bandwidth
        ids.tf_pakt_addr.text = profile.pakt_device_address or ""
        self.set_mode(profile.hardware_mode)

    def collect_profile(self, profile) -> None:
        """Write UI values back into *profile*."""
        ids = self.ids
        try:
            profile.frequency = float(ids.tf_freq.text or "145.070")
        except ValueError:
            pass
        try:
            profile.offset = float(ids.tf_offset.text or "0.6")
        except ValueError:
            pass
        try:
            profile.squelch = int(ids.tf_squelch.text or "4")
        except ValueError:
            pass
        profile.bandwidth = ids.tf_bw.text or "Wide"
        profile.hardware_mode = self._mode
        profile.pakt_device_address = ids.tf_pakt_addr.text.strip()

    # ── serial port handling ──────────────────────────────────────────────────

    def set_radio_controller(self, ctrl, async_ctrl) -> None:
        """Wire a RadioController + RadioControllerAsync from main.py."""
        self._radio_ctrl  = ctrl
        self._radio_async = async_ctrl
        ctrl.on_response = lambda resp: Clock.schedule_once(
            lambda dt: self._on_radio_response(resp)
        )
        ctrl.on_error = lambda msg: Clock.schedule_once(
            lambda dt: Snackbar(text=f"Radio error: {msg}").open()
        )

    def _on_radio_response(self, resp: str) -> None:
        Snackbar(text=f"SA818: {resp}").open()

    def refresh_serial_ports(self) -> None:
        if self._serial_mgr is None:
            Snackbar(text="Serial manager not initialised").open()
            return
        self._port_list = self._serial_mgr.list_ports()
        dd = self.ids.dd_port
        if self._port_list:
            dd.set_item(self._port_list[0][1])
            self._selected_port = self._port_list[0][0]
            Snackbar(text=f"Found {len(self._port_list)} port(s)").open()
        else:
            dd.set_item("(no ports found)")
            self._selected_port = None
            Snackbar(text="No serial ports found — check USB OTG connection").open()

    def connect_serial(self) -> None:
        """Open the selected serial port and attach the radio controller."""
        if self._serial_mgr is None:
            return
        port = getattr(self, "_selected_port", None) or (
            self._port_list[0][0] if self._port_list else None
        )
        if port is None:
            Snackbar(text="No port selected — tap Refresh first").open()
            return
        ok = self._serial_mgr.connect(port, baudrate=9600)
        if ok and self._radio_ctrl:
            self._radio_ctrl.attach(self._serial_mgr)
            Snackbar(text=f"Connected to {port}").open()
            self.status_text  = "Serial Connected"
            self.status_icon  = "cable-data"
            self.status_color = [0.2, 0.8, 0.2, 1]
        elif not ok:
            Snackbar(text=f"Could not open {port}").open()

    def disconnect_serial(self) -> None:
        if self._radio_ctrl:
            self._radio_ctrl.detach()
        if self._serial_mgr:
            self._serial_mgr.disconnect()
        self.status_text  = "Disconnected"
        self.status_icon  = "radio-tower"
        self.status_color = [0.6, 0.6, 0.6, 1]

    def apply_radio(self) -> None:
        """Send SA818 DMOSETGROUP command with current UI values."""
        if self._radio_async is None or not (self._serial_mgr and self._serial_mgr.is_connected):
            Snackbar(text="Not connected — tap Connect first").open()
            return
        ids = self.ids
        try:
            freq   = float(ids.tf_freq.text   or "145.070")
            offset = float(ids.tf_offset.text or "0.0")
            sql    = int(ids.tf_squelch.text   or "4")
            bw     = ids.tf_bw.text            or "Wide"
        except ValueError:
            Snackbar(text="Invalid radio parameters").open()
            return
        # Read CTCSS from profile if available
        tx_tone = getattr(self._profile, "ctcss_tx", "None") if self._profile else "None"
        rx_tone = getattr(self._profile, "ctcss_rx", "None") if self._profile else "None"
        Snackbar(text="Applying radio settings…").open()
        self._radio_async.set_radio_async(
            on_result=lambda r: Clock.schedule_once(
                lambda dt: Snackbar(text=f"Radio set: {r}").open()
            ),
            on_error=lambda e: Clock.schedule_once(
                lambda dt: Snackbar(text=f"Radio error: {e}").open()
            ),
            frequency=freq,
            offset=offset,
            tx_tone=tx_tone,
            rx_tone=rx_tone,
            squelch=sql,
            bandwidth=bw,
        )

    def read_version(self) -> None:
        """Query SA818 firmware version."""
        if self._radio_async is None or not (self._serial_mgr and self._serial_mgr.is_connected):
            Snackbar(text="Not connected").open()
            return
        Snackbar(text="Reading SA818 version…").open()
        self._radio_async.version_async(
            on_result=lambda r: Clock.schedule_once(
                lambda dt: Snackbar(text=f"Version: {r}").open()
            ),
            on_error=lambda e: Clock.schedule_once(
                lambda dt: Snackbar(text=f"Version error: {e}").open()
            ),
        )

    # ── BLE / PAKT ───────────────────────────────────────────────────────────

    def set_ble_manager(self, mgr) -> None:
        self._ble_mgr = mgr
        mgr.on_device_found  = self._on_ble_device_found
        mgr.on_state_changed = self._on_ble_state_changed
        mgr.on_error         = self._on_ble_error

    def start_ble_scan(self) -> None:
        if self._ble_mgr is None:
            Snackbar(text="BLE manager not available").open()
            return
        self._found_devices.clear()
        self.ids.ble_device_list.clear_widgets()
        Snackbar(text="Scanning for PAKT devices…").open()
        self._ble_mgr.start_scan(timeout=8.0)

    def ble_connect(self) -> None:
        if self._ble_mgr is None:
            return
        addr = self.ids.tf_pakt_addr.text.strip()
        if not addr:
            Snackbar(text="Enter or scan for a device address first").open()
            return
        self._ble_mgr.connect(addr)
        Snackbar(text=f"Connecting to {addr}…").open()

    def _on_ble_device_found(self, device) -> None:
        Clock.schedule_once(lambda dt: self._add_ble_device_item(device))

    def _add_ble_device_item(self, device) -> None:
        self._found_devices.append(device)
        item = TwoLineListItem(
            text=device.name,
            secondary_text=f"{device.address}  RSSI {device.rssi} dBm",
        )
        item.bind(on_release=lambda x, d=device: self._select_ble_device(d))
        self.ids.ble_device_list.add_widget(item)

    def _select_ble_device(self, device) -> None:
        self.ids.tf_pakt_addr.text = device.address

    def _on_ble_state_changed(self, state) -> None:
        Clock.schedule_once(lambda dt: self._apply_ble_state(state))

    def _apply_ble_state(self, state) -> None:
        from hal.ble_manager import BleState
        state_map = {
            BleState.IDLE:         ("Idle",       "radio-tower",   [0.6, 0.6, 0.6, 1]),
            BleState.SCANNING:     ("Scanning…",  "bluetooth-searching", [0.2, 0.6, 1.0, 1]),
            BleState.CONNECTING:   ("Connecting…","bluetooth-connect",   [1.0, 0.7, 0.0, 1]),
            BleState.CONNECTED:    ("Connected",  "bluetooth-connect",   [0.2, 0.8, 0.2, 1]),
            BleState.RECONNECTING: ("Reconnecting…","bluetooth-off",     [1.0, 0.5, 0.0, 1]),
            BleState.ERROR:        ("BLE Error",  "bluetooth-off",       [0.9, 0.2, 0.2, 1]),
        }
        text, icon, color = state_map.get(state, ("Unknown", "help", [0.5, 0.5, 0.5, 1]))
        self.status_text  = text
        self.status_icon  = icon
        self.status_color = color

    def _on_ble_error(self, msg: str) -> None:
        Clock.schedule_once(lambda dt: Snackbar(text=f"BLE error: {msg}").open())

    # ── audio ────────────────────────────────────────────────────────────────

    def refresh_audio(self) -> None:
        from hal import audio_manager
        outs = audio_manager.list_output_devices()
        ins  = audio_manager.list_input_devices()
        if outs:
            self.ids.dd_audio_out.set_item(outs[0][1])
        if ins:
            self.ids.dd_audio_in.set_item(ins[0][1])
        Snackbar(text=f"Audio: {len(outs)} out, {len(ins)} in").open()

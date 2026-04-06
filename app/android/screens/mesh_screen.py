"""screens/mesh_screen.py — PAKT mesh chat interface.

Provides a simple chat-style UI for the PAKT radio mesh network:
  • Message log (received mesh packets, timestamped)
  • Compose and send text message to a node or broadcast
  • Node list: known mesh nodes with RSSI/role
  • Mesh settings: role (ENDPOINT / REPEATER), TTL, hello beacon

Messages flow via BleManager → PaktService → MeshManager in Phase 2.
For Phase 1 (MVP) the UI is built and stubbed; actual BLE TX is wired
when PaktService is integrated.
"""

from __future__ import annotations

import logging
import time

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty, BooleanProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.list import TwoLineListItem, OneLineListItem
from kivymd.uix.snackbar import Snackbar

_log = logging.getLogger(__name__)

Builder.load_string("""
<MeshScreen>:
    name: "mesh"
    MDBoxLayout:
        orientation: "vertical"
        padding: dp(8)
        spacing: dp(8)

        # ── Connection status ─────────────────────────────────────────
        MDCard:
            size_hint_y: None
            height: dp(48)
            radius: [dp(8)]
            padding: [dp(8), dp(4)]
            MDBoxLayout:
                spacing: dp(8)
                MDIcon:
                    icon: "bluetooth-connect" if root.ble_connected else "bluetooth-off"
                    theme_text_color: "Custom"
                    text_color: [0.2,0.8,0.2,1] if root.ble_connected else [0.6,0.6,0.6,1]
                    size_hint_x: None
                    width: dp(24)
                MDLabel:
                    text: root.connection_label
                    font_style: "Body2"
                MDFlatButton:
                    text: "Nodes"
                    size_hint: None, None
                    size: dp(64), dp(36)
                    on_release: root.toggle_node_panel()

        # ── Node list (collapsible) ───────────────────────────────────
        MDCard:
            id: card_nodes
            radius: [dp(8)]
            padding: dp(8)
            size_hint_y: None
            height: self.minimum_height if root.show_nodes else 0
            opacity: 1 if root.show_nodes else 0
            disabled: not root.show_nodes
            MDBoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: self.minimum_height
                spacing: dp(4)

                MDLabel:
                    text: "Known Mesh Nodes"
                    font_style: "Subtitle2"
                    size_hint_y: None
                    height: dp(24)

                MDList:
                    id: node_list
                    size_hint_y: None
                    height: self.minimum_height

        # ── Chat log ──────────────────────────────────────────────────
        ScrollView:
            id: chat_scroll
            MDList:
                id: chat_list
                size_hint_y: None
                height: self.minimum_height

        # ── Compose bar ───────────────────────────────────────────────
        MDCard:
            size_hint_y: None
            height: dp(64)
            radius: [dp(12)]
            padding: [dp(8), dp(4)]
            MDBoxLayout:
                spacing: dp(8)
                MDDropDownItem:
                    id: dd_dest
                    text: "Broadcast"
                    size_hint_x: None
                    width: dp(120)
                    font_size: dp(13)
                MDTextField:
                    id: tf_msg
                    hint_text: "Type a message…"
                    size_hint_y: None
                    height: dp(48)
                    multiline: False
                    on_text_validate: root.send_msg()
                MDIconButton:
                    icon: "send"
                    on_release: root.send_msg()
                    theme_text_color: "Primary"

        # ── Mesh settings ─────────────────────────────────────────────
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
                    text: "Mesh Settings"
                    font_style: "Subtitle2"
                    size_hint_y: None
                    height: dp(24)

                MDBoxLayout:
                    size_hint_y: None
                    height: dp(40)
                    spacing: dp(8)
                    MDLabel:
                        text: "Node role:"
                    MDDropDownItem:
                        id: dd_role
                        text: "ENDPOINT"
                        size_hint_x: None
                        width: dp(130)
                        font_size: dp(13)

                MDBoxLayout:
                    size_hint_y: None
                    height: dp(40)
                    spacing: dp(8)
                    MDLabel:
                        text: "Default TTL:"
                    MDTextField:
                        id: tf_ttl
                        text: "4"
                        input_filter: "int"
                        size_hint_x: None
                        width: dp(60)
                        height: dp(36)

                MDBoxLayout:
                    size_hint_y: None
                    height: dp(40)
                    MDLabel:
                        text: "Hello beacon"
                    MDSwitch:
                        id: sw_hello
                        active: False

                # bottom padding
                MDBoxLayout:
                    size_hint_y: None
                    height: dp(72)
""")


class MeshScreen(MDScreen):
    """PAKT mesh chat and node management screen."""

    ble_connected    = BooleanProperty(False)
    connection_label = StringProperty("Not connected to PAKT device")
    show_nodes       = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._profile      = None
        self._pakt_bridge  = None     # PaktServiceBridge — set by main.py
        self._known_nodes: dict = {}  # callsign → {rssi, role}
        self._message_count = 0

    # ── profile ───────────────────────────────────────────────────────────────

    def load_profile(self, profile) -> None:
        self._profile = profile
        self.ids.tf_ttl.text = str(profile.mesh_default_ttl)
        self.ids.sw_hello.active = profile.mesh_hello_enabled
        role = profile.mesh_node_role or "ENDPOINT"
        self.ids.dd_role.set_item(role)

    def collect_profile(self, profile) -> None:
        try:
            profile.mesh_default_ttl = int(self.ids.tf_ttl.text)
        except ValueError:
            pass
        profile.mesh_hello_enabled = self.ids.sw_hello.active
        profile.mesh_node_role = self.ids.dd_role.current_item

    # ── UI events ─────────────────────────────────────────────────────────────

    def toggle_node_panel(self) -> None:
        self.show_nodes = not self.show_nodes

    # ── PaktServiceBridge wiring ──────────────────────────────────────────────

    def set_pakt_bridge(self, bridge) -> None:
        """Wire a PaktServiceBridge from main.py."""
        self._pakt_bridge = bridge
        bridge.on_connected    = self._on_pakt_connected
        bridge.on_disconnected = self._on_pakt_disconnected
        bridge.on_status       = self._on_pakt_status
        bridge.on_tx_result    = self._on_pakt_tx_result
        bridge.on_device_info  = self._on_pakt_device_info
        bridge.on_telemetry    = self._on_pakt_telemetry

    def _on_pakt_connected(self, event) -> None:
        addr = getattr(event, "address", "?")
        self.ble_connected = True
        self.connection_label = f"Connected: {addr}"
        Snackbar(text=f"PAKT connected: {addr}").open()
        # Request device info and capabilities
        if self._pakt_bridge:
            self._pakt_bridge.read_device_info()
            self._pakt_bridge.read_capabilities()

    def _on_pakt_disconnected(self) -> None:
        self.ble_connected = False
        self.connection_label = "Not connected to PAKT device"
        Snackbar(text="PAKT disconnected").open()

    def _on_pakt_status(self, msg: str) -> None:
        _log.info("PAKT status: %s", msg)

    def _on_pakt_tx_result(self, event) -> None:
        success = getattr(event, "success", True)
        local_id = getattr(event, "local_id", "?")
        if success:
            Snackbar(text=f"PAKT TX {local_id} delivered").open()
        else:
            reason = getattr(event, "reason", "unknown")
            Snackbar(text=f"PAKT TX {local_id} failed: {reason}").open()

    def _on_pakt_device_info(self, event) -> None:
        callsign = getattr(event, "callsign", None)
        fw       = getattr(event, "firmware", None)
        parts = []
        if callsign:
            parts.append(callsign)
        if fw:
            parts.append(f"fw {fw}")
        if parts:
            self.connection_label = "PAKT: " + "  ".join(parts)

    def _on_pakt_telemetry(self, event) -> None:
        _log.debug("PAKT telemetry: %s", event)

    # ── UI events ─────────────────────────────────────────────────────────────

    def send_msg(self) -> None:
        text = self.ids.tf_msg.text.strip()
        if not text:
            return
        dest = self.ids.dd_dest.current_item or "Broadcast"
        self.ids.tf_msg.text = ""
        if not self.ble_connected:
            Snackbar(text="Not connected to PAKT device").open()
            return
        if self._pakt_bridge is not None and self._pakt_bridge.is_connected:
            try:
                self._pakt_bridge.send(dest=dest, text=text)
                _log.info("Mesh TX sent: %s → %s", dest, text)
            except Exception as exc:
                _log.error("Mesh send error: %s", exc)
                Snackbar(text=f"Send failed: {exc}").open()
                return
        else:
            _log.info("Mesh TX (stub — bridge not connected): %s → %s", dest, text)

        self._add_message(
            from_cs="Me",
            to_cs=dest,
            text=text,
            outgoing=True,
        )

    # ── BLE state callbacks (also called from main.py BleManager path) ──────────

    def on_ble_connected(self, address: str) -> None:
        """Legacy hook — also called from main.py BleManager path."""
        self.ble_connected = True
        self.connection_label = f"Connected: {address}"

    def on_ble_disconnected(self) -> None:
        self.ble_connected = False
        self.connection_label = "Not connected to PAKT device"

    # ── incoming packet handling ──────────────────────────────────────────────

    def on_mesh_packet(self, packet) -> None:
        """Called from PaktServiceBridge (already on main thread via Clock)."""
        self._handle_packet(packet)

    def _handle_packet(self, packet) -> None:
        """Handle a received PAKT packet (PaktRxEvent, raw dict, or any object)."""
        # Support both structured events and raw dicts
        if isinstance(packet, dict):
            src  = packet.get("src_callsign", packet.get("src", "?"))
            text = packet.get("payload", packet.get("text", ""))
        else:
            src  = getattr(packet, "src_callsign", getattr(packet, "src", "?"))
            text = getattr(packet, "payload",      getattr(packet, "text", ""))
        self._add_message(from_cs=str(src), to_cs="Me", text=str(text), outgoing=False)
        # Track new nodes
        if src not in self._known_nodes:
            rssi = getattr(packet, "rssi", -100)
            self._known_nodes[src] = {"rssi": rssi, "role": "ENDPOINT"}
            self._add_node_item(str(src))

    def _add_message(self, from_cs: str, to_cs: str, text: str,
                     outgoing: bool = False) -> None:
        self._message_count += 1
        ts = time.strftime("%H:%M:%S")
        if outgoing:
            header = f"→ {to_cs}  [{ts}]"
        else:
            header = f"← {from_cs}  [{ts}]"
        item = TwoLineListItem(
            text=header,
            secondary_text=text[:100],
        )
        self.ids.chat_list.add_widget(item, index=0)
        # Keep at most 200 messages
        children = self.ids.chat_list.children
        if len(children) > 200:
            self.ids.chat_list.remove_widget(children[-1])

    def _add_node_item(self, callsign: str) -> None:
        item = OneLineListItem(text=callsign)
        self.ids.node_list.add_widget(item)
        # Update destination dropdown
        # Rebuild dest options
        self.ids.dd_dest.set_item("Broadcast")

"""main.py — HAM HAT Control Center v4 — Android (Kivy/KivyMD) entry point.

Architecture
────────────
• KivyMD MDApp with responsive layout:
    - Phone  (width < 600 dp): MDBottomNavigation, single-column screens
    - Tablet (width ≥ 600 dp): MDNavigationRail, two-column layout

• 4 screens (via ScreenManager):
    control  – hardware mode / SA818 / PAKT BLE / audio
    aprs     – APRS packet log, beacon, messaging
    setup    – profile management, PTT, PAKT settings, audio test
    mesh     – PAKT mesh chat

• Engine reuse:
    - ProfileManager, AppProfile from app.engine.profile / models
    - APRS modem via hal.aprs_modem_bridge (wraps app.engine.aprs_modem)
    - PAKT service via hal.pakt_service_bridge (wraps app.engine.pakt.service)

• Platform layer (hal/):
    - ble_manager      – BLE scan/connect (bleak async)
    - serial_manager   – USB serial (usbserial4a on Android, pyserial on desktop)
    - radio_controller – SA818 AT command protocol over SerialManager
    - aprs_modem_bridge– APRS TX/RX using engine DSP + platform audio I/O
    - pakt_service_bridge – PaktService wrapped with Kivy-thread-safe callbacks
    - foreground_service  – Android foreground notification for background BLE
    - audio_manager    – audio enumeration and playback
    - paths            – Android/desktop data directory

Usage (development on desktop):
    python main.py

Build APK:
    cd app/android && buildozer android debug
"""

from __future__ import annotations

# ── Bootstrap engine imports first (sets sys.path) ──────────────────────────
import engine_bridge  # noqa: F401

import logging
import os
import threading
from pathlib import Path
from typing import Optional

# ── Kivy config must happen before kivy imports ──────────────────────────────
os.environ.setdefault("KIVY_NO_ENV_CONFIG", "1")

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.utils import platform as KIVY_PLATFORM
from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
from kivymd.uix.navigationrail import MDNavigationRail, MDNavigationRailItem
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.snackbar import Snackbar

# ── Internal imports ─────────────────────────────────────────────────────────
from screens.control_screen import ControlScreen
from screens.aprs_screen    import AprsScreen
from screens.setup_screen   import SetupScreen
from screens.mesh_screen    import MeshScreen
from hal.ble_manager         import BleManager, BleState, request_ble_permissions
from hal.serial_manager      import SerialManager, request_usb_permission
from hal.radio_controller    import RadioController, RadioControllerAsync
from hal.aprs_modem_bridge   import AprsModemBridge
from hal.pakt_service_bridge import PaktServiceBridge
from hal.foreground_service  import start_ble_foreground_service, stop_ble_foreground_service
from hal.paths               import get_user_data_dir, get_profile_file

_log = logging.getLogger(__name__)

_IS_ANDROID = (KIVY_PLATFORM == "android")
_IS_TABLET  = False   # set at build() time based on Window.width

# ── Tablet layout (NavigationRail on the left) ───────────────────────────────
TABLET_KV = """
<TabletLayout>:
    MDBoxLayout:
        orientation: "horizontal"
        MDNavigationRail:
            id: nav_rail
            MDNavigationRailItem:
                icon: "radio-tower"
                text: "Control"
                on_release: app.switch_screen("control")
            MDNavigationRailItem:
                icon: "antenna"
                text: "APRS"
                on_release: app.switch_screen("aprs")
            MDNavigationRailItem:
                icon: "cog"
                text: "Setup"
                on_release: app.switch_screen("setup")
            MDNavigationRailItem:
                icon: "chat-outline"
                text: "Mesh"
                on_release: app.switch_screen("mesh")
        MDBoxLayout:
            orientation: "vertical"
            MDTopAppBar:
                title: "HAM HAT Control Center  (4.0)"
                elevation: 2
            MDScreenManager:
                id: sm
"""

# ── Phone layout (BottomNavigation) ─────────────────────────────────────────
PHONE_KV = """
<PhoneLayout>:
    MDBoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            id: toolbar
            title: "HAM HAT CC"
            elevation: 2
        MDBottomNavigation:
            id: bottom_nav
            selected_color_background: app.theme_cls.primary_color
            MDBottomNavigationItem:
                name: "control"
                text: "Control"
                icon: "radio-tower"
            MDBottomNavigationItem:
                name: "aprs"
                text: "APRS"
                icon: "antenna"
            MDBottomNavigationItem:
                name: "setup"
                text: "Setup"
                icon: "cog"
            MDBottomNavigationItem:
                name: "mesh"
                text: "Mesh"
                icon: "chat-outline"
"""


class HamHatApp(MDApp):
    """Main KivyMD application class."""

    AUTOSAVE_INTERVAL = 30   # seconds

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "HAM HAT Control Center"

        # ── Core managers (Phase 1) ──────────────────────────────────────────
        self._profile          = None   # AppProfile instance
        self._profile_manager  = None   # ProfileManager instance
        self._ble_manager:    BleManager    = BleManager()
        self._serial_manager: SerialManager = SerialManager()

        # ── Phase 2 hardware managers ────────────────────────────────────────
        self._radio_ctrl:  RadioController       = RadioController()
        self._radio_async: RadioControllerAsync  = RadioControllerAsync(self._radio_ctrl)
        self._aprs_modem:  AprsModemBridge       = AprsModemBridge()
        self._pakt_bridge: PaktServiceBridge     = PaktServiceBridge()

        # Screen refs (set after build)
        self._screens: dict[str, MDScreen] = {}
        self._sm: Optional[MDScreenManager] = None
        self._current_screen = "control"

        # Autosave
        self._autosave_event = None

    # ── build ────────────────────────────────────────────────────────────────

    def build(self):
        """Build the UI. Returns the root widget."""
        global _IS_TABLET
        _IS_TABLET = Window.width >= dp(600)

        # Theme
        self.theme_cls.theme_style     = "Dark"
        self.theme_cls.primary_palette = "Cyan"
        self.theme_cls.accent_palette  = "Amber"

        # Load KV strings
        if _IS_TABLET:
            Builder.load_string(TABLET_KV)
            root = self._build_tablet()
        else:
            Builder.load_string(PHONE_KV)
            root = self._build_phone()

        return root

    def _build_phone(self):
        """Phone layout: BottomNavigation containing the 4 screens."""
        from kivy.uix.boxlayout import BoxLayout
        root = BoxLayout(orientation="vertical")

        # Toolbar
        toolbar = MDTopAppBar(title="HAM HAT CC", elevation=2)
        root.add_widget(toolbar)

        # Bottom navigation
        from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
        nav = MDBottomNavigation(selected_color_background=self.theme_cls.primary_color)

        # Create screens as children of nav items
        for name, icon, label, cls in [
            ("control", "radio-tower",  "Control", ControlScreen),
            ("aprs",    "antenna",      "APRS",    AprsScreen),
            ("setup",   "cog",          "Setup",   SetupScreen),
            ("mesh",    "chat-outline", "Mesh",    MeshScreen),
        ]:
            item = MDBottomNavigationItem(name=name, text=label, icon=icon)
            screen = cls(name=name)
            self._screens[name] = screen
            item.add_widget(screen)
            nav.add_widget(item)

        root.add_widget(nav)
        return root

    def _build_tablet(self):
        """Tablet layout: NavigationRail + ScreenManager."""
        from kivy.uix.boxlayout import BoxLayout
        root = BoxLayout(orientation="horizontal")

        # Navigation rail
        rail = MDNavigationRail()
        for name, icon, label, cls in [
            ("control", "radio-tower",  "Control", ControlScreen),
            ("aprs",    "antenna",      "APRS",    AprsScreen),
            ("setup",   "cog",          "Setup",   SetupScreen),
            ("mesh",    "chat-outline", "Mesh",    MeshScreen),
        ]:
            item = MDNavigationRailItem(icon=icon, text=label)
            item.bind(on_release=lambda x, n=name: self.switch_screen(n))
            rail.add_widget(item)
            screen = cls(name=name)
            self._screens[name] = screen
        root.add_widget(rail)

        # Right panel: toolbar + screen manager
        right = BoxLayout(orientation="vertical")
        right.add_widget(MDTopAppBar(
            title="HAM HAT Control Center  (4.0)", elevation=2
        ))
        sm = MDScreenManager()
        self._sm = sm
        for screen in self._screens.values():
            sm.add_widget(screen)
        right.add_widget(sm)
        root.add_widget(right)
        return root

    def switch_screen(self, name: str) -> None:
        """Switch to a named screen (tablet mode)."""
        self._current_screen = name
        if self._sm:
            self._sm.current = name

    # ── on_start: initialise engine, load profile, wire managers ────────────

    def on_start(self):
        """Called after the UI is built and displayed."""
        _log.info("HamHatApp starting on %s", KIVY_PLATFORM)

        # ── Android permissions ───────────────────────────────────────────────
        if _IS_ANDROID:
            request_ble_permissions()
            request_usb_permission()
            from hal.audio_manager import request_audio_permission
            request_audio_permission()

        # ── Screen refs ──────────────────────────────────────────────────────
        ctrl_screen  = self._screens.get("control")
        aprs_screen  = self._screens.get("aprs")
        setup_screen = self._screens.get("setup")
        mesh_screen  = self._screens.get("mesh")

        # ── Wire Phase 1: BLE + Serial into Control screen ───────────────────
        if ctrl_screen:
            ctrl_screen._serial_mgr = self._serial_manager
            ctrl_screen.set_ble_manager(self._ble_manager)
            ctrl_screen.set_radio_controller(self._radio_ctrl, self._radio_async)

        # ── Wire Phase 2: APRS modem into APRS screen ────────────────────────
        if aprs_screen:
            aprs_screen.set_aprs_modem(self._aprs_modem)

        # ── Wire Phase 2: PAKT bridge into Mesh screen ───────────────────────
        if mesh_screen:
            mesh_screen.set_pakt_bridge(self._pakt_bridge)

        # ── Start PaktServiceBridge (creates background event loop) ──────────
        data_dir = get_user_data_dir()
        self._pakt_bridge.config_cache_path = data_dir / "pakt_config.json"
        self._pakt_bridge.start()

        # ── Wire BLE state → mesh screen (fallback for non-PAKT BLE use) ─────
        _orig_state_cb = self._ble_manager.on_state_changed
        def _combined_ble_state(state):
            if _orig_state_cb:
                _orig_state_cb(state)
            if mesh_screen:
                if state == BleState.CONNECTED:
                    addr = self._ble_manager._connected_address or "?"
                    Clock.schedule_once(lambda dt: mesh_screen.on_ble_connected(addr))
                elif state == BleState.IDLE:
                    Clock.schedule_once(lambda dt: mesh_screen.on_ble_disconnected())
        self._ble_manager.on_state_changed = _combined_ble_state

        # ── Wire APRS modem audio device indices from profile (deferred) ─────
        def _wire_audio_device(dt):
            if self._profile:
                self._aprs_modem.output_device_idx = getattr(
                    self._profile, "audio_output_device", None
                )
                self._aprs_modem.input_device_idx = getattr(
                    self._profile, "audio_input_device", None
                )
        Clock.schedule_once(_wire_audio_device, 0.5)

        # ── Wire serial errors ───────────────────────────────────────────────
        self._serial_manager.on_error = lambda msg: Clock.schedule_once(
            lambda dt: Snackbar(text=f"Serial: {msg}").open()
        )

        # ── Wire APRS modem PTT to radio controller ───────────────────────────
        self._aprs_modem.set_radio_controller(self._radio_ctrl)

        # ── Android foreground service (keeps BLE alive in background) ────────
        if _IS_ANDROID:
            Clock.schedule_once(
                lambda dt: start_ble_foreground_service(
                    title="HAM HAT Control Center",
                    body="Radio service running",
                ),
                2.0,
            )

        # ── Load profile (deferred so UI is fully built) ──────────────────────
        Clock.schedule_once(self._load_profile_deferred, 0.2)

        # ── Autosave ──────────────────────────────────────────────────────────
        self._autosave_event = Clock.schedule_interval(
            self._autosave, self.AUTOSAVE_INTERVAL
        )

        # ── Initial audio refresh ─────────────────────────────────────────────
        Clock.schedule_once(lambda dt: self._initial_audio_refresh(), 1.0)

    def _load_profile_deferred(self, dt) -> None:
        """Load profile from disk (deferred so UI is fully ready)."""
        try:
            from app.engine.profile import ProfileManager
            from app.engine.models  import AppProfile

            profile_file = get_profile_file()
            profile_file.parent.mkdir(parents=True, exist_ok=True)
            pm      = ProfileManager(profile_file)
            profile = pm.load() or AppProfile()

            self._profile         = profile
            self._profile_manager = pm

            # Populate all screens
            for name, screen in self._screens.items():
                if hasattr(screen, "load_profile"):
                    try:
                        screen.load_profile(profile)
                    except Exception as exc:
                        _log.warning("Screen %s load_profile error: %s", name, exc)

            setup = self._screens.get("setup")
            if setup and hasattr(setup, "set_profile_manager"):
                setup.set_profile_manager(pm)

            _log.info("Profile loaded from %s", profile_file)

        except Exception as exc:
            _log.error("Profile load failed: %s", exc)
            Snackbar(text=f"Profile load failed: {exc}").open()

    def _initial_audio_refresh(self) -> None:
        ctrl = self._screens.get("control")
        if ctrl and hasattr(ctrl, "refresh_audio"):
            try:
                ctrl.refresh_audio()
            except Exception as exc:
                _log.debug("Initial audio refresh error: %s", exc)

    # ── autosave ─────────────────────────────────────────────────────────────

    def _autosave(self, dt) -> None:
        if self._profile is None or self._profile_manager is None:
            return
        # Collect current UI values into profile
        for name, screen in self._screens.items():
            if hasattr(screen, "collect_profile"):
                try:
                    screen.collect_profile(self._profile)
                except Exception as exc:
                    _log.warning("collect_profile %s: %s", name, exc)
        # Save
        try:
            self._profile_manager.save(self._profile)
            _log.debug("Profile autosaved")
        except Exception as exc:
            _log.warning("Autosave failed: %s", exc)

    # ── on_stop / on_pause ───────────────────────────────────────────────────

    def on_stop(self) -> None:
        """Called when the app is closing (desktop) or swiped away (Android)."""
        if self._autosave_event:
            self._autosave_event.cancel()
        self._autosave(0)   # final save
        # Phase 2 teardown
        self._aprs_modem.stop_rx()
        self._pakt_bridge.stop()
        if self._radio_ctrl.is_attached:
            self._radio_ctrl.detach()
        # Phase 1 teardown
        self._ble_manager.disconnect()
        self._serial_manager.disconnect()
        # Android foreground notification
        if _IS_ANDROID:
            stop_ble_foreground_service()
        _log.info("HamHatApp stopped")

    def on_pause(self) -> bool:
        """Android: return True to keep the app alive in background."""
        self._autosave(0)
        return True

    def on_resume(self) -> None:
        """Android: called when returning from background."""
        _log.debug("HamHatApp resumed")


# ── Logging configuration ────────────────────────────────────────────────────

def _configure_logging() -> None:
    fmt = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"
    datefmt = "%H:%M:%S"
    logging.basicConfig(level=logging.INFO, format=fmt, datefmt=datefmt)
    # Suppress noisy libs
    for noisy in ("bleak", "asyncio", "kivy", "kivymd"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


# ── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    _configure_logging()
    HamHatApp().run()

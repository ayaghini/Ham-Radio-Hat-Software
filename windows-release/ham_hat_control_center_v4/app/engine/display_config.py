#!/usr/bin/env python3
"""DisplayConfig — cross-platform display/font configuration helper.

Provides preset display configurations for different deployment targets.
The main use case is the Raspberry Pi 5-inch 1280×720 display, which runs
at a high physical DPI but often has X11 configured at the default 96 DPI,
making default Tkinter fonts too small to read comfortably.

Usage::

    from app.engine.display_config import DisplayConfig

    cfg = DisplayConfig.rpi_720p()   # 5-inch 1280×720 RPi screen
    cfg = DisplayConfig.default()    # desktop default (no overrides)
    cfg = DisplayConfig(scale=1.5)   # custom scale

The config is applied once by HamHatApp.__init__ and affects:
  - Window geometry (size and position)
  - tk scaling factor (affects all widget pixel sizing)
  - ttk Style fonts (affects ttk Buttons, Labels, Entries, etc.)
  - option_add fonts (affects tk Text and Listbox widgets)
"""

from __future__ import annotations

import platform
import tkinter as tk
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Font resolution helpers
# ---------------------------------------------------------------------------

def _resolve_mono_font() -> str:
    """Return the best available monospace font name for the current platform.

    Uses the Tk ``"TkFixedFont"`` logical font alias which resolves to
    Courier New on Windows, Menlo/Monaco on macOS, and DejaVu Sans Mono
    (or Liberation Mono) on Linux/RPi.  The literal string ``"TkFixedFont"``
    can be used directly in widget ``font=`` kwargs and Tkinter resolves it.
    """
    # TkFixedFont is the portable alias; just return it for now.
    # We keep this function as a hook for future runtime font probing.
    return "TkFixedFont"


def _resolve_ui_font() -> str:
    """Return the best available proportional UI font for the current platform."""
    return "TkDefaultFont"


# ---------------------------------------------------------------------------
# DisplayConfig dataclass
# ---------------------------------------------------------------------------

@dataclass
class DisplayConfig:
    """All display/layout parameters for a single deployment target.

    Attributes:
        scale: Tkinter scaling factor passed to ``tk.call('tk', 'scaling', …)``.
            1.0 = default (72 pt/inch assumption).  1.333 ≈ 96 DPI.
            Use higher values on small high-DPI screens.
        geometry: Tkinter geometry string (``"WxH+X+Y"``) or None to let the
            window manager choose.
        fullscreen: Whether to request a full-screen window at startup.
        mono_font: Monospace font family.  ``"TkFixedFont"`` is the portable
            Tkinter alias (resolves to the best mono font on each platform).
        ui_font: Proportional UI font family.  ``"TkDefaultFont"`` is portable.
        mono_size: Base point size for monospace text (log, callsign entries).
        ui_size: Base point size for UI labels, buttons, etc.
        log_height_main: BoundedLog height (lines) on the Control tab.
        log_height_comms: BoundedLog height (lines) on the APRS Comms message area.
        log_height_aprs: BoundedLog height (lines) for the APRS event log.
        map_height: Tile map canvas height in pixels on the Comms tab.
        contacts_height: Listbox height (lines) for the contacts list.
        groups_height: Listbox height (lines) for the groups list.
        heard_height: Listbox height (lines) for heard stations.
        compose_height: Compose text area height (lines).
        route_tree_height: Route table Treeview height (rows) on the Mesh tab.
        mesh_log_height: Diagnostics BoundedLog height on the Mesh tab.
    """

    scale: float = 1.0
    geometry: Optional[str] = None
    fullscreen: bool = False

    mono_font: str = field(default_factory=_resolve_mono_font)
    ui_font: str = field(default_factory=_resolve_ui_font)
    mono_size: int = 9
    ui_size: int = 10

    # Layout heights — tab-specific
    log_height_main: int = 8
    log_height_comms: int = 10
    log_height_aprs: int = 5
    map_height: int = 180
    contacts_height: int = 6
    groups_height: int = 4
    heard_height: int = 5
    compose_height: int = 3
    route_tree_height: int = 6
    mesh_log_height: int = 6

    # Compact padding — used for section spacing on small screens.
    # Default (4) matches the existing desktop paddings.
    # Set to 2 on small screens to recover vertical pixels without
    # making the UI feel too cramped.
    compact_padding: int = 4

    # ------------------------------------------------------------------
    # Factory methods
    # ------------------------------------------------------------------

    @staticmethod
    def default() -> "DisplayConfig":
        """Default configuration — no overrides, desktop window manager decides."""
        return DisplayConfig()

    @staticmethod
    def rpi_720p() -> "DisplayConfig":
        """Optimized for a 5-inch 1280×720 16:9 screen on Raspberry Pi.

        Physical DPI of a 5-inch 1280×720 screen is ~293 PPI.  X11 on RPi
        typically reports 96 DPI, so all fonts would be ~3× too small without
        intervention.  A tk scaling of 1.5 maps 1 point → 1.5 physical pixels,
        making widgets and text comfortably readable at arm's reach.

        Vertical budget (approximate):
          720px screen
          − 24px OS title bar (LXDE/Openbox default)
          − 28px Notebook tab bar (at scale 1.5)
          − 26px status bar
          = ~642px usable content area

        Heights are tuned so the busiest tab (APRS Comms) fits without
        scrolling at 1280×720.  compact_padding=2 recovers ~30px of
        section spacing across the four tabs.
        """
        return DisplayConfig(
            scale=1.5,
            geometry="1280x720+0+0",
            fullscreen=False,
            mono_font="TkFixedFont",
            ui_font="TkDefaultFont",
            mono_size=9,
            ui_size=10,
            # Tightened heights for the 720px vertical budget
            log_height_main=4,
            log_height_comms=6,
            log_height_aprs=3,
            map_height=120,
            contacts_height=4,
            groups_height=3,
            heard_height=3,
            compose_height=2,
            route_tree_height=4,
            mesh_log_height=4,
            compact_padding=2,
        )

    @staticmethod
    def from_args(
        rpi: bool,
        scale: Optional[float],
        geometry: Optional[str],
        fullscreen: bool = False,
    ) -> "DisplayConfig":
        """Build a DisplayConfig from command-line arguments.

        Args:
            rpi: If True, start from the rpi_720p() preset.
            scale: Override tk scaling factor (overrides preset).
            geometry: Override window geometry (overrides preset).
            fullscreen: If True, request a full-screen window (overrides
                geometry; removes OS chrome completely).  Useful when running
                on a dedicated RPi display where no window manager chrome is
                wanted.
        """
        cfg = DisplayConfig.rpi_720p() if rpi else DisplayConfig.default()
        if scale is not None:
            cfg.scale = scale
        if geometry is not None:
            cfg.geometry = geometry
        if fullscreen:
            cfg.fullscreen = True
            cfg.geometry = None  # fullscreen and explicit geometry conflict
        return cfg

    # ------------------------------------------------------------------
    # Application helpers
    # ------------------------------------------------------------------

    def apply_to_root(self, root: tk.Tk) -> None:
        """Apply this config to the root Tk window.

        Call this *before* building any widgets so that scaling and font
        options take effect globally.
        """
        # 1. Scaling
        if self.scale != 1.0:
            root.tk.call("tk", "scaling", self.scale)

        # 2. Geometry / fullscreen
        if self.fullscreen:
            root.attributes("-fullscreen", True)
        elif self.geometry:
            root.geometry(self.geometry)

        # 3. ttk Style fonts — affects ttk::button, ttk::label, ttk::entry …
        from tkinter import ttk
        style = ttk.Style(root)
        # Only set if we have specific sizes to override
        if self.ui_size != 10 or self.ui_font != "TkDefaultFont":
            style.configure(".", font=(self.ui_font, self.ui_size))
        if self.mono_size != 9 or self.mono_font != "TkFixedFont":
            style.configure("TEntry",    font=(self.mono_font, self.mono_size))
            style.configure("TCombobox", font=(self.mono_font, self.mono_size))

        # 4. Classic Tk widget fonts (Text, Listbox, Canvas child labels)
        root.option_add("*Text*Font",    f"{self.mono_font} {self.mono_size}")
        root.option_add("*Listbox*Font", f"{self.mono_font} {self.mono_size}")

#!/usr/bin/env python3
"""MeshTab — Mesh (Test) feature tab.

Sections:
  Top-left  : Mesh Control (enable, role, TTL, rate, HELLO)
  Top-right : Discovery (target callsign, discover button, status)
  Middle    : Route table (treeview with actions)
  Bottom-left  : Mesh Send (destination + message)
  Bottom-right : Diagnostics (stats counters + bounded log)

All controls are disabled when mesh is off except the enable checkbox.
"""

from __future__ import annotations

import time
import tkinter as tk
from tkinter import ttk, messagebox
from typing import TYPE_CHECKING

from .widgets import BoundedLog

if TYPE_CHECKING:
    from ..app import HamHatApp
    from ..engine.models import AppProfile


class MeshTab(ttk.Frame):
    """Mesh (Test) tab."""

    ROUTE_REFRESH_MS = 5000   # auto-refresh route table every 5s

    def __init__(self, parent: ttk.Notebook, app: "HamHatApp") -> None:
        super().__init__(parent)
        self._app = app
        self._build()
        self.after(self.ROUTE_REFRESH_MS, self._auto_refresh_routes)

    # ------------------------------------------------------------------
    # Build layout
    # ------------------------------------------------------------------

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=2)

        # Top pane: control + discovery side by side
        top = ttk.Frame(self)
        top.grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 0))
        top.columnconfigure(0, weight=1)
        top.columnconfigure(1, weight=1)
        self._build_control(top)
        self._build_discovery(top)

        # Middle: route table
        self._build_routes(self)

        # Bottom pane: send + diagnostics side by side
        bot = ttk.Frame(self)
        bot.grid(row=2, column=0, sticky="nsew", padx=6, pady=(4, 6))
        bot.columnconfigure(0, weight=1)
        bot.columnconfigure(1, weight=2)
        bot.rowconfigure(0, weight=1)
        self._build_send(bot)
        self._build_diagnostics(bot)
        self._refresh_enabled_state()

    # ------------------------------------------------------------------
    # Mesh Control section
    # ------------------------------------------------------------------

    def _build_control(self, parent: ttk.Frame) -> None:
        lf = ttk.LabelFrame(parent, text="Mesh Control", padding=8)
        lf.grid(row=0, column=0, sticky="nsew", padx=(0, 4), pady=2)
        lf.columnconfigure(1, weight=1)
        self._ctrl_frame = lf

        row = 0
        # Enable checkbox
        self._enable_cb = ttk.Checkbutton(
            lf, text="Enable Mesh Test Mode",
            variable=self._app.mesh_enabled_var,
            command=self._on_enable_toggle,
        )
        self._enable_cb.grid(row=row, column=0, columnspan=2, sticky="w", pady=2)
        row += 1

        # Node role
        ttk.Label(lf, text="Node Role:").grid(row=row, column=0, sticky="w", pady=2)
        self._role_cb = ttk.Combobox(
            lf, textvariable=self._app.mesh_node_role_var,
            values=["ENDPOINT", "REPEATER"], state="readonly", width=12,
        )
        self._role_cb.grid(row=row, column=1, sticky="ew", padx=(6, 0), pady=2)
        row += 1

        # Default TTL
        ttk.Label(lf, text="Default TTL:").grid(row=row, column=0, sticky="w", pady=2)
        self._ttl_sb = ttk.Spinbox(
            lf, textvariable=self._app.mesh_default_ttl_var,
            from_=1, to=8, width=5,
        )
        self._ttl_sb.grid(row=row, column=1, sticky="w", padx=(6, 0), pady=2)
        row += 1

        # Rate limit ppm
        ttk.Label(lf, text="Rate Limit (ppm):").grid(row=row, column=0, sticky="w", pady=2)
        self._rate_sb = ttk.Spinbox(
            lf, textvariable=self._app.mesh_rate_limit_ppm_var,
            from_=1, to=60, width=5,
        )
        self._rate_sb.grid(row=row, column=1, sticky="w", padx=(6, 0), pady=2)
        row += 1

        # HELLO beacons
        self._hello_cb = ttk.Checkbutton(
            lf, text="HELLO Beacons",
            variable=self._app.mesh_hello_enabled_var,
        )
        self._hello_cb.grid(row=row, column=0, columnspan=2, sticky="w", pady=2)
        row += 1

        # Apply button
        self._apply_btn = ttk.Button(lf, text="Apply Config", command=self._apply_config)
        self._apply_btn.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(6, 0))

        self._meshctrl_widgets = [
            self._role_cb, self._ttl_sb, self._rate_sb,
            self._hello_cb, self._apply_btn,
        ]

    # ------------------------------------------------------------------
    # Discovery section
    # ------------------------------------------------------------------

    def _build_discovery(self, parent: ttk.Frame) -> None:
        lf = ttk.LabelFrame(parent, text="Discovery", padding=8)
        lf.grid(row=0, column=1, sticky="nsew", padx=(4, 0), pady=2)
        lf.columnconfigure(1, weight=1)

        ttk.Label(lf, text="Target Callsign:").grid(row=0, column=0, sticky="w", pady=2)
        self._disc_target_var = tk.StringVar()
        self._disc_entry = ttk.Entry(lf, textvariable=self._disc_target_var, width=14)
        self._disc_entry.grid(row=0, column=1, sticky="ew", padx=(6, 0), pady=2)
        # Enter in callsign field triggers discovery
        self._disc_entry.bind("<Return>", lambda _e: self._discover())

        self._disc_btn = ttk.Button(lf, text="▶ Discover Route", command=self._discover)
        self._disc_btn.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 2))

        ttk.Label(lf, text="Last Result:").grid(row=2, column=0, sticky="w", pady=2)
        self._disc_status_var = tk.StringVar(value="—")
        ttk.Label(lf, textvariable=self._disc_status_var, foreground="#aaaaaa",
                  wraplength=200, justify="left").grid(
            row=2, column=1, sticky="ew", padx=(6, 0), pady=2)

        self._disc_widgets = [self._disc_entry, self._disc_btn]

    # ------------------------------------------------------------------
    # Route table
    # ------------------------------------------------------------------

    def _build_routes(self, parent: ttk.Frame) -> None:
        lf = ttk.LabelFrame(parent, text="Routes", padding=4)
        lf.grid(row=1, column=0, sticky="nsew", padx=6, pady=4)
        lf.columnconfigure(0, weight=1)
        lf.rowconfigure(0, weight=1)

        cols = ("destination", "next_hop", "hops", "metric",
                "age_s", "expires_in_s", "learned_from", "pinned")
        self._route_tree = ttk.Treeview(
            lf, columns=cols, show="headings",
            height=self._app.display_cfg.route_tree_height,
            selectmode="browse",
        )
        col_widths = {
            "destination": 100, "next_hop": 100, "hops": 50, "metric": 55,
            "age_s": 60, "expires_in_s": 80, "learned_from": 80, "pinned": 50,
        }
        for c in cols:
            self._route_tree.heading(c, text=c.replace("_", " ").title())
            self._route_tree.column(c, width=col_widths.get(c, 80), anchor="center")
        vsb = ttk.Scrollbar(lf, orient="vertical", command=self._route_tree.yview)
        self._route_tree.configure(yscrollcommand=vsb.set)
        self._route_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")

        # Action buttons
        btn_row = ttk.Frame(lf)
        btn_row.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        self._invalidate_btn = ttk.Button(
            btn_row, text="Invalidate Route", command=self._invalidate_selected)
        self._invalidate_btn.pack(side="left", padx=2)
        self._pin_btn = ttk.Button(
            btn_row, text="Pin/Unpin", command=self._toggle_pin)
        self._pin_btn.pack(side="left", padx=2)

        self._route_widgets = [self._invalidate_btn, self._pin_btn]

    # ------------------------------------------------------------------
    # Mesh Send section
    # ------------------------------------------------------------------

    def _build_send(self, parent: ttk.Frame) -> None:
        lf = ttk.LabelFrame(parent, text="Mesh Send", padding=8)
        lf.grid(row=0, column=0, sticky="nsew", padx=(0, 4), pady=2)
        lf.columnconfigure(1, weight=1)
        lf.rowconfigure(1, weight=1)

        ttk.Label(lf, text="Destination:").grid(row=0, column=0, sticky="w", pady=2)
        self._send_dst_var = tk.StringVar()
        self._send_dst_entry = ttk.Entry(lf, textvariable=self._send_dst_var, width=14)
        self._send_dst_entry.grid(row=0, column=1, sticky="ew", padx=(6, 0), pady=2)
        # Tab from destination moves focus to message body
        self._send_dst_entry.bind("<Return>", lambda _e: self._send_text.focus_set())

        ttk.Label(lf, text="Message:").grid(row=1, column=0, sticky="nw", pady=2)
        self._send_text = tk.Text(lf, height=4, width=28, wrap="word")
        self._send_text.grid(row=1, column=1, sticky="nsew", padx=(6, 0), pady=2)
        # Ctrl+Enter sends from message body (plain Enter inserts newline)
        self._send_text.bind("<Control-Return>",
                             lambda _e: (self._send_mesh(), "break")[1])

        self._send_btn = ttk.Button(lf, text="▶ Send", command=self._send_mesh)
        self._send_btn.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(6, 0))

        self._send_widgets = [self._send_dst_entry, self._send_text, self._send_btn]

    # ------------------------------------------------------------------
    # Diagnostics section
    # ------------------------------------------------------------------

    def _build_diagnostics(self, parent: ttk.Frame) -> None:
        lf = ttk.LabelFrame(parent, text="Diagnostics", padding=8)
        lf.grid(row=0, column=1, sticky="nsew", pady=2)
        lf.columnconfigure(0, weight=1)
        lf.rowconfigure(1, weight=1)

        # Stats counters grid — label column + value column, 2 groups side by side
        stats_frame = ttk.Frame(lf)
        stats_frame.grid(row=0, column=0, sticky="ew", pady=(0, 4))

        self._stat_vars: dict[str, tk.StringVar] = {}
        # (internal_key, display_label) pairs
        stat_defs = [
            ("rreq_tx",     "RREQ TX"),  ("rreq_rx",     "RREQ RX"),
            ("rreq_fwd",    "RREQ fwd"), ("rreq_drop",   "RREQ drop"),
            ("rrep_tx",     "RREP TX"),  ("rrep_rx",     "RREP RX"),
            ("rrep_fwd",    "RREP fwd"), ("data_tx",     "Data TX"),
            ("data_rx",     "Data RX"),  ("data_fwd",    "Data fwd"),
            ("data_drop",   "Data drop"),("rerr_tx",     "RERR TX"),
            ("rerr_rx",     "RERR RX"),  ("hello_tx",    "HELLO TX"),
            ("hello_rx",    "HELLO RX"), ("dedupe_drop", "Dedupe drop"),
            ("ttl_drop",    "TTL drop"), ("rate_drop",   "Rate drop"),
            ("noroute_drop","No-route drop"), ("",        ""),
        ]
        # Lay out in 2 side-by-side groups of 10 rows (label + value each)
        for group in range(2):
            base_col = group * 3  # label, value, gap
            for row_in_group in range(10):
                idx = group * 10 + row_in_group
                if idx >= len(stat_defs):
                    break
                key, display = stat_defs[idx]
                if not key:
                    continue
                var = tk.StringVar(value="0")
                self._stat_vars[key] = var
                ttk.Label(stats_frame, text=display + ":",
                          font=("TkFixedFont", 8),
                          foreground="#888888").grid(
                    row=row_in_group, column=base_col, sticky="w", padx=(0, 2), pady=1)
                ttk.Label(stats_frame, textvariable=var,
                          font=("TkFixedFont", 8, "bold"),
                          foreground="#aaaaaa", width=4, anchor="e").grid(
                    row=row_in_group, column=base_col + 1, sticky="e", padx=(0, 12), pady=1)

        # Bounded log — height from DisplayConfig (shorter on RPi)
        self._mesh_log = BoundedLog(
            lf, height=self._app.display_cfg.mesh_log_height,
            width=40, state="disabled",
            font=("TkFixedFont", 8), wrap="word",
        )
        self._mesh_log.grid(row=1, column=0, sticky="nsew", pady=(0, 0))

    # ------------------------------------------------------------------
    # Public API (called by HamHatApp)
    # ------------------------------------------------------------------

    def apply_profile(self, p: "AppProfile") -> None:
        """Called during profile load — vars already set by app, just refresh UI."""
        self._refresh_enabled_state()

    def collect_profile(self, p: "AppProfile") -> None:
        """Mesh fields are collected directly from Tk vars in app._collect_profile_snapshot."""
        pass

    def append_log(self, msg: str) -> None:
        """Add a line to the mesh diagnostics log."""
        ts = time.strftime("%H:%M:%S")
        self._mesh_log.append(f"[{ts}] {msg}")
        self._refresh_stats()

    def refresh_routes(self) -> None:
        """Rebuild the route treeview from current MeshManager state."""
        self._refresh_route_table()

    # ------------------------------------------------------------------
    # Internal handlers
    # ------------------------------------------------------------------

    def _on_enable_toggle(self) -> None:
        self._apply_config()
        self._refresh_enabled_state()

    def _apply_config(self) -> None:
        self._app.mesh_apply_config()
        enabled = self._app.mesh_enabled_var.get()
        self.append_log(f"Mesh config applied (enabled={enabled})")

    def _refresh_enabled_state(self) -> None:
        enabled = self._app.mesh_enabled_var.get()
        state = "normal" if enabled else "disabled"
        for w in self._meshctrl_widgets:
            try:
                w.configure(state=state)
            except Exception:
                pass
        for w in self._disc_widgets + self._send_widgets + self._route_widgets:
            try:
                w.configure(state=state)
            except Exception:
                pass
        # Text widget state
        try:
            self._send_text.configure(state=state)
        except Exception:
            pass

    def _discover(self) -> None:
        target = self._disc_target_var.get().strip().upper()
        if not target:
            self._disc_status_var.set("Enter a callsign first")
            return
        self._disc_status_var.set(f"Discovering {target}…")
        self._app.mesh_discover(target)
        # Check if we already have the route
        self._refresh_route_table()

    def _send_mesh(self) -> None:
        dst = self._send_dst_var.get().strip().upper()
        body = self._send_text.get("1.0", "end").strip()
        if not dst:
            messagebox.showwarning("Mesh Send", "Enter a destination callsign.", parent=self)
            return
        if not body:
            messagebox.showwarning("Mesh Send", "Enter a message body.", parent=self)
            return
        if len(body) > 240:
            messagebox.showwarning(
                "Mesh Send",
                f"Message is {len(body)} chars; max 240. It will be chunked.",
                parent=self,
            )
        self._app.mesh_send(dst, body)
        self._send_text.delete("1.0", "end")

    def _invalidate_selected(self) -> None:
        sel = self._route_tree.selection()
        if not sel:
            return
        dst = self._route_tree.item(sel[0], "values")[0]
        self._app.mesh.invalidate_route(dst)
        self.append_log(f"Route to {dst} invalidated")
        self._refresh_route_table()

    def _toggle_pin(self) -> None:
        sel = self._route_tree.selection()
        if not sel:
            return
        dst = self._route_tree.item(sel[0], "values")[0]
        new_state = self._app.mesh.toggle_pin(dst)
        if new_state is not None:
            self.append_log(f"Route to {dst} pinned={new_state}")
            self._refresh_route_table()

    def _refresh_route_table(self) -> None:
        now = time.monotonic()
        routes = self._app.mesh.get_routes(now)
        for item in self._route_tree.get_children():
            self._route_tree.delete(item)
        for r in routes:
            age_s = int(now - r.last_seen_ts)
            expires_in = max(0, int(r.expiry_ts - now))
            self._route_tree.insert("", "end", values=(
                r.destination,
                r.next_hop,
                r.hop_count,
                r.metric,
                age_s,
                expires_in,
                r.learned_from,
                "Y" if r.pinned else "N",
            ))
        # Update discovery status if target found
        target = self._disc_target_var.get().strip().upper()
        if target and any(r.destination == target for r in routes):
            route = next(r for r in routes if r.destination == target)
            self._disc_status_var.set(
                f"Route found: via {route.next_hop}, {route.hop_count} hop(s)")
        self._refresh_stats()

    def _refresh_stats(self) -> None:
        stats = self._app.mesh.get_stats()
        for name, var in self._stat_vars.items():
            val = getattr(stats, name, 0)
            var.set(str(val))

    def _auto_refresh_routes(self) -> None:
        try:
            self._refresh_route_table()
        except Exception:
            pass
        self.after(self.ROUTE_REFRESH_MS, self._auto_refresh_routes)

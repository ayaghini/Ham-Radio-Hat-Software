#!/usr/bin/env python3
"""CommsTab — Merged APRS Comms tab.

Layout:
  Left panel : APRS Source, RX Monitor, Contacts (click → open thread),
               Groups, Heard stations, Intro/Position TX
  Right panel: Stations Map, Messages (shows active contact thread), Compose, APRS Log
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from typing import TYPE_CHECKING

from ..engine.models import ChatMessage
from .widgets import TiledMapCanvas, BoundedLog, add_row, scrollable_frame

if TYPE_CHECKING:
    from ..app import HamHatApp


class CommsTab(ttk.Frame):
    """Merged APRS Comms tab — source/monitor controls, contacts, map, chat, log."""

    def __init__(self, parent: ttk.Notebook, app: "HamHatApp") -> None:
        super().__init__(parent)
        self._app = app
        self._build()

    # ------------------------------------------------------------------
    # Build layout
    # ------------------------------------------------------------------

    def _build(self) -> None:
        self.columnconfigure(0, weight=0, minsize=260)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        left_host = ttk.Frame(self, padding=(6, 6, 4, 6))
        left_host.grid(row=0, column=0, sticky="nsew")

        right = ttk.Frame(self, padding=(4, 6, 6, 6))
        right.grid(row=0, column=1, sticky="nsew")

        self._build_left(left_host)
        self._build_right(right)

    # ------------------------------------------------------------------
    # Left panel
    # ------------------------------------------------------------------

    def _build_left(self, parent: ttk.Frame) -> None:
        cfg = self._app.display_cfg
        _sp = cfg.compact_padding
        _mf = cfg.mono_font
        _canvas, _vsb, inner = scrollable_frame(parent)
        inner.columnconfigure(0, weight=1)
        row = 0

        # ---- APRS Source ----
        sf = ttk.LabelFrame(inner, text="APRS Source", padding=6)
        sf.grid(row=row, column=0, sticky="ew", pady=(0, _sp))
        sf.columnconfigure(1, weight=1)
        row += 1

        ttk.Label(sf, text="Callsign:").grid(row=0, column=0, sticky="w")
        ttk.Entry(sf, textvariable=self._app.aprs_source_var, width=16,
                  font=(_mf, 9)).grid(row=0, column=1, sticky="ew", padx=(6, 0))

        # ---- RX Monitor ----
        rf = ttk.LabelFrame(inner, text="RX Monitor", padding=6)
        rf.grid(row=row, column=0, sticky="ew", pady=(0, _sp))
        rf.columnconfigure(0, weight=1)
        row += 1

        btn_row = ttk.Frame(rf)
        btn_row.grid(row=0, column=0, sticky="ew")
        ttk.Button(btn_row, text="▶ Start", command=self._app.start_rx_monitor,
                   width=8).pack(side="left")
        ttk.Button(btn_row, text="■ Stop", command=self._app.stop_rx_monitor,
                   width=8).pack(side="left", padx=(4, 0))
        ttk.Button(btn_row, text="One-Shot", command=self._app.rx_one_shot,
                   width=8).pack(side="left", padx=(4, 0))
        self._rx_status_lbl = ttk.Label(btn_row, text="", foreground="#5db85d")
        self._rx_status_lbl.pack(side="left", padx=(10, 0))

        info_row = ttk.Frame(rf)
        info_row.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        ttk.Label(info_row, text="Level:").pack(side="left")
        ttk.Label(info_row, textvariable=self._app.aprs_rx_level_var,
                  width=5).pack(side="left", padx=(2, 8))
        ttk.Label(info_row, text="Clip:").pack(side="left")
        ttk.Label(info_row, textvariable=self._app.rx_clip_var,
                  width=6).pack(side="left", padx=(2, 8))

        chk_row = ttk.Frame(rf)
        chk_row.grid(row=2, column=0, sticky="ew", pady=(4, 0))
        ttk.Checkbutton(chk_row, text="Auto-ACK",
                        variable=self._app.aprs_auto_ack_var).pack(side="left")
        ttk.Checkbutton(chk_row, text="Always-on",
                        variable=self._app.aprs_rx_auto_var,
                        command=self._app.on_rx_auto_toggle).pack(side="left", padx=(8, 0))

        # ---- Contacts ----
        lf = ttk.LabelFrame(inner, text="Contacts  (click to open thread)", padding=6)
        lf.grid(row=row, column=0, sticky="ew", pady=(0, _sp))
        lf.columnconfigure(0, weight=1)
        row += 1

        self._contacts_lb = tk.Listbox(lf, height=cfg.contacts_height,
                                       exportselection=False, font=(_mf, 9))
        self._contacts_lb.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        self._contacts_lb.bind("<<ListboxSelect>>", self._on_contact_select)

        btn_row = ttk.Frame(lf)
        btn_row.grid(row=1, column=0, columnspan=2, sticky="ew")
        ttk.Button(btn_row, text="Add…", command=self._add_contact,
                   width=8).pack(side="left", padx=(0, 2))
        ttk.Button(btn_row, text="Remove", command=self._remove_contact,
                   width=8).pack(side="left", padx=2)
        ttk.Button(btn_row, text="← Heard", command=self._import_heard_to_contacts,
                   width=8).pack(side="left", padx=2)

        # ---- Groups ----
        gf = ttk.LabelFrame(inner, text="Groups  (click to open thread)", padding=6)
        gf.grid(row=row, column=0, sticky="ew", pady=(0, _sp))
        gf.columnconfigure(0, weight=1)
        row += 1

        self._groups_lb = tk.Listbox(gf, height=cfg.groups_height,
                                     exportselection=False, font=(_mf, 9))
        self._groups_lb.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 4))
        self._groups_lb.bind("<<ListboxSelect>>", self._on_group_select)

        btn_row2 = ttk.Frame(gf)
        btn_row2.grid(row=1, column=0, columnspan=2, sticky="ew")
        ttk.Button(btn_row2, text="New…", command=self._new_group,
                   width=8).pack(side="left", padx=(0, 2))
        ttk.Button(btn_row2, text="Edit…", command=self._edit_group,
                   width=8).pack(side="left", padx=2)
        ttk.Button(btn_row2, text="Delete", command=self._delete_group,
                   width=8).pack(side="left", padx=2)

        self._group_members_var = tk.StringVar(value="")
        ttk.Label(gf, textvariable=self._group_members_var, foreground="#9cc4dd",
                  font=(_mf, 8), wraplength=230).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(4, 0))

        # ---- Heard Stations ----
        hf = ttk.LabelFrame(inner, text="Heard Stations  (click to open thread)", padding=6)
        hf.grid(row=row, column=0, sticky="ew", pady=(0, _sp))
        hf.columnconfigure(0, weight=1)
        row += 1

        self._heard_lb = tk.Listbox(hf, height=cfg.heard_height,
                                    exportselection=False, font=(_mf, 9))
        self._heard_lb.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        self._heard_lb.bind("<<ListboxSelect>>", self._on_heard_select)
        ttk.Button(hf, text="Clear Heard", command=self._clear_heard).grid(
            row=1, column=0, sticky="w")

        # ---- Intro + Position TX ----
        inf = ttk.LabelFrame(inner, text="Intro / Position TX", padding=6)
        inf.grid(row=row, column=0, sticky="ew", pady=(0, _sp))
        inf.columnconfigure(1, weight=1)
        row += 1

        self._intro_note_var = tk.StringVar(value="uConsole HAM HAT online")
        add_row(inf, "Note:", ttk.Entry(inf, textvariable=self._intro_note_var), row=0)
        add_row(inf, "Lat:", ttk.Entry(inf, textvariable=self._app.aprs_lat_var,
                                       width=12), row=1)
        add_row(inf, "Lon:", ttk.Entry(inf, textvariable=self._app.aprs_lon_var,
                                       width=12), row=2)
        add_row(inf, "Comment:", ttk.Entry(inf, textvariable=self._app.aprs_comment_var),
                row=3)

        intro_btns = ttk.Frame(inf)
        intro_btns.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(6, 0))
        ttk.Button(intro_btns, text="Send Intro",
                   command=self._send_intro).pack(side="left", padx=(0, 4))
        ttk.Button(intro_btns, text="Send Position",
                   command=self._send_position).pack(side="left")

    # ------------------------------------------------------------------
    # Right panel  (map, messages, compose, log)
    # ------------------------------------------------------------------

    def _build_right(self, parent: ttk.Frame) -> None:
        cfg = self._app.display_cfg
        _sp = cfg.compact_padding
        _mf = cfg.mono_font
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=0)  # map
        parent.rowconfigure(1, weight=1)  # messages
        parent.rowconfigure(2, weight=0)  # compose
        parent.rowconfigure(3, weight=0)  # APRS log

        # ---- Stations Map ----
        mf = ttk.LabelFrame(parent, text="Stations Map", padding=6)
        mf.grid(row=0, column=0, sticky="ew", pady=(0, _sp))
        mf.columnconfigure(0, weight=1)

        self._aprs_map = TiledMapCanvas(mf, self._app.tiles, height=cfg.map_height)
        self._aprs_map.grid(row=0, column=0, sticky="ew")
        self._aprs_map.set_on_pick(
            lambda lat, lon, label: self.append_log(
                f"Map pick: {label} @ {lat:.5f}, {lon:.5f}"))

        map_btns = ttk.Frame(mf)
        map_btns.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        ttk.Button(map_btns, text="Clear",
                   command=self._clear_map).pack(side="left")
        ttk.Button(map_btns, text="Open in Browser",
                   command=self._open_map_in_browser).pack(side="left", padx=(6, 0))
        ttk.Button(map_btns, text="Download Tiles…",
                   command=self._open_download_dialog).pack(side="left", padx=(6, 0))

        # ---- Message area ----
        msf = ttk.LabelFrame(parent, text="Messages", padding=6)
        msf.grid(row=1, column=0, sticky="nsew", pady=(0, _sp))
        msf.columnconfigure(0, weight=1)
        msf.rowconfigure(1, weight=1)

        # Thread indicator shown at top of messages section
        self._thread_label = ttk.Label(msf, text="Select a contact to start a conversation",
                                       foreground="#9cc4dd", font=("TkDefaultFont", 8))
        self._thread_label.grid(row=0, column=0, sticky="w", pady=(0, 4))

        self._msg_log = BoundedLog(msf, state="disabled", wrap="word",
                                   font=(_mf, 9), background="#0f2531",
                                   foreground="#d9edf7", height=cfg.log_height_comms)
        self._msg_log.grid(row=1, column=0, sticky="nsew")

        # Chat-bubble colour tags.
        # TX (right side): sender name muted blue, message body light blue.
        # RX (left side): sender name muted amber, message body amber.
        self._msg_log.tag_configure("tx_name", foreground="#4a7a9b",
                                    font=(_mf, 8), justify="right", spacing1=10)
        self._msg_log.tag_configure("tx_msg",  foreground="#cce8f8", justify="right")
        self._msg_log.tag_configure("tx_ok",   foreground="#5dba6e", justify="right")
        self._msg_log.tag_configure("tx_fail", foreground="#e07070", justify="right")
        self._msg_log.tag_configure("rx_name", foreground="#b07020",
                                    font=(_mf, 8), justify="left", spacing1=10)
        self._msg_log.tag_configure("rx_msg",  foreground="#f5a623", justify="left")
        self._msg_log.tag_configure("sys",     foreground="#9cc4dd", justify="center",
                                    spacing1=4, spacing3=4)
        self._msg_log.bind("<Configure>", self._on_msg_log_resize)

        # ---- Compose area ----
        cf = ttk.LabelFrame(parent, text="Send Message", padding=6)
        cf.grid(row=2, column=0, sticky="ew", pady=(0, _sp))
        cf.columnconfigure(0, weight=1)

        self._compose_text = tk.Text(cf, height=cfg.compose_height,
                                     wrap="word", font=(_mf, 9))
        self._compose_text.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        self._compose_text.bind("<Return>", self._on_compose_enter)
        self._compose_text.bind("<Shift-Return>", lambda _e: None)

        comp_btn_row = ttk.Frame(cf)
        comp_btn_row.grid(row=1, column=0, sticky="e")
        self._reliable_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(comp_btn_row, text="Reliable",
                        variable=self._reliable_var).pack(side="left", padx=(0, 8))
        ttk.Button(comp_btn_row, text="Send",
                   command=self._send_message).pack(side="left")

        # ---- APRS Log ----
        lf = ttk.LabelFrame(parent, text="APRS Log", padding=4)
        lf.grid(row=3, column=0, sticky="ew")
        lf.columnconfigure(0, weight=1)
        lf.rowconfigure(0, weight=1)

        self._aprs_log_box = BoundedLog(lf, height=cfg.log_height_aprs,
                                        state="disabled", font=(_mf, 8),
                                        background="#0a1a22", foreground="#9cc4dd")
        self._aprs_log_box.grid(row=0, column=0, sticky="nsew")

    # ------------------------------------------------------------------
    # Contacts management
    # ------------------------------------------------------------------

    def _add_contact(self) -> None:
        call = simpledialog.askstring("Add Contact", "Callsign:", parent=self)
        if call:
            self._app.add_contact(call)

    def _remove_contact(self) -> None:
        sel = self._contacts_lb.curselection()
        if not sel:
            return
        call = self._contacts_lb.get(sel[0]).split(" ")[0]  # strip unread marker
        if messagebox.askyesno("Remove Contact", f"Remove {call}?", parent=self):
            self._app.remove_contact(call)

    def _import_heard_to_contacts(self) -> None:
        self._app.import_heard_to_contacts()

    def _clear_heard(self) -> None:
        self._app.clear_heard()

    # ------------------------------------------------------------------
    # Group management
    # ------------------------------------------------------------------

    def _new_group(self) -> None:
        name = simpledialog.askstring("New Group", "Group name:", parent=self)
        if not name:
            return
        members_str = simpledialog.askstring(
            "Group Members",
            "Members (comma-separated callsigns):",
            parent=self,
        )
        if members_str is None:
            return
        members = [m.strip() for m in members_str.split(",") if m.strip()]
        self._app.set_group(name, members)

    def _edit_group(self) -> None:
        sel = self._groups_lb.curselection()
        if not sel:
            return
        name = self._groups_lb.get(sel[0]).split(" ")[0]
        groups = self._app.comms.groups
        current = groups.get(name, [])
        members_str = simpledialog.askstring(
            "Edit Group Members",
            f"Members of {name} (comma-separated):",
            initialvalue=", ".join(current),
            parent=self,
        )
        if members_str is None:
            return
        members = [m.strip() for m in members_str.split(",") if m.strip()]
        self._app.set_group(name, members)

    def _delete_group(self) -> None:
        sel = self._groups_lb.curselection()
        if not sel:
            return
        name = self._groups_lb.get(sel[0]).split(" ")[0]
        if messagebox.askyesno("Delete Group", f"Delete group {name}?", parent=self):
            self._app.delete_group(name)

    def _on_group_select(self, _e: tk.Event) -> None:
        sel = self._groups_lb.curselection()
        if not sel:
            self._group_members_var.set("")
            return
        name = self._groups_lb.get(sel[0]).split(" ")[0]
        groups = self._app.comms.groups
        members = groups.get(name, [])
        self._group_members_var.set(
            "Members: " + ", ".join(members) if members else "No members")
        # Open the group's message thread
        self._activate_thread(f"GROUP:{name}")

    # ------------------------------------------------------------------
    # Thread activation — called by all list selection handlers
    # ------------------------------------------------------------------

    def _activate_thread(self, thread_key: str) -> None:
        """Set the active thread and load its messages."""
        self._app.comms.set_active_thread(thread_key)
        self._load_thread(thread_key)
        # Update thread indicator label
        if thread_key.startswith("GROUP:"):
            label_text = f"Group: {thread_key[6:]}"
        else:
            label_text = f"→ {thread_key}"
        self._thread_label.configure(text=label_text)
        # Refresh contact/heard lists to update unread markers
        self.refresh_contacts()
        self.refresh_heard()

    def _on_contact_select(self, _e: tk.Event) -> None:
        sel = self._contacts_lb.curselection()
        if not sel:
            return
        call = self._contacts_lb.get(sel[0]).split(" ")[0]  # strip unread marker
        self._activate_thread(call)

    def _on_heard_select(self, _e: tk.Event) -> None:
        sel = self._heard_lb.curselection()
        if not sel:
            return
        call = self._heard_lb.get(sel[0]).split(" ")[0]
        self._activate_thread(call)

    # ------------------------------------------------------------------
    # Intro + Position TX
    # ------------------------------------------------------------------

    def _send_intro(self) -> None:
        self._app.send_intro(self._intro_note_var.get())

    def _send_position(self) -> None:
        self._app.send_aprs_position()

    # ------------------------------------------------------------------
    # Map helpers
    # ------------------------------------------------------------------

    def _clear_map(self) -> None:
        self._aprs_map.clear()
        self.append_log("Map cleared")

    def _open_map_in_browser(self) -> None:
        import webbrowser
        pos = self._aprs_map.last_position
        if not pos:
            messagebox.showinfo("Map", "No APRS position plotted yet.", parent=self)
            return
        lat, lon, _ = pos
        url = (f"https://www.openstreetmap.org/?mlat={lat:.6f}"
               f"&mlon={lon:.6f}#map=13/{lat:.6f}/{lon:.6f}")
        webbrowser.open(url, new=2)

    def _open_download_dialog(self) -> None:
        DownloadRegionDialog(self, self._app.tiles, self._aprs_map)

    # ------------------------------------------------------------------
    # Thread & message handling
    # ------------------------------------------------------------------

    def _load_thread(self, thread_key: str) -> None:
        msgs = self._app.comms.messages_for_thread(thread_key)
        self._msg_log.configure(state="normal")
        self._msg_log.delete("1.0", "end")
        for msg in msgs:
            self._render_message(msg)
        self._msg_log.configure(state="disabled")
        self._msg_log.see("end")

    def _render_message(self, msg: ChatMessage) -> None:
        """Append a message in chat-bubble style: TX right, RX left."""
        self._msg_log.configure(state="normal")
        if msg.direction == "TX":
            self._msg_log.insert("end", f"{msg.src} → {msg.dst}\n", ("tx_name",))
            if msg.failed:
                self._msg_log.insert("end", msg.text + " !\n", ("tx_fail",))
            elif msg.delivered:
                self._msg_log.insert("end", msg.text + " ✓\n", ("tx_ok",))
            else:
                self._msg_log.insert("end", msg.text + "\n", ("tx_msg",))
        elif msg.direction == "RX":
            self._msg_log.insert("end", msg.src + "\n", ("rx_name",))
            self._msg_log.insert("end", msg.text + "\n", ("rx_msg",))
        else:
            self._msg_log.insert("end", msg.text + "\n", ("sys",))
        self._msg_log.configure(state="disabled")
        self._msg_log.see("end")

    def _on_compose_enter(self, event: tk.Event) -> str:
        """Send on Enter (not Shift+Enter)."""
        if not (event.state & 0x1):  # shift not held
            self._send_message()
            return "break"
        return ""  # allow newline

    def _send_message(self) -> None:
        """Send to the currently active thread (contact or group)."""
        thread_key = self._app.comms.active_thread
        text = self._compose_text.get("1.0", "end-1c").strip()
        if not thread_key or not text:
            return
        reliable = self._reliable_var.get()
        if thread_key.startswith("GROUP:"):
            group = thread_key[6:]
            self._app.send_group_message(group, text)
        else:
            self._app.send_direct_message(thread_key, text, reliable=reliable)
        self._compose_text.delete("1.0", "end")

    # ------------------------------------------------------------------
    # Public update methods (called from app event dispatcher)
    # ------------------------------------------------------------------

    def _on_msg_log_resize(self, event: tk.Event) -> None:
        """Keep bubble margins proportional when the message area is resized."""
        margin = max(60, int(event.width * 0.28))
        for tag in ("tx_name", "tx_msg", "tx_ok", "tx_fail"):
            self._msg_log.tag_configure(tag, lmargin1=margin, lmargin2=margin)
        for tag in ("rx_name", "rx_msg"):
            self._msg_log.tag_configure(tag, rmargin=margin)

    def on_message(self, msg: ChatMessage) -> None:
        """Called when a new message arrives (on main thread via after())."""
        active = self._app.comms.active_thread
        if msg.thread_key == active:
            self._render_message(msg)
        # Update unread indicators in contact/heard lists
        self.refresh_contacts()
        self.refresh_heard()

    def on_delivered(self, thread_key: str) -> None:
        """Called when a TX message in thread_key receives its ACK."""
        if thread_key == self._app.comms.active_thread:
            self._load_thread(thread_key)

    def on_message_updated(self, thread_key: str) -> None:
        """Reload the active thread after a delivery-state change."""
        if thread_key == self._app.comms.active_thread:
            self._load_thread(thread_key)

    def refresh_contacts(self) -> None:
        """Rebuild contacts and group listboxes, highlighting active thread and unread."""
        comms = self._app.comms
        active = comms.active_thread

        # Save current selections so we can restore them after rebuild
        prev_contact_sel = self._contacts_lb.curselection()
        prev_group_sel = self._groups_lb.curselection()

        self._contacts_lb.delete(0, "end")
        for i, c in enumerate(comms.contacts):
            thread_key = c
            unread = comms.unread_for_thread(thread_key)
            label = f"{c}  ● new" if unread else c
            self._contacts_lb.insert("end", label)
            if thread_key == active:
                self._contacts_lb.selection_set(i)

        self._groups_lb.delete(0, "end")
        for i, (name, members) in enumerate(comms.groups.items()):
            thread_key = f"GROUP:{name}"
            unread = comms.unread_for_thread(thread_key)
            label = f"{name}  ({len(members)})  ● new" if unread else f"{name}  ({len(members)})"
            self._groups_lb.insert("end", label)
            if thread_key == active:
                self._groups_lb.selection_set(i)

    def refresh_heard(self) -> None:
        """Rebuild heard-stations list, highlighting active thread and unread."""
        comms = self._app.comms
        active = comms.active_thread

        self._heard_lb.delete(0, "end")
        for i, call in enumerate(comms.heard):
            unread = comms.unread_for_thread(call)
            label = f"{call}  ● new" if unread else call
            self._heard_lb.insert("end", label)
            if call == active:
                self._heard_lb.selection_set(i)

    # ------------------------------------------------------------------
    # Public API methods replacing aprs_tab (called from app dispatcher)
    # ------------------------------------------------------------------

    def append_log(self, msg: str) -> None:
        """Append a line to the APRS log box."""
        self._aprs_log_box.append(msg)

    def set_monitor_active(self, active: bool) -> None:
        """Update the RX monitor status indicator label."""
        self._rx_status_lbl.configure(text="● MONITORING" if active else "")

    def set_input_level(self, level: float) -> None:
        """Update input level indicator."""
        pct = int(min(100, max(0, level * 100.0)))
        self._app.aprs_rx_level_var.set(f"{pct:3d}%")

    def set_output_level(self, level: float) -> None:
        """Update TX level (future: drive a TX level indicator)."""
        pass

    def push_waterfall(self, mono, rate: int) -> None:
        """Feed audio samples to the waterfall widget if present."""
        pass

    def set_rx_clip(self, pct: float) -> None:
        """Show RX clip percentage."""
        if pct > 5.0:
            self._app.rx_clip_var.set(f"⚠ {pct:.1f}%")
        else:
            self._app.rx_clip_var.set(f"{pct:.1f}%")

    def add_map_point(self, lat: float, lon: float, label: str) -> None:
        """Add a station to the map."""
        self._aprs_map.add_point(lat, lon, label)

    # ------------------------------------------------------------------
    # Profile integration — owns all APRS shared var apply/collect
    # ------------------------------------------------------------------

    def apply_profile(self, p) -> None:
        """Load profile values — handles all APRS shared vars (took over from aprs_tab)."""
        self._app.aprs_source_var.set(p.aprs_source)
        self._app.aprs_dest_var.set(p.aprs_dest)
        self._app.aprs_path_var.set(p.aprs_path)
        self._app.aprs_tx_gain_var.set(str(p.aprs_tx_gain))
        self._app.aprs_preamble_var.set(str(p.aprs_preamble_flags))
        self._app.aprs_repeats_var.set(str(p.aprs_tx_repeats))
        self._app.aprs_reinit_var.set(p.aprs_tx_reinit)
        self._app.aprs_symbol_table_var.set(p.aprs_symbol_table)
        self._app.aprs_symbol_var.set(p.aprs_symbol)
        self._app.aprs_msg_to_var.set(p.aprs_msg_to)
        self._app.aprs_msg_text_var.set(p.aprs_msg_text)
        self._app.aprs_reliable_var.set(p.aprs_reliable)
        self._app.aprs_ack_timeout_var.set(str(p.aprs_ack_timeout))
        self._app.aprs_ack_retries_var.set(str(p.aprs_ack_retries))
        self._app.aprs_auto_ack_var.set(p.aprs_auto_ack)
        self._app.aprs_lat_var.set(str(p.aprs_lat))
        self._app.aprs_lon_var.set(str(p.aprs_lon))
        self._app.aprs_comment_var.set(p.aprs_comment)
        self._app.aprs_rx_dur_var.set(str(p.aprs_rx_duration))
        self._app.aprs_rx_chunk_var.set(str(p.aprs_rx_chunk))
        self._app.aprs_rx_trim_var.set(p.aprs_rx_trim_db)
        self._app.aprs_rx_os_level_var.set(p.aprs_rx_os_level)
        self._app.aprs_rx_auto_var.set(p.aprs_rx_auto)
        # Local comms vars
        self._intro_note_var.set(getattr(p, "chat_intro_note", "uConsole HAM HAT online"))

    def collect_profile(self, p) -> None:
        """Write widget values back into profile object."""
        p.aprs_source = self._app.aprs_source_var.get().strip().upper()
        p.aprs_dest = self._app.aprs_dest_var.get().strip().upper()
        p.aprs_path = self._app.aprs_path_var.get().strip().upper()
        try:
            p.aprs_tx_gain = float(self._app.aprs_tx_gain_var.get())
        except ValueError:
            pass
        try:
            p.aprs_preamble_flags = int(self._app.aprs_preamble_var.get())
        except ValueError:
            pass
        try:
            p.aprs_tx_repeats = int(self._app.aprs_repeats_var.get())
        except ValueError:
            pass
        p.aprs_tx_reinit = self._app.aprs_reinit_var.get()
        p.aprs_symbol_table = self._app.aprs_symbol_table_var.get()
        p.aprs_symbol = self._app.aprs_symbol_var.get()
        p.aprs_msg_to = self._app.aprs_msg_to_var.get().strip().upper()
        p.aprs_msg_text = self._app.aprs_msg_text_var.get()
        p.aprs_reliable = self._app.aprs_reliable_var.get()
        try:
            p.aprs_ack_timeout = float(self._app.aprs_ack_timeout_var.get())
        except ValueError:
            pass
        try:
            p.aprs_ack_retries = int(self._app.aprs_ack_retries_var.get())
        except ValueError:
            pass
        p.aprs_auto_ack = self._app.aprs_auto_ack_var.get()
        try:
            p.aprs_lat = float(self._app.aprs_lat_var.get())
        except ValueError:
            pass
        try:
            p.aprs_lon = float(self._app.aprs_lon_var.get())
        except ValueError:
            pass
        p.aprs_comment = self._app.aprs_comment_var.get()
        try:
            p.aprs_rx_duration = float(self._app.aprs_rx_dur_var.get())
        except ValueError:
            pass
        try:
            p.aprs_rx_chunk = float(self._app.aprs_rx_chunk_var.get())
        except ValueError:
            pass
        p.aprs_rx_trim_db = float(self._app.aprs_rx_trim_var.get())
        p.aprs_rx_os_level = int(self._app.aprs_rx_os_level_var.get())
        p.aprs_rx_auto = self._app.aprs_rx_auto_var.get()
        # Local comms vars
        p.chat_intro_note = self._intro_note_var.get()


# ---------------------------------------------------------------------------
# Download Region Dialog
# ---------------------------------------------------------------------------

class DownloadRegionDialog(tk.Toplevel):
    """Dialog for downloading OSM tiles for a lat/lon region offline.

    Pre-fills from the current map center and zoom.
    Downloads tiles in a background thread with progress reporting.
    """

    _MAX_TILES_WARN = 500
    _MAX_TILES_HARD = 5_000

    def __init__(
        self,
        parent: tk.Widget,
        tile_provider,
        map_canvas: "TiledMapCanvas",
    ) -> None:
        super().__init__(parent)
        self.title("Download Offline Tiles")
        self.resizable(False, False)
        self.grab_set()

        self._tp = tile_provider
        self._map = map_canvas
        self._cancel_flag: list[bool] = [False]
        self._running = False

        self._build()
        self._prefill()
        self._update_estimate()
        self.transient(parent)

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        pad = dict(padx=8, pady=4)

        # --- Bounds ---
        bf = ttk.LabelFrame(self, text="Region Bounds (decimal degrees)", padding=8)
        bf.grid(row=0, column=0, columnspan=2, sticky="ew", **pad)
        bf.columnconfigure(1, weight=1)
        bf.columnconfigure(3, weight=1)

        ttk.Label(bf, text="Lat min:").grid(row=0, column=0, sticky="w")
        self._lat_min = ttk.Entry(bf, width=12)
        self._lat_min.grid(row=0, column=1, sticky="ew", padx=(4, 16))

        ttk.Label(bf, text="Lat max:").grid(row=0, column=2, sticky="w")
        self._lat_max = ttk.Entry(bf, width=12)
        self._lat_max.grid(row=0, column=3, sticky="ew", padx=(4, 0))

        ttk.Label(bf, text="Lon min:").grid(row=1, column=0, sticky="w", pady=(4, 0))
        self._lon_min = ttk.Entry(bf, width=12)
        self._lon_min.grid(row=1, column=1, sticky="ew", padx=(4, 16), pady=(4, 0))

        ttk.Label(bf, text="Lon max:").grid(row=1, column=2, sticky="w", pady=(4, 0))
        self._lon_max = ttk.Entry(bf, width=12)
        self._lon_max.grid(row=1, column=3, sticky="ew", padx=(4, 0), pady=(4, 0))

        # --- Zoom ---
        zf = ttk.LabelFrame(self, text="Zoom Range", padding=8)
        zf.grid(row=1, column=0, columnspan=2, sticky="ew", **pad)
        zf.columnconfigure(1, weight=1)
        zf.columnconfigure(3, weight=1)

        ttk.Label(zf, text="Min zoom:").grid(row=0, column=0, sticky="w")
        self._z_min = ttk.Spinbox(zf, from_=2, to=18, width=6)
        self._z_min.grid(row=0, column=1, sticky="w", padx=(4, 16))
        self._z_min.bind("<<Increment>>", lambda _e: self._update_estimate())
        self._z_min.bind("<<Decrement>>", lambda _e: self._update_estimate())
        self._z_min.bind("<FocusOut>", lambda _e: self._update_estimate())

        ttk.Label(zf, text="Max zoom:").grid(row=0, column=2, sticky="w")
        self._z_max = ttk.Spinbox(zf, from_=2, to=18, width=6)
        self._z_max.grid(row=0, column=3, sticky="w", padx=(4, 0))
        self._z_max.bind("<<Increment>>", lambda _e: self._update_estimate())
        self._z_max.bind("<<Decrement>>", lambda _e: self._update_estimate())
        self._z_max.bind("<FocusOut>", lambda _e: self._update_estimate())

        ttk.Label(zf, text="(Z13 = neighborhood,  Z15 = street level)",
                  foreground="#9cc4dd",
                  font=("TkDefaultFont", 8)).grid(
            row=1, column=0, columnspan=4, sticky="w", pady=(4, 0))

        # --- Estimate ---
        ef = ttk.Frame(self, padding=(8, 0))
        ef.grid(row=2, column=0, columnspan=2, sticky="ew")
        self._estimate_var = tk.StringVar(value="")
        ttk.Label(ef, textvariable=self._estimate_var,
                  foreground="#9cc4dd").pack(side="left")

        # --- Cache info ---
        self._cache_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self._cache_var,
                  font=("TkDefaultFont", 8),
                  foreground="#888888").grid(
            row=3, column=0, columnspan=2, sticky="w", padx=8)

        # --- Progress ---
        pf = ttk.Frame(self, padding=(8, 4))
        pf.grid(row=4, column=0, columnspan=2, sticky="ew")
        pf.columnconfigure(0, weight=1)
        self._progress = ttk.Progressbar(pf, length=320, maximum=100)
        self._progress.grid(row=0, column=0, sticky="ew")
        self._progress_lbl = ttk.Label(pf, text="", width=14, anchor="e")
        self._progress_lbl.grid(row=0, column=1, padx=(6, 0))

        # --- Buttons ---
        btnf = ttk.Frame(self, padding=(8, 4, 8, 8))
        btnf.grid(row=5, column=0, columnspan=2, sticky="ew")
        self._btn_download = ttk.Button(btnf, text="Download",
                                        command=self._start_download)
        self._btn_download.pack(side="left")
        self._btn_cancel = ttk.Button(btnf, text="Cancel",
                                      command=self._cancel, state="disabled")
        self._btn_cancel.pack(side="left", padx=(8, 0))
        ttk.Button(btnf, text="Close", command=self.destroy).pack(side="right")
        ttk.Button(btnf, text="Clear Cache",
                   command=self._clear_cache).pack(side="right", padx=(0, 8))

        # Update estimate when bounds change
        for var in (self._lat_min, self._lat_max,
                    self._lon_min, self._lon_max):
            var.bind("<FocusOut>", lambda _e: self._update_estimate())

        self._refresh_cache_label()

    # ------------------------------------------------------------------
    # Prefill from current map state
    # ------------------------------------------------------------------

    def _prefill(self) -> None:
        from ..engine.tile_provider import lat_lon_to_world_px, world_px_to_lat_lon, TILE_SIZE
        z = self._map._zoom
        clat = self._map._center_lat
        clon = self._map._center_lon

        # Derive approx visible bounds from a nominal 400×300 canvas
        w, h = self._map.winfo_width() or 400, self._map.winfo_height() or 300
        c_wx, c_wy = lat_lon_to_world_px(clat, clon, z)
        lat_n, lon_w = world_px_to_lat_lon(c_wx - w / 2, c_wy - h / 2, z)
        lat_s, lon_e = world_px_to_lat_lon(c_wx + w / 2, c_wy + h / 2, z)

        def _fmt(v: float) -> str:
            return f"{v:.5f}"

        self._lat_min.insert(0, _fmt(min(lat_n, lat_s)))
        self._lat_max.insert(0, _fmt(max(lat_n, lat_s)))
        self._lon_min.insert(0, _fmt(min(lon_w, lon_e)))
        self._lon_max.insert(0, _fmt(max(lon_w, lon_e)))

        z_lo = max(2, z - 2)
        z_hi = min(18, z + 2)
        self._z_min.delete(0, "end"); self._z_min.insert(0, str(z_lo))
        self._z_max.delete(0, "end"); self._z_max.insert(0, str(z_hi))

    # ------------------------------------------------------------------
    # Estimate
    # ------------------------------------------------------------------

    def _update_estimate(self) -> None:
        try:
            lamin = float(self._lat_min.get())
            lamax = float(self._lat_max.get())
            lomin = float(self._lon_min.get())
            lomax = float(self._lon_max.get())
            zmin = int(self._z_min.get())
            zmax = int(self._z_max.get())
        except ValueError:
            self._estimate_var.set("")
            return

        if zmin > zmax:
            self._estimate_var.set("⚠ Min zoom > max zoom")
            return

        count = self._tp.tile_count_for_region(lamin, lamax, lomin, lomax, zmin, zmax)
        mb = count * 10 / 1024  # rough estimate ~10 KB per tile
        text = f"~{count:,} tiles  (~{mb:.0f} MB)"
        if count > self._MAX_TILES_HARD:
            text += "  ⚠ Too large — reduce zoom range or area"
        elif count > self._MAX_TILES_WARN:
            text += "  ⚠ Large download"
        self._estimate_var.set(text)

    def _refresh_cache_label(self) -> None:
        n = self._tp.cached_tile_count()
        self._cache_var.set(f"Cached on disk: {n:,} tiles")

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------

    def _start_download(self) -> None:
        if self._running:
            return
        try:
            lamin = float(self._lat_min.get())
            lamax = float(self._lat_max.get())
            lomin = float(self._lon_min.get())
            lomax = float(self._lon_max.get())
            zmin = int(self._z_min.get())
            zmax = int(self._z_max.get())
        except ValueError:
            messagebox.showerror("Input Error",
                                 "Please enter valid numeric bounds.",
                                 parent=self)
            return

        if zmin > zmax:
            messagebox.showerror("Input Error",
                                 "Min zoom must be ≤ max zoom.",
                                 parent=self)
            return

        count = self._tp.tile_count_for_region(lamin, lamax, lomin, lomax, zmin, zmax)
        if count > self._MAX_TILES_HARD:
            messagebox.showerror(
                "Too Many Tiles",
                f"This region requires ~{count:,} tiles.\n"
                f"Please reduce the zoom range or area (max {self._MAX_TILES_HARD:,}).",
                parent=self,
            )
            return

        if not self._tp.pil_available:
            messagebox.showerror(
                "Pillow Not Installed",
                "Tile map requires Pillow.\n"
                "Run:  pip install Pillow",
                parent=self,
            )
            return

        self._running = True
        self._cancel_flag[0] = False
        self._btn_download.configure(state="disabled")
        self._btn_cancel.configure(state="normal")
        self._progress["value"] = 0
        self._progress_lbl.configure(text="Starting…")

        import threading
        threading.Thread(
            target=self._download_worker,
            args=(lamin, lamax, lomin, lomax, zmin, zmax),
            daemon=True,
        ).start()

    def _download_worker(
        self,
        lamin: float, lamax: float,
        lomin: float, lomax: float,
        zmin: int, zmax: int,
    ) -> None:
        def progress(done: int, total: int) -> None:
            pct = int(done / max(1, total) * 100)
            self.after(0, self._update_progress, done, total, pct)

        downloaded, skipped = self._tp.download_region(
            lamin, lamax, lomin, lomax, zmin, zmax,
            progress_cb=progress,
            cancel_flag=self._cancel_flag,
        )
        self.after(0, self._download_done, downloaded, skipped)

    def _update_progress(self, done: int, total: int, pct: int) -> None:
        try:
            self._progress["value"] = pct
            self._progress_lbl.configure(text=f"{done}/{total}")
        except tk.TclError:
            pass

    def _download_done(self, downloaded: int, skipped: int) -> None:
        try:
            self._running = False
            self._btn_download.configure(state="normal")
            self._btn_cancel.configure(state="disabled")
            self._progress["value"] = 100
            cancelled = self._cancel_flag[0]
            status = "Cancelled." if cancelled else "Done."
            self._progress_lbl.configure(
                text=f"{status} ↓{downloaded} skip{skipped}")
            self._refresh_cache_label()
            # Trigger map redraw to show newly cached tiles
            self._map._schedule_draw()
        except tk.TclError:
            pass

    def _cancel(self) -> None:
        self._cancel_flag[0] = True
        self._btn_cancel.configure(state="disabled")

    def _clear_cache(self) -> None:
        if messagebox.askyesno(
            "Clear Cache",
            "Delete all cached map tiles from disk?\nThis cannot be undone.",
            parent=self,
        ):
            self._tp.clear_disk_cache()
            self._refresh_cache_label()
            messagebox.showinfo("Cache Cleared",
                                "All cached tiles have been removed.",
                                parent=self)

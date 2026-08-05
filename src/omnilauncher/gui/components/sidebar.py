"""Sidebar component - modern inspired."""

import tkinter as tk
from typing import Callable, Dict, List, Tuple

from omnilauncher.gui.themes import get_theme


class SidebarButton(tk.Frame):
    def __init__(
        self,
        parent,
        key: str,
        icon: str,
        label: str,
        theme: Dict[str, str],
        command: Callable[[str], None],
        badge: str = "",
    ):
        super().__init__(parent, bg=theme["sidebar_bg"])
        self.key = key
        self.theme = theme
        self.command = command
        self.active = False
        self.badge = badge

        self.button = tk.Button(
            self,
            text=f" {icon}   {label}",
            anchor="w",
            font=("Segoe UI", 10),
            fg=theme["text_secondary"],
            bg=theme["sidebar_bg"],
            activebackground=theme["sidebar_hover"],
            activeforeground=theme["text_primary"],
            bd=0,
            relief="flat",
            padx=16,
            pady=10,
            command=lambda: self.command(self.key),
        )
        self.button.pack(fill="x", padx=6, pady=2)

        self.button.bind("<Enter>", self._on_enter)
        self.button.bind("<Leave>", self._on_leave)

        if badge:
            self.badge_label = tk.Label(
                self.button,
                text=badge,
                font=("Segoe UI", 7, "bold"),
                bg=self.button["bg"],
                fg=theme["accent"],
            )
            # place later via place - keep simple

    def _on_enter(self, e):
        if not self.active:
            self.button.configure(bg=self.theme["sidebar_hover"], fg=self.theme["text_primary"])

    def _on_leave(self, e):
        if not self.active:
            self.button.configure(bg=self.theme["sidebar_bg"], fg=self.theme["text_secondary"])

    def set_active(self, active: bool):
        self.active = active
        if active:
            self.button.configure(
                bg=self.theme["sidebar_active"],
                fg=self.theme["text_primary"],
                font=("Segoe UI", 10, "bold"),
            )
            # add accent left border effect via bg?
        else:
            self.button.configure(
                bg=self.theme["sidebar_bg"],
                fg=self.theme["text_secondary"],
                font=("Segoe UI", 10),
            )

    def update_theme(self, theme: Dict[str, str]):
        self.theme = theme
        self.configure(bg=theme["sidebar_bg"])
        if self.active:
            self.button.configure(bg=theme["sidebar_active"], fg=theme["text_primary"])
        else:
            self.button.configure(bg=theme["sidebar_bg"], fg=theme["text_secondary"])


class Sidebar(tk.Frame):
    def __init__(self, parent, theme: Dict[str, str], on_select: Callable[[str], None]):
        super().__init__(parent, bg=theme["sidebar_bg"], width=240)
        self.theme = theme
        self.on_select = on_select
        self.buttons: Dict[str, SidebarButton] = {}
        self.pack_propagate(False)

        # Logo area
        logo_frame = tk.Frame(self, bg=theme["sidebar_bg"], height=80)
        logo_frame.pack(fill="x", pady=(16, 8))
        logo_frame.pack_propagate(False)

        # Icon O like brand
        icon_canvas = tk.Canvas(logo_frame, width=48, height=48, bg=theme["sidebar_bg"], highlightthickness=0)
        icon_canvas.pack(side="left", padx=16)
        # draw hexagon O
        icon_canvas.create_oval(6, 6, 42, 42, fill=theme["card_bg"], outline=theme["accent"], width=2)
        icon_canvas.create_text(24, 26, text="O", font=("Segoe UI", 18, "bold"), fill=theme["accent"])

        text_frame = tk.Frame(logo_frame, bg=theme["sidebar_bg"])
        text_frame.pack(side="left", fill="y")
        tk.Label(
            text_frame,
            text="OmniLauncher",
            font=("Segoe UI", 12, "bold"),
            bg=theme["sidebar_bg"],
            fg=theme["text_primary"],
        ).pack(anchor="w")
        tk.Label(
            text_frame,
            text="MC  •  v0.2.0",
            font=("Segoe UI", 8),
            bg=theme["sidebar_bg"],
            fg=theme["text_muted"],
        ).pack(anchor="w")

        # separator
        sep = tk.Frame(self, bg=theme["separator"], height=1)
        sep.pack(fill="x", padx=16, pady=8)

        # nav - modern style with many sections
        nav_items: List[Tuple[str, str, str]] = [
            ("play", "▶", "Play"),
            ("instances", "◫", "Instances"),
            ("accounts", "◍", "Accounts"),
            ("mods", "⬢", "Mods"),
            ("explorer", "📁", "File Explorer"),
            ("servers", "🌐", "Servers"),
            ("friends", "👥", "Friends [Exp]"),
            ("skins", "☻", "Skins"),
            ("settings", "⚙", "Settings"),
            ("console", "▤", "Console"),
            ("about", "ℹ", "About"),
        ]

        nav_frame = tk.Frame(self, bg=theme["sidebar_bg"])
        nav_frame.pack(fill="x", padx=0, pady=4)

        for key, icon, label in nav_items:
            btn = SidebarButton(nav_frame, key, icon, label, theme, self._clicked)
            btn.pack(fill="x")
            self.buttons[key] = btn

        # spacer
        spacer = tk.Frame(self, bg=theme["sidebar_bg"])
        spacer.pack(fill="both", expand=True)

        # bottom user preview
        self.user_frame = tk.Frame(self, bg=theme["card_bg"], height=72)
        self.user_frame.pack(fill="x", padx=12, pady=12)
        self.user_frame.pack_propagate(False)

        self._build_user_preview()

        # footer actions
        bottom_actions = tk.Frame(self, bg=theme["sidebar_bg"])
        bottom_actions.pack(fill="x", padx=12, pady=(0, 12))

        tk.Button(
            bottom_actions,
            text="📁  Open Folder",
            anchor="w",
            font=("Segoe UI", 9),
            bg=theme["sidebar_bg"],
            fg=theme["text_muted"],
            activebackground=theme["sidebar_hover"],
            bd=0,
            command=lambda: self.on_select("open_folder"),
        ).pack(side="left")
        tk.Button(
            bottom_actions,
            text="⤓",
            font=("Segoe UI", 9),
            bg=theme["sidebar_bg"],
            fg=theme["text_muted"],
            bd=0,
        ).pack(side="right")

    def _build_user_preview(self):
        # clear
        for w in self.user_frame.winfo_children():
            w.destroy()
        theme = self.theme
        # avatar canvas
        av = tk.Canvas(self.user_frame, width=36, height=36, bg=theme["card_bg"], highlightthickness=0)
        av.pack(side="left", padx=12, pady=12)
        av.create_rectangle(0, 0, 36, 36, fill=theme["accent"], outline="")
        av.create_text(18, 20, text="S", font=("Segoe UI", 14, "bold"), fill="white")

        txt = tk.Frame(self.user_frame, bg=theme["card_bg"])
        txt.pack(side="left", fill="y", pady=8)

        self.user_name_label = tk.Label(
            txt,
            text="Steve",
            font=("Segoe UI", 10, "bold"),
            bg=theme["card_bg"],
            fg=theme["text_primary"],
            anchor="w",
        )
        self.user_name_label.pack(anchor="w")
        self.user_status_label = tk.Label(
            txt,
            text="Offline • Ready",
            font=("Segoe UI", 8),
            bg=theme["card_bg"],
            fg=theme["text_muted"],
            anchor="w",
        )
        self.user_status_label.pack(anchor="w")

    def _clicked(self, key: str):
        if key == "open_folder":
            self.on_select(key)
            return
        self.set_active(key)
        self.on_select(key)

    def set_active(self, key: str):
        for k, btn in self.buttons.items():
            btn.set_active(k == key)

    def update_user(self, username: str, status: str = "Offline • Ready"):
        self.user_name_label.configure(text=username)
        self.user_status_label.configure(text=status)

    def update_theme(self, theme: Dict[str, str]):
        self.theme = theme
        self.configure(bg=theme["sidebar_bg"])
        for child in self.winfo_children():
            try:
                child.configure(bg=theme["sidebar_bg"])
            except Exception:
                pass
        self.user_frame.configure(bg=theme["card_bg"])
        for btn in self.buttons.values():
            btn.update_theme(theme)
        self._build_user_preview()

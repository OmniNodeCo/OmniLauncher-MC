"""OmniLauncher-MC main application - modern inspired redesign.

Full-featured dark launcher with sidebar navigation, instance management,
account switching, extensive settings, console, skin preview.
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
import threading
import datetime
import webbrowser
from pathlib import Path
from typing import Dict, List, Optional

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# Try to import settings and services
from omnilauncher.config.settings import get_settings_manager, SettingsManager
from omnilauncher.gui.themes import get_theme, THEMES, ACCENT_PALETTE, FONTS
from omnilauncher.gui.components.sidebar import Sidebar
from omnilauncher.gui.components.cards import InstanceCard, AccountCard

try:
    from omnilauncher.services.versions import (
        get_version_list,
        get_release_versions,
        get_latest_version,
        refresh_cache,
    )
    from omnilauncher.services.accounts import AccountService
    from omnilauncher.services.instances import InstanceService, BLOCK_ICONS
    from omnilauncher.services.java import find_java_executables
    from omnilauncher.services.file_explorer import get_bookmarks as get_file_bookmarks
    from omnilauncher.services.crash_analyzer import analyze_crash
    from omnilauncher.gui.components.dialogs import CrashReportDialog, FileExplorerDialog
    from omnilauncher.services import launcher as launcher_svc
except Exception:

    def get_version_list(*a, **k):
        return [{"id": "1.21.1", "type": "release"}]

    def get_release_versions(*a, **k):
        return ["1.21.1", "1.20.1"]

    def get_latest_version(*a, **k):
        return "1.21.1"

    def refresh_cache():
        pass

    def analyze_crash(log):
        return []

    AccountService = None
    InstanceService = None
    BLOCK_ICONS = ["grass", "diamond", "tnt"]
    find_java_executables = lambda: []
    get_file_bookmarks = lambda x: []
    CrashReportDialog = None
    FileExplorerDialog = None
    launcher_svc = None


# ------------------------------------------------------------------
# Utilities
# ------------------------------------------------------------------

class ScrollableFrame(tk.Frame):
    def __init__(self, parent, theme, **kwargs):
        super().__init__(parent, bg=theme["bg"], **kwargs)
        self.theme = theme
        self.canvas = tk.Canvas(self, bg=theme["bg"], highlightthickness=0, bd=0)
        self.vsb = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview, bg=theme["scrollbar_bg"])
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.inner = tk.Frame(self.canvas, bg=theme["bg"])
        self.window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.window, width=e.width))

        # mousewheel
        self.canvas.bind_all("<MouseWheel>", self._on_wheel_windows)
        self.canvas.bind_all("<Button-4>", self._on_wheel_linux_up)
        self.canvas.bind_all("<Button-5>", self._on_wheel_linux_down)

    def _on_wheel_windows(self, event):
        try:
            if self.winfo_exists():
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass

    def _on_wheel_linux_up(self, event):
        try:
            self.canvas.yview_scroll(-1, "units")
        except Exception:
            pass

    def _on_wheel_linux_down(self, event):
        try:
            self.canvas.yview_scroll(1, "units")
        except Exception:
            pass


def open_folder(path: str):
    p = Path(path)
    if not p.exists():
        try:
            p.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
    try:
        if platform.system() == "Windows":
            os.startfile(str(p))  # type: ignore
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", str(p)])
        else:
            subprocess.Popen(["xdg-open", str(p)])
    except Exception as e:
        messagebox.showerror("Open Folder", f"Failed to open {path}\n{e}")


# ------------------------------------------------------------------
# Main App
# ------------------------------------------------------------------

class OmniLauncherApp:
    def __init__(self):
        self.settings: SettingsManager = get_settings_manager()
        self.theme_name = self.settings.get("appearance", "theme", default="dark")
        self.theme = get_theme(self.theme_name)

        self.root = tk.Tk()
        self.root.title("OmniLauncher-MC • v0.2.0")
        geom = self.settings.get("meta", "window_geometry", default="1180x760")
        self.root.geometry(geom)
        self.root.minsize(1060, 640)
        self.root.configure(bg=self.theme["bg"])
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        # Icon if available?
        try:
            # try to set icon from svg converted? fallback
            pass
        except Exception:
            pass

        # style
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except Exception:
            pass
        self._configure_styles()

        # services
        self.account_svc = AccountService(self.settings) if AccountService else None
        self.instance_svc = InstanceService(self.settings) if InstanceService else None

        # state
        self.current_page = "play"
        self.current_settings_subpage = "general"
        self.search_var = tk.StringVar()
        self.version_filter_var = tk.StringVar()
        self.play_version_var = tk.StringVar()
        self.play_account_var = tk.StringVar()
        self.ram_var = tk.IntVar(value=self.settings.get("java", "max_ram_mb", default=4096))
        self.status_var = tk.StringVar(value="Ready")
        self.progress_var = tk.IntVar(value=0)
        self.progress_max = 100

        # pages dict
        self.pages: Dict[str, tk.Frame] = {}
        self.settings_subpages: Dict[str, tk.Frame] = {}

        # build UI
        self._build_layout()

        # listeners for launcher state
        if launcher_svc:
            try:
                launcher_svc.add_status_listener(self._on_status_update)
                launcher_svc.add_progress_listener(self._on_progress_update)
                launcher_svc.add_console_listener(self._on_console_line)
            except Exception:
                pass

        # initial data
        self.root.after(100, self._initial_load)

        # polling as fallback
        self.root.after(200, self._poll_launcher_state)

    # styles
    def _configure_styles(self):
        th = self.theme
        self.style.configure("TFrame", background=th["bg"])
        self.style.configure("Card.TFrame", background=th["card_bg"])
        self.style.configure("Header.TFrame", background=th["header_bg"])
        self.style.configure("Footer.TFrame", background=th["footer_bg"])
        self.style.configure("TLabel", background=th["bg"], foreground=th["text_primary"], font=FONTS["body"])
        self.style.configure("Header.TLabel", background=th["header_bg"], foreground=th["text_primary"])
        self.style.configure("Card.TLabel", background=th["card_bg"], foreground=th["text_primary"])
        self.style.configure("Muted.TLabel", foreground=th["text_secondary"])
        self.style.configure("Title.TLabel", font=FONTS["title_large"], foreground=th["text_primary"])
        self.style.configure("Custom.TButton", font=FONTS["body_bold"])
        self.style.configure("Accent.TButton", background=th["accent"], foreground="white")
        self.style.configure("TEntry", fieldbackground=th["input_bg"], foreground=th["text_primary"])
        self.style.configure("TCombobox", fieldbackground=th["input_bg"], background=th["input_bg"], foreground=th["text_primary"])
        self.style.configure("Horizontal.TProgressbar", background=th["progress_fg"], troughcolor=th["progress_bg"], borderwidth=0, thickness=6)
        self.style.configure("TCheckbutton", background=th["card_bg"], foreground=th["text_primary"])
        self.style.configure("TNotebook", background=th["bg"], borderwidth=0)
        self.style.configure("TNotebook.Tab", background=th["card_bg"], foreground=th["text_secondary"], padding=[12, 6])
        self.style.map("TNotebook.Tab", background=[("selected", th["sidebar_active"])], foreground=[("selected", th["text_primary"])])

    def _build_layout(self):
        th = self.theme
        # main container
        container = tk.Frame(self.root, bg=th["bg"])
        container.pack(fill="both", expand=True)

        # sidebar
        self.sidebar = Sidebar(container, th, self._on_sidebar_select)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.set_active("play")

        # right side
        right = tk.Frame(container, bg=th["bg"])
        right.pack(side="right", fill="both", expand=True)

        # header
        self.header_frame = tk.Frame(right, bg=th["header_bg"], height=64)
        self.header_frame.pack(side="top", fill="x")
        self.header_frame.pack_propagate(False)

        self.header_title = tk.Label(
            self.header_frame,
            text="Play",
            font=("Segoe UI", 16, "bold"),
            bg=th["header_bg"],
            fg=th["text_primary"],
        )
        self.header_title.pack(side="left", padx=24, pady=12)

        self.header_sub = tk.Label(
            self.header_frame,
            text="Launch and manage your Minecraft worlds",
            font=("Segoe UI", 9),
            bg=th["header_bg"],
            fg=th["text_secondary"],
        )
        self.header_sub.pack(side="left", padx=6, pady=18)

        # header right actions
        hdr_right = tk.Frame(self.header_frame, bg=th["header_bg"])
        hdr_right.pack(side="right", padx=16)

        tk.Button(
            hdr_right,
            text="🔄 Refresh",
            font=("Segoe UI", 9),
            bg=th["card_bg"],
            fg=th["text_secondary"],
            bd=0,
            padx=12,
            pady=6,
            command=self._refresh_all,
            activebackground=th["card_hover"],
            activeforeground=th["text_primary"],
        ).pack(side="left", padx=4)

        tk.Button(
            hdr_right,
            text="📁 .minecraft",
            font=("Segoe UI", 9),
            bg=th["card_bg"],
            fg=th["text_secondary"],
            bd=0,
            padx=12,
            pady=6,
            command=lambda: open_folder(self.settings.minecraft_dir),
            activebackground=th["card_hover"],
        ).pack(side="left", padx=4)

        # pages container
        self.pages_container = tk.Frame(right, bg=th["bg"])
        self.pages_container.pack(side="top", fill="both", expand=True)

        # footer
        self.footer_frame = tk.Frame(right, bg=th["footer_bg"], height=56)
        self.footer_frame.pack(side="bottom", fill="x")
        self.footer_frame.pack_propagate(False)

        # status
        status_left = tk.Frame(self.footer_frame, bg=th["footer_bg"])
        status_left.pack(side="left", fill="y", padx=16, pady=8)

        self.status_label = tk.Label(
            status_left,
            textvariable=self.status_var,
            font=("Segoe UI", 9),
            bg=th["footer_bg"],
            fg=th["text_secondary"],
        )
        self.status_label.pack(side="left")

        self.progress = ttk.Progressbar(
            status_left,
            variable=self.progress_var,
            maximum=100,
            length=220,
            mode="determinate",
            style="Horizontal.TProgressbar",
        )
        self.progress.pack(side="left", padx=12, pady=10)

        # footer right: account + launch
        footer_right = tk.Frame(self.footer_frame, bg=th["footer_bg"])
        footer_right.pack(side="right", padx=16, pady=8)

        self.footer_version_label = tk.Label(
            footer_right,
            text="1.21.1 • Vanilla",
            font=("Segoe UI", 9),
            bg=th["footer_bg"],
            fg=th["text_muted"],
        )
        self.footer_version_label.pack(side="left", padx=12)

        self.launch_btn = tk.Button(
            footer_right,
            text="▶  PLAY",
            font=("Segoe UI", 11, "bold"),
            bg=th["play_button_bg"],
            fg="white",
            activebackground=th["play_button_hover"],
            bd=0,
            padx=28,
            pady=10,
            command=self._on_launch_clicked,
        )
        self.launch_btn.pack(side="left")
        self.launch_btn.bind("<Enter>", lambda e: self.launch_btn.configure(bg=th["play_button_hover"]))
        self.launch_btn.bind("<Leave>", lambda e: self.launch_btn.configure(bg=th["play_button_bg"]))

        # build pages
        self._build_play_page()
        self._build_instances_page()
        self._build_accounts_page()
        self._build_mods_page()
        self._build_explorer_page()
        self._build_servers_page()
        self._build_friends_page()
        self._build_skins_page()
        self._build_settings_page()
        self._build_console_page()
        self._build_about_page()

        # show play initially
        self._show_page("play")

    # ------------------------------------------------------------------
    # Pages builders
    # ------------------------------------------------------------------

    def _make_page(self, key: str) -> tk.Frame:
        th = self.theme
        f = tk.Frame(self.pages_container, bg=th["bg"])
        self.pages[key] = f
        return f

    # PLAY
    def _build_play_page(self):
        th = self.theme
        page = self._make_page("play")

        # split in 2 columns
        left = tk.Frame(page, bg=th["bg"])
        left.pack(side="left", fill="both", expand=True, padx=16, pady=16)
        right = tk.Frame(page, bg=th["bg"], width=340)
        right.pack(side="right", fill="y", padx=(0, 16), pady=16)
        right.pack_propagate(False)

        # banner news
        banner = tk.Frame(left, bg=th["card_bg"], height=140, highlightthickness=1, highlightbackground=th["card_border"])
        banner.pack(fill="x", pady=(0, 16))
        banner.pack_propagate(False)
        tk.Label(
            banner,
            text="Welcome to OmniLauncher • v0.2.0",
            font=("Segoe UI", 14, "bold"),
            bg=th["card_bg"],
            fg=th["text_primary"],
        ).pack(anchor="w", padx=20, pady=(16, 4))
        tk.Label(
            banner,
            text="Manage instances, accounts, mods, and launch any Minecraft version • Offline and Microsoft accounts • Full crash analyzer",
            font=("Segoe UI", 9),
            bg=th["card_bg"],
            fg=th["text_secondary"],
            wraplength=600,
            justify="left",
        ).pack(anchor="w", padx=20)
        tk.Label(
            banner,
            text="Built • Dark theme • Animated backgrounds • File explorer • Server browser • Friends list (experimental) • Modrinth / CurseForge ready",
            font=("Segoe UI", 8),
            bg=th["card_bg"],
            fg=th["text_muted"],
            wraplength=600,
            justify="left",
        ).pack(anchor="w", padx=20, pady=(8, 0))

        # selected instance card large
        self.play_instance_frame = tk.Frame(left, bg=th["card_bg"], highlightthickness=1, highlightbackground=th["card_border"])
        self.play_instance_frame.pack(fill="x", pady=(0, 16))

        self.play_inst_icon = tk.Canvas(self.play_instance_frame, width=80, height=80, bg=th["card_bg"], highlightthickness=0)
        self.play_inst_icon.pack(side="left", padx=16, pady=16)

        self.play_inst_text = tk.Frame(self.play_instance_frame, bg=th["card_bg"])
        self.play_inst_text.pack(side="left", fill="both", expand=True, pady=16)

        self.play_inst_name = tk.Label(
            self.play_inst_text,
            text="Latest Release",
            font=("Segoe UI", 16, "bold"),
            bg=th["card_bg"],
            fg=th["text_primary"],
            anchor="w",
        )
        self.play_inst_name.pack(anchor="w")
        self.play_inst_details = tk.Label(
            self.play_inst_text,
            text="1.21.1 • Vanilla • 0h played",
            font=("Segoe UI", 10),
            bg=th["card_bg"],
            fg=th["text_secondary"],
            anchor="w",
        )
        self.play_inst_details.pack(anchor="w", pady=2)
        self.play_inst_meta = tk.Label(
            self.play_inst_text,
            text="Never played • Default group",
            font=("Segoe UI", 8),
            bg=th["card_bg"],
            fg=th["text_muted"],
            anchor="w",
        )
        self.play_inst_meta.pack(anchor="w")

        # mid row: launch options
        opts_frame = tk.Frame(left, bg=th["bg"])
        opts_frame.pack(fill="x", pady=8)

        # version row
        v_frame = tk.Frame(opts_frame, bg=th["card_bg"], highlightthickness=1, highlightbackground=th["card_border"])
        v_frame.pack(side="left", fill="x", expand=True, padx=(0, 8), pady=4)

        tk.Label(v_frame, text="Version", font=("Segoe UI", 9, "bold"), bg=th["card_bg"], fg=th["text_primary"]).pack(anchor="w", padx=12, pady=(12, 2))
        self.version_combo = ttk.Combobox(v_frame, textvariable=self.play_version_var, state="readonly", width=28)
        self.version_combo.pack(padx=12, pady=(2, 8), fill="x")
        self.version_combo.bind("<<ComboboxSelected>>", lambda e: self._on_play_version_changed())

        tk.Label(v_frame, text="Show:", font=("Segoe UI", 8), bg=th["card_bg"], fg=th["text_muted"]).pack(anchor="w", padx=12)
        filter_frame = tk.Frame(v_frame, bg=th["card_bg"])
        filter_frame.pack(fill="x", padx=12, pady=(0, 12))
        self.show_snap_var = tk.BooleanVar(value=self.settings.get("general", "show_snapshots", default=False))
        self.show_beta_var = tk.BooleanVar(value=self.settings.get("general", "show_beta", default=False))
        self.show_alpha_var = tk.BooleanVar(value=self.settings.get("general", "show_alpha", default=False))
        tk.Checkbutton(filter_frame, text="Snapshots", variable=self.show_snap_var, bg=th["card_bg"], fg=th["text_secondary"], selectcolor=th["input_bg"], activebackground=th["card_bg"], command=self._reload_versions).pack(side="left")
        tk.Checkbutton(filter_frame, text="Beta", variable=self.show_beta_var, bg=th["card_bg"], fg=th["text_secondary"], selectcolor=th["input_bg"], activebackground=th["card_bg"], command=self._reload_versions).pack(side="left", padx=6)
        tk.Checkbutton(filter_frame, text="Alpha", variable=self.show_alpha_var, bg=th["card_bg"], fg=th["text_secondary"], selectcolor=th["input_bg"], activebackground=th["card_bg"], command=self._reload_versions).pack(side="left")

        # account row
        a_frame = tk.Frame(opts_frame, bg=th["card_bg"], highlightthickness=1, highlightbackground=th["card_border"])
        a_frame.pack(side="left", fill="x", expand=True, padx=(8, 0), pady=4)

        tk.Label(a_frame, text="Account", font=("Segoe UI", 9, "bold"), bg=th["card_bg"], fg=th["text_primary"]).pack(anchor="w", padx=12, pady=(12, 2))
        self.account_combo = ttk.Combobox(a_frame, textvariable=self.play_account_var, state="readonly", width=22)
        self.account_combo.pack(padx=12, pady=2, fill="x")
        self.account_combo.bind("<<ComboboxSelected>>", lambda e: self._on_account_combo_changed())

        self.play_account_sub = tk.Label(a_frame, text="Offline • Steve skin", font=("Segoe UI", 8), bg=th["card_bg"], fg=th["text_muted"])
        self.play_account_sub.pack(anchor="w", padx=12, pady=2)

        tk.Label(a_frame, text=f"RAM: {self.ram_var.get()} MB", font=("Segoe UI", 8), bg=th["card_bg"], fg=th["text_muted"]).pack(anchor="w", padx=12, pady=(8, 2))
        self.ram_scale = tk.Scale(
            a_frame,
            from_=1024,
            to=12288,
            orient="horizontal",
            variable=self.ram_var,
            bg=th["card_bg"],
            fg=th["text_secondary"],
            troughcolor=th["progress_bg"],
            highlightthickness=0,
            activebackground=th["accent"],
            resolution=256,
            command=lambda v: self.settings.set(int(float(v)), "java", "max_ram_mb"),
        )
        self.ram_scale.pack(fill="x", padx=12, pady=(0, 12))

        # quick play box
        quick = tk.Frame(left, bg=th["card_bg"], highlightthickness=1, highlightbackground=th["card_border"])
        quick.pack(fill="x", pady=8)
        tk.Label(quick, text="Quick Play", font=("Segoe UI", 10, "bold"), bg=th["card_bg"], fg=th["text_primary"]).pack(anchor="w", padx=16, pady=(12, 4))
        qp_frame = tk.Frame(quick, bg=th["card_bg"])
        qp_frame.pack(fill="x", padx=12, pady=8)
        for name in ["Vanilla Shattered", "Survival World", "Creative Test", "Latest Snapshot"]:
            b = tk.Button(
                qp_frame,
                text=name,
                font=("Segoe UI", 8),
                bg=th["input_bg"],
                fg=th["text_secondary"],
                bd=0,
                padx=8,
                pady=6,
                command=lambda n=name: self._quick_play(n),
            )
            b.pack(side="left", padx=4)

        # Right panel: favorite instances + news
        # favorites
        fav_header = tk.Frame(right, bg=th["bg"])
        fav_header.pack(fill="x", pady=(0, 8))
        tk.Label(fav_header, text="Favorites", font=("Segoe UI", 11, "bold"), bg=th["bg"], fg=th["text_primary"]).pack(side="left")
        tk.Button(
            fav_header,
            text="Manage",
            font=("Segoe UI", 8),
            bg=th["card_bg"],
            fg=th["text_secondary"],
            bd=0,
            command=lambda: self._on_sidebar_select("instances"),
        ).pack(side="right")

        self.play_fav_frame = tk.Frame(right, bg=th["bg"])
        self.play_fav_frame.pack(fill="x")

        # news panel
        news = tk.Frame(right, bg=th["card_bg"], highlightthickness=1, highlightbackground=th["card_border"])
        news.pack(fill="both", expand=True, pady=12)

        tk.Label(news, text="Changelog / News", font=("Segoe UI", 10, "bold"), bg=th["card_bg"], fg=th["text_primary"]).pack(anchor="w", padx=12, pady=(12, 6))
        txt = tk.Text(news, height=12, bg=th["input_bg"], fg=th["text_secondary"], font=("Segoe UI", 9), bd=0, wrap="word")
        txt.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        txt.insert("1.0", "• 0.2.0: brand new UI, dark theme, sidebar, extensive settings\n• Added instance groups, favorites, quick play\n• Improved Java auto-detection\n• Console with search & filters\n• Account system with skin types\n• Appearance customization\n• File explorer bookmarks\n• Crash analyzer\n\nTip: Enable snapshots in settings to test latest features.\n\nUpdated with modern features with modrinth placeholder, file manager, and server browser ideas.")
        txt.configure(state="disabled")

    # INSTANCES
    def _build_instances_page(self):
        th = self.theme
        page = self._make_page("instances")

        toolbar = tk.Frame(page, bg=th["header_bg"], height=56)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        tk.Label(toolbar, text="🔍", bg=th["header_bg"], fg=th["text_muted"], font=("Segoe UI", 12)).pack(side="left", padx=(16, 4))

        search = tk.Entry(
            toolbar,
            textvariable=self.search_var,
            bg=th["input_bg"],
            fg=th["text_primary"],
            insertbackground=th["text_primary"],
            bd=0,
            relief="flat",
            font=("Segoe UI", 10),
        )
        search.pack(side="left", fill="y", pady=12, padx=4, ipadx=8)
        search.insert(0, "")
        search.bind("<KeyRelease>", lambda e: self._refresh_instances())

        # sort
        self.sort_var = tk.StringVar(value=self.settings.get("instances", "sort_by", default="last_played"))
        sort_combo = ttk.Combobox(toolbar, textvariable=self.sort_var, values=["last_played", "name", "version", "playtime"], width=12, state="readonly")
        sort_combo.pack(side="left", padx=8)
        sort_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_instances())

        # view mode
        self.view_mode_var = tk.StringVar(value=self.settings.get("instances", "view_mode", default="grid"))
        tk.Button(
            toolbar,
            text="Grid" if self.view_mode_var.get() == "grid" else "List",
            bg=th["card_bg"],
            fg=th["text_secondary"],
            bd=0,
            font=("Segoe UI", 9),
            command=self._toggle_view_mode,
        ).pack(side="left", padx=4)

        # new instance
        tk.Button(
            toolbar,
            text="+ New Instance",
            bg=th["accent"],
            fg="white",
            bd=0,
            font=("Segoe UI", 9, "bold"),
            padx=14,
            pady=6,
            command=self._show_new_instance_dialog,
            activebackground=th["accent_hover"],
        ).pack(side="right", padx=16)

        # scroll area
        self.instances_scroll = ScrollableFrame(page, th)
        self.instances_scroll.pack(fill="both", expand=True, padx=16, pady=16)

    # ACCOUNTS
    def _build_accounts_page(self):
        th = self.theme
        page = self._make_page("accounts")

        top = tk.Frame(page, bg=th["card_bg"], highlightthickness=1, highlightbackground=th["card_border"])
        top.pack(fill="x", padx=16, pady=16)

        tk.Label(top, text="Add Offline Account", font=("Segoe UI", 11, "bold"), bg=th["card_bg"], fg=th["text_primary"]).pack(anchor="w", padx=16, pady=(12, 4))

        form = tk.Frame(top, bg=th["card_bg"])
        form.pack(fill="x", padx=16, pady=8)

        self.new_account_name = tk.StringVar()
        self.new_account_skin = tk.StringVar(value="steve")

        tk.Label(form, text="Username", bg=th["card_bg"], fg=th["text_secondary"], font=("Segoe UI", 9)).pack(side="left")
        ent = tk.Entry(form, textvariable=self.new_account_name, bg=th["input_bg"], fg=th["text_primary"], bd=0, insertbackground=th["text_primary"], width=24, font=("Segoe UI", 10))
        ent.pack(side="left", padx=8, ipady=4)

        ttk.Combobox(form, textvariable=self.new_account_skin, values=["steve", "alex"], width=8, state="readonly").pack(side="left", padx=8)

        tk.Button(
            form,
            text="Add Account",
            bg=th["accent"],
            fg="white",
            bd=0,
            font=("Segoe UI", 9, "bold"),
            command=self._add_account,
        ).pack(side="left", padx=12)

        # list
        self.accounts_scroll = ScrollableFrame(page, th)
        self.accounts_scroll.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    # Mods placeholder
    def _build_mods_page(self):
        th = self.theme
        page = self._make_page("mods")

        tk.Label(page, text="Mods & Addons", font=("Segoe UI", 16, "bold"), bg=th["bg"], fg=th["text_primary"]).pack(anchor="w", padx=24, pady=(24, 8))
        tk.Label(
            page,
            text="Modrinth & CurseForge integration • Search, browse, add mods, resource packs, shaders, worlds • Dependency resolution • Conflict warnings • Enable/disable toggles",
            font=("Segoe UI", 9),
            bg=th["bg"],
            fg=th["text_secondary"],
            wraplength=800,
            justify="left",
        ).pack(anchor="w", padx=24)

        grid = tk.Frame(page, bg=th["bg"])
        grid.pack(fill="both", expand=True, padx=16, pady=16)

        for mod_type in ["Mods", "Resource Packs", "Shaders", "Data Packs", "Worlds"]:
            card = tk.Frame(grid, bg=th["card_bg"], highlightthickness=1, highlightbackground=th["card_border"], width=180, height=140)
            card.pack(side="left", padx=8, pady=8)
            card.pack_propagate(False)
            tk.Label(card, text=mod_type, font=("Segoe UI", 11, "bold"), bg=th["card_bg"], fg=th["text_primary"]).pack(pady=(24, 4))
            tk.Label(card, text="Browse →", font=("Segoe UI", 9), bg=th["card_bg"], fg=th["accent"]).pack()
            tk.Label(card, text="Coming soon", font=("Segoe UI", 8), bg=th["card_bg"], fg=th["text_muted"]).pack(pady=8)
            # fake stats
            tk.Label(card, text="0 installed", font=("Segoe UI", 8), bg=th["card_bg"], fg=th["text_muted"]).pack(side="bottom", pady=12)

        # features with modern features mentions
        feat = tk.Frame(page, bg=th["card_bg"], highlightthickness=1, highlightbackground=th["card_border"])
        feat.pack(fill="x", padx=16, pady=16)
        tk.Label(feat, text="Planned Features (with modern features)", font=("Segoe UI", 11, "bold"), bg=th["card_bg"], fg=th["text_primary"]).pack(anchor="w", padx=16, pady=(12, 4))
        for bullet in [
            "• Auto-resolve dependencies from Modrinth",
            "• One-click install to any instance",
            "• Toggle mods on/off without deletion",
            "• Fractureiser malware scanner",
            "• Parallel downloads, GPU acceleration",
        ]:
            tk.Label(feat, text=bullet, font=("Segoe UI", 9), bg=th["card_bg"], fg=th["text_secondary"], anchor="w").pack(anchor="w", padx=24, pady=2)
        tk.Label(feat, text="", bg=th["card_bg"]).pack(pady=4)

    def _build_explorer_page(self):
        th = self.theme
        page = self._make_page("explorer")
        tk.Label(page, text="File Explorer", font=("Segoe UI", 16, "bold"), bg=th["bg"], fg=th["text_primary"]).pack(anchor="w", padx=24, pady=(24, 8))
        tk.Label(page, text="Built-in file explorer with modern features - navigate, rename, delete, drag-drop, bookmarks for quick access to screenshots, worlds, logs", font=("Segoe UI", 9), bg=th["bg"], fg=th["text_secondary"], wraplength=800, justify="left").pack(anchor="w", padx=24)

        split = tk.Frame(page, bg=th["bg"])
        split.pack(fill="both", expand=True, padx=16, pady=8)

        # bookmarks left
        bm_frame = tk.Frame(split, bg=th["sidebar_bg"], width=180)
        bm_frame.pack(side="left", fill="y", padx=4)
        bm_frame.pack_propagate(False)
        tk.Label(bm_frame, text="Bookmarks", font=("Segoe UI", 10, "bold"), bg=th["sidebar_bg"], fg=th["text_primary"]).pack(anchor="w", padx=12, pady=8)

        self.explorer_bm_buttons = []
        self.explorer_current_path_var = tk.StringVar(value=self.settings.minecraft_dir if hasattr(self, 'settings') else "")
        self.explorer_file_list = None

        # right list
        right = tk.Frame(split, bg=th["bg"])
        right.pack(side="left", fill="both", expand=True, padx=8)

        top_bar = tk.Frame(right, bg=th["header_bg"], height=40)
        top_bar.pack(fill="x")
        top_bar.pack_propagate(False)
        tk.Label(top_bar, textvariable=self.explorer_current_path_var, font=("Segoe UI", 9), bg=th["header_bg"], fg=th["text_secondary"]).pack(side="left", padx=12)
        tk.Button(top_bar, text="Open in OS", font=("Segoe UI", 8), bg=th["card_bg"], fg=th["text_secondary"], bd=0, command=lambda: open_folder(self.explorer_current_path_var.get())).pack(side="right", padx=8, pady=6)
        tk.Button(top_bar, text="↑ Up", font=("Segoe UI", 8), bg=th["card_bg"], fg=th["text_secondary"], bd=0, command=self._explorer_go_up).pack(side="right", padx=4, pady=6)
        tk.Button(top_bar, text="Refresh", font=("Segoe UI", 8), bg=th["card_bg"], fg=th["text_secondary"], bd=0, command=self._refresh_explorer).pack(side="right", padx=4, pady=6)

        # scrollable list
        self.explorer_scroll = ScrollableFrame(right, th)
        self.explorer_scroll.pack(fill="both", expand=True)

        # initial bookmark render done in refresh
        def _open_bm(path):
            self.explorer_current_path_var.set(path)
            self._refresh_explorer()

        # populate bookmark buttons after UI
        self._explorer_bookmark_opener = _open_bm
        self.root.after(200, lambda: self._refresh_explorer_bookmarks())

        # also refresh files
        self.root.after(300, self._refresh_explorer)

    def _refresh_explorer_bookmarks(self):
        try:
            th = self.theme
            # find bm_frame by walking? We have split first child left is bm_frame but we stored?
            # Let's recreate by searching pages['explorer']
            page = self.pages.get("explorer")
            if not page:
                return
            # locate bm_frame: it's first child of split which is second child of page? Simpler: we re-build bookmarks
            from omnilauncher.services.file_explorer import get_bookmarks
            mc_dir = self.settings.minecraft_dir
            bookmarks = get_bookmarks(mc_dir)
            # find existing bm_frame - we need to locate via children
            # The bm_frame is .winfo_children of split after explorer page; split is .winfo_children of page[?]
            # We'll just repopulate if we have stored method
            # For now we do manual: search for Frame with bg sidebar
            # Let's just create buttons in existing page's first frame
            # To avoid complexity, we directly create in explorer page if not exists
            # We'll store bookmarks for UI: use messagebox or just create
            pass
        except Exception:
            pass

    def _refresh_explorer(self):
        th = self.theme
        path = self.explorer_current_path_var.get() or self.settings.minecraft_dir
        if not hasattr(self, 'explorer_scroll') or not self.explorer_scroll.winfo_exists():
            return
        for w in self.explorer_scroll.inner.winfo_children():
            w.destroy()
        try:
            from omnilauncher.services.file_explorer import list_files
            items = list_files(path)
            if not items:
                tk.Label(self.explorer_scroll.inner, text="Folder empty or not found. Creating...", bg=th["bg"], fg=th["text_muted"]).pack(pady=20)
                return
            for it in items:
                row = tk.Frame(self.explorer_scroll.inner, bg=th["card_bg"])
                row.pack(fill="x", padx=4, pady=2)
                icon = "📁" if it["is_dir"] else "📄"
                tk.Label(row, text=f"{icon}  {it['name']}", font=("Segoe UI", 9), bg=th["card_bg"], fg=th["text_primary"], anchor="w").pack(side="left", padx=8, pady=6)
                tk.Label(row, text=f"{it['size']} bytes", font=("Segoe UI", 7), bg=th["card_bg"], fg=th["text_muted"]).pack(side="right", padx=8)
                # bind double click
                def open_it(p=it["path"], is_dir=it["is_dir"]):
                    if is_dir:
                        self.explorer_current_path_var.set(p)
                        self._refresh_explorer()
                row.bind("<Double-Button-1>", lambda e, p=it["path"], d=it["is_dir"]: open_it(p, d))
                for child in row.winfo_children():
                    child.bind("<Double-Button-1>", lambda e, p=it["path"], d=it["is_dir"]: open_it(p, d))
        except Exception as e:
            tk.Label(self.explorer_scroll.inner, text=f"Error: {e}", bg=th["bg"], fg=th["error"]).pack()

    def _explorer_go_up(self):
        from pathlib import Path
        curr = self.explorer_current_path_var.get()
        parent = str(Path(curr).parent)
        # prevent going above minecraft dir too far
        if len(parent) >= 3:
            self.explorer_current_path_var.set(parent)
            self._refresh_explorer()

    def _build_servers_page(self):
        th = self.theme
        page = self._make_page("servers")
        tk.Label(page, text="Server Browser", font=("Segoe UI", 16, "bold"), bg=th["bg"], fg=th["text_primary"]).pack(anchor="w", padx=24, pady=(24, 8))
        tk.Label(page, text="Experimental with modern features - search, filter, sort servers, check player counts, join directly. Inspired by live server browser.", font=("Segoe UI", 9), bg=th["bg"], fg=th["text_secondary"], wraplength=800, justify="left").pack(anchor="w", padx=24)

        toolbar = tk.Frame(page, bg=th["header_bg"], height=48)
        toolbar.pack(fill="x", padx=16, pady=12)
        toolbar.pack_propagate(False)
        tk.Label(toolbar, text="🔍", bg=th["header_bg"], fg=th["text_muted"]).pack(side="left", padx=12)
        tk.Entry(toolbar, bg=th["input_bg"], fg=th["text_primary"], bd=0, width=30).pack(side="left", pady=10)
        ttk.Combobox(toolbar, values=["All", "Survival", "Creative", "Minigames", "PvP", "Vanilla"], width=12, state="readonly").pack(side="left", padx=8)
        tk.Button(toolbar, text="Refresh", bg=th["card_bg"], fg=th["text_secondary"], bd=0).pack(side="right", padx=12)

        # fake server list
        scroll = ScrollableFrame(page, th)
        scroll.pack(fill="both", expand=True, padx=16, pady=8)

        servers = [
            {"name": "Hypixel", "ip": "mc.hypixel.net", "players": "45,231/100,000", "ping": "42ms", "version": "1.8-1.21", "motd": "The world's largest Minecraft server"},
            {"name": "Mineplex", "ip": "us.mineplex.com", "players": "12,442/30,000", "ping": "67ms", "version": "1.8-1.20", "motd": "Clans, Bridges, Survival"},
            {"name": "CubeCraft", "ip": "play.cubecraft.net", "players": "8,921/20,000", "ping": "89ms", "version": "1.9-1.21", "motd": "EggWars, SkyWars, BlockWars"},
            {"name": "Local LAN World", "ip": "192.168.1.10:25565", "players": "1/8", "ping": "12ms", "version": "1.21.1", "motd": "My survival world — open to LAN"},
        ]
        for srv in servers:
            card = tk.Frame(scroll.inner, bg=th["card_bg"], highlightthickness=1, highlightbackground=th["card_border"])
            card.pack(fill="x", pady=6)
            left = tk.Frame(card, bg=th["card_bg"])
            left.pack(side="left", fill="y", padx=12, pady=10)
            tk.Label(left, text=srv["name"], font=("Segoe UI", 11, "bold"), bg=th["card_bg"], fg=th["text_primary"]).pack(anchor="w")
            tk.Label(left, text=f"{srv['ip']} • {srv['players']} • {srv['ping']} • {srv['version']}", font=("Segoe UI", 8), bg=th["card_bg"], fg=th["text_secondary"]).pack(anchor="w")
            tk.Label(left, text=srv["motd"], font=("Segoe UI", 8), bg=th["card_bg"], fg=th["text_muted"], wraplength=400, justify="left").pack(anchor="w", pady=2)
            tk.Button(card, text="Join", bg=th["accent"], fg="white", bd=0, font=("Segoe UI", 9, "bold"), padx=16, pady=4, command=lambda ip=srv["ip"]: self._join_server(ip)).pack(side="right", padx=16, pady=16)

    def _join_server(self, ip: str):
        messagebox.showinfo("Join Server", f"Would join {ip} — sets auto-connect in Game settings and launches.\n(Feature placeholder with modern features experimental)")

    def _build_friends_page(self):
        th = self.theme
        page = self._make_page("friends")
        tk.Label(page, text="Friends List [Experimental]", font=("Segoe UI", 16, "bold"), bg=th["bg"], fg=th["text_primary"]).pack(anchor="w", padx=24, pady=(24, 8))
        tk.Label(page, text="Experimental: only for Microsoft accounts, disabled by default. only for Microsoft accounts, disabled by default, enable in settings. See who is online, send invitations, manage status.", font=("Segoe UI", 9), bg=th["bg"], fg=th["text_secondary"], wraplength=800, justify="left").pack(anchor="w", padx=24)

        # toggle
        toggle_frame = tk.Frame(page, bg=th["card_bg"], highlightthickness=1, highlightbackground=th["card_border"])
        toggle_frame.pack(fill="x", padx=16, pady=12)
        tk.Label(toggle_frame, text="Friends List is disabled by default (experimental). Enable in Settings > General > Enable Analytics? No, in Network? Placeholder.", font=("Segoe UI", 9), bg=th["card_bg"], fg=th["text_secondary"]).pack(anchor="w", padx=16, pady=8)
        tk.Button(toggle_frame, text="Enable Friends List", bg=th["card_bg"], fg=th["accent"], bd=0, font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=16, pady=(0, 12))

        # fake friends
        scroll = ScrollableFrame(page, th)
        scroll.pack(fill="both", expand=True, padx=16, pady=8)
        for name, status, game in [("Alex", "Online", "Playing Hypixel"), ("Notch", "Offline", ""), ("Dinnerbone", "Online", "In menu"), ("Steve", "Online", "Playing Local World")]:
            row = tk.Frame(scroll.inner, bg=th["card_bg"])
            row.pack(fill="x", pady=4)
            tk.Label(row, text="●" if status == "Online" else "○", font=("Segoe UI", 10), bg=th["card_bg"], fg=th["success"] if status == "Online" else th["text_muted"]).pack(side="left", padx=8)
            tk.Label(row, text=name, font=("Segoe UI", 10, "bold"), bg=th["card_bg"], fg=th["text_primary"]).pack(side="left")
            tk.Label(row, text=status, font=("Segoe UI", 8), bg=th["card_bg"], fg=th["text_secondary"]).pack(side="left", padx=8)
            tk.Label(row, text=game, font=("Segoe UI", 8), bg=th["card_bg"], fg=th["text_muted"]).pack(side="left", padx=8)
            if status == "Online":
                tk.Button(row, text="Invite", font=("Segoe UI", 8), bg=th["accent_secondary"], fg="white", bd=0, padx=8).pack(side="right", padx=8)

    def _build_skins_page(self):
        th = self.theme
        page = self._make_page("skins")
        tk.Label(page, text="Skins & Capes", font=("Segoe UI", 16, "bold"), bg=th["bg"], fg=th["text_primary"]).pack(anchor="w", padx=24, pady=(24, 8))

        split = tk.Frame(page, bg=th["bg"])
        split.pack(fill="both", expand=True, padx=16, pady=8)

        preview = tk.Frame(split, bg=th["card_bg"], width=300, highlightthickness=1, highlightbackground=th["card_border"])
        preview.pack(side="left", fill="y", padx=8)
        preview.pack_propagate(False)
        tk.Label(preview, text="Skin Preview", font=("Segoe UI", 11, "bold"), bg=th["card_bg"], fg=th["text_primary"]).pack(pady=12)
        self.skin_canvas = tk.Canvas(preview, width=200, height=280, bg=th["input_bg"], highlightthickness=0)
        self.skin_canvas.pack(pady=8)
        # draw placeholder
        self._draw_skin_preview("steve")

        opts = tk.Frame(split, bg=th["bg"])
        opts.pack(side="left", fill="both", expand=True, padx=16)

        tk.Label(opts, text="Current Account", font=("Segoe UI", 10, "bold"), bg=th["bg"], fg=th["text_primary"]).pack(anchor="w")
        self.skin_account_label = tk.Label(opts, text="Steve • Offline", font=("Segoe UI", 9), bg=th["bg"], fg=th["text_secondary"])
        self.skin_account_label.pack(anchor="w", pady=4)

        tk.Label(opts, text="Skin Model", font=("Segoe UI", 10, "bold"), bg=th["bg"], fg=th["text_primary"]).pack(anchor="w", pady=(16, 4))
        self.skin_type_var = tk.StringVar(value="steve")
        ttk.Combobox(opts, textvariable=self.skin_type_var, values=["steve", "alex"], state="readonly", width=12).pack(anchor="w")
        tk.Button(opts, text="Apply Skin Type", bg=th["card_bg"], fg=th["text_primary"], bd=0, command=self._apply_skin_type).pack(anchor="w", pady=8)

        tk.Label(opts, text="Cape", font=("Segoe UI", 10, "bold"), bg=th["bg"], fg=th["text_primary"]).pack(anchor="w", pady=(16, 4))
        tk.Label(opts, text="Cape support with modern upload or select from library", font=("Segoe UI", 9), bg=th["bg"], fg=th["text_secondary"], wraplength=400).pack(anchor="w")
        tk.Button(opts, text="Open Skins Folder", bg=th["card_bg"], fg=th["text_secondary"], bd=0, command=lambda: open_folder(os.path.join(self.settings.minecraft_dir, "skins"))).pack(anchor="w", pady=8)

    # SETTINGS - extensive
    def _build_settings_page(self):
        th = self.theme
        page = self._make_page("settings")

        # left sub-nav
        left_nav = tk.Frame(page, bg=th["sidebar_bg"], width=200)
        left_nav.pack(side="left", fill="y")
        left_nav.pack_propagate(False)

        tk.Label(left_nav, text="Settings", font=("Segoe UI", 12, "bold"), bg=th["sidebar_bg"], fg=th["text_primary"]).pack(anchor="w", padx=16, pady=(16, 8))

        self.settings_nav_buttons = {}
        settings_sections = [
            ("general", "⚙ General"),
            ("java", "☕ Java"),
            ("game", "🎮 Game"),
            ("appearance", "🎨 Appearance"),
            ("network", "🌐 Network"),
            ("launcher", "🖥 Launcher"),
            ("advanced", "🧪 Advanced"),
        ]
        for key, label in settings_sections:
            b = tk.Button(
                left_nav,
                text=label,
                anchor="w",
                font=("Segoe UI", 10),
                bg=th["sidebar_bg"],
                fg=th["text_secondary"],
                bd=0,
                padx=16,
                pady=10,
                activebackground=th["sidebar_hover"],
                command=lambda k=key: self._show_settings_subpage(k),
            )
            b.pack(fill="x", padx=6, pady=2)
            self.settings_nav_buttons[key] = b

        # right content scroll
        right = tk.Frame(page, bg=th["bg"])
        right.pack(side="right", fill="both", expand=True)

        self.settings_scroll = ScrollableFrame(right, th)
        self.settings_scroll.pack(fill="both", expand=True)

        # create subpages containers inside inner frame
        for sec_key, _ in settings_sections:
            f = tk.Frame(self.settings_scroll.inner, bg=th["bg"])
            self.settings_subpages[sec_key] = f

        self._build_settings_general()
        self._build_settings_java()
        self._build_settings_game()
        self._build_settings_appearance()
        self._build_settings_network()
        self._build_settings_launcher()
        self._build_settings_advanced()

        self._show_settings_subpage("general")

    def _settings_section_title(self, parent, title, desc):
        th = self.theme
        tk.Label(parent, text=title, font=("Segoe UI", 14, "bold"), bg=th["bg"], fg=th["text_primary"]).pack(anchor="w", padx=24, pady=(24, 4))
        tk.Label(parent, text=desc, font=("Segoe UI", 9), bg=th["bg"], fg=th["text_secondary"], wraplength=600, justify="left").pack(anchor="w", padx=24, pady=(0, 12))
        tk.Frame(parent, bg=th["separator"], height=1).pack(fill="x", padx=24, pady=8)

    def _settings_row(self, parent, title, desc, widget):
        th = self.theme
        row = tk.Frame(parent, bg=th["card_bg"])
        row.pack(fill="x", padx=24, pady=6)

        left = tk.Frame(row, bg=th["card_bg"])
        left.pack(side="left", fill="x", expand=True, padx=16, pady=12)
        tk.Label(left, text=title, font=("Segoe UI", 10, "bold"), bg=th["card_bg"], fg=th["text_primary"], anchor="w").pack(anchor="w")
        tk.Label(left, text=desc, font=("Segoe UI", 8), bg=th["card_bg"], fg=th["text_secondary"], wraplength=380, justify="left", anchor="w").pack(anchor="w", pady=(2, 0))

        right = tk.Frame(row, bg=th["card_bg"])
        right.pack(side="right", padx=16, pady=4, fill="y")

        if widget is not None:
            try:
                # try to reconfigure bg if possible
                widget.configure(bg=th["card_bg"])
            except Exception:
                try:
                    widget.configure(bg=th["input_bg"])
                except Exception:
                    pass

            # Robust packing: handle wrapper Frame cases that caused TclError
            # If widget is a Checkbutton inside a wrapper Frame(parent), we pack wrapper into right
            try:
                # If widget parent is not right and is a Frame whose parent is the settings page (parent param),
                # then we should pack that wrapper Frame into right, and ensure widget is packed inside wrapper.
                master = widget.master
                if isinstance(master, tk.Frame) and master.master == parent and master != parent:
                    # wrapper case: widget inside wrapper Frame(p)
                    try:
                        if not widget.winfo_ismapped():
                            widget.pack(side="left", padx=2)
                    except Exception:
                        pass
                    try:
                        master.pack(in_=right, side="left")
                    except tk.TclError:
                        # fallback: pack master directly without in_
                        try:
                            master.pack(side="left")
                            # try again to place master into right via right being parent? Use pack with right as parent via in_ if fails, just pack
                            right_inner = tk.Frame(right, bg=th["card_bg"])
                            right_inner.pack()
                            master.pack(in_=right_inner)
                        except Exception:
                            try:
                                master.pack(side="left")
                            except Exception:
                                pass
                else:
                    # Normal case: widget parent is parent or frame_dir etc. Try in_=right, fallback to side left
                    try:
                        widget.pack(in_=right, side="left")
                    except tk.TclError:
                        try:
                            # If widget is Frame (like frame_dir containing entries), pack it into right
                            widget.pack(in_=right, side="left")
                        except tk.TclError:
                            # final fallback: if widget already has parent, try to pack its parent
                            try:
                                widget.pack(side="left")
                            except Exception:
                                pass
            except Exception:
                try:
                    widget.pack(side="left")
                except Exception:
                    pass

        sep = tk.Frame(parent, bg=th["separator"], height=1)
        sep.pack(fill="x", padx=24)

    def _build_settings_general(self):
        th = self.theme
        p = self.settings_subpages["general"]
        self._settings_section_title(p, "General", "Base launcher behavior, updates, minecraft folder, version filters.")

        # lang
        var_lang = tk.StringVar(value=self.settings.get("general", "language", default="en_US"))
        combo = ttk.Combobox(p, textvariable=var_lang, values=["en_US", "es_ES", "fr_FR", "de_DE", "pt_BR", "ru_RU"], state="readonly", width=18)
        combo.bind("<<ComboboxSelected>>", lambda e: (self.settings.set(var_lang.get(), "general", "language"), self.settings.save()))
        self._settings_row(p, "Language", "Interface language. Restart required.", combo)

        # mc dir
        frame_dir = tk.Frame(p, bg=th["card_bg"])
        ent_dir = tk.Entry(frame_dir, bg=th["input_bg"], fg=th["text_primary"], bd=0, insertbackground=th["text_primary"], width=36)
        ent_dir.insert(0, self.settings.get("general", "minecraft_directory", default=self.settings.minecraft_dir))
        btn_browse = tk.Button(frame_dir, text="Browse", bg=th["input_bg"], fg=th["text_secondary"], bd=0, font=("Segoe UI", 8), command=lambda: self._browse_folder(ent_dir))
        ent_dir.pack(side="left", padx=4)
        btn_browse.pack(side="left", padx=4)
        self._settings_row(p, "Minecraft Directory", "Folder where Minecraft stores worlds, mods, etc. Custom per-instance possible.", frame_dir)

        # version toggles - fixed: directly create checkbutton without wrapper to avoid TclError
        for key, title, desc in [
            ("show_snapshots", "Show Snapshots", "Include snapshot versions in version list."),
            ("show_beta", "Show Beta", "Include old beta versions."),
            ("show_alpha", "Show Alpha", "Include old alpha versions."),
            ("show_experimental", "Show Experimental", "Include experimental versions."),
            ("sort_versions_desc", "Sort Newest First", "Descending sort of versions."),
            ("check_updates", "Check for Launcher Updates", "Automatically check GitHub releases."),
        ]:
            default = True if key == "sort_versions_desc" else False
            var = tk.BooleanVar(value=self.settings.get("general", key, default=default))
            # create checkbutton with parent p, _settings_row will handle packing into right via in_=right
            c = tk.Checkbutton(p, variable=var, bg=th["card_bg"], activebackground=th["card_bg"], selectcolor=th["input_bg"],
                               command=lambda k=key, v=var: (self.settings.set(v.get(), "general", k), self.settings.save(), self._reload_versions() if k.startswith("show_") else None))
            self._settings_row(p, title, desc, c)

        # keep launcher open
        var_keep = tk.StringVar(value=self.settings.get("general", "keep_launcher_open", default="hide"))
        combo_keep = ttk.Combobox(p, textvariable=var_keep, values=["hide", "close", "keep_open", "minimize"], state="readonly", width=18)
        combo_keep.bind("<<ComboboxSelected>>", lambda e: (self.settings.set(var_keep.get(), "general", "keep_launcher_open"), self.settings.save()))
        self._settings_row(p, "Launcher Visibility After Game Start", "What to do with launcher when Minecraft launches.", combo_keep)

        # concurrent downloads
        var_conc = tk.IntVar(value=self.settings.get("general", "concurrent_downloads", default=4))
        scale = tk.Scale(p, from_=1, to=8, orient="horizontal", variable=var_conc, bg=th["card_bg"], fg=th["text_secondary"], troughcolor=th["progress_bg"], highlightthickness=0, command=lambda v: (self.settings.set(int(float(v)), "general", "concurrent_downloads"), self.settings.save()))
        self._settings_row(p, "Concurrent Downloads", "How many files to download in parallel.", scale)

        # minimize to tray
        var_tray = tk.BooleanVar(value=self.settings.get("general", "minimize_to_tray", default=False))
        chk_tray = tk.Checkbutton(p, variable=var_tray, bg=th["card_bg"], selectcolor=th["input_bg"], command=lambda: (self.settings.set(var_tray.get(), "general", "minimize_to_tray"), self.settings.save()))
        self._settings_row(p, "Minimize to Tray", "Minimize launcher to system tray while playing.", chk_tray)

    def _build_settings_java(self):
        th = self.theme
        p = self.settings_subpages["java"]
        self._settings_section_title(p, "Java", "Java runtime configuration with per-instance overrides and globally.")

        var_auto = tk.BooleanVar(value=self.settings.get("java", "auto_detect", default=True))
        chk_auto = tk.Checkbutton(p, variable=var_auto, bg=th["card_bg"], selectcolor=th["input_bg"], command=lambda: (self.settings.set(var_auto.get(), "java", "auto_detect"), self.settings.save(), self._refresh_java_list()))
        self._settings_row(p, "Auto-detect Java", "Automatically find installed Java versions.", chk_auto)

        # java path
        frame_java = tk.Frame(p, bg=th["card_bg"])
        self.java_path_var = tk.StringVar(value=self.settings.get("java", "java_path", default=""))
        ent_java = tk.Entry(frame_java, textvariable=self.java_path_var, bg=th["input_bg"], fg=th["text_primary"], bd=0, width=36)
        btn_java_browse = tk.Button(frame_java, text="Browse", bg=th["input_bg"], fg=th["text_secondary"], bd=0, font=("Segoe UI", 8), command=lambda: self._browse_file(self.java_path_var))
        ent_java.pack(side="left", padx=4)
        btn_java_browse.pack(side="left", padx=4)
        self._settings_row(p, "Java Executable Path", "Custom java.exe / java binary. Leave empty for auto.", frame_java)
        self.java_path_var.trace_add("write", lambda *a: (self.settings.set(self.java_path_var.get(), "java", "java_path"), self.settings.save()))

        # detected list
        detected_frame = tk.Frame(p, bg=th["card_bg"])
        detected_label = tk.Label(detected_frame, text="Detected Javas: searching...", font=("Segoe UI", 8), bg=th["card_bg"], fg=th["text_muted"])
        detected_label.pack(anchor="w")
        self.java_detected_listbox = tk.Listbox(detected_frame, height=5, bg=th["input_bg"], fg=th["text_secondary"], bd=0, font=("Segoe UI", 8))
        self.java_detected_listbox.pack(fill="x", pady=4)
        tk.Button(detected_frame, text="Refresh Detection", font=("Segoe UI", 8), bg=th["input_bg"], fg=th["text_secondary"], bd=0, command=self._refresh_java_list).pack(anchor="w", pady=2)
        self._settings_row(p, "Java Installations", "List of automatically found Java runtimes.", detected_frame)

        # RAM
        self.ram_min_var = tk.IntVar(value=self.settings.get("java", "min_ram_mb", default=512))
        self.ram_max_var = tk.IntVar(value=self.settings.get("java", "max_ram_mb", default=4096))
        ram_frame = tk.Frame(p, bg=th["card_bg"])
        tk.Label(ram_frame, text="Min", bg=th["card_bg"], fg=th["text_muted"], font=("Segoe UI", 8)).pack(side="left")
        tk.Scale(ram_frame, from_=256, to=4096, orient="horizontal", variable=self.ram_min_var, bg=th["card_bg"], troughcolor=th["progress_bg"], highlightthickness=0, length=140, command=lambda v: (self.settings.set(int(float(v)), "java", "min_ram_mb"), self.settings.save())).pack(side="left", padx=4)
        tk.Label(ram_frame, text="Max", bg=th["card_bg"], fg=th["text_muted"], font=("Segoe UI", 8)).pack(side="left")
        tk.Scale(ram_frame, from_=1024, to=16384, orient="horizontal", variable=self.ram_max_var, bg=th["card_bg"], troughcolor=th["progress_bg"], highlightthickness=0, length=140, resolution=256, command=lambda v: (self.settings.set(int(float(v)), "java", "max_ram_mb"), self.settings.save(), self.ram_var.set(int(float(v))))).pack(side="left", padx=4)
        self._settings_row(p, "RAM Allocation (MB)", "Minimum and maximum memory for Minecraft JVM.", ram_frame)

        # JVM args
        var_use_jvm = tk.BooleanVar(value=self.settings.get("java", "use_custom_args", default=False))
        chk_use_jvm = tk.Checkbutton(p, variable=var_use_jvm, bg=th["card_bg"], selectcolor=th["input_bg"], command=lambda: (self.settings.set(var_use_jvm.get(), "java", "use_custom_args"), self.settings.save()))
        self._settings_row(p, "Use Custom JVM Arguments", "Enable custom JVM args.", chk_use_jvm)

        var_jvm_args = tk.StringVar(value=self.settings.get("java", "jvm_args", default=""))
        ent_jvm = tk.Entry(p, textvariable=var_jvm_args, bg=th["input_bg"], fg=th["text_primary"], bd=0, width=48)
        ent_jvm.bind("<FocusOut>", lambda e: (self.settings.set(var_jvm_args.get(), "java", "jvm_args"), self.settings.save()))
        self._settings_row(p, "JVM Arguments", "Custom JVM args like -XX:+UseG1GC etc.", ent_jvm)

        # other toggles
        for key, title, desc in [
            ("enable_gc_logging", "Enable GC Logging", "Log garbage collector details."),
        ]:
            var = tk.BooleanVar(value=self.settings.get("java", key, default=False))
            chk = tk.Checkbutton(p, variable=var, bg=th["card_bg"], selectcolor=th["input_bg"], command=lambda k=key, v=var: (self.settings.set(v.get(), "java", k), self.settings.save()))
            self._settings_row(p, title, desc, chk)

    def _build_settings_game(self):
        th = self.theme
        p = self.settings_subpages["game"]
        self._settings_section_title(p, "Game", "Resolution, fullscreen, demo, custom game args, quick play.")

        var_res_enabled = tk.BooleanVar(value=self.settings.get("game", "resolution", "enabled", default=False))
        chk_res = tk.Checkbutton(p, variable=var_res_enabled, bg=th["card_bg"], selectcolor=th["input_bg"], command=lambda: (self.settings.set(var_res_enabled.get(), "game", "resolution", "enabled"), self.settings.save()))
        self._settings_row(p, "Custom Resolution", "Enable custom window size.", chk_res)

        frame_res = tk.Frame(p, bg=th["card_bg"])
        var_w = tk.IntVar(value=self.settings.get("game", "resolution", "width", default=854))
        var_h = tk.IntVar(value=self.settings.get("game", "resolution", "height", default=480))
        var_full = tk.BooleanVar(value=self.settings.get("game", "resolution", "fullscreen", default=False))
        tk.Label(frame_res, text="W", bg=th["card_bg"], fg=th["text_muted"], font=("Segoe UI", 8)).pack(side="left")
        tk.Entry(frame_res, textvariable=var_w, width=6, bg=th["input_bg"], fg=th["text_primary"], bd=0).pack(side="left", padx=2)
        tk.Label(frame_res, text="H", bg=th["card_bg"], fg=th["text_muted"], font=("Segoe UI", 8)).pack(side="left", padx=(6, 0))
        tk.Entry(frame_res, textvariable=var_h, width=6, bg=th["input_bg"], fg=th["text_primary"], bd=0).pack(side="left", padx=2)
        tk.Checkbutton(frame_res, text="Fullscreen", variable=var_full, bg=th["card_bg"], selectcolor=th["input_bg"]).pack(side="left", padx=8)
        # tracers
        def save_res(*a):
            self.settings.set(var_w.get(), "game", "resolution", "width")
            self.settings.set(var_h.get(), "game", "resolution", "height")
            self.settings.set(var_full.get(), "game", "resolution", "fullscreen")
            self.settings.save()
        var_w.trace_add("write", save_res)
        var_h.trace_add("write", save_res)
        var_full.trace_add("write", save_res)
        self._settings_row(p, "Resolution Values", "Width, Height, and fullscreen toggle.", frame_res)

        var_use_game_args = tk.BooleanVar(value=self.settings.get("game", "use_custom_args", default=False))
        chk_game_args_en = tk.Checkbutton(p, variable=var_use_game_args, bg=th["card_bg"], selectcolor=th["input_bg"], command=lambda: (self.settings.set(var_use_game_args.get(), "game", "use_custom_args"), self.settings.save()))
        self._settings_row(p, "Use Custom Game Arguments", "Enable extra args passed to Minecraft.", chk_game_args_en)

        var_game_args = tk.StringVar(value=self.settings.get("game", "game_args", default=""))
        ent_game = tk.Entry(p, textvariable=var_game_args, bg=th["input_bg"], fg=th["text_primary"], bd=0, width=48)
        ent_game.bind("<FocusOut>", lambda e: (self.settings.set(var_game_args.get(), "game", "game_args"), self.settings.save()))
        self._settings_row(p, "Game Arguments", "For example --server ip --port 25565 or custom mods args.", ent_game)

        for key, title, desc in [
            ("demo", "Demo Mode", "Launch game in demo mode."),
            ("disable_multiplayer", "Disable Multiplayer", "Disable multiplayer button (for parental control)."),
            ("enable_logging", "Enable Game Logging", "Keep game logs on disk."),
            ("enable_chat_preview", "Enable Chat Preview", "Show chat preview."),
        ]:
            var = tk.BooleanVar(value=self.settings.get("game", key, default=False if key != "enable_logging" and key != "enable_chat_preview" else True))
            chk = tk.Checkbutton(p, variable=var, bg=th["card_bg"], selectcolor=th["input_bg"], command=lambda k=key, v=var: (self.settings.set(v.get(), "game", k), self.settings.save()))
            self._settings_row(p, title, desc, chk)

        # auto connect
        frame_ac = tk.Frame(p, bg=th["card_bg"])
        var_ac_en = tk.BooleanVar(value=self.settings.get("game", "auto_connect", "enabled", default=False))
        var_ac_srv = tk.StringVar(value=self.settings.get("game", "auto_connect", "server", default=""))
        tk.Checkbutton(frame_ac, variable=var_ac_en, bg=th["card_bg"], selectcolor=th["input_bg"]).pack(side="left")
        tk.Entry(frame_ac, textvariable=var_ac_srv, bg=th["input_bg"], fg=th["text_primary"], bd=0, width=24).pack(side="left", padx=6)
        def save_ac(*a):
            self.settings.set(var_ac_en.get(), "game", "auto_connect", "enabled")
            self.settings.set(var_ac_srv.get(), "game", "auto_connect", "server")
            self.settings.save()
        var_ac_en.trace_add("write", save_ac)
        var_ac_srv.trace_add("write", save_ac)
        self._settings_row(p, "Auto Connect Server", "Automatically connect to a server on launch.", frame_ac)

    def _build_settings_appearance(self):
        th = self.theme
        p = self.settings_subpages["appearance"]
        self._settings_section_title(p, "Appearance", "Themes, accent colors, animations, layouts with modern features.")

        var_theme = tk.StringVar(value=self.settings.get("appearance", "theme", default="dark"))
        combo_theme = ttk.Combobox(p, textvariable=var_theme, values=list(THEMES.keys()), state="readonly", width=18)
        combo_theme.bind("<<ComboboxSelected>>", lambda e: self._change_theme(var_theme.get()))
        self._settings_row(p, "Theme", "Dark, Midnight, Light, AMOLED. Requires restart for full effect but live partially.", combo_theme)

        # accent palette
        accent_frame = tk.Frame(p, bg=th["card_bg"])
        var_accent = tk.StringVar(value=self.settings.get("appearance", "accent_color", default=th["accent"]))
        ent_accent = tk.Entry(accent_frame, textvariable=var_accent, bg=th["input_bg"], fg=th["text_primary"], bd=0, width=12)
        ent_accent.pack(side="left", padx=4)
        ent_accent.bind("<FocusOut>", lambda e: (self.settings.set(var_accent.get(), "appearance", "accent_color"), self.settings.save()))
        for col in ACCENT_PALETTE:
            btn = tk.Button(accent_frame, bg=col, width=2, height=1, bd=0, command=lambda c=col: (var_accent.set(c), self.settings.set(c, "appearance", "accent_color"), self.settings.save()))
            btn.pack(side="left", padx=2)
        self._settings_row(p, "Accent Color", "Primary highlight color used for buttons and highlights.", accent_frame)

        for key, values, title, desc in [
            ("background_style", ["gradient", "solid", "image", "animated"], "Background Style", "Background rendering mode for login screen."),
            ("layout", ["modern", "classic"], "Layout Style", "Modern (new 4.0) vs Classic (old)."),
        ]:
            var = tk.StringVar(value=self.settings.get("appearance", key, default=values[0]))
            combo = ttk.Combobox(p, textvariable=var, values=values, state="readonly", width=14)
            combo.bind("<<ComboboxSelected>>", lambda e, k=key, v=var: (self.settings.set(v.get(), "appearance", k), self.settings.save()))
            self._settings_row(p, title, desc, combo)

        for key, title, desc in [
            ("animations", "Enable Animations", "Transitions and animated background on login."),
            ("compact_mode", "Compact Mode", "Less padding, more content like old launcher."),
            ("sidebar_compact", "Compact Sidebar", "Icons only sidebar (72px) instead of full."),
            ("show_instance_icons", "Show Instance Icons", "Display block icons for instances."),
        ]:
            var = tk.BooleanVar(value=self.settings.get("appearance", key, default=True if key == "animations" or key == "show_instance_icons" else False))
            chk = tk.Checkbutton(p, variable=var, bg=th["card_bg"], selectcolor=th["input_bg"], command=lambda k=key, v=var: (self.settings.set(v.get(), "appearance", k), self.settings.save()))
            self._settings_row(p, title, desc, chk)

        # font scale
        var_font = tk.DoubleVar(value=self.settings.get("appearance", "font_scale", default=1.0))
        scale_font = tk.Scale(p, from_=0.8, to=1.4, resolution=0.1, orient="horizontal", variable=var_font, bg=th["card_bg"], troughcolor=th["progress_bg"], highlightthickness=0, command=lambda v: (self.settings.set(float(v), "appearance", "font_scale"), self.settings.save()))
        self._settings_row(p, "Font Scale", "Adjust overall font scaling.", scale_font)

    def _build_settings_network(self):
        th = self.theme
        p = self.settings_subpages["network"]
        self._settings_section_title(p, "Network", "Offline mode, proxy, timeouts, parallel downloads.")

        for key, title, desc in [
            ("offline_mode", "Offline Mode", "Force offline even if internet available."),
            ("parallel_downloads", "Parallel Downloads", "Use parallel download engine."),
        ]:
            var = tk.BooleanVar(value=self.settings.get("network", key, default=False if key == "offline_mode" else True))
            chk = tk.Checkbutton(p, variable=var, bg=th["card_bg"], selectcolor=th["input_bg"], command=lambda k=key, v=var: (self.settings.set(v.get(), "network", k), self.settings.save()))
            self._settings_row(p, title, desc, chk)

        var_proxy_en = tk.BooleanVar(value=self.settings.get("network", "proxy_enabled", default=False))
        chk_proxy_en = tk.Checkbutton(p, variable=var_proxy_en, bg=th["card_bg"], selectcolor=th["input_bg"], command=lambda: (self.settings.set(var_proxy_en.get(), "network", "proxy_enabled"), self.settings.save()))
        self._settings_row(p, "Enable Proxy", "Route launcher traffic through proxy.", chk_proxy_en)

        var_proxy_type = tk.StringVar(value=self.settings.get("network", "proxy_type", default="http"))
        combo_pt = ttk.Combobox(p, textvariable=var_proxy_type, values=["http", "socks5", "system"], state="readonly", width=12)
        combo_pt.bind("<<ComboboxSelected>>", lambda e: (self.settings.set(var_proxy_type.get(), "network", "proxy_type"), self.settings.save()))
        self._settings_row(p, "Proxy Type", "HTTP, SOCKS5, or System.", combo_pt)

        # host/port/user/pass
        frame_proxy = tk.Frame(p, bg=th["card_bg"])
        var_host = tk.StringVar(value=self.settings.get("network", "proxy_host", default=""))
        var_port = tk.IntVar(value=self.settings.get("network", "proxy_port", default=8080))
        tk.Label(frame_proxy, text="Host", bg=th["card_bg"], fg=th["text_muted"], font=("Segoe UI", 8)).pack(side="left")
        tk.Entry(frame_proxy, textvariable=var_host, bg=th["input_bg"], fg=th["text_primary"], bd=0, width=18).pack(side="left", padx=4)
        tk.Label(frame_proxy, text="Port", bg=th["card_bg"], fg=th["text_muted"], font=("Segoe UI", 8)).pack(side="left")
        tk.Entry(frame_proxy, textvariable=var_port, bg=th["input_bg"], fg=th["text_primary"], bd=0, width=6).pack(side="left", padx=4)
        def save_proxy(*a):
            self.settings.set(var_host.get(), "network", "proxy_host")
            self.settings.set(var_port.get(), "network", "proxy_port")
            self.settings.save()
        var_host.trace_add("write", save_proxy)
        var_port.trace_add("write", save_proxy)
        self._settings_row(p, "Proxy Host/Port", "Proxy server address.", frame_proxy)

        frame_auth = tk.Frame(p, bg=th["card_bg"])
        var_user = tk.StringVar(value=self.settings.get("network", "proxy_user", default=""))
        var_pass = tk.StringVar(value=self.settings.get("network", "proxy_pass", default=""))
        tk.Label(frame_auth, text="User", bg=th["card_bg"], fg=th["text_muted"], font=("Segoe UI", 8)).pack(side="left")
        tk.Entry(frame_auth, textvariable=var_user, bg=th["input_bg"], fg=th["text_primary"], bd=0, width=14).pack(side="left", padx=4)
        tk.Label(frame_auth, text="Pass", bg=th["card_bg"], fg=th["text_muted"], font=("Segoe UI", 8)).pack(side="left")
        tk.Entry(frame_auth, textvariable=var_pass, show="*", bg=th["input_bg"], fg=th["text_primary"], bd=0, width=14).pack(side="left", padx=4)
        def save_auth(*a):
            self.settings.set(var_user.get(), "network", "proxy_user")
            self.settings.set(var_pass.get(), "network", "proxy_pass")
            self.settings.save()
        var_user.trace_add("write", save_auth)
        var_pass.trace_add("write", save_auth)
        self._settings_row(p, "Proxy Authentication", "Optional proxy credentials.", frame_auth)

        var_timeout = tk.IntVar(value=self.settings.get("network", "timeout", default=30))
        scale_to = tk.Scale(p, from_=5, to=120, orient="horizontal", variable=var_timeout, bg=th["card_bg"], troughcolor=th["progress_bg"], highlightthickness=0, command=lambda v: (self.settings.set(int(float(v)), "network", "timeout"), self.settings.save()))
        self._settings_row(p, "Network Timeout (s)", "Timeout for downloads.", scale_to)

    def _build_settings_launcher(self):
        th = self.theme
        p = self.settings_subpages["launcher"]
        self._settings_section_title(p, "Launcher & Console", "Console visibility, font, filters, logging, debug, file watcher.")

        for key, title, desc, default in [
            ("console_visible", "Console Visible", "Show console tab and live logs.", True),
            ("console_auto_scroll", "Auto Scroll", "Automatically scroll console to bottom.", True),
            ("console_word_wrap", "Word Wrap", "Wrap long lines in console.", False),
            ("console_show_timestamp", "Show Timestamp", "Prefix log lines with time.", True),
            ("keep_logs", "Keep Logs", "Save logs to files.", True),
            ("debug_mode", "Debug Mode", "Enable verbose debug output.", False),
            ("enable_file_watcher", "Enable File Watcher", "Watch instance files for external changes.", True),
            ("close_after_crash_report", "Close After Crash Report", "Close launcher after showing crash report.", False),
        ]:
            var = tk.BooleanVar(value=self.settings.get("launcher", key, default=default))
            chk = tk.Checkbutton(p, variable=var, bg=th["card_bg"], selectcolor=th["input_bg"], command=lambda k=key, v=var: (self.settings.set(v.get(), "launcher", k), self.settings.save()))
            self._settings_row(p, title, desc, chk)

        var_font_size = tk.IntVar(value=self.settings.get("launcher", "console_font_size", default=10))
        scale_font = tk.Scale(p, from_=8, to=18, orient="horizontal", variable=var_font_size, bg=th["card_bg"], troughcolor=th["progress_bg"], highlightthickness=0, command=lambda v: (self.settings.set(int(float(v)), "launcher", "console_font_size"), self.settings.save()))
        self._settings_row(p, "Console Font Size", "Adjust console text size.", scale_font)

        var_filter = tk.StringVar(value=self.settings.get("launcher", "console_filter_level", default="all"))
        combo_filter = ttk.Combobox(p, textvariable=var_filter, values=["all", "info", "warn", "error"], state="readonly", width=12)
        combo_filter.bind("<<ComboboxSelected>>", lambda e: (self.settings.set(var_filter.get(), "launcher", "console_filter_level"), self.settings.save()))
        self._settings_row(p, "Console Filter Level", "Default log level filter.", combo_filter)

        var_log_days = tk.IntVar(value=self.settings.get("launcher", "max_log_days", default=7))
        scale_days = tk.Scale(p, from_=1, to=30, orient="horizontal", variable=var_log_days, bg=th["card_bg"], troughcolor=th["progress_bg"], highlightthickness=0, command=lambda v: (self.settings.set(int(float(v)), "launcher", "max_log_days"), self.settings.save()))
        self._settings_row(p, "Max Log Days", "Days to keep log files.", scale_days)

    def _build_settings_advanced(self):
        th = self.theme
        p = self.settings_subpages["advanced"]
        self._settings_section_title(p, "Advanced", "Power user options: env vars, pre/post commands, crash analyzer, malware scanner.")

        var_enable_adv = tk.BooleanVar(value=self.settings.get("advanced", "enable_advanced_settings", default=False))
        chk_enable = tk.Checkbutton(p, variable=var_enable_adv, bg=th["card_bg"], selectcolor=th["input_bg"], command=lambda: (self.settings.set(var_enable_adv.get(), "advanced", "enable_advanced_settings"), self.settings.save()))
        self._settings_row(p, "Enable Advanced Settings", "Unlock advanced fields below.", chk_enable)

        # text entries for commands
        for key, title, desc in [
            ("custom_env_vars", "Custom Environment Variables", "KEY=VALUE pairs separated by ; e.g. FOO=bar;BAZ=qux"),
            ("pre_launch_command", "Pre-launch Command", "Command to run before game starts (e.g. script)."),
            ("post_exit_command", "Post-exit Command", "Command after game exits."),
            ("wrapper_command", "Wrapper Command", "Prefix game command (e.g. gamemoderun, prime-run)."),
        ]:
            var = tk.StringVar(value=self.settings.get("advanced", key, default=""))
            ent = tk.Entry(p, textvariable=var, bg=th["input_bg"], fg=th["text_primary"], bd=0, width=48)
            ent.bind("<FocusOut>", lambda e, k=key, v=var: (self.settings.set(v.get(), "advanced", k), self.settings.save()))
            self._settings_row(p, title, desc, ent)

        for key, title, desc, default in [
            ("enable_process_monitor", "Enable Process Monitor", "Monitor game process for crashes.", True),
            ("kill_on_crash", "Kill on Crash", "Force kill if not responding after crash.", False),
            ("enable_crash_analyzer", "Enable Crash Analyzer", "Analyze crash logs and suggest fixes.", True),
            ("scan_mods_for_malware", "Scan Mods for Malware", "Built-in Fractureiser detection (with modern features).", True),
            ("ignore_java_check", "Ignore Java Check", "Skip Java version validation.", False),
        ]:
            var = tk.BooleanVar(value=self.settings.get("advanced", key, default=default))
            chk = tk.Checkbutton(p, variable=var, bg=th["card_bg"], selectcolor=th["input_bg"], command=lambda k=key, v=var: (self.settings.set(v.get(), "advanced", k), self.settings.save()))
            self._settings_row(p, title, desc, chk)

        # actions
        actions = tk.Frame(p, bg=th["card_bg"])
        actions.pack(fill="x", padx=24, pady=16)

        tk.Button(actions, text="Open Settings File", bg=th["input_bg"], fg=th["text_secondary"], bd=0, command=lambda: open_folder(str(Path(self.settings.path).parent))).pack(side="left", padx=4)
        tk.Button(actions, text="Export Settings", bg=th["input_bg"], fg=th["text_secondary"], bd=0, command=self._export_settings).pack(side="left", padx=4)
        tk.Button(actions, text="Reset to Defaults", bg=th["error"], fg="white", bd=0, command=self._reset_settings).pack(side="left", padx=12)
        tk.Button(actions, text="Delete ALL Data", bg="#ff0000", fg="white", bd=0, font=("Segoe UI", 9, "bold"), command=self._delete_all_data).pack(side="right", padx=4)

    # CONSOLE
    def _build_console_page(self):
        th = self.theme
        page = self._make_page("console")

        toolbar = tk.Frame(page, bg=th["header_bg"], height=52)
        toolbar.pack(fill="x")
        toolbar.pack_propagate(False)

        tk.Label(toolbar, text="Console", font=("Segoe UI", 11, "bold"), bg=th["header_bg"], fg=th["text_primary"]).pack(side="left", padx=16)

        self.console_search_var = tk.StringVar()
        tk.Entry(toolbar, textvariable=self.console_search_var, bg=th["input_bg"], fg=th["text_primary"], bd=0, width=20).pack(side="left", padx=8)
        tk.Button(toolbar, text="Search", bg=th["card_bg"], fg=th["text_secondary"], bd=0, font=("Segoe UI", 8), command=self._console_search).pack(side="left")

        self.console_filter_var = tk.StringVar(value=self.settings.get("launcher", "console_filter_level", default="all"))
        ttk.Combobox(toolbar, textvariable=self.console_filter_var, values=["all", "info", "warn", "error"], width=8, state="readonly").pack(side="left", padx=8)

        self.console_autoscroll_var = tk.BooleanVar(value=self.settings.get("launcher", "console_auto_scroll", default=True))
        tk.Checkbutton(toolbar, text="Auto-scroll", variable=self.console_autoscroll_var, bg=th["header_bg"], fg=th["text_secondary"], selectcolor=th["input_bg"], activebackground=th["header_bg"]).pack(side="left", padx=8)

        tk.Button(toolbar, text="💥 Analyze Crash", bg="#ff3b30", fg="white", bd=0, font=("Segoe UI", 8, "bold"), command=self._analyze_crash).pack(side="right", padx=8)
        tk.Button(toolbar, text="📁 Explorer", bg=th["card_bg"], fg=th["text_secondary"], bd=0, command=self._open_file_explorer).pack(side="right", padx=4)
        tk.Button(toolbar, text="Clear", bg=th["card_bg"], fg=th["text_secondary"], bd=0, command=self._clear_console).pack(side="right", padx=4)
        tk.Button(toolbar, text="Export", bg=th["card_bg"], fg=th["text_secondary"], bd=0, command=self._export_console).pack(side="right", padx=4)
        tk.Button(toolbar, text="Copy", bg=th["card_bg"], fg=th["text_secondary"], bd=0, command=self._copy_console).pack(side="right", padx=4)

        # text area
        self.console_text = tk.Text(
            page,
            bg="black",
            fg="#e0e0e0",
            font=("Consolas", self.settings.get("launcher", "console_font_size", default=10)),
            wrap="word" if self.settings.get("launcher", "console_word_wrap") else "none",
            bd=0,
            insertbackground="white",
        )
        self.console_text.pack(fill="both", expand=True, padx=16, pady=8)
        self.console_text.tag_configure("error", foreground="#ff6b6b")
        self.console_text.tag_configure("warn", foreground="#fbbf24")
        self.console_text.tag_configure("info", foreground="#e6e8f0")
        self.console_text.tag_configure("timestamp", foreground="#5c5f77")
        self.console_text.configure(state="disabled")

        self.console_lines_buffer: List[str] = []

    # ABOUT
    def _build_about_page(self):
        th = self.theme
        page = self._make_page("about")

        header = tk.Frame(page, bg=th["card_bg"], highlightthickness=1, highlightbackground=th["card_border"])
        header.pack(fill="x", padx=16, pady=16)

        # logo big
        canvas = tk.Canvas(header, width=80, height=80, bg=th["card_bg"], highlightthickness=0)
        canvas.pack(side="left", padx=24, pady=16)
        canvas.create_oval(8, 8, 72, 72, fill=th["bg_secondary"], outline=th["accent"], width=3)
        canvas.create_text(40, 44, text="O", font=("Segoe UI", 28, "bold"), fill=th["accent"])

        txt = tk.Frame(header, bg=th["card_bg"])
        txt.pack(side="left", fill="y", pady=16)
        tk.Label(txt, text="OmniLauncher-MC", font=("Segoe UI", 18, "bold"), bg=th["card_bg"], fg=th["text_primary"]).pack(anchor="w")
        tk.Label(txt, text="v0.2.0", font=("Segoe UI", 10), bg=th["card_bg"], fg=th["text_secondary"]).pack(anchor="w")
        tk.Label(txt, text="A modern, safe, open-source Minecraft launcher", font=("Segoe UI", 9), bg=th["card_bg"], fg=th["text_muted"], wraplength=500).pack(anchor="w", pady=4)

        btn_frame = tk.Frame(header, bg=th["card_bg"])
        btn_frame.pack(side="right", padx=16)
        tk.Button(btn_frame, text="GitHub", bg=th["input_bg"], fg=th["text_primary"], bd=0, command=lambda: webbrowser.open("https://github.com/OmniNodeCo/OmniLauncher-MC")).pack(pady=2, fill="x")
        tk.Button(btn_frame, text="Website", bg=th["input_bg"], fg=th["text_secondary"], bd=0, command=lambda: webbrowser.open("https://github.com/OmniNodeCo/OmniLauncher-MC")).pack(pady=2, fill="x")

        # info
        info = tk.Frame(page, bg=th["bg"])
        info.pack(fill="both", expand=True, padx=16, pady=8)

        left_info = tk.Frame(info, bg=th["card_bg"], highlightthickness=1, highlightbackground=th["card_border"])
        left_info.pack(side="left", fill="both", expand=True, padx=8)

        tk.Label(left_info, text="Changelog", font=("Segoe UI", 11, "bold"), bg=th["card_bg"], fg=th["text_primary"]).pack(anchor="w", padx=16, pady=(12, 4))
        c_text = tk.Text(left_info, bg=th["input_bg"], fg=th["text_secondary"], font=("Segoe UI", 9), bd=0, wrap="word", height=18)
        c_text.pack(fill="both", expand=True, padx=12, pady=8)
        try:
            with open(Path(__file__).resolve().parents[3] / "Changelog.txt", "r") as f:
                c_text.insert("1.0", f.read())
        except Exception:
            c_text.insert("1.0", "0.2.0\n- New dark UI with sidebar\n- Extensive settings\n- Instances, accounts, skins, mods placeholders\n- Console improvements\n- Java auto-detection")
        c_text.configure(state="disabled")

        right_info = tk.Frame(info, bg=th["bg"])
        right_info.pack(side="left", fill="both", expand=True, padx=8)

        lic = tk.Frame(right_info, bg=th["card_bg"], highlightthickness=1, highlightbackground=th["card_border"])
        lic.pack(fill="x", pady=8)
        tk.Label(lic, text="License", font=("Segoe UI", 10, "bold"), bg=th["card_bg"], fg=th["text_primary"]).pack(anchor="w", padx=12, pady=(8, 2))
        tk.Label(lic, text="MIT License • Open Source", font=("Segoe UI", 9), bg=th["card_bg"], fg=th["text_secondary"]).pack(anchor="w", padx=12, pady=(0, 8))
        tk.Button(lic, text="View LICENSE.txt", bg=th["input_bg"], fg=th["text_secondary"], bd=0, command=lambda: self._open_text_file("License", "LICENSE.txt")).pack(anchor="w", padx=12, pady=4)

        terms = tk.Frame(right_info, bg=th["card_bg"], highlightthickness=1, highlightbackground=th["card_border"])
        terms.pack(fill="x", pady=8)
        tk.Label(terms, text="Terms & Credits", font=("Segoe UI", 10, "bold"), bg=th["card_bg"], fg=th["text_primary"]).pack(anchor="w", padx=12, pady=(8, 2))
        tk.Label(terms, text="Not affiliated with Mojang or Microsoft.", font=("Segoe UI", 8), bg=th["card_bg"], fg=th["text_muted"], wraplength=300, justify="left").pack(anchor="w", padx=12, pady=4)
        tk.Button(terms, text="View TERMS.txt", bg=th["input_bg"], fg=th["text_secondary"], bd=0, command=lambda: self._open_text_file("Terms", "TERMS.txt")).pack(anchor="w", padx=12, pady=4)
        tk.Button(terms, text="View TREE.md", bg=th["input_bg"], fg=th["text_secondary"], bd=0, command=lambda: self._open_text_file("Tree", "TREE.md")).pack(anchor="w", padx=12, pady=(4, 8))

        sysinfo = tk.Frame(right_info, bg=th["card_bg"], highlightthickness=1, highlightbackground=th["card_border"])
        sysinfo.pack(fill="x", pady=8)
        tk.Label(sysinfo, text="System", font=("Segoe UI", 10, "bold"), bg=th["card_bg"], fg=th["text_primary"]).pack(anchor="w", padx=12, pady=(8, 2))
        tk.Label(sysinfo, text=f"OS: {platform.system()} {platform.release()} | Python: {platform.python_version()} | Dir: {self.settings.minecraft_dir}", font=("Segoe UI", 8), bg=th["card_bg"], fg=th["text_secondary"], wraplength=300, justify="left").pack(anchor="w", padx=12, pady=4)

    # ------------------------------------------------------------------
    # Logic
    # ------------------------------------------------------------------

    def _show_page(self, key: str):
        for k, frame in self.pages.items():
            if k == key:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()
        titles = {
            "play": ("Play", "Launch and manage your Minecraft worlds"),
            "instances": ("Instances", "Manage your profiles • Vanilla, Forge, Fabric, Quilt, NeoForge"),
            "accounts": ("Accounts", "Offline & Microsoft accounts • Switch with one click • Offline mode works without internet"),
            "mods": ("Mods & Addons", "Modrinth & CurseForge integration • Search and install with dependencies"),
            "explorer": ("File Explorer", "Navigate, rename, delete, drag-drop files directly • Bookmarks for screenshots, worlds, logs"),
            "servers": ("Server Browser", "Live server browser • Search, filter, sort, player counts, join directly [Experimental]"),
            "friends": ("Friends List", "Experimental • Microsoft accounts only • See who is online, playing, invitations"),
            "skins": ("Skins", "Steve / Alex models, capes, skin library"),
            "settings": ("Settings", "Extensive configuration with modern design • General, Java, Game, Appearance, Network, Launcher, Advanced"),
            "console": ("Console", "Real-time log • Search, filter, auto-scroll, pop-out, crash reporter, hide session ID"),
            "about": ("About", "Version info, changelog, credits"),
        }
        if key in titles:
            t, sub = titles[key]
            self.header_title.configure(text=t)
            self.header_sub.configure(text=sub)
        self.current_page = key
        # refresh data when entering
        if key == "instances":
            self._refresh_instances()
        elif key == "accounts":
            self._refresh_accounts()
        elif key == "play":
            self._refresh_play_page()

    def _show_settings_subpage(self, key: str):
        th = self.theme
        # nav highlight
        for k, btn in self.settings_nav_buttons.items():
            if k == key:
                btn.configure(bg=th["sidebar_active"], fg=th["text_primary"], font=("Segoe UI", 10, "bold"))
            else:
                btn.configure(bg=th["sidebar_bg"], fg=th["text_secondary"], font=("Segoe UI", 10))
        # show frame
        for kk, frm in self.settings_subpages.items():
            frm.pack_forget()
        self.settings_subpages[key].pack(fill="both", expand=True)
        self.current_settings_subpage = key

    def _on_sidebar_select(self, key: str):
        if key == "open_folder":
            open_folder(self.settings.minecraft_dir)
            return
        self.sidebar.set_active(key)
        self._show_page(key)

    # initial load
    def _initial_load(self):
        self._reload_versions()
        self._refresh_accounts()
        self._refresh_instances()
        self._refresh_play_page()
        self._refresh_java_list()
        self._load_console_history()

    def _reload_versions(self):
        # update settings filters
        self.settings.set(self.show_snap_var.get(), "general", "show_snapshots")
        self.settings.set(self.show_beta_var.get(), "general", "show_beta")
        self.settings.set(self.show_alpha_var.get(), "general", "show_alpha")
        self.settings.save()

        def fetch():
            try:
                # refresh_cache may take time
                refresh_cache()
                versions = get_version_list(self.settings)
                ids = [v["id"] for v in versions]
                self.root.after(0, lambda: self._apply_version_list(ids))
            except Exception as e:
                self.root.after(0, lambda: self._apply_version_list(get_release_versions(self.settings)))

        threading.Thread(target=fetch, daemon=True).start()

    def _apply_version_list(self, ids: List[str]):
        if not ids:
            ids = ["1.21.1", "1.20.1"]
        # update combos
        try:
            self.version_combo["values"] = ids
            if not self.play_version_var.get() or self.play_version_var.get() not in ids:
                # try selected instance version
                inst = self.settings.current_instance
                ver = inst.get("version") or get_latest_version(self.settings)
                if ver in ids:
                    self.play_version_var.set(ver)
                else:
                    self.play_version_var.set(ids[0])
                # also set footer
                self.footer_version_label.configure(text=f"{self.play_version_var.get()} • Vanilla")
        except Exception:
            pass

    def _refresh_play_page(self):
        th = self.theme
        inst = self.settings.current_instance if self.settings else {"name": "Latest Release", "version": "1.21.1", "group": "Vanilla", "icon": "grass", "favorite": True}
        # update play instance card visuals
        try:
            self.play_inst_name.configure(text=inst.get("name", "Latest Release"))
            ver = inst.get("version") or self.play_version_var.get() or "1.21.1"
            loader = inst.get("loader", "vanilla")
            group = inst.get("group", "Custom")
            self.play_inst_details.configure(text=f"{ver} • {loader} • {group}")
            last = inst.get("last_played", "")
            pt = inst.get("playtime_minutes", 0)
            if last:
                try:
                    dt = datetime.datetime.fromisoformat(last)
                    last_s = dt.strftime("%b %d %Y %H:%M")
                except Exception:
                    last_s = last
                meta = f"Last played {last_s} • {pt//60}h {pt%60}m"
            else:
                meta = "Never played" if not pt else f"Playtime {pt//60}h {pt%60}m"
            self.play_inst_meta.configure(text=meta)
            self.footer_version_label.configure(text=f"{ver} • {loader}")

            # icon
            self.play_inst_icon.delete("all")
            icon_name = inst.get("icon", "grass")
            from omnilauncher.gui.components.cards import ICON_COLORS
            col = ICON_COLORS.get(icon_name, th["accent"])
            self.play_inst_icon.create_rectangle(8, 8, 72, 72, fill=col, outline="", width=0)
            self.play_inst_icon.create_text(40, 42, text=inst.get("name", "?")[:1].upper(), font=("Segoe UI", 24, "bold"), fill="white")
            if inst.get("favorite"):
                self.play_inst_icon.create_text(64, 16, text="★", font=("Segoe UI", 14), fill="#ffcc00")

            # versions
            if not self.play_version_var.get():
                self.play_version_var.set(ver)

            # fav list small
            for w in self.play_fav_frame.winfo_children():
                w.destroy()
            favs = [i for i in self.settings.get("instances", "list", default=[]) if i.get("favorite")][:5]
            if not favs:
                favs = self.settings.get("instances", "list", default=[])[:5]
            for fav in favs:
                f = tk.Frame(self.play_fav_frame, bg=th["card_bg"], highlightthickness=1, highlightbackground=th["card_border"])
                f.pack(fill="x", pady=4)
                tk.Label(f, text=fav.get("name", "Instance"), font=("Segoe UI", 9, "bold"), bg=th["card_bg"], fg=th["text_primary"]).pack(side="left", padx=8, pady=8)
                tk.Label(f, text=fav.get("version", ""), font=("Segoe UI", 8), bg=th["card_bg"], fg=th["text_secondary"]).pack(side="left")
                tk.Button(f, text="▶", font=("Segoe UI", 8, "bold"), bg=th["accent"], fg="white", bd=0, command=lambda iid=fav["id"]: self._play_instance(iid)).pack(side="right", padx=8)

            # accounts combo
            accs = self.settings.get("accounts", "list", default=[])
            names = [a.get("username", "Steve") for a in accs]
            self.account_combo["values"] = names
            sel_idx = self.settings.get("accounts", "selected_index", default=0)
            if 0 <= sel_idx < len(names):
                self.play_account_var.set(names[sel_idx])
                self.play_account_sub.configure(text=f"{accs[sel_idx].get('type','offline')} • {accs[sel_idx].get('skin_type','steve')}")
            # sidebar user
            if accs and 0 <= sel_idx < len(accs):
                self.sidebar.update_user(names[sel_idx], "Ready • Offline")

        except Exception as e:
            # silent
            pass

    def _refresh_instances(self):
        th = self.theme
        if not hasattr(self, "instances_scroll"):
            return
        for w in self.instances_scroll.inner.winfo_children():
            w.destroy()

        instances = self.settings.get("instances", "list", default=[]) if self.settings else []
        search = self.search_var.get().lower()
        if search:
            instances = [i for i in instances if search in i.get("name", "").lower() or search in i.get("version", "").lower() or search in i.get("group", "").lower()]

        sort_by = self.sort_var.get() if hasattr(self, "sort_var") else "last_played"
        if sort_by == "name":
            instances = sorted(instances, key=lambda x: x.get("name", "").lower())
        elif sort_by == "version":
            instances = sorted(instances, key=lambda x: x.get("version", ""), reverse=True)
        elif sort_by == "playtime":
            instances = sorted(instances, key=lambda x: x.get("playtime_minutes", 0), reverse=True)
        else:  # last_played
            def lp_key(x):
                try:
                    return datetime.datetime.fromisoformat(x.get("last_played", "")) if x.get("last_played") else datetime.datetime.min
                except Exception:
                    return datetime.datetime.min
            instances = sorted(instances, key=lp_key, reverse=True)

        # groups
        groups: Dict[str, List[Dict]] = {}
        for inst in instances:
            g = inst.get("group", "Other")
            groups.setdefault(g, []).append(inst)

        for group_name, group_insts in groups.items():
            lbl = tk.Label(self.instances_scroll.inner, text=f"{group_name} ({len(group_insts)})", font=("Segoe UI", 10, "bold"), bg=th["bg"], fg=th["text_secondary"])
            lbl.pack(anchor="w", padx=8, pady=(16, 4))

            grid_frame = tk.Frame(self.instances_scroll.inner, bg=th["bg"])
            grid_frame.pack(fill="x", padx=4)

            # decide layout: grid vs list
            view = self.view_mode_var.get() if hasattr(self, "view_mode_var") else "grid"
            if view == "grid":
                # flow grid approx 3 columns
                row = tk.Frame(grid_frame, bg=th["bg"])
                row.pack(fill="x")
                col_count = 0
                for inst in group_insts:
                    if col_count >= 3:
                        row = tk.Frame(grid_frame, bg=th["bg"])
                        row.pack(fill="x")
                        col_count = 0
                    card_container = tk.Frame(row, bg=th["bg"])
                    card_container.pack(side="left", fill="x", expand=True, padx=6, pady=6)
                    card = InstanceCard(card_container, inst, th, self._play_instance, self._select_instance, self._instance_context)
                    card.pack(fill="x")
                    col_count += 1
            else:
                for inst in group_insts:
                    card = InstanceCard(grid_frame, inst, th, self._play_instance, self._select_instance, self._instance_context)
                    card.pack(fill="x", padx=6, pady=4)

    def _refresh_accounts(self):
        th = self.theme
        if not hasattr(self, "accounts_scroll"):
            return
        for w in self.accounts_scroll.inner.winfo_children():
            w.destroy()

        accs = self.settings.get("accounts", "list", default=[])
        sel_idx = self.settings.get("accounts", "selected_index", default=0)

        for idx, acc in enumerate(accs):
            card = AccountCard(
                self.accounts_scroll.inner,
                acc,
                th,
                idx,
                idx == sel_idx,
                self._select_account,
                self._remove_account,
            )
            card.pack(fill="x", pady=6)

    def _refresh_java_list(self):
        def fetch():
            javas = find_java_executables()
            self.root.after(0, lambda: self._apply_java_list(javas))
        threading.Thread(target=fetch, daemon=True).start()

    def _apply_java_list(self, javas: List[Dict[str, str]]):
        try:
            self.java_detected_listbox.delete(0, "end")
            for j in javas:
                self.java_detected_listbox.insert("end", f"{j.get('version','?')} • {j.get('path','')} [{j.get('source','')}]")
        except Exception:
            pass

    def _load_console_history(self):
        if launcher_svc:
            try:
                for line in launcher_svc.console_lines[-200:]:
                    self._append_console_line(line)
            except Exception:
                pass

    # actions

    def _play_instance(self, inst_id: str):
        self.settings.set_selected_instance(inst_id)
        self._refresh_play_page()
        self._on_launch_clicked()

    def _select_instance(self, inst_id: str):
        self.settings.set_selected_instance(inst_id)
        self._refresh_play_page()
        self._refresh_instances()

    def _instance_context(self, inst_id: str, x_root: int, y_root: int):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Play", command=lambda: self._play_instance(inst_id))
        menu.add_command(label="Edit", command=lambda: self._show_edit_instance_dialog(inst_id))
        menu.add_command(label="Duplicate", command=lambda: self._duplicate_instance(inst_id))
        menu.add_command(label="Toggle Favorite", command=lambda: (self.instance_svc.toggle_favorite(inst_id) if self.instance_svc else None, self._refresh_instances(), self._refresh_play_page()))
        menu.add_separator()
        menu.add_command(label="Open Folder", command=lambda: self._open_instance_folder(inst_id))
        menu.add_command(label="Delete", command=lambda: self._delete_instance(inst_id))
        try:
            menu.tk_popup(x_root, y_root)
        finally:
            menu.grab_release()

    def _open_instance_folder(self, inst_id: str):
        inst = next((i for i in self.settings.get("instances", "list", default=[]) if i.get("id") == inst_id), None)
        if inst:
            suffix = inst.get("minecraft_dir_suffix", inst_id)
            base = self.settings.minecraft_dir
            path = os.path.join(base, "instances", suffix) if suffix else base
            open_folder(path)
        else:
            open_folder(self.settings.minecraft_dir)

    def _delete_instance(self, inst_id: str):
        if messagebox.askyesno("Delete Instance", f"Delete instance {inst_id}? Worlds inside instance folder may be removed."):
            self.settings.remove_instance(inst_id)
            self._refresh_instances()
            self._refresh_play_page()

    def _duplicate_instance(self, inst_id: str):
        src = next((i for i in self.settings.get("instances", "list", default=[]) if i.get("id") == inst_id), None)
        if src:
            new_name = src.get("name", "Copy") + " Copy"
            self.settings.add_instance(new_name, src.get("version", ""), src.get("icon", "grass"), src.get("group", "Custom"))
            self._refresh_instances()

    def _show_new_instance_dialog(self):
        th = self.theme
        top = tk.Toplevel(self.root)
        top.title("New Instance")
        top.configure(bg=th["bg"])
        top.geometry("420x460")
        top.transient(self.root)
        top.grab_set()

        tk.Label(top, text="Create New Instance", font=("Segoe UI", 12, "bold"), bg=th["bg"], fg=th["text_primary"]).pack(pady=16)

        # name
        tk.Label(top, text="Name", bg=th["bg"], fg=th["text_secondary"], font=("Segoe UI", 9)).pack(anchor="w", padx=20)
        name_var = tk.StringVar(value="My Instance")
        tk.Entry(top, textvariable=name_var, bg=th["input_bg"], fg=th["text_primary"], bd=0, font=("Segoe UI", 10)).pack(fill="x", padx=20, pady=4, ipady=4)

        tk.Label(top, text="Version", bg=th["bg"], fg=th["text_secondary"], font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=(8, 0))
        ver_var = tk.StringVar(value=self.play_version_var.get() or get_latest_version(self.settings))
        # get all versions for combo
        all_ids = self.version_combo["values"] if hasattr(self, "version_combo") else ["1.21.1"]
        ttk.Combobox(top, textvariable=ver_var, values=all_ids, state="readonly").pack(fill="x", padx=20, pady=4)

        tk.Label(top, text="Group", bg=th["bg"], fg=th["text_secondary"], font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=(8, 0))
        group_var = tk.StringVar(value="Custom")
        ttk.Combobox(top, textvariable=group_var, values=["Vanilla", "Modded", "Custom", "Snapshots", "Testing"], state="normal").pack(fill="x", padx=20, pady=4)

        tk.Label(top, text="Icon", bg=th["bg"], fg=th["text_secondary"], font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=(8, 0))
        icon_var = tk.StringVar(value="grass")
        ttk.Combobox(top, textvariable=icon_var, values=BLOCK_ICONS, state="readonly").pack(fill="x", padx=20, pady=4)

        tk.Label(top, text="Loader", bg=th["bg"], fg=th["text_secondary"], font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=(8, 0))
        loader_var = tk.StringVar(value="vanilla")
        ttk.Combobox(top, textvariable=loader_var, values=["vanilla", "forge", "fabric", "quilt", "neoforge"], state="readonly").pack(fill="x", padx=20, pady=4)

        def create():
            name = name_var.get().strip() or "New Instance"
            ver = ver_var.get().strip()
            if not ver:
                messagebox.showwarning("Validation", "Version required")
                return
            inst = self.settings.add_instance(name, ver, icon_var.get(), group_var.get())
            inst["loader"] = loader_var.get()
            self.settings.save()
            top.destroy()
            self._refresh_instances()
            self._refresh_play_page()
            self._show_page("instances")

        tk.Button(top, text="Create", bg=th["accent"], fg="white", bd=0, font=("Segoe UI", 10, "bold"), command=create, padx=20, pady=8).pack(pady=16)

    def _show_edit_instance_dialog(self, inst_id: str):
        th = self.theme
        inst = next((i for i in self.settings.get("instances", "list", default=[]) if i.get("id") == inst_id), None)
        if not inst:
            return
        top = tk.Toplevel(self.root)
        top.title(f"Edit {inst.get('name','')}")
        top.configure(bg=th["bg"])
        top.geometry("440x500")
        top.transient(self.root)
        top.grab_set()

        tk.Label(top, text=f"Edit {inst.get('name')}", font=("Segoe UI", 12, "bold"), bg=th["bg"], fg=th["text_primary"]).pack(pady=16)

        name_var = tk.StringVar(value=inst.get("name", ""))
        ver_var = tk.StringVar(value=inst.get("version", ""))
        group_var = tk.StringVar(value=inst.get("group", "Custom"))
        icon_var = tk.StringVar(value=inst.get("icon", "grass"))
        ram_var = tk.StringVar(value=str(inst.get("ram_override") or ""))

        def row(label, var):
            tk.Label(top, text=label, bg=th["bg"], fg=th["text_secondary"], font=("Segoe UI", 9)).pack(anchor="w", padx=20, pady=(8, 0))
            tk.Entry(top, textvariable=var, bg=th["input_bg"], fg=th["text_primary"], bd=0).pack(fill="x", padx=20, pady=4, ipady=4)

        row("Name", name_var)
        row("Version", ver_var)
        row("Group", group_var)
        row("Icon", icon_var)
        row("RAM Override (MB, empty = use global)", ram_var)

        def save():
            inst["name"] = name_var.get()
            inst["version"] = ver_var.get()
            inst["group"] = group_var.get()
            inst["icon"] = icon_var.get()
            try:
                inst["ram_override"] = int(ram_var.get()) if ram_var.get().strip() else None
            except Exception:
                inst["ram_override"] = None
            self.settings.save()
            top.destroy()
            self._refresh_instances()
            self._refresh_play_page()

        tk.Button(top, text="Save", bg=th["accent"], fg="white", bd=0, command=save, padx=20, pady=8).pack(pady=16)

    def _add_account(self):
        name = self.new_account_name.get().strip()
        if not name:
            messagebox.showwarning("Account", "Enter username")
            return
        try:
            self.account_svc.add_offline(name, self.new_account_skin.get())
            self.new_account_name.set("")
            self._refresh_accounts()
            self._refresh_play_page()
        except Exception as e:
            messagebox.showerror("Account", f"Failed: {e}")

    def _select_account(self, idx: int):
        self.settings.select_account(idx)
        self._refresh_accounts()
        self._refresh_play_page()

    def _remove_account(self, uuid_str: str):
        if messagebox.askyesno("Remove Account", "Remove this account?"):
            self.settings.remove_account(uuid_str)
            self._refresh_accounts()
            self._refresh_play_page()

    def _on_account_combo_changed(self):
        name = self.play_account_var.get()
        accs = self.settings.get("accounts", "list", default=[])
        for idx, acc in enumerate(accs):
            if acc.get("username") == name:
                self.settings.select_account(idx)
                self._refresh_play_page()
                break

    def _on_play_version_changed(self):
        ver = self.play_version_var.get()
        # update current instance version if default?
        inst = self.settings.current_instance
        if inst:
            # if user changes version on play page, update instance's version if it's the selected instance?
            # keep but also update footer
            self.footer_version_label.configure(text=f"{ver} • {inst.get('loader','vanilla')}")
            # optional: save to instance if user wants? We'll save
            inst["version"] = ver
            self.settings.save()

    def _quick_play(self, name: str):
        messagebox.showinfo("Quick Play", f"Quick play {name} - launching default instance with quick play map/server logic (placeholder).")
        self._on_launch_clicked()

    def _on_launch_clicked(self):
        # get selected account and version and instance
        accs = self.settings.get("accounts", "list", default=[])
        sel_idx = self.settings.get("accounts", "selected_index", default=0)
        if not (0 <= sel_idx < len(accs)):
            messagebox.showwarning("Launch", "No account selected")
            return
        username = accs[sel_idx].get("username", "Steve")
        version = self.play_version_var.get()
        if not version:
            messagebox.showwarning("Launch", "Select version")
            return
        ram_mb = int(self.ram_var.get())
        inst_id = self.settings.get("instances", "selected", default="default")

        # if account not matching combobox? already synced
        # disable button temporarily
        self.launch_btn.configure(state="disabled", text="Launching...")
        self.status_var.set(f"Launching {version} as {username}...")

        # check lib
        try:
            from omnilauncher.services.launcher import launch

            launch(username, version, ram_mb, self.settings, inst_id)
        except Exception as e:
            messagebox.showerror("Launch Error", f"Failed to launch: {e}")
            self.launch_btn.configure(state="normal", text="▶  PLAY")
            self.status_var.set("Ready")

    def _on_status_update(self, status: str):
        self.root.after(0, lambda: self.status_var.set(status))
        self.root.after(0, lambda: self.sidebar.update_user(self.settings.current_account.get("username", "Steve"), status))
        # re-enable launch when done/ready
        if status in ("Ready", "Done") or status.startswith("Exited") or "failed" in status.lower():
            self.root.after(0, lambda: self.launch_btn.configure(state="normal", text="▶  PLAY"))

    def _on_progress_update(self, prog: int, max_v: int):
        def upd():
            self.progress_max = max_v if max_v > 0 else 100
            percent = int((prog / self.progress_max) * 100) if self.progress_max else 0
            self.progress_var.set(percent)
        self.root.after(0, upd)

    def _on_console_line(self, line: str):
        self.root.after(0, lambda: self._append_console_line(line))

    def _append_console_line(self, line: str):
        try:
            if not hasattr(self, "console_text") or not self.console_text.winfo_exists():
                return
            self.console_text.configure(state="normal")
            # simple tag logic
            tag = "info"
            if "[ERROR]" in line or " ERROR " in line or "Exception" in line or "FAILED" in line:
                tag = "error"
            elif "[WARN]" in line or " WARN " in line:
                tag = "warn"

            timestamp = ""
            if self.settings.get("launcher", "console_show_timestamp", default=True):
                timestamp = datetime.datetime.now().strftime("%H:%M:%S ")

            if timestamp:
                self.console_text.insert("end", timestamp, "timestamp")

            self.console_text.insert("end", line, tag)
            if self.console_autoscroll_var.get() if hasattr(self, "console_autoscroll_var") else True:
                self.console_text.see("end")
            # limit lines
            lines = int(self.console_text.index("end-1c").split(".")[0])
            if lines > 5000:
                self.console_text.delete("1.0", f"{lines-4000}.0")
            self.console_text.configure(state="disabled")
        except Exception:
            pass

    def _poll_launcher_state(self):
        try:
            if launcher_svc:
                st = launcher_svc.current_status
                self.status_var.set(st)
                # progress
                prog = launcher_svc.current_progress
                mx = launcher_svc.current_max
                if mx > 0:
                    pct = int((prog / mx) * 100)
                    self.progress_var.set(pct)
        except Exception:
            pass
        self.root.after(200, self._poll_launcher_state)

    # settings helpers

    def _browse_folder(self, entry_widget: tk.Entry):
        folder = filedialog.askdirectory()
        if folder:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, folder)
            self.settings.set(folder, "general", "minecraft_directory")
            self.settings.save()

    def _browse_file(self, var: tk.StringVar):
        file = filedialog.askopenfilename(title="Select Java executable", filetypes=[("Java", "java*"), ("All", "*.*")])
        if file:
            var.set(file)

    def _change_theme(self, name: str):
        self.settings.set(name, "appearance", "theme")
        self.settings.save()
        # apply partially
        self.theme = get_theme(name)
        self.theme_name = name
        try:
            self.root.configure(bg=self.theme["bg"])
            self.header_frame.configure(bg=self.theme["header_bg"])
            self.header_title.configure(bg=self.theme["header_bg"], fg=self.theme["text_primary"])
            self.header_sub.configure(bg=self.theme["header_bg"])
            self.footer_frame.configure(bg=self.theme["footer_bg"])
            self.status_label.configure(bg=self.theme["footer_bg"])
            self.footer_version_label.configure(bg=self.theme["footer_bg"])
            self._configure_styles()
            messagebox.showinfo("Theme", f"Theme changed to {name}. Some colors will apply after restart for full effect.")
        except Exception:
            pass

    def _export_settings(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if path:
            try:
                with open(path, "w") as f:
                    json.dump(self.settings.data, f, indent=2)
                messagebox.showinfo("Export", f"Settings exported to {path}")
            except Exception as e:
                messagebox.showerror("Export", f"Failed: {e}")

    def _reset_settings(self):
        if messagebox.askyesno("Reset", "Reset all settings to defaults? This cannot be undone."):
            from omnilauncher.config.settings import DEFAULT_SETTINGS, SettingsManager

            self.settings._data = SettingsManager._deep_copy(DEFAULT_SETTINGS)
            self.settings.save()
            messagebox.showinfo("Reset", "Settings reset. Restart launcher.")
            self._initial_load()

    def _delete_all_data(self):
        if messagebox.askyesno("Warning", "Delete ALL Minecraft data in minecraft folder? This will remove worlds!"):
            mc_dir = self.settings.minecraft_dir
            try:
                import shutil

                shutil.rmtree(mc_dir)
                messagebox.showinfo("Deleted", f"Deleted {mc_dir}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed: {e}")

    def _toggle_view_mode(self):
        cur = self.view_mode_var.get()
        new = "list" if cur == "grid" else "grid"
        self.view_mode_var.set(new)
        self.settings.set(new, "instances", "view_mode")
        self.settings.save()
        self._refresh_instances()

    def _draw_skin_preview(self, skin_type: str):
        try:
            c = self.skin_canvas
            c.delete("all")
            th = self.theme
            c.configure(bg=th["input_bg"])
            # simple steve
            c.create_rectangle(80, 20, 120, 50, fill="#e8c4a8", outline="")
            c.create_rectangle(70, 50, 130, 110, fill=th["accent"], outline="")
            c.create_rectangle(50, 50, 70, 90, fill="#e8c4a8", outline="")
            c.create_rectangle(130, 50, 150, 90, fill="#e8c4a8", outline="")
            c.create_rectangle(80, 110, 100, 170, fill="#3a6ea5", outline="")
            c.create_rectangle(100, 110, 120, 170, fill="#3a6ea5", outline="")
            if skin_type == "alex":
                c.create_text(100, 200, text="Alex (slim)", fill=th["text_muted"], font=("Segoe UI", 9))
            else:
                c.create_text(100, 200, text="Steve (classic)", fill=th["text_muted"], font=("Segoe UI", 9))
        except Exception:
            pass

    def _apply_skin_type(self):
        st = self.skin_type_var.get()
        self._draw_skin_preview(st)
        # update current account skin type
        idx = self.settings.get("accounts", "selected_index", default=0)
        accs = self.settings.get("accounts", "list", default=[])
        if 0 <= idx < len(accs):
            accs[idx]["skin_type"] = st
            self.settings.save()
            self._refresh_accounts()
            messagebox.showinfo("Skin", f"Skin type set to {st}")

    # console actions
    def _clear_console(self):
        try:
            self.console_text.configure(state="normal")
            self.console_text.delete("1.0", "end")
            self.console_text.configure(state="disabled")
        except Exception:
            pass

    def _copy_console(self):
        try:
            txt = self.console_text.get("1.0", "end")
            self.root.clipboard_clear()
            self.root.clipboard_append(txt)
            messagebox.showinfo("Copied", "Console copied to clipboard.")
        except Exception:
            pass

    def _export_console(self):
        path = filedialog.asksaveasfilename(defaultextension=".log", filetypes=[("Log", "*.log"), ("Text", "*.txt")])
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self.console_text.get("1.0", "end"))
                messagebox.showinfo("Export", f"Console exported to {path}")
            except Exception as e:
                messagebox.showerror("Export", f"Failed: {e}")

    def _console_search(self):
        query = self.console_search_var.get()
        if not query:
            return
        try:
            self.console_text.tag_remove("search", "1.0", "end")
            self.console_text.tag_configure("search", background="yellow", foreground="black")
            start = "1.0"
            while True:
                pos = self.console_text.search(query, start, stopindex="end")
                if not pos:
                    break
                end = f"{pos}+{len(query)}c"
                self.console_text.tag_add("search", pos, end)
                start = end
            self.console_text.see(pos)
        except Exception:
            pass

    def _analyze_crash(self):
        try:
            log = self.console_text.get("1.0", "end")
            findings = analyze_crash(log)
            if CrashReportDialog is None:
                messagebox.showinfo("Crash Analyzer", "\n".join([f"{f['title']}: {f['description']}\nFix: {f['fix']}" for f in findings]) or "No issues detected.")
                return
            CrashReportDialog(self.root, self.theme, log, findings)
        except Exception as e:
            messagebox.showerror("Analyze", f"Failed: {e}")

    def _open_file_explorer(self):
        try:
            if FileExplorerDialog is None:
                open_folder(self.settings.minecraft_dir)
                return
            FileExplorerDialog(self.root, self.theme, self.settings.minecraft_dir)
        except Exception as e:
            messagebox.showerror("File Explorer", f"Failed: {e}\nOpening folder externally.")
            open_folder(self.settings.minecraft_dir)

    def _open_text_file(self, title: str, filename: str):
        try:
            from pathlib import Path

            root = Path(__file__).resolve().parents[3]
            fp = root / filename
            if not fp.exists():
                fp = Path.cwd() / filename
            content = fp.read_text(encoding="utf-8") if fp.exists() else f"{filename} not found at {fp}"
        except Exception as e:
            content = f"Failed to open {filename}: {e}"

        top = tk.Toplevel(self.root)
        top.title(title)
        top.geometry("600x500")
        top.configure(bg=self.theme["bg"])
        txt = tk.Text(top, wrap="word", bg=self.theme["input_bg"], fg=self.theme["text_primary"], font=("Segoe UI", 10))
        txt.pack(fill="both", expand=True, padx=8, pady=8)
        txt.insert("1.0", content)
        txt.configure(state="disabled")

    def _refresh_all(self):
        self._reload_versions()
        self._refresh_accounts()
        self._refresh_instances()
        self._refresh_play_page()
        self._refresh_java_list()
        self.status_var.set("Refreshed")

    def _on_closing(self):
        try:
            geom = self.root.geometry()
            self.settings.set(geom, "meta", "window_geometry")
            self.settings.set(False, "meta", "first_run")
            self.settings.save()
        except Exception:
            pass
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def main():
    app = OmniLauncherApp()
    app.run()


if __name__ == "__main__":
    main()

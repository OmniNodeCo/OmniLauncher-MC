"""Main launcher UI for OmniLauncher-MC."""

import sys
import os

_here = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, "frozen", False):
    _here = sys._MEIPASS
if _here not in sys.path:
    sys.path.insert(0, _here)

import subprocess
import threading
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Optional

import customtkinter as ctk
from PIL import Image

from appdata import AppDataManager
from auth import AuthManager
from profiles import Profile, ProfileManager
from settings import SettingsManager
from downloader import DownloadManager
from updater import UpdateChecker, CURRENT_VERSION
from utils import get_asset_path, get_java_executable, format_bytes


COLORS = {
    "bg_dark": "#0F0F14",
    "bg_card": "#1A1A24",
    "bg_hover": "#252535",
    "accent": "#6C3BF5",
    "accent_hover": "#7C4BFF",
    "accent_secondary": "#3B82F6",
    "text_primary": "#F1F5F9",
    "text_secondary": "#94A3B8",
    "text_dim": "#64748B",
    "success": "#22C55E",
    "warning": "#F59E0B",
    "error": "#EF4444",
    "border": "#2A2A3A",
}


class OmniLauncher(ctk.CTk):
    """Main application window."""

    def __init__(self):
        super().__init__()

        # App data manager (creates full directory structure)
        self.appdata = AppDataManager()
        self.appdata.clean_temp()
        self.appdata.clean_old_logs(max_days=30)
        self.appdata.clean_old_backups(max_count=10)

        # Managers (all use appdata)
        self.settings_mgr = SettingsManager(appdata_mgr=self.appdata)
        self.profile_mgr = ProfileManager(appdata_mgr=self.appdata)
        self.auth_mgr = AuthManager(appdata_mgr=self.appdata)
        self.download_mgr = DownloadManager(self.settings_mgr.get("minecraft_dir"))
        self.update_checker = UpdateChecker(appdata_mgr=self.appdata)

        # Window setup
        self.title("OmniLauncher-MC")
        self.geometry(
            "%dx%d" % (
                self.settings_mgr.get("window_width"),
                self.settings_mgr.get("window_height"),
            )
        )
        self.minsize(900, 600)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color=COLORS["bg_dark"])

        # State
        self.current_page = "home"
        self.is_downloading = False
        self.download_progress = 0
        self.download_max = 0
        self.update_info = None

        # Build UI
        self._build_ui()

        # Ensure logged in
        if not self.auth_mgr.is_logged_in():
            self.auth_mgr.login_offline("Player")

        # Check for updates in background
        if self.settings_mgr.get("check_updates_on_start"):
            self.update_checker.check_if_needed(callback=self._on_update_check)

    def _on_update_check(self, info):
        """Called when update check completes."""
        self.update_info = info
        if info.available and not self.update_checker.is_version_skipped(info.latest_version):
            self.after(0, self._show_update_banner)

    def _show_update_banner(self):
        """Show update available banner on home page."""
        if self.current_page == "home" and self.update_info and self.update_info.available:
            try:
                if hasattr(self, "update_banner"):
                    self.update_banner.destroy()
            except Exception:
                pass

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_content_area()
        self._show_page("home")

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self, width=220, corner_radius=0, fg_color=COLORS["bg_card"]
        )
        self.sidebar.grid(row=0, column=0, sticky="nswe")
        self.sidebar.grid_propagate(False)

        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=20, pady=(24, 8))

        ctk.CTkLabel(
            logo_frame,
            text="OmniLauncher",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["text_primary"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            logo_frame,
            text="Minecraft Edition",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_dim"],
        ).pack(anchor="w")

        ctk.CTkFrame(self.sidebar, height=1, fg_color=COLORS["border"]).pack(
            fill="x", padx=16, pady=16
        )

        self.nav_buttons = {}
        nav_items = [
            ("home", "Home"),
            ("profiles", "Profiles"),
            ("versions", "Versions"),
            ("settings", "Settings"),
        ]

        for page_id, label in nav_items:
            btn = ctk.CTkButton(
                self.sidebar,
                text=label,
                font=ctk.CTkFont(size=14),
                anchor="w",
                height=42,
                corner_radius=10,
                fg_color="transparent",
                hover_color=COLORS["bg_hover"],
                text_color=COLORS["text_secondary"],
                command=lambda p=page_id: self._show_page(p),
            )
            btn.pack(fill="x", padx=12, pady=2)
            self.nav_buttons[page_id] = btn

        ctk.CTkFrame(self.sidebar, fg_color="transparent").pack(
            fill="both", expand=True
        )

        user_frame = ctk.CTkFrame(
            self.sidebar, fg_color=COLORS["bg_hover"], corner_radius=12
        )
        user_frame.pack(fill="x", padx=12, pady=(0, 16))

        user_info = ctk.CTkFrame(user_frame, fg_color="transparent")
        user_info.pack(fill="x", padx=12, pady=12)

        self.username_label = ctk.CTkLabel(
            user_info,
            text=self.auth_mgr.username or "Not logged in",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text_primary"],
            anchor="w",
        )
        self.username_label.pack(anchor="w")

        ctk.CTkLabel(
            user_info,
            text="Offline Mode",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_dim"],
            anchor="w",
        ).pack(anchor="w")

        ctk.CTkLabel(
            self.sidebar,
            text="v%s by OmniNodeCo" % CURRENT_VERSION,
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_dim"],
        ).pack(pady=(0, 12))

    def _build_content_area(self):
        self.content = ctk.CTkFrame(self, fg_color=COLORS["bg_dark"], corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nswe")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

    def _show_page(self, page_id):
        for pid, btn in self.nav_buttons.items():
            if pid == page_id:
                btn.configure(
                    fg_color=COLORS["accent"],
                    text_color=COLORS["text_primary"],
                    hover_color=COLORS["accent_hover"],
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=COLORS["text_secondary"],
                    hover_color=COLORS["bg_hover"],
                )

        for widget in self.content.winfo_children():
            widget.destroy()

        self.current_page = page_id

        builders = {
            "home": self._build_home_page,
            "profiles": self._build_profiles_page,
            "versions": self._build_versions_page,
            "settings": self._build_settings_page,
        }
        builders.get(page_id, self._build_home_page)()

    # ─── HOME ────────────────────────────────────────────────

    def _build_home_page(self):
        page = ctk.CTkScrollableFrame(
            self.content, fg_color="transparent", corner_radius=0
        )
        page.pack(fill="both", expand=True, padx=32, pady=24)

        # Update banner
        if self.update_info and self.update_info.available:
            if not self.update_checker.is_version_skipped(self.update_info.latest_version):
                self.update_banner = ctk.CTkFrame(
                    page, fg_color="#1a2e1a", corner_radius=12,
                    border_width=1, border_color=COLORS["success"],
                )
                self.update_banner.pack(fill="x", pady=(0, 16))

                banner_inner = ctk.CTkFrame(self.update_banner, fg_color="transparent")
                banner_inner.pack(fill="x", padx=16, pady=12)

                ctk.CTkLabel(
                    banner_inner,
                    text="Update Available: %s" % self.update_info.latest_version,
                    font=ctk.CTkFont(size=14, weight="bold"),
                    text_color=COLORS["success"],
                ).pack(side="left")

                ctk.CTkButton(
                    banner_inner,
                    text="Skip",
                    width=60, height=28, corner_radius=6,
                    fg_color="transparent",
                    hover_color=COLORS["bg_hover"],
                    text_color=COLORS["text_dim"],
                    font=ctk.CTkFont(size=11),
                    command=lambda: self._skip_update(),
                ).pack(side="right", padx=(4, 0))

                ctk.CTkButton(
                    banner_inner,
                    text="Download",
                    width=90, height=28, corner_radius=6,
                    fg_color=COLORS["success"],
                    hover_color="#2ad064",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    command=lambda: self.update_checker.open_download_page(),
                ).pack(side="right")

        # Header
        ctk.CTkLabel(
            page,
            text="Welcome Back!",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=COLORS["text_primary"],
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(
            page,
            text="Ready to play Minecraft? Select a profile and launch.",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_secondary"],
            anchor="w",
        ).pack(fill="x", pady=(0, 24))

        # Launch card
        launch_card = ctk.CTkFrame(
            page, fg_color=COLORS["bg_card"], corner_radius=16, height=200
        )
        launch_card.pack(fill="x", pady=(0, 24))
        launch_card.pack_propagate(False)

        inner = ctk.CTkFrame(launch_card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=28, pady=24)

        top_row = ctk.CTkFrame(inner, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(
            top_row,
            text="Active Profile",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_dim"],
        ).pack(anchor="w")

        profile_names = self.profile_mgr.get_names()
        active = self.profile_mgr.get_active()

        self.home_profile_var = ctk.StringVar(value=active.name if active else "")
        self.home_profile_menu = ctk.CTkOptionMenu(
            top_row,
            values=profile_names if profile_names else ["Default"],
            variable=self.home_profile_var,
            font=ctk.CTkFont(size=14),
            width=300, height=38,
            fg_color=COLORS["bg_hover"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            dropdown_fg_color=COLORS["bg_card"],
            corner_radius=10,
            command=self._on_profile_select,
        )
        self.home_profile_menu.pack(anchor="w", pady=(4, 0))

        if active:
            resolved = self.download_mgr.resolve_version(active.version)
            version_text = "Version: %s  |  Loader: %s" % (resolved, active.loader.title())
        else:
            version_text = "No profile selected"

        self.version_info_label = ctk.CTkLabel(
            inner,
            text=version_text,
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_secondary"],
            anchor="w",
        )
        self.version_info_label.pack(fill="x", pady=(0, 16))

        bottom_row = ctk.CTkFrame(inner, fg_color="transparent")
        bottom_row.pack(fill="x")

        self.launch_btn = ctk.CTkButton(
            bottom_row,
            text="Launch Minecraft",
            font=ctk.CTkFont(size=16, weight="bold"),
            height=50, width=260, corner_radius=12,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self._launch_game,
        )
        self.launch_btn.pack(side="left")

        self.status_label = ctk.CTkLabel(
            bottom_row,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_dim"],
        )
        self.status_label.pack(side="left", padx=20)

        self.progress_bar = ctk.CTkProgressBar(
            page, height=6, corner_radius=3,
            fg_color=COLORS["bg_card"],
            progress_color=COLORS["accent"],
        )
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(
            page, text="", font=ctk.CTkFont(size=11),
            text_color=COLORS["text_dim"],
        )

        # Stats
        stats_frame = ctk.CTkFrame(page, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(0, 16))

        stats = [
            ("Profiles", str(len(self.profile_mgr.profiles))),
            ("Installed", str(len(self.download_mgr.get_installed_versions()))),
            ("Player", self.auth_mgr.username),
            ("Data", self.appdata.get_size_formatted()),
        ]

        for label, value in stats:
            card = ctk.CTkFrame(stats_frame, fg_color=COLORS["bg_card"], corner_radius=12)
            card.pack(side="left", fill="x", expand=True, padx=(0, 12), ipady=12)
            ctk.CTkLabel(card, text=value,
                         font=ctk.CTkFont(size=20, weight="bold"),
                         text_color=COLORS["text_primary"]).pack()
            ctk.CTkLabel(card, text=label,
                         font=ctk.CTkFont(size=11),
                         text_color=COLORS["text_dim"]).pack()

    def _skip_update(self):
        if self.update_info:
            self.update_checker.skip_version(self.update_info.latest_version)
        if hasattr(self, "update_banner"):
            try:
                self.update_banner.destroy()
            except Exception:
                pass

    def _on_profile_select(self, name):
        profile = self.profile_mgr.get_by_name(name)
        if profile:
            self.profile_mgr.set_active(profile.id)
            resolved = self.download_mgr.resolve_version(profile.version)
            self.version_info_label.configure(
                text="Version: %s  |  Loader: %s" % (resolved, profile.loader.title())
            )

    # ─── PROFILES ────────────────────────────────────────────

    def _build_profiles_page(self):
        page = ctk.CTkScrollableFrame(
            self.content, fg_color="transparent", corner_radius=0
        )
        page.pack(fill="both", expand=True, padx=32, pady=24)

        header = ctk.CTkFrame(page, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(
            header, text="Profiles",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=COLORS["text_primary"],
        ).pack(side="left")

        ctk.CTkButton(
            header, text="+ New Profile",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38, width=140, corner_radius=10,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self._new_profile_dialog,
        ).pack(side="right")

        for profile in self.profile_mgr.profiles:
            is_active = profile.id == self.profile_mgr.active_id

            card = ctk.CTkFrame(
                page, fg_color=COLORS["bg_card"], corner_radius=14,
                border_width=2 if is_active else 0,
                border_color=COLORS["accent"] if is_active else COLORS["border"],
            )
            card.pack(fill="x", pady=4)

            inner = ctk.CTkFrame(card, fg_color="transparent")
            inner.pack(fill="x", padx=20, pady=16)

            info = ctk.CTkFrame(inner, fg_color="transparent")
            info.pack(side="left", fill="x", expand=True)

            name_row = ctk.CTkFrame(info, fg_color="transparent")
            name_row.pack(anchor="w")

            ctk.CTkLabel(
                name_row, text=profile.name,
                font=ctk.CTkFont(size=16, weight="bold"),
                text_color=COLORS["text_primary"],
            ).pack(side="left")

            if is_active:
                ctk.CTkLabel(
                    name_row, text="  ACTIVE",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color=COLORS["success"],
                ).pack(side="left", padx=(8, 0))

            resolved = self.download_mgr.resolve_version(profile.version)
            ctk.CTkLabel(
                info, text="%s  |  %s" % (resolved, profile.loader.title()),
                font=ctk.CTkFont(size=12),
                text_color=COLORS["text_dim"],
            ).pack(anchor="w")

            btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
            btn_frame.pack(side="right")

            if not is_active:
                ctk.CTkButton(
                    btn_frame, text="Set Active",
                    width=90, height=32, corner_radius=8,
                    font=ctk.CTkFont(size=11),
                    fg_color=COLORS["bg_hover"],
                    hover_color=COLORS["accent"],
                    command=lambda pid=profile.id: self._set_active_profile(pid),
                ).pack(side="left", padx=4)

            ctk.CTkButton(
                btn_frame, text="Delete",
                width=60, height=32, corner_radius=8,
                fg_color=COLORS["bg_hover"],
                hover_color=COLORS["error"],
                command=lambda pid=profile.id: self._delete_profile(pid),
            ).pack(side="left", padx=4)

    def _set_active_profile(self, profile_id):
        self.profile_mgr.set_active(profile_id)
        self._show_page("profiles")

    def _delete_profile(self, profile_id):
        if len(self.profile_mgr.profiles) > 1:
            self.profile_mgr.remove(profile_id)
            self._show_page("profiles")

    def _new_profile_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("New Profile")
        dialog.geometry("450x400")
        dialog.configure(fg_color=COLORS["bg_dark"])
        dialog.transient(self)
        dialog.grab_set()

        frame = ctk.CTkFrame(dialog, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=28, pady=24)

        ctk.CTkLabel(
            frame, text="Create New Profile",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=COLORS["text_primary"],
        ).pack(anchor="w", pady=(0, 20))

        ctk.CTkLabel(frame, text="Profile Name",
                     font=ctk.CTkFont(size=12),
                     text_color=COLORS["text_secondary"]).pack(anchor="w")
        name_entry = ctk.CTkEntry(
            frame, height=38, corner_radius=10,
            fg_color=COLORS["bg_card"],
            border_color=COLORS["border"],
            placeholder_text="My Profile",
        )
        name_entry.pack(fill="x", pady=(4, 16))

        ctk.CTkLabel(frame, text="Minecraft Version",
                     font=ctk.CTkFont(size=12),
                     text_color=COLORS["text_secondary"]).pack(anchor="w")

        versions = self.download_mgr.get_versions(
            include_snapshots=self.settings_mgr.get("show_snapshots")
        )
        version_ids = [v["id"] for v in versions[:50]]
        if not version_ids:
            version_ids = ["latest-release"]

        version_var = ctk.StringVar(value=version_ids[0])
        ctk.CTkOptionMenu(
            frame, values=version_ids, variable=version_var,
            height=38, corner_radius=10,
            fg_color=COLORS["bg_card"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            dropdown_fg_color=COLORS["bg_card"],
        ).pack(fill="x", pady=(4, 16))

        ctk.CTkLabel(frame, text="Mod Loader",
                     font=ctk.CTkFont(size=12),
                     text_color=COLORS["text_secondary"]).pack(anchor="w")

        loader_var = ctk.StringVar(value="vanilla")
        ctk.CTkOptionMenu(
            frame, values=["vanilla", "fabric", "forge", "quilt"],
            variable=loader_var, height=38, corner_radius=10,
            fg_color=COLORS["bg_card"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            dropdown_fg_color=COLORS["bg_card"],
        ).pack(fill="x", pady=(4, 24))

        def create():
            name = name_entry.get().strip()
            if not name:
                name = "Profile %d" % (len(self.profile_mgr.profiles) + 1)
            profile = Profile(
                name=name,
                version=version_var.get(),
                loader=loader_var.get(),
            )
            self.profile_mgr.add(profile)
            dialog.destroy()
            self._show_page("profiles")

        ctk.CTkButton(
            frame, text="Create Profile",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=44, corner_radius=10,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=create,
        ).pack(fill="x")

    # ─── VERSIONS ────────────────────────────────────────────

    def _build_versions_page(self):
        page = ctk.CTkScrollableFrame(
            self.content, fg_color="transparent", corner_radius=0
        )
        page.pack(fill="both", expand=True, padx=32, pady=24)

        ctk.CTkLabel(
            page, text="Available Versions",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=COLORS["text_primary"],
        ).pack(anchor="w", pady=(0, 20))

        installed = self.download_mgr.get_installed_versions()
        versions = self.download_mgr.get_versions(
            include_snapshots=self.settings_mgr.get("show_snapshots")
        )

        if not versions:
            ctk.CTkLabel(
                page,
                text="Could not fetch version list.\nCheck your internet connection.",
                font=ctk.CTkFont(size=14),
                text_color=COLORS["text_dim"],
            ).pack(pady=40)
            return

        for version in versions[:40]:
            vid = version["id"]
            vtype = version["type"]
            is_installed = vid in installed

            card = ctk.CTkFrame(page, fg_color=COLORS["bg_card"], corner_radius=12)
            card.pack(fill="x", pady=3)

            inner_v = ctk.CTkFrame(card, fg_color="transparent")
            inner_v.pack(fill="x", padx=16, pady=12)

            info_v = ctk.CTkFrame(inner_v, fg_color="transparent")
            info_v.pack(side="left", fill="x", expand=True)

            name_row_v = ctk.CTkFrame(info_v, fg_color="transparent")
            name_row_v.pack(anchor="w")

            ctk.CTkLabel(
                name_row_v, text=vid,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=COLORS["text_primary"],
            ).pack(side="left")

            type_colors = {
                "release": COLORS["success"],
                "snapshot": COLORS["warning"],
                "old_beta": COLORS["text_dim"],
                "old_alpha": COLORS["text_dim"],
            }
            ctk.CTkLabel(
                name_row_v, text="  %s" % vtype.upper(),
                font=ctk.CTkFont(size=9, weight="bold"),
                text_color=type_colors.get(vtype, COLORS["text_dim"]),
            ).pack(side="left")

            if is_installed:
                ctk.CTkLabel(
                    inner_v, text="Installed",
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color=COLORS["success"],
                ).pack(side="right")
            else:
                ctk.CTkButton(
                    inner_v, text="Install",
                    width=80, height=30, corner_radius=8,
                    font=ctk.CTkFont(size=11),
                    fg_color=COLORS["accent"],
                    hover_color=COLORS["accent_hover"],
                    command=lambda v=vid: self._install_version(v),
                ).pack(side="right")

    def _install_version(self, version_id):
        if self.is_downloading:
            return
        self.is_downloading = True
        self._show_page("home")

        self.progress_bar.pack(fill="x", pady=(0, 4))
        self.progress_label.pack(anchor="w", pady=(0, 16))

        def on_progress(ptype, value):
            try:
                if ptype == "status":
                    self.progress_label.configure(text=str(value))
                elif ptype == "max":
                    self.download_max = value
                elif ptype == "progress":
                    if self.download_max > 0:
                        self.progress_bar.set(value / self.download_max)
            except Exception:
                pass

        def on_done(vid):
            self.is_downloading = False
            try:
                self.status_label.configure(text="%s installed!" % vid)
                self.progress_bar.pack_forget()
                self.progress_label.pack_forget()
            except Exception:
                pass

        def on_error(msg):
            self.is_downloading = False
            try:
                self.status_label.configure(text="Error: %s" % msg)
                self.progress_bar.pack_forget()
                self.progress_label.pack_forget()
            except Exception:
                pass

        self.download_mgr.install_version(
            version_id,
            progress_callback=on_progress,
            done_callback=on_done,
            error_callback=on_error,
        )

    # ─── SETTINGS ────────────────────────────────────────────

    def _build_settings_page(self):
        page = ctk.CTkScrollableFrame(
            self.content, fg_color="transparent", corner_radius=0
        )
        page.pack(fill="both", expand=True, padx=32, pady=24)

        ctk.CTkLabel(
            page, text="Settings",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=COLORS["text_primary"],
        ).pack(anchor="w", pady=(0, 24))

        # ── Account
        self._settings_section(page, "Account")
        account_card = self._settings_card(page)

        ctk.CTkLabel(account_card, text="Username",
                     font=ctk.CTkFont(size=12),
                     text_color=COLORS["text_secondary"]).pack(anchor="w")

        username_entry = ctk.CTkEntry(
            account_card, height=38, corner_radius=10,
            fg_color=COLORS["bg_hover"], border_color=COLORS["border"],
        )
        username_entry.insert(0, self.auth_mgr.username)
        username_entry.pack(fill="x", pady=(4, 12))

        self.status_label_settings = ctk.CTkLabel(
            account_card, text="", font=ctk.CTkFont(size=11),
        )

        def save_username():
            name = username_entry.get().strip()
            if self.auth_mgr.login_offline(name):
                self.username_label.configure(text=name)
                self.status_label_settings.configure(
                    text="Username saved!", text_color=COLORS["success"]
                )
            else:
                self.status_label_settings.configure(
                    text="Invalid username (3-16 alphanumeric)",
                    text_color=COLORS["error"],
                )

        ctk.CTkButton(
            account_card, text="Save Username",
            height=36, corner_radius=10,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=save_username, width=160,
        ).pack(anchor="w")

        self.status_label_settings.pack(anchor="w", pady=(8, 0))

        # ── Java
        self._settings_section(page, "Java")
        java_card = self._settings_card(page)

        ctk.CTkLabel(java_card, text="Java Executable Path (leave empty for auto-detect)",
                     font=ctk.CTkFont(size=12),
                     text_color=COLORS["text_secondary"]).pack(anchor="w")

        java_entry = ctk.CTkEntry(
            java_card, height=38, corner_radius=10,
            fg_color=COLORS["bg_hover"],
            border_color=COLORS["border"],
            placeholder_text="Auto-detect",
        )
        java_entry.insert(0, self.settings_mgr.get("java_path"))
        java_entry.pack(fill="x", pady=(4, 16))

        ram_value = self.settings_mgr.get("ram_max")
        ram_label = ctk.CTkLabel(
            java_card, text="Maximum RAM: %d MB" % ram_value,
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
        )
        ram_label.pack(anchor="w")

        def on_ram_change(value):
            val = int(value)
            ram_label.configure(text="Maximum RAM: %d MB" % val)
            self.settings_mgr.set("ram_max", val)

        ram_slider = ctk.CTkSlider(
            java_card, from_=512, to=16384, number_of_steps=31,
            height=16, fg_color=COLORS["bg_hover"],
            progress_color=COLORS["accent"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            command=on_ram_change,
        )
        ram_slider.set(ram_value)
        ram_slider.pack(fill="x", pady=(4, 12))

        ctk.CTkLabel(java_card, text="JVM Arguments",
                     font=ctk.CTkFont(size=12),
                     text_color=COLORS["text_secondary"]).pack(anchor="w")

        jvm_entry = ctk.CTkEntry(
            java_card, height=38, corner_radius=10,
            fg_color=COLORS["bg_hover"],
            border_color=COLORS["border"],
        )
        jvm_entry.insert(0, self.settings_mgr.get("java_args"))
        jvm_entry.pack(fill="x", pady=(4, 0))

        # ── Game
        self._settings_section(page, "Game")
        game_card = self._settings_card(page)

        show_snap_var = ctk.BooleanVar(value=self.settings_mgr.get("show_snapshots"))
        ctk.CTkCheckBox(
            game_card, text="Show snapshot versions",
            variable=show_snap_var, font=ctk.CTkFont(size=13),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            border_color=COLORS["border"],
            command=lambda: self.settings_mgr.set("show_snapshots", show_snap_var.get()),
        ).pack(anchor="w", pady=4)

        close_var = ctk.BooleanVar(value=self.settings_mgr.get("close_on_launch"))
        ctk.CTkCheckBox(
            game_card, text="Close launcher when game starts",
            variable=close_var, font=ctk.CTkFont(size=13),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            border_color=COLORS["border"],
            command=lambda: self.settings_mgr.set("close_on_launch", close_var.get()),
        ).pack(anchor="w", pady=4)

        # ── Updates
        self._settings_section(page, "Updates")
        update_card = self._settings_card(page)

        auto_update_var = ctk.BooleanVar(value=self.settings_mgr.get("check_updates_on_start"))
        ctk.CTkCheckBox(
            update_card, text="Check for updates on startup",
            variable=auto_update_var, font=ctk.CTkFont(size=13),
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            border_color=COLORS["border"],
            command=lambda: self.settings_mgr.set(
                "check_updates_on_start", auto_update_var.get()
            ),
        ).pack(anchor="w", pady=4)

        update_status_label = ctk.CTkLabel(
            update_card, text="", font=ctk.CTkFont(size=11),
        )
        update_status_label.pack(anchor="w", pady=(8, 0))

        def check_updates_now():
            update_status_label.configure(
                text="Checking...", text_color=COLORS["text_dim"]
            )

            def on_result(info):
                try:
                    if info.error:
                        self.after(0, lambda: update_status_label.configure(
                            text="Error: %s" % info.error,
                            text_color=COLORS["error"],
                        ))
                    elif info.available:
                        self.update_info = info
                        self.after(0, lambda: update_status_label.configure(
                            text="Update available: %s" % info.latest_version,
                            text_color=COLORS["success"],
                        ))
                    else:
                        self.after(0, lambda: update_status_label.configure(
                            text="You are on the latest version (%s)" % CURRENT_VERSION,
                            text_color=COLORS["success"],
                        ))
                except Exception:
                    pass

            self.update_checker.check_async(callback=on_result)

        ctk.CTkButton(
            update_card, text="Check for Updates Now",
            height=36, width=200, corner_radius=10,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=check_updates_now,
        ).pack(anchor="w", pady=(4, 0))

        # ── Data Management
        self._settings_section(page, "Data Management")
        data_card = self._settings_card(page)

        ctk.CTkLabel(
            data_card,
            text="App data location: %s" % str(self.appdata.root),
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_dim"],
            wraplength=500,
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            data_card,
            text="Total size: %s" % self.appdata.get_size_formatted(),
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_dim"],
        ).pack(anchor="w", pady=(0, 12))

        data_btn_frame = ctk.CTkFrame(data_card, fg_color="transparent")
        data_btn_frame.pack(anchor="w")

        data_status = ctk.CTkLabel(
            data_card, text="", font=ctk.CTkFont(size=11),
        )

        def do_backup():
            result = self.appdata.backup()
            if result:
                data_status.configure(
                    text="Backup created!", text_color=COLORS["success"]
                )
            else:
                data_status.configure(
                    text="Backup failed", text_color=COLORS["error"]
                )

        def do_clean():
            t = self.appdata.clean_temp()
            l = self.appdata.clean_old_logs()
            data_status.configure(
                text="Cleaned %d temp + %d logs" % (t, l),
                text_color=COLORS["success"],
            )

        def do_validate():
            results = self.appdata.validate()
            if results.get("all_ok"):
                data_status.configure(
                    text="All data valid!", text_color=COLORS["success"]
                )
            else:
                failed = [k for k, v in results.items() if v is False]
                data_status.configure(
                    text="Issues: %s" % ", ".join(failed),
                    text_color=COLORS["warning"],
                )

        def do_open_folder():
            import subprocess as sp
            import platform as plat
            path = str(self.appdata.root)
            system = plat.system()
            if system == "Windows":
                sp.Popen(["explorer", path])
            elif system == "Darwin":
                sp.Popen(["open", path])
            else:
                sp.Popen(["xdg-open", path])

        ctk.CTkButton(
            data_btn_frame, text="Backup", width=80, height=32,
            corner_radius=8, fg_color=COLORS["bg_hover"],
            hover_color=COLORS["accent"], command=do_backup,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            data_btn_frame, text="Clean", width=80, height=32,
            corner_radius=8, fg_color=COLORS["bg_hover"],
            hover_color=COLORS["accent"], command=do_clean,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            data_btn_frame, text="Validate", width=80, height=32,
            corner_radius=8, fg_color=COLORS["bg_hover"],
            hover_color=COLORS["accent"], command=do_validate,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            data_btn_frame, text="Open Folder", width=100, height=32,
            corner_radius=8, fg_color=COLORS["bg_hover"],
            hover_color=COLORS["accent"], command=do_open_folder,
        ).pack(side="left")

        data_status.pack(anchor="w", pady=(8, 0))

        # ── About
        self._settings_section(page, "About")
        about_card = self._settings_card(page)

        ctk.CTkLabel(
            about_card, text="OmniLauncher-MC v%s" % CURRENT_VERSION,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COLORS["text_primary"],
        ).pack(anchor="w")

        ctk.CTkLabel(
            about_card, text="Built by OmniNodeCo",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
        ).pack(anchor="w", pady=(4, 12))

        ctk.CTkButton(
            about_card, text="GitHub Repository",
            height=34, width=160, corner_radius=8,
            fg_color=COLORS["bg_hover"],
            hover_color=COLORS["accent"],
            command=lambda: webbrowser.open(
                "https://github.com/OmniNodeCo/OmniLauncher-MC"
            ),
        ).pack(anchor="w")

        # Save all
        def save_all():
            self.settings_mgr.set("java_path", java_entry.get().strip())
            self.settings_mgr.set("java_args", jvm_entry.get().strip())

        ctk.CTkButton(
            page, text="Save All Settings",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=44, corner_radius=12,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=save_all,
        ).pack(fill="x", pady=(24, 0))

    def _settings_section(self, parent, title):
        ctk.CTkLabel(
            parent, text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COLORS["text_primary"],
        ).pack(anchor="w", pady=(16, 8))

    def _settings_card(self, parent):
        card = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=14)
        card.pack(fill="x", pady=(0, 8))
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=16)
        return inner

    # ─── LAUNCH ──────────────────────────────────────────────

    def _launch_game(self):
        profile = self.profile_mgr.get_active()
        if not profile:
            self.status_label.configure(text="No profile selected!")
            return

        version_id = self.download_mgr.resolve_version(profile.version)
        if not version_id:
            self.status_label.configure(text="Could not resolve version!")
            return

        if not self.download_mgr.is_installed(version_id):
            self.status_label.configure(text="Installing %s..." % version_id)
            self._install_version(version_id)
            return

        ram_max = self.settings_mgr.get("ram_max")
        ram_min = self.settings_mgr.get("ram_min")
        jvm_args = ["-Xmx%dM" % ram_max, "-Xms%dM" % ram_min]

        extra_args = self.settings_mgr.get("java_args", "").strip()
        if extra_args:
            jvm_args.extend(extra_args.split())

        java_path = self.settings_mgr.get("java_path") or get_java_executable()
        auth_data = self.auth_mgr.get_login_data()
        mc_dir = self.settings_mgr.get("minecraft_dir")

        command = self.download_mgr.get_launch_command(
            version_id=version_id,
            username=auth_data["username"],
            uuid_str=auth_data["uuid"],
            token=auth_data["token"],
            java_path=java_path,
            jvm_args=jvm_args,
        )

        if not command:
            self.status_label.configure(text="Failed to build launch command!")
            return

        self.status_label.configure(text="Launching %s..." % version_id)

        profile.last_played = datetime.now().isoformat()
        self.profile_mgr.update(profile)

        def run_game():
            try:
                subprocess.Popen(command, cwd=mc_dir)
                if self.settings_mgr.get("close_on_launch"):
                    self.after(2000, self.destroy)
                else:
                    self.after(3000, lambda: self.status_label.configure(text=""))
            except Exception as e:
                self.after(
                    0,
                    lambda: self.status_label.configure(
                        text="Launch failed: %s" % str(e)
                    ),
                )

        threading.Thread(target=run_game, daemon=True).start()
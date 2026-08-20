"""OmniLauncher-MC main application - PySide6 modern redesign.

Full-featured dark launcher with sidebar navigation, instance management,
account switching, extensive settings, console, skin preview.
"""

from __future__ import annotations

import datetime
import json
import os
import platform
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QStackedWidget,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QSlider,
    QSpinBox,
    QDoubleSpinBox,
    QProgressBar,
    QScrollArea,
    QFrame,
    QTextEdit,
    QPlainTextEdit,
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
    QFileDialog,
    QMessageBox,
    QMenu,
    QDialog,
    QColorDialog,
    QTabWidget,
    QSplitter,
    QGroupBox,
    QButtonGroup,
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QSize
from PySide6.QtGui import QFont, QColor, QAction, QIcon, QPalette

from omnilauncher.config.settings import get_settings_manager, SettingsManager
from omnilauncher.gui.themes import get_theme, THEMES, ACCENT_PALETTE, generate_stylesheet
from omnilauncher.gui.components.sidebar import Sidebar
from omnilauncher.gui.components.cards import InstanceCard, AccountCard, ICON_COLORS

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
    from omnilauncher.services.file_explorer import get_bookmarks as get_file_bookmarks, list_files
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
    list_files = lambda x: []
    CrashReportDialog = None
    FileExplorerDialog = None
    launcher_svc = None


VERSION = "0.2.0"


# ------------------------------------------------------------------
# Utilities
# ------------------------------------------------------------------

def open_folder(path: str):
    p = Path(path)
    if not p.exists():
        try:
            p.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
    try:
        if platform.system() == "Windows":
            os.startfile(str(p))
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", str(p)])
        else:
            subprocess.Popen(["xdg-open", str(p)])
    except Exception as e:
        QMessageBox.critical(None, "Open Folder", f"Failed to open {path}\n{e}")


def make_scroll_area(widget: QWidget, theme: Dict[str, str]) -> QScrollArea:
    """Wrap a widget in a styled scroll area."""
    scroll = QScrollArea()
    scroll.setWidget(widget)
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
    return scroll


def make_card_frame(theme: Dict[str, str], parent=None) -> QFrame:
    """Create a card-styled frame."""
    f = QFrame(parent)
    f.setStyleSheet(f"""
        QFrame {{
            background-color: {theme['card_bg']};
            border: 1px solid {theme['card_border']};
            border-radius: 10px;
        }}
    """)
    return f


def make_section_label(text: str, theme: Dict[str, str], size: int = 16, bold: bool = True) -> QLabel:
    lbl = QLabel(text)
    weight = QFont.Weight.Bold if bold else QFont.Weight.Normal
    lbl.setFont(QFont("Segoe UI", size, weight))
    lbl.setStyleSheet(f"color: {theme['text_primary']};")
    return lbl


def make_desc_label(text: str, theme: Dict[str, str]) -> QLabel:
    lbl = QLabel(text)
    lbl.setFont(QFont("Segoe UI", 9))
    lbl.setStyleSheet(f"color: {theme['text_secondary']};")
    lbl.setWordWrap(True)
    return lbl


def make_accent_button(text: str, theme: Dict[str, str]) -> QPushButton:
    btn = QPushButton(text)
    btn.setProperty("accent", True)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


def make_toolbar_button(text: str, theme: Dict[str, str]) -> QPushButton:
    btn = QPushButton(text)
    btn.setFont(QFont("Segoe UI", 9))
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    return btn


# ------------------------------------------------------------------
# Background worker for version fetching
# ------------------------------------------------------------------

class VersionWorker(QThread):
    finished = Signal(list)

    def __init__(self, settings):
        super().__init__()
        self.settings = settings

    def run(self):
        try:
            refresh_cache()
            versions = get_version_list(self.settings)
            ids = [v["id"] for v in versions]
        except Exception:
            ids = get_release_versions(self.settings)
        self.finished.emit(ids)


class JavaWorker(QThread):
    finished = Signal(list)

    def run(self):
        javas = find_java_executables()
        self.finished.emit(javas)


# ------------------------------------------------------------------
# Main Window
# ------------------------------------------------------------------

class OmniLauncherApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings: SettingsManager = get_settings_manager()
        self.theme_name = self.settings.get("appearance", "theme", default="dark")
        self.theme = get_theme(self.theme_name)

        self.setWindowTitle(f"OmniLauncher-MC • v{VERSION}")
        geom = self.settings.get("meta", "window_geometry", default="1180x760")
        try:
            import re
            match = re.search(r"(\d+)\s*x\s*(\d+)", str(geom))
            if match:
                self.resize(int(match.group(1)), int(match.group(2)))
            else:
                self.resize(1180, 760)
        except Exception:
            self.resize(1180, 760)
        self.setMinimumSize(1060, 640)

        # Services
        self.account_svc = AccountService(self.settings) if AccountService else None
        self.instance_svc = InstanceService(self.settings) if InstanceService else None

        # State
        self.current_page = "play"
        self.versions_list: List[str] = []
        self._console_lines: List[str] = []
        self._updating_ui = False

        # Build UI
        self._build_ui()
        self._apply_theme()

        # Launcher listeners
        if launcher_svc:
            try:
                launcher_svc.add_status_listener(self._on_status_update)
                launcher_svc.add_progress_listener(self._on_progress_update)
                launcher_svc.add_console_listener(self._on_console_line)
            except Exception:
                pass

        # Initial load
        QTimer.singleShot(100, self._initial_load)
        QTimer.singleShot(200, self._poll_launcher_state)

    def _build_ui(self):
        t = self.theme

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar(t)
        self.sidebar.page_selected.connect(self._on_sidebar_select)
        main_layout.addWidget(self.sidebar)

        # Right side
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Header
        self.header_frame = QFrame()
        self.header_frame.setFixedHeight(64)
        self.header_frame.setObjectName("header")
        hdr_layout = QHBoxLayout(self.header_frame)
        hdr_layout.setContentsMargins(24, 0, 16, 0)

        self.header_title = QLabel("Play")
        self.header_title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.header_title.setStyleSheet(f"color: {t['text_primary']};")
        hdr_layout.addWidget(self.header_title)

        self.header_sub = QLabel("Launch and manage your Minecraft worlds")
        self.header_sub.setFont(QFont("Segoe UI", 9))
        self.header_sub.setStyleSheet(f"color: {t['text_secondary']};")
        hdr_layout.addWidget(self.header_sub)
        hdr_layout.addStretch()

        refresh_btn = make_toolbar_button("🔄 Refresh", t)
        refresh_btn.clicked.connect(self._refresh_all)
        hdr_layout.addWidget(refresh_btn)

        folder_btn = make_toolbar_button("📁 .minecraft", t)
        folder_btn.clicked.connect(lambda: open_folder(self.settings.minecraft_dir))
        hdr_layout.addWidget(folder_btn)

        right_layout.addWidget(self.header_frame)

        # Pages container (stacked)
        self.pages_stack = QStackedWidget()
        right_layout.addWidget(self.pages_stack, 1)

        # Build all pages
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

        # Footer
        self.footer_frame = QFrame()
        self.footer_frame.setFixedHeight(56)
        self.footer_frame.setObjectName("footer")
        footer_layout = QHBoxLayout(self.footer_frame)
        footer_layout.setContentsMargins(16, 0, 16, 0)

        self.status_label = QLabel("Ready")
        self.status_label.setFont(QFont("Segoe UI", 9))
        self.status_label.setStyleSheet(f"color: {t['text_secondary']};")
        footer_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(220)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        footer_layout.addWidget(self.progress_bar)

        footer_layout.addStretch()

        self.footer_version_label = QLabel("1.21.1 • Vanilla")
        self.footer_version_label.setFont(QFont("Segoe UI", 9))
        self.footer_version_label.setStyleSheet(f"color: {t['text_muted']};")
        footer_layout.addWidget(self.footer_version_label)

        self.launch_btn = QPushButton("▶  PLAY")
        self.launch_btn.setProperty("play", True)
        self.launch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.launch_btn.clicked.connect(self._on_launch_clicked)
        footer_layout.addWidget(self.launch_btn)

        right_layout.addWidget(self.footer_frame)

        main_layout.addWidget(right, 1)

        # Set initial page
        self._show_page("play")

    # ------------------------------------------------------------------
    # Page builders
    # ------------------------------------------------------------------

    def _make_page(self) -> QWidget:
        page = QWidget()
        page.setObjectName("page")
        return page

    def _make_page_scroll(self) -> tuple[QWidget, QWidget]:
        """Create a page with scroll area. Returns (outer_page, inner_content)."""
        outer = self._make_page()
        layout = QVBoxLayout(outer)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        inner = QWidget()
        inner.setObjectName("scrollContent")
        scroll.setWidget(inner)

        layout.addWidget(scroll)
        return outer, inner

    # PLAY PAGE
    def _build_play_page(self):
        t = self.theme
        outer = self._make_page()
        layout = QHBoxLayout(outer)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Left column
        left = QVBoxLayout()
        left.setSpacing(16)

        # Banner
        banner = make_card_frame(t)
        banner.setFixedHeight(140)
        b_layout = QVBoxLayout(banner)
        b_layout.setContentsMargins(20, 16, 20, 16)
        b_layout.addWidget(make_section_label(f"Welcome to OmniLauncher • v{VERSION}", t, 14))
        b_layout.addWidget(make_desc_label(
            "Manage instances, accounts, mods, and launch any Minecraft version • Offline and Microsoft accounts • Full crash analyzer", t))
        tip = QLabel("Built with PySide6 • Dark theme • File explorer • Server browser")
        tip.setFont(QFont("Segoe UI", 8))
        tip.setStyleSheet(f"color: {t['text_muted']};")
        b_layout.addWidget(tip)
        left.addWidget(banner)

        # Selected instance card
        inst_card = make_card_frame(t)
        inst_layout = QHBoxLayout(inst_card)
        inst_layout.setContentsMargins(16, 16, 16, 16)
        inst_layout.setSpacing(12)

        self.play_inst_icon = QLabel("L")
        self.play_inst_icon.setFixedSize(72, 72)
        self.play_inst_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.play_inst_icon.setStyleSheet(f"""
            QLabel {{
                background-color: {t['accent']};
                color: white;
                border-radius: 12px;
                font-size: 28px;
                font-weight: bold;
            }}
        """)
        inst_layout.addWidget(self.play_inst_icon)

        inst_text = QVBoxLayout()
        inst_text.setSpacing(4)
        self.play_inst_name = QLabel("Latest Release")
        self.play_inst_name.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.play_inst_name.setStyleSheet(f"color: {t['text_primary']};")
        inst_text.addWidget(self.play_inst_name)

        self.play_inst_details = QLabel("1.21.1 • Vanilla • 0h played")
        self.play_inst_details.setFont(QFont("Segoe UI", 10))
        self.play_inst_details.setStyleSheet(f"color: {t['text_secondary']};")
        inst_text.addWidget(self.play_inst_details)

        self.play_inst_meta = QLabel("Never played • Default group")
        self.play_inst_meta.setFont(QFont("Segoe UI", 8))
        self.play_inst_meta.setStyleSheet(f"color: {t['text_muted']};")
        inst_text.addWidget(self.play_inst_meta)

        inst_layout.addLayout(inst_text, 1)
        left.addWidget(inst_card)

        # Launch options row
        opts_layout = QHBoxLayout()
        opts_layout.setSpacing(8)

        # Version selector
        ver_card = make_card_frame(t)
        vc_layout = QVBoxLayout(ver_card)
        vc_layout.setContentsMargins(12, 12, 12, 12)
        vc_layout.setSpacing(6)
        vc_layout.addWidget(make_section_label("Version", t, 9))

        self.version_combo = QComboBox()
        self.version_combo.currentTextChanged.connect(self._on_play_version_changed)
        vc_layout.addWidget(self.version_combo)

        filter_layout = QHBoxLayout()
        self.show_snap_var = QCheckBox("Snapshots")
        self.show_snap_var.setChecked(self.settings.get("general", "show_snapshots", default=False))
        self.show_snap_var.stateChanged.connect(self._reload_versions)
        filter_layout.addWidget(self.show_snap_var)

        self.show_beta_var = QCheckBox("Beta")
        self.show_beta_var.setChecked(self.settings.get("general", "show_beta", default=False))
        self.show_beta_var.stateChanged.connect(self._reload_versions)
        filter_layout.addWidget(self.show_beta_var)

        self.show_alpha_var = QCheckBox("Alpha")
        self.show_alpha_var.setChecked(self.settings.get("general", "show_alpha", default=False))
        self.show_alpha_var.stateChanged.connect(self._reload_versions)
        filter_layout.addWidget(self.show_alpha_var)

        vc_layout.addLayout(filter_layout)
        opts_layout.addWidget(ver_card)

        # Account selector
        acc_card = make_card_frame(t)
        ac_layout = QVBoxLayout(acc_card)
        ac_layout.setContentsMargins(12, 12, 12, 12)
        ac_layout.setSpacing(6)
        ac_layout.addWidget(make_section_label("Account", t, 9))

        self.account_combo = QComboBox()
        self.account_combo.currentTextChanged.connect(self._on_account_combo_changed)
        ac_layout.addWidget(self.account_combo)

        self.play_account_sub = QLabel("Offline • Steve skin")
        self.play_account_sub.setFont(QFont("Segoe UI", 8))
        self.play_account_sub.setStyleSheet(f"color: {t['text_muted']};")
        ac_layout.addWidget(self.play_account_sub)

        ram_label = QLabel(f"RAM: {self.settings.get('java', 'max_ram_mb', default=4096)} MB")
        ram_label.setFont(QFont("Segoe UI", 8))
        ram_label.setStyleSheet(f"color: {t['text_muted']};")
        ac_layout.addWidget(ram_label)

        self.ram_slider = QSlider(Qt.Orientation.Horizontal)
        self.ram_slider.setRange(1024, 12288)
        self.ram_slider.setSingleStep(256)
        self.ram_slider.setValue(self.settings.get("java", "max_ram_mb", default=4096))
        self.ram_slider.valueChanged.connect(lambda v: self._on_ram_changed(v, ram_label))
        ac_layout.addWidget(self.ram_slider)

        opts_layout.addWidget(acc_card)
        left.addLayout(opts_layout)

        # Quick play
        qp_card = make_card_frame(t)
        qp_layout = QVBoxLayout(qp_card)
        qp_layout.setContentsMargins(12, 12, 12, 12)
        qp_layout.addWidget(make_section_label("Quick Play", t, 10))

        qp_btns = QHBoxLayout()
        for name in ["Vanilla Shattered", "Survival World", "Creative Test", "Latest Snapshot"]:
            btn = QPushButton(name)
            btn.setFont(QFont("Segoe UI", 8))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, n=name: self._quick_play(n))
            qp_btns.addWidget(btn)
        qp_layout.addLayout(qp_btns)
        left.addWidget(qp_card)

        left.addStretch()

        # Right column
        right = QVBoxLayout()
        right.setSpacing(12)

        # Favorites header
        fav_hdr = QHBoxLayout()
        fav_hdr.addWidget(make_section_label("Favorites", t, 11))
        fav_hdr.addStretch()
        manage_btn = QPushButton("Manage")
        manage_btn.setFont(QFont("Segoe UI", 8))
        manage_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        manage_btn.clicked.connect(lambda: self._on_sidebar_select("instances"))
        fav_hdr.addWidget(manage_btn)
        right.addLayout(fav_hdr)

        # Favorites list
        self.play_fav_container = QWidget()
        self.play_fav_layout = QVBoxLayout(self.play_fav_container)
        self.play_fav_layout.setContentsMargins(0, 0, 0, 0)
        self.play_fav_layout.setSpacing(6)
        right.addWidget(self.play_fav_container)

        # News panel
        news = make_card_frame(t)
        news_layout = QVBoxLayout(news)
        news_layout.setContentsMargins(12, 12, 12, 12)
        news_layout.addWidget(make_section_label("Changelog / News", t, 10))

        news_text = QPlainTextEdit()
        news_text.setReadOnly(True)
        news_text.setFont(QFont("Segoe UI", 9))
        news_text.setPlainText(
            f"• {VERSION}: PySide6 GUI remake with modern dark theme\n"
            "• Added instance groups, favorites, quick play\n"
            "• Improved Java auto-detection\n"
            "• Console with search & filters\n"
            "• Account system with skin types\n"
            "• Appearance customization\n"
            "• File explorer bookmarks\n"
            "• Crash analyzer\n\n"
            "Tip: Enable snapshots in settings to test latest features.\n\n"
            "Updated with PySide6, modern features with modrinth placeholder, file manager, and server browser ideas."
        )
        news_text.setMaximumHeight(200)
        news_layout.addWidget(news_text)

        right.addWidget(news)
        right.addStretch()

        # Add columns
        left_widget = QWidget()
        left_widget.setLayout(left)
        right_widget = QWidget()
        right_widget.setLayout(right)
        right_widget.setFixedWidth(340)

        layout.addWidget(left_widget, 1)
        layout.addWidget(right_widget)

        self.play_page = outer
        self.pages_stack.addWidget(outer)

    # INSTANCES PAGE
    def _build_instances_page(self):
        t = self.theme
        outer = self._make_page()
        layout = QVBoxLayout(outer)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = QFrame()
        toolbar.setFixedHeight(56)
        toolbar.setObjectName("header")
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(16, 0, 16, 0)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search instances...")
        self.search_input.setFixedWidth(250)
        self.search_input.textChanged.connect(self._refresh_instances)
        tb_layout.addWidget(self.search_input)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["last_played", "name", "version", "playtime"])
        self.sort_combo.setCurrentText(self.settings.get("instances", "sort_by", default="last_played"))
        self.sort_combo.currentTextChanged.connect(self._refresh_instances)
        tb_layout.addWidget(self.sort_combo)

        self.view_mode_btn = QPushButton("Grid" if self.settings.get("instances", "view_mode", default="grid") == "grid" else "List")
        self.view_mode_btn.clicked.connect(self._toggle_view_mode)
        tb_layout.addWidget(self.view_mode_btn)

        tb_layout.addStretch()

        new_btn = make_accent_button("+ New Instance", t)
        new_btn.clicked.connect(self._show_new_instance_dialog)
        tb_layout.addWidget(new_btn)

        layout.addWidget(toolbar)

        # Instances scroll area
        self.instances_container = QWidget()
        self.instances_container.setObjectName("scrollContent")
        self.instances_layout = QVBoxLayout(self.instances_container)
        self.instances_layout.setContentsMargins(16, 16, 16, 16)
        self.instances_layout.setSpacing(8)
        self.instances_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidget(self.instances_container)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(scroll, 1)

        self.instances_page = outer
        self.pages_stack.addWidget(outer)

    # ACCOUNTS PAGE
    def _build_accounts_page(self):
        t = self.theme
        outer = self._make_page()
        layout = QVBoxLayout(outer)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Add account form
        form_card = make_card_frame(t)
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(16, 12, 16, 12)
        form_layout.addWidget(make_section_label("Add Offline Account", t, 11))

        form_row = QHBoxLayout()
        form_row.setSpacing(8)
        form_row.addWidget(QLabel("Username"))

        self.new_account_name = QLineEdit()
        self.new_account_name.setFixedWidth(200)
        self.new_account_name.setPlaceholderText("3-16 characters")
        form_row.addWidget(self.new_account_name)

        self.new_account_skin = QComboBox()
        self.new_account_skin.addItems(["steve", "alex"])
        form_row.addWidget(self.new_account_skin)

        add_btn = make_accent_button("Add Account", t)
        add_btn.clicked.connect(self._add_account)
        form_row.addWidget(add_btn)
        form_row.addStretch()

        form_layout.addLayout(form_row)
        layout.addWidget(form_card)

        # Account list
        self.accounts_container = QWidget()
        self.accounts_container.setObjectName("scrollContent")
        self.accounts_layout = QVBoxLayout(self.accounts_container)
        self.accounts_layout.setContentsMargins(0, 0, 0, 0)
        self.accounts_layout.setSpacing(8)
        self.accounts_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidget(self.accounts_container)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(scroll, 1)

        self.accounts_page = outer
        self.pages_stack.addWidget(outer)

    # MODS PAGE
    def _build_mods_page(self):
        t = self.theme
        page, inner = self._make_page_scroll()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(make_section_label("Mods & Addons", t))
        layout.addWidget(make_desc_label(
            "Modrinth & CurseForge integration • Search, browse, add mods, resource packs, shaders, worlds", t))

        grid = QHBoxLayout()
        grid.setSpacing(12)
        for mod_type in ["Mods", "Resource Packs", "Shaders", "Data Packs", "Worlds"]:
            card = make_card_frame(t)
            card.setFixedSize(170, 130)
            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(12, 16, 12, 12)
            c_layout.addWidget(make_section_label(mod_type, t, 11))
            browse = QLabel("Browse →")
            browse.setStyleSheet(f"color: {t['accent']}; background: transparent;")
            c_layout.addWidget(browse)
            c_layout.addWidget(make_desc_label("Coming soon", t))
            c_layout.addStretch()
            grid.addWidget(card)
        grid.addStretch()
        layout.addLayout(grid)

        # Features list
        feat = make_card_frame(t)
        feat_layout = QVBoxLayout(feat)
        feat_layout.setContentsMargins(16, 12, 16, 12)
        feat_layout.addWidget(make_section_label("Planned Features", t, 11))
        for bullet in [
            "• Auto-resolve dependencies from Modrinth",
            "• One-click install to any instance",
            "• Toggle mods on/off without deletion",
            "• Fractureiser malware scanner",
            "• Parallel downloads, GPU acceleration",
        ]:
            feat_layout.addWidget(make_desc_label(bullet, t))
        layout.addWidget(feat)
        layout.addStretch()

        self.mods_page = page
        self.pages_stack.addWidget(page)

    # EXPLORER PAGE
    def _build_explorer_page(self):
        t = self.theme
        outer = self._make_page()
        layout = QVBoxLayout(outer)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Title bar
        title_bar = QFrame()
        title_bar.setObjectName("header")
        title_bar.setFixedHeight(48)
        tl = QHBoxLayout(title_bar)
        tl.setContentsMargins(16, 0, 16, 0)
        tl.addWidget(make_section_label("File Explorer", t, 14))
        tl.addStretch()

        self.explorer_path_label = QLabel(self.settings.minecraft_dir)
        self.explorer_path_label.setFont(QFont("Segoe UI", 9))
        self.explorer_path_label.setStyleSheet(f"color: {t['text_secondary']};")
        tl.addWidget(self.explorer_path_label)

        up_btn = make_toolbar_button("↑ Up", t)
        up_btn.clicked.connect(self._explorer_go_up)
        tl.addWidget(up_btn)

        refresh_btn = make_toolbar_button("Refresh", t)
        refresh_btn.clicked.connect(self._refresh_explorer)
        tl.addWidget(refresh_btn)

        os_btn = make_toolbar_button("Open in OS", t)
        os_btn.clicked.connect(lambda: open_folder(self.explorer_current_path))
        tl.addWidget(os_btn)

        layout.addWidget(title_bar)

        # Content splitter
        content = QSplitter(Qt.Orientation.Horizontal)
        content.setHandleWidth(2)

        # Bookmarks
        bm_widget = QWidget()
        bm_widget.setFixedWidth(180)
        bm_layout = QVBoxLayout(bm_widget)
        bm_layout.setContentsMargins(12, 12, 12, 12)
        bm_layout.addWidget(make_section_label("Bookmarks", t, 10))

        self.explorer_current_path = self.settings.minecraft_dir

        try:
            from omnilauncher.services.file_explorer import get_bookmarks
            for bm in get_bookmarks(self.settings.minecraft_dir):
                btn = QPushButton(f"{bm['icon']}  {bm['name']}")
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        color: {t['text_secondary'] if bm['exists'] else t['text_muted']};
                        border: none;
                        text-align: left;
                        padding: 6px 8px;
                        border-radius: 6px;
                    }}
                    QPushButton:hover {{
                        background-color: {t['sidebar_hover']};
                        color: {t['text_primary']};
                    }}
                """)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.clicked.connect(lambda checked, p=bm['path']: self._explorer_navigate(p))
                bm_layout.addWidget(btn)
        except Exception:
            pass
        bm_layout.addStretch()

        content.addWidget(bm_widget)

        # File list
        self.explorer_list = QListWidget()
        self.explorer_list.setFont(QFont("Segoe UI", 10))
        self.explorer_list.itemDoubleClicked.connect(self._explorer_double_click)
        content.addWidget(self.explorer_list)

        layout.addWidget(content, 1)

        self.explorer_page = outer
        self.pages_stack.addWidget(outer)

        QTimer.singleShot(300, self._refresh_explorer)

    def _explorer_navigate(self, path: str):
        self.explorer_current_path = path
        self.explorer_path_label.setText(path)
        self._refresh_explorer()

    def _refresh_explorer(self):
        try:
            items = list_files(self.explorer_current_path)
            self.explorer_list.clear()
            self._explorer_items = items
            if not items:
                self.explorer_list.addItem("Folder empty or not found")
                return
            for it in items:
                prefix = "📁" if it["is_dir"] else "📄"
                text = f"{prefix}  {it['name']}/" if it["is_dir"] else f"{prefix}  {it['name']}  ({it['size']} bytes)"
                self.explorer_list.addItem(text)
        except Exception as e:
            self.explorer_list.clear()
            self.explorer_list.addItem(f"Error: {e}")

    def _explorer_double_click(self, item: QListWidgetItem):
        idx = self.explorer_list.row(item)
        if hasattr(self, '_explorer_items') and 0 <= idx < len(self._explorer_items):
            it = self._explorer_items[idx]
            if it["is_dir"]:
                self.explorer_current_path = it["path"]
                self.explorer_path_label.setText(it["path"])
                self._refresh_explorer()

    def _explorer_go_up(self):
        parent = str(Path(self.explorer_current_path).parent)
        if len(parent) >= 3:
            self.explorer_current_path = parent
            self.explorer_path_label.setText(parent)
            self._refresh_explorer()

    # SERVERS PAGE
    def _build_servers_page(self):
        t = self.theme
        page, inner = self._make_page_scroll()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(make_section_label("Server Browser", t))
        layout.addWidget(make_desc_label(
            "Experimental • Search, filter, sort servers, check player counts, join directly.", t))

        # Search toolbar
        toolbar = QFrame()
        toolbar.setObjectName("header")
        toolbar.setFixedHeight(48)
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(12, 0, 12, 0)

        search = QLineEdit()
        search.setPlaceholderText("🔍 Search servers...")
        tb_layout.addWidget(search)

        filter_combo = QComboBox()
        filter_combo.addItems(["All", "Survival", "Creative", "Minigames", "PvP", "Vanilla"])
        tb_layout.addWidget(filter_combo)

        refresh_btn = make_toolbar_button("Refresh", t)
        tb_layout.addWidget(refresh_btn)
        layout.addWidget(toolbar)

        # Fake servers
        servers = [
            {"name": "Hypixel", "ip": "mc.hypixel.net", "players": "45,231/100,000", "ping": "42ms", "version": "1.8-1.21", "motd": "The world's largest Minecraft server"},
            {"name": "Mineplex", "ip": "us.mineplex.com", "players": "12,442/30,000", "ping": "67ms", "version": "1.8-1.20", "motd": "Clans, Bridges, Survival"},
            {"name": "CubeCraft", "ip": "play.cubecraft.net", "players": "8,921/20,000", "ping": "89ms", "version": "1.9-1.21", "motd": "EggWars, SkyWars, BlockWars"},
            {"name": "Local LAN World", "ip": "192.168.1.10:25565", "players": "1/8", "ping": "12ms", "version": "1.21.1", "motd": "My survival world — open to LAN"},
        ]

        for srv in servers:
            card = make_card_frame(t)
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(12, 10, 12, 10)

            text = QVBoxLayout()
            text.setSpacing(3)
            name = QLabel(srv["name"])
            name.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            name.setStyleSheet(f"color: {t['text_primary']}; background: transparent;")
            text.addWidget(name)

            info = QLabel(f"{srv['ip']} • {srv['players']} • {srv['ping']} • {srv['version']}")
            info.setFont(QFont("Segoe UI", 8))
            info.setStyleSheet(f"color: {t['text_secondary']}; background: transparent;")
            text.addWidget(info)

            motd = QLabel(srv["motd"])
            motd.setFont(QFont("Segoe UI", 8))
            motd.setStyleSheet(f"color: {t['text_muted']}; background: transparent;")
            text.addWidget(motd)

            card_layout.addLayout(text, 1)

            join_btn = make_accent_button("Join", t)
            join_btn.clicked.connect(lambda checked, ip=srv["ip"]: self._join_server(ip))
            card_layout.addWidget(join_btn)

            layout.addWidget(card)

        layout.addStretch()
        self.servers_page = page
        self.pages_stack.addWidget(page)

    def _join_server(self, ip: str):
        QMessageBox.information(self, "Join Server",
                                f"Would join {ip} — sets auto-connect in Game settings and launches.\n(Feature placeholder)")

    # FRIENDS PAGE
    def _build_friends_page(self):
        t = self.theme
        page, inner = self._make_page_scroll()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(make_section_label("Friends List [Experimental]", t))
        layout.addWidget(make_desc_label(
            "Experimental: only for Microsoft accounts, disabled by default. See who is online, send invitations, manage status.", t))

        toggle = make_card_frame(t)
        toggle_layout = QVBoxLayout(toggle)
        toggle_layout.setContentsMargins(16, 12, 16, 12)
        toggle_layout.addWidget(make_desc_label(
            "Friends List is disabled by default (experimental). Enable in Settings.", t))
        enable_btn = QPushButton("Enable Friends List")
        enable_btn.setStyleSheet(f"color: {t['accent']}; background: transparent; border: none; font-weight: bold;")
        enable_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        toggle_layout.addWidget(enable_btn)
        layout.addWidget(toggle)

        # Fake friends
        for name, status, game in [("Alex", "Online", "Playing Hypixel"), ("Notch", "Offline", ""),
                                    ("Dinnerbone", "Online", "In menu"), ("Steve", "Online", "Playing Local World")]:
            row = make_card_frame(t)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(12, 8, 12, 8)

            dot = QLabel("●" if status == "Online" else "○")
            dot.setStyleSheet(f"color: {t['success'] if status == 'Online' else t['text_muted']}; background: transparent;")
            row_layout.addWidget(dot)

            n = QLabel(name)
            n.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            n.setStyleSheet(f"color: {t['text_primary']}; background: transparent;")
            row_layout.addWidget(n)

            s = QLabel(status)
            s.setFont(QFont("Segoe UI", 8))
            s.setStyleSheet(f"color: {t['text_secondary']}; background: transparent;")
            row_layout.addWidget(s)

            g = QLabel(game)
            g.setFont(QFont("Segoe UI", 8))
            g.setStyleSheet(f"color: {t['text_muted']}; background: transparent;")
            row_layout.addWidget(g)

            row_layout.addStretch()

            if status == "Online":
                inv = QPushButton("Invite")
                inv.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {t['accent_secondary']};
                        color: white;
                        border: none;
                        border-radius: 6px;
                        padding: 4px 12px;
                        font-size: 11px;
                    }}
                    QPushButton:hover {{ opacity: 0.8; }}
                """)
                row_layout.addWidget(inv)

            layout.addWidget(row)

        layout.addStretch()
        self.friends_page = page
        self.pages_stack.addWidget(page)

    # SKINS PAGE
    def _build_skins_page(self):
        t = self.theme
        outer = self._make_page()
        layout = QHBoxLayout(outer)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Preview
        preview = make_card_frame(t)
        preview.setFixedWidth(300)
        preview_layout = QVBoxLayout(preview)
        preview_layout.setContentsMargins(16, 16, 16, 16)
        preview_layout.addWidget(make_section_label("Skin Preview", t, 11))

        self.skin_preview = QLabel("Steve\n(classic)")
        self.skin_preview.setFixedSize(200, 260)
        self.skin_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.skin_preview.setStyleSheet(f"""
            QLabel {{
                background-color: {t['input_bg']};
                border-radius: 12px;
                color: {t['text_muted']};
                font-size: 12px;
            }}
        """)
        preview_layout.addWidget(self.skin_preview, 0, Qt.AlignmentFlag.AlignCenter)
        preview_layout.addStretch()

        # Options
        opts = QVBoxLayout()
        opts.setSpacing(12)

        opts.addWidget(make_section_label("Skins & Capes", t))
        opts.addWidget(make_section_label("Current Account", t, 10))
        self.skin_account_label = QLabel("Steve • Offline")
        self.skin_account_label.setFont(QFont("Segoe UI", 9))
        self.skin_account_label.setStyleSheet(f"color: {t['text_secondary']};")
        opts.addWidget(self.skin_account_label)

        opts.addWidget(make_section_label("Skin Model", t, 10))
        self.skin_type_combo = QComboBox()
        self.skin_type_combo.addItems(["steve", "alex"])
        opts.addWidget(self.skin_type_combo)

        apply_btn = QPushButton("Apply Skin Type")
        apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_btn.clicked.connect(self._apply_skin_type)
        opts.addWidget(apply_btn)

        opts.addWidget(make_section_label("Cape", t, 10))
        opts.addWidget(make_desc_label("Cape support with upload or select from library", t))

        open_skins = QPushButton("Open Skins Folder")
        open_skins.setCursor(Qt.CursorShape.PointingHandCursor)
        open_skins.clicked.connect(lambda: open_folder(os.path.join(self.settings.minecraft_dir, "skins")))
        opts.addWidget(open_skins)

        opts.addStretch()

        layout.addWidget(preview)
        opts_widget = QWidget()
        opts_widget.setLayout(opts)
        layout.addWidget(opts_widget, 1)

        self.skins_page = outer
        self.pages_stack.addWidget(outer)

    def _apply_skin_type(self):
        st = self.skin_type_combo.currentText()
        self.skin_preview.setText(f"{st.capitalize()}\n({'slim' if st == 'alex' else 'classic'})")
        idx = self.settings.get("accounts", "selected_index", default=0)
        accs = self.settings.get("accounts", "list", default=[])
        if 0 <= idx < len(accs):
            accs[idx]["skin_type"] = st
            self.settings.save()
            self._refresh_accounts()
            QMessageBox.information(self, "Skin", f"Skin type set to {st}")

    # SETTINGS PAGE
    def _build_settings_page(self):
        t = self.theme
        outer = self._make_page()
        layout = QHBoxLayout(outer)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Left nav
        left_nav = QFrame()
        left_nav.setFixedWidth(200)
        left_nav.setStyleSheet(f"background-color: {t['sidebar_bg']};")
        nav_layout = QVBoxLayout(left_nav)
        nav_layout.setContentsMargins(12, 16, 12, 12)
        nav_layout.addWidget(make_section_label("Settings", t, 12))

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
            btn = QPushButton(label)
            btn.setFont(QFont("Segoe UI", 10))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {t['text_secondary']};
                    border: none;
                    border-radius: 8px;
                    text-align: left;
                    padding: 10px 16px;
                }}
                QPushButton:hover {{
                    background-color: {t['sidebar_hover']};
                    color: {t['text_primary']};
                }}
            """)
            btn.clicked.connect(lambda checked, k=key: self._show_settings_subpage(k))
            nav_layout.addWidget(btn)
            self.settings_nav_buttons[key] = btn

        nav_layout.addStretch()
        layout.addWidget(left_nav)

        # Right content
        self.settings_stack = QStackedWidget()
        layout.addWidget(self.settings_stack, 1)

        # Build sub-pages
        self._build_settings_general()
        self._build_settings_java()
        self._build_settings_game()
        self._build_settings_appearance()
        self._build_settings_network()
        self._build_settings_launcher()
        self._build_settings_advanced()

        self._show_settings_subpage("general")

        self.settings_page = outer
        self.pages_stack.addWidget(outer)

    def _make_settings_page(self) -> QWidget:
        """Create a scrollable settings sub-page."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(8)
        return page

    def _add_settings_row(self, parent_layout: QVBoxLayout, title: str, desc: str,
                          control: QWidget | None = None):
        """Add a settings row with title, description, and optional control."""
        t = self.theme
        row = QFrame()
        row.setStyleSheet(f"background-color: {t['card_bg']}; border-radius: 8px;")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(16, 12, 16, 12)
        row_layout.setSpacing(16)

        text = QVBoxLayout()
        text.setSpacing(4)
        tl = QLabel(title)
        tl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        tl.setStyleSheet(f"color: {t['text_primary']}; background: transparent;")
        text.addWidget(tl)
        dl = QLabel(desc)
        dl.setFont(QFont("Segoe UI", 8))
        dl.setStyleSheet(f"color: {t['text_secondary']}; background: transparent;")
        dl.setWordWrap(True)
        text.addWidget(dl)
        row_layout.addLayout(text, 1)

        if control is not None:
            row_layout.addWidget(control)

        parent_layout.addWidget(row)

    def _add_settings_section(self, parent_layout: QVBoxLayout, title: str, desc: str):
        t = self.theme
        parent_layout.addWidget(make_section_label(title, t, 14))
        parent_layout.addWidget(make_desc_label(desc, t))
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {t['separator']};")
        parent_layout.addWidget(sep)

    def _build_settings_general(self):
        t = self.theme
        page = self._make_settings_page()
        layout = page.layout()

        self._add_settings_section(layout, "General", "Base launcher behavior, updates, minecraft folder, version filters.")

        # Language
        lang_combo = QComboBox()
        lang_combo.addItems(["en_US", "es_ES", "fr_FR", "de_DE", "pt_BR", "ru_RU"])
        lang_combo.setCurrentText(self.settings.get("general", "language", default="en_US"))
        lang_combo.currentTextChanged.connect(lambda v: (self.settings.set(v, "general", "language"), self.settings.save()))
        self._add_settings_row(layout, "Language", "Interface language. Restart required.", lang_combo)

        # MC dir
        dir_widget = QWidget()
        dir_layout = QHBoxLayout(dir_widget)
        dir_layout.setContentsMargins(0, 0, 0, 0)
        self.mc_dir_edit = QLineEdit(self.settings.get("general", "minecraft_directory", default=self.settings.minecraft_dir))
        self.mc_dir_edit.setFixedWidth(300)
        dir_layout.addWidget(self.mc_dir_edit)
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse_mc_dir)
        dir_layout.addWidget(browse_btn)
        self._add_settings_row(layout, "Minecraft Directory", "Folder where Minecraft stores worlds, mods, etc.", dir_widget)

        # Version toggles
        for key, title, desc in [
            ("show_snapshots", "Show Snapshots", "Include snapshot versions in version list."),
            ("show_beta", "Show Beta", "Include old beta versions."),
            ("show_alpha", "Show Alpha", "Include old alpha versions."),
            ("show_experimental", "Show Experimental", "Include experimental versions."),
            ("sort_versions_desc", "Sort Newest First", "Descending sort of versions."),
            ("check_updates", "Check for Launcher Updates", "Automatically check GitHub releases."),
        ]:
            default = True if key == "sort_versions_desc" else False
            chk = QCheckBox()
            chk.setChecked(self.settings.get("general", key, default=default))
            chk.stateChanged.connect(lambda state, k=key: (self.settings.set(bool(state), "general", k), self.settings.save()))
            self._add_settings_row(layout, title, desc, chk)

        # Keep launcher open
        keep_combo = QComboBox()
        keep_combo.addItems(["hide", "close", "keep_open", "minimize"])
        keep_combo.setCurrentText(self.settings.get("general", "keep_launcher_open", default="hide"))
        keep_combo.currentTextChanged.connect(lambda v: (self.settings.set(v, "general", "keep_launcher_open"), self.settings.save()))
        self._add_settings_row(layout, "Launcher Visibility After Game Start", "What to do with launcher when Minecraft launches.", keep_combo)

        # Concurrent downloads
        conc_spin = QSpinBox()
        conc_spin.setRange(1, 8)
        conc_spin.setValue(self.settings.get("general", "concurrent_downloads", default=4))
        conc_spin.valueChanged.connect(lambda v: (self.settings.set(v, "general", "concurrent_downloads"), self.settings.save()))
        self._add_settings_row(layout, "Concurrent Downloads", "How many files to download in parallel.", conc_spin)

        # Minimize to tray
        tray_chk = QCheckBox()
        tray_chk.setChecked(self.settings.get("general", "minimize_to_tray", default=False))
        tray_chk.stateChanged.connect(lambda state: (self.settings.set(bool(state), "general", "minimize_to_tray"), self.settings.save()))
        self._add_settings_row(layout, "Minimize to Tray", "Minimize launcher to system tray while playing.", tray_chk)

        layout.addStretch()
        self.settings_stack.addWidget(page)

    def _build_settings_java(self):
        t = self.theme
        page = self._make_settings_page()
        layout = page.layout()

        self._add_settings_section(layout, "Java", "Java runtime configuration with per-instance overrides and globally.")

        auto_chk = QCheckBox()
        auto_chk.setChecked(self.settings.get("java", "auto_detect", default=True))
        auto_chk.stateChanged.connect(lambda state: (self.settings.set(bool(state), "java", "auto_detect"), self.settings.save(), self._refresh_java_list()))
        self._add_settings_row(layout, "Auto-detect Java", "Automatically find installed Java versions.", auto_chk)

        # Java path
        java_widget = QWidget()
        java_layout = QHBoxLayout(java_widget)
        java_layout.setContentsMargins(0, 0, 0, 0)
        self.java_path_edit = QLineEdit(self.settings.get("java", "java_path", default=""))
        self.java_path_edit.setFixedWidth(300)
        self.java_path_edit.textChanged.connect(lambda v: (self.settings.set(v, "java", "java_path"), self.settings.save()))
        java_layout.addWidget(self.java_path_edit)
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse_java)
        java_layout.addWidget(browse_btn)
        self._add_settings_row(layout, "Java Executable Path", "Custom java binary. Leave empty for auto.", java_widget)

        # Detected list
        self.java_list_widget = QListWidget()
        self.java_list_widget.setMaximumHeight(130)
        self._add_settings_row(layout, "Java Installations", "Auto-detected Java runtimes.", self.java_list_widget)

        refresh_java_btn = QPushButton("Refresh Detection")
        refresh_java_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_java_btn.clicked.connect(self._refresh_java_list)
        layout.addWidget(refresh_java_btn)

        # RAM
        ram_widget = QWidget()
        ram_layout = QHBoxLayout(ram_widget)
        ram_layout.setContentsMargins(0, 0, 0, 0)
        ram_layout.addWidget(QLabel("Min"))
        min_ram = QSpinBox()
        min_ram.setRange(256, 4096)
        min_ram.setValue(self.settings.get("java", "min_ram_mb", default=512))
        min_ram.valueChanged.connect(lambda v: (self.settings.set(v, "java", "min_ram_mb"), self.settings.save()))
        ram_layout.addWidget(min_ram)
        ram_layout.addWidget(QLabel("Max"))
        max_ram = QSpinBox()
        max_ram.setRange(1024, 16384)
        max_ram.setValue(self.settings.get("java", "max_ram_mb", default=4096))
        max_ram.setSingleStep(256)
        max_ram.valueChanged.connect(lambda v: (self.settings.set(v, "java", "max_ram_mb"), self.settings.save()))
        ram_layout.addWidget(max_ram)
        self._add_settings_row(layout, "RAM Allocation (MB)", "Min/max memory for Minecraft JVM.", ram_widget)

        # JVM args
        jvm_chk = QCheckBox()
        jvm_chk.setChecked(self.settings.get("java", "use_custom_args", default=False))
        jvm_chk.stateChanged.connect(lambda state: (self.settings.set(bool(state), "java", "use_custom_args"), self.settings.save()))
        self._add_settings_row(layout, "Use Custom JVM Arguments", "Enable custom JVM args.", jvm_chk)

        jvm_edit = QLineEdit(self.settings.get("java", "jvm_args", default=""))
        jvm_edit.textChanged.connect(lambda v: (self.settings.set(v, "java", "jvm_args"), self.settings.save()))
        self._add_settings_row(layout, "JVM Arguments", "Custom JVM args like -XX:+UseG1GC", jvm_edit)

        # GC logging
        gc_chk = QCheckBox()
        gc_chk.setChecked(self.settings.get("java", "enable_gc_logging", default=False))
        gc_chk.stateChanged.connect(lambda state: (self.settings.set(bool(state), "java", "enable_gc_logging"), self.settings.save()))
        self._add_settings_row(layout, "Enable GC Logging", "Log garbage collector details.", gc_chk)

        layout.addStretch()
        self.settings_stack.addWidget(page)

    def _build_settings_game(self):
        t = self.theme
        page = self._make_settings_page()
        layout = page.layout()

        self._add_settings_section(layout, "Game", "Resolution, fullscreen, demo, custom game args, quick play.")

        res_chk = QCheckBox()
        res_chk.setChecked(self.settings.get("game", "resolution", "enabled", default=False))
        res_chk.stateChanged.connect(lambda state: (self.settings.set(bool(state), "game", "resolution", "enabled"), self.settings.save()))
        self._add_settings_row(layout, "Custom Resolution", "Enable custom window size.", res_chk)

        res_widget = QWidget()
        res_layout = QHBoxLayout(res_widget)
        res_layout.setContentsMargins(0, 0, 0, 0)
        res_layout.addWidget(QLabel("W"))
        w_spin = QSpinBox()
        w_spin.setRange(640, 3840)
        w_spin.setValue(self.settings.get("game", "resolution", "width", default=854))
        w_spin.valueChanged.connect(lambda v: (self.settings.set(v, "game", "resolution", "width"), self.settings.save()))
        res_layout.addWidget(w_spin)
        res_layout.addWidget(QLabel("H"))
        h_spin = QSpinBox()
        h_spin.setRange(480, 2160)
        h_spin.setValue(self.settings.get("game", "resolution", "height", default=480))
        h_spin.valueChanged.connect(lambda v: (self.settings.set(v, "game", "resolution", "height"), self.settings.save()))
        res_layout.addWidget(h_spin)
        fs_chk = QCheckBox("Fullscreen")
        fs_chk.setChecked(self.settings.get("game", "resolution", "fullscreen", default=False))
        fs_chk.stateChanged.connect(lambda state: (self.settings.set(bool(state), "game", "resolution", "fullscreen"), self.settings.save()))
        res_layout.addWidget(fs_chk)
        self._add_settings_row(layout, "Resolution Values", "Width, Height, fullscreen toggle.", res_widget)

        # Custom game args
        game_args_chk = QCheckBox()
        game_args_chk.setChecked(self.settings.get("game", "use_custom_args", default=False))
        game_args_chk.stateChanged.connect(lambda state: (self.settings.set(bool(state), "game", "use_custom_args"), self.settings.save()))
        self._add_settings_row(layout, "Use Custom Game Arguments", "Enable extra args passed to Minecraft.", game_args_chk)

        game_args_edit = QLineEdit(self.settings.get("game", "game_args", default=""))
        game_args_edit.textChanged.connect(lambda v: (self.settings.set(v, "game", "game_args"), self.settings.save()))
        self._add_settings_row(layout, "Game Arguments", "For example --server ip --port 25565.", game_args_edit)

        # Toggles
        for key, title, desc, default in [
            ("demo", "Demo Mode", "Launch game in demo mode.", False),
            ("disable_multiplayer", "Disable Multiplayer", "Disable multiplayer (parental control).", False),
            ("enable_logging", "Enable Game Logging", "Keep game logs on disk.", True),
            ("enable_chat_preview", "Enable Chat Preview", "Show chat preview.", True),
        ]:
            chk = QCheckBox()
            chk.setChecked(self.settings.get("game", key, default=default))
            chk.stateChanged.connect(lambda state, k=key: (self.settings.set(bool(state), "game", k), self.settings.save()))
            self._add_settings_row(layout, title, desc, chk)

        # Auto connect
        ac_widget = QWidget()
        ac_layout = QHBoxLayout(ac_widget)
        ac_layout.setContentsMargins(0, 0, 0, 0)
        ac_chk = QCheckBox()
        ac_chk.setChecked(self.settings.get("game", "auto_connect", "enabled", default=False))
        ac_chk.stateChanged.connect(lambda state: (self.settings.set(bool(state), "game", "auto_connect", "enabled"), self.settings.save()))
        ac_layout.addWidget(ac_chk)
        ac_edit = QLineEdit(self.settings.get("game", "auto_connect", "server", default=""))
        ac_edit.textChanged.connect(lambda v: (self.settings.set(v, "game", "auto_connect", "server"), self.settings.save()))
        ac_layout.addWidget(ac_edit)
        self._add_settings_row(layout, "Auto Connect Server", "Automatically connect to a server on launch.", ac_widget)

        layout.addStretch()
        self.settings_stack.addWidget(page)

    def _build_settings_appearance(self):
        t = self.theme
        page = self._make_settings_page()
        layout = page.layout()

        self._add_settings_section(layout, "Appearance", "Themes, accent colors, animations, layouts.")

        # Theme
        theme_combo = QComboBox()
        theme_combo.addItems(list(THEMES.keys()))
        theme_combo.setCurrentText(self.theme_name)
        theme_combo.currentTextChanged.connect(self._change_theme)
        self._add_settings_row(layout, "Theme", "Dark, Midnight, Light, AMOLED.", theme_combo)

        # Accent color
        accent_widget = QWidget()
        accent_layout = QHBoxLayout(accent_widget)
        accent_layout.setContentsMargins(0, 0, 0, 0)
        self.accent_edit = QLineEdit(self.settings.get("appearance", "accent_color", default=t["accent"]))
        self.accent_edit.setFixedWidth(100)
        self.accent_edit.textChanged.connect(lambda v: (self.settings.set(v, "appearance", "accent_color"), self.settings.save()))
        accent_layout.addWidget(self.accent_edit)
        for col in ACCENT_PALETTE[:10]:
            btn = QPushButton()
            btn.setFixedSize(24, 24)
            btn.setStyleSheet(f"background-color: {col}; border: none; border-radius: 4px;")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, c=col: (self.accent_edit.setText(c), self.settings.set(c, "appearance", "accent_color"), self.settings.save()))
            accent_layout.addWidget(btn)
        accent_layout.addStretch()
        self._add_settings_row(layout, "Accent Color", "Primary highlight color.", accent_widget)

        # Background style / layout
        for key, values, title, desc in [
            ("background_style", ["gradient", "solid", "image", "animated"], "Background Style", "Background rendering mode."),
            ("layout", ["modern", "classic"], "Layout Style", "Modern vs Classic."),
        ]:
            combo = QComboBox()
            combo.addItems(values)
            combo.setCurrentText(self.settings.get("appearance", key, default=values[0]))
            combo.currentTextChanged.connect(lambda v, k=key: (self.settings.set(v, "appearance", k), self.settings.save()))
            self._add_settings_row(layout, title, desc, combo)

        # Toggle settings
        for key, title, desc, default in [
            ("animations", "Enable Animations", "Transitions and animations.", True),
            ("compact_mode", "Compact Mode", "Less padding, more content.", False),
            ("sidebar_compact", "Compact Sidebar", "Icons only sidebar.", False),
            ("show_instance_icons", "Show Instance Icons", "Display block icons.", True),
        ]:
            chk = QCheckBox()
            chk.setChecked(self.settings.get("appearance", key, default=default))
            chk.stateChanged.connect(lambda state, k=key: (self.settings.set(bool(state), "appearance", k), self.settings.save()))
            self._add_settings_row(layout, title, desc, chk)

        # Font scale
        font_slider = QDoubleSpinBox()
        font_slider.setRange(0.8, 1.4)
        font_slider.setSingleStep(0.1)
        font_slider.setValue(self.settings.get("appearance", "font_scale", default=1.0))
        font_slider.valueChanged.connect(lambda v: (self.settings.set(v, "appearance", "font_scale"), self.settings.save()))
        self._add_settings_row(layout, "Font Scale", "Adjust overall font scaling.", font_slider)

        layout.addStretch()
        self.settings_stack.addWidget(page)

    def _build_settings_network(self):
        t = self.theme
        page = self._make_settings_page()
        layout = page.layout()

        self._add_settings_section(layout, "Network", "Offline mode, proxy, timeouts, parallel downloads.")

        for key, title, desc, default in [
            ("offline_mode", "Offline Mode", "Force offline even if internet available.", False),
            ("parallel_downloads", "Parallel Downloads", "Use parallel download engine.", True),
        ]:
            chk = QCheckBox()
            chk.setChecked(self.settings.get("network", key, default=default))
            chk.stateChanged.connect(lambda state, k=key: (self.settings.set(bool(state), "network", k), self.settings.save()))
            self._add_settings_row(layout, title, desc, chk)

        # Proxy
        proxy_chk = QCheckBox()
        proxy_chk.setChecked(self.settings.get("network", "proxy_enabled", default=False))
        proxy_chk.stateChanged.connect(lambda state: (self.settings.set(bool(state), "network", "proxy_enabled"), self.settings.save()))
        self._add_settings_row(layout, "Enable Proxy", "Route traffic through proxy.", proxy_chk)

        proxy_type = QComboBox()
        proxy_type.addItems(["http", "socks5", "system"])
        proxy_type.setCurrentText(self.settings.get("network", "proxy_type", default="http"))
        proxy_type.currentTextChanged.connect(lambda v: (self.settings.set(v, "network", "proxy_type"), self.settings.save()))
        self._add_settings_row(layout, "Proxy Type", "HTTP, SOCKS5, or System.", proxy_type)

        proxy_widget = QWidget()
        proxy_layout = QHBoxLayout(proxy_widget)
        proxy_layout.setContentsMargins(0, 0, 0, 0)
        proxy_layout.addWidget(QLabel("Host"))
        host_edit = QLineEdit(self.settings.get("network", "proxy_host", default=""))
        host_edit.textChanged.connect(lambda v: (self.settings.set(v, "network", "proxy_host"), self.settings.save()))
        proxy_layout.addWidget(host_edit)
        proxy_layout.addWidget(QLabel("Port"))
        port_spin = QSpinBox()
        port_spin.setRange(1, 65535)
        port_spin.setValue(self.settings.get("network", "proxy_port", default=8080))
        port_spin.valueChanged.connect(lambda v: (self.settings.set(v, "network", "proxy_port"), self.settings.save()))
        proxy_layout.addWidget(port_spin)
        self._add_settings_row(layout, "Proxy Host/Port", "Proxy server address.", proxy_widget)

        auth_widget = QWidget()
        auth_layout = QHBoxLayout(auth_widget)
        auth_layout.setContentsMargins(0, 0, 0, 0)
        auth_layout.addWidget(QLabel("User"))
        user_edit = QLineEdit(self.settings.get("network", "proxy_user", default=""))
        user_edit.textChanged.connect(lambda v: (self.settings.set(v, "network", "proxy_user"), self.settings.save()))
        auth_layout.addWidget(user_edit)
        auth_layout.addWidget(QLabel("Pass"))
        pass_edit = QLineEdit(self.settings.get("network", "proxy_pass", default=""))
        pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        pass_edit.textChanged.connect(lambda v: (self.settings.set(v, "network", "proxy_pass"), self.settings.save()))
        auth_layout.addWidget(pass_edit)
        self._add_settings_row(layout, "Proxy Authentication", "Optional proxy credentials.", auth_widget)

        timeout_spin = QSpinBox()
        timeout_spin.setRange(5, 120)
        timeout_spin.setValue(self.settings.get("network", "timeout", default=30))
        timeout_spin.valueChanged.connect(lambda v: (self.settings.set(v, "network", "timeout"), self.settings.save()))
        self._add_settings_row(layout, "Network Timeout (s)", "Timeout for downloads.", timeout_spin)

        layout.addStretch()
        self.settings_stack.addWidget(page)

    def _build_settings_launcher(self):
        t = self.theme
        page = self._make_settings_page()
        layout = page.layout()

        self._add_settings_section(layout, "Launcher & Console", "Console visibility, font, filters, logging, debug.")

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
            chk = QCheckBox()
            chk.setChecked(self.settings.get("launcher", key, default=default))
            chk.stateChanged.connect(lambda state, k=key: (self.settings.set(bool(state), "launcher", k), self.settings.save()))
            self._add_settings_row(layout, title, desc, chk)

        font_spin = QSpinBox()
        font_spin.setRange(8, 18)
        font_spin.setValue(self.settings.get("launcher", "console_font_size", default=10))
        font_spin.valueChanged.connect(lambda v: (self.settings.set(v, "launcher", "console_font_size"), self.settings.save()))
        self._add_settings_row(layout, "Console Font Size", "Adjust console text size.", font_spin)

        filter_combo = QComboBox()
        filter_combo.addItems(["all", "info", "warn", "error"])
        filter_combo.setCurrentText(self.settings.get("launcher", "console_filter_level", default="all"))
        filter_combo.currentTextChanged.connect(lambda v: (self.settings.set(v, "launcher", "console_filter_level"), self.settings.save()))
        self._add_settings_row(layout, "Console Filter Level", "Default log level filter.", filter_combo)

        days_spin = QSpinBox()
        days_spin.setRange(1, 30)
        days_spin.setValue(self.settings.get("launcher", "max_log_days", default=7))
        days_spin.valueChanged.connect(lambda v: (self.settings.set(v, "launcher", "max_log_days"), self.settings.save()))
        self._add_settings_row(layout, "Max Log Days", "Days to keep log files.", days_spin)

        layout.addStretch()
        self.settings_stack.addWidget(page)

    def _build_settings_advanced(self):
        t = self.theme
        page = self._make_settings_page()
        layout = page.layout()

        self._add_settings_section(layout, "Advanced", "Power user options: env vars, pre/post commands, crash analyzer.")

        adv_chk = QCheckBox()
        adv_chk.setChecked(self.settings.get("advanced", "enable_advanced_settings", default=False))
        adv_chk.stateChanged.connect(lambda state: (self.settings.set(bool(state), "advanced", "enable_advanced_settings"), self.settings.save()))
        self._add_settings_row(layout, "Enable Advanced Settings", "Unlock advanced fields below.", adv_chk)

        for key, title, desc in [
            ("custom_env_vars", "Custom Environment Variables", "KEY=VALUE pairs separated by ;"),
            ("pre_launch_command", "Pre-launch Command", "Command to run before game starts."),
            ("post_exit_command", "Post-exit Command", "Command after game exits."),
            ("wrapper_command", "Wrapper Command", "Prefix game command (e.g. gamemoderun)."),
        ]:
            edit = QLineEdit(self.settings.get("advanced", key, default=""))
            edit.textChanged.connect(lambda v, k=key: (self.settings.set(v, "advanced", k), self.settings.save()))
            self._add_settings_row(layout, title, desc, edit)

        for key, title, desc, default in [
            ("enable_process_monitor", "Enable Process Monitor", "Monitor game process for crashes.", True),
            ("kill_on_crash", "Kill on Crash", "Force kill if not responding.", False),
            ("enable_crash_analyzer", "Enable Crash Analyzer", "Analyze crash logs and suggest fixes.", True),
            ("scan_mods_for_malware", "Scan Mods for Malware", "Built-in Fractureiser detection.", True),
            ("ignore_java_check", "Ignore Java Check", "Skip Java version validation.", False),
        ]:
            chk = QCheckBox()
            chk.setChecked(self.settings.get("advanced", key, default=default))
            chk.stateChanged.connect(lambda state, k=key: (self.settings.set(bool(state), "advanced", k), self.settings.save()))
            self._add_settings_row(layout, title, desc, chk)

        # Actions
        actions = QHBoxLayout()
        open_btn = QPushButton("Open Settings File")
        open_btn.clicked.connect(lambda: open_folder(str(Path(self.settings.path).parent)))
        actions.addWidget(open_btn)

        export_btn = QPushButton("Export Settings")
        export_btn.clicked.connect(self._export_settings)
        actions.addWidget(export_btn)

        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setStyleSheet(f"QPushButton {{ background-color: {t['error']}; color: white; border: none; border-radius: 6px; padding: 8px 16px; }}")
        reset_btn.clicked.connect(self._reset_settings)
        actions.addWidget(reset_btn)

        delete_btn = QPushButton("Delete ALL Data")
        delete_btn.setStyleSheet("QPushButton { background-color: #ff0000; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold; }")
        delete_btn.clicked.connect(self._delete_all_data)
        actions.addWidget(delete_btn)

        actions.addStretch()
        layout.addLayout(actions)
        layout.addStretch()

        self.settings_stack.addWidget(page)

    def _show_settings_subpage(self, key: str):
        t = self.theme
        # Highlight active nav
        for k, btn in self.settings_nav_buttons.items():
            if k == key:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {t['sidebar_active']};
                        color: {t['text_primary']};
                        border: none;
                        border-radius: 8px;
                        text-align: left;
                        padding: 10px 16px;
                        font-weight: bold;
                        border-left: 3px solid {t['accent']};
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        color: {t['text_secondary']};
                        border: none;
                        border-radius: 8px;
                        text-align: left;
                        padding: 10px 16px;
                    }}
                    QPushButton:hover {{
                        background-color: {t['sidebar_hover']};
                        color: {t['text_primary']};
                    }}
                """)

        idx_map = {"general": 0, "java": 1, "game": 2, "appearance": 3,
                    "network": 4, "launcher": 5, "advanced": 6}
        if key in idx_map:
            self.settings_stack.setCurrentIndex(idx_map[key])

    # CONSOLE PAGE
    def _build_console_page(self):
        t = self.theme
        outer = self._make_page()
        layout = QVBoxLayout(outer)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = QFrame()
        toolbar.setFixedHeight(52)
        toolbar.setObjectName("header")
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(16, 0, 16, 0)

        tb_layout.addWidget(make_section_label("Console", t, 11))

        self.console_search_edit = QLineEdit()
        self.console_search_edit.setPlaceholderText("Search...")
        self.console_search_edit.setFixedWidth(160)
        tb_layout.addWidget(self.console_search_edit)

        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self._console_search)
        tb_layout.addWidget(search_btn)

        self.console_filter_combo = QComboBox()
        self.console_filter_combo.addItems(["all", "info", "warn", "error"])
        self.console_filter_combo.setCurrentText(self.settings.get("launcher", "console_filter_level", default="all"))
        tb_layout.addWidget(self.console_filter_combo)

        self.console_autoscroll_chk = QCheckBox("Auto-scroll")
        self.console_autoscroll_chk.setChecked(self.settings.get("launcher", "console_auto_scroll", default=True))
        tb_layout.addWidget(self.console_autoscroll_chk)

        tb_layout.addStretch()

        crash_btn = QPushButton("💥 Analyze Crash")
        crash_btn.setStyleSheet(f"QPushButton {{ background-color: #ff3b30; color: white; border: none; border-radius: 6px; padding: 6px 12px; font-weight: bold; font-size: 11px; }}")
        crash_btn.clicked.connect(self._analyze_crash)
        tb_layout.addWidget(crash_btn)

        for text, slot in [("📁 Explorer", self._open_file_explorer), ("Clear", self._clear_console),
                           ("Export", self._export_console), ("Copy", self._copy_console)]:
            btn = QPushButton(text)
            btn.clicked.connect(slot)
            tb_layout.addWidget(btn)

        layout.addWidget(toolbar)

        # Console text
        self.console_text = QPlainTextEdit()
        self.console_text.setReadOnly(True)
        self.console_text.setFont(QFont("Consolas", self.settings.get("launcher", "console_font_size", default=10)))
        self.console_text.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: #000000;
                color: #e0e0e0;
                border: none;
                padding: 8px;
            }}
        """)
        layout.addWidget(self.console_text, 1)

        self.console_page = outer
        self.pages_stack.addWidget(outer)

    # ABOUT PAGE
    def _build_about_page(self):
        t = self.theme
        page, inner = self._make_page_scroll()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header card
        header = make_card_frame(t)
        hdr_layout = QHBoxLayout(header)
        hdr_layout.setContentsMargins(24, 16, 16, 16)

        logo = QLabel("O")
        logo.setFixedSize(72, 72)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setStyleSheet(f"""
            QLabel {{
                background-color: {t['bg_secondary']};
                color: {t['accent']};
                border: 3px solid {t['accent']};
                border-radius: 36px;
                font-size: 32px;
                font-weight: bold;
            }}
        """)
        hdr_layout.addWidget(logo)

        txt = QVBoxLayout()
        txt.addWidget(make_section_label("OmniLauncher-MC", t, 18))
        v_label = QLabel(f"v{VERSION}")
        v_label.setStyleSheet(f"color: {t['text_secondary']};")
        txt.addWidget(v_label)
        txt.addWidget(make_desc_label("A modern, safe, open-source Minecraft launcher", t))
        hdr_layout.addLayout(txt, 1)

        btn_frame = QVBoxLayout()
        gh_btn = QPushButton("GitHub")
        gh_btn.clicked.connect(lambda: webbrowser.open("https://github.com/OmniNodeCo/OmniLauncher-MC"))
        btn_frame.addWidget(gh_btn)
        web_btn = QPushButton("Website")
        web_btn.clicked.connect(lambda: webbrowser.open("https://github.com/OmniNodeCo/OmniLauncher-MC"))
        btn_frame.addWidget(web_btn)
        hdr_layout.addLayout(btn_frame)

        layout.addWidget(header)

        # Info columns
        cols = QHBoxLayout()
        cols.setSpacing(16)

        # Changelog
        changelog = make_card_frame(t)
        cl_layout = QVBoxLayout(changelog)
        cl_layout.setContentsMargins(16, 12, 16, 12)
        cl_layout.addWidget(make_section_label("Changelog", t, 11))

        changelog_text = QPlainTextEdit()
        changelog_text.setReadOnly(True)
        changelog_text.setFont(QFont("Segoe UI", 9))
        try:
            cl_path = Path(__file__).resolve().parents[3] / "Changelog.txt"
            if cl_path.exists():
                changelog_text.setPlainText(cl_path.read_text(encoding="utf-8"))
            else:
                changelog_text.setPlainText(f"v{VERSION}\n- PySide6 GUI remake\n- Modern dark theme\n- All features preserved")
        except Exception:
            changelog_text.setPlainText(f"v{VERSION}\n- PySide6 GUI remake")
        changelog_text.setMaximumHeight(350)
        cl_layout.addWidget(changelog_text)
        cols.addWidget(changelog, 1)

        # Right column
        right_col = QVBoxLayout()
        right_col.setSpacing(12)

        # License
        lic = make_card_frame(t)
        lic_layout = QVBoxLayout(lic)
        lic_layout.setContentsMargins(12, 8, 12, 8)
        lic_layout.addWidget(make_section_label("License", t, 10))
        lic_layout.addWidget(make_desc_label("MIT License • Open Source", t))
        lic_btn = QPushButton("View LICENSE.txt")
        lic_btn.clicked.connect(lambda: self._open_text_file("License", "LICENSE.txt"))
        lic_layout.addWidget(lic_btn)
        right_col.addWidget(lic)

        # Terms
        terms = make_card_frame(t)
        terms_layout = QVBoxLayout(terms)
        terms_layout.setContentsMargins(12, 8, 12, 8)
        terms_layout.addWidget(make_section_label("Terms & Credits", t, 10))
        terms_layout.addWidget(make_desc_label("Not affiliated with Mojang or Microsoft.", t))
        for fname in ["TERMS.txt", "TREE.md"]:
            btn = QPushButton(f"View {fname}")
            btn.clicked.connect(lambda checked, f=fname: self._open_text_file(f.replace('.txt', '').replace('.md', ''), f))
            terms_layout.addWidget(btn)
        right_col.addWidget(terms)

        # System
        sysinfo = make_card_frame(t)
        sys_layout = QVBoxLayout(sysinfo)
        sys_layout.setContentsMargins(12, 8, 12, 8)
        sys_layout.addWidget(make_section_label("System", t, 10))
        sys_label = QLabel(
            f"OS: {platform.system()} {platform.release()}\n"
            f"Python: {platform.python_version()}\n"
            f"Qt: 6.x (PySide6)\n"
            f"Dir: {self.settings.minecraft_dir}"
        )
        sys_label.setFont(QFont("Segoe UI", 8))
        sys_label.setStyleSheet(f"color: {t['text_secondary']};")
        sys_layout.addWidget(sys_label)
        right_col.addWidget(sysinfo)

        right_col.addStretch()

        right_widget = QWidget()
        right_widget.setLayout(right_col)
        cols.addWidget(right_widget)

        layout.addLayout(cols)
        layout.addStretch()

        self.about_page = page
        self.pages_stack.addWidget(page)

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def _apply_theme(self):
        t = self.theme
        qss = generate_stylesheet(t)
        self.setStyleSheet(qss)

        # Apply specific header/footer/sidebar backgrounds
        self.header_frame.setStyleSheet(f"background-color: {t['header_bg']};")
        self.footer_frame.setStyleSheet(f"background-color: {t['footer_bg']};")

    def _change_theme(self, name: str):
        self.settings.set(name, "appearance", "theme")
        self.settings.save()
        self.theme = get_theme(name)
        self.theme_name = name
        self._apply_theme()
        QMessageBox.information(self, "Theme", f"Theme changed to {name}. Restart for full effect.")

    # ------------------------------------------------------------------
    # Page switching
    # ------------------------------------------------------------------

    def _show_page(self, key: str):
        page_map = {
            "play": 0, "instances": 1, "accounts": 2, "mods": 3,
            "explorer": 4, "servers": 5, "friends": 6, "skins": 7,
            "settings": 8, "console": 9, "about": 10,
        }

        titles = {
            "play": ("Play", "Launch and manage your Minecraft worlds"),
            "instances": ("Instances", "Manage your profiles • Vanilla, Forge, Fabric, Quilt, NeoForge"),
            "accounts": ("Accounts", "Offline & Microsoft accounts • Switch with one click"),
            "mods": ("Mods & Addons", "Modrinth & CurseForge integration"),
            "explorer": ("File Explorer", "Navigate files • Bookmarks for screenshots, worlds, logs"),
            "servers": ("Server Browser", "Search, filter, sort servers [Experimental]"),
            "friends": ("Friends List", "Experimental • Microsoft accounts only"),
            "skins": ("Skins", "Steve / Alex models, capes"),
            "settings": ("Settings", "Extensive configuration • General, Java, Game, Appearance, Network, Launcher, Advanced"),
            "console": ("Console", "Real-time log • Search, filter, crash reporter"),
            "about": ("About", "Version info, changelog, credits"),
        }

        if key in page_map:
            self.pages_stack.setCurrentIndex(page_map[key])

        if key in titles:
            t, sub = titles[key]
            self.header_title.setText(t)
            self.header_sub.setText(sub)

        self.current_page = key

        # Refresh data when entering
        if key == "instances":
            self._refresh_instances()
        elif key == "accounts":
            self._refresh_accounts()
        elif key == "play":
            self._refresh_play_page()

    def _on_sidebar_select(self, key: str):
        if key == "open_folder":
            open_folder(self.settings.minecraft_dir)
            return
        self.sidebar.set_active(key)
        self._show_page(key)

    # ------------------------------------------------------------------
    # Data refresh
    # ------------------------------------------------------------------

    def _initial_load(self):
        self._reload_versions()
        self._refresh_accounts()
        self._refresh_instances()
        self._refresh_play_page()
        self._refresh_java_list()
        self._load_console_history()

    def _reload_versions(self):
        self.settings.set(self.show_snap_var.isChecked(), "general", "show_snapshots")
        self.settings.set(self.show_beta_var.isChecked(), "general", "show_beta")
        self.settings.set(self.show_alpha_var.isChecked(), "general", "show_alpha")
        self.settings.save()

        self._version_worker = VersionWorker(self.settings)
        self._version_worker.finished.connect(self._apply_version_list)
        self._version_worker.start()

    def _apply_version_list(self, ids: List[str]):
        if not ids:
            ids = ["1.21.1", "1.20.1"]
        self.versions_list = ids
        self.version_combo.blockSignals(True)
        try:
            self.version_combo.clear()
            self.version_combo.addItems(ids)

            inst = self.settings.current_instance
            ver = inst.get("version") or get_latest_version(self.settings)
            if ver in ids:
                self.version_combo.setCurrentText(ver)
            elif ids:
                self.version_combo.setCurrentText(ids[0])
        finally:
            self.version_combo.blockSignals(False)
        self.footer_version_label.setText(f"{self.version_combo.currentText()} • Vanilla")

    def _refresh_play_page(self):
        if getattr(self, "_updating_ui", False):
            return
        self._updating_ui = True
        t = self.theme
        inst = self.settings.current_instance if self.settings else {
            "name": "Latest Release", "version": "1.21.1", "group": "Vanilla",
            "icon": "grass", "favorite": True
        }

        try:
            self.play_inst_name.setText(inst.get("name", "Latest Release"))
            ver = inst.get("version") or self.version_combo.currentText() or "1.21.1"
            loader = inst.get("loader", "vanilla")
            group = inst.get("group", "Custom")
            self.play_inst_details.setText(f"{ver} • {loader} • {group}")

            last = inst.get("last_played", "")
            pt = inst.get("playtime_minutes", 0)
            if last:
                try:
                    dt = datetime.datetime.fromisoformat(last)
                    last_s = dt.strftime("%b %d %Y %H:%M")
                except Exception:
                    last_s = last
                meta = f"Last played {last_s} • {pt // 60}h {pt % 60}m"
            else:
                meta = "Never played" if not pt else f"Playtime {pt // 60}h {pt % 60}m"
            self.play_inst_meta.setText(meta)
            self.footer_version_label.setText(f"{ver} • {loader}")

            # Icon
            icon_name = inst.get("icon", "grass")
            color = ICON_COLORS.get(icon_name, t["accent"])
            fav = inst.get("favorite", False)
            border = f"border: 2px solid #ffcc00;" if fav else ""
            self.play_inst_icon.setText(inst.get("name", "?")[:1].upper())
            self.play_inst_icon.setStyleSheet(f"""
                QLabel {{
                    background-color: {color};
                    color: white;
                    border-radius: 12px;
                    font-size: 28px;
                    font-weight: bold;
                    {border}
                }}
            """)

            if not self.version_combo.currentText():
                self.version_combo.blockSignals(True)
                self.version_combo.setCurrentText(ver)
                self.version_combo.blockSignals(False)

            # Favorites
            # Clear existing fav items
            while self.play_fav_layout.count():
                item = self.play_fav_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            favs = [i for i in self.settings.get("instances", "list", default=[]) if i.get("favorite")][:5]
            if not favs:
                favs = self.settings.get("instances", "list", default=[])[:5]
            for fav in favs:
                card = make_card_frame(t)
                card.setFixedHeight(48)
                cl = QHBoxLayout(card)
                cl.setContentsMargins(8, 4, 8, 4)
                name = QLabel(fav.get("name", "Instance"))
                name.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                name.setStyleSheet(f"color: {t['text_primary']}; background: transparent;")
                cl.addWidget(name)
                ver_lbl = QLabel(fav.get("version", ""))
                ver_lbl.setFont(QFont("Segoe UI", 8))
                ver_lbl.setStyleSheet(f"color: {t['text_secondary']}; background: transparent;")
                cl.addWidget(ver_lbl)
                cl.addStretch()
                play_btn = QPushButton("▶")
                play_btn.setFixedSize(32, 32)
                play_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {t['accent']};
                        color: white;
                        border: none;
                        border-radius: 6px;
                        font-weight: bold;
                    }}
                    QPushButton:hover {{ background-color: {t['accent_hover']}; }}
                """)
                play_btn.clicked.connect(lambda checked, iid=fav["id"]: self._play_instance(iid))
                cl.addWidget(play_btn)
                self.play_fav_layout.addWidget(card)

            # Accounts combo — block signals so setCurrentText cannot recurse
            accs = self.settings.get("accounts", "list", default=[])
            names = [a.get("username", "Steve") for a in accs]
            self.account_combo.blockSignals(True)
            try:
                self.account_combo.clear()
                self.account_combo.addItems(names)
                sel_idx = self.settings.get("accounts", "selected_index", default=0)
                if 0 <= sel_idx < len(names):
                    self.account_combo.setCurrentText(names[sel_idx])
                    self.play_account_sub.setText(
                        f"{accs[sel_idx].get('type', 'offline')} • {accs[sel_idx].get('skin_type', 'steve')}"
                    )
            finally:
                self.account_combo.blockSignals(False)

            sel_idx = self.settings.get("accounts", "selected_index", default=0)
            if accs and 0 <= sel_idx < len(accs):
                self.sidebar.update_user(names[sel_idx], "Ready • Offline")

        except Exception:
            pass
        finally:
            self._updating_ui = False

    def _refresh_instances(self):
        t = self.theme
        # Clear existing
        while self.instances_layout.count():
            item = self.instances_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        instances = self.settings.get("instances", "list", default=[]) if self.settings else []
        search = self.search_input.text().lower() if hasattr(self, 'search_input') else ""
        if search:
            instances = [i for i in instances if search in i.get("name", "").lower()
                         or search in i.get("version", "").lower()
                         or search in i.get("group", "").lower()]

        sort_by = self.sort_combo.currentText() if hasattr(self, 'sort_combo') else "last_played"
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

        # Group
        groups: Dict[str, List[Dict]] = {}
        for inst in instances:
            g = inst.get("group", "Other")
            groups.setdefault(g, []).append(inst)

        for group_name, group_insts in groups.items():
            lbl = QLabel(f"{group_name} ({len(group_insts)})")
            lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            lbl.setStyleSheet(f"color: {t['text_secondary']};")
            self.instances_layout.addWidget(lbl)

            view = self.view_mode_btn.text().lower() if hasattr(self, 'view_mode_btn') else "grid"

            if view == "grid":
                grid_widget = QWidget()
                grid = QGridLayout(grid_widget)
                grid.setSpacing(8)
                col = 0
                row = 0
                for inst in group_insts:
                    card = InstanceCard(inst, t)
                    card.play_clicked.connect(self._play_instance)
                    card.select_clicked.connect(self._select_instance)
                    card.context_menu.connect(self._instance_context)
                    grid.addWidget(card, row, col)
                    col += 1
                    if col >= 3:
                        col = 0
                        row += 1
                self.instances_layout.addWidget(grid_widget)
            else:
                for inst in group_insts:
                    card = InstanceCard(inst, t)
                    card.play_clicked.connect(self._play_instance)
                    card.select_clicked.connect(self._select_instance)
                    card.context_menu.connect(self._instance_context)
                    self.instances_layout.addWidget(card)

        self.instances_layout.addStretch()

    def _refresh_accounts(self):
        t = self.theme
        # Clear existing
        while self.accounts_layout.count():
            item = self.accounts_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        accs = self.settings.get("accounts", "list", default=[])
        sel_idx = self.settings.get("accounts", "selected_index", default=0)

        for idx, acc in enumerate(accs):
            card = AccountCard(acc, t, idx, idx == sel_idx)
            card.select_clicked.connect(self._select_account)
            card.delete_clicked.connect(self._remove_account)
            self.accounts_layout.addWidget(card)

        self.accounts_layout.addStretch()

    def _refresh_java_list(self):
        self._java_worker = JavaWorker()
        self._java_worker.finished.connect(self._apply_java_list)
        self._java_worker.start()

    def _apply_java_list(self, javas: List[Dict[str, str]]):
        if hasattr(self, 'java_list_widget'):
            self.java_list_widget.clear()
            for j in javas:
                self.java_list_widget.addItem(f"{j.get('version', '?')} • {j.get('path', '')} [{j.get('source', '')}]")

    def _load_console_history(self):
        if launcher_svc:
            try:
                for line in launcher_svc.console_lines[-200:]:
                    self._append_console_line(line)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _play_instance(self, inst_id: str):
        self.settings.set_selected_instance(inst_id)
        self._refresh_play_page()
        self._on_launch_clicked()

    def _select_instance(self, inst_id: str):
        self.settings.set_selected_instance(inst_id)
        self._refresh_play_page()
        self._refresh_instances()

    def _instance_context(self, inst_id: str, global_pos):
        menu = QMenu(self)
        menu.addAction("Play", lambda: self._play_instance(inst_id))
        menu.addAction("Edit", lambda: self._show_edit_instance_dialog(inst_id))
        menu.addAction("Duplicate", lambda: self._duplicate_instance(inst_id))
        menu.addAction("Toggle Favorite", lambda: self._toggle_favorite(inst_id))
        menu.addSeparator()
        menu.addAction("Open Folder", lambda: self._open_instance_folder(inst_id))
        menu.addAction("Delete", lambda: self._delete_instance(inst_id))
        menu.exec(global_pos)

    def _toggle_favorite(self, inst_id: str):
        if self.instance_svc:
            self.instance_svc.toggle_favorite(inst_id)
        self._refresh_instances()
        self._refresh_play_page()

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
        reply = QMessageBox.question(self, "Delete Instance", f"Delete instance {inst_id}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
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
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton
        t = self.theme

        dlg = QDialog(self)
        dlg.setWindowTitle("New Instance")
        dlg.setFixedSize(420, 460)
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        layout.addWidget(make_section_label("Create New Instance", t, 12))

        layout.addWidget(QLabel("Name"))
        name_edit = QLineEdit("My Instance")
        layout.addWidget(name_edit)

        layout.addWidget(QLabel("Version"))
        ver_combo = QComboBox()
        ver_combo.addItems(self.versions_list or ["1.21.1"])
        ver_combo.setEditable(True)
        layout.addWidget(ver_combo)

        layout.addWidget(QLabel("Group"))
        group_combo = QComboBox()
        group_combo.addItems(["Vanilla", "Modded", "Custom", "Snapshots", "Testing"])
        group_combo.setEditable(True)
        layout.addWidget(group_combo)

        layout.addWidget(QLabel("Icon"))
        icon_combo = QComboBox()
        icon_combo.addItems(BLOCK_ICONS)
        layout.addWidget(icon_combo)

        layout.addWidget(QLabel("Loader"))
        loader_combo = QComboBox()
        loader_combo.addItems(["vanilla", "forge", "fabric", "quilt", "neoforge"])
        layout.addWidget(loader_combo)

        def create():
            name = name_edit.text().strip() or "New Instance"
            ver = ver_combo.currentText().strip()
            if not ver:
                QMessageBox.warning(dlg, "Validation", "Version required")
                return
            inst = self.settings.add_instance(name, ver, icon_combo.currentText(), group_combo.currentText())
            inst["loader"] = loader_combo.currentText()
            self.settings.save()
            dlg.accept()
            self._refresh_instances()
            self._refresh_play_page()
            self._show_page("instances")

        create_btn = make_accent_button("Create", t)
        create_btn.clicked.connect(create)
        layout.addWidget(create_btn)

        dlg.exec()

    def _show_edit_instance_dialog(self, inst_id: str):
        t = self.theme
        inst = next((i for i in self.settings.get("instances", "list", default=[]) if i.get("id") == inst_id), None)
        if not inst:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Edit {inst.get('name', '')}")
        dlg.setFixedSize(440, 420)
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        layout.addWidget(make_section_label(f"Edit {inst.get('name')}", t, 12))

        name_edit = QLineEdit(inst.get("name", ""))
        layout.addWidget(QLabel("Name"))
        layout.addWidget(name_edit)

        ver_edit = QLineEdit(inst.get("version", ""))
        layout.addWidget(QLabel("Version"))
        layout.addWidget(ver_edit)

        group_edit = QLineEdit(inst.get("group", "Custom"))
        layout.addWidget(QLabel("Group"))
        layout.addWidget(group_edit)

        icon_edit = QLineEdit(inst.get("icon", "grass"))
        layout.addWidget(QLabel("Icon"))
        layout.addWidget(icon_edit)

        ram_edit = QLineEdit(str(inst.get("ram_override") or ""))
        layout.addWidget(QLabel("RAM Override (MB, empty = use global)"))
        layout.addWidget(ram_edit)

        def save():
            inst["name"] = name_edit.text()
            inst["version"] = ver_edit.text()
            inst["group"] = group_edit.text()
            inst["icon"] = icon_edit.text()
            try:
                inst["ram_override"] = int(ram_edit.text()) if ram_edit.text().strip() else None
            except Exception:
                inst["ram_override"] = None
            self.settings.save()
            dlg.accept()
            self._refresh_instances()
            self._refresh_play_page()

        save_btn = make_accent_button("Save", t)
        save_btn.clicked.connect(save)
        layout.addWidget(save_btn)

        dlg.exec()

    def _add_account(self):
        name = self.new_account_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Account", "Enter username")
            return
        try:
            self.account_svc.add_offline(name, self.new_account_skin.currentText())
            self.new_account_name.setText("")
            self._refresh_accounts()
            self._refresh_play_page()
        except Exception as e:
            QMessageBox.critical(self, "Account", f"Failed: {e}")

    def _select_account(self, idx: int):
        self.settings.select_account(idx)
        self._refresh_accounts()
        self._refresh_play_page()

    def _remove_account(self, uuid_str: str):
        reply = QMessageBox.question(self, "Remove Account", "Remove this account?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.settings.remove_account(uuid_str)
            self._refresh_accounts()
            self._refresh_play_page()

    def _on_account_combo_changed(self, name: str):
        if getattr(self, "_updating_ui", False) or not name:
            return
        accs = self.settings.get("accounts", "list", default=[])
        for idx, acc in enumerate(accs):
            if acc.get("username") == name:
                self.settings.select_account(idx)
                self.play_account_sub.setText(
                    f"{acc.get('type', 'offline')} • {acc.get('skin_type', 'steve')}"
                )
                self.sidebar.update_user(name, "Ready • Offline")
                break

    def _on_play_version_changed(self, ver: str):
        inst = self.settings.current_instance
        if inst:
            self.footer_version_label.setText(f"{ver} • {inst.get('loader', 'vanilla')}")
            inst["version"] = ver
            self.settings.save()

    def _on_ram_changed(self, value: int, label: QLabel):
        label.setText(f"RAM: {value} MB")
        self.settings.set(value, "java", "max_ram_mb")

    def _quick_play(self, name: str):
        QMessageBox.information(self, "Quick Play", f"Quick play {name} - launching with quick play logic (placeholder).")
        self._on_launch_clicked()

    def _on_launch_clicked(self):
        accs = self.settings.get("accounts", "list", default=[])
        sel_idx = self.settings.get("accounts", "selected_index", default=0)
        if not (0 <= sel_idx < len(accs)):
            QMessageBox.warning(self, "Launch", "No account selected")
            return
        username = accs[sel_idx].get("username", "Steve")
        version = self.version_combo.currentText()
        if not version:
            QMessageBox.warning(self, "Launch", "Select version")
            return
        ram_mb = self.ram_slider.value()
        inst_id = self.settings.get("instances", "selected", default="default")

        self.launch_btn.setEnabled(False)
        self.launch_btn.setText("Launching...")
        self.status_label.setText(f"Launching {version} as {username}...")

        try:
            from omnilauncher.services.launcher import launch
            launch(username, version, ram_mb, self.settings, inst_id)
        except Exception as e:
            QMessageBox.critical(self, "Launch Error", f"Failed to launch: {e}")
            self.launch_btn.setEnabled(True)
            self.launch_btn.setText("▶  PLAY")
            self.status_label.setText("Ready")

    def _on_status_update(self, status: str):
        QTimer.singleShot(0, lambda: self.status_label.setText(status))
        QTimer.singleShot(0, lambda: self.sidebar.update_user(
            self.settings.current_account.get("username", "Steve"), status))
        if status in ("Ready", "Done") or status.startswith("Exited") or "failed" in status.lower():
            QTimer.singleShot(0, lambda: (self.launch_btn.setEnabled(True), self.launch_btn.setText("▶  PLAY")))

    def _on_progress_update(self, prog: int, max_v: int):
        def upd():
            pct = int((prog / max(max_v, 1)) * 100)
            self.progress_bar.setValue(pct)
        QTimer.singleShot(0, upd)

    def _on_console_line(self, line: str):
        QTimer.singleShot(0, lambda: self._append_console_line(line))

    def _append_console_line(self, line: str):
        try:
            if not hasattr(self, "console_text"):
                return
            self.console_text.appendPlainText(line.rstrip())
            if self.console_autoscroll_chk.isChecked():
                scrollbar = self.console_text.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
            # Limit lines
            doc = self.console_text.document()
            if doc.blockCount() > 5000:
                cursor = self.console_text.textCursor()
                cursor.movePosition(cursor.MoveOperation.Start)
                cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.KeepAnchor, doc.blockCount() - 4000)
                cursor.removeSelectedText()
        except Exception:
            pass

    def _poll_launcher_state(self):
        try:
            if launcher_svc:
                self.status_label.setText(launcher_svc.current_status)
                prog = launcher_svc.current_progress
                mx = launcher_svc.current_max
                if mx > 0:
                    self.progress_bar.setValue(int((prog / mx) * 100))
        except Exception:
            pass
        QTimer.singleShot(200, self._poll_launcher_state)

    # ------------------------------------------------------------------
    # Console actions
    # ------------------------------------------------------------------

    def _clear_console(self):
        self.console_text.clear()

    def _copy_console(self):
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.console_text.toPlainText())
        QMessageBox.information(self, "Copied", "Console copied to clipboard.")

    def _export_console(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Console", "", "Log (*.log);;Text (*.txt)")
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self.console_text.toPlainText())
                QMessageBox.information(self, "Export", f"Console exported to {path}")
            except Exception as e:
                QMessageBox.critical(self, "Export", f"Failed: {e}")

    def _console_search(self):
        query = self.console_search_edit.text()
        if not query:
            return
        # Simple highlight - find and select
        cursor = self.console_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        self.console_text.setTextCursor(cursor)
        found = self.console_text.find(query)
        if not found:
            QMessageBox.information(self, "Search", f"'{query}' not found.")

    def _analyze_crash(self):
        try:
            log = self.console_text.toPlainText()
            findings = analyze_crash(log)
            if CrashReportDialog is None:
                QMessageBox.information(self, "Crash Analyzer",
                                        "\n".join([f"{f['title']}: {f['description']}\nFix: {f['fix']}" for f in findings]) or "No issues detected.")
                return
            dlg = CrashReportDialog(self.theme, log, findings, self)
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "Analyze", f"Failed: {e}")

    def _open_file_explorer(self):
        try:
            if FileExplorerDialog is None:
                open_folder(self.settings.minecraft_dir)
                return
            dlg = FileExplorerDialog(self.theme, self.settings.minecraft_dir, self)
            dlg.exec()
        except Exception as e:
            QMessageBox.critical(self, "File Explorer", f"Failed: {e}")
            open_folder(self.settings.minecraft_dir)

    # ------------------------------------------------------------------
    # Settings actions
    # ------------------------------------------------------------------

    def _browse_mc_dir(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Minecraft Directory")
        if folder:
            self.mc_dir_edit.setText(folder)
            self.settings.set(folder, "general", "minecraft_directory")
            self.settings.save()

    def _browse_java(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Java executable", "", "Java (java*);;All (*)")
        if file:
            self.java_path_edit.setText(file)

    def _export_settings(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Settings", "", "JSON (*.json)")
        if path:
            try:
                with open(path, "w") as f:
                    json.dump(self.settings.data, f, indent=2)
                QMessageBox.information(self, "Export", f"Settings exported to {path}")
            except Exception as e:
                QMessageBox.critical(self, "Export", f"Failed: {e}")

    def _reset_settings(self):
        reply = QMessageBox.question(self, "Reset", "Reset all settings to defaults?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            from omnilauncher.config.settings import DEFAULT_SETTINGS, SettingsManager
            self.settings._data = SettingsManager._deep_copy(DEFAULT_SETTINGS)
            self.settings.save()
            QMessageBox.information(self, "Reset", "Settings reset. Restart launcher.")
            self._initial_load()

    def _delete_all_data(self):
        reply = QMessageBox.warning(self, "Warning", "Delete ALL Minecraft data? This will remove worlds!",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                import shutil
                shutil.rmtree(self.settings.minecraft_dir)
                QMessageBox.information(self, "Deleted", f"Deleted {self.settings.minecraft_dir}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed: {e}")

    def _toggle_view_mode(self):
        cur = self.view_mode_btn.text().lower()
        new = "list" if cur == "grid" else "grid"
        self.view_mode_btn.setText(new.capitalize())
        self.settings.set(new, "instances", "view_mode")
        self.settings.save()
        self._refresh_instances()

    def _open_text_file(self, title: str, filename: str):
        try:
            fp = Path(__file__).resolve().parents[3] / filename
            if not fp.exists():
                fp = Path.cwd() / filename
            content = fp.read_text(encoding="utf-8") if fp.exists() else f"{filename} not found"
        except Exception as e:
            content = f"Failed to open {filename}: {e}"

        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.resize(600, 500)
        layout = QVBoxLayout(dlg)
        txt = QPlainTextEdit()
        txt.setReadOnly(True)
        txt.setFont(QFont("Segoe UI", 10))
        txt.setPlainText(content)
        layout.addWidget(txt)
        dlg.exec()

    def _refresh_all(self):
        self._reload_versions()
        self._refresh_accounts()
        self._refresh_instances()
        self._refresh_play_page()
        self._refresh_java_list()
        self.status_label.setText("Refreshed")

    def closeEvent(self, event):
        try:
            geom = f"{self.width()}x{self.height()}"
            self.settings.set(geom, "meta", "window_geometry")
            self.settings.set(False, "meta", "first_run")
            self.settings.save()
        except Exception:
            pass
        event.accept()


def main():
    def _dbg(msg: str) -> None:
        try:
            log = (
                Path(sys.executable).resolve().parent / "omnilauncher-startup.log"
                if getattr(sys, "frozen", False)
                else Path.cwd() / "omnilauncher-startup.log"
            )
            with log.open("a", encoding="utf-8") as fh:
                fh.write(msg + "\n")
                fh.flush()
        except Exception:
            pass

    _dbg("QApplication()")
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    _dbg("palette")
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#1a1d27"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#e6e8f0"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#1f2333"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#242836"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#242836"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#e6e8f0"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#e6e8f0"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#242836"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#e6e8f0"))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Link, QColor("#e94560"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#e94560"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    _dbg("OmniLauncherApp()")
    window = OmniLauncherApp()
    _dbg("show()")
    window.show()
    _dbg("exec()")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

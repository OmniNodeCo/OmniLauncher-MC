"""Sidebar component - PySide6 modern design."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPainter, QColor, QPen

from typing import Dict, List, Tuple


class SidebarButton(QPushButton):
    """A single sidebar nav button."""

    def __init__(self, key: str, icon: str, label: str, theme: Dict[str, str], parent=None):
        super().__init__(f"  {icon}   {label}", parent)
        self.key = key
        self.theme = theme
        self._active = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(42)
        self.setFont(QFont("Segoe UI", 10))
        self._apply_style()

    def _apply_style(self):
        t = self.theme
        if self._active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {t['sidebar_active']};
                    color: {t['text_primary']};
                    border: none;
                    border-radius: 8px;
                    text-align: left;
                    padding-left: 16px;
                    font-weight: bold;
                    border-left: 3px solid {t['accent']};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {t['text_secondary']};
                    border: none;
                    border-radius: 8px;
                    text-align: left;
                    padding-left: 16px;
                }}
                QPushButton:hover {{
                    background-color: {t['sidebar_hover']};
                    color: {t['text_primary']};
                }}
            """)

    def set_active(self, active: bool):
        self._active = active
        self._apply_style()

    def update_theme(self, theme: Dict[str, str]):
        self.theme = theme
        self._apply_style()


class Sidebar(QFrame):
    """Main sidebar with navigation, logo, and user preview."""

    page_selected = Signal(str)

    def __init__(self, theme: Dict[str, str], parent=None):
        super().__init__(parent)
        self.theme = theme
        self.setFixedWidth(240)
        self.setObjectName("sidebar")

        self.buttons: Dict[str, SidebarButton] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 12)
        layout.setSpacing(0)

        # Logo area
        logo_frame = QFrame()
        logo_frame.setFixedHeight(72)
        logo_layout = QHBoxLayout(logo_frame)
        logo_layout.setContentsMargins(8, 0, 8, 0)

        # Logo icon label
        self._logo_icon = QLabel("O")
        self._logo_icon.setFixedSize(44, 44)
        self._logo_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._logo_icon.setStyleSheet(f"""
            QLabel {{
                background-color: {theme['card_bg']};
                color: {theme['accent']};
                border: 2px solid {theme['accent']};
                border-radius: 22px;
                font-size: 20px;
                font-weight: bold;
            }}
        """)
        logo_layout.addWidget(self._logo_icon)

        logo_text = QVBoxLayout()
        logo_text.setSpacing(0)
        title = QLabel("OmniLauncher")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {theme['text_primary']}; background: transparent;")
        subtitle = QLabel("MC  •  v0.2.0")
        subtitle.setFont(QFont("Segoe UI", 8))
        subtitle.setStyleSheet(f"color: {theme['text_muted']}; background: transparent;")
        logo_text.addWidget(title)
        logo_text.addWidget(subtitle)
        logo_layout.addLayout(logo_text)

        layout.addWidget(logo_frame)

        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {theme['separator']};")
        layout.addWidget(sep)
        layout.addSpacing(8)

        # Navigation items
        nav_items: List[Tuple[str, str, str]] = [
            ("play", "▶", "Play"),
            ("instances", "◫", "Instances"),
            ("accounts", "👤", "Accounts"),
            ("mods", "⬢", "Mods"),
            ("explorer", "📁", "File Explorer"),
            ("servers", "🌐", "Servers"),
            ("friends", "👥", "Friends [Exp]"),
            ("skins", "☻", "Skins"),
            ("settings", "⚙", "Settings"),
            ("console", "▤", "Console"),
            ("about", "ℹ", "About"),
        ]

        for key, icon, label in nav_items:
            btn = SidebarButton(key, icon, label, theme)
            btn.clicked.connect(lambda checked, k=key: self._on_click(k))
            layout.addWidget(btn)
            self.buttons[key] = btn

        # Spacer
        layout.addStretch()

        # User preview card
        self.user_frame = QFrame()
        self.user_frame.setFixedHeight(64)
        self.user_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {theme['card_bg']};
                border-radius: 10px;
            }}
        """)
        user_layout = QHBoxLayout(self.user_frame)
        user_layout.setContentsMargins(12, 8, 12, 8)

        # Avatar
        self._avatar = QLabel("S")
        self._avatar.setFixedSize(36, 36)
        self._avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._avatar.setStyleSheet(f"""
            QLabel {{
                background-color: {theme['accent']};
                color: white;
                border-radius: 18px;
                font-size: 14px;
                font-weight: bold;
            }}
        """)
        user_layout.addWidget(self._avatar)

        user_text = QVBoxLayout()
        user_text.setSpacing(2)
        self.user_name_label = QLabel("Steve")
        self.user_name_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.user_name_label.setStyleSheet(f"color: {theme['text_primary']}; background: transparent;")
        self.user_status_label = QLabel("Offline • Ready")
        self.user_status_label.setFont(QFont("Segoe UI", 8))
        self.user_status_label.setStyleSheet(f"color: {theme['text_muted']}; background: transparent;")
        user_text.addWidget(self.user_name_label)
        user_text.addWidget(self.user_status_label)
        user_layout.addLayout(user_text)

        layout.addWidget(self.user_frame)
        layout.addSpacing(8)

        # Bottom action
        bottom = QFrame()
        bottom_layout = QHBoxLayout(bottom)
        bottom_layout.setContentsMargins(4, 0, 4, 0)
        open_btn = QPushButton("📁  Open Folder")
        open_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {theme['text_muted']};
                border: none;
                text-align: left;
                padding: 4px 8px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                color: {theme['text_primary']};
            }}
        """)
        open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_btn.clicked.connect(lambda: self.page_selected.emit("open_folder"))
        bottom_layout.addWidget(open_btn)
        layout.addWidget(bottom)

        self._apply_bg()

    def _apply_bg(self):
        t = self.theme
        self.setStyleSheet(f"""
            QFrame#sidebar {{
                background-color: {t['sidebar_bg']};
                border-right: 1px solid {t['separator']};
            }}
        """)

    def _on_click(self, key: str):
        self.set_active(key)
        self.page_selected.emit(key)

    def set_active(self, key: str):
        for k, btn in self.buttons.items():
            btn.set_active(k == key)

    def update_user(self, username: str, status: str = "Offline • Ready"):
        self.user_name_label.setText(username)
        self.user_status_label.setText(status)
        if username:
            self._avatar.setText(username[0].upper())

    def update_theme(self, theme: Dict[str, str]):
        self.theme = theme
        self._apply_bg()
        for btn in self.buttons.values():
            btn.update_theme(theme)

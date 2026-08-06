"""Reusable card widgets - PySide6 Instance/Account cards."""

from __future__ import annotations

from datetime import datetime
from typing import Callable, Dict

from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QWidget, QSizePolicy, QMenu,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QAction


ICON_COLORS = {
    "grass": "#5aad5a",
    "crafting_table": "#c49a6c",
    "furnace": "#7a7a7a",
    "diamond": "#5ec4d6",
    "emerald": "#2ecc71",
    "command_block": "#d67d2b",
    "bedrock": "#2b2b2b",
    "tnt": "#ff3b30",
    "chest": "#d3a56a",
    "book": "#c0392b",
    "anvil": "#444444",
    "beacon": "#7dd6ff",
    "bricks": "#b04a3a",
    "dirt": "#866043",
    "stone": "#9b9b9b",
    "gold": "#ffcc00",
    "iron": "#d8d8d8",
    "redstone": "#ff0000",
    "lapis": "#2043c0",
    "nether": "#5a1a1a",
    "end": "#e6e3a8",
}


def _icon_color(name: str) -> str:
    return ICON_COLORS.get(name, "#e94560")


class InstanceCard(QFrame):
    """An instance card with icon, details, and play button."""

    play_clicked = Signal(str)
    select_clicked = Signal(str)
    context_menu = Signal(str, object)  # inst_id, QPoint

    def __init__(self, instance: Dict, theme: Dict[str, str], parent=None):
        super().__init__(parent)
        self.instance = instance
        self.theme = theme
        self.setObjectName("instanceCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context)
        self._build()
        self._apply_style(False)

    def _build(self):
        t = self.theme
        inst = self.instance

        self.setFixedHeight(90)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)

        # Icon
        self._icon_label = QLabel(inst.get("name", "?")[:1].upper())
        self._icon_label.setFixedSize(48, 48)
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        color = _icon_color(inst.get("icon", "grass"))
        fav = inst.get("favorite", False)
        border = f"border: 2px solid #ffcc00;" if fav else "border: none;"
        self._icon_label.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
                {border}
            }}
        """)
        layout.addWidget(self._icon_label)

        # Text
        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)

        name_lbl = QLabel(inst.get("name", "Unnamed"))
        name_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        name_lbl.setStyleSheet(f"color: {t['text_primary']}; background: transparent;")
        text_layout.addWidget(name_lbl)

        ver = inst.get("version") or "No version"
        loader = inst.get("loader", "vanilla")
        group = inst.get("group", "Custom")
        detail_lbl = QLabel(f"{ver} • {loader} • {group}")
        detail_lbl.setFont(QFont("Segoe UI", 9))
        detail_lbl.setStyleSheet(f"color: {t['text_secondary']}; background: transparent;")
        text_layout.addWidget(detail_lbl)

        # Playtime meta
        pt = inst.get("playtime_minutes", 0)
        last = inst.get("last_played", "")
        if last:
            try:
                dt = datetime.fromisoformat(last)
                last_s = dt.strftime("%b %d")
            except Exception:
                last_s = last[:10]
            meta = f"Played {last_s}"
            if pt:
                meta += f" • {pt // 60}h {pt % 60}m"
        else:
            meta = "Never played" if not pt else f"{pt // 60}h {pt % 60}m"
        meta_lbl = QLabel(meta)
        meta_lbl.setFont(QFont("Segoe UI", 8))
        meta_lbl.setStyleSheet(f"color: {t['text_muted']}; background: transparent;")
        text_layout.addWidget(meta_lbl)

        layout.addLayout(text_layout, 1)

        # Play button
        play_btn = QPushButton("▶")
        play_btn.setFixedSize(40, 36)
        play_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t['accent']};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {t['accent_hover']};
            }}
        """)
        play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        play_btn.clicked.connect(lambda: self.play_clicked.emit(self.instance["id"]))
        layout.addWidget(play_btn)

    def _apply_style(self, hovered: bool):
        t = self.theme
        bg = t['card_hover'] if hovered else t['card_bg']
        self.setStyleSheet(f"""
            QFrame#instanceCard {{
                background-color: {bg};
                border: 1px solid {t['card_border']};
                border-radius: 10px;
            }}
        """)

    def enterEvent(self, event):
        self._apply_style(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_style(False)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.select_clicked.emit(self.instance["id"])
        super().mousePressEvent(event)

    def _show_context(self, pos):
        self.context_menu.emit(self.instance["id"], self.mapToGlobal(pos))


class AccountCard(QFrame):
    """An account card with avatar, details, and actions."""

    select_clicked = Signal(int)
    delete_clicked = Signal(str)

    def __init__(self, account: Dict, theme: Dict[str, str], index: int, selected: bool, parent=None):
        super().__init__(parent)
        self.account = account
        self.theme = theme
        self.index = index
        self.selected = selected
        self.setObjectName("accountCard")
        self._build()

    def _build(self):
        t = self.theme
        acc = self.account

        self.setFixedHeight(76)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)

        # Avatar
        skin_color = "#e8c4a8"
        shirt_color = t['accent'] if acc.get("skin_type") != "alex" else t['accent_secondary']
        avatar = QLabel(acc.get("username", "S")[:1].upper())
        avatar.setFixedSize(44, 44)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(f"""
            QLabel {{
                background-color: {shirt_color};
                color: white;
                border-radius: 22px;
                font-size: 16px;
                font-weight: bold;
            }}
        """)
        layout.addWidget(avatar)

        # Text
        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)

        name_lbl = QLabel(acc.get("username", "Steve"))
        name_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        name_lbl.setStyleSheet(f"color: {t['text_primary']}; background: transparent;")
        text_layout.addWidget(name_lbl)

        acc_type = acc.get("type", "offline")
        skin = acc.get("skin_type", "steve")
        uuid_short = acc.get("uuid", "")[:8]
        detail_lbl = QLabel(f"{acc_type} • {skin} • {uuid_short}")
        detail_lbl.setFont(QFont("Segoe UI", 8))
        detail_lbl.setStyleSheet(f"color: {t['text_secondary']}; background: transparent;")
        text_layout.addWidget(detail_lbl)

        layout.addLayout(text_layout, 1)

        # Selected indicator
        if self.selected:
            sel_lbl = QLabel("● SELECTED")
            sel_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            sel_lbl.setStyleSheet(f"color: {t['success']}; background: transparent;")
            layout.addWidget(sel_lbl)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)

        if not self.selected:
            select_btn = QPushButton("Select")
            select_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {t['accent']};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 6px 14px;
                    font-weight: bold;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background-color: {t['accent_hover']};
                }}
            """)
            select_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            select_btn.clicked.connect(lambda: self.select_clicked.emit(self.index))
            btn_layout.addWidget(select_btn)

        del_btn = QPushButton("✕")
        del_btn.setFixedSize(32, 32)
        del_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {t['text_muted']};
                border: none;
                border-radius: 6px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {t['error']};
                color: white;
            }}
        """)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.clicked.connect(lambda: self.delete_clicked.emit(acc.get("uuid", "")))
        btn_layout.addWidget(del_btn)

        layout.addLayout(btn_layout)

        self.setStyleSheet(f"""
            QFrame#accountCard {{
                background-color: {t['card_bg']};
                border: 1px solid {t['card_border']};
                border-radius: 10px;
            }}
        """)


class SettingsRow(QFrame):
    """A settings row with title, description, and control widget."""

    def __init__(self, title: str, description: str, theme: Dict[str, str],
                 control: QWidget | None = None, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.setObjectName("settingsRow")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(16)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)

        title_lbl = QLabel(title)
        title_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {theme['text_primary']}; background: transparent;")
        text_layout.addWidget(title_lbl)

        desc_lbl = QLabel(description)
        desc_lbl.setFont(QFont("Segoe UI", 8))
        desc_lbl.setStyleSheet(f"color: {theme['text_secondary']}; background: transparent;")
        desc_lbl.setWordWrap(True)
        text_layout.addWidget(desc_lbl)

        layout.addLayout(text_layout, 1)

        if control is not None:
            layout.addWidget(control)

        self.setStyleSheet(f"""
            QFrame#settingsRow {{
                background-color: {theme['card_bg']};
                border-radius: 8px;
            }}
        """)

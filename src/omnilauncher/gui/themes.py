"""Theme definitions - modern dark themes with QSS stylesheet generation."""

from __future__ import annotations

from typing import Dict


THEMES: Dict[str, Dict[str, str]] = {
    "dark": {
        "name": "Dark",
        "bg": "#1a1d27",
        "bg_secondary": "#1e212f",
        "sidebar_bg": "#12141d",
        "sidebar_hover": "#1c1f2e",
        "sidebar_active": "#252a40",
        "card_bg": "#242836",
        "card_hover": "#2c3044",
        "card_border": "#2f344b",
        "header_bg": "#1e212f",
        "footer_bg": "#1e212f",
        "input_bg": "#1f2333",
        "input_border": "#2f344b",
        "text_primary": "#e6e8f0",
        "text_secondary": "#8b8fa3",
        "text_muted": "#5c5f77",
        "accent": "#e94560",
        "accent_hover": "#ff5a77",
        "accent_active": "#c7364f",
        "accent_secondary": "#2d8cff",
        "success": "#4ade80",
        "warning": "#fbbf24",
        "error": "#f87171",
        "info": "#60a5fa",
        "progress_bg": "#252a3e",
        "progress_fg": "#e94560",
        "scrollbar_bg": "#1a1d27",
        "scrollbar_thumb": "#2f344b",
        "separator": "#252a3e",
        "play_button_bg": "#e94560",
        "play_button_hover": "#ff5a77",
    },
    "midnight": {
        "name": "Midnight",
        "bg": "#10121a",
        "bg_secondary": "#171926",
        "sidebar_bg": "#0b0c14",
        "sidebar_hover": "#151727",
        "sidebar_active": "#1f2236",
        "card_bg": "#191c2a",
        "card_hover": "#222640",
        "card_border": "#23273d",
        "header_bg": "#171926",
        "footer_bg": "#171926",
        "input_bg": "#1a1d2e",
        "input_border": "#252a40",
        "text_primary": "#e2e4f0",
        "text_secondary": "#7d8199",
        "text_muted": "#4e516b",
        "accent": "#7c5cfc",
        "accent_hover": "#9a7cff",
        "accent_active": "#6a4ae0",
        "accent_secondary": "#00d9ff",
        "success": "#4ade80",
        "warning": "#fbbf24",
        "error": "#f87171",
        "info": "#60a5fa",
        "progress_bg": "#1e2030",
        "progress_fg": "#7c5cfc",
        "scrollbar_bg": "#10121a",
        "scrollbar_thumb": "#252a40",
        "separator": "#1e2030",
        "play_button_bg": "#7c5cfc",
        "play_button_hover": "#9a7cff",
    },
    "light": {
        "name": "Light",
        "bg": "#f5f6fa",
        "bg_secondary": "#ffffff",
        "sidebar_bg": "#ebedf3",
        "sidebar_hover": "#e0e3ed",
        "sidebar_active": "#d6dae8",
        "card_bg": "#ffffff",
        "card_hover": "#f8f9ff",
        "card_border": "#e6e8ee",
        "header_bg": "#ffffff",
        "footer_bg": "#ffffff",
        "input_bg": "#ffffff",
        "input_border": "#d0d4e4",
        "text_primary": "#1a1d27",
        "text_secondary": "#5a5e73",
        "text_muted": "#8b8fa3",
        "accent": "#e94560",
        "accent_hover": "#ff5a77",
        "accent_active": "#c7364f",
        "accent_secondary": "#2d8cff",
        "success": "#16a34a",
        "warning": "#d97706",
        "error": "#dc2626",
        "info": "#2563eb",
        "progress_bg": "#e6e8ee",
        "progress_fg": "#e94560",
        "scrollbar_bg": "#f5f6fa",
        "scrollbar_thumb": "#c5cadb",
        "separator": "#e6e8ee",
        "play_button_bg": "#e94560",
        "play_button_hover": "#ff5a77",
    },
    "amoled": {
        "name": "AMOLED",
        "bg": "#000000",
        "bg_secondary": "#0a0a0a",
        "sidebar_bg": "#000000",
        "sidebar_hover": "#141414",
        "sidebar_active": "#1f1f1f",
        "card_bg": "#121212",
        "card_hover": "#1e1e1e",
        "card_border": "#222222",
        "header_bg": "#0a0a0a",
        "footer_bg": "#0a0a0a",
        "input_bg": "#121212",
        "input_border": "#2a2a2a",
        "text_primary": "#ffffff",
        "text_secondary": "#a0a0a0",
        "text_muted": "#606060",
        "accent": "#ff3b5c",
        "accent_hover": "#ff5a77",
        "accent_active": "#e0354f",
        "accent_secondary": "#00d1ff",
        "success": "#4ade80",
        "warning": "#fbbf24",
        "error": "#f87171",
        "info": "#60a5fa",
        "progress_bg": "#1a1a1a",
        "progress_fg": "#ff3b5c",
        "scrollbar_bg": "#000000",
        "scrollbar_thumb": "#2a2a2a",
        "separator": "#1a1a1a",
        "play_button_bg": "#ff3b5c",
        "play_button_hover": "#ff5a77",
    },
}


def get_theme(name: str = "dark") -> Dict[str, str]:
    return THEMES.get(name, THEMES["dark"])


def generate_stylesheet(theme: Dict[str, str]) -> str:
    """Generate a full QSS stylesheet from a theme dict."""
    t = theme
    return f"""
    /* ===== Global ===== */
    QWidget {{
        background-color: {t['bg']};
        color: {t['text_primary']};
        font-family: 'Segoe UI', 'SF Pro Display', 'Cantarell', sans-serif;
        font-size: 13px;
    }}

    /* ===== ScrollBars ===== */
    QScrollBar:vertical {{
        background: {t['scrollbar_bg']};
        width: 10px;
        margin: 0;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical {{
        background: {t['scrollbar_thumb']};
        min-height: 30px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {t['text_muted']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar:horizontal {{
        background: {t['scrollbar_bg']};
        height: 10px;
        margin: 0;
        border-radius: 5px;
    }}
    QScrollBar::handle:horizontal {{
        background: {t['scrollbar_thumb']};
        min-width: 30px;
        border-radius: 5px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {t['text_muted']};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}

    /* ===== Inputs ===== */
    QLineEdit, QSpinBox, QDoubleSpinBox {{
        background-color: {t['input_bg']};
        color: {t['text_primary']};
        border: 1px solid {t['input_border']};
        border-radius: 6px;
        padding: 6px 10px;
        selection-background-color: {t['accent']};
    }}
    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 1px solid {t['accent']};
    }}

    QComboBox {{
        background-color: {t['input_bg']};
        color: {t['text_primary']};
        border: 1px solid {t['input_border']};
        border-radius: 6px;
        padding: 6px 10px;
        min-height: 20px;
    }}
    QComboBox:hover {{
        border: 1px solid {t['text_muted']};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}
    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid {t['text_secondary']};
        margin-right: 8px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {t['card_bg']};
        color: {t['text_primary']};
        border: 1px solid {t['card_border']};
        selection-background-color: {t['sidebar_active']};
        selection-color: {t['text_primary']};
        outline: none;
    }}

    /* ===== Checkbox ===== */
    QCheckBox {{
        color: {t['text_secondary']};
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {t['input_border']};
        border-radius: 4px;
        background: {t['input_bg']};
    }}
    QCheckBox::indicator:checked {{
        background: {t['accent']};
        border: 2px solid {t['accent']};
    }}
    QCheckBox::indicator:hover {{
        border: 2px solid {t['accent']};
    }}

    /* ===== Buttons ===== */
    QPushButton {{
        background-color: {t['card_bg']};
        color: {t['text_secondary']};
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: {t['card_hover']};
        color: {t['text_primary']};
    }}
    QPushButton:pressed {{
        background-color: {t['sidebar_active']};
    }}
    QPushButton:disabled {{
        color: {t['text_muted']};
        background-color: {t['bg_secondary']};
    }}

    /* ===== Accent Button ===== */
    QPushButton[accent="true"] {{
        background-color: {t['accent']};
        color: white;
        font-weight: bold;
    }}
    QPushButton[accent="true"]:hover {{
        background-color: {t['accent_hover']};
    }}
    QPushButton[accent="true"]:pressed {{
        background-color: {t['accent_active']};
    }}

    /* ===== Play Button ===== */
    QPushButton[play="true"] {{
        background-color: {t['play_button_bg']};
        color: white;
        font-size: 15px;
        font-weight: bold;
        padding: 12px 32px;
        border-radius: 8px;
    }}
    QPushButton[play="true"]:hover {{
        background-color: {t['play_button_hover']};
    }}

    /* ===== Slider ===== */
    QSlider::groove:horizontal {{
        height: 6px;
        background: {t['progress_bg']};
        border-radius: 3px;
    }}
    QSlider::handle:horizontal {{
        background: {t['accent']};
        width: 16px;
        height: 16px;
        margin: -5px 0;
        border-radius: 8px;
    }}
    QSlider::handle:horizontal:hover {{
        background: {t['accent_hover']};
    }}
    QSlider::sub-page:horizontal {{
        background: {t['accent']};
        border-radius: 3px;
    }}

    /* ===== Progress Bar ===== */
    QProgressBar {{
        background: {t['progress_bg']};
        border: none;
        border-radius: 4px;
        height: 8px;
        text-align: center;
        color: transparent;
    }}
    QProgressBar::chunk {{
        background: {t['progress_fg']};
        border-radius: 4px;
    }}

    /* ===== TextEdit / PlainTextEdit ===== */
    QTextEdit, QPlainTextEdit {{
        background-color: {t['input_bg']};
        color: {t['text_primary']};
        border: 1px solid {t['input_border']};
        border-radius: 6px;
        padding: 4px;
        selection-background-color: {t['accent']};
    }}

    /* ===== ListWidget ===== */
    QListWidget {{
        background-color: {t['input_bg']};
        color: {t['text_primary']};
        border: 1px solid {t['input_border']};
        border-radius: 6px;
        outline: none;
    }}
    QListWidget::item {{
        padding: 6px 8px;
        border-radius: 4px;
    }}
    QListWidget::item:selected {{
        background-color: {t['sidebar_active']};
        color: {t['text_primary']};
    }}
    QListWidget::item:hover {{
        background-color: {t['card_hover']};
    }}

    /* ===== TabWidget ===== */
    QTabWidget::pane {{
        border: none;
        background: {t['bg']};
    }}
    QTabBar::tab {{
        background: {t['card_bg']};
        color: {t['text_secondary']};
        padding: 8px 16px;
        border: none;
        border-bottom: 2px solid transparent;
    }}
    QTabBar::tab:selected {{
        background: {t['sidebar_active']};
        color: {t['text_primary']};
        border-bottom: 2px solid {t['accent']};
    }}
    QTabBar::tab:hover {{
        background: {t['card_hover']};
        color: {t['text_primary']};
    }}

    /* ===== Menu ===== */
    QMenu {{
        background-color: {t['card_bg']};
        color: {t['text_primary']};
        border: 1px solid {t['card_border']};
        border-radius: 8px;
        padding: 4px;
    }}
    QMenu::item {{
        padding: 8px 24px;
        border-radius: 4px;
    }}
    QMenu::item:selected {{
        background-color: {t['sidebar_active']};
    }}
    QMenu::separator {{
        height: 1px;
        background: {t['separator']};
        margin: 4px 8px;
    }}

    /* ===== ToolTip ===== */
    QToolTip {{
        background-color: {t['card_bg']};
        color: {t['text_primary']};
        border: 1px solid {t['card_border']};
        border-radius: 4px;
        padding: 4px 8px;
    }}

    /* ===== Splitter ===== */
    QSplitter::handle {{
        background: {t['separator']};
    }}
    QSplitter::handle:horizontal {{
        width: 2px;
    }}
    QSplitter::handle:vertical {{
        height: 2px;
    }}

    /* ===== GroupBox ===== */
    QGroupBox {{
        border: 1px solid {t['card_border']};
        border-radius: 8px;
        margin-top: 12px;
        padding-top: 16px;
        font-weight: bold;
        color: {t['text_primary']};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
    }}

    /* ===== Dialog ===== */
    QDialog {{
        background-color: {t['bg']};
    }}
"""


# Common fonts (compatible with PySide6 QFont)
FONTS = {
    "title": ("Segoe UI", 16),
    "title_large": ("Segoe UI", 20),
    "heading": ("Segoe UI", 12),
    "body": ("Segoe UI", 10),
    "body_bold": ("Segoe UI", 10),
    "small": ("Segoe UI", 9),
    "small_bold": ("Segoe UI", 9),
    "mono": ("Consolas", 10),
    "mono_small": ("Consolas", 9),
    "icon": ("Segoe UI", 14),
}

# Accent palettes for color picker
ACCENT_PALETTE = [
    "#e94560",
    "#ff3b5c",
    "#ff4655",
    "#00d1ff",
    "#2d8cff",
    "#7c5cfc",
    "#9c27b0",
    "#4caf50",
    "#8bc34a",
    "#ffc107",
    "#ff9800",
    "#ff5722",
    "#00bcd4",
    "#009688",
]

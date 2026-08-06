"""Dialogs and popups - PySide6."""

from __future__ import annotations

from typing import Callable, Dict, List

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame, QFileDialog, QListWidget, QListWidgetItem,
    QSizePolicy,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


class CrashReportDialog(QDialog):
    """Shows crash analysis results."""

    def __init__(self, theme: Dict[str, str], log_text: str, findings: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crash Report • OmniLauncher")
        self.setMinimumSize(640, 520)
        self._log = log_text
        self._findings = findings
        t = theme

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Title
        title = QLabel("💥  Minecraft Crashed")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {t['error']};")
        layout.addWidget(title)

        sub = QLabel("Launcher analyzed the log and tried to explain what went wrong:")
        sub.setFont(QFont("Segoe UI", 9))
        sub.setStyleSheet(f"color: {t['text_secondary']};")
        layout.addWidget(sub)

        # Findings
        findings_frame = QFrame()
        findings_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {t['card_bg']};
                border: 1px solid {t['card_border']};
                border-radius: 8px;
            }}
        """)
        findings_layout = QVBoxLayout(findings_frame)
        findings_layout.setContentsMargins(12, 12, 12, 12)
        findings_layout.setSpacing(8)

        if not findings:
            lbl = QLabel("No specific cause found. Please check full log.")
            lbl.setStyleSheet(f"color: {t['text_secondary']}; background: transparent;")
            findings_layout.addWidget(lbl)
        else:
            for f in findings:
                sev = f.get("severity", "error")
                color = t['error'] if sev in ("error", "critical") else t['warning'] if sev == "warn" else t['text_primary']
                row = QVBoxLayout()
                row.setSpacing(4)

                title_lbl = QLabel(f"[{sev.upper()}] {f['title']}")
                title_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                title_lbl.setStyleSheet(f"color: {color}; background: transparent;")
                row.addWidget(title_lbl)

                desc_lbl = QLabel(f["description"])
                desc_lbl.setFont(QFont("Segoe UI", 9))
                desc_lbl.setStyleSheet(f"color: {t['text_secondary']}; background: transparent;")
                desc_lbl.setWordWrap(True)
                row.addWidget(desc_lbl)

                fix_lbl = QLabel(f"Fix: {f['fix']}")
                fix_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                fix_lbl.setStyleSheet(f"color: {t['text_primary']}; background: transparent;")
                fix_lbl.setWordWrap(True)
                row.addWidget(fix_lbl)

                findings_layout.addLayout(row)

        layout.addWidget(findings_frame)

        # Log snippet
        log_title = QLabel("Log Snippet")
        log_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        log_title.setStyleSheet(f"color: {t['text_primary']};")
        layout.addWidget(log_title)

        log_text_edit = QTextEdit()
        log_text_edit.setReadOnly(True)
        log_text_edit.setFont(QFont("Consolas", 9))
        log_text_edit.setPlainText(log_text[-4000:] if len(log_text) > 4000 else log_text)
        log_text_edit.setMaximumHeight(200)
        layout.addWidget(log_text_edit)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        copy_btn = QPushButton("Copy Report")
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t['card_bg']};
                color: {t['text_primary']};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{ background-color: {t['card_hover']}; }}
        """)
        copy_btn.clicked.connect(self._copy)
        btn_layout.addWidget(copy_btn)

        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t['accent']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {t['accent_hover']}; }}
        """)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _copy(self):
        report = "\n".join(
            [f"{f['title']}: {f['description']} Fix: {f['fix']}" for f in self._findings]
        ) + "\n\nLog:\n" + self._log[-2000:]
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(report)


class ConfirmDialog(QDialog):
    """Simple confirm/cancel dialog."""

    def __init__(self, theme: Dict[str, str], title: str, message: str,
                 on_confirm: Callable, danger: bool = False, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(420, 180)
        self._on_confirm = on_confirm
        t = theme

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(8)

        ttl = QLabel(title)
        ttl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        ttl.setStyleSheet(f"color: {t['error'] if danger else t['text_primary']};")
        layout.addWidget(ttl)

        msg = QLabel(message)
        msg.setFont(QFont("Segoe UI", 9))
        msg.setStyleSheet(f"color: {t['text_secondary']};")
        msg.setWordWrap(True)
        layout.addWidget(msg)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t['card_bg']};
                color: {t['text_secondary']};
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{ background-color: {t['card_hover']}; }}
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        confirm_btn = QPushButton("Confirm")
        confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t['error'] if danger else t['accent']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {'#e0354f' if danger else t['accent_hover']};
            }}
        """)
        confirm_btn.clicked.connect(self._do_confirm)
        btn_layout.addWidget(confirm_btn)

        layout.addLayout(btn_layout)

    def _do_confirm(self):
        self._on_confirm()
        self.accept()


class FileExplorerDialog(QDialog):
    """Built-in file explorer dialog."""

    def __init__(self, theme: Dict[str, str], mc_dir: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"File Explorer • {mc_dir}")
        self.setMinimumSize(780, 520)
        self.mc_dir = mc_dir
        self.current_path = mc_dir
        self.theme = theme
        t = theme

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Left bookmarks
        left = QFrame()
        left.setFixedWidth(180)
        left.setStyleSheet(f"background-color: {t['sidebar_bg']};")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(12, 12, 12, 12)

        bm_title = QLabel("Bookmarks")
        bm_title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        bm_title.setStyleSheet(f"color: {t['text_primary']}; background: transparent;")
        left_layout.addWidget(bm_title)

        from omnilauncher.services.file_explorer import get_bookmarks
        for bm in get_bookmarks(mc_dir):
            btn = QPushButton(f"{bm['icon']}  {bm['name']}")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {t['text_secondary'] if bm['exists'] else t['text_muted']};
                    border: none;
                    text-align: left;
                    padding: 6px 8px;
                    border-radius: 6px;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background-color: {t['sidebar_hover']};
                    color: {t['text_primary']};
                }}
            """)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, p=bm['path']: self._navigate(p))
            left_layout.addWidget(btn)

        left_layout.addStretch()
        layout.addWidget(left)

        # Right content
        right = QFrame()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(8)

        # Toolbar
        toolbar = QFrame()
        toolbar.setFixedHeight(40)
        toolbar.setStyleSheet(f"background-color: {t['header_bg']}; border-radius: 6px;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(12, 0, 12, 0)

        self.path_label = QLabel(mc_dir)
        self.path_label.setFont(QFont("Segoe UI", 9))
        self.path_label.setStyleSheet(f"color: {t['text_secondary']}; background: transparent;")
        toolbar_layout.addWidget(self.path_label, 1)

        up_btn = QPushButton("↑ Up")
        up_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t['card_bg']};
                color: {t['text_secondary']};
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 11px;
            }}
            QPushButton:hover {{ color: {t['text_primary']}; }}
        """)
        up_btn.clicked.connect(self._go_up)
        toolbar_layout.addWidget(up_btn)

        open_btn = QPushButton("Open in OS")
        open_btn.setStyleSheet(up_btn.styleSheet())
        open_btn.clicked.connect(self._open_os)
        toolbar_layout.addWidget(open_btn)

        right_layout.addWidget(toolbar)

        # File list
        self.file_list = QListWidget()
        self.file_list.setFont(QFont("Segoe UI", 10))
        self.file_list.itemDoubleClicked.connect(self._on_double_click)
        right_layout.addWidget(self.file_list, 1)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {t['accent']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {t['accent_hover']}; }}
        """)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        right_layout.addLayout(btn_layout)

        layout.addWidget(right, 1)

        self._items = []
        self._refresh()

    def _navigate(self, path: str):
        self.current_path = path
        self._refresh()

    def _refresh(self):
        from omnilauncher.services.file_explorer import list_files
        self.path_label.setText(self.current_path)
        self.file_list.clear()
        self._items = list_files(self.current_path)
        for it in self._items:
            prefix = "📁" if it["is_dir"] else "📄"
            text = f"{prefix}  {it['name']}/" if it["is_dir"] else f"{prefix}  {it['name']}  ({it['size']} bytes)"
            self.file_list.addItem(text)

    def _on_double_click(self, item: QListWidgetItem):
        idx = self.file_list.row(item)
        if 0 <= idx < len(self._items):
            it = self._items[idx]
            if it["is_dir"]:
                self.current_path = it["path"]
                self._refresh()

    def _go_up(self):
        from pathlib import Path
        parent = str(Path(self.current_path).parent)
        if parent and len(parent) >= len(self.mc_dir) - 10:
            self.current_path = parent
        else:
            self.current_path = self.mc_dir
        self._refresh()

    def _open_os(self):
        import os, platform, subprocess
        try:
            if platform.system() == "Windows":
                os.startfile(self.current_path)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", self.current_path])
            else:
                subprocess.Popen(["xdg-open", self.current_path])
        except Exception:
            pass

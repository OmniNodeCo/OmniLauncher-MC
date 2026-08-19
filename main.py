"""OmniLauncher-MC entry point."""

from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path


def _frozen_base() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent


def _configure_qt_plugins() -> None:
    """Point Qt at bundled plugins inside a PyInstaller build."""
    if not getattr(sys, "frozen", False):
        return
    base = _frozen_base()
    candidates = [
        base / "PySide6" / "plugins",
        base / "PySide6" / "Qt6" / "plugins",
        base / "PySide6" / "qt-plugins",
        base / "qt6_plugins",
        base / "plugins",
    ]
    for plugins in candidates:
        platforms = plugins / "platforms"
        if platforms.is_dir():
            os.environ.setdefault("QT_PLUGIN_PATH", str(plugins))
            os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", str(platforms))
            break


def _crash_log_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "omnilauncher-crash.log"
    return Path.cwd() / "omnilauncher-crash.log"


def _show_error(title: str, message: str) -> None:
    try:
        if sys.platform == "win32":
            import ctypes

            ctypes.windll.user32.MessageBoxW(0, message[:2000], title, 0x10)
            return
    except Exception:
        pass
    try:
        sys.stderr.write(f"{title}: {message}\n")
    except Exception:
        pass


def main() -> None:
    _configure_qt_plugins()
    try:
        from omnilauncher.gui.app import main as gui_main

        gui_main()
    except Exception:
        text = traceback.format_exc()
        try:
            _crash_log_path().write_text(text, encoding="utf-8")
        except Exception:
            pass
        _show_error(
            "OmniLauncher-MC failed to start",
            f"{text}\n\nA crash log was written next to the executable "
            f"({_crash_log_path().name}).",
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()

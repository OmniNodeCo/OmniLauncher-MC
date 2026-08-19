"""PyInstaller runtime hook: locate Qt platform plugins before any import."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _set_qt_plugin_env() -> None:
    if not getattr(sys, "frozen", False):
        return
    roots = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        roots.append(Path(meipass))
    roots.append(Path(sys.executable).resolve().parent)
    plugin_names = ("qwindows.dll", "libqxcb.so", "libqcocoa.dylib")
    for root in roots:
        if not root.exists():
            continue
        for dirpath, _dirnames, filenames in os.walk(root):
            for name in plugin_names:
                if name in filenames:
                    platforms = Path(dirpath)
                    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(platforms)
                    os.environ["QT_PLUGIN_PATH"] = str(platforms.parent)
                    return


_set_qt_plugin_env()

"""PyInstaller runtime hook: locate Qt platform plugins before any import."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _set_qt_plugin_env() -> None:
    if not getattr(sys, "frozen", False):
        return
    exe_dir = Path(sys.executable).resolve().parent
    meipass = Path(getattr(sys, "_MEIPASS", exe_dir))
    # Prefer plugins that live next to the Qt DLLs inside _internal / _MEIPASS.
    roots = [meipass, exe_dir / "_internal"]
    plugin_names = ("qwindows.dll", "libqxcb.so", "libqcocoa.dylib")
    for root in roots:
        if not root.exists():
            continue
        for dirpath, _dirnames, filenames in os.walk(root):
            # Skip the stray copy we used to put next to the exe
            if Path(dirpath).parent == exe_dir:
                continue
            for name in plugin_names:
                if name in filenames:
                    platforms = Path(dirpath)
                    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(platforms)
                    os.environ["QT_PLUGIN_PATH"] = str(platforms.parent)
                    return


_set_qt_plugin_env()

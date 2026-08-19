"""OmniLauncher-MC entry point."""

from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path


def _app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _frozen_base() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", _app_dir()))
    return Path(__file__).resolve().parent


def _log_path() -> Path:
    return _app_dir() / "omnilauncher-startup.log"


def _log(message: str) -> None:
    try:
        path = _log_path()
        with path.open("a", encoding="utf-8") as fh:
            fh.write(message.rstrip() + "\n")
    except Exception:
        try:
            fallback = Path.home() / "OmniLauncher-MC-startup.log"
            with fallback.open("a", encoding="utf-8") as fh:
                fh.write(message.rstrip() + "\n")
        except Exception:
            pass


def _find_platforms_dir() -> Path | None:
    plugin_names = ("qwindows.dll", "libqxcb.so", "libqcocoa.dylib")
    roots = [_app_dir(), _app_dir() / "platforms", _frozen_base()]
    internal = _app_dir() / "_internal"
    if internal.exists():
        roots.append(internal)
    seen: set[str] = set()
    for root in roots:
        if not root.exists():
            continue
        key = str(root.resolve())
        if key in seen:
            continue
        seen.add(key)
        # Fast path: already next to the exe
        direct = root / "platforms" if root.name != "platforms" else root
        for name in plugin_names:
            if (direct / name).is_file():
                return direct
        for dirpath, _dirnames, filenames in os.walk(root):
            for name in plugin_names:
                if name in filenames:
                    return Path(dirpath)
    return None


def _configure_qt_plugins() -> None:
    platforms = _find_platforms_dir()
    if platforms is None:
        _log("Qt platforms directory not found")
        return
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(platforms)
    os.environ["QT_PLUGIN_PATH"] = str(platforms.parent)
    _log(f"QT_QPA_PLATFORM_PLUGIN_PATH={platforms}")


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
    try:
        _log_path().write_text("OmniLauncher-MC starting\n", encoding="utf-8")
    except Exception:
        pass
    _log(f"frozen={getattr(sys, 'frozen', False)}")
    _log(f"executable={sys.executable}")
    _log(f"meipass={getattr(sys, '_MEIPASS', '')}")
    _configure_qt_plugins()
    try:
        _log("importing omnilauncher.gui.app")
        from omnilauncher.gui.app import main as gui_main

        _log("starting GUI")
        gui_main()
    except Exception:
        text = traceback.format_exc()
        _log(text)
        _show_error(
            "OmniLauncher-MC failed to start",
            f"{text}\n\nSee {_log_path()}",
        )
        raise SystemExit(1)


if __name__ == "__main__":
    main()

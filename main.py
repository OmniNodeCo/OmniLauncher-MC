"""OmniLauncher-MC entry point."""

from __future__ import annotations

import faulthandler
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
    line = message.rstrip() + "\n"
    for path in (_log_path(), Path.home() / "OmniLauncher-MC-startup.log"):
        try:
            with path.open("a", encoding="utf-8") as fh:
                fh.write(line)
                fh.flush()
            return
        except Exception:
            continue


def _prepare_dll_search() -> None:
    """Windows 3.8+ will not load Qt DLLs from _internal unless we add it."""
    if sys.platform != "win32" or not getattr(sys, "frozen", False):
        return
    dirs = []
    internal = _app_dir() / "_internal"
    if internal.is_dir():
        dirs.append(internal)
    meipass = _frozen_base()
    if meipass.is_dir() and meipass not in dirs:
        dirs.append(meipass)
    for folder in dirs:
        try:
            os.add_dll_directory(str(folder))
        except (OSError, AttributeError):
            pass
        os.environ["PATH"] = str(folder) + os.pathsep + os.environ.get("PATH", "")
        _log(f"dll search: {folder}")
        # PySide6 often keeps Qt6Core.dll in a nested folder
        for core in folder.rglob("Qt6Core.dll"):
            parent = str(core.parent)
            try:
                os.add_dll_directory(parent)
            except (OSError, AttributeError):
                pass
            os.environ["PATH"] = parent + os.pathsep + os.environ.get("PATH", "")
            _log(f"dll search: {parent}")
            break


def _find_platforms_dir() -> Path | None:
    plugin_names = ("qwindows.dll", "libqxcb.so", "libqcocoa.dylib")
    exe_dir = _app_dir()
    roots = [_frozen_base(), exe_dir / "_internal"]
    seen: set[str] = set()
    for root in roots:
        if not root.exists():
            continue
        key = str(root.resolve())
        if key in seen:
            continue
        seen.add(key)
        for dirpath, _dirnames, filenames in os.walk(root):
            # Do not use a platforms folder sitting beside the exe — those
            # copies of qwindows.dll cannot load Qt6Gui from _internal.
            if Path(dirpath).parent == exe_dir:
                continue
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
    try:
        faulthandler.enable(open(_log_path(), "a", encoding="utf-8"))
    except Exception:
        try:
            faulthandler.enable()
        except Exception:
            pass
    _log(f"frozen={getattr(sys, 'frozen', False)}")
    _log(f"executable={sys.executable}")
    _log(f"meipass={getattr(sys, '_MEIPASS', '')}")
    _prepare_dll_search()
    _configure_qt_plugins()
    try:
        _log("importing omnilauncher.gui.app")
        from omnilauncher.gui.app import main as gui_main

        _log("starting GUI")
        gui_main()
        _log("GUI exited")
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

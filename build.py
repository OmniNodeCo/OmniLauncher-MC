"""Build OmniLauncher-MC standalone executable.

Usage:
    uv run --with pyinstaller python build.py
    uv sync --extra build && python build.py
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path


def _clean_dir(path: str) -> None:
    """Remove a directory tree, handling read-only files on Windows."""
    if not os.path.exists(path):
        return
    for root, dirs, files in os.walk(path):
        for name in files + dirs:
            entry = os.path.join(root, name)
            try:
                os.chmod(entry, stat.S_IWRITE)
            except OSError:
                pass
    shutil.rmtree(path, ignore_errors=True)
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)


def build() -> None:
    sep = ";" if sys.platform == "win32" else ":"

    data_files = ["Changelog.txt", "LICENSE.txt", "TERMS.txt"]
    add_data = [f"--add-data={f}{sep}." for f in data_files if os.path.exists(f)]

    # onedir + console: Qt can find plugins, and startup errors are visible.
    console_flag = "--console"

    _clean_dir("dist")
    _clean_dir("build")

    spec_file = "OmniLauncher-MC.spec"
    if os.path.exists(spec_file):
        os.remove(spec_file)

    hidden = [
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
        "PySide6.QtNetwork",
        "shiboken6",
        "omnilauncher",
        "omnilauncher.gui",
        "omnilauncher.gui.app",
        "omnilauncher.gui.themes",
        "omnilauncher.gui.components",
        "omnilauncher.gui.components.sidebar",
        "omnilauncher.gui.components.cards",
        "omnilauncher.gui.components.dialogs",
        "omnilauncher.config",
        "omnilauncher.config.settings",
        "omnilauncher.services",
        "omnilauncher.services.launcher",
        "omnilauncher.services.versions",
        "omnilauncher.services.accounts",
        "omnilauncher.services.instances",
        "omnilauncher.services.java",
        "omnilauncher.services.file_explorer",
        "omnilauncher.services.crash_analyzer",
        "omnilauncher.services.error_handler",
        "minecraft_launcher_lib",
        "minecraft_launcher_lib.utils",
        "minecraft_launcher_lib.command",
        "minecraft_launcher_lib.install",
    ]

    runtime_hook = "hook-qt-plugins.py"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "main.py",
        "--onedir",
        "--name",
        "OmniLauncher-MC",
        console_flag,
        "--noconfirm",
        "--clean",
        "--paths",
        "src",
        "--collect-all",
        "PySide6",
        "--collect-all",
        "shiboken6",
        "--collect-submodules",
        "minecraft_launcher_lib",
        "--runtime-hook",
        runtime_hook,
        *[item for name in hidden for item in ("--hidden-import", name)],
        *add_data,
    ]

    subprocess.check_call(cmd)

    dist_dir = Path("dist") / "OmniLauncher-MC"
    exe_name = "OmniLauncher-MC.exe" if sys.platform == "win32" else "OmniLauncher-MC"
    built = dist_dir / exe_name
    if built.exists():
        print(f"Built {built}")


if __name__ == "__main__":
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        sys.exit(
            "PyInstaller not found. Install it with:\n"
            "  uv sync --extra build\n"
            "  uv pip install pyinstaller\n"
            "  uv run --with pyinstaller python build.py"
        )
    build()

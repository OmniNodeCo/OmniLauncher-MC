"""Build OmniLauncher-MC standalone executable.

Usage:
    uv run --with pyinstaller python build.py
    uv sync --group build && python build.py
"""

import os
import shutil
import stat
import subprocess
import sys


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

    # Windowed on Windows so a console does not flash; crashes still show a MessageBox.
    console_flag = "--noconsole" if sys.platform == "win32" else "--console"

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

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "main.py",
        "--onefile",
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
        *[item for name in hidden for item in ("--hidden-import", name)],
        *add_data,
    ]

    subprocess.check_call(cmd)


if __name__ == "__main__":
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        sys.exit(
            "PyInstaller not found. Install it with:\n"
            "  uv sync --group build\n"
            "  uv pip install pyinstaller\n"
            "  uv run --with pyinstaller python build.py"
        )
    build()

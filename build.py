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
    # Retry if rmtree failed (e.g. file still locked)
    if os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)


def build() -> None:
    sep = ";" if sys.platform == "win32" else ":"

    data_files = ["Changelog.txt", "LICENSE.txt", "TERMS.txt"]
    add_data = [f"--add-data={f}{sep}." for f in data_files]

    console_flag = "--noconsole" if sys.platform == "win32" else "--console"

    _clean_dir("dist")
    _clean_dir("build")

    # Remove stale .spec file to force regeneration
    spec_file = "OmniLauncher-MC.spec"
    if os.path.exists(spec_file):
        os.remove(spec_file)

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
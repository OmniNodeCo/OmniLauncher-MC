"""Build OmniLauncher-MC standalone executable.

Usage:
    uv run --with pyinstaller python build.py
    uv sync --group build && python build.py
"""

import subprocess
import sys


def build() -> None:
    sep = ";" if sys.platform == "win32" else ":"

    data_files = ["Changelog.txt", "LICENSE.txt", "TERMS.txt"]
    add_data = [f"--add-data={f}{sep}." for f in data_files]

    console_flag = "--noconsole" if sys.platform == "win32" else "--console"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "main.py",
        "--onefile",
        "--name",
        "OmniLauncher-MC",
        console_flag,
        "--clean",
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

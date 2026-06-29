"""Utility functions for OmniLauncher-MC."""

import os
import sys
import platform
import json
from pathlib import Path


def get_app_dir():
    """Get the application data directory. Kept for backward compat."""
    system = platform.system()
    if system == "Windows":
        base = Path(os.getenv("APPDATA", str(Path.home())))
    elif system == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.getenv("XDG_DATA_HOME", str(Path.home() / ".local" / "share")))

    app_dir = base / "OmniLauncher-MC"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_minecraft_dir():
    """Get the default Minecraft directory."""
    system = platform.system()
    if system == "Windows":
        return Path(os.getenv("APPDATA", str(Path.home()))) / ".minecraft"
    elif system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "minecraft"
    else:
        return Path.home() / ".minecraft"


def get_asset_path(filename):
    """Get the path to a bundled asset file."""
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).parent.parent

    return str(base / "assets" / filename)


def load_json(filepath):
    """Load JSON from file, return empty dict on failure."""
    try:
        with open(str(filepath), "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def save_json(filepath, data):
    """Save dict as JSON to file."""
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(str(filepath), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def format_bytes(size):
    """Format byte count to human readable string."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(size) < 1024.0:
            return "%.1f %s" % (size, unit)
        size /= 1024.0
    return "%.1f PB" % size


def get_java_executable():
    """Try to find a Java executable."""
    system = platform.system()

    java_home = os.getenv("JAVA_HOME")
    if java_home:
        if system == "Windows":
            java_path = Path(java_home) / "bin" / "javaw.exe"
        else:
            java_path = Path(java_home) / "bin" / "java"
        if java_path.exists():
            return str(java_path)

    if system == "Windows":
        return "javaw.exe"
    return "java"
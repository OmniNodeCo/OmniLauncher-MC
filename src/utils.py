"""Utility functions for OmniLauncher-MC."""

import os
import sys
import platform
import json
from pathlib import Path


def get_app_dir() -> Path:
    """Get the application data directory."""
    system = platform.system()
    if system == "Windows":
        base = Path(os.getenv("APPDATA", Path.home()))
    elif system == "Darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".local" / "share"

    app_dir = base / "OmniLauncher-MC"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_minecraft_dir() -> Path:
    """Get the default Minecraft directory."""
    system = platform.system()
    if system == "Windows":
        return Path(os.getenv("APPDATA", Path.home())) / ".minecraft"
    elif system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "minecraft"
    else:
        return Path.home() / ".minecraft"


def get_asset_path(filename: str) -> str:
    """Get the path to a bundled asset file."""
    if getattr(sys, 'frozen', False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).parent.parent

    return str(base / "assets" / filename)


def load_json(filepath: Path) -> dict:
    """Load JSON from file, return empty dict on failure."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_json(filepath: Path, data: dict) -> None:
    """Save dict as JSON to file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def format_bytes(size: int) -> str:
    """Format byte count to human readable string."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(size) < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def get_java_executable() -> str:
    """Try to find a Java executable."""
    system = platform.system()

    # Check JAVA_HOME first
    java_home = os.getenv("JAVA_HOME")
    if java_home:
        if system == "Windows":
            java_path = Path(java_home) / "bin" / "javaw.exe"
        else:
            java_path = Path(java_home) / "bin" / "java"
        if java_path.exists():
            return str(java_path)

    # Fallback
    if system == "Windows":
        return "javaw.exe"
    return "java"
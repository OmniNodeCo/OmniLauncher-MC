"""Settings management for OmniLauncher-MC."""

import sys
import os

_here = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, "frozen", False):
    _here = sys._MEIPASS
if _here not in sys.path:
    sys.path.insert(0, _here)

from pathlib import Path
from utils import get_app_dir, get_minecraft_dir, load_json, save_json


DEFAULT_SETTINGS = {
    "minecraft_dir": str(get_minecraft_dir()),
    "java_path": "",
    "java_args": "-Xmx2G -Xms512M",
    "ram_min": 512,
    "ram_max": 2048,
    "theme": "dark",
    "accent_color": "#6C3BF5",
    "close_on_launch": False,
    "show_snapshots": False,
    "auto_update": True,
    "window_width": 1100,
    "window_height": 700,
}


class SettingsManager:
    """Manages application settings with persistence."""

    def __init__(self):
        self.filepath = get_app_dir() / "settings.json"
        self.settings = dict(DEFAULT_SETTINGS)
        self.load()

    def load(self) -> None:
        """Load settings from file."""
        saved = load_json(self.filepath)
        self.settings.update(saved)

    def save(self) -> None:
        """Save current settings to file."""
        save_json(self.filepath, self.settings)

    def get(self, key: str, default=None):
        """Get a setting value."""
        return self.settings.get(key, default)

    def set(self, key: str, value) -> None:
        """Set a setting value and save."""
        self.settings[key] = value
        self.save()

    def reset(self) -> None:
        """Reset to default settings."""
        self.settings = dict(DEFAULT_SETTINGS)
        self.save()
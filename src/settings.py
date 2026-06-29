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
    "check_updates_on_start": True,
    "window_width": 1100,
    "window_height": 700,
}


class SettingsManager:
    """Manages application settings with persistence."""

    def __init__(self, appdata_mgr=None):
        if appdata_mgr:
            self.filepath = appdata_mgr.get_file("settings")
        else:
            self.filepath = get_app_dir() / "settings.json"
        self.settings = dict(DEFAULT_SETTINGS)
        self.load()

    def load(self):
        saved = load_json(self.filepath)
        self.settings.update(saved)

    def save(self):
        save_json(self.filepath, self.settings)

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self.save()

    def reset(self):
        self.settings = dict(DEFAULT_SETTINGS)
        self.save()
"""Profile management for OmniLauncher-MC."""

import sys
import os

_here = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, "frozen", False):
    _here = sys._MEIPASS
if _here not in sys.path:
    sys.path.insert(0, _here)

import uuid
from datetime import datetime
from pathlib import Path
from utils import get_app_dir, load_json, save_json


class Profile:
    """Represents a game profile / instance."""

    def __init__(self, name, version, profile_id=None,
                 java_args="", game_dir="",
                 created=None, last_played=None,
                 loader="vanilla", loader_version=""):
        self.id = profile_id or str(uuid.uuid4())[:8]
        self.name = name
        self.version = version
        self.java_args = java_args
        self.game_dir = game_dir
        self.loader = loader
        self.loader_version = loader_version
        self.created = created or datetime.now().isoformat()
        self.last_played = last_played or ""

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "java_args": self.java_args,
            "game_dir": self.game_dir,
            "loader": self.loader,
            "loader_version": self.loader_version,
            "created": self.created,
            "last_played": self.last_played,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data.get("name", "Unnamed"),
            version=data.get("version", ""),
            profile_id=data.get("id"),
            java_args=data.get("java_args", ""),
            game_dir=data.get("game_dir", ""),
            created=data.get("created"),
            last_played=data.get("last_played"),
            loader=data.get("loader", "vanilla"),
            loader_version=data.get("loader_version", ""),
        )


class ProfileManager:
    """Manages game profiles."""

    def __init__(self, appdata_mgr=None):
        if appdata_mgr:
            self.filepath = appdata_mgr.get_file("profiles")
        else:
            self.filepath = get_app_dir() / "profiles.json"
        self.profiles = []
        self.active_id = ""
        self.load()

    def load(self):
        data = load_json(self.filepath)
        self.profiles = [
            Profile.from_dict(p) for p in data.get("profiles", [])
        ]
        self.active_id = data.get("active", "")
        if not self.profiles:
            default = Profile(name="Default", version="latest-release")
            self.profiles.append(default)
            self.active_id = default.id
            self.save()

    def save(self):
        data = {
            "active": self.active_id,
            "profiles": [p.to_dict() for p in self.profiles],
        }
        save_json(self.filepath, data)

    def get_active(self):
        for p in self.profiles:
            if p.id == self.active_id:
                return p
        return self.profiles[0] if self.profiles else None

    def set_active(self, profile_id):
        self.active_id = profile_id
        self.save()

    def add(self, profile):
        self.profiles.append(profile)
        self.save()

    def remove(self, profile_id):
        self.profiles = [p for p in self.profiles if p.id != profile_id]
        if self.active_id == profile_id and self.profiles:
            self.active_id = self.profiles[0].id
        self.save()

    def update(self, profile):
        for i, p in enumerate(self.profiles):
            if p.id == profile.id:
                self.profiles[i] = profile
                break
        self.save()

    def get_names(self):
        return [p.name for p in self.profiles]

    def get_by_name(self, name):
        for p in self.profiles:
            if p.name == name:
                return p
        return None
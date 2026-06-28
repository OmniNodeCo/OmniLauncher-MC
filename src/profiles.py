"""Profile management for OmniLauncher-MC."""

import uuid
from datetime import datetime
from pathlib import Path
from utils import get_app_dir, load_json, save_json


class Profile:
    """Represents a game profile / instance."""

    def __init__(self, name: str, version: str, profile_id: str = None,
                 java_args: str = "", game_dir: str = "",
                 created: str = None, last_played: str = None,
                 loader: str = "vanilla", loader_version: str = ""):
        self.id = profile_id or str(uuid.uuid4())[:8]
        self.name = name
        self.version = version
        self.java_args = java_args
        self.game_dir = game_dir
        self.loader = loader
        self.loader_version = loader_version
        self.created = created or datetime.now().isoformat()
        self.last_played = last_played or ""

    def to_dict(self) -> dict:
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
    def from_dict(cls, data: dict) -> "Profile":
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

    def __init__(self):
        self.filepath = get_app_dir() / "profiles.json"
        self.profiles: list[Profile] = []
        self.active_id: str = ""
        self.load()

    def load(self) -> None:
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

    def save(self) -> None:
        data = {
            "active": self.active_id,
            "profiles": [p.to_dict() for p in self.profiles],
        }
        save_json(self.filepath, data)

    def get_active(self) -> Profile | None:
        for p in self.profiles:
            if p.id == self.active_id:
                return p
        return self.profiles[0] if self.profiles else None

    def set_active(self, profile_id: str) -> None:
        self.active_id = profile_id
        self.save()

    def add(self, profile: Profile) -> None:
        self.profiles.append(profile)
        self.save()

    def remove(self, profile_id: str) -> None:
        self.profiles = [p for p in self.profiles if p.id != profile_id]
        if self.active_id == profile_id and self.profiles:
            self.active_id = self.profiles[0].id
        self.save()

    def update(self, profile: Profile) -> None:
        for i, p in enumerate(self.profiles):
            if p.id == profile.id:
                self.profiles[i] = profile
                break
        self.save()

    def get_names(self) -> list[str]:
        return [p.name for p in self.profiles]

    def get_by_name(self, name: str) -> Profile | None:
        for p in self.profiles:
            if p.name == name:
                return p
        return None
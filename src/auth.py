"""Authentication module for OmniLauncher-MC (offline mode)."""

import uuid
from pathlib import Path
from utils import get_app_dir, load_json, save_json


class AuthManager:
    """Manages player authentication. Currently supports offline mode."""

    def __init__(self):
        self.filepath = get_app_dir() / "auth.json"
        self.username = ""
        self.uuid = ""
        self.token = ""
        self.auth_type = "offline"
        self.load()

    def load(self) -> None:
        data = load_json(self.filepath)
        self.username = data.get("username", "Player")
        self.uuid = data.get("uuid", self._generate_offline_uuid("Player"))
        self.token = data.get("token", "")
        self.auth_type = data.get("auth_type", "offline")

    def save(self) -> None:
        data = {
            "username": self.username,
            "uuid": self.uuid,
            "token": self.token,
            "auth_type": self.auth_type,
        }
        save_json(self.filepath, data)

    def login_offline(self, username: str) -> bool:
        """Login with offline / local username."""
        if not username or len(username) < 3 or len(username) > 16:
            return False
        if not username.isalnum() and "_" not in username:
            return False

        self.username = username
        self.uuid = self._generate_offline_uuid(username)
        self.token = ""
        self.auth_type = "offline"
        self.save()
        return True

    def is_logged_in(self) -> bool:
        return bool(self.username)

    def logout(self) -> None:
        self.username = ""
        self.uuid = ""
        self.token = ""
        self.save()

    def get_login_data(self) -> dict:
        return {
            "username": self.username,
            "uuid": self.uuid,
            "token": self.token if self.token else "0",
        }

    @staticmethod
    def _generate_offline_uuid(username: str) -> str:
        return str(uuid.uuid3(uuid.NAMESPACE_DNS, f"OfflinePlayer:{username}"))
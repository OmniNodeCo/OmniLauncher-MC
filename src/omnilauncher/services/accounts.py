"""Account management."""

from __future__ import annotations

from typing import Dict, List
from omnilauncher.config.settings import SettingsManager


class AccountService:
    def __init__(self, settings: SettingsManager):
        self.settings = settings

    def list_accounts(self) -> List[Dict]:
        return self.settings.get("accounts", "list", default=[])

    def get_selected(self) -> Dict:
        return self.settings.current_account

    def add_offline(self, username: str, skin_type: str = "steve") -> Dict:
        if not username or len(username) < 3 or len(username) > 16:
            raise ValueError("Username must be 3-16 characters")
        # basic check
        if not username.replace("_", "").isalnum():
            # allow but warn - Minecraft allows _? We'll allow alnum+underscore but offline lenient
            pass
        return self.settings.add_account(username, skin_type)

    def remove(self, uuid_str: str) -> None:
        self.settings.remove_account(uuid_str)

    def select(self, index: int) -> None:
        self.settings.select_account(index)

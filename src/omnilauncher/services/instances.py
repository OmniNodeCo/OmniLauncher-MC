"""Instances / Profiles management."""

from __future__ import annotations

from typing import Dict, List
from omnilauncher.config.settings import SettingsManager


BLOCK_ICONS = [
    "grass",
    "crafting_table",
    "furnace",
    "diamond",
    "emerald",
    "command_block",
    "bedrock",
    "tnt",
    "chest",
    "book",
    "anvil",
    "beacon",
    "bricks",
    "dirt",
    "stone",
    "gold",
    "iron",
    "redstone",
    "lapis",
    "nether",
    "end",
]


class InstanceService:
    def __init__(self, settings: SettingsManager):
        self.settings = settings

    def list_instances(self) -> List[Dict]:
        return self.settings.get("instances", "list", default=[])

    def get_selected_id(self) -> str:
        return self.settings.get("instances", "selected", default="default")

    def get_selected(self) -> Dict:
        return self.settings.current_instance

    def create(self, name: str, version: str, icon: str = "grass", group: str = "Custom") -> Dict:
        return self.settings.add_instance(name, version, icon, group)

    def delete(self, inst_id: str) -> None:
        self.settings.remove_instance(inst_id)

    def select(self, inst_id: str) -> None:
        self.settings.set_selected_instance(inst_id)

    def toggle_favorite(self, inst_id: str) -> None:
        for inst in self.settings.data["instances"]["list"]:
            if inst.get("id") == inst_id:
                inst["favorite"] = not inst.get("favorite", False)
        self.settings.save()

    def get_groups(self) -> List[str]:
        groups = set()
        for i in self.list_instances():
            groups.add(i.get("group", "Other"))
        return sorted(groups)

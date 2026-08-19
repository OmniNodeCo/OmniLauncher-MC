"""OmniLauncher settings manager - extensive configuration."""

from __future__ import annotations

import json
import os
import platform
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional


def _default_minecraft_dir() -> str:
    try:
        import minecraft_launcher_lib.utils as mcu

        return mcu.get_minecraft_directory()
    except Exception:
        return str(Path.home() / ".minecraft")


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _default_settings_file() -> Path:
    # Prefer app data dir if possible, fallback to project root
    try:
        if platform.system() == "Windows":
            base = Path(os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming")))
            p = base / "OmniLauncher-MC"
            p.mkdir(parents=True, exist_ok=True)
            return p / "settings.json"
        else:
            p = Path.home() / ".config" / "omnilauncher"
            p.mkdir(parents=True, exist_ok=True)
            return p / "settings.json"
    except Exception:
        pass
    return _project_root() / "settings.json"


DEFAULT_SETTINGS: Dict[str, Any] = {
    "general": {
        "language": "en_US",
        "keep_launcher_open": "hide",  # hide | close | minimize | keep_open
        "minimize_to_tray": False,
        "show_news": True,
        "check_updates": True,
        "enable_analytics": False,
        "minecraft_directory": "",  # empty = default
        "show_snapshots": False,
        "show_beta": False,
        "show_alpha": False,
        "show_experimental": False,
        "enable_historical": False,
        "sort_versions_desc": True,
        "hide_library": False,
        "quick_play_instance": "",
        "concurrent_downloads": 4,
        "auto_update": True,
    },
    "java": {
        "auto_detect": True,
        "java_path": "",
        "java_path_x86": "",
        "min_ram_mb": 512,
        "max_ram_mb": 4096,
        "perm_gen": 128,
        "jvm_args": "",
        "use_custom_args": False,
        "enable_gc_logging": False,
        "java_version_policy": "auto",  # auto | manual
    },
    "game": {
        "resolution": {
            "enabled": False,
            "width": 854,
            "height": 480,
            "fullscreen": False,
        },
        "game_args": "",
        "use_custom_args": False,
        "demo": False,
        "auto_connect": {
            "enabled": False,
            "server": "",
        },
        "quick_play_world": "",
        "quick_play_realm": "",
        "enable_chat_preview": True,
        "disable_multiplayer": False,
        "enable_logging": True,
    },
    "appearance": {
        "theme": "dark",  # dark | midnight | light | amoled | custom
        "accent_color": "#e94560",
        "background_style": "gradient",  # gradient | solid | image | animated
        "animations": True,
        "compact_mode": False,
        "sidebar_compact": False,
        "show_instance_icons": True,
        "layout": "modern",  # modern | classic
        "font_scale": 1.0,
        "transparency": 0.0,
    },
    "launcher": {
        "console_visible": True,
        "console_auto_scroll": True,
        "console_word_wrap": False,
        "console_font_size": 10,
        "console_show_timestamp": True,
        "console_filter_level": "all",  # all | info | warn | error
        "keep_logs": True,
        "max_log_days": 7,
        "debug_mode": False,
        "enable_file_watcher": True,
        "close_after_crash_report": False,
    },
    "network": {
        "proxy_enabled": False,
        "proxy_type": "http",  # http | socks5 | system
        "proxy_host": "",
        "proxy_port": 8080,
        "proxy_user": "",
        "proxy_pass": "",
        "offline_mode": False,
        "timeout": 30,
        "parallel_downloads": True,
    },
    "advanced": {
        "enable_advanced_settings": False,
        "custom_env_vars": "",
        "pre_launch_command": "",
        "post_exit_command": "",
        "wrapper_command": "",
        "enable_process_monitor": True,
        "kill_on_crash": False,
        "enable_crash_analyzer": True,
        "scan_mods_for_malware": True,
        "ignore_java_check": False,
    },
    "accounts": {
        "list": [
            {
                "uuid": str(uuid.uuid4()),
                "username": "Steve",
                "type": "offline",
                "skin_type": "steve",  # steve | alex
                "selected": True,
                "last_used": "",
                "cape": None,
            }
        ],
        "selected_index": 0,
    },
    "instances": {
        "list": [
            {
                "id": "default",
                "name": "Latest Release",
                "group": "Vanilla",
                "version": "",
                "icon": "grass",
                "minecraft_dir_suffix": "",
                "ram_override": None,
                "java_override": None,
                "jvm_args_override": None,
                "game_args_override": None,
                "resolution_override": None,
                "last_played": "",
                "playtime_minutes": 0,
                "favorite": True,
                "created": "",
                "loader": "vanilla",  # vanilla | forge | fabric | quilt | neoforge
                "loader_version": "",
            }
        ],
        "selected": "default",
        "view_mode": "grid",  # grid | list
        "sort_by": "last_played",  # name | last_played | version | playtime
        "show_favorites_only": False,
    },
    "meta": {
        "version": "0.2.0",
        "first_run": True,
        "last_username": "Steve",
        "last_version": "",
        "window_geometry": "1150x750",
        "window_maximized": False,
    },
}


class SettingsManager:
    """Manages persistent settings with extensive options."""

    def __init__(self, path: Optional[Path] = None):
        self.path = path or _default_settings_file()
        self._data: Dict[str, Any] = {}
        self.load()

    # ---- persistence ----

    def load(self) -> Dict[str, Any]:
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                # deep merge with defaults
                self._data = self._deep_merge(DEFAULT_SETTINGS, loaded)
            except Exception:
                self._data = self._deep_copy(DEFAULT_SETTINGS)
        else:
            self._data = self._deep_copy(DEFAULT_SETTINGS)

        # ensure minecraft dir filled
        if not self._data["general"]["minecraft_directory"]:
            self._data["general"]["minecraft_directory"] = _default_minecraft_dir()

        # ensure at least one account
        if not self._data["accounts"]["list"]:
            self._data["accounts"]["list"] = self._deep_copy(DEFAULT_SETTINGS["accounts"]["list"])

        # ensure at least one instance
        if not self._data["instances"]["list"]:
            self._data["instances"]["list"] = self._deep_copy(DEFAULT_SETTINGS["instances"]["list"])

        # migrate: fill empty version with latest if needed later, lazy
        return self._data

    def save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except Exception:
            # fallback to project root
            try:
                fallback = _project_root() / "settings.json"
                with open(fallback, "w", encoding="utf-8") as f:
                    json.dump(self._data, f, indent=2, ensure_ascii=False)
            except Exception:
                pass

    # ---- helpers ----

    @staticmethod
    def _deep_copy(d: Dict[str, Any]) -> Dict[str, Any]:
        return json.loads(json.dumps(d))

    @staticmethod
    def _deep_merge(default: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
        result = json.loads(json.dumps(default))
        for k, v in loaded.items():
            if isinstance(v, dict) and k in result and isinstance(result[k], dict):
                result[k] = SettingsManager._deep_merge(result[k], v)
            else:
                result[k] = v
        return result

    # ---- typed accessors ----

    def get(self, *keys: str, default: Any = None) -> Any:
        cur = self._data
        for k in keys:
            if not isinstance(cur, dict) or k not in cur:
                return default
            cur = cur[k]
        return cur

    def set(self, value: Any, *keys: str) -> None:
        cur = self._data
        for k in keys[:-1]:
            cur = cur.setdefault(k, {})
        cur[keys[-1]] = value

    @property
    def data(self) -> Dict[str, Any]:
        return self._data

    # convenience shortcuts

    @property
    def minecraft_dir(self) -> str:
        d = self.get("general", "minecraft_directory") or _default_minecraft_dir()
        return d

    @property
    def current_account(self) -> Dict[str, Any]:
        accounts = self.get("accounts", "list", default=[])
        idx = self.get("accounts", "selected_index", default=0)
        if 0 <= idx < len(accounts):
            return accounts[idx]
        return accounts[0] if accounts else {"username": "Steve"}

    @property
    def current_instance(self) -> Dict[str, Any]:
        instances = self.get("instances", "list", default=[])
        sel = self.get("instances", "selected", default="default")
        for inst in instances:
            if inst.get("id") == sel:
                return inst
        return instances[0] if instances else {}

    @property
    def ram_max_gb(self) -> float:
        return self.get("java", "max_ram_mb", default=4096) / 1024.0

    # accounts handling

    def add_account(self, username: str, skin_type: str = "steve") -> Dict[str, Any]:
        acc = {
            "uuid": str(uuid.uuid4()),
            "username": username,
            "type": "offline",
            "skin_type": skin_type,
            "selected": False,
            "last_used": "",
            "cape": None,
        }
        self._data["accounts"]["list"].append(acc)
        self.save()
        return acc

    def remove_account(self, acc_uuid: str) -> None:
        lst = self._data["accounts"]["list"]
        self._data["accounts"]["list"] = [a for a in lst if a.get("uuid") != acc_uuid]
        if not self._data["accounts"]["list"]:
            self._data["accounts"]["list"] = self._deep_copy(DEFAULT_SETTINGS["accounts"]["list"])
        self._data["accounts"]["selected_index"] = 0
        self.save()

    def select_account(self, index: int) -> None:
        if 0 <= index < len(self._data["accounts"]["list"]):
            self._data["accounts"]["selected_index"] = index
            self._data["meta"]["last_username"] = self._data["accounts"]["list"][index]["username"]
            self.save()

    # instances

    def add_instance(self, name: str, version: str, icon: str = "grass", group: str = "Custom") -> Dict[str, Any]:
        inst_id = f"{name.lower().replace(' ', '-')}-{uuid.uuid4().hex[:6]}"
        inst = {
            "id": inst_id,
            "name": name,
            "group": group,
            "version": version,
            "icon": icon,
            "minecraft_dir_suffix": inst_id,
            "ram_override": None,
            "java_override": None,
            "jvm_args_override": None,
            "game_args_override": None,
            "resolution_override": None,
            "last_played": "",
            "playtime_minutes": 0,
            "favorite": False,
            "created": "",
            "loader": "vanilla",
            "loader_version": "",
        }
        self._data["instances"]["list"].append(inst)
        self.save()
        return inst

    def remove_instance(self, inst_id: str) -> None:
        lst = self._data["instances"]["list"]
        if len(lst) <= 1:
            return  # keep at least one
        self._data["instances"]["list"] = [i for i in lst if i.get("id") != inst_id]
        if self._data["instances"]["selected"] == inst_id:
            self._data["instances"]["selected"] = self._data["instances"]["list"][0]["id"]
        self.save()

    def set_selected_instance(self, inst_id: str) -> None:
        self._data["instances"]["selected"] = inst_id
        self.save()


# singleton accessor
_settings_singleton: Optional[SettingsManager] = None


def get_settings_manager(path: Optional[Path] = None) -> SettingsManager:
    global _settings_singleton
    if _settings_singleton is None or path is not None:
        _settings_singleton = SettingsManager(path)
    return _settings_singleton

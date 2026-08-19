"""Minecraft version handling with caching and filtering with modern design."""

from __future__ import annotations

import time
from typing import List, Dict, Optional
from omnilauncher.config.settings import SettingsManager

try:
    import minecraft_launcher_lib.utils as mc_utils

    HAS_LIB = True
except Exception:
    HAS_LIB = False

_CACHE: Dict[str, any] = {"list": [], "timestamp": 0, "latest": {}}
CACHE_TTL = 60 * 30  # 30 min


def _fetch_all_versions_raw() -> List[Dict]:
    if not HAS_LIB:
        return [
            {"id": "1.21.1", "type": "release"},
            {"id": "1.21", "type": "release"},
            {"id": "1.20.6", "type": "release"},
            {"id": "1.20.1", "type": "release"},
            {"id": "1.19.4", "type": "release"},
        ]
    fallback = [
        {"id": "1.21.1", "type": "release"},
        {"id": "1.21", "type": "release"},
        {"id": "1.20.6", "type": "release"},
        {"id": "1.20.1", "type": "release"},
        {"id": "1.19.4", "type": "release"},
    ]
    try:
        result = mc_utils.get_version_list()
        if result:
            return result
    except Exception:
        if _CACHE["list"]:
            return _CACHE["list"]
        return fallback
    if _CACHE["list"]:
        return _CACHE["list"]
    return fallback


def _get_latest_raw() -> Dict[str, str]:
    if not HAS_LIB:
        return {"release": "1.21.1", "snapshot": "24w14a"}
    try:
        return mc_utils.get_latest_version()
    except Exception:
        return _CACHE.get("latest", {"release": "1.21.1", "snapshot": "24w14a"})


def refresh_cache() -> None:
    lst = _fetch_all_versions_raw()
    latest = _get_latest_raw()
    _CACHE["list"] = lst
    _CACHE["timestamp"] = time.time()
    _CACHE["latest"] = latest


def get_version_list(settings: Optional[SettingsManager] = None, force_refresh: bool = False) -> List[Dict]:
    now = time.time()
    if force_refresh or not _CACHE["list"] or (now - _CACHE["timestamp"] > CACHE_TTL):
        refresh_cache()
    versions = _CACHE["list"][:]

    if settings:
        show_snap = settings.get("general", "show_snapshots", default=False)
        show_beta = settings.get("general", "show_beta", default=False)
        show_alpha = settings.get("general", "show_alpha", default=False)
        show_exp = settings.get("general", "show_experimental", default=False)
        # if filters not enabled, only keep release by default, unless user enabled
        if not show_snap and not show_beta and not show_alpha:
            # if any filter enabled, keep logic:
            # Only release always shown, others filtered by toggles
            pass

        filtered: List[Dict] = []
        for v in versions:
            t = v.get("type", "release")
            if t == "release":
                filtered.append(v)
            elif t == "snapshot" and show_snap:
                filtered.append(v)
            elif t == "old_beta" and show_beta:
                filtered.append(v)
            elif t == "old_alpha" and show_alpha:
                filtered.append(v)
            elif t not in ("release", "snapshot", "old_beta", "old_alpha") and show_exp:
                filtered.append(v)
        versions = filtered

        # sorting
        if settings.get("general", "sort_versions_desc", default=True):
            # keep original order which is newest first from Mojang, so don't sort? but ensure stable
            pass
        else:
            versions = list(reversed(versions))

    return versions


def get_release_versions(settings: Optional[SettingsManager] = None) -> List[str]:
    return [v["id"] for v in get_version_list(settings) if v["type"] == "release"]


def get_all_version_ids(settings: Optional[SettingsManager] = None) -> List[str]:
    return [v["id"] for v in get_version_list(settings)]


def get_latest_version(settings: Optional[SettingsManager] = None) -> str:
    # check cache first
    if not _CACHE["latest"]:
        refresh_cache()
    latest = _CACHE["latest"] or {}
    return latest.get("release", "1.21.1")


def get_latest_snapshot() -> str:
    if not _CACHE["latest"]:
        refresh_cache()
    return _CACHE["latest"].get("snapshot", "")


def is_mod_loader_version(version_id: str) -> bool:
    # very simple heuristic
    for loader in ["forge", "fabric", "quilt", "neoforge", "optifine"]:
        if loader in version_id.lower():
            return True
    return False
